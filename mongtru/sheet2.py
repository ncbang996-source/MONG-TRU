"""Tờ 2 (TKBVTC): bố trí thép trụ (mặt cắt qua tim 1 trụ), thép bản đế (mặt bằng: nửa trái lớp trên, nửa phải
lớp dưới), mặt cắt cổ móng 1-1, lưới thép đầu trụ, bảng thống kê cốt thép, bảng kích thước từng thanh, bảng tổng kê."""
from __future__ import annotations

from . import model, tables
from .cad import Ctx, ensure_dimstyle, txtw
from .geom import ANCHOR, CH_LEG, Geo, ceil_
from .sheet1 import bolts_aa, pad_aa, pad_plan
from .view import V, Callouts, cut_line, dai_draw, note_at, ni, phi, tick45, tie, title

T_TOP = "LỚP TRÊN"
T_BOT = "LỚP DƯỚI"
T_CHONG = "THANH CHỐNG"
T_DAI = "THÉP ĐAI"
T_MESH = "LƯỚI THÉP"
T_MESHH = "LƯỚI THÉP ĐẦU TRỤ"
DET = [25, 30, 40, 50, 60, 75, 100]
XT = 268.0               # mép trái cột bảng


def det_scale(g: Geo):
    """Tỷ lệ hình bố trí thép trụ và thép bản đế."""
    for d in DET:
        k = 1000.0 / d
        if k * (g.B + 0.2) <= 112.0 and k * (g.H + g.B + 0.2) <= 168.0:
            return d
    return DET[-1]


def pier_scale(g: Geo):
    for d in (20, 25, 30, 40, 50):
        if 1000.0 / d * g.bb <= 50.0:
            return d
    return 50


def sc_title(c: Ctx, x, y, s, den):
    title(c, x, y, s, f"TL:1/{den}")


