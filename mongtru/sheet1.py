"""Tờ 1: mặt cắt A-A (qua 2 trụ), mặt bằng móng 4 trụ, bảng tổng kê (mọi giai đoạn)."""
from __future__ import annotations

import math

from . import model, tables
from .cad import Ctx, txtw
from .geom import Geo
from .view import V, bolt_side, elev, marker, note_at, sym, sym_r, title, vee

T_SOIL = "ĐẤT THỪA ĐẮP LẠI"
T_FILL = "ĐẤT ĐẮP ĐẦM CHẶT"
T_AXIS = "TIM MÓNG"
T_ROUTE = "HƯỚNG TUYẾN"
T_BISECT = "HƯỚNG PHÂN GIÁC"
XMAX = 258.0             # mép phải vùng hình (bên phải là bảng)


def fx(x, n):
    return f"{abs(x):.{n}f}"


def bt_txt(g, add=0.0):
    """Chữ kích thước liên quan khoảng cách tim trụ: giá trị thật khi hình bị thu gọn, '<>' khi vẽ đúng tỷ lệ."""
    return f"{1000 * (g.bt + add):.0f}" if getattr(g, "squeezed", False) else "<>"


def layout(g: Geo):
    """Vị trí giấy của mặt cắt A-A và mặt bằng trên tờ 1."""
    p, k = g.p, g.k
    sl = model.SLOPE_DRAW
    g.joint = model.pit_joint_draw(p)                         # trình bày hố đào (không ảnh hưởng khối lượng)
    g.btd = model.draw_bt(p, g.den)                           # khoảng cách tim trụ thể hiện (có thể thu gọn)
    g.squeezed = g.btd < g.bt - 1e-6
    g.T = g.btd / 2                                           # tim đỉnh cổ (tim chân cột) thể hiện
    g.P = (g.btd + g.tp) / 2                                  # tim bản đế thể hiện (cổ vát ra ngoài)
    base = p["B"] + 2 * p["MPIT"]
    g.pitB = (base + 2 * g.P if g.joint else base) / 2        # nửa đáy hố (m)
    g.pitT = g.pitB + sl * model.pit_depth(p)                 # nửa miệng hố (m)
    g.pitX = 0.0 if g.joint else g.P                          # tim hố (m)
    g.ext = g.pitX + g.pitT                                    # nửa bề rộng hình A-A (m)
    g.cx = min(max(105.0, 66.0 + k * g.ext), XMAX - 12.0 - k * g.ext)   # cao độ bên trái không ra ngoài khung
    g.ytop = 262.2
    g.ybase = g.ytop - k * g.H
    g.ygl = g.ybase + k * p["H1"]
    g.ylt = g.ybase - k * model.TL
    g.yd = g.ylt - 10.4
    g.planTop = g.yd - 24.0
    g.cy = g.planTop - k * (g.P + g.Bh + model.ML)
    g.xgl = g.cx - k * g.ext
    g.dimX1 = g.xgl - 21.0
    g.dimX2 = g.xgl - 13.2


# ---------------------------------------------------------------------------
def col_x(g: Geo, xc, so, z):
    """(trái, phải) cổ móng tại cao độ z trên mặt cắt qua tim bản đế xc; so: phía mặt vát (+1 phải, −1 trái)."""
    b2, b = g.b2, g.b_at(z)
    if so > 0:
        return xc - b2 / 2, xc - b2 / 2 + b
    return xc + b2 / 2 - b, xc + b2 / 2


def pad_aa(v: V, g: Geo, xc, lot=True, so=1):
    """Đường bao 1 trụ trên mặt cắt (cắt qua tim bản đế xc); cổ vát về phía so, mặt kia thẳng đứng."""
    B, pm = g.Bh, g.pm
    l0, r0 = col_x(g, xc, so, g.hb)
    l1, r1 = col_x(g, xc, so, g.H)
    v.pl("MAIN", True, [(xc - B, 0.0), (xc + B, 0.0), (xc + B, g.hv), (xc + pm, g.hb), (r0, g.hb),
                        (r1, g.H), (l1, g.H), (l0, g.hb), (xc - pm, g.hb), (xc - B, g.hv)])
    if lot:
        ml, tl = model.ML, model.TL
        v.rect("HINH THUC", xc - B - ml, -tl, xc + B + ml, 0.0)
        v.hatch("HATCH", [(xc - B - ml, -tl), (xc + B + ml, -tl), (xc + B + ml, 0.0), (xc - B - ml, 0.0)],
                "AR-CONC", 0.375 * v.k / 10.0)


