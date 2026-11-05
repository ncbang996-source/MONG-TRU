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
    res = build(data, frame_path, fields, offsets)
    stem = os.path.splitext(os.path.basename(path))[0]
    os.makedirs(outdir, exist_ok=True)
    done = []
    for k, _, ext in KINDS:
        if k not in kinds:
            continue
        f = os.path.join(outdir, stem + ext)
        if os.path.abspath(f) == os.path.abspath(path):
            raise ValueError("Không được ghi đè lên file Excel đầu vào.")
        write(res, k, f)
        done.append(f)
    out = _Done(done)
    out.warn = warn
    return out


class _Done(list):
    warn: list = []