# ---------------------------------------------------------------------------
def pier_section(c: Ctx, g: Geo, co: Callouts, cx, ytop):
    """Bố trí thép trụ: mặt cắt qua tim 1 trụ (theo X), z = 0 tại đáy bản đế. Trả về v."""
    p = g.p
    den = det_scale(g)
    k = 1000.0 / den
    v = V(c, cx, ytop - 14.0 - k * g.H, den)
    pad_aa(v, g, 0.0)
    v.ln("TRUC", 0.0, -model.TL - 0.08, 0.0, g.H + 0.1)
    cov, B = g.cov, g.Bh
    e = B - cov
    # lưới dưới: thanh theo X (ngoài cùng) thấy dài, thanh theo Y là chấm
    zx, zy = g.z_bot()
    rdb = v.rbar(p["RB_BOT_D"])
    v.ln("COTTHEP", -e, zx, e, zx)
    xs = g.xs_bot()
    for x in xs:
        v.disc("COTTHEP", x, zy, rdb)
    # lưới trên: thanh theo X ở tim (uốn theo mặt vát, móc chân), thanh theo Y là chấm
    d0, d1 = g.d_top()
    rdt = v.rbar(p["RB_TOP_D"])
    hk = g.hook_top()
    zt = lambda x, d: g.ztop(x) - d
    pm = g.pm
    v.pl("COTTHEP", False, [(-e, zt(e, d0) - hk), (-e, zt(e, d0)), (-pm, zt(pm, d0)), (pm, zt(pm, d0)),
                            (e, zt(e, d0)), (e, zt(e, d0) - hk)])
    xt = g.xs_top()
    for x in xt:
        v.disc("COTTHEP", x, zt(x, d1), rdt)
    # thanh chống (dãy gần tim): thân đứng, 2 chân ngang
    chs = sorted({round(x, 6) for x, _ in g.chairs() if abs(x) > g.bb / 2})
    zc0 = g.covb + g.db
    for x in chs:
        z1 = zc0 + g.chair_body(x, 0.0)
        sg = 1.0 if x < 0 else -1.0
        v.pl("DAI", False, [(x + sg * CH_LEG, zc0), (x, zc0), (x, z1), (x + sg * CH_LEG, z1)])
    # cổ móng: thép chủ neo chân quay ra ngoài, đai, lưới đầu trụ
    us = g.pier_us()
    z0, z1 = g.pier_z0(), g.z_col_top()
    for u in (us[0], us[-1]):
        sg = 1.0 if u > 0 else -1.0
        v.pl("COTTHEP", False, [(u, z1), (u, z0), (u + sg * ANCHOR, z0)])
    wh = g.bb / 2 - cov
    for z in g.hoop_zs():
        v.ln("DAI", -wh, z, wh, z)
    rl = v.rbar(p["RL_D"])
    hl = wh - g.g("RT_D") / 1000.0
    nd = ceil_(2 * hl / (p["RL_S"] / 1000.0) - 1e-6)
    for z in g.mesh_zs():
        v.ln("DAI", -hl, z, hl, z)
        for j in range(nd + 1):
            v.disc("DAI", -hl + j * 2 * hl / nd, z - p["RL_D"] / 1000.0, rl)
    bolts_aa(c, g, cx)
    # ---- chú thích
    xr = v.x(B + model.ML) + 4.0
    xl = v.x(-B - model.ML) - 4.0
    # 1: lưới dưới (chấm + thanh dài)
    i1 = max(0, len(xs) // 2 + 2)
    i1 = min(i1, len(xs) - 2)
    co([v.P(xs[i1], zy), v.P(0.5 * (xs[i1] + xs[i1 + 1]), zx)], xr, v.y(-model.TL) - 11.0, 1, 1,
       phi(p["RB_BOT_D"], p["RB_BOT_S"]), tick=False)
    # 2: lưới trên
    j2 = max(0, len(xt) // 2 + 2)
    j2 = min(j2, len(xt) - 2)
    xa = xt[j2]
    co([v.P(xa, zt(xa, d1)), v.P(0.5 * (xt[j2] + xt[j2 + 1]), zt(0.5 * (xt[j2] + xt[j2 + 1]), d0))],
       xr, v.y(g.hb) + 4.0, 1, 2, phi(p["RB_TOP_D"], p["RB_TOP_S"]), tick=False)
    # 3: thanh chống (bên trái)
    x3 = chs[0]
    co([v.P(x3, 0.5 * (zc0 + zc0 + g.chair_body(x3, 0.0)))], xl, v.y(-model.TL) - 11.0, -1, 3, T_CHONG,
       phi(p["RB_CH_D"], p["RB_CH_S"]))
    # 4: thép chủ (bên phải cổ)
    xp = v.x(g.bb / 2) + 6.0
    hz = g.hoop_zs()
    zq = g.hb + 0.5 * (z1 - g.hb)                     # chú thích thép chủ ở giữa cổ, giữa 2 đai
    hi = min(range(len(hz) - 1), key=lambda i: abs(0.5 * (hz[i] + hz[i + 1]) - zq)) if len(hz) > 1 else 0
    zm = 0.5 * (hz[hi] + hz[hi + 1]) if len(hz) > 1 else zq
    co([v.P(us[-1], zm), v.P(us[0], zm)], xp, v.y(zm), 1, 4, f"{ni(p['RC_N'])}%%C{ni(p['RC_D'])}", mode=True)
    # 5 (+6, 7): đai - đường đứng qua các đai, dấu xẹt
    zlo = g.hb + 12.0 / v.k                       # trên kích thước gờ cổ móng
    zi = [z for z in hz if zlo < z < zm - 0.1]
    z5 = zi[0] if zi else 0.5 * (g.hb + zm)
    nums = [5] + [q for q in (6, 7) if q in g.seq]
    xv = v.x(wh - 0.06)
    with c.item("callout5", f"Chú thích thép {g.sq(5)}"):
        y5 = v.y(z5) - 3.0
        bx = xp
        w = txtw(T_DAI, 2.0)
        sel = [z for z in hz if abs(z - z5) < 0.45][:4] or [z5]
        c.ln("CHU", xv, min(v.y(z) for z in sel + [z5 - 0.06]), xv, max(v.y(z) for z in sel),
             fixed1=True, fixed2=True)
        for z in sel:
            tick45(c, xv, v.y(z), fixed=True)
        c.ln("CHU", xv, y5, bx, y5, fixed1=True)
        xb = bx + 4.3 + w + 1.3
        c.ln("CHU", bx, y5, xb - 3.0, y5)
        c.txj("CHU", bx + 1.0, y5 + 0.8, 2.0, T_DAI, 0)
        c.txj("CHU", bx + 1.0, y5 - 2.8, 2.0, phi(p["RT_D"], p["RT_S"]), 0)
        from .view import balloon
        for i, q in enumerate(nums):
            balloon(c, xb + 6.6 * i, y5, g.sq(q))
    # 8: lưới đầu trụ
    zl = g.mesh_zs()
    co([v.P(hl, zl[0]), v.P(hl - 0.05, zl[min(1, len(zl) - 1)] - p["RL_D"] / 1000.0)], xp, v.y(z1) + 2.0, 1, 8,
       T_MESH, phi(p["RL_D"], p["RL_S"]), tick=False)
    # ký hiệu mặt cắt 1-1 trên cổ móng
    zc = g.hb + 0.78 * (z1 - g.hb)
    cut_line(c, v.P(-g.bb / 2, zc), v.P(g.bb / 2, zc), "1", side=-1.0, ext=2.0)
    dims_pier(c, g, v)
    sc_title(c, cx, v.y(-model.TL) - 17.0, "BỐ TRÍ THÉP TRỤ", den)
    return v


def dims_pier(c: Ctx, g: Geo, v: V):
    w100 = txtw("100", 2.0)
    B, ml = g.Bh, model.ML
    yb = v.y(-model.TL) - 4.0
    v.dimH((-B, -model.TL), (B, -model.TL), yb)
    v.dimH((-B - ml, -model.TL), (-B, -model.TL), yb, (v.x(-B - ml) - 1.0 - w100 / 2, yb + 2.0))
    v.dimH((B, -model.TL), (B + ml, -model.TL), yb, (v.x(B + ml) + 1.0 + w100 / 2, yb + 2.0))
    xd = v.x(-B - ml) - 5.0
    zs = [0.0, g.hv, g.hb, g.H]
    for i in range(3):
        v.dimV((-B, zs[i]), (-g.bb / 2 if i == 2 else -B, zs[i + 1]), xd)
    v.dimV((-B, 0.0), (-g.bb / 2, g.H), xd - 7.0)
    # cổ móng, gờ
    yt = v.y(g.H) + 7.0
    v.dimH((-g.bb / 2, g.H), (g.bb / 2, g.H), yt)
    ygr = v.y(g.hb) + 4.0
    for s in (-1, 1):
        tx = v.x(s * g.pm) + s * (1.0 + w100 / 2)
        v.dimH((s * g.bb / 2, g.hb), (s * g.pm, g.hb), ygr, (tx, ygr + 1.2) if v.k * model.MPL < w100 + 1 else None)


# ---------------------------------------------------------------------------
def slab_plan(c: Ctx, g: Geo, co: Callouts, cx, cy, den):
    """Thép bản đế trên mặt bằng 1 trụ: nửa trái lớp trên, nửa phải lớp dưới."""
    p = g.p
    v = V(c, cx, cy, den)
    pad_plan(c, g, v, 0.0, 0.0, lot=True, bolts=False)
    B, cov = g.Bh, g.cov
    e = B - cov
    v.ln("TRUC", -B - 0.25, 0.0, B + 0.25, 0.0)
    v.ln("TRUC", 0.0, -B - 0.25, 0.0, B + 0.25)
    # nét ngắt ở tim (chia 2 nửa)
    from .view import brk
    brk(c, v.x(0.0), v.y(B + 0.18), v.x(0.0), v.y(-B - 0.18), 1.2)

    def pick(lst, lo, hi, tgt):
        c_ = [x for x in lst if lo < x < hi]
        return min(c_, key=lambda x: abs(x - tgt)) if c_ else tgt
    xb = g.xs_bot()
    xt = g.xs_top()
    # lớp dưới (phải): 1 thanh theo Y, 1 thanh theo X
    x1 = pick(xb, g.pm, e, 0.62 * B)
    v.ln("COTTHEP", x1, -e, x1, e)
    y1 = pick(xb, g.pm, e, 0.8 * B)
    v.ln("COTTHEP", 0.06, y1, e, y1)
    # lớp trên (trái)
    x2 = pick([-x for x in xt], -e, -g.pm, -0.62 * B)
    v.ln("COTTHEP", x2, -e, x2, e)
    y2 = pick([-x for x in xt], -e, -g.pm, -0.8 * B)
    v.ln("COTTHEP", -e, y2, -0.06, y2)
    for x, y in ((x2, -e), (x2, e), (-e, y2)):
        v.disc("COTTHEP", x, y, v.rbar(p["RB_TOP_D"]) + 0.15)
    xr = v.x(B + model.ML) + 5.0
    xl = v.x(-B - model.ML) - 5.0
    co([v.P(x1, 0.35 * B)], xr, v.y(0.35 * B), 1, 1, phi(p["RB_BOT_D"], p["RB_BOT_S"]), mode=True)
    co([v.P(0.5 * (x1 + e), y1)], xr, v.y(0.8 * B + 0.05) + 3.0, 1, 1, phi(p["RB_BOT_D"], p["RB_BOT_S"]), mode=True)
    co([v.P(x2, 0.35 * B)], xl, v.y(0.35 * B), -1, 2, phi(p["RB_TOP_D"], p["RB_TOP_S"]), mode=True)
    co([v.P(0.5 * (x2 - e), y2)], xl, v.y(y2) - 4.0, -1, 2, phi(p["RB_TOP_D"], p["RB_TOP_S"]), mode=True)
    yb = v.y(-B - model.ML)
    c.txj("CHU", v.x(-0.5 * B), yb - 5.0, 2.5, T_TOP, 1, underline=True)
    c.txj("CHU", v.x(0.5 * B), yb - 5.0, 2.5, T_BOT, 1, underline=True)
    w100 = txtw("100", 2.0)
    v.dimH((-B, B), (B, B), v.y(B + model.ML) + 4.0)
    yy = v.y(B + model.ML) + 4.0
    for s in (-1, 1):
        v.dimH((s * B, B), (s * (B + model.ML), B + model.ML), yy, (v.x(s * (B + model.ML)) + s * (1.0 + w100 / 2), yy + 2.0))
    sc_title(c, cx, yb - 13.0, "THÉP BẢN ĐẾ", den)


# ---------------------------------------------------------------------------
def col_section(c: Ctx, g: Geo, co: Callouts, cx, cy):
    """1-1: mặt cắt ngang cổ móng (thép chủ, đai, đai bát giác, đai phụ)."""
    p = g.p
    den = pier_scale(g)
    kk, cov = 1000.0 / den, p["COVER"]
    hh = kk * g.bb / 2
    c.rect("MAIN", cx - hh, cy - hh, cx + hh, cy + hh)
    hb = hh - kk * cov
    hb0 = hb
    dai_draw(c, "DAI", cx - hb, cy - hb, cx + hb, cy + hb, 1.0, 1.3)
    n = int(p["RC_N"])
    m = 1 + int(n / 4.0)
    dia = p["RC_D"]
    r = max(0.35, 0.5 * dia / 1000.0 * kk)
    hb = hb - 0.2 - r
    lst = []
    for i in range(m):
        x = -hb + i * 2 * hb / (m - 1)
        lst += [(x, -hb), (x, hb)]
        if 0 < i < m - 1:
            lst += [(-hb, x), (hb, x)]
    for px, py in lst:
        c.disc("COTTHEP", cx + px, cy + py, r)
    grp, st = g.tie_plan()
    rt = r + 0.12
    for i in st:
        x = -hb + i * 2 * hb / (m - 1)
        tie(c, "DAI", cx + x + rt, cy - hb, 0.0, 1.0, 2 * hb, rt, 2.2)
        tie(c, "DAI", cx - hb, cy + x - rt, 1.0, 0.0, 2 * hb, rt, 2.2)
    xo = yo = None
    if grp:
        i = max(grp)
        xo = abs(-hb + i * 2 * hb / (m - 1)) + 0.41421356 * rt
        yo = hb + rt
        c.pl("DAI", True, [(cx - xo, cy + yo), (cx + xo, cy + yo), (cx + yo, cy + xo), (cx + yo, cy - xo),
                           (cx + xo, cy - yo), (cx - xo, cy - yo), (cx - yo, cy - xo), (cx - yo, cy + xo)])
    # bu lông neo (lỗ) trong cổ móng
    o = kk * model.bolt_gap(p, g.bb) / 2
    rb = 0.5 * kk * model.bolt_dia(p) / 1000.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = cx + sx * o, cy + sy * o
            c.ci("CHU", x, y, rb)
            c.ln("CHU", x - 1.6 * rb, y, x + 1.6 * rb, y)
            c.ln("CHU", x, y - 1.6 * rb, x, y + 1.6 * rb)
    bx = cx + hh + 5.0
    sp = 2 * hb / (m - 1)
    co([(cx - hb + i * sp, cy + hb) for i in range(m)], bx, cy + hh + 5.0, 1, 4,
       f"{n}%%C{ni(dia)}", tick=False, mode=True)
    co([(cx + hb0, cy + 0.55 * hh)], bx, cy + 0.55 * hh, 1, 5, phi(p["RT_D"], p["RT_S"]), mode=True)
    if grp:
        co([(cx + 0.5 * (xo + yo), cy - 0.5 * (xo + yo))], bx, cy - 0.15 * hh, 1, 6,
           phi(p["RP_D"], p["RP_S"]), mode=True)
    if st:
        xi = -hb + max(st) * sp
        sole = sorted(st) != sorted(m - 1 - j for j in st)
        yv = cy - 0.8 * hh
        co([(cx + xi + rt, yv), (cx + 0.55 * hb, cy + xi - rt)], bx, yv, 1, 7, phi(p["RP_D"], p["RP_S"]),
           "SO LE" if sole else None, mode=True)
    nm = ensure_dimstyle(c.doc, den)
    c.dimH("DIM", (cx - hh, cy - hh), (cx + hh, cy - hh), cy - hh - 4.5, dimname=nm)
    c.dimV("DIM", (cx - hh, cy - hh), (cx - hh, cy + hh), cx - hh - 4.5, dimname=nm)
    sc_title(c, cx, cy - hh - 13.0, "MẶT CẮT 1-1", den)


def mesh(c: Ctx, g: Geo, co: Callouts, cx, cy):
    p = g.p
    den = pier_scale(g)
    kk = 1000.0 / den
    hh = kk * g.bb / 2
    c.rect("MAIN", cx - hh, cy - hh, cx + hh, cy + hh)
    hb = hh - kk * p["COVER"]
    s = kk * p["RL_S"] / 1000.0
    n = ceil_(2 * hb / s - 1e-6)
    for i in range(n + 1):
        t = -hb + i * 2 * hb / n
        c.ln("DAI", cx - hb, cy + t, cx + hb, cy + t)
        c.ln("DAI", cx + t, cy - hb, cx + t, cy + hb)
    co([(cx + hb, cy + 0.5 * s)], cx + hh + 5.0, cy + 0.5 * s, 1, 8, phi(p["RL_D"], p["RL_S"]),
       f"({int(p['RL_N'])} LỚP)", mode=True)
    nm = ensure_dimstyle(c.doc, den)
    c.dimH("DIM", (cx - hh, cy - hh), (cx + hh, cy - hh), cy - hh - 4.5, dimname=nm)
    c.dimV("DIM", (cx - hh, cy - hh), (cx - hh, cy + hh), cx - hh - 4.5, dimname=nm)
    sc_title(c, cx, cy - hh - 13.0, T_MESHH, den)


# ---------------------------------------------------------------------------
def draw(c: Ctx, g: Geo):
    if not getattr(g, "kl", None):
        g.calc_kl()
    co = Callouts(c, g)
    den = det_scale(g)
    k = 1000.0 / den
    cx = 95.0
    with c.group("pier", "Bố trí thép trụ"):
        pier_section(c, g, co, cx, 276.0)
    ytop = 276.0 - 14.0 - k * (model.TL + 0.0) - 28.0 - k * g.H
    with c.group("plan", "Thép bản đế"):
        slab_plan(c, g, co, cx, ytop - 10.0 - k * (g.Bh + model.ML), den)
    hp = 1000.0 / pier_scale(g) * g.bb / 2
    xm = 205.0
    y11 = 262.0 - hp
    with c.group("sec11", "Mặt cắt 1-1"):
        col_section(c, g, co, xm, y11)
    ym = y11 - hp - 30.0 - hp
    with c.group("mesh", "Lưới thép đầu trụ"):
        mesh(c, g, co, xm, ym)
    ytb = tables.steel_table(c, g, XT, 280.0, 120.0)
    yb = tables.summary(c, g, 405.0, ytb - 6.0)
    note_at(c, XT, yb - 6.0, ["- XEM GHI CHÚ CHUNG TẠI BẢN VẼ SỐ: " + str(g.p.get("CODE", "")),
                              "- KÍCH THƯỚC GHI TRÊN BẢN VẼ TÍNH BẰNG mm."])
    yy = ym - hp - 24.0
    x0 = XT - 5.0 - sum(tables.BT_CW)
    for pos in (2, 3):
        yy = tables.bar_table(c, g, x0, yy, pos, ybot=12.0 if pos == 3 else None) - 9.0
