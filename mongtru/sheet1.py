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
    g.joint = model.pit_joint(p)
    g.btd = model.draw_bt(p, g.den)                           # khoảng cách tim trụ thể hiện (có thể thu gọn)
    g.squeezed = g.btd < g.bt - 1e-6
    base = p["B"] + 2 * p["MPIT"]
    g.pitB = (base + g.btd if g.joint else base) / 2          # nửa đáy hố (m)
    g.pitT = g.pitB + sl * model.pit_depth(p)                 # nửa miệng hố (m)
    g.pitX = 0.0 if g.joint else g.btd / 2                     # tim hố (m)
    g.ext = g.pitX + g.pitT                                    # nửa bề rộng hình A-A (m)
    g.cx = min(max(105.0, 66.0 + k * g.ext), XMAX - 12.0 - k * g.ext)   # cao độ bên trái không ra ngoài khung
    g.ytop = 262.2
    g.ybase = g.ytop - k * g.H
    g.ygl = g.ybase + k * p["H1"]
    g.ylt = g.ybase - k * model.TL
    g.yd = g.ylt - 10.4
    g.planTop = g.yd - 24.0
    g.cy = g.planTop - k * (g.btd / 2 + g.Bh + model.ML)
    g.xgl = g.cx - k * g.ext
    g.dimX1 = g.xgl - 21.0
    g.dimX2 = g.xgl - 13.2


# ---------------------------------------------------------------------------
def pad_aa(v: V, g: Geo, xc, lot=True):
    """Đường bao 1 trụ trên mặt cắt (cắt qua tim trụ), tim tại u = xc."""
    B, pm, bh = g.Bh, g.pm, g.bb / 2
    v.pl("MAIN", True, [(xc - B, 0.0), (xc + B, 0.0), (xc + B, g.hv), (xc + pm, g.hb), (xc + bh, g.hb),
                        (xc + bh, g.H), (xc - bh, g.H), (xc - bh, g.hb), (xc - pm, g.hb), (xc - B, g.hv)])
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
        pad_aa(v, g, s * g.btd / 2)
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
        xs += [cx + k * (s * g.btd / 2 - g.bb / 2), cx + k * (s * g.btd / 2 + g.bb / 2)]
    xs.append(cx + k * g.ext + 8.0)
    for i in range(0, len(xs), 2):
        c.ln("HINH THUC", xs[i], ygl, xs[i + 1], ygl)
    # trục
    for s in (-1, 1):
        c.ln("TRUC", cx + s * k * g.btd / 2, g.ytop + 4.3, cx + s * k * g.btd / 2, g.ylt - 2.2)
    c.ln("TRUC", cx, g.ylt - 1.5, cx, g.ytop + 4.4)
    sym(c, cx, g.ytop - 0.5)
    ybt = g.ytop
    for s in (-1, 1):
        ybt = bolts_aa(c, g, cx + s * k * g.btd / 2)
    xb = cx + k * g.btd / 2 + k * model.bolt_gap(p, g.bb) / 2 + 1.1
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
    sx = cx - k * (g.btd / 2 + g.Bh)
    xi = cx - k * (g.btd / 2 + g.bb / 2)
    xa = min(sx + 3.2, xi - 0.5)
    c.ln("HINH THUC", sx, ygl, xa, pa)
    c.ln("HINH THUC", xa, pa, xi, pa)
    c.ln("HINH THUC", cx - k * (g.btd / 2 - g.bb / 2), pa, cx + k * (g.btd / 2 - g.bb / 2), pa)
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
    xl = cx - k * (g.btd / 2 + g.Bh)
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
        x0 = cx + k * s * g.btd / 2
        hl, hb_ = k * (g.Bh + model.ML), k * g.Bh
        c.dimH("DIM", (x0 - hb_, yb), (x0 + hb_, yb), g.yd)
        # chữ lót phía trong (giữa 2 trụ) đặt vào trong bản đế để không chồng chữ của trụ bên cạnh
        # chữ dày lót đặt vào trong bản đế: phía ngoài để chỗ cho kích thước mép hố cùng hàng
        tl_ = x0 - hb_ + 1.0 + w100 / 2
        tr_ = x0 + hb_ - 1.0 - w100 / 2
        c.dimH("DIM", (x0 - hl, yb), (x0 - hb_, yb), g.yd, (tl_, g.yd + 2.0))
        c.dimH("DIM", (x0 + hb_, yb), (x0 + hl, yb), g.yd, (tr_, g.yd + 2.0))
    # mép hố ngoài cùng
    hl = k * (g.btd / 2 + g.Bh + model.ML)
    xp = k * (g.pitX + g.pitB)
    if xp - hl > 0.5:
        w = txtw(f"{1000 * (g.pitX + g.pitB - g.btd / 2 - g.Bh - model.ML):.0f}", 2.0)
        for s in (-1, 1):
            c.dimH("DIM", (cx + s * hl, yb), (cx + s * xp, yb), g.yd,
                   (cx + s * (xp + 1.0 + w / 2), g.yd + 2.0) if xp - hl < w + 1.0 else None)
    # trên: cổ móng, tim trụ
    y1, y2 = g.ytop + 6.0, g.ytop + 12.9
    for s in (-1, 1):
        xc = s * g.btd / 2
        c.dimH("DIM", (cx + k * (xc - g.bb / 2), g.ytop), (cx + k * (xc + g.bb / 2), g.ytop), y1)
    # mép bản đế: đường gióng dừng ở mặt đất (cos 0.00)
    c.dimH("DIM", (cx - k * (g.btd / 2 + g.Bh), g.ygl), (cx - k * g.btd / 2, g.ytop + 4.3), y2)
    c.dimH("DIM", (cx - k * g.btd / 2, g.ytop + 4.3), (cx + k * g.btd / 2, g.ytop + 4.3), y2, text=bt_txt(g))
    c.dimH("DIM", (cx + k * g.btd / 2, g.ytop + 4.3), (cx + k * (g.btd / 2 + g.Bh), g.ygl), y2)
    # gờ quanh cổ móng (trụ phải)
    x0 = cx + k * g.btd / 2
    yg = g.ybase + k * g.hb
    for s in (-1, 1):
        xe, xf = x0 + s * k * g.bb / 2, x0 + s * k * g.pm
        tx = xf + s * (1.0 + w100 / 2)
        c.dimH("DIM", (xe, yg), (xf, yg), yg + 4.0, (tx, yg + 5.2) if k * model.MPL < w100 + 1 else None)


