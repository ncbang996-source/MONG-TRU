"""Mô hình 3D diễn hoạ cốt thép móng trụ (bê tông trong suốt + thép màu), vẽ bằng Pillow, không cần OpenGL."""
from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw

from . import model

COL = {
    "lot": (150, 150, 140), "bt": (176, 182, 96), "edge": (80, 84, 40),
    "slab_y": (200, 30, 40), "slab_x": (90, 40, 200), "slab_h": (230, 120, 0),
    "rib": (150, 0, 20), "dai": (40, 80, 230), "gia": (120, 60, 160),
    "pier": (220, 90, 20), "hoop": (30, 110, 210), "bg": (255, 255, 255),
    "tie": (0, 150, 200), "chair": (90, 90, 90), "haunch": (0, 140, 90), "mesh": (60, 60, 200),
    "bolt": (70, 70, 70), "ladder": (110, 110, 110),
}
LAYERS = ("bt", "slab", "pier", "dai")


def box(x0, x1, y0, y1, z0, z1):
    p = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return [[p[i] for i in q] for q in f]


def prism(pts, z0, z1):
    """Lăng trụ đáy đa giác pts (x, y)."""
    bot = [(x, y, z0) for x, y in pts]
    top = [(x, y, z1) for x, y in pts]
    out = [bot, top]
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        out.append([bot[i], bot[j], top[j], top[i]])
    return out


