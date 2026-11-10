"""Xử lý hàng loạt: tìm file Excel trong thư mục dự án, đọc (4 trụ giống nhau / móng 2 loại), dựng bản vẽ và xuất
PDF, DXF, Excel khối lượng, IFC cho từng file - cùng cách đọc và cùng vị trí đã sắp xếp như khi mở từng file trong app."""
from __future__ import annotations

import os

from . import export, ifc, kl_excel, model
from .lech import export as lexport
from .lech import kl_excel as lkl
from .lech import model as lmodel

EXCEL_EXT = (".xls", ".xlsx", ".xlsm")
# loại file xuất: (khoá, tên, đuôi thêm vào tên file Excel)
KINDS = [("pdf", "PDF bản vẽ", ".pdf"), ("dxf", "AutoCAD DXF (kèm mặt bằng 1:1 đơn vị m)", ".dxf"),
         ("xlsx", "Excel khối lượng", "_KL.xlsx"), ("ifc", "Mô hình IFC (BIM)", ".ifc")]


def find_excel(folder, sub=False) -> list:
    """File Excel đầu vào trong thư mục (bỏ file khối lượng đã xuất *_KL.xlsx và file tạm ~$)."""
    out = []
    for root, dirs, files in os.walk(folder):
        dirs.sort()
        for f in sorted(files):
            lo = f.lower()
            if lo.endswith(EXCEL_EXT) and not f.startswith("~$") and not lo.endswith("_kl.xlsx"):
                out.append(os.path.join(root, f))
        if not sub:
            break
    return out


def load(path, base=None):
    """Đọc 1 file Excel như nút Mở Excel: (thông số, cảnh báo, móng 2 loại?). Số liệu sai -> ValueError."""
    try:
        return _load(path, base)
    except ValueError:
        raise
    except Exception as ex:
        raise ValueError(f"Không đọc được file Excel (không đúng mẫu sheet TONG HOP hoặc file hỏng: {ex})") from ex


def _load(path, base):
    if lmodel.detect(path):
        data, warn = lmodel.read_excel(path)
        err = lmodel.validate(data)
        if err:
            raise ValueError(err)
        data["SCALE"] = lmodel.auto_scale(data)
        return data, warn, True
    data, warn = model.read_excel(path, "TONG HOP", model.fresh_params(base or model.default_params()))
    err = model.validate(data)
    if err:
        raise ValueError(err)
    data["SCALE"] = model.auto_scale(data)
    return data, warn, False


def build(data, frame_path=None, fields=None, offsets=None):
    b = lexport.build if "TYPES" in data else export.build
    res = b(data, frame_path, fields, dict(offsets or {}))
    res.params = data
    return res


def write(res, kind, f, pdf=None):
    """Ghi 1 loại file từ bản vẽ đã dựng."""
    data = res.params
    if kind == "pdf":
        with open(f, "wb") as fh:
            fh.write(pdf if pdf is not None else export.pdf_bytes(res))
    elif kind == "dxf":
        export.save_dxf(res, f)
    elif kind == "xlsx":
        if "TYPES" in data:
            lkl.export(data, lexport.geos(data), f)
        else:
            kl_excel.export(data, res.geo, f)
    elif kind == "ifc":
        ifc.export(data, f)


def export_file(path, outdir, kinds, frame_path=None, fields=None, offsets=None, base=None) -> list:
    """Đọc 1 file Excel, dựng bản vẽ, ghi các loại file đã chọn vào outdir (tên = tên file Excel + đuôi).
    Trả về danh sách file đã ghi (cảnh báo đọc Excel ở thuộc tính .warn)."""
    data, warn, _ = load(path, base)
    stem = os.path.splitext(os.path.basename(path))[0]
    done = []
    if not any(k in kinds for k, *_ in KINDS):          # chỉ lấy số liệu (khối lượng tổng hợp): không dựng bản vẽ
        out = _Done(done)
        out.warn, out.data = warn, data
        return out
    res = build(data, frame_path, fields, offsets)
    os.makedirs(outdir, exist_ok=True)
    for k, _, ext in KINDS:
        if k not in kinds:
            continue
        f = os.path.join(outdir, stem + ext)
        if os.path.abspath(f) == os.path.abspath(path):
            raise ValueError("Không được ghi đè lên file Excel đầu vào.")
        write(res, k, f)
        done.append(f)
    out = _Done(done)
    out.warn, out.data = warn, data
    return out


