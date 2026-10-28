"""Tiện ích vẽ dùng chung 2 tờ: khung nhìn theo tỷ lệ, ký hiệu, chú thích thép, uốn góc thép."""
from __future__ import annotations

import math

from .cad import Ctx, ensure_dimstyle, txtw


def ni(x):
    return str(int(x + 0.5))


def phi(d, s):
    return f"%%C{ni(d)}@{ni(s)}"


class V:
    """Khung nhìn: toạ độ cục bộ (m) -> giấy (mm). u theo phương ngang hình, v theo phương đứng."""

    def __init__(self, c: Ctx, ox, oy, den):
        self.c, self.ox, self.oy = c, ox, oy
        self.den = int(den)
        self.k = 1000.0 / self.den
        self.dimname = ensure_dimstyle(c.doc, self.den)

    def x(self, u):
        return self.ox + self.k * u

    def y(self, v):
        return self.oy + self.k * v

    def P(self, u, v):
        return (self.ox + self.k * u, self.oy + self.k * v)

    def ln(self, lay, u1, v1, u2, v2, **kw):
        a, b = self.P(u1, v1), self.P(u2, v2)
        return self.c.ln(lay, a[0], a[1], b[0], b[1], **kw)

    def pl(self, lay, closed, pts, **kw):
        return self.c.pl(lay, closed, [self.P(*q) for q in pts], **kw)

    def rect(self, lay, u1, v1, u2, v2):
        return self.c.rect(lay, self.x(u1), self.y(v1), self.x(u2), self.y(v2))

    def disc(self, lay, u, v, r):
        return self.c.disc(lay, self.x(u), self.y(v), r)

    def rbar(self, dmm):
        """Bán kính chấm thép trên giấy (mm), tối thiểu 0.2."""
        return max(0.2, 0.5 * self.k * dmm / 1000.0)

    def hatch(self, lay, pts, pattern, scale, **kw):
        return self.c.hatch(lay, [self.P(*q) for q in pts], pattern, scale, **kw)

    def dimH(self, p1, p2, yd, tp=None, text="<>"):
        """p1, p2 cục bộ (m); yd giấy."""
        return self.c.dimH("DIM", self.P(*p1), self.P(*p2), yd, tp, dimname=self.dimname, text=text)

    def dimV(self, p1, p2, xd, tp=None, text="<>"):
        return self.c.dimV("DIM", self.P(*p1), self.P(*p2), xd, tp, dimname=self.dimname, text=text)


# ---------------------------------------------------------------------------
# ký hiệu
def elev(c: Ctx, x, y, s):
    """Ký hiệu cao độ."""
    with c.item("elev", "Cao độ"):
        c.pl("CHU", False, [(x, y), (x + 2.2, y + 2.4), (x, y + 2.4), (x - 2.1, y + 2.4), (x, y), (x, y + 4.7),
                            (x - 8.0, y + 4.7)])
        c.ln("CHU", x + 4.4, y, x - 4.3, y)
        c.tx("CHU", x - 8.0, y + 5.5, 2.0, s)


def sym(c: Ctx, x, y):
    """Ký hiệu đối xứng: 2 nét mảnh cắt nhau + 2 móc dày ở đầu trên (gốc = giao điểm)."""
    for s in (-1.0, 1.0):
        c.ln("CHU", x + s * 2.836, y - 2.226, x - s * 3.817, y + 2.996)
        c.pl("CHU", False, [(x - s * 3.817, y + 2.996), (x - s * 5.699, y + 0.599)], width=0.5)


def sym_r(c: Ctx, x, y, ang):
    """Ký hiệu đối xứng xoay góc ang (độ) quanh giao điểm."""
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    T = lambda u, w: (x + u * ca - w * sa, y + u * sa + w * ca)
    for s in (-1.0, 1.0):
        a, b = T(s * 2.836, -2.226), T(-s * 3.817, 2.996)
        c.ln("CHU", a[0], a[1], b[0], b[1])
        c.pl("CHU", False, [b, T(-s * 5.699, 0.599)], width=0.5)


