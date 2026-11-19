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
# số trụ từng chân (layer TEN TRU): M1..M4 trong ô bản đế đúng chân, không đè BLN, trùng tag Mk của khối IFC
import copy  # noqa: E402
import re  # noqa: E402
from mongtru import ifc  # noqa: E402


def ifc_quads(path):
    """{tag Mk: (dấu x, dấu y) tâm khối IfcFooting, tên khối} đọc từ file IFC."""
    src = open(path, encoding="ascii").read()
    ent = {int(m.group(1)): m.group(2) for m in re.finditer(r"^#(\d+)=(.*);$", src, re.M)}
    out = {}
    for k, v in ent.items():
        m = re.match(r"IFCFOOTING\('[^']+',#\d+,'([^']*)',\$,\$,#\d+,#(\d+),'(M\d)'", v)
        if not m:
            continue
        shp = ent[int(m.group(2))]
        rep = ent[int(re.search(r"\(#(\d+)\)", shp).group(1))]
        fs = ent[int(re.search(r",\(#(\d+)", rep).group(1))]
        pl = ent[int(re.search(r"IFCPOLYGONALFACESET\(#(\d+)", fs).group(1))]
        xy = [tuple(map(float, t.split(",")[:2])) for t in re.findall(r"\(([-0-9.E]+,[-0-9.E]+,[-0-9.E]+)\)", pl)]
        cx, cy = sum(a for a, _ in xy) / len(xy), sum(b for _, b in xy) / len(xy)
        out[m.group(3)] = ((1 if cx > 0 else -1, 1 if cy > 0 else -1), m.group(1))
    return out


mp2 = copy.deepcopy(mp)                       # như MT65.0 3T35-35/1T35-45: trụ 2 là loại sâu (loại 1)
mp2["TYPES"][0]["POS"], mp2["TYPES"][1]["POS"] = [2], [1, 3, 4]
for nm, data in (("4tru", p), ("2loai", mp), ("2loai_tru2", mp2)):
    res = le.build(data) if "TYPES" in data else export.build(data)
    f = os.path.join(d, nm + "_tt.dxf")
    export.save_dxf(res, f)
    doc = ezdxf.readfile(f)
    msp = doc.modelspace()
    pt = [e for e in doc.blocks.get("TIM TRU") if e.dxftype() == "POINT"][0].dxf.location
    tt = {t.dxf.text: t for t in msp.query("TEXT") if t.dxf.layer == "TEN TRU"}
    assert sorted(tt) == ["M1", "M2", "M3", "M4"], sorted(tt)
    h_cot = [t.dxf.height for t in msp.query("TEXT") if t.dxf.layer == "COT"][0]
    fi = os.path.join(d, nm + ".ifc")
    ifc.export(data, fi)
    iq = ifc_quads(fi)
    bln = [(e.dxf.insert.x, e.dxf.insert.y) for e in msp.query("INSERT") if e.dxf.name == "BLN"]
    mains = [e for e in msp.query("LWPOLYLINE") if e.dxf.layer == "MAIN" and e.closed]
    for k in range(1, 5):
        t = tt[f"M{k}"]
        x, y = t.dxf.align_point.x, t.dxf.align_point.y
        q = (1 if x > pt.x else -1, 1 if y > pt.y else -1)
        assert q == ifc.QUAD[k] == iq[f"M{k}"][0], (nm, k, q, iq[f"M{k}"])        # cùng chân với khối IFC Mk
        assert t.dxf.height == h_cot and t.dxf.rotation == 0
        b = [e for e in bln if (1 if e[0] > pt.x else -1, 1 if e[1] > pt.y else -1) == q][0]
        assert abs(x - b[0]) > 0.25 or abs(y - b[1]) > 0.25                      # không đè block BLN

        def bx(e):
            xs, ys = zip(*[(v[0], v[1]) for v in e.get_points()])
            return min(xs), min(ys), max(xs), max(ys)
        pad = max((bx(e) for e in mains if bx(e)[0] < b[0] < bx(e)[2] and bx(e)[1] < b[1] < bx(e)[3]),
                  key=lambda r: r[2] - r[0])
        assert pad[0] < x < pad[2] and pad[1] < y < pad[3]                         # trong ô bản đế của chân đó
        if "TYPES" in data:                                                       # đúng loại móng
            ty = next(t_ for t_ in data["TYPES"] if k in t_["POS"])
            assert abs((pad[2] - pad[0]) - ty["B"]) < 1e-9 and iq[f"M{k}"][1].endswith(" - " + ty["NAME"]), (k, ty["NAME"])
    print(f"  {nm}: TEN TRU M1..M4 khớp IFC " + ", ".join(f"M{k}={iq[f'M{k}'][1].split(' - ')[-1]}" for k in range(1, 5)))
print("OK - mat bang 1:1 theo quy uoc")
