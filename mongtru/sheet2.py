"""Tờ 2 (TKBVTC): bố trí thép trụ (mặt cắt qua tim 1 trụ), thép bản đế (mặt bằng: nửa trái lớp trên, nửa phải
lớp dưới), mặt cắt cổ móng 1-1, lưới thép đầu trụ, bảng thống kê cốt thép, bảng kích thước từng thanh, bảng tổng kê."""
from __future__ import annotations

import math

from . import model, tables
from .cad import Ctx, ensure_dimstyle, txtw
from .geom import ANCHOR, CH_LEG, Geo, ceil_
from .sheet1 import bolts_aa, col_x, pad_aa, pad_plan
from .view import V, Callouts, cut_line, dai_draw, note_at, ni, phi, sym, tick45, tick_at, tie, title

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
        if 1000.0 / d * g.b2 <= 50.0:
            return d
    return 50


def _ov(g: Geo, key, auto):
    """Tỷ lệ người dùng nhập cho từng hình (ô mục 4. Bản vẽ), 0 / trống = tự động."""
    v = g.p.get(key) or 0
    return int(v + 0.5) if v > 0 else auto


def pier_den(g: Geo):
    """Tỷ lệ hình bố trí thép trụ (ghi ở khung tên tờ thép)."""
    return _ov(g, "TL_PIER", det_scale(g))


def slab_den(g: Geo):
    return _ov(g, "TL_SLAB", det_scale(g))


def sec_den(g: Geo):
    return _ov(g, "TL_11", pier_scale(g))


def mesh_den(g: Geo):
    return _ov(g, "TL_MESH", pier_scale(g))


def sc_title(c: Ctx, x, y, s, den):
    title(c, x, y, s, f"TL:1/{den}")


