"""Kiểm tra nhanh móng 2 loại (mongtru.lech): đọc Excel mẫu, khối lượng so với Excel mẫu, dựng bản vẽ các
trường hợp (3+1, 2+2, cao độ khác nhau, đào chung đáy bậc, cổ vát, TKCS / TKKT), PDF / DXF / Excel, 3D."""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from mongtru import export, model  # noqa: E402
from mongtru.lech import export as le  # noqa: E402
from mongtru.lech import kl_excel as lk  # noqa: E402
from mongtru.lech import model as lm  # noqa: E402
from mongtru.lech import ui as lui  # noqa: E402
from mongtru.lech.view3d import MixedScene  # noqa: E402

F = os.path.join(ROOT, "samples", "N112-52(60) - 3T-1T.xls")
assert lm.detect(F)
assert not lm.detect(os.path.join(ROOT, "samples", "D112-30.xls"))
assert not lm.detect(os.path.join(ROOT, "samples", "N112-30(60).xls"))
mp, warn = lm.read_excel(F)
t1, t2 = mp["TYPES"]
assert (t1["NAME"], t1["POS"], t2["NAME"], t2["POS"]) == ("T42-60", [1], "T42-40", [2, 3, 4]), mp["TYPES"]
assert t1["H2"] == 2.5 and t2["H2"] == 0.5 and mp["BT"] == 9.3 and mp["HT"] == 1
assert mp["MABV"] == "2511TNC2.F.NM.C.201" and mp["TENMONG"] == "MT93.0 1T42-60/3T42-40"
assert any("C46" in w for w in warn), warn                 # ô lỗi liên kết ở loại 2 -> lấy theo loại 1
assert lm.validate(mp) is None
# khối lượng theo sheet TONG HOP KL của Excel mẫu (1/4 loại 1 + 3/4 loại 2; đào / đắp cùng độ sâu)
for f, want in ((lm.vol_mong, 59.3533), (lm.vol_lot, 7.744), (lm.area_vk, 92.0), (lm.vol_dao, 642.816),
                (lm.vol_dap, 580.5587), (lm.den_bu, 14.5)):
    assert abs(f(mp) - want) < 1e-3, (f.__name__, f(mp), want)
assert lm.bolt_text(mp) == "16M36"
# 2 loại giống nhau -> trùng công thức bản 4 trụ giống nhau (cả hố chung)
p, _ = model.read_excel(os.path.join(ROOT, "samples", "D112-30.xls"))
mq = lm.default_mp()
mq.update({k: p[k] for k in lm.COMMON if k in p})
for t in mq["TYPES"]:
    t.update({k: p[k] for k in lm.TYPE_KEYS})
for bt in (3.2, 8.0):
    mq["BT"] = bt
    q = dict(p, BT=bt)
    assert lm.pit_joint(mq) == model.pit_joint(q)
    for a, b in ((lm.vol_dao, model.vol_dao), (lm.vol_dap, model.vol_dap), (lm.vol_mong, model.vol_mong)):
        assert abs(a(mq) - b(q)) < 1e-4, (bt, a.__name__, a(mq), b(q))


def case(**kw):
    m = {k: (v if k != "TYPES" else [dict(t) for t in v]) for k, v in mp.items()}
    for k, v in kw.items():
        if k in ("t1", "t2"):
            m["TYPES"][int(k[1]) - 1].update(v)
        else:
            m[k] = v
    m["SCALE"] = lm.auto_scale(m)
    assert lm.validate(m) is None, (kw, lm.validate(m))
    return m


