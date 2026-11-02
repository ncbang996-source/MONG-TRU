"""Khung tên: nạp file DXF, chuyển thành block, điền thông tin (attribute hoặc toạ độ cố định), trích logo OLE."""
from __future__ import annotations

import io
import os
import struct

import ezdxf

from . import cad

BLOCK = "KHUNG_TEN"
STAGE_WORDS = {"TKCS", "TKBVTC", "TKKT", "BVTC", "TKTC"}

# Vị trí các ô điền thông tin (toạ độ trong khung, mm) - mặc định theo khung KT-A3 (SEIAC)
DEFAULT_FIELDS = {
    "TEN1": {"x": 372.2, "y": 27.3, "h": 2.0, "align": "MC", "wmax": 72.0, "bold": False,
             "box": [334.7, 20.0, 409.6, 31.0]},
    "TEN2": {"x": 372.2, "y": 22.6, "h": 2.5, "align": "MC", "wmax": 72.0, "bold": False, "box": None},
    "TL":   {"x": 340.4, "y": 11.0, "h": 2.0, "align": "L", "wmax": 9.0, "bold": False, "box": None},
    "TO":   {"x": 357.4, "y": 11.0, "h": 2.0, "align": "L", "wmax": 7.0, "bold": False, "box": None},
    "MABV": {"x": 387.2, "y": 15.0, "h": 2.5, "align": "MC", "wmax": 43.0, "bold": True,
             "box": [364.7, 10.0, 409.6, 20.0]},
}
# Logo chọn từ file ảnh (khung có logo OLE nhưng file DXF không lưu dữ liệu ảnh): ô đặt logo (x0, y0, x1, y1) mm,
# ảnh giữ tỷ lệ, căn giữa ô. Mặc định: chỗ logo SEIAC của khung A3 SEIAC (KT-A3 dời theo khung NMĐG Hướng Phùng 7:
# khung lệch +0.3 / +0.5 mm), cùng cỡ 27.4 x 7.0 mm như OLE trống trong khung. "<SEIAC>" = logo kèm chương trình
# (trích từ OLE của KT-A3).
LOGO_BUILTIN = "<SEIAC>"
DEFAULT_LOGO = {"file": "", "rect": [265.2, 39.4, 292.6, 46.4]}
FIELD_LABELS = {"TEN1": "Tên bản vẽ (dòng 1)", "TEN2": "Tên bản vẽ (dòng 2)", "TL": "Tỷ lệ",
                "TO": "Tờ", "MABV": "Mã số bản vẽ"}
# tag attribute được nhận theo các tên thường gặp
TAG_SYNONYMS = {
    "TEN1": {"TEN1", "TENBV", "TENBV1", "TEN_BV", "TEN_BAN_VE", "TITLE", "TITLE1"},
    "TEN2": {"TEN2", "TENBV2", "TITLE2"},
    "TL": {"TL", "TYLE", "TY_LE", "SCALE"},
    "TO": {"TO", "SOTO", "SO_TO", "SHEET", "TO_SO"},
    "MABV": {"MABV", "MASO", "MA_SO", "MA_BV", "DWGNO", "DRAWING_NO", "SOBV"},
    "GD": {"GD", "GIAIDOAN", "GIAI_DOAN", "STAGE"},
}


_ole_cache: dict = {}


def ole_images(path: str):
    """Trả về danh sách (x0, y0, x1, y1, png_bytes) cho các OLE2FRAME chứa ảnh bitmap."""
    try:
        key = (os.path.abspath(path), os.path.getmtime(path))
    except OSError:
        return []
    if key not in _ole_cache:
        _ole_cache[key] = _ole_images(path)
    return _ole_cache[key]


def _ole_images(path: str):
    out = []
    try:
        doc = ezdxf.readfile(path)
    except Exception:
        return out
    for e in doc.modelspace().query("OLE2FRAME"):
        try:
            tags = e.acdb_ole2frame
            p1 = p2 = None
            chunks = []
            for t in tags:
                if t.code == 10:
                    p1 = t.value
                elif t.code == 11:
                    p2 = t.value
                elif t.code == 310:
                    chunks.append(t.value)
            png = _dib_to_png(b"".join(chunks))
            if png and p1 and p2:
                out.append((min(p1[0], p2[0]), min(p1[1], p2[1]), max(p1[0], p2[0]), max(p1[1], p2[1]), png))
        except Exception:
            continue
    return out


