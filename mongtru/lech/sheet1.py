"""Tờ 1 móng 2 loại: mặt cắt A-A (qua 2 trụ khác loại, cao độ riêng từng trụ, hố đào riêng / chung đáy bậc),
mặt bằng 4 trụ (ghi tên loại trong từng bản đế), bảng tổng kê cả vị trí móng.

Dùng lại hàm vẽ 1 trụ của bản 4 trụ giống nhau (mongtru/sheet1.py) - không sửa file đó."""
from __future__ import annotations

import numpy as np

from .. import model
from ..cad import Ctx, txtw
from ..sheet1 import T_AXIS, T_FILL, T_SOIL, XMAX, bolts_aa, col_x, draw_route, pad_aa, pad_plan, tim_mong, top_sq
from ..tables import TH
from ..view import V, elev, marker, note_at, sym, sym_r, title
from . import model as lm

SD = model.SLOPE_DRAW


class Lay:
    """Bố trí giấy tờ 1: gs = [Geo loại 1, Geo loại 2] (cùng tỷ lệ tờ 1)."""

    def __init__(self, mp, gs):
        self.mp, self.gs = mp, gs
        self.den = int(mp["SCALE"] + 0.5)
        self.k = k = 1000.0 / self.den
        self.btd = lm.draw_bt(mp, self.den)
        self.squeezed = self.btd < mp["BT"] - 1e-6
        self.T = self.btd / 2
        ts = mp["TYPES"]
        self.P = [(self.btd + lm.tp(t)) / 2 for t in ts]          # tâm bản đế thể hiện của từng loại
        self.ta = lm.type_at(mp)
        self.joint = lm.pit_joint_draw(mp)
        self.a, self.b, self.ax = lm.section_pair(mp)
        self.iL, self.iR = self.ta[self.a], self.ta[self.b]
        # mặt cắt: cao độ tuyệt đối -> giấy; đỉnh trụ cao nhất tại 262.2
        self.zmax = max(lm.z_top(t) for t in ts)
        self.ytop0 = 262.2
        ext = 0.0
        for i in (self.iL, self.iR):
            t = ts[i]
            ext = max(ext, self.P[i] + t["B"] / 2 + mp["MPIT"] + SD * (lm.ground(t) - lm.z_pit(t)))
        self.ext = ext
        # bên phải mặt cắt: chữ "đất đắp đầm chặt" trên mái ngoài hố phải, rồi kích thước + cao độ trụ phải
        t = ts[self.iR]
        xf = self.P[self.iR] + t["B"] / 2 + mp["MPIT"] + 0.55 * SD * (lm.ground(t) - lm.z_pit(t)) - ext
        self.ro = max(0.0, k * xf + 4.4 + txtw(T_FILL, 2.0) + 3.0 - 9.2)
        self.cx = min(max(105.0, 66.0 + k * ext), XMAX + 38.0 - 43.0 - self.ro - k * ext)
        self.zmin = min(lm.z_pit(ts[i]) for i in (self.iL, self.iR))
        self.yd = self.y(self.zmin) - 10.4
        self.planTop = self.yd - 24.0
        top_i = [self.ta[1], self.ta[2]]
        self.cy = self.planTop - k * max(self.P[i] + ts[i]["B"] / 2 + model.ML for i in top_i)
        for i, g in enumerate(gs):                                # các hàm vẽ cũ dùng g.ytop, g.k
            g.ytop = self.y(lm.z_top(ts[i]))

    def y(self, z):
        return self.ytop0 + self.k * (z - self.zmax)

    def bt_txt(self, add=0.0):
        return f"{1000 * (self.mp['BT'] + add):.0f}" if self.squeezed else "<>"


def rdp(pts, tol):
    """Rút gọn đường gấp khúc (Ramer-Douglas-Peucker)."""
    if len(pts) < 3:
        return pts
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    dx, dy = x1 - x0, y1 - y0
    n = max(1e-12, (dx * dx + dy * dy) ** 0.5)
    dm, im = -1.0, 0
    for i in range(1, len(pts) - 1):
        d = abs(dy * (pts[i][0] - x0) - dx * (pts[i][1] - y0)) / n
        if d > dm:
            dm, im = d, i
    if dm <= tol:
        return [pts[0], pts[-1]]
    return rdp(pts[:im + 1], tol)[:-1] + rdp(pts[im:], tol)