class Scene:
    """Danh sách mặt bê tông và đoạn thép (m, gốc tại tim móng, z = 0 ở đáy bản đế).
    quarter=True: chỉ hiện 1 trụ (trụ +X, +Y), đủ cả trụ."""

    def __init__(self, g, quarter=False):
        self.g = g
        self.quarter = quarter
        self.lim = (-1e9, -1e9)
        self.faces = []      # (layer, color, alpha, [pts])
        self.lines = []      # (layer, color, width_m, p0, p1)
        self.build()

    def F(self, lay, col, al, faces):
        for f in faces:
            if all(p[0] >= self.lim[0] - 1e-9 and p[1] >= self.lim[1] - 1e-9 for p in f):
                self.faces.append((lay, col, al, f))

    def L(self, lay, col, d, pts, closed=False):
        n = len(pts)
        for i in range(n if closed else n - 1):
            p0, p1 = np.array(pts[i], float), np.array(pts[(i + 1) % n], float)
            t0, t1 = 0.0, 1.0
            for ax in (0, 1):                 # xén đoạn theo mặt cắt 1/4
                a, b, m = p0[ax], p1[ax], self.lim[ax]
                if a < m and b < m:
                    t0 = 2.0
                elif a < m:
                    t0 = max(t0, (m - a) / (b - a))
                elif b < m:
                    t1 = min(t1, (m - a) / (b - a))
            if t1 - t0 > 1e-6:
                self.lines.append((lay, col, d, tuple(p0 + t0 * (p1 - p0)), tuple(p0 + t1 * (p1 - p0))))

    def pad_faces(self, X, Y, sx, sy):
        """Mặt bê tông 1/4 trụ (góc phần tư sx, sy của trụ tại X, Y)."""
        g = self.g
        B, pm, bh, hb, hv, H = g.Bh, g.pm, g.bb / 2, g.hb, g.hv, g.H
        P = lambda u, w, z: (X + sx * u, Y + sy * w, z)
        fs = [
            [P(0, 0, 0), P(B, 0, 0), P(B, B, 0), P(0, B, 0)],
            [P(B, 0, 0), P(B, B, 0), P(B, B, hv), P(B, 0, hv)],
            [P(0, B, 0), P(B, B, 0), P(B, B, hv), P(0, B, hv)],
            [P(B, 0, hv), P(B, B, hv), P(pm, pm, hb), P(pm, 0, hb)],
            [P(0, B, hv), P(B, B, hv), P(pm, pm, hb), P(0, pm, hb)],
            [P(bh, 0, hb), P(pm, 0, hb), P(pm, pm, hb), P(0, pm, hb), P(0, bh, hb), P(bh, bh, hb)],
            [P(bh, 0, hb), P(bh, bh, hb), P(bh, bh, H), P(bh, 0, H)],
            [P(0, bh, hb), P(bh, bh, hb), P(bh, bh, H), P(0, bh, H)],
            [P(0, 0, H), P(bh, 0, H), P(bh, bh, H), P(0, bh, H)],
        ]
        return fs

    def build(self):
        g = self.g
        p = g.p
        g.calc_kl() if not getattr(g, "kl", None) else None
        d = g.bt / 2
        B, cov, H = g.Bh, g.cov, g.H
        e = B - cov
        ml = model.ML
        bt, al = COL["bt"], 0.16
        piers = [(sx * d, sy * d) for sx in (-1, 1) for sy in (-1, 1)]
        if self.quarter:
            piers = [(d, d)]
        for X, Y in piers:
            hl = B + ml
            self.F("bt", COL["lot"], 0.30, [[(X - hl, Y - hl, 0.0), (X + hl, Y - hl, 0.0), (X + hl, Y + hl, 0.0),
                                             (X - hl, Y + hl, 0.0)]])
            for sx in (-1, 1):
                for sy in (-1, 1):
                    self.F("bt", bt, al, self.pad_faces(X, Y, sx, sy))
        zx, zy = g.z_bot()
        d0, d1 = g.d_top()
        hk = g.hook_top()
        db, dt = g.db, g.dt
        xb, xt = g.xs_bot(), g.xs_top()
        dch = p["RB_CH_D"] / 1000.0
        from .geom import ANCHOR, CH_LEG
        zc0 = g.covb + db
        dc = g.dc
        dh = p["RT_D"] / 1000.0
        dp = p["RP_D"] / 1000.0
        us = g.pier_us()
        w = us[-1]
        m = len(us)
        ring = [(u, -w) for u in us] + [(w, u) for u in us[1:]] + \
               [(u, w) for u in reversed(us[:-1])] + [(-w, u) for u in reversed(us[1:-1])]
        z0, z1 = g.pier_z0(), g.z_col_top()
        dl, sl = p["RL_D"] / 1000.0, p["RL_S"] / 1000.0
        wl = g.bb / 2 - cov - dh
        nd = max(1, math.ceil(2 * wl / sl - 1e-6))
        db_ = model.bolt_dia(p) / 1000.0
        ob = model.bolt_gap(p, g.bb) / 2
        grp, st = g.tie_plan()
        for X, Y in piers:
            # lưới dưới
            for y in xb:
                self.L("slab", COL["slab_x"], db, [(X - e, Y + y, zx), (X + e, Y + y, zx)])
                self.L("slab", COL["slab_y"], db, [(X + y, Y - e, zy), (X + y, Y + e, zy)])
            # lưới trên (uốn theo mặt vát)
            for a in xt:
                b_, _ = g.top_bar(a)
                for col, dd, ax in ((COL["slab_x"], d0, 0), (COL["slab_y"], d1, 1)):
                    zt = lambda t: g.ztop(t, a) - dd
                    ts = [(-e, zt(e) - hk), (-e, zt(e)), (-b_, zt(b_)), (b_, zt(b_)), (e, zt(e)), (e, zt(e) - hk)]
                    pts = [(X + t, Y + a, z) if ax == 0 else (X + a, Y + t, z) for t, z in ts]
                    self.L("slab", col, dt, pts)
            # thanh chống
            for x, y in g.chairs():
                z1c = zc0 + g.chair_body(x, y)
                sg = -1.0 if x > 0 else 1.0
                self.L("slab", COL["chair"], dch, [(X + x + sg * CH_LEG, Y + y, zc0), (X + x, Y + y, zc0),
                                                   (X + x, Y + y, z1c), (X + x + sg * CH_LEG, Y + y, z1c)])
            # thép chủ cổ móng, neo chân quay ra ngoài
            for u, v in ring:
                ax = (math.copysign(ANCHOR, u), 0.0) if abs(u) >= abs(v) - 1e-9 else (0.0, math.copysign(ANCHOR, v))
                self.L("pier", COL["pier"], dc, [(X + u, Y + v, z1), (X + u, Y + v, z0),
                                                 (X + u + ax[0], Y + v + ax[1], z0)])
            wh = g.bb / 2 - cov - dh / 2
            for z in g.hoop_zs():
                self.L("dai", COL["hoop"], dh, [(X - wh, Y - wh, z), (X + wh, Y - wh, z), (X + wh, Y + wh, z),
                                                (X - wh, Y + wh, z)], True)
            wt = w + dc / 2 + dp / 2
            for z in g.tie_zs():
                z -= 0.03
                if grp:
                    xo = abs(us[max(grp)]) + 0.41421356 * (dc / 2 + dp / 2)
                    self.L("dai", COL["tie"], dp, [(X + a_, Y + b_, z) for a_, b_ in
                                                   ((-xo, wt), (xo, wt), (wt, xo), (wt, -xo), (xo, -wt), (-xo, -wt),
                                                    (-wt, -xo), (-wt, xo))], True)
                for j in st:
                    t = us[j] + dc / 2 + dp / 2
                    self.L("dai", COL["tie"], dp, [(X + t, Y - wt, z), (X + t, Y + wt, z)])
                    self.L("dai", COL["tie"], dp, [(X - wt, Y + t, z - dp), (X + wt, Y + t, z - dp)])
            # lưới đầu trụ
            for zz in g.mesh_zs():
                for j in range(nd + 1):
                    o = -wl + j * 2 * wl / nd
                    self.L("pier", COL["mesh"], dl, [(X + o, Y - wl, zz), (X + o, Y + wl, zz)])
                    self.L("pier", COL["mesh"], dl, [(X - wl, Y + o, zz - dl), (X + wl, Y + o, zz - dl)])
            # bu lông neo (phần nhô lên)
            for bx in (-1, 1):
                for by in (-1, 1):
                    px, py = X + bx * ob, Y + by * ob
                    self.L("pier", COL["bolt"], db_ * 0.8, [(px, py, H), (px, py, H + 0.25)])
                    hn = 0.9 * db_
                    for zn in (H + 0.06, H + 0.14):
                        self.L("pier", COL["bolt"], 0.012, [(px - hn, py - hn, zn), (px + hn, py - hn, zn),
                                                           (px + hn, py + hn, zn), (px - hn, py + hn, zn)], True)
        _ = m

    def bounds(self):
        pts = np.array([p for f in self.faces for p in f[3]] or [(0, 0, 0)])
        return pts.min(0), pts.max(0)


