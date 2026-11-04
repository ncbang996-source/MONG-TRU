"""Kiểm tra xuất IFC4 (cú pháp STEP, đủ phần tử, GUID không trùng, cao độ), mô hình 3D (thanh bo cung, khối bê tông,
trục) và mặt bằng 1:1 (m) trong DXF - cho 4 trụ giống nhau và móng 2 loại."""
import math
import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from mongtru import export, ifc, model, view3d  # noqa: E402
from mongtru.geom import Geo  # noqa: E402
from mongtru.lech import export as le  # noqa: E402
from mongtru.lech import model as lm  # noqa: E402

d = tempfile.mkdtemp()
# bo cung: góc vuông bán kính r -> các điểm cung cách tâm đúng r
pts = view3d.fillet([(0, 0, 0), (1, 0, 0), (1, 1, 0)], 0.1, n=4)
assert len(pts) == 2 + 5 and all(abs(math.dist(p, (0.9, 0.1, 0)) - 0.1) < 1e-9 for p in pts[1:-1]), pts
assert abs(view3d.bend_r(0.008) - 0.012) < 1e-12 and abs(view3d.bend_r(0.014) - 0.035) < 1e-12
p, _ = model.read_excel(os.path.join(ROOT, "samples", "D112-30.xls"))
mp, _ = lm.read_excel(os.path.join(ROOT, "samples", "N112-52(60) - 3T-1T.xls"))
mp["SCALE"] = lm.auto_scale(mp)
sc = view3d.Scene(Geo(p))
assert {k for k, _, _ in sc.solids} == {"mong", "lot"} and len(sc.solids) == 8 and len(sc.axes) == 4
for nm, data in (("d112", p), ("mix", mp)):
    f = os.path.join(d, nm + ".ifc")
    ifc.export(data, f)
    s = open(f, encoding="ascii").read()
    assert s.startswith("ISO-10303-21;") and "FILE_SCHEMA(('IFC4'));" in s and s.rstrip().endswith("END-ISO-10303-21;")
    rows = re.findall(r"^#(\d+)=([A-Z0-9]+)\((.*)\);$", s, re.M)
    ids = [int(r[0]) for r in rows]
    assert ids == list(range(1, len(ids) + 1))
    refs = {int(x) for r in rows for x in re.findall(r"#(\d+)", r[2])}
    assert refs <= set(ids), "tham chiếu tới thực thể không có"
    cnt = {}
    for _, t, _ in rows:
        cnt[t] = cnt.get(t, 0) + 1
    assert cnt["IFCFOOTING"] == 4 and cnt["IFCSLAB"] == 4 and cnt["IFCMECHANICALFASTENER"] == 4, cnt
    assert cnt["IFCREINFORCINGBAR"] >= 4 * 6 and cnt["IFCGRID"] == 1 and cnt["IFCPROJECT"] == 1, cnt
    gids = re.findall(r"^#\d+=IFC[A-Z]+\('([0-9A-Za-z_$]{22})',", s, re.M)
    assert len(gids) == len(set(gids)), "GlobalId trùng"
    # cao độ: 4 trụ giống nhau - mặt đất 0 -> đỉnh cổ = d (H2), đáy lót = -(H1 + lót)
    zs = [float(z) for z in re.findall(r"\([-0-9.]+,[-0-9.]+,([-0-9.]+)\)", s)]
    if nm == "d112":
        assert abs(min(zs) + (p["H1"] + model.TL) * 1000) < 1 and max(zs) >= p["H2"] * 1000 - 1, (min(zs), max(zs))
    # mặt bằng 1:1 trong DXF (ngoài các tờ, không in PDF)
    r = le.build(data) if "TYPES" in data else export.build(data)
    txt = [t.dxf.text for t in r.doc.modelspace().query("TEXT")]
    assert any(t.startswith("MẶT BẰNG MÓNG - TỶ LỆ 1:1") for t in txt)
    ins = {h for hs in r.handles for h in hs}
    plan = [e for e in r.doc.modelspace().query("TEXT") if e.dxf.text.startswith("TRỤ ")]
    assert len(plan) == 4 and not any(e.dxf.handle in ins for e in plan)
    xs = [e.dxf.insert.x for e in plan]
    assert max(xs) < 0                                          # bên trái tờ 1
    print(f"  {nm}: {len(rows)} thực thể IFC, {cnt['IFCREINFORCINGBAR']} nhóm thép, {os.path.getsize(f) // 1024} KB")
print("OK - IFC, 3D, mat bang 1:1")
