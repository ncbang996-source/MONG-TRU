"""Mặt bằng móng tỷ lệ 1:1, đơn vị mét (1 đơn vị bản vẽ = 1 m) trong file DXF - để chép sang bản vẽ tổng mặt bằng /
định vị. Kích thước thật (không rút ngắn khoảng cách tim như tờ in), gốc toạ độ tại tim móng, đặt bên trái tờ 1;
không in ra PDF. Chữ, kích thước ghi theo mm (DIMLFAC 1000) như các tờ bản vẽ."""
from __future__ import annotations

import math

from ezdxf.enums import TextEntityAlignment

from . import cad, model
from .geom import Geo
from .sheet1 import T_AXIS, T_BISECT, T_ROUTE

QUAD = {1: (-1, 1), 2: (1, 1), 3: (-1, -1), 4: (1, -1)}
H_TXT = 0.20                    # cao chữ (m) - in tỷ lệ 1:100 ra chữ 2 mm
DIMSTYLE = "MB_1_1_M"


def _dimstyle(doc):
    if DIMSTYLE in doc.dimstyles:
        return DIMSTYLE
    nm = cad.ensure_dimstyle(doc, 1000)                    # cùng kiểu như tờ in, đổi cỡ theo mét
    ds = doc.dimstyles.duplicate_entry(nm, DIMSTYLE)
    a = ds.dxf
    a.dimtxt, a.dimasz, a.dimexo, a.dimexe, a.dimgap, a.dimdle = H_TXT, 0.1, 0.1, 0.1, 0.06, 0.1
    a.dimlfac, a.dimrnd = 1000.0, 1.0
    return DIMSTYLE


def piers(data):
    """[(vị trí 1..4, Geo, tên loại)] - 4 trụ giống nhau (p) hoặc móng 2 loại (mp)."""
    if "TYPES" in data:
        from .lech import model as lm
        return [(q, Geo(lm.type_params(data, i)), t["NAME"]) for i, t in enumerate(data["TYPES"]) for q in t["POS"]]
    g = Geo(data)
    return [(q, g, model.type_name(data)) for q in (1, 2, 3, 4)]


