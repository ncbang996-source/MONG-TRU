"""Render bản vẽ ra ảnh PNG để xem nhanh (không cần giao diện).

    python tools/render_preview.py [file.xlsx] [KEY=VAL ...] [--out thư_mục]

KEY=VAL ghi đè thông số (vd RD_N=10 C=0); không có SCALE thì tự chọn tỷ lệ.
Ra s1.png, s2.png (130 dpi) và s1_hi.png, s2_hi.png (300 dpi) để cắt soi chi tiết.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import pymupdf  # noqa: E402

from mongtru import export, model  # noqa: E402

args = sys.argv[1:]
out = "."
if "--out" in args:
    i = args.index("--out")
    out = args[i + 1]
    del args[i:i + 2]
xls = args[0] if args and "=" not in args[0] else os.path.join(ROOT, "samples", "D112-30.xls")
p, _ = model.read_excel(xls)
for kv in [a for a in args if "=" in a]:
    k, v = kv.split("=", 1)
    p[k] = v if isinstance(p.get(k), str) else float(v)
if not any(a.startswith("SCALE=") for a in args):
    p["SCALE"] = model.auto_scale(p)
res = export.build(p, os.path.join(ROOT, "assets", "frames", "KT-A3.dxf"))
os.makedirs(out, exist_ok=True)
for i, pg in enumerate(pymupdf.open("pdf", export.pdf_bytes(res))):
    pg.get_pixmap(dpi=130).save(os.path.join(out, f"s{i + 1}.png"))
    pg.get_pixmap(dpi=300).save(os.path.join(out, f"s{i + 1}_hi.png"))
print("ok", len(res.origins), "tờ, tỷ lệ 1 /", res.geo.den, "- thép", round(sum(r["kg"] for r in res.geo.kl), 2), "kg")