def _runs(mask):
    out, cur = [], []
    for j, v in enumerate(mask):
        if v:
            cur.append(j)
        elif cur:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def _cross(us, gz, sz, j0, j1):
    """Điểm mặt hố cắt mặt đất giữa 2 mẫu j0, j1."""
    d0, d1 = gz[j0] - sz[j0], gz[j1] - sz[j1]
    t = d0 / (d0 - d1) if abs(d0 - d1) > 1e-12 else 0.5
    return us[j0] + t * (us[j1] - us[j0]), gz[j0] + t * (gz[j1] - gz[j0])


def _above(c, us, gz, L, pts, n=60):
    """Vẽ đường gấp khúc pts (giấy), chỉ phần nằm trên mặt đất (mặt cắt: us, gz)."""
    k, cx = L.k, L.cx
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        t = np.linspace(0.0, 1.0, n + 1)
        xs, ys = x0 + t * (x1 - x0), y0 + t * (y1 - y0)
        zg = np.interp((xs - cx) / k, us, gz)
        ok = ys >= L.y(zg) - 0.05
        for run in _runs(ok):
            j0, j1 = run[0], run[-1]
            if j1 > j0:
                c.ln("HINH THUC", xs[j0], ys[j0], xs[j1], ys[j1])


def section_profiles(L, step=0.005):
    """Mẫu theo mặt cắt A-A (toạ độ ngang u của hình): (u, cao độ mặt đất, cao độ mặt hố đào) - lấy theo khoảng cách
    tim trụ thể hiện, mái hố thể hiện 1:SLOPE_DRAW."""
    mp = dict(L.mp, BT=L.btd)
    G, S = lm.ground_fn(mp), lm.pit_surface(mp, L.joint, SD)
    pa, pb = L.P[L.iL], L.P[L.iR]
    qa = lm.QUAD[L.a]
    e = L.ext + 8.0 / L.k
    us = np.arange(-e, e + step / 2, step)
    if L.ax == "x":
        xs, ys = us, np.full_like(us, qa[1] * (pa + pb) / 2)
    else:
        xs, ys = np.full_like(us, qa[0] * (pa + pb) / 2), us
    return us, G(xs, ys), S(xs, ys)


def _ztxt(z):
    return "%%p0.00" if abs(z) < 5e-4 else f"{z:+.2f}m"


