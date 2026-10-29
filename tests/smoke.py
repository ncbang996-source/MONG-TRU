"""Kiểm tra nhanh: đọc Excel mẫu (.xls), dựng 2 tờ, xuất PDF + DXF + Excel khối lượng, so với Excel mẫu."""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from mongtru import export, kl_excel, model, view3d  # noqa: E402
from mongtru.geom import Geo  # noqa: E402

p, warn = model.read_excel(os.path.join(ROOT, "samples", "D112-30.xls"))
assert not warn, warn
assert int(p["NPIER"]) == 4 and abs(p["DP"] - 10) < 1e-9 and p["RL_N"] == 2
# khối lượng theo sheet "KL" của Excel mẫu (4 trụ, đào chung 1 hố)
assert abs(model.vol_mong(p) - 18.872) < 0.001
assert abs(model.vol_lot(p) - 3.364) < 0.001
assert model.pit_joint(p)
assert abs(model.vol_dao(p) - 159.649) < 0.001 and abs(model.vol_dap(p) - 138.393) < 0.001
assert abs(model.area_vk(p) - 38.72) < 0.001
res = export.build(p, os.path.join(ROOT, "assets", "frames", "KT-A3.dxf"))
g = res.geo
# thép tính theo bố trí trên bản vẽ (quy tắc app móng bản không dầm), khác sheet "KL" của Excel mẫu:
# - thép bản đế rải theo vùng gờ cổ móng / phần vát: 15 thanh mỗi phương (Excel 14)
# - đai cổ móng: 2 đai dưới 2 lớp lưới đầu trụ, còn lại @200 (Excel: @100 trên 1950 mm + @200)
# - thanh chống đủ lưới (16), vị trí gần thép chủ cổ móng dời tránh; neo chân thép chủ 500 (Excel 400)
kl = {r["pos"]: r for r in g.kl}
assert kl[1]["qty"] == "30x4" and kl[2]["qty"] == "30x4" and kl[3]["qty"] == "16x4", kl
assert kl[4]["qty"] == "20x4" and kl[5]["qty"] == "13x4" and kl[8]["qty"] == "28x4", kl
d = tempfile.mkdtemp()
export.save_dxf(res, os.path.join(d, "t.dxf"))
data = export.pdf_bytes(res)
assert data[:4] == b"%PDF" and len(res.origins) == 2
print("OK - thep", round(sum(r["kg"] for r in g.kl), 2), "kg; PDF", len(data), "bytes")
kl_excel.export(p, g, os.path.join(d, "kl.xlsx"))
# giai đoạn TKCS: 1 tờ
assert len(export.build(dict(p, GD="TKCS")).origins) == 1
# đào riêng từng trụ, cổ móng nhiều thanh, móng lớn
for ov in (dict(BT=8.0), dict(RC_N=32, B1=1.2, B2=1.2, B=5.5, BT=8.06, H1=4.0, H2=1.0, HB=1.0, HV=0.4),
           dict(HT=1), dict(HT=2, RL_N=1)):
    q = dict(p, **ov)
    q["SCALE"] = model.auto_scale(q)
    assert model.validate(q) is None, (ov, model.validate(q))
    r = export.build(q)
    export.pdf_bytes(r)
    view3d.Scene(Geo(q), quarter=True)
print("OK - Excel khoi luong, TKCS, cac truong hop khac")

# --- móc 2 đầu thép lớp trên: bội số 5 mm, đầu móc không thấp hơn mặt trên lưới dưới
for hv in (0.25, 0.30, 0.35, 0.45):
    q = dict(p, HV=hv, HB=max(p["HB"], hv + 0.2))
    g2 = Geo(q)
    hk = g2.hook_top()
    assert abs(hk * 1000 / 5 - round(hk * 1000 / 5)) < 1e-6, (hv, hk)
    z_end = g2.ztop(g2.Bh - g2.cov) - (g2.cov + g2.dt / 2) - hk        # đầu móc thanh ngoài cùng lớp trên
    assert z_end >= g2.covb + 2 * g2.db - 1e-9, (hv, hk, z_end)
    g2.calc_kl()
    assert abs({r["pos"]: r for r in g2.kl}[2]["dims"][2] - 1000 * hk) < 1e-6

# --- đọc 2 file liên tiếp: ô trống ở file 2 không giữ giá trị của file 1
import openpyxl  # noqa: E402

def make_xlsx(path, **cells):
    src = openpyxl.Workbook()
    ws = src.active
    ws.title = "TONG HOP"
    vals = {"B4": "ĐỠ", "C4": "D1", "C6": "TKBVTC", "J4": "B20", "J5": "B7.5", "B9": 2.7, "B10": 2.5, "B11": 0.5,
            "B12": 3.2, "B13": 0.7, "B14": 0.7, "B15": 0.7, "B16": 0.3, "C18": 0.5, "C19": 0.3, "C20": "BLN-",
            "D20": "M36-250", "H21": 12, "I21": 200, "H22": 12, "I22": 200, "H23": 12, "I23": 600, "C22": 50,
            "C23": 50, "C24": 4, "H25": 20, "I25": 20, "H26": 8, "I26": 200, "H27": 8, "I27": 400, "H28": 8,
            "I28": 100, "K28": "02 lớp", "H29": 10}
    vals.update(cells)
    for a, v in vals.items():
        if v is not None:
            ws[a] = v
    src.save(path)