def arrow2(c: Ctx, x1, y1, x2, y2, hl=1.2, hw=0.45):
    """Đường rải thép: đoạn thẳng, 2 đầu mũi tên hở."""
    c.ln("CHU", x1, y1, x2, y2)
    d = math.hypot(x2 - x1, y2 - y1)
    if d < 1e-9:
        return
    ux, uy = (x2 - x1) / d, (y2 - y1) / d
    for px, py, sx in ((x2, y2, 1.0), (x1, y1, -1.0)):
        bx, by = px - sx * ux * hl, py - sx * uy * hl
        c.pl("CHU", False, [(bx - uy * hw, by + ux * hw), (px, py), (bx + uy * hw, by - ux * hw)])


def marker(c: Ctx, mx, my, sgn, txt, ang=0.0, mlen=7.76):
    """Ký hiệu mặt cắt: thanh đậm dọc vết cắt + mũi tên hướng nhìn + chữ.
    ang = 0: vết cắt nằm ngang, nhìn lên; sgn: thanh kéo về phía +1 / -1 theo vết cắt."""
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))

    def T(u, v):
        return (mx + u * ca - v * sa, my + u * sa + v * ca)
    with c.item("marker", "Ký hiệu mặt cắt"):
        c.pl("MAT CAT", True, [T(0, -0.4), T(sgn * mlen, -0.4), T(sgn * mlen, 0), T(0, 0)])
        ua = sgn * (mlen - 2.4)
        a, b = T(ua, -6.36), T(ua, -2.36)
        c.ln("MAT CAT", a[0], a[1], b[0], b[1])
        e = T(ua, -0.4)
        c.arrow("MAT CAT", b[0], b[1], e[0], e[1], 1.96, 0.8)
        tu = ua + sgn * 3.2
        t = T(tu, -4.3)
        c.txc("CHU", t[0], t[1], 4.0, txt)


def cut_line(c: Ctx, p1, p2, txt, side=1.0, ext=2.0):
    """2 ký hiệu mặt cắt ở 2 đầu vết cắt p1 -> p2 (giấy); side = +1: nhìn sang trái của hướng p1->p2."""
    ang = math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))
    if side < 0:
        ang += 180.0
        p1, p2 = p2, p1
    ux, uy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    marker(c, p1[0] - ux * ext, p1[1] - uy * ext, -1.0, txt, ang, 5.4)
    marker(c, p2[0] + ux * ext, p2[1] + uy * ext, 1.0, txt, ang, 5.4)


def vee(c: Ctx, x1, y1, x2, y2):
    """Mũi tên chữ V tại (x2, y2)."""
    dx, dy = x2 - x1, y2 - y1
    d = math.hypot(dx, dy)
    if d < 1e-9:
        return
    ux, uy = dx / d, dy / d
    bx, by = x2 - ux * 1.2, y2 - uy * 1.2
    c.pl("CHU", False, [(x1, y1), (x2, y2), (bx - uy * 1.6, by + ux * 1.6), (x2, y2), (bx + uy * 1.6, by - ux * 1.6)])


def title(c: Ctx, x, y, s, scale_txt):
    """Tên hình (gạch chân, cao 4) + tỷ lệ bên dưới, canh giữa tại x."""
    with c.item("title", "Tên hình"):
        c.txj("CHU", x, y, 4.0, s, 1, underline=True)
        c.txj("CHU", x, y - 4.5, 2.0, scale_txt, 1)


def brk(c: Ctx, x1, y1, x2, y2, w=1.6):
    """Đường cắt ngắt (zig-zag ở giữa)."""
    dx, dy = x2 - x1, y2 - y1
    d = math.hypot(dx, dy)
    ux, uy = dx / d, dy / d
    nx, ny = -uy, ux
    m = d / 2
    pts = [(x1 - ux * 1.5, y1 - uy * 1.5)]
    for t, o in ((m - w, 0), (m - w / 2, w), (m + w / 2, -w), (m + w, 0)):
        pts.append((x1 + ux * t + nx * o, y1 + uy * t + ny * o))
    pts.append((x2 + ux * 1.5, y2 + uy * 1.5))
    c.pl("CHU", False, pts)


