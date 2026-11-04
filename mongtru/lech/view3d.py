"""Mô hình 3D móng 2 loại: dựng mô hình 4 trụ của từng loại (mongtru.view3d), giữ các trụ ở vị trí của loại đó,
dời theo cao độ đáy bản đế của loại (cao độ thiết kế − Hm)."""
from __future__ import annotations

import numpy as np

from .. import view3d
from ..geom import Geo
from . import model as lm


class MixedScene:
    def __init__(self, mp, quarter=False):
        self.faces, self.lines, self.bars, self.solids, self.axes = [], [], [], [], []
        self.z0 = None                                     # cao độ (m) ứng với z = 0 của mô hình
        z0 = min(lm.z_pad(t) for t in mp["TYPES"])
        for i, t in enumerate(mp["TYPES"]):
            qs = {lm.QUAD[q] for q in t["POS"]}
            if quarter:
                qs &= {(1, 1)}
            if not qs:
                continue
            sc = view3d.Scene(Geo(lm.type_params(mp, i)))
            dz = lm.z_pad(t) - z0
            self.z0 = z0
            sh = lambda pts, dz=dz: [(x, y, z + dz) for x, y, z in pts]
            self.bars += [(lay, col, d, sh(pts), cl, pk) for lay, col, d, pts, cl, pk in sc.bars if pk in qs]
            self.solids += [(k, pk, [sh(f) for f in fs]) for k, pk, fs in sc.solids if pk in qs]
            names = {a[0] for a in self.axes}
            for nm, a, b in sc.axes:
                s_ = -1 if nm.endswith("1") else 1
                if nm not in names and any((q[0] if nm[0] == "X" else q[1]) == s_ for q in qs):
                    self.axes.append((nm, (a[0], a[1], a[2] + dz), (b[0], b[1], b[2] + dz)))

            def q_of(pts):
                c = np.mean(np.array(pts, float), axis=0)
                return (1 if c[0] > 0 else -1, 1 if c[1] > 0 else -1)
            for lay, col, al, f in sc.faces:
                if q_of(f) in qs:
                    self.faces.append((lay, col, al, [(x, y, z + dz) for x, y, z in f]))
            for lay, col, d, p0, p1 in sc.lines:
                if q_of([p0, p1]) in qs:
                    self.lines.append((lay, col, d, (p0[0], p0[1], p0[2] + dz), (p1[0], p1[1], p1[2] + dz)))

    def bounds(self):
        pts = np.array([p for f in self.faces for p in f[3]] or [(0, 0, 0)])
        return pts.min(0), pts.max(0)