def bolts_aa(c: Ctx, g: Geo, xc_paper):
    """Bu lông neo nhìn ngang trên đỉnh cổ móng, trả về cao độ giấy đỉnh bu lông."""
    gp = g.k * model.bolt_gap(g.p, g.bb) / 2
    top = g.ytop
    for t in (-1, 1):
        top = bolt_side(c, g.k, xc_paper + t * gp, g.ytop)
    return top


def draw_section(c: Ctx, g: Geo):
    p, k = g.p, g.k
    v = V(c, g.cx, g.ybase, g.den)
    cx = g.cx
    for s in (-1, 1):
        pad_aa(v, g, s * g.P, so=s)                    # cổ vát ra phía ngoài
    # hố đào
    ygl = g.ygl
    hp, ht = k * g.pitB, k * g.pitT
    pits = [0.0] if g.joint else [-g.pitX, g.pitX]
    for xp in pits:
        x0 = cx + k * xp
        for sg in (-1, 1):
            xe, ye = x0 + sg * ht, ygl
            if not g.joint and sg * xp < 0 and sg * (xe - cx) > 0:     # 2 hố riêng: mái trong cắt nhau dưới mặt đất
                t = (cx - (x0 + sg * hp)) / (sg * (ht - hp))
                xe, ye = cx, g.ylt + t * (ygl - g.ylt)
            c.ln("HINH THUC", x0 + sg * hp, g.ylt, xe, ye)
        c.ln("HINH THUC", x0 - hp, g.ylt, x0 + hp, g.ylt)
    # mặt đất (ngắt tại cổ móng)
    xs = [cx - k * g.ext - 8.0]
    for s in (-1, 1):
        xs += [cx + k * x_ for x_ in col_x(g, s * g.P, s, p["H1"])]
    xs.append(cx + k * g.ext + 8.0)
    for i in range(0, len(xs), 2):
        c.ln("HINH THUC", xs[i], ygl, xs[i + 1], ygl)
    # trục
    for s in (-1, 1):
        c.ln("TRUC", cx + s * k * g.T, g.ytop + 4.3, cx + s * k * g.T, g.ylt - 2.2)
        if g.tp > 1e-6:                                    # tim bản đế (khác tim đỉnh cổ khi cổ vát)
            c.ln("TRUC", cx + s * k * g.P, g.ybase + k * g.hb + 2.0, cx + s * k * g.P, g.ylt - 2.2)
    c.ln("TRUC", cx, g.ylt - 1.5, cx, g.ytop + 4.4)
    sym(c, cx, g.ytop - 0.5)
    ybt = g.ytop
    for s in (-1, 1):
        ybt = bolts_aa(c, g, cx + s * k * g.T)
    xb = cx + k * g.T + k * model.bolt_gap(p, g.bb) / 2 + 1.1
    yb = (g.ytop + ybt) / 2
    with c.item("bln", "Ghi chú bu lông"):
        c.ln("CHU", xb, yb, xb + 6.0, yb, fixed1=True)
        c.tx("CHU", xb + 7.0, yb - 0.8, 2.0, p["BLN"])
    # cao độ
    elev(c, g.dimX2 - 17.4, g.ybase, f"-{fx(p['H1'], 2)}m")
    elev(c, g.dimX2 - 17.4, ygl, "%%p0.00")
    elev(c, g.dimX2 - 5.4, g.ytop, f"+{fx(p['H2'], 2)}m")
    # ụ đất thừa đắp lại giữa 2 cổ móng
    pa = ygl + 3.1
    sx = cx - k * (g.P + g.Bh)
    cl_, cr_ = col_x(g, -g.P, -1, p["H1"] + 3.1 / k)      # cổ móng trái tại cao độ ụ đất
    xi = cx + k * cl_
    xa = min(sx + 3.2, xi - 0.5)
    c.ln("HINH THUC", sx, ygl, xa, pa)
    c.ln("HINH THUC", xa, pa, xi, pa)
    c.ln("HINH THUC", cx + k * cr_, pa, cx - k * cr_, pa)
    c.ln("HINH THUC", 2 * cx - sx, ygl, 2 * cx - xa, pa)
    c.ln("HINH THUC", 2 * cx - xa, pa, 2 * cx - xi, pa)
    xl = 0.5 * (sx + xi)
    with c.item("soil", "Ghi chú đất thừa"):
        w = txtw(T_SOIL, 2.0)
        c.pl("CHU", False, [(xl, pa - 0.6), (xl - 4.2, pa + 5.0), (xl - 4.7 - w, pa + 5.0)], fixed=(0,))
        c.tx("CHU", xl - 4.6 - w, pa + 5.8, 2.0, T_SOIL)
    xf = cx + k * (g.ext - 0.45 * (g.pitT - g.pitB))
    with c.item("fill", "Ghi chú đất đắp đầm chặt"):
        c.pl("CHU", False, [(xf, ygl - 2.5), (xf + 4.0, ygl + 4.5), (xf + 4.4 + txtw(T_FILL, 2.0), ygl + 4.5)],
             fixed=(0,))
        c.tx("CHU", xf + 4.2, ygl + 5.3, 2.0, T_FILL)
    title(c, cx, g.yd - 8.5, "MẶT CẮT A-A", f"TL:1/{g.den}")