class _Done(list):
    warn: list = []
    data: dict = {}


# ---------------------------------------------------------------------------
# khối lượng tổng hợp phần móng của dự án (mỗi dòng 1 loại móng, tính cho 01 móng; dòng TỔNG nhân số lượng)
SUMMARY_NAME = "KL_TONG_HOP_PHAN_MONG.xlsx"


def summary_row(data) -> dict:
    """Khối lượng 01 móng (cả 4 trụ) - cùng số liệu bảng tổng kê tờ 1 (thép từng Ø đã gồm dự phòng)."""
    by = {}
    if "TYPES" in data:
        gs = lexport.geos(data)
        k = 1.0 + data.get("DP", 0.0) / 100.0
        m = lmodel
        bt, lot, dao, dap, vk, db = (m.vol_mong(data), m.vol_lot(data), m.vol_dao(data), m.vol_dap(data),
                                     m.area_vk(data), m.den_bu(data))
        hm = max(t["H1"] for t in data["TYPES"])
        name = data.get("TENMONG") or m.type_name(data)
        dia = sorted({model.bolt_dia(m.type_params(data, i)) for i in range(2)})
    else:
        from .geom import Geo
        gs = [Geo(data)]
        gs[0].calc_kl()
        k = gs[0].dp()
        bt, lot, dao, dap, vk, db = (model.vol_mong(data), model.vol_lot(data), model.vol_dao(data),
                                     model.vol_dap(data), model.area_vk(data), model.den_bu(data))
        hm = data["H1"]
        name = model.type_name(data)
        dia = [model.bolt_dia(data)]
    for g in gs:
        for d, _, w in g.klc:
            if w > 1e-6:
                by[int(d + 0.5)] = by.get(int(d + 0.5), 0.0) + w * k
    return {"cot": str(data.get("COT", "")), "mong": name, "btm": str(data.get("BTM", "")),
            "btl": str(data.get("BTL", "")), "bt": bt, "lot": lot, "steel": by,
            "bln": " + ".join(f"BLN M{d}" for d in dia), "dao": dao, "dap": dap, "vk": vk, "hm": hm,
            "db": db, "dp": data.get("DP", 0.0)}


