"""Kiểm tra khung tên khác mẫu KT-A3: nhãn "TL:" / "TỜ:" có sẵn trong khung (ghi giá trị ngay sau nhãn), chữ giai đoạn
theo Excel, logo chọn từ file ảnh (PDF + DXF), font Roboto gọi theo họ trong MTEXT dùng font kèm chương trình."""
import copy
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import ezdxf  # noqa: E402
from ezdxf.enums import TextEntityAlignment as A  # noqa: E402

from mongtru import cad, export, frame, model  # noqa: E402

d = tempfile.mkdtemp()
# khung giả: nhãn căn giữa ô, có khoảng trắng chừa chỗ ghi giá trị (như khung NMĐG Hướng Phùng 7)
fd = ezdxf.new("R2018")
m = fd.modelspace()
m.add_lwpolyline([(20, 10), (410, 10), (410, 287), (20, 287)], close=True)
for s_, x, y in (("TL:       ", 342.2, 12.6), ("TỜ:       ", 357.8, 12.6), ("TKCS", 342.6, 18.1)):
    m.add_text(s_, height=2.0).set_placement((x, y), align=A.MIDDLE_CENTER)
m.add_mtext(r"{\fRoboto Condensed|b1|i0|c163|p2;NHÀ MÁY}", dxfattribs={"char_height": 2.5, "insert": (300, 45)})
fp = os.path.join(d, "khung.dxf")
fd.saveas(fp)

p, _ = model.read_excel(os.path.join(ROOT, "samples", "D112-30.xls"))
fl = copy.deepcopy(frame.DEFAULT_FIELDS)
fl["LOGO"] = {"file": frame.LOGO_BUILTIN, "rect": frame.DEFAULT_LOGO["rect"]}
for gd in ("TKBVTC", "TKCS"):
    r = export.build(dict(p, GD=gd), fp, fl)
    txt = [t.dxf.text for t in r.doc.modelspace().query("TEXT")]
    assert f"TL: 1/{r.geo.den}" in txt, txt                     # nhãn + giá trị, không đè nhãn
    assert any(t.startswith("TỜ: 1/") for t in txt), txt
    blk = [t.dxf.text.strip() for t in r.doc.blocks.get(frame.BLOCK).query("TEXT")]
    assert "TL:" not in blk and gd in blk and ("TKCS" not in blk or gd == "TKCS"), blk
    assert len(r.ole) == 1 and r.ole[0][4][:4] == b"\x89PNG"    # logo vào PDF
    export.pdf_bytes(r, only={0})
out = os.path.join(d, "out", "m.dxf")
os.makedirs(os.path.dirname(out))
export.save_dxf(r, out)
assert os.path.isfile(os.path.join(d, "out", "SEIAC_logo.png"))  # logo chép cạnh DXF, tham chiếu theo tên file
idefs = list(ezdxf.readfile(out).objects.query("IMAGEDEF"))
assert idefs and idefs[0].dxf.filename == "SEIAC_logo.png"
# khung KT-A3: ô TL / TỜ giữ vị trí cấu hình như cũ
r = export.build(p, os.path.join(ROOT, "assets", "frames", "KT-A3.dxf"))
assert not any(t.dxf.text.startswith("TL: ") and t.dxf.insert.x > 300 and t.dxf.insert.y < 20
               for t in r.doc.modelspace().query("TEXT"))
# MTEXT gọi font theo họ Roboto -> font tĩnh kèm chương trình
cad.init_fonts()
from ezdxf.fonts import fonts  # noqa: E402
for fam, w, want in (("Roboto Condensed", 700, cad.FONT_B), ("Roboto", 400, "Roboto-Regular.ttf"),
                     ("Roboto SemiBold", 400, "Roboto-Bold.ttf")):
    assert fonts.find_font_file_name(fonts.FontFace(family=fam, weight=w)) == want, fam
# PDF: chữ là chữ thật (chọn / sửa được), đúng chỗ; ô tỷ lệ, số tờ kéo dịch được
import pymupdf  # noqa: E402
r = export.build(p, fp, fl)
pg = pymupdf.open("pdf", export.pdf_bytes(r, only={0}))[0]
words = pg.get_text("words")
assert any(w[4] == "MẶT" for w in words) and any(w[4] == "1/100" or w[4].endswith("1/50") for w in words), words[:20]
ids = {o.id for o in r.objs[0]}
assert {"s1.tl", "s1.to"} <= ids, ids
pos = lambda r: [(t.dxf.insert.x, t.dxf.insert.y) for t in r.doc.modelspace().query("TEXT") if t.dxf.text.startswith("TL: ")][0]
(x0, y0), (x1, y1) = pos(r), pos(export.build(p, fp, fl, {"s1.tl": (4.0, 2.0)}))
assert abs(x1 - x0 - 4.0) < 1e-6 and abs(y1 - y0 - 2.0) < 1e-6
print("OK - khung ten")