def dim_section(c: Ctx, g: Geo):
    k, cx = g.k, g.cx
    w100 = txtw("100", 2.0)
    xa = g.dimX2 + 4.0          # đường gióng các kích thước đứng bên trái dừng tại đây
    xl = cx - k * (g.P + g.Bh)
    # trái: H1, H2 (ngoài); hv, hb - hv, H1 - hb, H2 (trong)
    c.dimV("DIM", (xa, g.ygl), (xa, g.ybase), g.dimX1)
    c.dimV("DIM", (xa, g.ygl), (xa, g.ytop), g.dimX1)
    ys = [g.ybase, g.ybase + k * g.hv, g.ybase + k * g.hb, g.ygl, g.ytop]
    for i in range(4):
        tp = (g.dimX2 - 2.0, g.ybase + k * (g.hv + g.hb) / 2 + 0.6) if i == 1 and k * (g.hb - g.hv) < w100 + 1 else None
        c.dimV("DIM", (xa, ys[i]), (xa, ys[i + 1]), g.dimX2, tp)
    # dày lót
    xd = cx - k * (g.pitX + g.pitB) - 4.0              # bên trái mép đáy hố, không đè nét mái hố
    c.dimV("DIM", (xl - k * model.ML, g.ybase), (xl - k * model.ML, g.ylt), xd,
           (xd - 2.0, g.ylt - 1.0 - w100 / 2))
    # dưới mặt cắt: lót, B, lót cho từng trụ; mép hố
    yb = g.ylt
    for s in (-1, 1):
        x0 = cx + k * s * g.P
        hl, hb_ = k * (g.Bh + model.ML), k * g.Bh
        c.dimH("DIM", (x0 - hb_, yb), (x0 + hb_, yb), g.yd)
        # chữ lót phía trong (giữa 2 trụ) đặt vào trong bản đế để không chồng chữ của trụ bên cạnh
        # chữ dày lót đặt vào trong bản đế: phía ngoài để chỗ cho kích thước mép hố cùng hàng
        tl_ = x0 - hb_ + 1.0 + w100 / 2
        tr_ = x0 + hb_ - 1.0 - w100 / 2
        c.dimH("DIM", (x0 - hl, yb), (x0 - hb_, yb), g.yd, (tl_, g.yd + 2.0))
        c.dimH("DIM", (x0 + hb_, yb), (x0 + hl, yb), g.yd, (tr_, g.yd + 2.0))
    # mép hố ngoài cùng
    hl = k * (g.P + g.Bh + model.ML)
    xp = k * (g.pitX + g.pitB)
    if xp - hl > 0.5:
        w = txtw(f"{1000 * (g.pitX + g.pitB - g.P - g.Bh - model.ML):.0f}", 2.0)
        for s in (-1, 1):
            c.dimH("DIM", (cx + s * hl, yb), (cx + s * xp, yb), g.yd,
                   (cx + s * (xp + 1.0 + w / 2), g.yd + 2.0) if xp - hl < w + 1.0 else None)
    # trên: cổ móng, tim trụ
    y1, y2 = g.ytop + 6.0, g.ytop + 12.9
    for s in (-1, 1):
        xc = s * g.T
        c.dimH("DIM", (cx + k * (xc - g.bb / 2), g.ytop), (cx + k * (xc + g.bb / 2), g.ytop), y1)
    # mép bản đế: đường gióng dừng ở mặt đất (cos 0.00)
    c.dimH("DIM", (cx - k * (g.P + g.Bh), g.ygl), (cx - k * g.T, g.ytop + 4.3), y2)
    c.dimH("DIM", (cx - k * g.T, g.ytop + 4.3), (cx + k * g.T, g.ytop + 4.3), y2, text=bt_txt(g))
    c.dimH("DIM", (cx + k * g.T, g.ytop + 4.3), (cx + k * (g.P + g.Bh), g.ygl), y2)
    # gờ quanh chân cổ móng (trụ phải) + cạnh chân cổ b2 khi cổ vát
    x0 = cx + k * g.P
    yg = g.ybase + k * g.hb
    for s in (-1, 1):
        xe, xf = x0 + s * k * g.b2 / 2, x0 + s * k * g.pm
        tx = xf + s * (1.0 + w100 / 2)
        c.dimH("DIM", (xe, yg), (xf, yg), yg + 4.0, (tx, yg + 5.2) if k * model.MPL < w100 + 1 else None)
    if g.tp > 1e-6:
        c.dimH("DIM", (x0 - k * g.b2 / 2, yg), (x0 + k * g.b2 / 2, yg), yg + 4.0)