# ---------------------------------------------------------------------------
def draw_section(c: Ctx, L: Lay):
    mp, k, cx = L.mp, L.k, L.cx
    ts = mp["TYPES"]
    sides = [(-1, L.iL), (1, L.iR)]
    info = {}
    for s, i in sides:
        t, g = ts[i], L.gs[i]
        xc = s * L.P[i]
        v = V(c, cx, L.y(lm.z_pad(t)), L.den)
        pad_aa(v, g, xc, so=s)                                    # cổ vát ra phía ngoài
        zb, zg = lm.z_pit(t), lm.ground(t)
        wb = t["B"] / 2 + mp["MPIT"]
        info[s] = dict(t=t, g=g, v=v, xc=xc, zb=zb, zg=zg, wb=wb, yb=L.y(zb), yg=L.y(zg))
    X = lambda u: cx + k * u                                       # noqa: E731
    lo, hi = info[-1], info[1]
    # ---- mặt đất (hạ cao độ) và hố đào: giao tuyến của mặt đất / mặt hố với mặt cắt (toạ độ thể hiện)
    us, gz, sz = section_profiles(L)
    cuts = []
    for s in (-1, 1):
        d = info[s]
        cuts.append(col_x(d["g"], d["xc"], s, d["zg"] - lm.z_pad(d["t"])))
    ins = sz < gz - 1e-9
    for run in _runs(ins):                                         # nét hố: đáy + mái, 2 đầu nối vào mặt đất
        pts = [(us[j], sz[j]) for j in run]
        j0, j1 = run[0], run[-1]
        if j0 > 0:
            pts.insert(0, _cross(us, gz, sz, j0 - 1, j0))
        if j1 < len(us) - 1:
            pts.append(_cross(us, gz, sz, j1, j1 + 1))
        c.pl("HINH THUC", False, [(X(u), L.y(z)) for u, z in rdp(pts, 0.002)])
    out = np.ones(len(us), bool)                                   # mặt đất (sau khi đắp), ngắt tại cổ móng
    for a_, b_ in cuts:
        out &= ~((us > a_) & (us < b_))
    for run in _runs(out):
        pts = [(us[j], gz[j]) for j in run]
        if len(pts) > 1:
            c.pl("HINH THUC", False, [(X(u), L.y(z)) for u, z in rdp(pts, 0.002)])
    # ---- trục, ký hiệu đối xứng, bu lông
    ylt = min(lo["yb"], hi["yb"])
    for s in (-1, 1):
        d = info[s]
        g = d["g"]
        c.ln("TRUC", X(s * L.T), g.ytop + 4.3, X(s * L.T), d["yb"] - 2.2)
        if g.tp > 1e-6:
            c.ln("TRUC", X(d["xc"]), L.y(lm.z_pad(d["t"]) + g.hb) + 2.0, X(d["xc"]), d["yb"] - 2.2)
    ytopm = max(info[s]["g"].ytop for s in (-1, 1))
    c.ln("TRUC", cx, ylt - 1.5, cx, ytopm + 4.4)
    sym(c, cx, ytopm - 0.5)
    for s in (-1, 1):
        bolts_aa(c, info[s]["g"], X(s * L.T))
    gR = hi["g"]
    xb = X(L.T) + k * model.bolt_gap(gR.p, gR.bb) / 2 + 1.1
    yb = gR.ytop + 2.5
    with c.item("bln", "Ghi chú bu lông"):
        c.ln("CHU", xb, yb, xb + 6.0, yb, fixed1=True)
        c.tx("CHU", xb + 7.0, yb - 0.8, 2.0, mp["BLN"])
    # ---- ụ đất thừa đắp lại quanh mỗi cổ móng
    for s in (-1, 1):
        d = info[s]
        g, t = d["g"], d["t"]
        pa = d["yg"] + 3.1
        zp = lm.z_pad(t)
        cl_, cr_ = col_x(g, d["xc"], s, d["zg"] + 3.1 / k - zp)
        for sg, xcol in ((-1, cl_), (1, cr_)):
            xp = X(d["xc"] + sg * g.Bh)
            xa = xp - sg * min(3.2, abs(X(xcol) - xp) - 0.5)
            # mái hạ cao độ cắt qua: bỏ phần nét ụ đất nằm dưới mặt đất
            _above(c, us, gz, L, [(xp, d["yg"]), (xa, pa), (X(xcol), pa)])
    d = lo
    xl = X(d["xc"] - 0.5 * d["g"].Bh)
    pa = d["yg"] + 3.1
    with c.item("soil", "Ghi chú đất thừa"):
        w = txtw(T_SOIL, 2.0)
        c.pl("CHU", False, [(xl, pa - 0.6), (xl - 4.2, pa + 5.0), (xl - 4.7 - w, pa + 5.0)], fixed=(0,))
        c.tx("CHU", xl - 4.6 - w, pa + 5.8, 2.0, T_SOIL)
    d = hi
    xf = X(d["xc"] + d["wb"] + 0.55 * SD * (d["zg"] - d["zb"]))
    with c.item("fill", "Ghi chú đất đắp đầm chặt"):
        c.pl("CHU", False, [(xf, d["yg"] - 2.5), (xf + 4.0, d["yg"] + 4.5),
                            (xf + 4.4 + txtw(T_FILL, 2.0), d["yg"] + 4.5)], fixed=(0,))
        c.tx("CHU", xf + 4.2, d["yg"] + 5.3, 2.0, T_FILL)
    # ---- tên loại móng: leader từ mặt vát bản đế ra phía ngoài
    for s in (-1, 1):
        d = info[s]
        g, t = d["g"], d["t"]
        u = d["xc"] + s * 0.5 * (g.pm + g.Bh)
        zs = lm.z_pad(t) + g.hv + (g.hb - g.hv) * (g.Bh - abs(u - d["xc"])) / (g.Bh - g.pm)
        px, py = X(u), L.y(zs)
        name = t["NAME"]
        w = txtw(name, 2.0)
        with c.item(f"tname{s}", f"Tên loại móng {name}"):
            c.pl("CHU", False, [(px, py), (px + s * 3.0, py + 4.0), (px + s * (3.6 + w), py + 4.0)], fixed=(0,))
            c.txj("CHU", px + s * 3.3, py + 4.8, 2.0, name, 0 if s > 0 else 2)
    # ---- cao độ: trụ trái bên trái, trụ phải bên phải
    for s in (-1, 1):
        d = info[s]
        t = d["t"]
        xg = X(s * L.ext) + (L.ro if s > 0 else 0.0)
        x1 = xg + s * 21.0
        x2 = xg + s * 13.2
        d["x1"], d["x2"] = x1, x2
        ex = x2 - 17.4 if s < 0 else x2 + 17.4
        ex2 = x2 - 5.4 if s < 0 else x2 + 5.4
        elev(c, ex, L.y(lm.z_pad(t)), _ztxt(lm.z_pad(t)))
        elev(c, ex, d["yg"], _ztxt(d["zg"]))
        elev(c, ex2, d["g"].ytop, _ztxt(lm.z_top(t)))
    title(c, cx, L.yd - 8.5, "MẶT CẮT A-A", f"TL:1/{L.den}")
    return info