def draw(doc, data, xr=-10.0, ym=148.5):
    """Vẽ mặt bằng 1:1 (m) vào modelspace: mép phải tại x = xr, tim móng ở cao y = ym (bên trái tờ 1).
    Trả về (ox, oy) - toạ độ tim móng."""
    msp = doc.modelspace()
    dn = _dimstyle(doc)
    ps = piers(data)
    ext = max((g.bt + g.tp) / 2 + g.Bh + model.ML for _, g, _ in ps)
    e = ext + 0.6
    ox, oy = xr - e, ym
    A = lambda x, y: (ox + x, oy + y)

    def rect(lay, x0, y0, x1, y1):
        msp.add_lwpolyline([A(x0, y0), A(x1, y0), A(x1, y1), A(x0, y1)], close=True, dxfattribs={"layer": lay})

    def ln(lay, x0, y0, x1, y1):
        e_ = msp.add_line(A(x0, y0), A(x1, y1), dxfattribs={"layer": lay})
        if lay == "TRUC":
            e_.dxf.ltscale = 0.025                      # kiểu nét trục định nghĩa theo mm giấy -> theo m

    def tx(s, x, y, h=H_TXT, al=TextEntityAlignment.MIDDLE_CENTER, bold=False, rot=0.0):
        t = msp.add_text(s, height=h, rotation=rot, dxfattribs={"layer": "CHU", "width": cad.WIDTH,
                                                                "style": cad.STYLE_B if bold else cad.STYLE})
        t.set_placement(A(x, y), align=al)

    def vee(x1, y1, x2, y2):
        """Mũi tên chữ V tại (x2, y2) - như tờ in (đầu 1.2 x 1.6 mm giấy ở 1:100)."""
        d_ = math.hypot(x2 - x1, y2 - y1)
        ux, uy = (x2 - x1) / d_, (y2 - y1) / d_
        bx, by = x2 - ux * 0.12, y2 - uy * 0.12
        msp.add_lwpolyline([A(x1, y1), A(x2, y2), A(bx - uy * 0.16, by + ux * 0.16), A(x2, y2),
                            A(bx + uy * 0.16, by - ux * 0.16)], dxfattribs={"layer": "CHU"})

    def dim(p1, p2, loc, rot):
        msp.add_linear_dim(base=A(*loc), p1=A(*p1), p2=A(*p2), angle=rot, dimstyle=dn,
                           dxfattribs={"layer": "DIM"}).render()

    xs_ax, ys_ax = set(), set()
    for q, g, name in ps:
        sx, sy = QUAD[q]
        P, T = (g.bt + g.tp) / 2, g.bt / 2
        xc, yc = sx * P, sy * P
        B, pm, bh, ml = g.Bh, g.pm, g.b2 / 2, model.ML
        rect("HINH THUC", xc - B - ml, yc - B - ml, xc + B + ml, yc + B + ml)          # bê tông lót
        rect("MAIN", xc - B, yc - B, xc + B, yc + B)                                    # bản đế
        rect("MAIN", xc - pm, yc - pm, xc + pm, yc + pm)                                # gờ
        for qx in (-1, 1):
            for qy in (-1, 1):
                ln("MAIN", xc + qx * pm, yc + qy * pm, xc + qx * B, yc + qy * B)       # nét vát
        rect("MAIN", xc - bh, yc - bh, xc + bh, yc + bh)                                # chân cổ b2
        b1 = g.b1
        x0 = xc - bh if sx > 0 else xc + bh - b1                                        # đỉnh cổ b1, mặt trong thẳng
        y0 = yc - bh if sy > 0 else yc + bh - b1
        if g.tp > 1e-6:
            rect("MAIN", x0, y0, x0 + b1, y0 + b1)
            ln("MAIN", x0 + b1 if sx > 0 else x0, y0 + b1 if sy > 0 else y0, xc + sx * bh, yc + sy * bh)
        cx, cy = x0 + b1 / 2, y0 + b1 / 2                                               # tim cột = tim cụm bu lông
        o = model.bolt_gap(g.p, g.bb) / 2
        r = model.bolt_dia(g.p) / 2000.0
        for bx in (-1, 1):
            for by in (-1, 1):
                msp.add_circle(A(cx + bx * o, cy + by * o), r, dxfattribs={"layer": "CHU"})
        tx(f"TRỤ {q}: {name}", xc, yc + sy * (B + ml + 0.2))           # phía ngoài bản đế (khe giữa 2 trụ có thể hẹp)
        xs_ax.add(round(sx * T, 6))
        ys_ax.add(round(sy * T, 6))
    ln("TRUC", 0.0, -e, 0.0, e)                                          # chỉ trục qua tim móng
    ln("TRUC", -e, 0.0, e, 0.0)
    # đường bao đền bù: cách mép bê tông móng (bản đế) 0.5 m - cùng cạnh với khối lượng (model.den_bu)
    if "TYPES" in data:
        from .lech import model as lm
        a_db = lm.den_bu(data)
    else:
        a_db = model.den_bu(data)
    if "MB_DASH_M" not in doc.linetypes:
        doc.linetypes.add("MB_DASH_M", pattern=[0.3, 0.2, -0.1], description="Net dut (m) __ __ __")
    hb = a_db / 2
    msp.add_lwpolyline([A(-hb, -hb), A(hb, -hb), A(hb, hb), A(-hb, hb)], close=True,
                       dxfattribs={"layer": "HINH THUC", "linetype": "MB_DASH_M"})
    tx(f"ĐƯỜNG BAO ĐỀN BÙ (CÁCH MÉP BÊ TÔNG MÓNG 0.5 m): {a_db:.2f} x {a_db:.2f} = {a_db * a_db:.2f} m²",
       0.0, e + 0.25)
    # tim móng
    rc = 0.15
    msp.add_circle(A(0.0, 0.0), rc, dxfattribs={"layer": "CHU"})
    for a0 in (0.0, 180.0):
        pts = [A(0.0, 0.0)] + [A(rc * math.cos(math.radians(a0 + t)), rc * math.sin(math.radians(a0 + t)))
                               for t in range(0, 91, 10)]
        hh = msp.add_hatch(color=256, dxfattribs={"layer": "CHU"})
        hh.paths.add_polyline_path(pts, is_closed=True)
    ht = int(data.get("HT", 0))
    w = cad.txtw(T_AXIS, H_TXT)                         # ghi chú tim móng có đường dẫn, như tờ in
    sg = 1.0 if ht in model.HT_TIM_BR else -1.0          # mũi tên sang trái -> ghi phía dưới bên phải
    msp.add_lwpolyline([A(0.0, 0.0), A(sg * 0.3, -sg * 0.47), A(sg * (0.4 + w), -sg * 0.47)], dxfattribs={"layer": "CHU"})
    tx(T_AXIS, sg * 0.39 - (w if sg < 0 else 0.0), -sg * 0.47 + 0.09, al=TextEntityAlignment.LEFT)
    # hướng tuyến, hướng phân giác - cùng quy tắc mặt bằng tờ in (sheet1.draw_route), kích thước thật
    lh = min((g.bt + g.tp) / 2 + g.Bh for _, g, _ in ps)                 # tới mép bản đế
    lx = min((g.bt + g.tp) / 2 + 0.6 * g.Bh for _, g, _ in ps)           # phân giác: quá khe hở, chưa tới mép
    wr = cad.txtw(T_ROUTE, H_TXT)
    a = max(0.3 + wr / 2, min(0.5 * lh, lh - 0.24 - wr / 2))
    if ht in model.HT_ANGLE:
        dlt = math.radians(10.0)
        sn, cs = math.sin(dlt), math.cos(dlt)
        vee(0.0, 0.0, -lh * sn, lh * cs)
        vee(0.0, 0.0, -lh * sn, -lh * cs)
        tx(T_ROUTE, -a * sn - 0.24 * cs, a * cs - 0.24 * sn, rot=100.0)
    elif ht == 2:
        vee(0.0, 0.0, 0.0, -lh)
        tx(T_ROUTE, -0.24, -a, rot=90.0)
    elif ht == model.HT_90:                                      # néo góc 90°: lên và sang trái, không phân giác
        vee(0.0, 0.0, 0.0, lh)
        tx(T_ROUTE, -0.24, a, rot=90.0)
        vee(0.0, 0.0, -lh, 0.0)
        tx(T_ROUTE, -a, 0.24)
    else:
        vee(0.0, 0.0, 0.0, -lh)
        vee(0.0, 0.0, 0.0, lh)
        tx(T_ROUTE, -0.24, a, rot=90.0)
    if ht in model.HT_BISECT:
        vee(0.0, 0.0, -lx, 0.0)
        tx(T_BISECT, -lx + 0.25, 0.16, al=TextEntityAlignment.LEFT)
    # kích thước: mép bản đế - tim cột - tim cột - mép bản đế, tổng (dưới và trái)
    for axis in (0, 1):
        cs = sorted({round(c, 6) for c in (xs_ax if axis == 0 else ys_ax)})
        lo = min((QUAD[q][axis] * (g.bt + g.tp) / 2 - g.Bh) for q, g, _ in ps if QUAD[q][axis] < 0)
        hi = max((QUAD[q][axis] * (g.bt + g.tp) / 2 + g.Bh) for q, g, _ in ps if QUAD[q][axis] > 0)
        chain = [lo] + cs + [hi]
        for k, off in ((0, e + 0.6), (1, e + 1.2)):
            pts = chain if k == 0 else [lo, hi]
            for a, b in zip(pts, pts[1:]):
                if axis == 0:
                    dim((a, -ext), (b, -ext), (0.0, -off), 0)
                else:
                    dim((-ext, a), (-ext, b), (-off, 0.0), 90)
    tx("MẶT BẰNG MÓNG - TỶ LỆ 1:1 (ĐƠN VỊ BẢN VẼ: m, KÍCH THƯỚC GHI: mm)", 0.0, -e - 2.2, h=0.3, bold=True)
    tx(f"CỘT {model.HT_NAMES[int(data.get('HT', 0))]} {data.get('COT', '')}".strip(), 0.0, -e - 2.75, h=0.25)
    tx(f"MÓNG {data.get('TENMONG') or (lm.type_name(data) if 'TYPES' in data else model.type_name(data))}",
       0.0, -e - 3.15, h=0.25)
    tx("Gốc toạ độ tại tim móng", 0.0, -e - 3.55)
    return ox, oy