def write_summary(rows, path):
    """rows: [(số lượng, summary_row)] -> file Excel theo mẫu KHỐI LƯỢNG PHẦN MÓNG (TÍNH CHO 01 MÓNG)."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter as L
    wb = Workbook()
    ws = wb.active
    ws.title = "KL PHAN MONG"
    btm = sorted({r["btm"] for _, r in rows}, key=str)
    btl = sorted({r["btl"] for _, r in rows}, key=str)
    dias = sorted({d for _, r in rows for d in r["steel"]})
    cols = [("TÊN CỘT", 14), ("TÊN MÓNG", 22), ("SỐ LƯỢNG", 9)]
    cols += [(f"{b}(m³)", 10) for b in btm] + [(f"{b}(m³)", 10) for b in btl]
    cols += [(f"Ø{d}(kg)", 10) for d in dias]
    cols += [("Tổng khối lượng (kg)", 11), ("Bulong neo", 12), ("Đào đất(m³)", 10), ("Đắp đất(m³)", 10),
             ("Ván khuôn(m²)", 11), ("Chiều sâu chôn móng (m)", 9), ("Dài (m)", 8), ("Rộng (m)", 8),
             ("Diện tích (m2)", 10)]
    n = len(cols)
    ci = {h: j for j, (h, _) in enumerate(cols, 1)}
    thin = Side(style="thin")
    box = Border(left=thin, right=thin, top=thin, bottom=thin)
    fn, fb = Font(name="Times New Roman", size=11), Font(name="Times New Roman", size=11, bold=True)
    ctr = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n)
    c = ws.cell(row=1, column=1, value="KHỐI LƯỢNG PHẦN MÓNG (TÍNH CHO 01 MÓNG)")
    c.font, c.alignment = Font(name="Times New Roman", size=14, bold=True), ctr
    c.fill = PatternFill("solid", fgColor="FFFF00")
    ws.row_dimensions[1].height = 26
    ws.row_dimensions[2].height = 66
    for j, (h, w) in enumerate(cols, 1):
        ws.column_dimensions[L(j)].width = w
        c = ws.cell(row=2, column=j, value=h)
        c.font, c.alignment, c.border = fb, ctr, box
    r0 = 3
    for i, (q, r) in enumerate(rows):
        y = r0 + i
        vals = {"TÊN CỘT": r["cot"], "TÊN MÓNG": r["mong"], "SỐ LƯỢNG": q,
                f"{r['btm']}(m³)": round(r["bt"], 2), f"{r['btl']}(m³)": round(r["lot"], 2),
                "Bulong neo": r["bln"], "Đào đất(m³)": round(r["dao"], 2), "Đắp đất(m³)": round(r["dap"], 2),
                "Ván khuôn(m²)": round(r["vk"], 2), "Chiều sâu chôn móng (m)": r["hm"],
                "Dài (m)": round(r["db"], 2), "Rộng (m)": round(r["db"], 2)}
        for d, w in r["steel"].items():
            vals[f"Ø{d}(kg)"] = round(w, 2)
        vals["Tổng khối lượng (kg)"] = round(sum(r["steel"].values()), 2)     # như bảng tổng kê tờ 1
        vals["Diện tích (m2)"] = f"={L(ci['Dài (m)'])}{y}*{L(ci['Rộng (m)'])}{y}"
        for j, (h, _) in enumerate(cols, 1):
            c = ws.cell(row=y, column=j, value=vals.get(h))
            c.font, c.border = fn, box
            c.alignment = Alignment(horizontal="left" if j <= 2 else "center", vertical="center")
            if j > 3 and h != "Bulong neo":
                c.number_format = "0.00"
    yt = r0 + len(rows)
    ws.merge_cells(start_row=yt, start_column=1, end_row=yt, end_column=2)
    ws.cell(row=yt, column=1, value="TỔNG")
    qa = f"$C${r0}:$C${yt - 1}"
    no_sum = {"TÊN CỘT", "TÊN MÓNG", "Bulong neo", "Chiều sâu chôn móng (m)", "Dài (m)", "Rộng (m)"}
    for j, (h, _) in enumerate(cols, 1):
        c = ws.cell(row=yt, column=j)
        if h == "SỐ LƯỢNG":
            c.value = f"=SUM({qa})"
        elif h not in no_sum and rows:
            c.value = f"=SUMPRODUCT({qa},{L(j)}{r0}:{L(j)}{yt - 1})"
            c.number_format = "0.00"
        c.font, c.border, c.alignment = fb, box, ctr
    ws.cell(row=yt + 2, column=1, value="Ghi chú: mỗi dòng là khối lượng cho 01 móng (4 trụ); dòng TỔNG = Σ (khối "
                                        "lượng 01 móng × số lượng). Diện tích = diện tích đền bù (bao 4 trụ, cách mép "
                                        "bê tông móng 0.5 m).").font = Font(name="Times New Roman", italic=True)
    dps = sorted({r["dp"] for _, r in rows if r["dp"] > 0})
    if dps:
        ws.cell(row=yt + 3, column=1, value="Khối lượng thép đã gồm " + ", ".join(f"{d:g}%" for d in dps)
                + " dự phòng.").font = Font(name="Times New Roman", italic=True)
    ws.freeze_panes = "D3"
    ws.page_setup.orientation = "landscape"
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    wb.save(path)