def dim_section(c: Ctx, L: Lay, info):
    k, cx = L.k, L.cx
    X = lambda u: cx + k * u                                       # noqa: E731
    w100 = txtw("100", 2.0)
    for s in (-1, 1):
        d = info[s]
        g, t = d["g"], d["t"]
        ybase = L.y(lm.z_pad(t))
        xa = d["x2"] - s * 4.0
        c.dimV("DIM", (xa, d["yg"]), (xa, ybase), d["x1"])
        c.dimV("DIM", (xa, d["yg"]), (xa, g.ytop), d["x1"])
        ys = [ybase, ybase + k * g.hv, ybase + k * g.hb, d["yg"], g.ytop]
        for j in range(4):
            tp = (d["x2"] - s * 2.0, ybase + k * (g.hv + g.hb) / 2 + 0.6) \
                if j == 1 and k * (g.hb - g.hv) < w100 + 1 else None
            c.dimV("DIM", (xa, ys[j]), (xa, ys[j + 1]), d["x2"], tp)
        # dày lót
        xl = X(d["xc"] + s * (g.Bh + model.ML))
        xd = X(d["xc"] + s * d["wb"]) + s * 4.0
        c.dimV("DIM", (xl, ybase), (xl, d["yb"]), xd, (xd + s * 2.0, d["yb"] - 1.0 - w100 / 2))
        # dưới: lót, Bm, lót
        hl, hb_ = k * (g.Bh + model.ML), k * g.Bh
        x0 = X(d["xc"])
        yb = d["yb"]
        yd = yb - 10.4                                     # kích thước đáy ngay dưới từng trụ
        c.dimH("DIM", (x0 - hb_, yb), (x0 + hb_, yb), yd)
        c.dimH("DIM", (x0 - hl, yb), (x0 - hb_, yb), yd, (x0 - hb_ + 1.0 + w100 / 2, yd + 2.0))
        c.dimH("DIM", (x0 + hb_, yb), (x0 + hl, yb), yd, (x0 + hb_ - 1.0 - w100 / 2, yd + 2.0))
        # mép hố phía ngoài
        xo, xp = X(d["xc"] + s * (g.Bh + model.ML)), X(d["xc"] + s * d["wb"])
        if abs(xp - xo) > 0.5:
            w = txtw(f"{1000 * (d['wb'] - g.Bh - model.ML):.0f}", 2.0)
            c.dimH("DIM", (xo, yb), (xp, yb), yd, (xp + s * (1.0 + w / 2), yd + 2.0) if abs(xp - xo) < w + 1 else None)
        # gờ quanh chân cổ móng + cạnh chân cổ b2 khi cổ vát
        yg = ybase + k * g.hb
        for sg in (-1, 1):
            xe, xf = x0 + sg * k * g.b2 / 2, x0 + sg * k * g.pm
            tx = xf + sg * (1.0 + w100 / 2)
            c.dimH("DIM", (xe, yg), (xf, yg), yg + 4.0, (tx, yg + 5.2) if k * model.MPL < w100 + 1 else None)
        if g.tp > 1e-6:
            c.dimH("DIM", (x0 - k * g.b2 / 2, yg), (x0 + k * g.b2 / 2, yg), yg + 4.0)
    # trên: cổ móng từng trụ; chuỗi mép bản đế - tim đỉnh - tim đỉnh - mép bản đế
    ytm = max(info[s]["g"].ytop for s in (-1, 1))
    y2 = ytm + 12.9
    for s in (-1, 1):
        g = info[s]["g"]
        xc = s * L.T
        c.dimH("DIM", (X(xc - g.bb / 2), g.ytop), (X(xc + g.bb / 2), g.ytop), g.ytop + 6.0)
    lo, hi = info[-1], info[1]
    c.dimH("DIM", (X(lo["xc"] - lo["g"].Bh), lo["yg"]), (X(-L.T), lo["g"].ytop + 4.3), y2)
    c.dimH("DIM", (X(-L.T), lo["g"].ytop + 4.3), (X(L.T), hi["g"].ytop + 4.3), y2, text=L.bt_txt())
    c.dimH("DIM", (X(L.T), hi["g"].ytop + 4.3), (X(hi["xc"] + hi["g"].Bh), hi["yg"]), y2)