def bolts_plan(c: Ctx, px, py, ph):
    """Cụm 4 bu lông neo nhìn từ trên (ph = nửa cạnh cổ móng trên giấy)."""
    o = 0.47 * ph
    r = max(0.3, 0.12 * ph)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = px + sx * o, py + sy * o
            c.ci("CHU", x, y, r)
            c.ln("CHU", x - 1.8 * r, y, x + 1.8 * r, y)
            c.ln("CHU", x, y - 1.8 * r, x, y + 1.8 * r)


BOLT_GAP = 0.05    # khe hở thực tế giữa vòng đệm / đai ốc và mặt trên cổ móng (m)


def bolt_side(c: Ctx, k, xb, ytop):
    """Bu lông neo nhìn ngang: thân + vòng đệm + 2 đai ốc."""
    gp = max(0.8, k * BOLT_GAP)
    c.rect("CHU", xb - 0.3, ytop, xb + 0.3, ytop + 3.4 + gp)
    for x0, y0, x1, y1 in ((-1.1, 0, 1.1, 0.25), (-0.8, 0.25, 0.8, 1.15), (-0.8, 1.45, 0.8, 2.35)):
        c.rect("CHU", xb + x0, ytop + gp + y0, xb + x1, ytop + gp + y1)
    return ytop + gp + 3.4


def note_at(c: Ctx, x, y, lines):
    with c.item("note", "Ghi chú"):
        c.tx("CHU", x, y, 3.5, "GHI CHÚ", underline=True)
        for i, t in enumerate(lines):
            c.tx("CHU", x, y - 5.5 - 3.6 * i, 2.0, t)


# ---------------------------------------------------------------------------
# uốn góc thép
def rcorner(a, p, b, r):
    dx, dy = p[0] - a[0], p[1] - a[1]
    l1 = math.hypot(dx, dy)
    d1x, d1y = dx / l1, dy / l1
    dx, dy = b[0] - p[0], b[1] - p[1]
    l2 = math.hypot(dx, dy)
    d2x, d2y = dx / l2, dy / l2
    cr = d1x * d2y - d1y * d2x
    dt = d1x * d2x + d1y * d2y
    ph = math.atan2(abs(cr), dt)
    tt = r * math.tan(ph / 2)
    return ((p[0] - d1x * tt, p[1] - d1y * tt), (-1 if cr < 0 else 1) * math.tan(ph / 4),
            (p[0] + d2x * tt, p[1] + d2y * tt))


def rounded(pts, closed, r):
    out, bul = [], []
    n = len(pts)
    for i, p in enumerate(pts):
        if not closed and i in (0, n - 1):
            out.append(p)
            bul.append(0.0)
            continue
        t1, bg, t2 = rcorner(pts[(i - 1) % n], p, pts[(i + 1) % n], r)
        out += [t1, t2]
        bul += [bg, 0.0]
    return out, bul


def rpl(c: Ctx, lay, pts, closed, r):
    out, bul = rounded(pts, closed, r)
    c.pl(lay, closed, out, bulges=bul)


def dai_draw(c: Ctx, lay, x0, y0, x1, y1, r, hk):
    """Đai kín bo góc bán kính r, 2 móc 45 độ ở góc dưới phải."""
    rpl(c, lay, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], True, r)
    e = r + 0.3
    c.ln(lay, x1, y0 + e, x1 - hk, y0 + e + hk)
    c.ln(lay, x1 - e, y0, x1 - e - hk, y0 + hk)


def tie(c: Ctx, lay, x0, y0, ux, uy, ln, r, tl):
    """Thanh đai phụ: thẳng, 2 đầu uốn móc 180 độ."""
    vx, vy = -uy, ux
    tp = lambda a, b: (x0 + a * ux + b * vx, y0 + a * uy + b * vy)
    c.pl(lay, False, [tp(tl, 2 * r), tp(0, 2 * r), tp(0, 0), tp(ln, 0), tp(ln, 2 * r), tp(ln - tl, 2 * r)],
         bulges=[0, 1.0, 0, 1.0, 0, 0])


def tick45(c: Ctx, x, y, fixed=False):
    c.pl("CHU", False, [(x - 0.48, y - 0.48), (x + 0.48, y + 0.48)], width=0.12, fixed=(0, 1) if fixed else ())