# ---------------------------------------------------------------------------
def top_sq(g: Geo, xc, yc, sx, sy):
    """Đỉnh cổ móng trên mặt bằng: (x0, y0, x1, y1). Trụ ở góc (sx, sy): mặt trong (phía tim móng) thẳng đứng."""
    b1, h2 = g.b1, g.b2 / 2
    xa = xc - h2 if sx > 0 else xc + h2 - b1
    ya = yc - h2 if sy > 0 else yc + h2 - b1
    return xa, ya, xa + b1, ya + b1


def pad_plan(c: Ctx, g: Geo, v: V, xc, yc, lot=True, bolts=True, sx=1, sy=1):
    """1 trụ trên mặt bằng: lót, bản đế, gờ, nét vát, chân cổ b2, đỉnh cổ b1 (lệch về phía tim móng), bu lông."""
    B, pm, bh, ml = g.Bh, g.pm, g.b2 / 2, model.ML
    if lot:
        v.rect("HINH THUC", xc - B - ml, yc - B - ml, xc + B + ml, yc + B + ml)
    v.rect("MAIN", xc - B, yc - B, xc + B, yc + B)
    v.rect("MAIN", xc - pm, yc - pm, xc + pm, yc + pm)
    for qx in (-1, 1):
        for qy in (-1, 1):
            v.ln("MAIN", xc + qx * pm, yc + qy * pm, xc + qx * B, yc + qy * B)
    v.rect("MAIN", xc - bh, yc - bh, xc + bh, yc + bh)
    x0, y0, x1, y1 = top_sq(g, xc, yc, sx, sy)
    if g.tp > 1e-6:
        v.rect("MAIN", x0, y0, x1, y1)
        ox, oy = (x1 if sx > 0 else x0), (y1 if sy > 0 else y0)          # góc ngoài đỉnh cổ -> góc ngoài chân cổ
        v.ln("MAIN", ox, oy, xc + sx * bh, yc + sy * bh)
    if bolts:
        bolts_plan(c, g, v.x((x0 + x1) / 2), v.y((y0 + y1) / 2))