# ---------------------------------------------------------------------------
def pier_section(c: Ctx, g: Geo, co: Callouts, cx, ytop):
    """Bố trí thép trụ: mặt cắt qua tim bản đế 1 trụ (theo X), z = 0 tại đáy bản đế. Trả về v.
    Mặt vát của cổ móng (phía ngoài) thể hiện bên trái, mặt thẳng đứng (phía tim móng) bên phải."""
    p = g.p
    den = pier_den(g)
    k = 1000.0 / den
    v = V(c, cx, ytop - 14.0 - k * g.H, den)
    pad_aa(v, g, 0.0, so=-1)
    U = lambda i, z: -g.bar_u(i, z)                    # toạ độ hình (lật trái - phải so với toạ độ cục bộ)
    tc = g.tp / 2                                      # tim đỉnh cổ trên hình
    colx = lambda z: col_x(g, 0.0, -1, z)
    v.ln("TRUC", 0.0, -model.TL - 0.08, 0.0, g.hb + 0.1)
    v.ln("TRUC", tc, g.hb - 0.1, tc, g.H + 0.1)        # tim đỉnh cổ (trùng tim bản đế khi cổ thẳng)
    cov, B = g.cov, g.Bh
    e = B - cov
    # lưới dưới: thanh theo X (ngoài cùng) thấy dài, thanh theo Y là chấm
    zx, zy = g.z_bot()
    dot = lambda dmm: max(0.45, v.rbar(dmm))          # chấm thép đủ to để nhìn rõ
    rdb = dot(p["RB_BOT_D"])
    v.ln("COTTHEP", -e, zx, e, zx)
    xs = g.xs_bot()
    for x in xs:
        v.disc("COTTHEP", x, zy, rdb)
    # lưới trên: thanh theo X ở tim (uốn theo mặt vát, móc chân), thanh theo Y là chấm
    d0, d1 = g.d_top()
    rdt = dot(p["RB_TOP_D"])
    hk = g.hook_top()
    zt = lambda x, d: g.ztop(x) - d
    pm = g.pm
    v.pl("COTTHEP", False, [(-e, zt(e, d0) - hk), (-e, zt(e, d0)), (-pm, zt(pm, d0)), (pm, zt(pm, d0)),
                            (e, zt(e, d0)), (e, zt(e, d0) - hk)])
    xt = g.xs_top()
    for x in xt:
        v.disc("COTTHEP", x, zt(x, d1), rdt)
    # thanh chống (dãy gần tim nhất): thân đứng, 2 chân ngang
    cg = g.chair_grid()
    nj = 1 + max(j for _, j, _, _ in cg)
    jr = nj // 2                                       # hàng lưới gần tim nhất (phía +Y)
    row = [(x, y) for _, j, x, y in cg if j == jr]
    chs = sorted(x for x, _ in row)
    ych = {x: y for x, y in row}
    zc0 = g.covb + g.db
    for x in chs:
        z1 = zc0 + g.chair_body(x, ych[x])
        sg = 1.0 if x < 0 else -1.0
        v.pl("DAI", False, [(x + sg * CH_LEG, zc0), (x, zc0), (x, z1), (x + sg * CH_LEG, z1)])
    # cổ móng: thép chủ (thanh mặt vát nghiêng theo mặt vát) neo chân quay ra ngoài, đai, lưới đầu trụ
    m = g.m_bars()
    z0, z1 = g.pier_z0(), g.z_col_top()
    z0 = max(z0, zy + (rdb + 0.35) / v.k)             # đoạn neo vẽ nằm trên chấm thép lớp dưới (không trùng nét)
    for i, sg in ((0, 1.0), (m - 1, -1.0)):
        v.pl("COTTHEP", False, [(U(i, z1), z1), (U(i, z0), z0), (U(i, z0) + sg * ANCHOR, z0)])
    wh = g.bb / 2 - cov
    rl = dot(p["RL_D"])
    hl = wh - g.g("RT_D") / 1000.0
    nd = ceil_(2 * hl / (p["RL_S"] / 1000.0) - 1e-6)
    # lưới đầu trụ + đai đỡ từng lớp lưới: thể hiện tách nét (thanh, chấm, đai cách nhau tối thiểu trên giấy)
    nm = len(g.mesh_zs())
    for i, z in enumerate(g.mesh_zs()):
        yl = v.y(z) - 0.35
        c.ln("DAI", v.x(tc - hl), yl, v.x(tc + hl), yl)
        for j in range(nd + 1):
            c.disc("DAI", v.x(tc - hl + j * 2 * hl / nd), yl - rl - 0.3, rl)
        yh = yl - 2 * rl - 0.9
        c.ln("DAI", v.x(tc - wh), yh, v.x(tc + wh), yh)
    for z in g.hoop_zs()[nm:]:
        l_, r_ = colx(z)
        v.ln("DAI", l_ + cov, z, r_ - cov, z)
    bolts_aa(c, g, cx + k * tc)
    # ---- chú thích
    # 1, 2: thép 2 phương giống nhau -> 1 tag chỉ cả chấm tròn và thanh nằm ngang, đặt ở chỗ trống
    # (giữa đầu neo thép chủ / mép gờ và mép bản đế, tránh thanh chống)
    us0 = U(0, z0)                                    # thanh mặt đứng (phải) - neo chân quay sang phải

    def free(lst, lo, hi):
        cand = [i for i in range(len(lst) - 1) if lo < lst[i] and lst[i + 1] < hi]
        cand = [i for i in cand if all(abs(0.5 * (lst[i] + lst[i + 1]) - x) > 0.06 for x in chs)] or cand
        if not cand:
            return max(0, min(len(lst) - 2, len(lst) // 2 + 1))
        m = 0.5 * (lo + hi)
        return min(cand, key=lambda i: abs(0.5 * (lst[i] + lst[i + 1]) - m))
    # 2 nhánh leader: 1 chỉ chấm tròn (thanh i), 1 chỉ thanh nằm ngang ở khoảng giữa 2 chấm, cách chấm >= 1 bước
    def line_x(lst, i):
        if i + 2 < len(lst):
            return 0.5 * (lst[i + 1] + lst[i + 2])
        return 0.5 * (lst[i - 2] + lst[i - 1]) if i >= 2 else lst[i] + 1.5 * (lst[i] - lst[i - 1])
    i1 = free(xs, us0 + ANCHOR + 0.05, e)
    xl1 = line_x(xs, i1)
    co([v.P(xs[i1], zy), v.P(xl1, zx)], v.x(max(xs[i1], xl1)) + 4.0, v.y(-model.TL) - 11.0, 1, 1,
       phi(p["RB_BOT_D"], p["RB_BOT_S"]), tick=False)
    j2 = free(xt, pm + 0.1, e - 0.05)
    xa, xb2 = xt[j2], line_x(xt, j2)
    co([v.P(xa, zt(xa, d1)), v.P(xb2, zt(xb2, d0))], v.x(pm) + 7.0, v.y(g.hb) + 4.0, 1, 2,
       phi(p["RB_TOP_D"], p["RB_TOP_S"]), tick=False)
    # 3: thanh chống (bên trái), tag ngay dưới bản đế
    x3 = chs[0]
    co([v.P(x3, zc0 + 0.5 * g.chair_body(x3, ych[x3]))], v.x(x3) - 4.0, v.y(-model.TL) - 11.0, -1, 3, T_CHONG,
       phi(p["RB_CH_D"], p["RB_CH_S"]))
    # 4: thép chủ (bên phải cổ)
    xp = v.x(g.b2 / 2) + 6.0
    hz = g.hoop_zs()
    zq = g.hb + 0.5 * (z1 - g.hb)                     # chú thích thép chủ ở giữa cổ, giữa 2 đai
    hi = min(range(len(hz) - 1), key=lambda i: abs(0.5 * (hz[i] + hz[i + 1]) - zq)) if len(hz) > 1 else 0
    zm = 0.5 * (hz[hi] + hz[hi + 1]) if len(hz) > 1 else zq
    co([v.P(U(0, zm), zm), v.P(U(m - 1, zm), zm)], xp, v.y(zm), 1, 4, f"{ni(p['RC_N'])}%%C{ni(p['RC_D'])}",
       mode=True)
    # 5 (+6, 7): đai - đường đứng qua các đai, dấu xẹt
    zlo = g.hb + 12.0 / v.k                       # trên kích thước gờ cổ móng
    zi = [z for z in hz if zlo < z < zm - 0.1]
    z5 = zi[0] if zi else 0.5 * (g.hb + zm)
    nums = [5] + [q for q in (6, 7, 9) if q in g.seq]
    xv = v.x(U(0, z1)) - 2.5                      # đường đứng lệch vào trong, không trùng nét thép chủ (mặt đứng)
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
        for i, q in enumerate(nums if not co.nonum else []):
            balloon(c, xb + 6.6 * i, y5, g.sq(q))
    # 8: lưới đầu trụ
    zl = g.mesh_zs()
    # chỉ vào chấm tròn (thanh lưới thấy mặt cắt) của 2 lớp trên cùng, thanh thứ 2 từ phải
    xd = v.x(tc - hl + (nd - 1) * 2 * hl / nd)
    tg = [(xd, v.y(z) - 0.35 - rl - 0.3) for z in zl[:2]]
    co(tg, xp,
       v.y(z1) + 2.0, 1, 8,
       T_MESH, phi(p["RL_D"], p["RL_S"]), tick=False)
    # ký hiệu mặt cắt 1-1 trên cổ móng
    zc = zcut(g)
    cut_line(c, v.P(colx(zc)[0], zc), v.P(colx(zc)[1], zc), "1", side=-1.0, ext=2.0)
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
    lt, rt = col_x(g, 0.0, -1, g.H)                   # đỉnh cổ (mặt vát bên trái)
    for i in range(3):
        v.dimV((-B, zs[i]), (lt if i == 2 else -B, zs[i + 1]), xd)
    v.dimV((-B, 0.0), (lt, g.H), xd - 7.0)
    # cổ móng (đỉnh b1), gờ quanh chân cổ, chân cổ b2 khi vát
    yt = v.y(g.H) + 7.0
    v.dimH((lt, g.H), (rt, g.H), yt)
    ygr = v.y(g.hb) + 4.0
    for s in (-1, 1):
        tx = v.x(s * g.pm) + s * (1.0 + w100 / 2)
        v.dimH((s * g.b2 / 2, g.hb), (s * g.pm, g.hb), ygr, (tx, ygr + 1.2) if v.k * model.MPL < w100 + 1 else None)
    if g.tp > 1e-6:
        v.dimH((-g.b2 / 2, g.hb), (g.b2 / 2, g.hb), ygr)


# ---------------------------------------------------------------------------
def slab_plan(c: Ctx, g: Geo, co: Callouts, cx, cy, den):
    """Thép bản đế trên mặt bằng 1 trụ: nửa trái lớp trên, nửa phải lớp dưới."""
    p = g.p
    v = V(c, cx, cy, den)
    pad_plan(c, g, v, 0.0, 0.0, lot=True, bolts=False, sx=-1, sy=-1)
    B, cov = g.Bh, g.cov
    e = B - cov
    v.ln("TRUC", -B - 0.25, 0.0, B + 0.25, 0.0)
    # trục đứng chia 2 nửa (lớp trên / lớp dưới) + ký hiệu đối xứng
    ys0 = v.y(B + model.ML) + 2.5                  # ký hiệu đối xứng ở đầu trên trục đứng
    c.ln("TRUC", v.x(0.0), v.y(-B - 0.25), v.x(0.0), ys0 + 3.5)
    sym(c, v.x(0.0), ys0)

    def pick(lst, lo, hi, tgt):
        c_ = [x for x in lst if lo < x < hi]
        return min(c_, key=lambda x: abs(x - tgt)) if c_ else tgt
    xb = g.xs_bot()
    xt = g.xs_top()
    # lớp dưới (phải): 1 thanh theo Y, 1 thanh theo X
    x1 = pick(xb, g.pm, e, 0.62 * B)
    v.ln("COTTHEP", x1, -e, x1, e)
    y1 = pick(xb, g.pm, e, 0.8 * B)
    v.ln("COTTHEP", 0.0, y1, e, y1)
    # lớp trên (trái): như app móng bản không dầm - đoạn xiên theo mặt vát vẽ lệch về góc, móc 100 ở đầu
    hk, pm = 0.1, g.pm
    x2 = pick([-x for x in xt], -e, -pm, -0.62 * B)
    ca = abs(x2)
    ya = max(pm, ca)
    sh = max(0.0, min(0.5 * (e - ya), e - ca - hk))
    v.pl("COTTHEP", False, [(x2 - sh - hk, -e), (x2 - sh, -e), (x2, -ya), (x2, ya), (x2 - sh, e), (x2 - sh - hk, e)])
    y2 = pick([-x for x in xt], -e, -pm, -0.8 * B)
    cy2 = abs(y2)
    x1_ = max(pm, cy2)
    yy2 = min(e - hk, cy2 + 0.5 * (e - x1_))
    v.pl("COTTHEP", False, [(0.0, y2), (-x1_, y2), (-e, -yy2), (-e, -yy2 - hk)])
    xr = v.x(B + model.ML) + 5.0
    xl = v.x(-B - model.ML) - 5.0
    co([v.P(x1, 0.35 * B)], xr, v.y(0.35 * B), 1, 1, phi(p["RB_BOT_D"], p["RB_BOT_S"]), mode=True)
    co([v.P(0.5 * (x1 + e), y1)], xr, v.y(0.8 * B + 0.05) + 3.0, 1, 1, phi(p["RB_BOT_D"], p["RB_BOT_S"]), mode=True)
    co([v.P(x2, 0.35 * B)], xl, v.y(0.35 * B), -1, 2, phi(p["RB_TOP_D"], p["RB_TOP_S"]), mode=True)
    xq = -0.5 * x1_
    co([v.P(xq, y2)], xl, v.y(y2) + 4.0, -1, 2, phi(p["RB_TOP_D"], p["RB_TOP_S"]), mode=True)
    yb = v.y(-B - model.ML)
    yt = v.y(B + model.ML) + 2.0                        # tên lớp ghi phía trên hình, dưới đường kích thước
    c.txj("CHU", v.x(-0.5 * B), yt, 2.5, T_TOP, 1, underline=True)
    c.txj("CHU", v.x(0.5 * B), yt, 2.5, T_BOT, 1, underline=True)
    w100 = txtw("100", 2.0)
    v.dimH((-B, B), (B, B), v.y(B + model.ML) + 8.0)
    yy = v.y(B + model.ML) + 8.0
    for s in (-1, 1):
        v.dimH((s * B, B), (s * (B + model.ML), B + model.ML), yy, (v.x(s * (B + model.ML)) + s * (1.0 + w100 / 2), yy + 2.0))
    sc_title(c, cx, yb - 9.0, "THÉP BẢN ĐẾ", den)


# ---------------------------------------------------------------------------
def zcut(g: Geo):
    """Cao độ mặt cắt 1-1: sát đỉnh cổ móng, dưới lớp lưới đầu trụ thấp nhất (tiết diện thể hiện = b1)."""
    return max(g.hb + 0.5 * (g.z_col_top() - g.hb), min(g.mesh_zs()) - 0.15)


def col_section(c: Ctx, g: Geo, co: Callouts, cx, cy):
    """1-1: mặt cắt ngang cổ móng tại cao độ cắt (thép chủ, đai, đai bát giác, đai phụ). (cx, cy): tim tiết diện.
    Cổ vát: thấy thêm đường bao chân cổ b2 và cạnh vát; mặt đứng (phía tim móng) bên phải và phía trên."""
    p = g.p
    den = sec_den(g)
    kk, cov = 1000.0 / den, p["COVER"]
    bs = g.b1                                          # cắt sát đỉnh cổ: tiết diện b1
    hh = kk * bs / 2
    c.rect("MAIN", cx - hh, cy - hh, cx + hh, cy + hh)
    if g.tp > 1e-6:
        b2 = kk * g.b2
        c.rect("MAIN", cx + hh - b2, cy + hh - b2, cx + hh, cy + hh)
        c.ln("MAIN", cx + hh - b2, cy + hh - b2, cx - hh, cy - hh)
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
    grp, st, nd = g.tie_plan3()
    rt = r + 0.12
    for i in st:
        x = -hb + i * 2 * hb / (m - 1)
        tie(c, "DAI", cx + x + rt, cy - hb, 0.0, 1.0, 2 * hb, rt, 2.2)
        tie(c, "DAI", cx - hb, cy + x - rt, 1.0, 0.0, 2 * hb, rt, 2.2)
    dg = None
    if nd:                                   # đai xiên: nối thanh giữa cạnh này với thanh giữa (lệch 1 bước) cạnh đối diện
        xa_ = -hb + (m // 2 - 1) * 2 * hb / (m - 1)
        xb_ = -hb + (m // 2) * 2 * hb / (m - 1)
        ln_ = math.hypot(xb_ - xa_, 2 * hb)
        ux, uy = (xb_ - xa_) / ln_, 2 * hb / ln_
        tie(c, "DAI", cx + xa_ + rt * uy, cy - hb - rt * ux, ux, uy, ln_, rt, 2.2)
        tie(c, "DAI", cx - hb - rt * ux, cy + xb_ - rt * uy, uy, -ux, ln_, rt, 2.2)
        dg = (xa_, xb_, ux, uy)
    xo = yo = None
    if grp:
        i = max(grp)
        xo = abs(-hb + i * 2 * hb / (m - 1)) + 0.41421356 * rt
        yo = hb + rt
        c.pl("DAI", True, [(cx - xo, cy + yo), (cx + xo, cy + yo), (cx + yo, cy + xo), (cx + yo, cy - xo),
                           (cx + xo, cy - yo), (cx - xo, cy - yo), (cx - yo, cy - xo), (cx - yo, cy + xo)])
    # bu lông neo (lỗ) trong cổ móng, quanh tim đỉnh cổ
    o = kk * model.bolt_gap(p, g.bb) / 2
    rb = 0.5 * kk * model.bolt_dia(p) / 1000.0
    bc = hh - kk * g.b1 / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = cx + bc + sx * o, cy + bc + sy * o
            c.ci("CHU", x, y, rb)
            c.ln("CHU", x - 1.6 * rb, y, x + 1.6 * rb, y)
            c.ln("CHU", x, y - 1.6 * rb, x, y + 1.6 * rb)
    bx = cx + hh + 5.0
    sp = 2 * hb / (m - 1)
    co([(cx - hb + i * sp, cy + hb) for i in range(m)], bx, cy + hh + 5.0, 1, 4,
       f"{n}%%C{ni(dia)}", tick=False, mode=True)
    co([(cx + hb0, cy + 0.55 * hh)], bx, cy + 0.55 * hh, 1, 5, phi(p["RT_D"], p["RT_S"]), mode=True)
    if grp:
        # nét xẹt 45° trùng thanh xiên của đai bát giác -> xoay vuông góc thanh (quy tắc app cũ)
        tx6, ty6 = cx + 0.5 * (xo + yo), cy - 0.5 * (xo + yo)
        co([(tx6, ty6)], bx, cy - 0.15 * hh, 1, 6, phi(p["RP_D"], p["RP_S"]), mode=True, tick=False)
        tick_at(c, tx6, ty6, -45.0)
    if st:
        xi = -hb + max(st) * sp
        sole = sorted(st) != sorted(m - 1 - j for j in st)
        yv = cy - 0.8 * hh
        # nhánh lên đai ngang: đoạn đứng đặt giữa 2 thanh chủ, không trùng đai phụ đứng / bu lông
        vx = [-hb + j * sp + rt for j in st]
        cand = [-hb + (i + 0.5) * sp for i in range(m - 1)]
        cand = [x for x in cand if x > 0.1 * hb and all(abs(x - t) > 0.3 * sp for t in vx)
                and all(abs(cx + x - (cx + bc + q * o)) > 2.0 * rb for q in (-1, 1))] or cand
        xh = min(cand, key=lambda x: abs(x - 0.55 * hb))
        co([(cx + xi + rt, yv), (cx + xh, cy + xi - rt)], bx, yv, 1, 7, phi(p["RP_D"], p["RP_S"]),
           "SO LE" if sole else None, mode=True)
    if dg:
        # đai xiên (số hiệu riêng): chỉ vào đai xiên gần ngang, phía phải
        xa_, xb_, ux, uy = dg
        x9 = 0.62 * hb
        t9 = (x9 + hb + rt * ux) / uy
        y9 = xb_ - rt * uy - ux * t9
        co([(cx + x9, cy + y9)], bx, cy + y9, 1, 9, phi(p["RP_D"], p["RP_S"]), mode=True)
    nm = ensure_dimstyle(c.doc, den)
    if g.tp > 1e-6:
        b2 = kk * g.b2
        x0, y0 = cx + hh - b2, cy + hh - b2
        c.dimH("DIM", (cx - hh, cy + hh), (cx + hh, cy + hh), cy + hh + 10.0, dimname=nm)
        c.dimH("DIM", (x0, y0), (cx + hh, y0), y0 - 4.5, dimname=nm)
        c.dimV("DIM", (x0, y0), (x0, cy + hh), x0 - 4.5, dimname=nm)
        sc_title(c, cx + hh - b2 / 2, y0 - 13.0, "MẶT CẮT 1-1", den)
        return
    c.dimH("DIM", (cx - hh, cy - hh), (cx + hh, cy - hh), cy - hh - 4.5, dimname=nm)
    c.dimV("DIM", (cx - hh, cy - hh), (cx - hh, cy + hh), cx - hh - 4.5, dimname=nm)
    sc_title(c, cx, cy - hh - 13.0, "MẶT CẮT 1-1", den)


def mesh(c: Ctx, g: Geo, co: Callouts, cx, cy):
    p = g.p
    den = mesh_den(g)
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
    tkkt = model.is_tkkt(g.p)               # TKKT: không có bảng thép, tag không ghi số hiệu
    co = Callouts(c, g, nonum=tkkt)
    k = 1000.0 / pier_den(g)
    ks = 1000.0 / slab_den(g)
    cx = 125.0 if tkkt else 95.0
    with c.group("pier", "Bố trí thép trụ"):
        pier_section(c, g, co, cx, 276.0)
    ytop = 276.0 - 14.0 - k * (model.TL + 0.0) - 28.0 - k * g.H
    with c.group("plan", "Thép bản đế"):
        slab_plan(c, g, co, cx, ytop - 10.0 - ks * (g.Bh + model.ML), slab_den(g))
    xm, y11, ym, hp, ex = right_layout(g, tkkt)
    with c.group("sec11", "Mặt cắt 1-1"):
        col_section(c, g, co, xm + ex / 2, y11)
    with c.group("mesh", "Lưới thép đầu trụ"):
        mesh(c, g, co, xm, ym)
    note = ["- XEM GHI CHÚ CHUNG TẠI BẢN VẼ SỐ: " + str(g.p.get("CODE", "")),
            "- KÍCH THƯỚC GHI TRÊN BẢN VẼ TÍNH BẰNG mm."]
    if tkkt:
        note_at(c, 268.0, 90.0, note)
        return
    mode, place, rh = table_plan(g)
    if mode == "s3":
        note.append(f"- BẢNG KÍCH THƯỚC TỪNG THANH XEM TỜ {getattr(g, 'tables_ref', '3/3')}.")
    if mode == "s1":
        note.append("- BẢNG THỐNG KÊ CỐT THÉP XEM TỜ 1/2.")
        note_at(c, XT, 280.0, note)
    else:
        ytb = tables.steel_table(c, g, XT, 280.0, 120.0)
        note_at(c, XT, ytb - 10.0, note)
    for pos, x, y in place or []:
        tables.bar_table(c, g, x, y, pos, rh=rh)


# ---------------------------------------------------------------------------
# bảng kích thước từng thanh: đặt ở khoảng trống giữa tờ 2, không đủ chỗ thì chuyển hết sang tờ 3
BAR_POS = (2, 3, 4, 5, 6, 7, 9)
MX0 = XT - 5.0 - sum(tables.BT_CW)                  # mép trái cột bảng giữa tờ 2
MID_BOT = 15.0
COLS3 = (25.0, 121.0, 217.0, 313.0)                  # tờ 3: 4 cột bảng, cách khung (x 20..410) 5 mm
TOP3, BOT3, BOT3_KT = 276.0, 16.0, 70.0             # cột chạm khung tên (x > 262, cao tới y 65) dừng ở 70


def bar_list(g: Geo):
    return [p for p in BAR_POS if tables.bar_table_h(g, p) > 0]


def right_layout(g: Geo, tkkt=False):
    """Vị trí mặt cắt 1-1 và lưới đầu trụ: (xm, y11, ym, hp, ex)."""
    kk = 1000.0 / sec_den(g)
    hp = 1000.0 / mesh_den(g) * g.bb / 2                # nửa lưới đầu trụ
    hs = kk * g.b1 / 2                                  # nửa tiết diện 1-1
    ex = kk * g.b2 - 2 * hs if g.tp > 1e-6 else 0.0     # đường bao chân cổ lòi ra trái / dưới
    xm = 285.0 if tkkt else 205.0
    y11 = 262.0 - hs
    ym = y11 - hs - ex - 30.0 - hp
    return xm, y11, ym, hp, ex


def mid_box(g: Geo):
    _, _, ym, hp, _ = right_layout(g)
    return ym - hp - 24.0, MID_BOT


# bảng thống kê cốt thép đưa sang tờ 1 (dưới bảng tổng kê) khi tờ 2 không đủ chỗ cho bảng kích thước từng thanh
S1_X, S1_TOP, S1_BOT = 268.0, 234.0, 100.0
RIGHT_TOP, RIGHT_BOT = 256.0, 72.0                 # cột phải tờ 2 (dưới ghi chú, trên khung tên)


def steel_fits_s1(g: Geo):
    h = 13.0 + 6.0 + sum(tables.row_h(r["pos"], 4.6) for r in g.kl)
    return h <= S1_TOP - S1_BOT


def _pack(g: Geo, cols, rh):
    """Xếp các bảng kích thước từng thanh vào các cột [(x, đỉnh, đáy)] -> [(pos, x, y)] hoặc None.
    Thử xếp lần lượt theo số hiệu (cột giữa trước, rồi cột phải trước); không vừa thì xếp bảng cao trước vào cột
    đầu tiên còn đủ chỗ
    (trong mỗi cột các bảng vẫn theo thứ tự số hiệu)."""
    lst = bar_list(g)
    hs = {pos: tables.BT_HH + len(g.klb[pos]) * rh for pos in lst}
    for cs in (cols, cols[::-1]):                   # giữ thứ tự số hiệu: cột giữa trước, rồi thử cột phải trước
        out, ci, y = [], 0, cs[0][1]
        for pos in lst:
            while ci < len(cs) and y - hs[pos] < cs[ci][2]:
                ci += 1
                y = cs[ci][1] if ci < len(cs) else 0.0
            if ci >= len(cs):
                break
            out.append((pos, cs[ci][0], y))
            y -= hs[pos] + tables.BT_GAP
        else:
            return out
    used = [0.0] * len(cols)
    where = {i: [] for i in range(len(cols))}
    for pos in sorted(lst, key=lambda q: -hs[q]):
        for i, (_, top, bot) in enumerate(cols):
            need = hs[pos] + (tables.BT_GAP if where[i] else 0.0)
            if used[i] + need <= top - bot:
                used[i] += need
                where[i].append(pos)
                break
        else:
            return None
    out = []
    for i, (x, top, _) in enumerate(cols):
        y = top
        for pos in sorted(where[i], key=lambda q: lst.index(q)):
            out.append((pos, x, y))
            y -= hs[pos] + tables.BT_GAP
    return out


def table_plan(g: Geo):
    """Cách bố trí bảng: ("s2" | "s1" | "s3", vị trí các bảng kích thước từng thanh trên tờ 2, chiều cao dòng).
    s2: bảng kích thước ở khoảng giữa tờ 2; s1: bảng thống kê sang tờ 1, bảng kích thước ở giữa + cột phải tờ 2;
    s3: bảng kích thước sang tờ 3."""
    if not getattr(g, "kl", None):
        g.calc_kl()
    if model.is_tkkt(g.p) or not model.is_detail(g.p):
        return "s2", [], tables.BT_RH
    top, bot = mid_box(g)
    opts = [("s2", [(MX0, top, bot)])]
    if steel_fits_s1(g) and not getattr(g, "no_s1", False):    # móng 2 loại: tờ 1 dành cho tổng kê
        opts.append(("s1", [(MX0, top, bot), (XT, RIGHT_TOP, RIGHT_BOT)]))
    for mode, cols in opts:
        for rh in (tables.BT_RH, 4.5, 4.0):
            r = _pack(g, cols, rh)
            if r is not None:
                return mode, r, rh
    return "s3", None, None


def need_sheet3(g: Geo):
    return table_plan(g)[0] == "s3"


def steel_on_s1(g: Geo):
    return table_plan(g)[0] == "s1"


def draw3(c: Ctx, g: Geo):
    """Tờ 3: các bảng kích thước từng thanh xếp theo cột."""
    ci, yy = 0, TOP3
    for pos in bar_list(g):
        h = tables.bar_table_h(g, pos) - tables.BT_GAP
        while ci < len(COLS3) - 1 and yy < TOP3 and yy - h < _bot3(ci):
            ci, yy = ci + 1, TOP3
        x = COLS3[ci]
        yy = tables.bar_table(c, g, x, yy, pos, ybot=_bot3(ci)) - tables.BT_GAP


def _bot3(ci):
    return BOT3_KT if COLS3[ci] + sum(tables.BT_CW) > 262.0 else BOT3
