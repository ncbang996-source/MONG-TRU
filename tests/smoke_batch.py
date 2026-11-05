"""Kiểm tra xuất đồng loạt (mongtru.batch): tìm file Excel trong thư mục dự án (cả thư mục con), xuất PDF / DXF /
Excel khối lượng / IFC cho từng file, file hỏng báo lỗi rõ ràng, không ghi đè file đầu vào."""
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from mongtru import batch  # noqa: E402

d = tempfile.mkdtemp()
sm = os.path.join(ROOT, "samples")
for f in ("D112-30.xls", "N112-52(60) - 3T-1T.xls"):
    shutil.copy(os.path.join(sm, f), d)
os.makedirs(os.path.join(d, "TUYEN2"))
shutil.copy(os.path.join(sm, "N112-30(60).xls"), os.path.join(d, "TUYEN2", "VT15.xls"))
open(os.path.join(d, "hong.xlsx"), "w").write("rac")
open(os.path.join(d, "~$D112-30.xls"), "w").write("tam")
open(os.path.join(d, "D112-30_KL.xlsx"), "w").write("kl")
fs = batch.find_excel(d)
assert [os.path.basename(f) for f in fs] == ["D112-30.xls", "N112-52(60) - 3T-1T.xls", "hong.xlsx"], fs
fs = batch.find_excel(d, sub=True)
assert len(fs) == 4 and fs[-1].endswith(os.path.join("TUYEN2", "VT15.xls")), fs
out = os.path.join(d, "XUAT")
kinds = [k for k, *_ in batch.KINDS]
for f in fs:
    if f.endswith("hong.xlsx"):
        try:
            batch.export_file(f, out, kinds)
            raise AssertionError("file hỏng phải báo lỗi")
        except ValueError as ex:
            assert "Không đọc được file Excel" in str(ex), ex
        continue
    sub = os.path.relpath(os.path.dirname(f), d)
    r = batch.export_file(f, os.path.join(out, sub), kinds)
    stem = os.path.splitext(os.path.basename(f))[0]
    want = {stem + ".pdf", stem + ".dxf", stem + "_KL.xlsx", stem + ".ifc"}
    assert {os.path.basename(x) for x in r} == want and all(os.path.getsize(x) > 1000 for x in r), r
    print(f"  {os.path.relpath(f, d)}: {len(r)} file" + (f", cảnh báo: {r.warn}" if r.warn else ""))
# chỉ PDF + IFC; không ghi đè file Excel đầu vào khi thư mục xuất = thư mục dự án
r = batch.export_file(fs[0], d, ["pdf", "ifc"])
assert len(r) == 2 and os.path.isfile(fs[0])
print("OK - xuat dong loat")