# ---------------------------------------------------------------------------
def pad_plan(c: Ctx, g: Geo, v: V, xc, yc, lot=True, bolts=True):
    """1 trụ trên mặt bằng: lót, bản đế, gờ, nét vát, cổ móng, bu lông."""
    B, pm, bh, ml = g.Bh, g.pm, g.bb / 2, model.ML
    if lot:
        v.rect("HINH THUC", xc - B - ml, yc - B - ml, xc + B + ml, yc + B + ml)
    v.rect("MAIN", xc - B, yc - B, xc + B, yc + B)
    v.rect("MAIN", xc - pm, yc - pm, xc + pm, yc + pm)
    for sx in (-1, 1):
        for sy in (-1, 1):
            v.ln("MAIN", xc + sx * pm, yc + sy * pm, xc + sx * B, yc + sy * B)
    v.rect("MAIN", xc - bh, yc - bh, xc + bh, yc + bh)
    if bolts:
        bolts_plan(c, g, v.x(xc), v.y(yc))


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
    """Hướng tuyến qua tim móng: đỡ - 2 chiều theo Y; néo - 2 tia lệch 10°, phân giác sang trái;
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
        c.tx("CHU", cx - lx + 1.0, cy + 1.2, 2.0, T_BISECT)
    elif ht == 2:
        vee(c, cx, cy, cx, cy - lh)
        c.txr("CHU", cx - 2.4, cy - a, 2.0, T_ROUTE, 90.0)
    else:
        vee(c, cx, cy, cx, cy - lh)
        vee(c, cx, cy, cx, cy + lh)
        c.txr("CHU", cx - 2.4, cy + a, 2.0, T_ROUTE, 90.0)


def plan_outline(c: Ctx, g: Geo, v: V, lot=True):
    d = g.btd / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            pad_plan(c, g, v, sx * d, sy * d, lot)
    e = d + g.Bh + 0.3
    for s in (-1, 1):
        v.ln("TRUC", s * d, -e, s * d, e)
        v.ln("TRUC", -e, s * d, e, s * d)
    v.ln("TRUC", -e, 0.0, e, 0.0)
    v.ln("TRUC", 0.0, -e, 0.0, e)


def dim_plan(c: Ctx, g: Geo, v: V, lot=True):
    d, B, ml = g.btd / 2, g.Bh, (model.ML if lot else 0.0)
    w100 = txtw("100", 2.0)
    E = d + B + ml
    x0, y0 = v.x(-E), v.y(-E)
    ys = ([-E] if lot else []) + [-d - B, -d, d, d + B] + ([E] if lot else [])
    for i in range(len(ys) - 1):
        tp = None
        if lot and i in (0, len(ys) - 2):
            yy = v.y(ys[i]) - 1.0 - w100 / 2 if i == 0 else v.y(ys[i + 1]) + 1.0 + w100 / 2
            tp = (x0 - 7.0 - 2.0, yy)
        v.dimV((-E, ys[i]), (-E, ys[i + 1]), x0 - 7.0, tp, text=bt_txt(g) if ys[i] == -d else "<>")
    v.dimV((-E, -d - B), (-E, d + B), x0 - 14.0, text=bt_txt(g, g.B))
    for i in range(len(ys) - 1):
        tp = None
        if lot and i in (0, len(ys) - 2):
            xx = v.x(ys[i]) - 1.0 - w100 / 2 if i == 0 else v.x(ys[i + 1]) + 1.0 + w100 / 2
            tp = (xx, y0 - 7.0 + 2.0)
        v.dimH((ys[i], -E), (ys[i + 1], -E), y0 - 7.0, tp, text=bt_txt(g) if ys[i] == -d else "<>")
    v.dimH((-d - B, -E), (d + B, -E), y0 - 14.0, text=bt_txt(g, g.B))
    # cổ móng + bản đế trụ trên phải
    bh = g.bb / 2
    v.dimH((d - bh, d + bh), (d + bh, d + bh), v.y(d + bh) + 3.5)
    v.dimV((d - bh, d - bh), (d - bh, d + bh), v.x(d - bh) - 3.5)
    v.dimH((d - B, d + B), (d + B, d + B), v.y(E) + 5.0)
    v.dimV((d + B, d - B), (d + B, d + B), v.x(E) + 5.0)


def draw_plan(c: Ctx, g: Geo):
    v = V(c, g.cx, g.cy, g.den)
    k = g.k
    plan_outline(c, g, v)
    cx, cy = g.cx, g.cy
    tim_mong(c, cx, cy, 1.2)
    with c.item("axis", "Ghi chú tim móng"):
        sg = -1.0 if int(g.p["HT"]) == 1 else 1.0
        w = txtw(T_AXIS, 2.0)
        c.pl("CHU", False, [(cx, cy), (cx - 3.0, cy + sg * 4.7), (cx - 4.0 - w, cy + sg * 4.7)], fixed=(0,))
        c.tx("CHU", cx - 3.9 - w, cy + sg * 4.7 + 0.9, 2.0, T_AXIS)
    gap = k * (g.btd / 2 - g.Bh)
    draw_route(c, g, cx, cy, k * (g.btd / 2 + g.Bh), max(8.0, gap - 1.0))
    E = g.btd / 2 + g.Bh + model.ML
    sym_r(c, v.x(-E) - 3.0, cy, 90.0)
    ya = g.btd / 2
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
