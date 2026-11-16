"""Kiểm tra mặt bằng 1:1 (m) trong DXF theo quy ước cho phần mềm nhận: 4 block BLN (tim cụm bu lông từng trụ), block
TIM TRU (gốc 0,0, hình ở toạ độ thật, chèn tại 0,0), bản đế polyline kín MAIN (ô vuông lớn nhất quanh mỗi chân), bê
tông lót polyline kín THIN, mã cột chữ COT, tên móng chữ MONG - đọc lại từ file DXF đã ghi."""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import ezdxf  # noqa: E402

from mongtru import model, export  # noqa: E402
from mongtru.lech import export as le  # noqa: E402
from mongtru.lech import model as lm  # noqa: E402

d = tempfile.mkdtemp()
p, _ = model.read_excel(os.path.join(ROOT, "samples", "D112-30.xls"))
mp, _ = lm.read_excel(os.path.join(ROOT, "samples", "N112-52(60) - 3T-1T.xls"))
mp["SCALE"] = lm.auto_scale(mp)
for nm, data, res in (("4tru", p, export.build(p)), ("2loai", mp, le.build(mp))):
    f = os.path.join(d, nm + ".dxf")
    export.save_dxf(res, f)
    doc = ezdxf.readfile(f)
    msp = doc.modelspace()
    bln = [e for e in msp.query("INSERT") if e.dxf.name == "BLN"]
    assert len(bln) == 4, len(bln)
    tim = [e for e in msp.query("INSERT") if e.dxf.name == "TIM TRU"]
    assert len(tim) == 1 and tuple(tim[0].dxf.insert)[:2] == (0.0, 0.0)
    blk = doc.blocks.get("TIM TRU")
    assert tuple(blk.block.dxf.base_point)[:2] == (0.0, 0.0)
    pt = [e for e in blk if e.dxftype() == "POINT"][0].dxf.location            # tim móng, toạ độ thật
    assert pt.x < 0 and abs(pt.y - 148.5) < 1e-9                                  # bên trái tờ 1
    # tim cụm bu lông 4 trụ đối xứng qua tim móng (cùng khoảng cách Bt/2 theo X, Y với 4 trụ giống nhau)
    cs = [(e.dxf.insert.x - pt.x, e.dxf.insert.y - pt.y) for e in bln]
    assert {(x > 0, y > 0) for x, y in cs} == {(True, True), (True, False), (False, True), (False, False)}
    if nm == "4tru":
        assert all(abs(abs(x) - p["BT"] / 2) < 1e-6 and abs(abs(y) - p["BT"] / 2) < 1e-6 for x, y in cs), cs

    def box(e):
        xs, ys = zip(*[(q[0], q[1]) for q in e.get_points()])
        return min(xs), min(ys), max(xs), max(ys)
    mains = [box(e) for e in msp.query("LWPOLYLINE") if e.dxf.layer == "MAIN" and e.closed]
    for e in bln:
        x, y = e.dxf.insert.x, e.dxf.insert.y
        around = [b for b in mains if b[0] < x < b[2] and b[1] < y < b[3]]
        big = max(around, key=lambda b: b[2] - b[0])
        g = (big[2] - big[0], big[3] - big[1])
        assert abs(g[0] - g[1]) < 1e-9                                            # ô vuông
        want = {t["B"] for t in data["TYPES"]} if "TYPES" in data else {data["B"]}
        assert any(abs(g[0] - w) < 1e-9 for w in want), (g, want)                 # = cạnh bản đế Bm
    thin = [e for e in msp.query("LWPOLYLINE") if e.dxf.layer == "THIN" and e.closed]
    assert len(thin) == 4
    cot = [t.dxf.text for t in msp.query("TEXT") if t.dxf.layer == "COT"]
    mong = [t.dxf.text for t in msp.query("TEXT") if t.dxf.layer == "MONG"]
    assert cot == [str(data["COT"])], cot
    assert mong == [data.get("TENMONG") or (lm.type_name(data) if "TYPES" in data else model.type_name(data))], mong
    assert not any(t.dxf.layer == "VI TRI" for t in msp.query("TEXT"))
    print(f"  {nm}: BLN {len(bln)}, TIM TRU tại 0,0 (tim {pt.x:.2f}, {pt.y:.2f}), MAIN/THIN ok, COT={cot[0]}, MONG={mong[0]}")
print("OK - mat bang 1:1 theo quy uoc")