def tick_at(c: Ctx, x, y, ang, fixed=False):
    """Nét xẹt nghiêng góc ang (độ) - dùng khi nét 45° cố định bị trùng thanh thép xiên."""
    dx, dy = 0.68 * math.cos(math.radians(ang)), 0.68 * math.sin(math.radians(ang))
    c.pl("CHU", False, [(x - dx, y - dy), (x + dx, y + dy)], width=0.12, fixed=(0, 1) if fixed else ())


def balloon(c: Ctx, x, y, num):
    c.ci("CHU", x, y, 3.0)
    c.txc("CHU", x, y, 2.4, num)


class Callouts:
    """Chú thích số hiệu thép: các nhánh tới mục tiêu -> đoạn ngang -> vòng tròn số."""

    def __init__(self, c: Ctx, g):
        self.c, self.g = c, g

    def __call__(self, targets, bx, by, side, num, txt1, txt2=None, tick=True, mode=False):
        with self.c.item(f"callout{num}", f"Chú thích thép {self.g.sq(num)}"):
            return self._draw(targets, bx, by, side, num, txt1, txt2, tick, mode)

    def _anchor(self, me, i, tp):
        """Điểm bắt leader vào thép: cố định theo hình, chỉ dịch khi kéo riêng điểm này (id ...@t<i>)."""
        c = self.c
        if me is None:
            return tp
        from .cad import Obj
        aid = f"{me.id}@t{i}"
        d = c.offsets.get(aid)
        x, y = (tp[0] + d[0], tp[1] + d[1]) if d else tp
        gx, gy = c.off(False)
        a = Obj(aid, "anchor", "Điểm bắt leader")
        a.add(x + gx - 0.9, y + gy - 0.9)
        a.add(x + gx + 0.9, y + gy + 0.9)
        c.objs.append(a)
        return (x, y)

    def _knee(self, me, ex, by):
        """Điểm gãy leader (id ...@k): mặc định ở đầu đường tag phía hình, đi theo tag; kéo riêng để chỉnh leader."""
        c = self.c
        if me is None:
            return ex, by
        from .cad import Obj
        kid = f"{me.id}@k"
        d = c.offsets.get(kid)
        x, y = (ex + d[0], by + d[1]) if d else (ex, by)
        gx, gy = c.off(True)
        a = Obj(kid, "anchor", "Điểm gãy leader")
        a.add(x + gx - 0.9, y + gy - 0.9)
        a.add(x + gx + 0.9, y + gy + 0.9)
        c.objs.append(a)
        return x, y

    def _draw(self, targets, bx, by, side, num, txt1, txt2, tick, mode):
        """bx: điểm đầu đường tag (phía hình); tag kéo dài về phía side."""
        c = self.c
        ln = max(txtw(txt1, 2.0), txtw(txt2, 2.0) if txt2 else 0.0)
        span = 3.0 + 1.3 + ln + 2.5
        ex = bx
        bx = bx + side * span
        tx = bx - side * 4.3
        c.ln("CHU", ex, by, bx - side * 3.0, by)
        di = c.item_off()
        me = c._stack[-1] if c._stack else None
        jx, jy = self._knee(me, ex, by)           # điểm gãy (giao leader ngang với nhánh xiên / đứng), kéo được
        if abs(jx - ex) > 1e-6 or abs(jy - by) > 1e-6:
            c.ln("CHU", ex, by, jx, jy)
        for i, tp in enumerate(targets):
            tp = self._anchor(me, i, tp)
            if mode:
                xt = tp[0] - di[0]                 # đoạn đứng luôn đi qua đúng thanh thép
                c.ln("CHU", jx, jy, xt, jy)
                if abs(jy + di[1] - tp[1]) > 0.01:
                    c.ln("CHU", xt, jy, tp[0], tp[1], fixed2=True)
            else:
                c.ln("CHU", jx, jy, tp[0], tp[1], fixed2=True)
            if tick:
                tick45(c, tp[0], tp[1], fixed=True)
        c.txj("CHU", tx, by + 0.8, 2.0, txt1, 2 if side > 0 else 0)
        if txt2:
            c.txj("CHU", tx, by - 2.8, 2.0, txt2, 2 if side > 0 else 0)
        balloon(c, bx, by, self.g.sq(num))
        return min(ex, bx - 3.0), max(ex, bx + 3.0)
