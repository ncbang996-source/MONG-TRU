"""Đối chiếu Excel khối lượng (công thức) với bảng thống kê thép và khối lượng bê tông / đất của chương trình.

Xuất _KL.xlsx cho nhiều bộ thông số, cho LibreOffice tính lại công thức (soffice --headless),
rồi so Ø, chiều dài, số lượng, khối lượng từng vị trí thép.   python tools/check_kl_excel.py [thư_mục_tạm]
"""
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import openpyxl  # noqa: E402

from mongtru import kl_excel, model  # noqa: E402
from mongtru.geom import Geo  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else tempfile.mkdtemp()
os.makedirs(OUT, exist_ok=True)
CASES = {"mau": {}, "b4": dict(B=4.0, BT=7.5), "lon": dict(B=5.5, BT=8.06, B1=1.2, B2=1.2, RC_N=32, RC_D=22, H1=4.0,
                                                             H2=1.0, HB=1.0, HV=0.4, RB_BOT_D=14, RB_TOP_D=14),
         "rc12": dict(RC_N=12), "rc28": dict(RC_N=28, B1=1.0, B2=1.0), "s150": dict(RB_BOT_S=150, RB_TOP_S=250),
         "ch500": dict(RB_CH_S=500), "nl1": dict(RL_N=1), "nl3": dict(RL_N=3), "hv": dict(HV=0.5, HB=0.9),
         "rc40": dict(RC_N=40, B1=1.4, B2=1.4, B=5.0, BT=6.0), "n8": dict(NPIER=8),
         # cổ móng vát
         "vat": dict(B=3.0, B2=1.2, BT=6.3, RC_N=32), "vat_lon": dict(B=4.5, B1=0.8, B2=1.6, BT=8.0, H1=3.0, H2=1.0,
                                                                          HB=0.9, HV=0.35, RC_N=24, RC_D=22),
         "vat_ho_chung": dict(B=3.0, B2=1.0, BT=3.6), "vat_rc12": dict(B2=1.0, RC_N=12)}
base, _ = model.read_excel(os.path.join(ROOT, "samples", "D112-30.xls"))
geos = {}
for nm, ov in CASES.items():
    p = dict(base)
    p.update({k: float(v) for k, v in ov.items()})
    assert model.validate(p) is None, (nm, model.validate(p))
    g = Geo(p)
    g.calc_kl()
    kl_excel.export(p, g, os.path.join(OUT, f"{nm}.xlsx"))
    geos[nm] = g
calc = os.path.join(OUT, "calc")
subprocess.run(["soffice", "--headless", "--calc", "--convert-to", "xlsx", "--outdir", calc] +
               [os.path.join(OUT, f"{nm}.xlsx") for nm in CASES], capture_output=True, timeout=900)
bad = 0
for nm, g in geos.items():
    ws = openpyxl.load_workbook(os.path.join(calc, f"{nm}.xlsx"), data_only=True)["KHOI LUONG"]
    rows = {}
    for r in range(1, ws.max_row + 1):
        b = ws.cell(r, 2).value
        if isinstance(b, str) and ws.cell(r, 9).value and isinstance(ws.cell(r, 5).value, (int, float)):
            rows[b.split(" - ")[0]] = [ws.cell(r, c).value for c in (3, 4, 5, 8)]
    for r in g.kl:
        ex = rows.get(r["name"])
        want = [int(r["dia"] + 0.5), r["len"], r["n"], r["kg"]]
        ok = ex is not None and ex[0] == want[0] and abs(ex[1] - want[1]) <= 0.6 and ex[2] == want[2] and \
            abs(ex[3] - want[3] * round(r["len"]) / r["len"]) <= max(0.05, 0.0005 * want[3])   # Excel làm tròn mm
        if not ok:
            bad += 1
            print(f"[{nm}] vị trí {r['pos']} {r['name']}: Excel {ex} - chương trình {[round(x, 2) for x in want]}")
    names = {r["name"] for r in g.kl}
    for k, v in rows.items():
        if k not in names and v[2] not in (0, None):
            bad += 1
            print(f"[{nm}] Excel có thêm {k}: {v}")
    tk = openpyxl.load_workbook(os.path.join(calc, f"{nm}.xlsx"), data_only=True)["TONG KE"]
    vals = {tk.cell(2, j).value: tk.cell(3, j).value for j in range(1, tk.max_column + 1)}
    p = g.p
    for key, v in ((f"{p['BTM']} (m³)", model.vol_mong(p)), (f"{p['BTL']} (m³)", model.vol_lot(p)),
                   ("Đào đất (m³)", model.vol_dao(p)), ("Đắp đất (m³)", model.vol_dap(p)),
                   ("Ván khuôn (m²)", model.area_vk(p)),
                   ("TỔNG K.LƯỢNG THÉP (kg)", sum(r["kg"] for r in g.kl) * g.dp())):
        if abs(vals.get(key, 1e9) - v) > max(0.01, 0.0005 * v):
            bad += 1
            print(f"[{nm}] {key}: Excel {vals.get(key)} - chương trình {v:.3f}")
# đổi Ø thanh chống ở THONG SO sang Ø14 (không có lúc xuất): phân loại có dòng Ø14, TONG KE báo xuất lại
src = os.path.join(OUT, "mau.xlsx")
wb = openpyxl.load_workbook(src)
ws = wb["THONG SO"]
for r in range(1, ws.max_row + 1):
    if ws.cell(r, 3).value == "dch":
        ws.cell(r, 4).value = 14
wb.save(os.path.join(OUT, "doi_d.xlsx"))
subprocess.run(["soffice", "--headless", "--calc", "--convert-to", "xlsx", "--outdir", calc,
                os.path.join(OUT, "doi_d.xlsx")], capture_output=True, timeout=300)
wb = openpyxl.load_workbook(os.path.join(calc, "doi_d.xlsx"), data_only=True)
kl = wb["KHOI LUONG"]
d14 = [kl.cell(r, 8).value for r in range(1, kl.max_row + 1) if kl.cell(r, 2).value == "Thép Ø14"]
msg = wb["TONG KE"].cell(6, 1).value
if not d14 or not d14[0] or msg != "Có đường kính mới - xuất lại file":
    bad += 1
    print("[doi_d] phân loại Ø14:", d14, "- cảnh báo TONG KE:", msg)
msg0 = openpyxl.load_workbook(os.path.join(calc, "mau.xlsx"), data_only=True)["TONG KE"].cell(6, 1).value
if msg0:
    bad += 1
    print("[mau] TONG KE báo sai:", msg0)
print("Số lỗi:", bad, "/", len(CASES) + 1, "bộ thông số")
sys.exit(1 if bad else 0)
