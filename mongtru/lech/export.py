"""Dựng bản vẽ móng 2 loại: tờ 1 (hình thức, tổng kê cả vị trí) + tờ cốt thép từng loại (vẽ như tờ 2 của bản
4 trụ giống nhau, thêm tờ bảng kích thước từng thanh khi không đủ chỗ). Xuất PDF / DXF dùng lại mongtru.export."""
from __future__ import annotations

from .. import cad, frame, model, sheet2
from ..cad import Ctx
from ..export import SHEET_DX, Result
from ..geom import Geo
from . import model as lm
from . import sheet1 as ls1


def geos(mp) -> list:
    out = []
    for i in range(2):
        p = lm.type_params(mp, i)
        g = Geo(p)
        g.calc_kl()
        g.no_s1 = True                       # không đưa bảng thống kê thép sang tờ 1
        out.append(g)
    return out


def sheet_plan(mp, gs) -> list:
    """Danh sách tờ: ("s1", None) | ("steel", i) | ("tables", i)."""
    out = [("s1", None)]
    if model.is_detail(mp):
        for i, g in enumerate(gs):
            out.append(("steel", i))
            if sheet2.need_sheet3(g):
                out.append(("tables", i))
    return out


def n_sheets(mp) -> int:
    return len(sheet_plan(mp, geos(mp)))


def title_values(mp, den, kind, i, sheet, nsheet) -> dict:
    ht = model.HT_NAMES[int(mp["HT"])]
    if kind == "s1":
        t1, t2 = f"HÌNH THỨC MÓNG CỘT {ht} {mp['COT']}", f"MÓNG {lm.type_name(mp)}"
    else:
        t = mp["TYPES"][i]
        pos = ", ".join(str(q) for q in t["POS"])
        t1 = f"CỐT THÉP MÓNG CỘT {ht} {mp['COT']}"
        t2 = f"MÓNG {len(t['POS'])}{t['NAME']} (VỊ TRÍ {pos})"
    return {"TEN1": t1.strip(), "TEN2": t2, "TL": f"1/{den}", "TO": f"{sheet}/{nsheet}",
            "MABV": mp.get("MABV", ""), "GD": mp.get("GD", "")}


def build(mp: dict, frame_path: str | None = None, fields: dict | None = None, offsets: dict | None = None) -> Result:
    from .. import _meta
    if not _meta.check(cad._SIG):
        raise RuntimeError("Tệp chương trình đã bị thay đổi.")
    err = lm.validate(mp)
    if err:
        raise ValueError(err)
    fields = fields or frame.DEFAULT_FIELDS
    doc, tags = frame.new_output_doc(frame_path, str(mp.get("GD", "")), fields)
    gs = geos(mp)
    plan = sheet_plan(mp, gs)
    nsheet = len(plan)
    msp = doc.modelspace()
    offsets = offsets or {}
    origins, handles, objs = [], [], []
    den1 = int(mp["SCALE"] + 0.5)
    tables_sheet = {i: j + 1 for j, (kind, i) in enumerate(plan) if kind == "tables"}
    for j, (kind, i) in enumerate(plan):
        ox = j * SHEET_DX
        origins.append((ox, 0.0))
        n0 = len(msp)
        den = den1 if kind == "s1" else sheet2.pier_den(gs[i])
        frame.place(doc, ox, 0.0, title_values(mp, den, kind, i, j + 1, nsheet), fields, tags)
        c = Ctx(doc, msp, ox, 0.0, den1, offsets, f"s{j + 1}")
        if kind == "s1":
            ls1.draw(c, mp, gs)
        elif kind == "steel":
            if i in tables_sheet:
                gs[i].tables_ref = f"{tables_sheet[i]}/{nsheet}"
            sheet2.draw(c, gs[i])
        else:
            sheet2.draw3(c, gs[i])
        handles.append({e.dxf.handle for e in list(msp)[n0:]})
        objs.append(c.objs)
    ole = frame.ole_images(frame_path) if frame_path else []
    return Result(doc, gs[0], origins, ole, handles, objs)