# ---------------------------------------------------------------------------
def draw_plan(c: Ctx, L: Lay):
    mp, k = L.mp, L.k
    ts = mp["TYPES"]
    v = V(c, L.cx, L.cy, L.den)
    cx, cy = L.cx, L.cy
    pc = {}
    dq = dim_piers(mp)
    for q, i, sx, sy in lm.piers(mp):
        g = L.gs[i]
        xc, yc = sx * L.P[i], sy * L.P[i]
        pc[q] = (i, sx, sy, xc, yc)
        pad_plan(c, g, v, xc, yc, True, sx=sx, sy=sy)
        name = ts[i]["NAME"]
        # tên loại ở phía trong (giữa mép gờ và mép bản đế, như bản vẽ mẫu)
        u = 0.72 * g.Bh
        if q in dq:
            if g.tp > 1e-6:          # cổ vát: 2 phía đều có kích thước -> đặt dưới đường kích thước b1
                u = min(g.Bh - 2.0 / k, max(u, g.pm + 9.6 / k))
            else:                    # phía trong có kích thước b1 -> ghi ở phía ngoài
                u = -u
        with c.item(f"pname{q}", f"Tên loại móng trụ {q}"):
            c.txc("CHU", v.x(xc), v.y(yc - sy * u), 2.2, name)
    E = max(L.P[i] + ts[i]["B"] / 2 for i in range(2)) + 0.3
    for s in (-1, 1):
        v.ln("TRUC", s * L.T, -E, s * L.T, E)
        v.ln("TRUC", -E, s * L.T, E, s * L.T)
    v.ln("TRUC", -E, 0.0, E, 0.0)
    _ground_step_plan(c, L, v, E)
    tim_mong(c, cx, cy, 1.2)
    with c.item("axis", "Ghi chú tim móng"):
        w = txtw(T_AXIS, 2.0)
        if int(mp["HT"]) == 1:
            c.pl("CHU", False, [(cx, cy), (cx + 3.0, cy - 4.7), (cx + 4.0 + w, cy - 4.7)], fixed=(0,))
            c.tx("CHU", cx + 3.9, cy - 4.7 + 0.9, 2.0, T_AXIS)
        else:
            c.pl("CHU", False, [(cx, cy), (cx - 3.0, cy + 4.7), (cx - 4.0 - w, cy + 4.7)], fixed=(0,))
            c.tx("CHU", cx - 3.9 - w, cy + 4.7 + 0.9, 2.0, T_AXIS)
    i1, i3 = L.ta[1], L.ta[3]
    reach = k * min(L.P[i] + ts[i]["B"] / 2 for i in range(2))
    lx = k * min(L.P[i] + 0.6 * ts[i]["B"] / 2 for i in (i1, i3))
    draw_route(c, L.gs[i1], cx, cy, reach, lx)
    # biên (giấy) theo từng phía
    def ext(qs):
        return max(L.P[pc[q][0]] + ts[pc[q][0]]["B"] / 2 + model.ML for q in qs)
    El, Er, Et, Eb = ext((1, 3)), ext((2, 4)), ext((1, 2)), ext((3, 4))
    # ký hiệu đối xứng đầu trên trục đứng + bên trái trục ngang
    gap = k * (min(L.P[pc[q][0]] - ts[pc[q][0]]["B"] / 2 for q in (1, 2)))
    ys0 = v.y(Et) + 3.0
    v.ln("TRUC", 0.0, -E, 0.0, 0.0)
    c.ln("TRUC", cx, cy, cx, ys0 + 3.5)
    sym(c, cx, ys0)
    sym_r(c, v.x(-El) - 3.0, cy, 90.0)
    # ký hiệu mặt cắt A-A
    a = pc[L.a]
    if L.ax == "x":
        ya = a[4]
        marker(c, v.x(-El) - 22.0, cy + k * ya, 1.0, "A")
        marker(c, v.x(Er) + 14.0, cy + k * ya, -1.0, "A")
    else:
        xa = a[3]
        marker(c, cx + k * xa, v.y(-Eb) - 22.0, -1.0, "A", 90.0)
        marker(c, cx + k * xa, v.y(Et) + 14.0, 1.0, "A", 90.0)
    _dims(c, L, v, pc, El, Er, Et, Eb, ys0, gap)
    title(c, cx, v.y(-Eb) - 25.0, "MẶT BẰNG MÓNG", f"TL:1/{L.den}")


