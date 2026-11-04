"""Dựng bản vẽ (DXF trong bộ nhớ) và xuất PDF / DXF."""
from __future__ import annotations

from dataclasses import dataclass, field

from . import cad, frame, model, plan11, sheet1, sheet2
from .cad import Ctx
from .geom import Geo

SHEET_DX = 420.0
PAGE_W, PAGE_H = 420.0, 297.0


@dataclass
class Result:
    doc: object
    geo: Geo
    origins: list
    ole: list = field(default_factory=list)
    handles: list = field(default_factory=list)   # handle các đối tượng của từng tờ
    objs: list = field(default_factory=list)      # đối tượng dịch chuyển được của từng tờ


def title_values(p: dict, den: int, sheet: int, nsheet: int) -> dict:
    return {
        "TEN1": (f"HÌNH THỨC MÓNG CỘT {model.HT_NAMES[int(p['HT'])]} {p['COT']}" if sheet == 1 else
                 f"CỐT THÉP MÓNG CỘT {model.HT_NAMES[int(p['HT'])]} {p['COT']}").strip(),
        "TEN2": f"MÓNG {model.type_name(p)}",
        "TL": f"1/{den}",
        "TO": f"{sheet}/{nsheet}",
        "MABV": p.get("MABV", ""),
        "GD": p.get("GD", ""),
    }


def build(p: dict, frame_path: str | None = None, fields: dict | None = None, offsets: dict | None = None) -> Result:
    from . import _meta
    if not _meta.check(cad._SIG):
        raise RuntimeError("Tệp chương trình đã bị thay đổi.")
    err = model.validate(p)
    if err:
        raise ValueError(err)
    fields = fields or frame.DEFAULT_FIELDS
    doc, tags = frame.new_output_doc(frame_path, str(p.get("GD", "")), fields)
    g = Geo(p)
    g.calc_kl()
    detail = model.is_detail(p)
    s3 = detail and sheet2.need_sheet3(g)
    nsheet = 3 if s3 else 2 if detail else 1
    origins = [(0.0, 0.0)]
    msp = doc.modelspace()
    handles = []
    n0 = len(msp)
    offsets = offsets or {}
    c1 = Ctx(doc, msp, 0.0, 0.0, g.den, offsets, "s1")
    frame.place(doc, 0.0, 0.0, title_values(p, g.den, 1, nsheet), fields, tags, c1)
    sheet1.draw(c1, g)
    handles.append({e.dxf.handle for e in list(msp)[n0:]})
    objs = [c1.objs]
    if detail:
        origins.append((SHEET_DX, 0.0))
        n0 = len(msp)
        c2 = Ctx(doc, msp, SHEET_DX, 0.0, g.den, offsets, "s2")
        frame.place(doc, SHEET_DX, 0.0, title_values(p, sheet2.pier_den(g), 2, nsheet), fields, tags, c2)
        sheet2.draw(c2, g)
        handles.append({e.dxf.handle for e in list(msp)[n0:]})
        objs.append(c2.objs)
    if s3:
        origins.append((2 * SHEET_DX, 0.0))
        n0 = len(msp)
        c3 = Ctx(doc, msp, 2 * SHEET_DX, 0.0, g.den, offsets, "s3")
        frame.place(doc, 2 * SHEET_DX, 0.0, title_values(p, sheet2.pier_den(g), 3, nsheet), fields, tags, c3)
        sheet2.draw3(c3, g)
        handles.append({e.dxf.handle for e in list(msp)[n0:]})
        objs.append(c3.objs)
    plan11.draw(doc, p)                       # mặt bằng 1:1 (m) cho CAD - ngoài các tờ, không in PDF
    ole = frame.pdf_images(frame_path, fields)
    return Result(doc, g, origins, ole, handles, objs)


def save_dxf(res: Result, path: str):
    # logo (IMAGE tham chiếu file ngoài): chép ảnh cạnh file DXF, tham chiếu theo tên file (AutoCAD tìm cùng thư mục)
    import os
    import shutil
    keep = []
    for idef in res.doc.objects.query("IMAGEDEF"):
        src = idef.dxf.filename
        if os.path.isabs(src) and os.path.isfile(src):
            dst = os.path.join(os.path.dirname(os.path.abspath(path)), os.path.basename(src))
            if os.path.abspath(dst) != os.path.abspath(src):
                shutil.copyfile(src, dst)
            keep.append((idef, src))
            idef.dxf.filename = os.path.basename(src)
    try:
        res.doc.saveas(path)
    finally:
        for idef, src in keep:
            idef.dxf.filename = src