def model_bolt_d(p):
    """Đường kính bu lông (m) đọc từ chữ BLN, vd 'BLN-M56' -> 0.056."""
    import re
    m_ = re.search(r"M\s*(\d+)", str(p.get("BLN", "")))
    return (int(m_.group(1)) if m_ else 36) / 1000.0


def axes2d(yaw, pitch):
    """Hướng 2D (phải, lên) của 3 trục X, Y, Z trên màn hình (để vẽ biểu tượng trục)."""
    R = rot(yaw, pitch)
    return [(R[0, i], R[1, i]) for i in range(3)]


def rot(yaw, pitch):
    cy_, sy_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    return np.array([[cy_, -sy_, 0.0], [sy_ * sp, cy_ * sp, cp], [-sy_ * cp, -cy_ * cp, sp]])   # hàng: phải, lên, về phía người xem


def render(scene: Scene, w=1200, h=800, yaw=-35.0, pitch=28.0, zoom=1.0, layers=LAYERS, ss=2,
           pan=(0.0, 0.0), fast=False, center=None) -> Image.Image:
    """Chiếu song song (trục đo), mặt bê tông trong suốt vẽ xa -> gần, sau đó thép xa -> gần.
    Tỷ lệ theo mặt cầu bao mô hình nên không nhảy khi xoay. fast: bản nháp khi đang kéo chuột."""
    if fast:
        ss = 1
    W, Hh = w * ss, h * ss
    R = rot(yaw, pitch)
    lo, hi = scene.bounds()
    ctr = (lo + hi) / 2
    rad = max(1e-3, 0.5 * float(np.linalg.norm(hi - lo)))
    k = zoom * 1.3 * min(W, Hh) / (2 * rad)
    c2 = R @ (ctr if center is None else np.asarray(center, float))
    ox = W / 2 - k * c2[0] + pan[0] * ss
    oy = Hh / 2 + k * c2[1] + pan[1] * ss

    def proj(pts):
        return np.asarray(pts, float) @ R.T

    def scr(q):
        return [(ox + k * a, oy - k * b) for a, b in q[:, :2]]

    img = Image.new("RGBA", (W, Hh), COL["bg"] + (255,))
    if "bt" in layers:
        fs = []
        for lay, col, al, f in scene.faces:
            qq = proj(f)
            fs.append((qq[:, 2].mean(), col, al, scr(qq)))
        fs.sort(key=lambda t: t[0])
        for _, col, al, pts in fs:          # ghép từng mặt trong khung bao của nó (nhanh hơn ghép cả ảnh)
            x0 = max(0, int(min(p[0] for p in pts)) - 1)
            y0 = max(0, int(min(p[1] for p in pts)) - 1)
            x1 = min(W, int(max(p[0] for p in pts)) + 2)
            y1 = min(Hh, int(max(p[1] for p in pts)) + 2)
            if x1 <= x0 or y1 <= y0:
                continue
            tile = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
            ImageDraw.Draw(tile).polygon([(a - x0, b - y0) for a, b in pts], fill=col + (int(255 * al),))
            img.alpha_composite(tile, (x0, y0))
        dr = ImageDraw.Draw(img, "RGBA")
        for _, col, al, pts in fs:
            dr.line(pts + [pts[0]], fill=COL["edge"] + (120,), width=max(1, ss))
    dr = ImageDraw.Draw(img)
    ls = [t for t in scene.lines if t[0] in layers]
    if ls:
        p0 = proj([t[3] for t in ls])
        p1 = proj([t[4] for t in ls])
        dep = (p0[:, 2] + p1[:, 2]) / 2
        s0, s1 = scr(p0), scr(p1)
        for i in np.argsort(dep):
            col, d = ls[i][1], ls[i][2]
            wd = max(1, int(round(k * d * 1.1)))
            dr.line([s0[i], s1[i]], fill=col + (255,), width=wd)
    img = img.convert("RGB")
    return img if ss == 1 else img.resize((w, h), Image.LANCZOS)