f1, f2 = os.path.join(d, "f1.xlsx"), os.path.join(d, "f2.xlsx")
make_xlsx(f1, C5="MT-FILE1", J6="MA-FILE1", C24=8, H29=5, B12=20.0, D20="M42-300")
make_xlsx(f2, C5=None, J6=None)
p1, _ = model.read_excel(f1, "TONG HOP", model.fresh_params(dict(model.default_params(), MABV="X", PIT_DRAW=2.0)))
p1["SCALE"] = model.auto_scale(p1)
assert p1["TENMONG"] == "MT-FILE1" and p1["NPIER"] == 8 and p1["MABV"] == "X" and p1["PIT_DRAW"] == 2.0
p2, _ = model.read_excel(f2, "TONG HOP", model.fresh_params(p1))
p2["SCALE"] = model.auto_scale(p2)
assert p2["TENMONG"] == "" and p2["CODE"] == "" and p2["NPIER"] == 4 and p2["DP"] == 10 and p2["BLN"] == "BLN-M36-250"
assert p2["MABV"] == "X" and p2["PIT_DRAW"] == 2.0, p2
assert p1["SCALE"] > p2["SCALE"], (p1["SCALE"], p2["SCALE"])          # mở file nhỏ sau file lớn: tỷ lệ đổi lại
make_xlsx(f2, C22=None, C24=None, H29=None)
_, w3 = model.read_excel(f2, "TONG HOP", model.fresh_params())
assert any("C22" in w for w in w3) and any("C24" in w for w in w3) and any("H29" in w for w in w3), w3

# --- tỷ lệ tờ 1: tỷ lệ lớn nhất vẽ đúng tỷ lệ (không thu gọn Bt)
for bt in (3.2, 8.0, 15.0, 20.0):
    q = dict(p, BT=bt)
    den = model.auto_scale(q)
    assert model.draw_bt(q, den) >= bt - 1e-9, (bt, den)
    bigger = [s for s in model.SCALES if s < den]
    assert not bigger or model.draw_bt(q, bigger[-1]) < bt - 1e-9, (bt, den)

# --- trình bày hố đào: dựng được cả 3 lựa chọn (kể cả khi Bt bị thu gọn), khối lượng đào / đắp không đổi
for ov in (dict(BT=3.2), dict(B=4.0, BT=7.5), dict(B=4.0, BT=7.5, SCALE=75)):
    q0 = dict(p, **ov)
    if "SCALE" not in ov:
        q0["SCALE"] = model.auto_scale(q0)
    vd, vp = model.vol_dao(q0), model.vol_dap(q0)
    for m in (0.0, 1.0, 2.0):
        q = dict(q0, PIT_DRAW=m)
        export.pdf_bytes(export.build(q))
        assert model.vol_dao(q) == vd and model.vol_dap(q) == vp
        assert model.pit_joint_draw(q) == (model.pit_joint(q) if m == 0 else m == 1)
    assert ov.get("SCALE") != 75 or model.draw_bt(q0, 75) < q0["BT"]     # trường hợp thu gọn Bt

# --- TKKT: 2 tờ, không có bảng thống kê thép
r = export.build(dict(p, GD="TKKT"))
assert len(r.origins) == 2
ids = {o.id for o in r.objs[1]}
assert not any("table" in i or ".bar" in i for i in ids), ids
assert any("table" in o.id for o in res.objs[1])
print("OK - moc lop tren, doc 2 file, ty le, trinh bay ho dao, TKKT")

# --- cổ móng vát (N112-30(60).xls): khối lượng theo sheet KL, ván khuôn theo diện tích vát thật
pv, wv = model.read_excel(os.path.join(ROOT, "samples", "N112-30(60).xls"))
pv["SCALE"] = model.auto_scale(pv)
assert not wv, wv
assert pv["B2"] > pv["B1"] and int(pv["HT"]) == 1 and pv["MABV"] == "2511TNC2.F.NM.C.201", pv
for f, want in ((model.vol_mong, 27.38), (model.vol_lot, 4.096), (model.vol_dao, 255.563), (model.vol_dap, 225.227),
                (model.area_vk, 49.768)):
    assert abs(f(pv) - want) < 0.001, (f.__name__, f(pv), want)
rv = export.build(pv)
gv = rv.geo
assert all(k in gv.klb for k in (4, 5)), gv.klb.keys()          # bảng kích thước từng thanh cho thép chiều dài thay đổi
assert len(rv.origins) == model.n_sheets(pv) == 3
ids3 = {o.id for o in rv.objs[2]}
assert all(any(f"bar{k}" in i for i in ids3) for k in gv.klb if k in gv.seq), ids3
export.pdf_bytes(rv)
export.save_dxf(rv, os.path.join(d, "vat.dxf"))
kl_excel.export(pv, gv, os.path.join(d, "vat.xlsx"))
assert len(export.build(dict(pv, GD="TKKT")).origins) == 2
view3d.Scene(gv)
view3d.Scene(Geo(pv), quarter=True)
# chiều dài trung bình thép chủ cổ = trung bình bảng kích thước từng thanh
r4 = {r["pos"]: r for r in gv.kl}[4]
rows = gv.klb[4]
assert abs(sum(x[3] * x[4] for x in rows) / sum(x[4] for x in rows) - r4["len"]) < 1.0, (r4["len"], rows[:2])
print("OK - co mong vat")