def dim_piers(mp) -> list:
    """Trụ ghi kích thước cổ móng trên mặt bằng: 1 trụ mỗi loại (ưu tiên cột bên phải)."""
    out, done = [], set()
    ta = lm.type_at(mp)
    for q in (2, 4, 1, 3):
        if ta[q] not in done:
            done.add(ta[q])
            out.append(q)
    return out


def step_lines(mp, cx, cy, w, E):
    """Đường mép trên và chân mái hạ cao độ trên mặt bằng: [(mép trên: [đoạn]), (chân mái: [đoạn])] trong khung ±E.
    Vùng cao = các góc phần tư của trụ cao (đỉnh (cx, cy)); chân mái cách mép trên w (vào vùng thấp)."""
    lv = {q: lm.ground(mp["TYPES"][lm.type_at(mp)[q]]) for q in range(1, 5)}
    hi = max(lv.values())
    H = {lm.QUAD[q] for q, z in lv.items() if z > hi - 1e-9}
    if len(H) == 4:
        return [], []
    if len(H) == 2:                                  # nửa mặt phẳng
        sxs = {q[0] for q in H}
        if len(sxs) == 1:                            # vùng cao 1 phía theo x
            sx = sxs.pop()
            return [[(cx, -E), (cx, E)]], [[(cx - sx * w, -E), (cx - sx * w, E)]]
        sy = {q[1] for q in H}.pop()
        return [[(-E, cy), (E, cy)]], [[(-E, cy - sy * w), (E, cy - sy * w)]]
    Q = next(iter(H)) if len(H) == 1 else next(q for q in lm.QUAD.values() if q not in H)
    qx, qy = Q
    din = -1 if len(H) == 1 else 1                   # hướng vào vùng thấp: ra khỏi góc cao / vào góc thấp
    top = [[(cx + qx * E, cy), (cx, cy), (cx, cy + qy * E)]]
    tx, ty = cx + din * qx * w, cy + din * qy * w
    toe = [[(cx + qx * E, ty), (tx, ty), (tx, cy + qy * E)]]
    return top, toe


def _ground_step_plan(c, L, v, E):
    """Mặt bằng: đường mép trên (nét liền) và chân mái (nét đứt) chỗ hạ cao độ mặt đất."""
    mp = L.mp
    zs = [lm.ground(t) for t in mp["TYPES"]]
    dz = abs(zs[0] - zs[1])
    if dz < 1e-6:
        return
    w = dz * mp.get("GM", 1.0)
    top, toe = step_lines(mp, mp.get("GX", 0.0), mp.get("GY", 0.0), w, E)
    clip = lambda p: (max(-E, min(E, p[0])), max(-E, min(E, p[1])))    # noqa: E731
    with c.item("gstep", "Hạ cao độ mặt đất"):
        for seg in top:
            v.pl("HINH THUC", False, [clip(p) for p in seg])
        for seg in toe:
            pts = [clip(p) for p in seg]
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                ln = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
                n = max(1, int(ln * L.k / 3.0))
                for j in range(0, n, 2):          # nét đứt 1.5 mm
                    a, b = j / n, min(1.0, (j + 1) / n)
                    v.ln("HINH THUC", x0 + a * (x1 - x0), y0 + a * (y1 - y0), x0 + b * (x1 - x0), y0 + b * (y1 - y0))
        # ký hiệu mái taluy: vạch vuông góc mép trên, chĩa về phía thấp, dài 0.3 m / ngắn 0.15 m xen kẽ, bước 0.15 m
        G = lm.ground_fn(dict(mp, BT=L.btd))
        for sg in top:
            pts = [clip(p) for p in sg]
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                ln = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
                if ln < 1e-6:
                    continue
                ux, uy = (x1 - x0) / ln, (y1 - y0) / ln
                nx, ny = -uy, ux
                xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
                e = 0.05
                if G(np.array([xm + nx * e]), np.array([ym + ny * e]))[0] > \
                        G(np.array([xm - nx * e]), np.array([ym - ny * e]))[0]:
                    nx, ny = -nx, -ny                   # pháp tuyến về phía thấp
                for j in range(1, int(ln / 0.15)):
                    s0 = j * 0.15
                    tl = min(w, 0.3 if j % 2 else 0.15)
                    px, py = x0 + ux * s0, y0 + uy * s0
                    v.ln("HINH THUC", px, py, px + nx * tl, py + ny * tl)
        seg = [clip(p) for p in toe[0]]                   # ghi chú tại góc / giữa đường chân mái
        lx, ly = seg[1] if len(seg) == 3 else ((seg[0][0] + seg[1][0]) / 2, (seg[0][1] + seg[1][1]) / 2)
        c.tx("CHU", v.x(lx) + 1.0, v.y(ly) + 1.0, 1.8, f"MÁI HẠ CAO ĐỘ 1:{mp.get('GM', 1.0):g}")
    # kích thước mép trên chỗ hạ cao độ -> tim móng (khi không trùng tim)
    gx, gy = mp.get("GX", 0.0), mp.get("GY", 0.0)
    for sg in top:
        for (x0, y0), (x1, y1) in zip(sg, sg[1:]):
            if abs(x1 - x0) < 1e-9 and abs(gx) > 1e-6:          # mép trên theo phương đứng (x = GX)
                yd = y0 + 0.75 * (max(-E, min(E, y1)) - y0) if abs(y1 - y0) < 2 * E - 1e-6 else 0.75 * E
                v.dimH((0.0, yd), (gx, yd), v.y(yd))
            if abs(y1 - y0) < 1e-9 and abs(gy) > 1e-6:          # mép trên theo phương ngang (y = GY)
                xd = x0 + 0.75 * (max(-E, min(E, x1)) - x0) if abs(x1 - x0) < 2 * E - 1e-6 else 0.75 * E
                v.dimV((xd, 0.0), (xd, gy), v.x(xd))


