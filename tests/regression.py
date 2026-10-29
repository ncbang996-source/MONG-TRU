"""Khóa định dạng bản móng trụ 4 trụ giống nhau (bản ổn định 1.0.0).

So dấu vân tay bản vẽ (từng nét, chữ, kích thước theo từng tờ), khối lượng và Excel khối lượng (công thức từng ô)
của một loạt trường hợp với tests/golden.json. Lệch bất kỳ chi tiết nào -> báo lỗi: phần phát triển mới đã làm
thay đổi định dạng cũ, cần người dùng xác nhận trước khi cập nhật mẫu.

    python tests/regression.py            # kiểm tra
    python tests/regression.py --update   # ghi lại mẫu (CHỈ khi người dùng đã đồng ý đổi định dạng cũ)
"""
import hashlib
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import openpyxl  # noqa: E402

from mongtru import export, kl_excel, model  # noqa: E402

GOLDEN = os.path.join(ROOT, "tests", "golden.json")
D112 = os.path.join(ROOT, "samples", "D112-30.xls")
N112 = os.path.join(ROOT, "samples", "N112-30(60).xls")
CASES = {
    "d112": (D112, {}),
    "d112_tkcs": (D112, dict(GD="TKCS")),
    "d112_tkkt": (D112, dict(GD="TKKT")),
    "d112_neo_goc": (D112, dict(HT=1)),
    "d112_neo_dung": (D112, dict(HT=2, RL_N=1)),
    "d112_ho_rieng": (D112, dict(BT=8.0)),
    "d112_lon": (D112, dict(RC_N=32, B1=1.2, B2=1.2, B=5.5, BT=8.06, H1=4.0, H2=1.0, HB=1.0, HV=0.4)),
    "d112_ho_ve_rieng": (D112, dict(PIT_DRAW=2.0)),
    "n112_vat": (N112, {}),
    "n112_vat_rc28": (N112, dict(RC_N=28)),
    "n112_vat_to3": (N112, dict(B=4.5, B2=1.6, RC_N=40, RT_S=100, RP_S=200)),
    "n112_tkkt": (N112, dict(GD="TKKT")),
}


def _r(x):
    return round(float(x), 2)


def _sig(e):
    t = e.dxftype()
    d = e.dxf
    lay = d.layer
    if t == "LINE":
        g = sorted([(_r(d.start.x), _r(d.start.y)), (_r(d.end.x), _r(d.end.y))])
    elif t == "TEXT":
        g = (d.text, _r(d.insert.x), _r(d.insert.y), _r(d.height), _r(d.get("rotation", 0.0)))
    elif t == "LWPOLYLINE":
        g = [(_r(x), _r(y), _r(b)) for x, y, *_, b in e.get_points("xyseb")] + [e.closed]
    elif t == "CIRCLE":
        g = (_r(d.center.x), _r(d.center.y), _r(d.radius))
    elif t == "DIMENSION":
        g = (e.get_measurement() if hasattr(e, "get_measurement") else None, d.get("text", ""),
             _r(d.defpoint.x), _r(d.defpoint.y), _r(d.defpoint2.x), _r(d.defpoint2.y),
             _r(d.defpoint3.x), _r(d.defpoint3.y), d.dimstyle)
        g = tuple(_r(x) if isinstance(x, float) else str(x) for x in g)
    elif t == "SOLID":
        g = [(_r(p.x), _r(p.y)) for p in (d.vtx0, d.vtx1, d.vtx2, d.vtx3)]
    elif t == "INSERT":
        g = (d.name, _r(d.insert.x), _r(d.insert.y))
    elif t == "HATCH":
        g = len(e.paths)
    else:
        g = None
    return json.dumps([t, lay, g], ensure_ascii=False, default=str)


def fingerprint(fn, ov):
    p, _ = model.read_excel(fn)
    p.update(ov)
    p["SCALE"] = model.auto_scale(p)
    res = export.build(p)
    g = res.geo
    msp = res.doc.modelspace()
    ents = {e.dxf.handle: e for e in msp}
    sheets = []
    for hs in res.handles:
        sig = sorted(_sig(ents[h]) for h in hs if h in ents)
        sheets.append(hashlib.sha1("\n".join(sig).encode()).hexdigest())
    kl = [[r["pos"], r["dia"], round(r["len"], 1), r["qty"], round(r["kg"], 2)] for r in g.kl]
    vol = [round(f(p), 3) for f in (model.vol_mong, model.vol_lot, model.vol_dao, model.vol_dap, model.area_vk)]
    xl = os.path.join(tempfile.mkdtemp(), "kl.xlsx")
    kl_excel.export(p, g, xl)
    wb = openpyxl.load_workbook(xl)
    cells = []
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if c.value is not None:
                    cells.append(f"{ws.title}!{c.coordinate}={c.value}")
    return {"sheets": sheets, "kl": kl, "vol": vol, "excel": hashlib.sha1("\n".join(cells).encode()).hexdigest()}


def main():
    cur = {nm: fingerprint(fn, ov) for nm, (fn, ov) in CASES.items()}
    if "--update" in sys.argv:
        with open(GOLDEN, "w", encoding="utf-8") as f:
            json.dump(cur, f, ensure_ascii=False, indent=1)
        print("Đã ghi mẫu:", GOLDEN)
        return 0
    with open(GOLDEN, encoding="utf-8") as f:
        gold = json.load(f)
    bad = 0
    for nm, v in cur.items():
        w = gold.get(nm)
        if w is None:
            print(f"[{nm}] chưa có trong mẫu")
            bad += 1
            continue
        for k in ("vol", "kl", "excel"):
            if v[k] != w[k]:
                print(f"[{nm}] {k} khác mẫu:\n   mẫu: {w[k]}\n   nay: {v[k]}")
                bad += 1
        if len(v["sheets"]) != len(w["sheets"]):
            print(f"[{nm}] số tờ {len(v['sheets'])} (mẫu {len(w['sheets'])})")
            bad += 1
        else:
            for i, (a, b) in enumerate(zip(v["sheets"], w["sheets"]), 1):
                if a != b:
                    print(f"[{nm}] tờ {i} khác mẫu")
                    bad += 1
    print("Khóa định dạng: số chỗ khác mẫu =", bad, "/", len(CASES), "trường hợp")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
