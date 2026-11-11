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
# khối lượng tổng hợp phần móng: mỗi dòng = bảng tổng kê tờ 1 (01 móng), dòng TỔNG nhân số lượng
import openpyxl  # noqa: E402
from mongtru import tables  # noqa: E402
from mongtru.geom import Geo  # noqa: E402
from mongtru.lech import export as le  # noqa: E402
from mongtru.lech import sheet1 as ls1  # noqa: E402
rows = []
for f, q in ((fs[0], 4), (fs[1], 1)):
    data, _, mix = batch.load(f)
    r = batch.summary_row(data)
    if mix:
        cols = ls1.summary_cols(data, le.geos(data))
    else:
        g = Geo(data)
        g.calc_kl()
        cols = tables.summary_cols(g)
    sh = {c[0]: float(c[3]) for c in cols if c[0] != "BULONG"}
    assert abs(sh[data["BTM"]] - r["bt"]) < 0.006 and abs(sh[data["BTL"]] - r["lot"]) < 0.006
    assert all(abs(sh[f"%%C{d}"] - w) < 0.006 for d, w in r["steel"].items()), (sh, r["steel"])
    assert abs(sh["TỔNG K.LƯỢNG"] - sum(r["steel"].values())) < 0.006
    rows.append((q, r))
fk = os.path.join(out, batch.SUMMARY_NAME)
batch.write_summary(rows, fk)
ws = openpyxl.load_workbook(fk).active
hd = [c.value for c in ws[2]]
assert hd[:3] == ["TÊN CỘT", "TÊN MÓNG", "SỐ LƯỢNG"] and "Ø8(kg)" in hd and hd[-3:] == ["Dài (m)", "Rộng (m)",
                                                                                        "Diện tích (m2)"], hd
assert [ws.cell(row=3, column=1).value, ws.cell(row=3, column=3).value] == ["D112-30", 4]
assert ws.cell(row=5, column=1).value == "TỔNG" and ws.cell(row=5, column=3).value == "=SUM($C$3:$C$4)"
assert ws.cell(row=5, column=4).value == "=SUMPRODUCT($C$3:$C$4,D3:D4)"
# file dự án *.mongtru: lưu đường dẫn tương đối + số lượng; chép cả thư mục sang chỗ khác vẫn mở được
pf = os.path.join(d, "DU_AN" + batch.PROJECT_EXT)
batch.save_project(pf, [fs[0], fs[1], fs[3]], {os.path.abspath(fs[0]): 4, os.path.abspath(fs[3]): 2}, 1)
d2 = d + "_copy"
shutil.copytree(d, d2)
lf, lq, cur, miss = batch.load_project(os.path.join(d2, "DU_AN" + batch.PROJECT_EXT))
assert [os.path.relpath(f, d2) for f in lf] == [os.path.relpath(f, d) for f in (fs[0], fs[1], fs[3])] and not miss
assert [lq[f] for f in lf] == [4, 1, 2] and cur == 1 and all(f.startswith(d2) for f in lf)
os.remove(os.path.join(d2, "D112-30.xls"))
lf, lq, cur, miss = batch.load_project(os.path.join(d2, "DU_AN" + batch.PROJECT_EXT))
assert len(lf) == 2 and len(miss) == 1                                    # file thiếu: bỏ qua, báo lại
open(os.path.join(d, "sai.mongtru"), "w").write("{}")
try:
    batch.load_project(os.path.join(d, "sai.mongtru"))
    raise AssertionError("file dự án sai phải báo lỗi")
except ValueError:
    pass
print("OK - xuat dong loat")
