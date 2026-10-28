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
# - thanh chống: bỏ vị trí nằm trong cổ móng; neo chân thép chủ 500 (Excel 400)
kl = {r["pos"]: r for r in g.kl}
assert kl[1]["qty"] == "30x4" and kl[2]["qty"] == "30x4" and kl[3]["qty"] == "12x4", kl
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