def _dims(c, L, v, pc, El, Er, Et, Eb, ys0, gap):
    mp, ts = L.mp, L.mp["TYPES"]
    w100 = txtw("100", 2.0)
    ml = model.ML
    x0, y0 = v.x(-El), v.y(-Eb)

    def chain(q_lo, q_hi, vert):
        il, ih = pc[q_lo][0], pc[q_hi][0]
        Pl, Bl = L.P[il], ts[il]["B"] / 2
        Ph, Bh = L.P[ih], ts[ih]["B"] / 2
        ys = [-(Pl + Bl + ml), -(Pl + Bl), -L.T, L.T, Ph + Bh, Ph + Bh + ml]
        for j in range(5):
            tp = None
            if j in (0, 4):
                pos = (v.y if vert else v.x)(ys[j]) - 1.0 - w100 / 2 if j == 0 else \
                    (v.y if vert else v.x)(ys[j + 1]) + 1.0 + w100 / 2
                tp = (x0 - 7.0 - 2.0, pos) if vert else (pos, y0 - 7.0 + 2.0)
            txt = L.bt_txt() if j == 2 else "<>"
            if vert:
                v.dimV((-El, ys[j]), (-El, ys[j + 1]), x0 - 7.0, tp, text=txt)
            else:
                v.dimH((ys[j], -Eb), (ys[j + 1], -Eb), y0 - 7.0, tp, text=txt)
        tot = L.bt_txt(Pl + Bl + Ph + Bh - L.btd) if L.squeezed else "<>"
        if vert:
            v.dimV((-El, ys[1]), (-El, ys[4]), x0 - 14.0, text=tot)
        else:
            v.dimH((ys[1], -Eb), (ys[4], -Eb), y0 - 14.0, text=tot)
    chain(3, 1, True)
    chain(3, 4, False)
    # bản đế: dọc bên phải (trụ 2, 4), ngang phía trên (trụ 1, 2)
    for q in (2, 4):
        i, sx, sy, xc, yc = pc[q]
        B = ts[i]["B"] / 2
        v.dimV((xc + B, yc - B), (xc + B, yc + B), v.x(Er) + 5.0)
    for q in (1, 2):
        i, sx, sy, xc, yc = pc[q]
        B = ts[i]["B"] / 2
        if gap > 7.0:
            v.dimH((xc - B, yc + B), (xc + B, yc + B), v.y(Et) + 5.0)
        else:
            # khe hẹp: đường gióng phía trục đứng đi qua ký hiệu đối xứng -> tự vẽ, ngắt quãng qua ký hiệu
            inner = 1 if sx > 0 else 2
            v.dimH((xc - B, yc + B), (xc + B, yc + B), v.y(Et) + 7.5, override={f"dimse{inner}": 1})
            xg = v.x(xc - sx * B)
            c.ln("DIM", xg, v.y(yc + B) + 1.0, xg, ys0 - 2.6)
            c.ln("DIM", xg, ys0 + 3.4, xg, v.y(Et) + 8.5)
    # cổ móng (đỉnh b1 phía trong, chân b2 phía ngoài) trên 1 trụ mỗi loại
    for q in dim_piers(mp):
        i, sx, sy, xc, yc = pc[q]
        g = L.gs[i]
        x0_, y0_, x1_, y1_ = top_sq(g, xc, yc, sx, sy)
        bh, pm = g.b2 / 2, g.pm
        yi = y0_ if sy > 0 else y1_
        xi = x0_ if sx > 0 else x1_
        v.dimH((x0_, yi), (x1_, yi), v.y(yc - sy * pm) - sy * 4.0)
        v.dimV((xi, y0_), (xi, y1_), v.x(xc - sx * pm) - sx * 4.0)
        if g.tp > 1e-6:
            v.dimH((xc - bh, yc + sy * bh), (xc + bh, yc + sy * bh), v.y(yc + sy * pm) + sy * 4.0)
            v.dimV((xc + sx * bh, yc - bh), (xc + sx * bh, yc + bh), v.x(xc + sx * pm) + sx * 4.0)


