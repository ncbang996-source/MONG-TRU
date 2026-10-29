"""Bố trí hình học, cốt thép và bảng thống kê thép của móng trụ rời.

Toạ độ cục bộ 1 trụ (m): gốc tại tim bản đế, X / Y theo 2 cạnh bản đế, z từ đáy bản đế lên.
Cổ móng vát (b1 đỉnh < b2 chân): 2 mặt phía trong (phía −X, −Y, quay về tim móng) thẳng đứng, 2 mặt phía ngoài
(+X, +Y) vát. Tim đỉnh cổ (tim chân cột) cách tim bản đế (b2 − b1)/2 về phía trong; các tim đỉnh cổ cách nhau Bt,
các tim bản đế cách nhau Bt + (b2 − b1). 4 trụ giống nhau (đối xứng qua tim móng).
Thép bản đế rải theo vùng (gờ cổ móng / phần vát) như app móng bản không dầm;
khối lượng tính từ đúng các thanh vẽ ra, nhân số trụ."""
from __future__ import annotations

import math

from . import model

KGM = {6: 0.222, 8: 0.395, 10: 0.617, 12: 0.888, 14: 1.21, 16: 1.58, 18: 2.0, 20: 2.47,
       22: 2.98, 25: 3.85, 28: 4.83, 32: 6.31, 36: 7.99, 40: 9.86, 50: 15.42}
HOOK = 0.06          # móc đai, đai phụ (m)
CH_LEG = 0.1         # chân thanh chống (m)
ANCHOR = 0.5         # đoạn neo chân thép chủ cổ móng (m), cố định như app móng bản có dầm

NAMES = {1: "Thép bản đế lớp dưới", 2: "Thép bản đế lớp trên (uốn theo mặt vát)", 3: "Thanh chống",
         4: "Thép chủ cổ móng", 5: "Đai cổ móng", 6: "Đai bát giác cổ móng", 7: "Đai phụ thẳng cổ móng",
         8: "Lưới thép đầu trụ"}


def ceil_(x):
    return int(x) + 1 if x > int(x) + 1e-6 else int(x)


def kg(d, tot):
    a = KGM.get(int(d + 0.5))
    return tot * (a if a else d * d / 162.0)


def offs(ln, s):
    """Rải đều trên đoạn dài ln (tâm tại 0), 2 đầu có thanh: 1 + ceil(ln / s) thanh."""
    n = 1 + max(1, ceil_(ln / s - 1e-6))
    sa = ln / (n - 1)
    return [sa * (i - (n - 1) / 2.0) for i in range(n)]


def offs_zone(ln, pm, s):
    """Thép bản đế: rải riêng vùng gờ cổ móng |x| <= pm và vùng vát, thanh cách mép vùng 1/2 bước."""
    hl = ln / 2.0
    if pm >= hl - 1e-6:
        nf = max(1, ceil_(ln / s))
        sf = ln / nf
        return [-hl + (j + 0.5) * sf for j in range(nf)]
    nf = max(1, ceil_(2 * pm / s))
    sf = 2 * pm / nf
    ns = max(1, ceil_((hl - pm) / s))
    ss = (hl - pm) / ns
    out = [-(pm + (j - 0.5) * ss) for j in range(ns, 0, -1)]
    out += [-pm + (j + 0.5) * sf for j in range(nf)]
    out += [pm + (j - 0.5) * ss for j in range(1, ns + 1)]
    return out


def tie_plan_mg(m, gstep):
    """Bố trí đai phụ cổ móng (giữ các thanh cách nhau <= 400 mm) theo số thanh 1 cạnh m và bước giữ thanh.
    Trả về (nhóm thanh của đai bát giác, các thanh có đai phụ thẳng) - như app móng bản có dầm."""
    if m <= 2:
        return None, []
    lst, i = [], 0
    while i <= (m - 1) / 2.0:
        lst.append(i)
        i += gstep
    res = []
    for j in lst:
        if j not in res:
            res.append(j)
        if (m - 1 - j) not in res:
            res.append(m - 1 - j)
    res.sort()
    extra, cur = [], res[0]
    for nx in res[1:]:
        while nx - cur > gstep:
            cur += gstep
            extra.append(cur)
        cur = nx
    res = sorted(set(res + extra))
    ti = sorted({j for j in res if 0 < j < m - 1})
    runs, cur = [], []
    for j in ti:
        if cur and j == cur[-1] + 1:
            cur.append(j)
        else:
            if cur:
                runs.append(cur)
            cur = [j]
    if cur:
        runs.append(cur)
    grp, st = None, []
    for run in runs:
        if grp is None and len(run) >= 2 and (m - 1 - run[0]) in run:
            c = len(run) if len(run) <= 3 else (2 if len(run) % 2 == 0 else 3)
            off = (len(run) - c) // 2
            grp = run[off:off + c]
            st += [j for j in run if j not in grp]
        else:
            st += run
    return grp, sorted(st)