def _capture_text(fe) -> list:
    """Chữ (TEXT, MTEXT, chữ kích thước, attribute) không vẽ thành nét: ghi lại dòng chữ sau khi ezdxf đã dàn trang
    (vị trí, góc xoay, hệ số rộng, font) để ghi thành chữ thật trong PDF. Font nét (SHX) vẫn vẽ nét."""
    import unicodedata

    from ezdxf.addons.drawing.pipeline import prepare_string_for_rendering
    from ezdxf.fonts.fonts import FontRenderType
    pl = fe.pipeline
    orig = pl.draw_text
    out = []

    def draw_text(text, transform, properties, cap_height, dxftype="TEXT"):
        if not text.strip():
            return
        ff = properties.font or pl.default_font_face
        try:
            font = pl.text_engine.get_font(ff)
            path = _font_path(font.name)
        except Exception:
            path = None
        if not path or font.font_render_type != FontRenderType.OUTLINE:
            return orig(text, transform, properties, cap_height, dxftype)
        # chữ tổ hợp (A + dấu rời, vd khung tên) -> dựng sẵn: PDF không ghép dấu rời
        out.append((unicodedata.normalize("NFC", prepare_string_for_rendering(text, dxftype)), transform, font,
                    path, cap_height))
    pl.draw_text = draw_text
    return out


def _font_path(name):
    import os
    from ezdxf.fonts import fonts
    try:
        p = str(fonts.font_manager._font_cache.get(name, cad.FONT_R).file_path)
    except Exception:
        return None
    return p if os.path.isfile(p) and p.lower().endswith((".ttf", ".otf")) else None


def _write_text(pg, texts, ox, oy):
    """Ghi chữ thật (chọn, tìm, sửa được) đúng chỗ ezdxf đã dàn: cỡ chữ khớp bề rộng dòng theo font ezdxf, ma trận
    = hệ số rộng + góc xoay của chữ."""
    import pymupdf
    k = 72.0 / 25.4
    names, fobj = {}, {}
    for text, m, font, path, ch in texts:
        if path not in names:
            names[path] = f"F{len(names)}"
            pg.insert_font(fontname=names[path], fontfile=path)
            fobj[path] = pymupdf.Font(fontfile=path)
        w0 = font.text_width_ex(text, ch, 1.0)
        l1 = fobj[path].text_length(text, fontsize=1.0)
        if w0 <= 0 or l1 <= 0:
            continue
        fs = w0 * k / l1
        o = m.transform((0, 0, 0))
        ex, ey = m.transform_direction((1, 0, 0)), m.transform_direction((0, 1, 0))
        p0 = pymupdf.Point((o.x - ox) * k, (PAGE_H - (o.y - oy)) * k)
        mat = pymupdf.Matrix(ex.x, ex.y, ey.x, ey.y, 0, 0)        # morph tính theo hệ PDF gốc (y lên)
        pg.insert_text(p0, text, fontsize=fs, fontname=names[path], morph=(p0, mat))


def pdf_bytes(res: Result, only=None, real_text=True) -> bytes:
    """Mỗi tờ 1 trang A3 ngang, tỷ lệ 1:1, nét theo layer, chữ Roboto (chữ thật, sửa được), kèm logo OLE."""
    import pymupdf
    from ezdxf.addons.drawing import Frontend, RenderContext, config, layout
    from ezdxf.addons.drawing import pymupdf as pmb
    from ezdxf.math import BoundingBox2d

    cad.init_fonts()
    cfg = config.Configuration(
        lineweight_policy=config.LineweightPolicy.ABSOLUTE,
        color_policy=config.ColorPolicy.BLACK,
        background_policy=config.BackgroundPolicy.WHITE,
        min_lineweight=0.05,
        hatch_policy=config.HatchPolicy.NORMAL,
    )
    out = pymupdf.open()
    msp = res.doc.modelspace()
    for i, (ox, oy) in enumerate(res.origins):
        if only is not None and i not in only:
            continue
        ctx = RenderContext(res.doc)
        be = pmb.PyMuPdfBackend()
        hs = res.handles[i] if i < len(res.handles) else None
        # IMAGE (logo) không vẽ qua ezdxf: ảnh chèn thẳng vào PDF (res.ole)
        flt = (lambda e, hs=hs: e.dxf.handle in hs and e.dxftype() != "IMAGE") if hs else \
            (lambda e: e.dxftype() != "IMAGE")
        fe = Frontend(ctx, be, config=cfg)
        texts = _capture_text(fe) if real_text else None
        fe.draw_layout(msp, finalize=True, filter_func=flt)
        page = layout.Page(PAGE_W, PAGE_H, layout.Units.mm, margins=layout.Margins.all(0))
        data = be.get_pdf_bytes(page, settings=layout.Settings(fit_page=False, scale=1.0),
                                render_box=BoundingBox2d([(ox, oy), (ox + PAGE_W, oy + PAGE_H)]))
        src = pymupdf.open("pdf", data)
        out.insert_pdf(src)
        pg = out[-1]
        mm = 72.0 / 25.4
        for x0, y0, x1, y1, png in res.ole:
            r = pymupdf.Rect(x0 * mm, (PAGE_H - y1) * mm, x1 * mm, (PAGE_H - y0) * mm)
            pg.insert_image(r, stream=png, keep_proportion=True)
        if texts:
            _write_text(pg, texts, ox, oy)
    if real_text:
        out.subset_fonts()
    data = out.tobytes(garbage=3, deflate=True)
    out.close()
    return data


def save_pdf(res: Result, path: str):
    with open(path, "wb") as f:
        f.write(pdf_bytes(res))