def _dib_to_png(data: bytes):
    from PIL import Image
    i = 0
    while True:
        i = data.find(b"\x28\x00\x00\x00", i)
        if i < 0:
            return None
        w, h, planes, bpp = struct.unpack("<iiHH", data[i + 4:i + 16])
        if planes == 1 and bpp in (1, 4, 8, 24, 32) and 0 < w < 20000 and 0 < abs(h) < 20000:
            comp = struct.unpack("<I", data[i + 16:i + 20])[0]
            ncol = struct.unpack("<I", data[i + 32:i + 36])[0] or ((1 << bpp) if bpp <= 8 else 0)
            if comp == 3:
                ncol = 3
            rowsz = ((w * bpp + 31) // 32) * 4
            size = 40 + ncol * 4 + rowsz * abs(h)
            if i + size <= len(data):
                bmp = b"BM" + struct.pack("<IHHI", 14 + size, 0, 0, 14 + 40 + ncol * 4) + data[i:i + size]
                try:
                    im = Image.open(io.BytesIO(bmp)).convert("RGB")
                    buf = io.BytesIO()
                    im.save(buf, "PNG")
                    return buf.getvalue()
                except Exception:
                    pass
        i += 1


def _fix_fonts(doc):
    """Kiểu chữ dùng font không có trên máy -> Roboto tương ứng."""
    from ezdxf.fonts import fonts
    cad.init_fonts()
    for st in doc.styles:
        f = (st.dxf.get("font") or "").strip()
        if not f:
            continue
        try:
            ok = fonts.font_manager.has_font(f)
        except Exception:
            ok = False
        if not ok:
            st.dxf.font = cad.FONT_R


def setup_doc(doc):
    """Thêm layer, kiểu chữ, linetype trục vào 1 document có sẵn."""
    cad.init_fonts()
    doc.header["$INSUNITS"] = 4
    doc.header["$MEASUREMENT"] = 1
    doc.header["$LWDISPLAY"] = 1
    if "MB_CENTER" not in doc.linetypes:
        doc.linetypes.add("MB_CENTER", pattern=[5.9, 4.0, -0.8, 0.3, -0.8], description="Truc ____ . ____ .")
    cad.ensure_styles(doc)
    for name, (col, lt, lw) in cad.LAYERS.items():
        ltn = "MB_CENTER" if lt == "CENTER" else "CONTINUOUS"
        if name in doc.layers:
            la = doc.layers.get(name)
            la.dxf.color, la.dxf.linetype, la.dxf.lineweight = col, ltn, lw
        else:
            doc.layers.add(name, color=col, linetype=ltn, lineweight=lw)
    if "KHUNG" not in doc.layers:
        doc.layers.add("KHUNG", color=7, lineweight=35)
    _fix_fonts(doc)


def new_output_doc(frame_path: str | None, stage: str, fields: dict | None = None):
    """Tạo document xuất: nếu có khung tên thì dùng chính file khung (giữ OLE, block chữ ký...)."""
    has_frame = bool(frame_path and os.path.isfile(frame_path))
    if has_frame:
        doc = ezdxf.readfile(frame_path)
        setup_doc(doc)
        msp = doc.modelspace()
        blk = doc.blocks.new(BLOCK) if BLOCK not in doc.blocks else doc.blocks.get(BLOCK)
        for e in list(msp):
            msp.move_to_layout(e, blk)
        boxes = [f["box"] for f in (fields or DEFAULT_FIELDS).values() if f.get("box")]
        for e in list(blk):
            if e.dxftype() in ("TEXT", "MTEXT"):
                pt = e.dxf.insert
                if e.dxftype() == "TEXT" and e.dxf.halign + e.dxf.valign and e.dxf.hasattr("align_point"):
                    pt = e.dxf.align_point
                if any(b[0] <= pt.x <= b[2] and b[1] <= pt.y <= b[3] for b in boxes):
                    blk.delete_entity(e)      # chữ cũ trong ô sẽ điền lại
        tags = Tags()
        _auto_labels(doc, blk, fields or DEFAULT_FIELDS, tags)
        for e in blk:
            if e.dxftype() == "TEXT" and e.dxf.text.strip().upper() in STAGE_WORDS:
                e.dxf.text = stage
            elif e.dxftype() == "ATTDEF":
                tags.add(e.dxf.tag.upper())
        _add_logo(doc, fields, tags)
        return doc, tags
    doc = ezdxf.new("R2018", setup=True, units=4)
    setup_doc(doc)
    blk = doc.blocks.new(BLOCK)
    _simple_frame(blk)
    tags = Tags()
    _add_logo(doc, fields, tags)
    return doc, tags


def _add_logo(doc, fields, tags):
    lg = logo_png(fields)
    if lg:
        tags.logo = (doc.add_image_def(filename=lg[3], size_in_pixel=(lg[1], lg[2])), logo_rect(fields, lg[1], lg[2]))


def logo_cfg(fields) -> dict:
    return {**DEFAULT_LOGO, **((fields or {}).get("LOGO") or {})}


_logo_cache: dict = {}


def logo_png(fields):
    """(png, w_px, h_px, đường dẫn) của logo đã chọn, None nếu không có / không đọc được."""
    f = logo_cfg(fields).get("file") or ""
    if f == LOGO_BUILTIN:
        f = os.path.join(cad.resource_dir(), "frames", "SEIAC_logo.png")
    try:
        key = (os.path.abspath(f), os.path.getmtime(f))
    except OSError:
        return None
    if key not in _logo_cache:
        from PIL import Image
        try:
            im = Image.open(f)
            im.load()
            buf = io.BytesIO()
            im.convert("RGBA").save(buf, "PNG")
            _logo_cache[key] = (buf.getvalue(), im.width, im.height, os.path.abspath(f))
        except Exception:
            _logo_cache[key] = None
    return _logo_cache[key]


def logo_rect(fields, wpx, hpx):
    """Ô đặt logo thu theo tỷ lệ ảnh, căn giữa: (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = (float(v) for v in logo_cfg(fields)["rect"])
    w, h = abs(x1 - x0), abs(y1 - y0)
    x0, y0 = min(x0, x1), min(y0, y1)
    k = min(w / wpx, h / hpx)
    dw, dh = wpx * k, hpx * k
    xa, ya = x0 + (w - dw) / 2, y0 + (h - dh) / 2
    return xa, ya, xa + dw, ya + dh


def pdf_images(frame_path, fields) -> list:
    """Ảnh chèn vào PDF (toạ độ trong khung): logo OLE của khung + logo chọn từ file ảnh."""
    out = list(ole_images(frame_path)) if frame_path else []
    lg = logo_png(fields)
    if lg:
        out.append((*logo_rect(fields, lg[1], lg[2]), lg[0]))
    return out


class Tags(set):
    """Tag attribute của khung + ô tự đặt theo nhãn có sẵn trong khung (auto: ô -> cấu hình chữ)."""

    def __init__(self, *a):
        super().__init__(*a)
        self.auto = {}
        self.logo = None                                   # (image def, (x0, y0, x1, y1)) -> IMAGE trong DXF


LABELS = {"TL": ("TL:", "TỶ LỆ:"), "TO": ("TỜ:", "TỜ SỐ:")}


def _auto_labels(doc, blk, fields, tags):
    """Khung có chữ nhãn "TL:" / "TỜ:" mà vị trí ô cấu hình đè lên nhãn (khung khác mẫu KT-A3): bỏ nhãn trong khung,
    mỗi tờ ghi lại "nhãn + giá trị" ngay sau nhãn, cùng kiểu chữ, cao chữ, đường chân chữ."""
    from ezdxf.fonts import fonts as ff
    for e in list(blk):
        if e.dxftype() != "TEXT":
            continue
        raw = e.dxf.text
        lab = raw.strip()
        key = next((k for k, v in LABELS.items() if lab.upper() in v), None)
        cfg = fields.get(key) if key else None
        if not cfg:
            continue
        h = float(e.dxf.height)
        st = e.dxf.get("style", "Standard")
        wf = float(e.dxf.get("width", 1.0) or 1.0)
        try:
            sty = doc.styles.get(st)
            font = ff.make_font(sty.dxf.font or cad.FONT_R, h)
            if not e.dxf.hasattr("width") and sty.dxf.width:
                wf = float(sty.dxf.width)
        except Exception:
            font = ff.make_font(cad.FONT_R, h)
        wfull = font.text_width(raw) * wf
        wlab = font.text_width(lab) * wf
        ha = e.dxf.get("halign", 0)
        if ha in (1, 4) and e.dxf.hasattr("align_point"):
            x0 = e.dxf.align_point.x - wfull / 2
        elif ha == 2 and e.dxf.hasattr("align_point"):
            x0 = e.dxf.align_point.x - wfull
        else:
            x0 = e.dxf.insert.x
        lead = raw[:len(raw) - len(raw.lstrip())]
        x0 += font.text_width(lead) * wf if lead else 0.0
        x1 = x0 + wlab
        if not (x0 - 0.5 <= float(cfg["x"]) <= x1 + 0.3):
            continue                                   # ô cấu hình nằm sau nhãn: giữ như cũ
        tags.auto[key] = {"x": x0, "y": e.dxf.insert.y, "h": h, "style": st, "width": wf, "layer": e.dxf.layer,
                          "label": raw.rstrip() + " "}
        blk.delete_entity(e)


def _simple_frame(blk):
    """Khung A3 đơn giản khi chưa nạp khung tên."""
    a = {"layer": "KHUNG"}
    blk.add_lwpolyline([(20, 10), (409.6, 10), (409.6, 286.7), (20, 286.7)], close=True, dxfattribs=a)
    blk.add_lwpolyline([(264.8, 10), (409.6, 10), (409.6, 50), (264.8, 50)], close=True, dxfattribs=a)
    for y in (20, 35):
        blk.add_line((264.8, y), (409.6, y), dxfattribs=a)
    for x in (334.7, 364.7):
        blk.add_line((x, 10), (x, 35 if x == 334.7 else 20), dxfattribs=a)
    blk.add_line((349.7, 10), (349.7, 20), dxfattribs=a)
    blk.add_line((334.7, 15), (364.7, 15), dxfattribs=a)
    for s_, x, y in (("TÊN BẢN VẼ:", 336.0, 31.4), ("TL:", 336.0, 11.0), ("TỜ:", 351.0, 11.0)):
        t = blk.add_text(s_, height=2.0, dxfattribs={"layer": "KHUNG", "style": cad.STYLE, "width": cad.WIDTH})
        t.set_placement((x, y))


def match_tag(tags, field):
    for t in tags:
        if t in TAG_SYNONYMS.get(field, {field}):
            return t
    return None


MOVABLE = {"TL": "Tỷ lệ (khung tên)", "TO": "Số tờ (khung tên)"}


def _movable(c, f, x, y, w, h, align):
    """Ô TL / TỜ: 1 đối tượng kéo được trên tờ (Ctx c, toạ độ trong khung) -> điểm đặt chữ đã cộng offset."""
    if c is None or f not in MOVABLE:
        return None
    x0 = x - {"L": 0.0, "C": w / 2, "MC": w / 2, "R": w}.get(align, 0.0)
    y0 = y - (h / 2 if align == "MC" else 0.0)
    with c.item(f.lower(), MOVABLE[f]):
        c.wp(x0, y0 - 0.3 * h)
        c.wp(x0 + w, y0 + h)
        return c.wp(x, y)


def place(doc, ox, oy, values: dict, fields: dict, tags: set, c=None):
    """Chèn khung tên tại (ox, oy) và điền thông tin. c: Ctx của tờ -> ô tỷ lệ, số tờ kéo dịch được."""
    msp = doc.modelspace()
    ins = msp.add_blockref(BLOCK, (ox, oy), dxfattribs={"layer": "0"})
    if tags:
        av = {}
        for f, v in values.items():
            t = match_tag(tags, f)
            if t:
                av[t] = v
        ins.add_auto_attribs(av)
    if getattr(tags, "logo", None):
        idef, (x0, y0, x1, y1) = tags.logo
        msp.add_image(idef, (ox + x0, oy + y0), (x1 - x0, y1 - y0), dxfattribs={"layer": "KHUNG"})
    done = {f for f in values if tags and match_tag(tags, f)}
    for f, a in getattr(tags, "auto", {}).items():
        if f in values and f not in done:
            s_ = a["label"] + str(values[f])
            t = msp.add_text(s_, height=a["h"],
                             dxfattribs={"layer": a["layer"], "style": a["style"], "width": a["width"]})
            w = cad.txtw(s_, a["h"]) * a["width"] / cad.WIDTH
            t.set_placement(_movable(c, f, a["x"], a["y"], w, a["h"], "L") or (ox + a["x"], oy + a["y"]))
            done.add(f)
    for f, v in values.items():
        if f in done or f not in fields or not v:
            continue
        cfg = fields[f]
        h = float(cfg.get("h", 2.0))
        bold = bool(cfg.get("bold"))
        w = cad.txtw(v, h, bold)
        wmax = float(cfg.get("wmax", 0) or 0)
        if wmax and w > wmax:
            h *= wmax / w
            w = wmax
        from ezdxf.enums import TextEntityAlignment as A
        ak = cfg.get("align", "L")
        al = {"MC": A.MIDDLE_CENTER, "L": A.LEFT, "C": A.CENTER, "R": A.RIGHT}.get(ak, A.LEFT)
        t = msp.add_text(v, height=h, dxfattribs={"layer": "CHU", "style": cad.STYLE_B if bold else cad.STYLE, "width": cad.WIDTH})
        x, y = float(cfg["x"]), float(cfg["y"])
        t.set_placement(_movable(c, f, x, y, w, h, ak) or (ox + x, oy + y), align=al)
    return ins