def group(items, extra, n):
    """Gom các thanh cùng chiều dài (làm tròn mm). items: [(chiều dài m, [L1, L2, L3] mm)].
    Trả về các dòng [L1, L2, L3, dài mm, số lượng cả móng, tổng dài m], dài trước."""
    out = {}
    for ln, dims in items:
        key = int(1000 * ln + extra + 0.5)
        if key not in out:
            out[key] = [dims, 0]
        out[key][1] += 1
    return [[d[0], d[1], d[2], key, c * n, c * n * key / 1000.0] for key, (d, c) in sorted(out.items(), reverse=True)]


class Geo:
    """Toàn bộ kích thước bố trí của 1 móng (4 trụ giống nhau)."""

    def __init__(self, p: dict):
        self.p = p
        g = self.g
        self.den = int(p["SCALE"] + 0.5)
        self.k = 1000.0 / self.den
        self.n = model.npier(p)
        self.B, self.Bh = g("B"), g("B") / 2
        self.b1, self.b2 = g("B1"), g("B2")
        self.bb = self.b1                                 # cạnh đỉnh cổ (lưới đầu trụ, mặt cắt đầu trụ)
        self.hb, self.hv = g("HB"), g("HV")
        self.H = model.H(p)
        self.bt = g("BT")
        self.tp = self.b2 - self.b1                       # độ vát (mặt ngoài lệch so với mặt trong)
        self.kz = self.tp / (self.H - self.hb)            # cạnh cổ giảm theo chiều cao (m/m)
        self.cov, self.covb = g("COVER"), g("COVER_B")
        self.pm = self.b2 / 2 + model.MPL                 # nửa gờ phẳng quanh chân cổ móng
        self.db, self.dt = g("RB_BOT_D") / 1000.0, g("RB_TOP_D") / 1000.0
        self.dc = g("RC_D") / 1000.0

    def g(self, k):
        return self.p[k]

    # ---- bản đế ---------------------------------------------------------
    def ztop(self, x, y=0.0):
        """Cao độ mặt trên bản đế tại (x, y)."""
        r = max(abs(x), abs(y))
        if r <= self.pm:
            return self.hb
        return self.hb - (self.hb - self.hv) * min(1.0, (r - self.pm) / (self.Bh - self.pm))

    def span(self):
        return self.B - 2 * self.cov

    def xs_bot(self):
        return offs_zone(self.span(), self.pm, self.g("RB_BOT_S") / 1000.0)

    def xs_top(self):
        return offs_zone(self.span(), self.pm, self.g("RB_TOP_S") / 1000.0)

    def z_bot(self):
        """(z thanh theo X - lớp ngoài cùng, z thanh theo Y) của lưới dưới."""
        z0 = self.covb + self.db / 2
        return z0, z0 + self.db

    def d_top(self):
        """Độ sâu tâm thanh (theo X - ngoài cùng, theo Y) của lưới trên, tính từ mặt bê tông."""
        d0 = self.cov + self.dt / 2
        return d0, d0 + self.dt

    def hook_top(self):
        """Chân móc 2 đầu thanh lớp trên (m): hv − cv − cvb − 2(Ø dưới + Ø trên), làm tròn XUỐNG tới 5 mm
        -> đầu móc luôn cao hơn mặt trên lưới dưới."""
        h = self.hv - self.cov - self.covb - 2 * (self.db + self.dt)
        return max(0.0, 0.005 * math.floor(h / 0.005 + 1e-6))

    def top_bar(self, a):
        """Thanh lớp trên nằm tại toạ độ ngang a: (nửa đoạn phẳng, chiều dài đoạn xiên mỗi bên).
        Đoạn phẳng trong phạm vi gờ (và phần vát chỉ thấp hơn theo phương vuông góc), đoạn xiên tới mép."""
        e = self.Bh - self.cov
        u = max(0.0, (abs(a) - self.pm) / (self.Bh - self.pm))
        b = self.pm + u * (self.Bh - self.pm)            # điểm bắt đầu xiên theo phương thanh
        dz = (self.hb - self.hv) * max(0.0, (e - self.pm) / (self.Bh - self.pm) - u)
        d = math.hypot(e - b, dz)
        if d < 0.06:
            return e, 0.0
        return b, d

    def chair_grid(self):
        """Thanh chống trên 1 trụ: [(i, j, x, y)] - lưới @ trong phạm vi bản đế trừ 1 bước mỗi bên (i, j: chỉ số
        hàng / cột của lưới). Thanh gần hàng thép chủ cổ móng dời vào trong / ra ngoài để tránh thép chủ."""
        s = self.g("RB_CH_S") / 1000.0
        xs = offs(max(s, self.span() - 2 * s), s)
        w = self.b2 / 2 - self.inset()                   # hàng thép chủ tại mặt gờ (z = hb), đối xứng qua tim
        cl = self.dc / 2 + self.g("RB_CH_D") / 2000.0 + 0.04
        out = []
        for i, x in enumerate(xs):
            for j, y in enumerate(xs):
                r = max(abs(x), abs(y))
                f = (w - cl if r < w else w + cl) / r if r > 1e-9 and abs(r - w) < cl else 1.0
                out.append((i, j, x * f, y * f))
        return out

    def chairs(self):
        return [(x, y) for _, _, x, y in self.chair_grid()]

    def chair_body(self, x, y):
        """Chiều cao thân thanh chống = chiều cao bản đế tại vị trí thanh − 2 lớp bê tông bảo vệ (cv + cvb)
        − 2Ø (Ø lớp dưới + Ø lớp trên)."""
        return self.ztop(x, y) - self.cov - self.covb - self.db - self.dt

    # ---- cổ móng --------------------------------------------------------
    def z_col_top(self):
        return self.H - self.cov

    def mesh_zs(self):
        s = self.g("RL_S") / 1000.0
        return [self.z_col_top() - i * s for i in range(int(self.g("RL_N")))]

    def hoop_zs(self):
        """Đai cổ móng: đai dưới từng lớp lưới đầu trụ (bước lưới), còn lại @ đai tới mặt gờ bản đế."""
        dl = self.g("RL_D") / 1000.0
        top = [z - 2 * dl for z in self.mesh_zs()]
        z0, z1 = top[-1], self.hb
        s = self.g("RT_S") / 1000.0
        if z0 - z1 <= 1e-6:
            return top
        n = 1 + max(1, ceil_((z0 - z1) / s - 1e-6))
        return top + [z0 - i * (z0 - z1) / (n - 1) for i in range(1, n)]

    def tie_zs(self):
        """Mức đai phụ (thẳng, bát giác): rải @ đai phụ từ đỉnh xuống mặt gờ."""
        z0, z1 = self.hoop_zs()[0], self.hb
        s = self.g("RP_S") / 1000.0
        n = 1 + max(1, ceil_((z0 - z1) / s - 1e-6))
        return [z0 - i * (z0 - z1) / (n - 1) for i in range(n)]

    def pier_z0(self):
        """Cao độ chân thép chủ cổ móng (tựa trên lưới dưới)."""
        return self.covb + 2 * self.db

    def pier_vert(self):
        return self.z_col_top() - self.pier_z0()

    def m_bars(self):
        return 1 + int(self.g("RC_N") / 4.0)

    def b_at(self, z):
        """Cạnh cổ móng tại cao độ z (kéo dài thẳng xuống trong bản đế)."""
        return self.b2 - self.kz * (z - self.hb)

    def x_in(self):
        """Mặt trong (thẳng đứng) của cổ móng."""
        return -self.b2 / 2

    def col_c(self, z):
        """Tim tiết diện cổ móng tại cao độ z (theo X và theo Y như nhau)."""
        return -self.b2 / 2 + self.b_at(z) / 2

    def top_c(self):
        """Tim đỉnh cổ móng (tim chân cột, cụm bu lông) so với tim bản đế."""
        return -self.tp / 2

    def inset(self):
        """Từ mặt bê tông tới tâm thép chủ cổ móng."""
        return self.cov + self.g("RT_D") / 1000.0 + self.dc / 2

    def bar_u(self, i, z):
        """Toạ độ tâm thanh thép chủ thứ i (tính từ mặt trong) trên 1 cạnh cổ móng, tại cao độ z."""
        c, m = self.inset(), self.m_bars()
        return self.x_in() + c + i * (self.b_at(z) - 2 * c) / (m - 1)

    def ring(self):
        """Chỉ số (i, j) các thanh thép chủ trên chu vi cổ móng."""
        m = self.m_bars()
        return [(i, j) for i in range(m) for j in range(m) if i in (0, m - 1) or j in (0, m - 1)]

    def pier_us(self, z=None):
        """Toạ độ tâm thép chủ 1 cạnh cổ móng tại cao độ z (mặc định đỉnh)."""
        z = self.z_col_top() if z is None else z
        return [self.bar_u(i, z) for i in range(self.m_bars())]

    def tie_plan(self):
        m = self.m_bars()
        w = 1000.0 * (self.bb - 2 * self.cov)
        if m <= 2 or (w <= 400.0 and m <= 4):
            return None, []
        s = w / (m - 1)
        return tie_plan_mg(m, max(1, min(2, int(400.0 / s))))

    def oct_dim(self, b=None):
        """(nửa cạnh thẳng, nửa bề rộng) đai bát giác (m) với cạnh cổ b - như app móng bản có dầm."""
        b = self.bb if b is None else b
        grp = self.tie_plan()[0]
        m = self.m_bars()
        kk = 40.0
        r = max(0.35, 0.5 * self.g("RC_D") / 1000.0 * kk)
        hb = kk * (b / 2 - self.g("COVER")) - 0.2 - r
        rt = r + 0.12
        s = 2 * hb / (m - 1)
        return ((max(grp) - (m - 1) / 2.0) * s + 0.41421356 * rt) / kk, (hb + rt) / kk

    # ---- khối lượng thép ------------------------------------------------
    def calc_kl(self):
        """Bảng thống kê thép cho 01 móng (NPIER trụ). Mỗi dòng: dict(pos, dia, len, qty, tot, kg, dims, name)."""
        g, n = self.g, self.n
        cov = self.cov
        rows = []

        def R(pos, dia, ln, cnt, dims):
            """ln: chiều dài 1 thanh (m, có thể là trung bình), cnt: số thanh 1 trụ."""
            if cnt <= 0 or ln <= 1e-6:
                return
            tot = cnt * n * ln
            rows.append(dict(pos=pos, dia=dia, len=1000 * ln, qty=f"{cnt}x{n}", tot=tot, kg=kg(dia, tot),
                             dims=dims, name=NAMES[pos], n=cnt * n))
        # 1: lớp dưới, 2 phương
        sp = self.span()
        R(1, g("RB_BOT_D"), sp, 2 * len(self.xs_bot()), [1000 * sp])
        # 2: lớp trên, 2 phương - từng thanh dài khác nhau
        hk = self.hook_top()
        grp2, cnt2, tot2, sd, sf = {}, 0, 0.0, 0.0, 0.0
        for a in self.xs_top():
            b, d = self.top_bar(a)
            key = (int(2000 * b + 0.5), int(1000 * d + 0.5))
            grp2[key] = grp2.get(key, 0) + 2              # 2 phương
            cnt2 += 2
            ln = 2 * b + 2 * d + 2 * hk
            tot2 += 2 * ln
            sd += 2 * d
            sf += 4 * b
        b2 = []
        for (fl, d), c in sorted(grp2.items(), key=lambda t: (-t[0][0], t[0][1])):
            ln = fl + 2 * d + 2000 * hk
            b2.append([fl, d, 1000 * hk, ln, c * n, c * n * ln / 1000.0])
        R(2, g("RB_TOP_D"), tot2 / cnt2, cnt2, [1000 * sd / cnt2, 1000 * sf / cnt2, 1000 * hk, 1000 * hk])
        # 3: thanh chống - thân cao theo mặt vát
        grp3, tot3, ch = {}, 0.0, self.chairs()
        for x, y in ch:
            body = self.chair_body(x, y)
            key = int(1000 * body + 0.5)
            grp3[key] = grp3.get(key, 0) + 1
            tot3 += body + 2 * CH_LEG
        b3 = []
        for body, c in sorted(grp3.items(), reverse=True):
            ln = body + 2000 * CH_LEG
            b3.append([body, 1000 * CH_LEG, 1000 * CH_LEG, ln, c * n, c * n * ln / 1000.0])
        R(3, g("RB_CH_D"), tot3 / len(ch), len(ch), [1000 * CH_LEG, 1000 * CH_LEG, 1000 * (tot3 / len(ch) - 2 * CH_LEG)])
        # 4: thép chủ cổ móng, neo chân - cổ vát: thanh nghiêng theo vị trí, dài khác nhau
        vert = self.pier_vert()
        m = self.m_bars()
        q = self.kz * vert / (m - 1)
        lens = [math.sqrt(vert ** 2 + (i * q) ** 2 + (j * q) ** 2) for i, j in self.ring()]
        b4 = group([(L_, [1000 * L_, 1000 * ANCHOR, 0.0]) for L_ in lens], 1000 * ANCHOR, n)
        avg = sum(lens) / len(lens)
        R(4, g("RC_D"), avg + ANCHOR, len(lens), [1000 * ANCHOR, 1000 * avg])
        # 5: đai cổ móng - cạnh theo cao độ
        hz = self.hoop_zs()
        sides = [self.b_at(z) - 2 * cov for z in hz]
        b5 = group([(4 * s_ + 2 * HOOK, [1000 * s_, 1000 * HOOK, 0.0]) for s_ in sides], 0.0, n)
        sa = sum(sides) / len(sides)
        R(5, g("RT_D"), 4 * sa + 2 * HOOK, len(hz), [1000 * HOOK, 1000 * sa])
        # 6: đai bát giác, 7: đai phụ thẳng - theo cao độ
        grp, st = self.tie_plan()
        tz = self.tie_zs()
        nt = len(tz)
        b6 = b7 = []
        if grp:
            od = [self.oct_dim(self.b_at(z)) for z in tz]
            lo = [8 * a_ + 4 * math.sqrt(2) * (f_ - a_) + 2 * HOOK for a_, f_ in od]
            b6 = group([(L_, [2000 * a_, 1414.2136 * (f_ - a_), 1000 * HOOK]) for L_, (a_, f_) in zip(lo, od)], 0.0, n)
            a_ = sum(x[0] for x in od) / nt
            f_ = sum(x[1] for x in od) / nt
            R(6, g("RP_D"), sum(lo) / nt, nt, [2000 * a_, 1414.2136 * (f_ - a_), 1000 * HOOK])
        if st:
            s7 = [self.b_at(z) - 2 * cov for z in tz]
            b7 = group([(s_ + 2 * HOOK, [1000 * s_, 1000 * HOOK, 1000 * HOOK]) for s_ in s7 for _ in range(2 * len(st))],
                       0.0, n)
            sa7 = sum(s7) / nt
            R(7, g("RP_D"), sa7 + 2 * HOOK, nt * 2 * len(st), [1000 * HOOK, 1000 * sa7, 1000 * HOOK])
        # 8: lưới thép đầu trụ
        hh = self.bb / 2 - cov
        nn = 1 + ceil_(2 * hh / (g("RL_S") / 1000.0) - 1e-6)
        R(8, g("RL_D"), 2 * hh, int(g("RL_N")) * 2 * nn, [2000 * hh])
        cls = {}
        for r in rows:
            a = cls.setdefault(r["dia"], [0.0, 0.0])
            a[0] += r["tot"]
            a[1] += r["kg"]
        self.kl = rows
        self.klc = sorted((d, v[0], v[1]) for d, v in cls.items())
        self.klb = {2: b2, 3: b3}
        for pos, bt_ in ((4, b4), (5, b5), (6, b6), (7, b7)):
            if len(bt_) > 1:                          # cổ móng vát: chiều dài từng thanh khác nhau
                self.klb[pos] = bt_
        self.seq = {r["pos"]: i for i, r in enumerate(rows, 1)}
        return rows

    def dp(self):
        """Hệ số dự phòng thép (1 + DP%)."""
        return 1.0 + self.g("DP") / 100.0

    def sq(self, num) -> str:
        """Số vị trí hiển thị liên tục 1..n."""
        try:
            return str(self.seq.get(int(num), num))
        except (ValueError, AttributeError):
            return str(num)