# ---------------------------------------------------------------------------
def summary_cols(mp, gs):
    """Cột bảng tổng kê cả vị trí móng: bê tông, lót, thép từng Ø (cộng 2 loại, có dự phòng), bu lông."""
    dpk = 1.0 + mp.get("DP", 0.0) / 100.0
    by = {}
    for g in gs:
        for d, _, w in g.klc:
            by[int(d + 0.5)] = by.get(int(d + 0.5), 0.0) + w
    by = {d: w for d, w in by.items() if w > 1e-6}
    cols = [(mp["BTM"], "(m3)", 14.0, f"{lm.vol_mong(mp):.2f}"),
            (mp["BTL"], "(m3)", 13.0, f"{lm.vol_lot(mp):.2f}")]
    for d in sorted(by):
        cols.append((f"%%C{d}", "(kg)", 14.0, f"{by[d] * dpk:.2f}"))
    if by:
        cols.append(("TỔNG K.LƯỢNG", "THÉP (kg)", 19.0, f"{sum(by.values()) * dpk:.2f}"))
    cols.append(("BULONG", "NEO", 18.0, lm.bolt_text(mp)))
    return cols


def summary(c: Ctx, mp, gs, xr, y0):
    """Bảng tổng kê (như tables.summary), số liệu cho cả vị trí móng (2 loại)."""
    cols = summary_cols(mp, gs)
    w = sum(x[2] for x in cols)
    hh, rh = 12.0, 8.0
    x0 = xr - w
    with c.table("summary", "Bảng tổng kê"):
        c.txj("BANG", x0 + w / 2, y0 + 1.6, 2.2, "BẢNG TỔNG KÊ KHỐI LƯỢNG CHO 01 VỊ TRÍ MÓNG", 1, underline=True)
        for y in (y0, y0 - hh, y0 - hh - rh):
            c.ln("BANG", x0, y, xr, y)
        xs = x0
        c.ln("BANG", xs, y0, xs, y0 - hh - rh)
        for col in cols:
            xs += col[2]
            c.ln("BANG", xs, y0, xs, y0 - hh - rh)
        xs = x0
        for col in cols:
            xm = xs + col[2] / 2
            c.txc("BANG", xm, y0 - 3.8, TH, col[0])
            c.txc("BANG", xm, y0 - 8.4, TH, col[1])
            c.txc("BANG", xm, y0 - hh - 4.0, TH, col[3])
            xs += col[2]
    return y0 - hh - rh - 5.0


def draw(c: Ctx, mp, gs):
    for g in gs:
        if not getattr(g, "kl", None):
            g.calc_kl()
    L = Lay(mp, gs)
    with c.group("section", "Mặt cắt A-A"):
        info = draw_section(c, L)
        dim_section(c, L, info)
    with c.group("plan", "Mặt bằng móng"):
        draw_plan(c, L)
    yb = summary(c, mp, gs, 405.0, 267.0)
    note_at(c, 268.0, min(yb - 14.0, 90.0), ["- XEM GHI CHÚ CHUNG TẠI BẢN VẼ SỐ: " + str(mp.get("CODE", "")),
                                             "- KÍCH THƯỚC GHI TRÊN BẢN VẼ TÍNH BẰNG mm, CAO ĐỘ TÍNH BẰNG m."])
    return L