d = tempfile.mkdtemp()
cases = {
    "mau": case(),
    "cao_do": case(t1=dict(CD=-2.0)),
    "2_2_hang": case(t1=dict(POS=[1, 2], B=3.6, CD=-1.0), t2=dict(POS=[3, 4])),
    "2_2_cot": case(t1=dict(POS=[1, 3]), t2=dict(POS=[2, 4], B=3.8)),
    "3_1_duoi": case(t1=dict(POS=[4]), t2=dict(POS=[1, 2, 3])),
    "chung_bac": case(BT=5.5, t1=dict(CD=-1.5, B2=1.6), t2=dict(B=3.6)),
    "tkcs": case(GD="TKCS"),
    "tkkt": case(GD="TKKT"),
    "neo_dung": case(HT=2),
    "do": case(HT=0, t2=dict(RC_N=28)),
    "ha_cao_do": case(GX=-0.5, GY=0.5, GM=1.5, t1=dict(CD=-2.0)),
    "ha_2_2": case(GY=1.0, t1=dict(POS=[1, 2], CD=-1.5), t2=dict(POS=[3, 4])),
    "bac_day": case(BT=7.0, FX=0.75, FY=-0.75, t1=dict(CD=-2.0, H1=4.5)),
}
for nm, m in cases.items():
    r = le.build(m, os.path.join(ROOT, "assets", "frames", "KT-A3.dxf"))
    nsh = le.n_sheets(m)
    assert len(r.origins) == nsh, (nm, len(r.origins), nsh)
    if "TKCS" in m["GD"]:
        assert nsh == 1
    elif "TKKT" in m["GD"]:
        assert nsh == 3                                    # tờ 1 + tờ thép 2 loại, không có bảng thép
        ids = {o.id for objs in r.objs[1:] for o in objs}
        assert not any("table" in i or ".bar" in i for i in ids), ids
    else:
        assert nsh >= 3
        ids = {o.id for o in r.objs[0]}
        assert not any(i.endswith("table") for i in ids)  # bảng thống kê thép không lên tờ 1 (tờ 1: tổng kê)
    export.pdf_bytes(r)
    export.save_dxf(r, os.path.join(d, f"{nm}.dxf"))
    lk.export(m, le.geos(m), os.path.join(d, f"{nm}.xlsx"))
    MixedScene(m)
    MixedScene(m, quarter=True)
    print(f"  {nm}: {nsh} tờ, tỷ lệ tờ 1 1/{m['SCALE']}, A-A {lm.section_pair(m)}, "
          f"đào {'chung' if lm.pit_joint(m) else 'riêng'} {lm.vol_dao(m):.2f} m3")
# hạ cao độ / bậc đáy: tích phân số trùng công thức chóp cụt khi mặt đất / đáy hố 1 mức
for m in (cases["mau"], case(BT=5.0)):
    exact = lm.vol_dao_joint(m) if lm.pit_joint(m) else lm.vol_dao_sep(m)
    assert abs(lm.vol_dao_num(m) - exact) < 0.002 * exact, (lm.vol_dao_num(m), exact)
assert lm.vol_dao(cases["ha_cao_do"]) > lm.vol_dao_sep(cases["ha_cao_do"])        # mái hạ cao độ cắt qua hố
assert not any("Bậc đáy" in w for w in lm.warnings(cases["bac_day"]))             # bậc đáy đặt đúng chỗ
assert any("Bậc đáy" in w for w in lm.warnings(case(BT=6.0, t1=dict(CD=-2.0, H1=4.5))))   # tại tim móng: cắt vào đáy
# mặt cắt A-A qua 2 trụ khác loại
for nm, m in cases.items():
    a, b, _ = lm.section_pair(m)
    ta = lm.type_at(m)
    assert ta[a] != ta[b], nm
# giao diện: ghép / tách thông số
p0 = lui.fill_params(mp, 1)
m2 = lui.merge(mp, 1, dict(p0, B=3.9), "2, 3", "-0.5")
assert m2["TYPES"][1]["POS"] == [2, 3] and m2["TYPES"][0]["POS"] == [1, 4] and m2["TYPES"][1]["B"] == 3.9
assert m2["TYPES"][1]["CD"] == -0.5 and lui.valid_saved(m2)
print("OK - mong 2 loai")