def bolts_plan(c: Ctx, g: Geo, px, py):
    """Cụm 4 bu lông neo nhìn từ trên."""
    o = g.k * model.bolt_gap(g.p, g.bb) / 2
    r = max(0.3, 0.5 * g.k * model.bolt_dia(g.p) / 1000.0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = px + sx * o, py + sy * o
            c.ci("CHU", x, y, r)
            c.ln("CHU", x - 1.8 * r, y, x + 1.8 * r, y)
            c.ln("CHU", x, y - 1.8 * r, x, y + 1.8 * r)


def tim_mong(c: Ctx, cx, cy, r):
    """Ký hiệu tim móng: vòng tròn, tô đen 2 góc phần tư đối đỉnh."""
    c.ci("CHU", cx, cy, r)
    for a0 in (0.0, 180.0):
        pts = [(cx, cy)] + [(cx + r * math.cos(math.radians(a0 + t)), cy + r * math.sin(math.radians(a0 + t)))
                            for t in range(0, 91, 10)]
        c.solid("CHU", pts)


def draw_route(c: Ctx, g: Geo, cx, cy, lh, lx):
    """Hướng tuyến qua tim móng: đỡ - 2 chiều theo Y; néo góc - 2 tia lệch 10°, phân giác sang trái;
    néo dừng - 1 chiều. Chữ đặt trong khoảng trống giữa 2 hàng trụ."""
    ht = int(g.p["HT"])
    wr = txtw(T_ROUTE, 2.0)
    a = max(3.0 + wr / 2, min(0.5 * lh, lh - 2.4 - wr / 2))
    if ht == 1:
        dlt = math.radians(10.0)
        sn, cs = math.sin(dlt), math.cos(dlt)
        vee(c, cx, cy, cx - lh * sn, cy + lh * cs)
        vee(c, cx, cy, cx - lh * sn, cy - lh * cs)
        c.txr("CHU", cx - a * sn - 2.4 * cs, cy + a * cs - 2.4 * sn, 2.0, T_ROUTE, 90.0 + 10.0)
        vee(c, cx, cy, cx - lx, cy)
        c.tx("CHU", cx - lx + 2.5, cy + 1.6, 2.0, T_BISECT)        # chữ ở đầu xa của mũi tên phân giác
    elif ht == 2:
        vee(c, cx, cy, cx, cy - lh)
        c.txr("CHU", cx - 2.4, cy - a, 2.0, T_ROUTE, 90.0)
    else:
        vee(c, cx, cy, cx, cy - lh)
        vee(c, cx, cy, cx, cy + lh)
        c.txr("CHU", cx - 2.4, cy + a, 2.0, T_ROUTE, 90.0)


def plan_outline(c: Ctx, g: Geo, v: V, lot=True):
    d, P = g.T, g.P
    for sx in (-1, 1):
        for sy in (-1, 1):
            pad_plan(c, g, v, sx * P, sy * P, lot, sx=sx, sy=sy)
    e = P + g.Bh + 0.3
    for s in (-1, 1):
        v.ln("TRUC", s * d, -e, s * d, e)                  # tim đỉnh cổ (tim chân cột)
        v.ln("TRUC", -e, s * d, e, s * d)
    v.ln("TRUC", -e, 0.0, e, 0.0)
    v.ln("TRUC", 0.0, -e, 0.0, e)


def dim_plan(c: Ctx, g: Geo, v: V, lot=True):
    d, B, ml, P = g.T, g.Bh, (model.ML if lot else 0.0), g.P
    w100 = txtw("100", 2.0)
    E = P + B + ml
    x0, y0 = v.x(-E), v.y(-E)
    ys = ([-E] if lot else []) + [-P - B, -d, d, P + B] + ([E] if lot else [])
    tot = bt_txt(g, g.B + g.tp)
    for i in range(len(ys) - 1):
        tp = None
        if lot and i in (0, len(ys) - 2):
            yy = v.y(ys[i]) - 1.0 - w100 / 2 if i == 0 else v.y(ys[i + 1]) + 1.0 + w100 / 2
            tp = (x0 - 7.0 - 2.0, yy)
        v.dimV((-E, ys[i]), (-E, ys[i + 1]), x0 - 7.0, tp, text=bt_txt(g) if ys[i] == -d else "<>")
    v.dimV((-E, -P - B), (-E, P + B), x0 - 14.0, text=tot)
    for i in range(len(ys) - 1):
        tp = None
        if lot and i in (0, len(ys) - 2):
            xx = v.x(ys[i]) - 1.0 - w100 / 2 if i == 0 else v.x(ys[i + 1]) + 1.0 + w100 / 2
            tp = (xx, y0 - 7.0 + 2.0)
        v.dimH((ys[i], -E), (ys[i + 1], -E), y0 - 7.0, tp, text=bt_txt(g) if ys[i] == -d else "<>")
    v.dimH((-P - B, -E), (P + B, -E), y0 - 14.0, text=tot)
    # cổ móng (đỉnh b1, chân b2) + bản đế trụ trên phải
    x0_, y0_, x1_, y1_ = top_sq(g, P, P, 1, 1)
    bh, pm = g.b2 / 2, g.pm
    v.dimH((x0_, y0_), (x1_, y0_), v.y(P - pm) - 4.0)
    v.dimV((x0_, y0_), (x0_, y1_), v.x(P - pm) - 4.0)
    if g.tp > 1e-6:
        v.dimH((P - bh, P + bh), (P + bh, P + bh), v.y(P + pm) + 4.0)
        v.dimV((P + bh, P - bh), (P + bh, P + bh), v.x(P + pm) + 4.0)
    v.dimH((P - B, P + B), (P + B, P + B), v.y(E) + 5.0)
    v.dimV((P + B, P - B), (P + B, P + B), v.x(E) + 5.0)


def draw_plan(c: Ctx, g: Geo):
    v = V(c, g.cx, g.cy, g.den)
    k = g.k
    plan_outline(c, g, v)
    cx, cy = g.cx, g.cy
    tim_mong(c, cx, cy, 1.2)
    with c.item("axis", "Ghi chú tim móng"):
        w = txtw(T_AXIS, 2.0)
        if int(g.p["HT"]) == 1:          # néo góc: phân giác chạy sang trái -> ghi tim móng phía dưới bên phải
            c.pl("CHU", False, [(cx, cy), (cx + 3.0, cy - 4.7), (cx + 4.0 + w, cy - 4.7)], fixed=(0,))
            c.tx("CHU", cx + 3.9, cy - 4.7 + 0.9, 2.0, T_AXIS)
        else:
            c.pl("CHU", False, [(cx, cy), (cx - 3.0, cy + 4.7), (cx - 4.0 - w, cy + 4.7)], fixed=(0,))
            c.tx("CHU", cx - 3.9 - w, cy + 4.7 + 0.9, 2.0, T_AXIS)
    reach = k * (g.P + g.Bh)
    draw_route(c, g, cx, cy, reach, k * (g.P + 0.6 * g.Bh))       # phân giác dài quá khe hở, chưa tới mép bản đế
    E = g.P + g.Bh + model.ML
    if int(g.p["HT"]) != 0:                               # trục đứng không có hướng tuyến: ký hiệu đối xứng ở đầu trên
        ys0 = v.y(E) + 9.5                               # trên đường kích thước bản đế trụ góc phải
        c.ln("TRUC", cx, v.y(g.P + g.Bh + 0.3), cx, ys0 + 3.5)
        sym(c, cx, ys0)
    sym_r(c, v.x(-E) - 3.0, cy, 90.0)
    ya = g.P
    marker(c, v.x(-E) - 22.0, cy + k * ya, 1.0, "A")
    marker(c, v.x(E) + 14.0, cy + k * ya, -1.0, "A")
    dim_plan(c, g, v)
    title(c, cx, v.y(-E) - 25.0, "MẶT BẰNG MÓNG", f"TL:1/{g.den}")


# ---------------------------------------------------------------------------
def draw(c: Ctx, g: Geo):
    if not getattr(g, "kl", None):
        g.calc_kl()
    layout(g)
    with c.group("section", "Mặt cắt A-A"):
        draw_section(c, g)
        dim_section(c, g)
    with c.group("plan", "Mặt bằng móng"):
        draw_plan(c, g)
    yb = tables.summary(c, g, 405.0, 267.0)
    note_at(c, 268.0, min(yb - 14.0, 90.0), ["- XEM GHI CHÚ CHUNG TẠI BẢN VẼ SỐ: " + str(g.p.get("CODE", "")),
                                             "- KÍCH THƯỚC GHI TRÊN BẢN VẼ TÍNH BẰNG mm, CAO ĐỘ TÍNH BẰNG m."])
