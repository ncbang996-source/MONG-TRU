"""Móng 2 loại: đọc Excel (sheet TONG HOP có 2 khối "Móng:"), thông số từng loại, vị trí trụ, cao độ, khối lượng.

Thông số cả vị trí móng (mp): các khoá dùng chung (COMMON) + mp["TYPES"] = [loại 1, loại 2], mỗi loại là dict các
khoá riêng (TYPE_KEYS) + "NAME" (vd "T42-60"), "POS" (vị trí trụ 1..4), "CD" (cao độ thiết kế = mặt đất tại trụ, m).
type_params(mp, i) ghép thành bộ thông số đủ như bản 4 trụ giống nhau (NPIER = số trụ của loại) để dùng lại
Geo / sheet2 / kl_excel của bản cũ.

Vị trí trụ (mặt bằng, như hình trong Excel): 1 trái trên, 2 phải trên, 3 trái dưới, 4 phải dưới.
Cao độ: mặt đất tại trụ = CD; đỉnh cổ móng = CD + d; đáy bản đế = CD − Hm.
"""
from __future__ import annotations

import re

import numpy as np

from .. import model

QUAD = {1: (-1, 1), 2: (1, 1), 3: (-1, -1), 4: (1, -1)}      # vị trí trụ -> hướng (x, y) so với tim móng
ROW_OFF = 22                                                  # khối loại 2 lùi xuống 22 dòng so với loại 1

COMMON = ("GD", "COT", "TENMONG", "BTM", "BTL", "CODE", "MABV", "HT", "BT", "SLOPE", "MPIT", "DP", "SCALE",
          "PIT_DRAW", "GX", "GY", "GM", "FX", "FY", "FM", "BLN")   # bu lông neo: chung 2 loại
# hạ cao độ mặt đất (2 trụ khác cao độ thiết kế): mép trên chỗ hạ tại tim móng + (GX, GY) (m), mái 1:GM;
# bậc đáy hố đào chung (2 trụ khác cao độ đáy hố): mép trên bậc tại tim móng + (FX, FY), mái 1:FM
STEP_DEF = {"GX": 0.0, "GY": 0.0, "GM": 1.0, "FX": 0.0, "FY": 0.0, "FM": 0.5}
TYPE_KEYS = ("B", "H1", "H2", "B1", "B2", "HB", "HV", "COVER_B", "COVER",
             "RB_BOT_D", "RB_BOT_S", "RB_TOP_D", "RB_TOP_S", "RB_CH_D", "RB_CH_S",
             "RC_D", "RC_N", "RT_D", "RT_S", "RP_D", "RP_S", "RL_D", "RL_S", "RL_N",
             "TL_PIER", "TL_SLAB", "TL_11", "TL_MESH")

# ô khối loại 1 (loại 2: cùng cột, +ROW_OFF dòng)
T_NUM = {"B": "B10", "H1": "B11", "H2": "B12", "BT": "B13", "B1": "B14", "B2": "B15", "HB": "B16", "HV": "B17"}
T_REBAR = [("RB_BOT_D", "H22"), ("RB_BOT_S", "I22"), ("RB_TOP_D", "H23"), ("RB_TOP_S", "I23"),
           ("RB_CH_D", "H24"), ("RB_CH_S", "I24"),
           ("RC_D", "H26"), ("RC_N", "I26"), ("RT_D", "H27"), ("RT_S", "I27"),
           ("RP_D", "H28"), ("RP_S", "I28"), ("RL_D", "H29"), ("RL_S", "I29")]
T_COVER = {"COVER_B": "C23", "COVER": "C24"}
T_NAME, T_BLN, T_RLN, T_NP, T_POS_ROW, T_CD = "B8", ("C21", "D21"), "K29", "C25", 26, "C27"
C_SLOPE, C_MPIT, C_DP = "C19", "C20", "H52"
C_STR = {"GD": "C6", "COT": "C4", "TENMONG": "C5", "BTM": "J4", "BTL": "J5", "CODE": "J6"}
C_HT, C_MABV = "B4", ("J7", "K7")


def _sh(a, i):
    """Địa chỉ ô của loại i (0, 1)."""
    m = re.fullmatch(r"([A-Z]+)(\d+)", a)
    return f"{m.group(1)}{int(m.group(2)) + ROW_OFF * i}"


def detect(path: str, sheet: str = "TONG HOP") -> bool:
    """File Excel móng 2 loại: sheet TONG HOP có khối "Móng:" thứ 2 (A30) kèm số liệu (B32)."""
    try:
        val, close = model._open_sheet(path, sheet)
    except Exception:
        return False
    try:
        a = str(val(_sh("A8", 1)) or "").strip().lower()
        return a.startswith("móng") and model._num(val(_sh(T_NUM["B"], 1)))
    finally:
        close()


def short_name(s: str) -> str:
    """'1T42-60' -> 'T42-60' (bỏ số trụ ở đầu tên móng)."""
    s = str(s or "").strip()
    m = re.fullmatch(r"\d+\s*(T.*)", s)
    return m.group(1).strip() if m else s


def default_mp() -> dict:
    p = dict(model.default_params(), **STEP_DEF)
    mp = {k: p[k] for k in COMMON}
    t = {k: p[k] for k in TYPE_KEYS}
    mp["TYPES"] = [dict(t, NAME="T1", POS=[1], CD=0.0), dict(t, NAME="T2", POS=[2, 3, 4], CD=0.0)]
    return mp


def read_excel(path: str, sheet: str = "TONG HOP") -> tuple[dict, list[str]]:
    mp = default_mp()
    warn: list[str] = []
    val, close = model._open_sheet(path, sheet)
    num = model._num
    try:
        for k, a in C_STR.items():
            v = val(a)
            if v not in (None, ""):
                mp[k] = str(v).strip()
        mv = [val(a) for a in C_MABV]
        if mv[1] not in (None, ""):
            n_ = f"{mv[1]:g}" if num(mv[1]) else str(mv[1]).strip()
            mp["MABV"] = f"{str(mv[0] or '').strip()}{n_}"
        v = val(C_HT)
        if isinstance(v, str):
            mp["HT"] = model.ht_from_string(v)
        for k, a in (("SLOPE", C_SLOPE), ("MPIT", C_MPIT)):
            v = val(a)
            if num(v):
                mp[k] = float(v)
            else:
                warn.append(f"Ô {a} ({k}) không có số, giữ giá trị {mp[k]:g}.")
        v = val(C_DP)
        if num(v) and v >= 0:
            mp["DP"] = float(v)
        else:
            warn.append(f"Ô {C_DP} (dự phòng thép) không có số, giữ giá trị {mp['DP']:g}%.")
        bts = []
        for i, t in enumerate(mp["TYPES"]):
            ref = mp["TYPES"][0] if i else None          # ô loại 2 trống / lỗi: lấy theo loại 1
            lab = f"Loại {i + 1}"

            def fb(k, a, unit=1.0, t=t, ref=ref, lab=lab):
                if ref is not None:
                    t[k] = ref[k]
                    warn.append(f"{lab}: ô {a} ({k}) không có số, lấy theo loại 1 ({ref[k] * unit:g}).")
                else:
                    warn.append(f"{lab}: ô {a} ({k}) không có số, giữ giá trị {t[k] * unit:g}.")
            nm = val(_sh(T_NAME, i))
            t["NAME"] = short_name(nm) or f"T{i + 1}"
            for k, a0 in T_NUM.items():
                a = _sh(a0, i)
                v = val(a)
                if k == "BT":
                    if num(v) and v > 0:
                        bts.append(float(v))
                    continue
                if num(v) and v > 0 or (k == "H2" and num(v) and v >= 0):
                    t[k] = float(v)
                else:
                    fb(k, a)
            bln = "".join(str(val(_sh(a, i)) or "").strip() for a in T_BLN)
            if i == 0 and bln:                     # bu lông neo chung 2 loại: lấy theo loại 1
                mp["BLN"] = bln
            elif i == 1 and bln and bln.upper() != str(mp["BLN"]).upper():
                warn.append(f"Bu lông neo loại 2 ({bln}) khác loại 1: dùng chung {mp['BLN']}.")
            for k, a0 in T_REBAR:
                a = _sh(a0, i)
                v = val(a)
                if num(v) and v > 0:
                    t[k] = float(v)
                else:
                    fb(k, a)
            for k, a0 in T_COVER.items():
                a = _sh(a0, i)
                v = val(a)
                if num(v) and v > 0:
                    t[k] = float(v) / 1000.0
                else:
                    fb(k, a, 1000.0)
            v = val(_sh(T_RLN, i))
            if v not in (None, ""):
                try:
                    n_ = int(v) if num(v) else int("".join(c for c in str(v) if c.isdigit()) or 0)
                    if n_ > 0:
                        t["RL_N"] = float(n_)
                except ValueError:
                    pass
            pos = []
            for col in "BCDEF":
                v = val(f"{col}{T_POS_ROW + ROW_OFF * i}")
                if num(v) and int(v) in QUAD and int(v) == v:
                    pos.append(int(v))
            t["POS"] = pos
            v = val(_sh(T_NP, i))
            if num(v) and int(v) != len(pos):
                warn.append(f"{lab}: số trụ ô {_sh(T_NP, i)} = {v:g} khác số vị trí trụ đã ghi ({len(pos)}).")
            v = val(_sh(T_CD, i))
            if num(v):
                t["CD"] = float(v)
            else:
                warn.append(f"{lab}: ô {_sh(T_CD, i)} (cao độ thiết kế) không có số, lấy 0.00.")
        if bts:
            mp["BT"] = bts[0]
            if len(bts) > 1 and abs(bts[1] - bts[0]) > 1e-6:
                warn.append(f"Bt của 2 loại khác nhau ({bts[0]:g} / {bts[1]:g}): dùng Bt của loại 1.")
    finally:
        close()
    return mp, warn


# ---------------------------------------------------------------------------
def type_params(mp: dict, i: int) -> dict:
    """Bộ thông số đủ (như bản 4 trụ giống nhau) cho loại i; NPIER = số trụ của loại."""
    p = model.default_params()
    p.update({k: mp[k] for k in COMMON if k in mp})
    t = mp["TYPES"][i]
    p.update({k: t[k] for k in TYPE_KEYS})
    p["NPIER"] = float(len(t["POS"]))
    p["TYPENAME"] = t["NAME"]
    return p


def piers(mp: dict) -> list:
    """[(vị trí, loại, sx, sy)] theo vị trí 1..4."""
    out = []
    for i, t in enumerate(mp["TYPES"]):
        for q in t["POS"]:
            out.append((q, i, *QUAD[q]))
    return sorted(out)


def type_at(mp: dict) -> dict:
    """vị trí -> loại."""
    return {q: i for q, i, _, _ in piers(mp)}


def tp(t) -> float:
    return t["B2"] - t["B1"]


def pad_c(mp: dict, i: int) -> float:
    """Toạ độ tâm bản đế loại i so với tim móng (theo mỗi phương): (Bt + b2 − b1)/2."""
    return (mp["BT"] + tp(mp["TYPES"][i])) / 2


def ground(t) -> float:
    return t["CD"]


def z_top(t) -> float:
    return t["CD"] + t["H2"]


def z_pad(t) -> float:
    """Cao độ đáy bản đế."""
    return t["CD"] - t["H1"]


def z_pit(t) -> float:
    """Cao độ đáy hố đào (đáy lót)."""
    return z_pad(t) - model.TL


def validate(mp: dict) -> str | None:
    if mp.get("GM", 1.0) < 0 or mp.get("FM", 0.5) < 0:
        return "Hệ số mái hạ cao độ / bậc đáy hố không được âm."
    for i, t in enumerate(mp["TYPES"]):
        p = type_params(mp, i)
        p["NPIER"] = 4.0
        e = model.validate(p)
        if e:
            return f"Loại {i + 1} ({t['NAME']}): {e}"
    pos = [q for t in mp["TYPES"] for q in t["POS"]]
    if sorted(pos) != [1, 2, 3, 4]:
        return "Vị trí trụ của 2 loại phải gồm đủ 1, 2, 3, 4 và không trùng nhau."
    if any(not t["POS"] for t in mp["TYPES"]):
        return "Mỗi loại móng phải có ít nhất 1 vị trí trụ."
    ta = type_at(mp)
    for a, b in ((1, 2), (3, 4), (1, 3), (2, 4)):
        ia, ib = ta[a], ta[b]
        d = pad_c(mp, ia) + pad_c(mp, ib)
        if d < (mp["TYPES"][ia]["B"] + mp["TYPES"][ib]["B"]) / 2 + 0.1:
            return f"Bản đế trụ {a} và trụ {b} chồng nhau (Bt quá nhỏ so với Bm)."
    return None


def warnings(mp: dict) -> list:
    out = []
    for i in range(2):
        out += [f"Loại {i + 1}: {w}" for w in model.warnings(type_params(mp, i))]
    if pit_joint(mp) and len({round(z_pit(t), 6) for t in mp["TYPES"]}) > 1:
        # bậc đáy hố chung không được ăn vào đáy hố của trụ nào (đáy hố trụ phải đúng cao độ đáy lót)
        F = floor_fn(mp)
        bad = []
        for q, (x0, x1, y0, y1, zb) in zip(range(1, 5), pit_boxes(mp)):
            xs, ys = np.meshgrid(np.linspace(x0, x1, 21), np.linspace(y0, y1, 21))
            if np.abs(F(xs, ys) - zb).max() > 1e-3:
                bad.append(str(q))
        if bad:
            out.append(f"Bậc đáy hố đào chung cắt vào đáy hố trụ {', '.join(bad)}: chỉnh vị trí / hệ số mái bậc đáy.")
    return out


# ---------------------------------------------------------------------------
# khối lượng cả vị trí móng
def _sum(mp, f):
    return sum(f(type_params(mp, i)) for i in range(2))


def vol_mong(mp):
    return _sum(mp, model.vol_mong)


def vol_lot(mp):
    return _sum(mp, model.vol_lot)


def vol_above(mp):
    return _sum(mp, model.vol_above)


def area_vk(mp):
    return _sum(mp, model.area_vk)


def pit_of(mp, q):
    """Hố đào riêng của trụ vị trí q: (tâm x, tâm y, nửa cạnh đáy, cao độ đáy, cao độ mặt đất)."""
    i = type_at(mp)[q]
    t = mp["TYPES"][i]
    sx, sy = QUAD[q]
    c = pad_c(mp, i)
    return sx * c, sy * c, t["B"] / 2 + mp["MPIT"], z_pit(t), ground(t)


def pit_joint(mp, slope=None) -> bool:
    """True: miệng hố riêng của 2 trụ cạnh nhau chạm nhau -> đào chung 1 hố cho 4 trụ (đáy bậc theo độ sâu)."""
    m = mp["SLOPE"] if slope is None else slope
    for a, b in ((1, 2), (3, 4), (1, 3), (2, 4)):
        xa, ya, wa, za, ga = pit_of(mp, a)
        xb, yb, wb, zb, gb = pit_of(mp, b)
        d = abs(xa - xb) + abs(ya - yb)
        if d - (wa + m * (ga - za) + wb + m * (gb - zb)) <= 0:
            return True
    return False


def pit_joint_draw(mp) -> bool:
    m = int(mp.get("PIT_DRAW", 0) or 0)
    return pit_joint(mp) if m == 0 else m == 1


def _frustum_sq(a, b, h):
    return h * (a * a + b * b + a * b) / 3.0


def vol_dao_sep(mp) -> float:
    """Đào riêng từng trụ: tổng chóp cụt, mỗi hố từ đáy hố tới mặt đất tại trụ đó."""
    v = 0.0
    for q in range(1, 5):
        _, _, w, zb, zg = pit_of(mp, q)
        h = zg - zb
        v += _frustum_sq(2 * w, 2 * (w + mp["SLOPE"] * h), h)
    return v


def joint_area(mp, z) -> float:
    """Diện tích hố chung tại cao độ z: hình chữ nhật bao các hố riêng đang có ở cao độ đó
    (hố trụ i có từ đáy hố tới mặt đất tại trụ i)."""
    m = mp["SLOPE"]
    xs0, xs1, ys0, ys1 = [], [], [], []
    for q in range(1, 5):
        x, y, w, zb, zg = pit_of(mp, q)
        if zb - 1e-9 <= z <= zg + 1e-9:
            h = w + m * (z - zb)
            xs0.append(x - h)
            xs1.append(x + h)
            ys0.append(y - h)
            ys1.append(y + h)
    if not xs0:
        return 0.0
    return (max(xs1) - min(xs0)) * (max(ys1) - min(ys0))


def vol_dao_joint(mp) -> float:
    """Đào chung 1 hố, đáy bậc: tích phân diện tích theo cao độ. Giữa 2 mức đáy / mặt đất liên tiếp, cạnh hố
    biến thiên tuyến tính (cùng hệ số mái) -> diện tích bậc 2 -> công thức Simpson cho kết quả đúng."""
    zs = sorted({round(v, 9) for q in range(1, 5) for v in pit_of(mp, q)[3:]})
    v = 0.0
    for z0, z1 in zip(zs, zs[1:]):
        e = 1e-7 * (z1 - z0)
        a0, am, a1 = joint_area(mp, z0 + e), joint_area(mp, (z0 + z1) / 2), joint_area(mp, z1 - e)
        v += (z1 - z0) / 6 * (a0 + 4 * am + a1)
    return v


def _dist_quads(x, y, quads, cx, cy):
    """Khoảng cách từ điểm (x, y) tới hợp các góc phần tư quads (sx, sy) có đỉnh tại (cx, cy)."""
    d = np.full(np.shape(x), np.inf)
    for sx, sy in quads:
        dx = np.maximum(0.0, -sx * (x - cx))
        dy = np.maximum(0.0, -sy * (y - cy))
        d = np.minimum(d, np.maximum(dx, dy))     # mái phẳng: 2 mặt mái giao nhau ở góc
    return d


def _step_fn(levels, cx, cy, m):
    """Mặt có bậc: levels {vị trí trụ: cao độ}. Vùng các trụ cao nhất (góc phần tư quanh đỉnh (cx, cy)) ở mức cao,
    ra ngoài vùng đó hạ theo mái 1:m tới mức thấp."""
    hi, lo = max(levels.values()), min(levels.values())
    if hi - lo < 1e-9:
        return lambda x, y: np.full(np.shape(x), hi, dtype=float)
    quads = [QUAD[q] for q, z in levels.items() if z > hi - 1e-9]
    m = max(1e-6, m)
    return lambda x, y: np.maximum(lo, hi - _dist_quads(x, y, quads, cx, cy) / m)


def ground_fn(mp):
    """Mặt đất tự nhiên G(x, y): cao độ thiết kế của từng trụ, hạ cao độ tại tim móng + (GX, GY), mái 1:GM."""
    lv = {q: ground(mp["TYPES"][type_at(mp)[q]]) for q in range(1, 5)}
    return _step_fn(lv, mp.get("GX", 0.0), mp.get("GY", 0.0), mp.get("GM", 1.0))


def floor_fn(mp):
    """Đáy hố đào chung: cao độ đáy hố từng trụ, bậc tại tim móng + (FX, FY), mái 1:FM."""
    lv = {q: pit_of(mp, q)[3] for q in range(1, 5)}
    return _step_fn(lv, mp.get("FX", 0.0), mp.get("FY", 0.0), mp.get("FM", 0.5))


def pit_boxes(mp):
    """Đáy hố riêng từng trụ: [(x0, x1, y0, y1, cao độ đáy)]."""
    out = []
    for q in range(1, 5):
        x, y, w, zb, _ = pit_of(mp, q)
        out.append((x - w, x + w, y - w, y + w, zb))
    return out


def pit_surface(mp, joint, m):
    """Mặt hố đào S(x, y) (đáy + mái 1:m): hố chung = đáy chữ nhật bao các đáy hố riêng (đáy bậc theo floor_fn),
    hố riêng = thấp nhất của các hố từng trụ."""
    bx = pit_boxes(mp)
    if joint:
        x0, x1 = min(b[0] for b in bx), max(b[1] for b in bx)
        y0, y1 = min(b[2] for b in bx), max(b[3] for b in bx)
        F = floor_fn(mp)

        def S(x, y):
            xc, yc = np.clip(x, x0, x1), np.clip(y, y0, y1)
            return F(xc, yc) + np.maximum(np.abs(x - xc), np.abs(y - yc)) / m
        return S

    def S(x, y):
        out = np.full(np.shape(x), np.inf)
        for x0, x1, y0, y1, zb in bx:
            xc, yc = np.clip(x, x0, x1), np.clip(y, y0, y1)
            out = np.minimum(out, zb + np.maximum(np.abs(x - xc), np.abs(y - yc)) / m)
        return out
    return S


def uniform(mp) -> bool:
    """Mặt đất 1 mức và (đào riêng hoặc đáy hố 1 mức): khối lượng đào có công thức chóp cụt."""
    g = {round(ground(t), 6) for t in mp["TYPES"]}
    f = {round(z_pit(t), 6) for t in mp["TYPES"]}
    return len(g) == 1 and (len(f) == 1 or not pit_joint(mp))


def vol_dao_num(mp, h=0.02) -> float:
    """Đào đất theo lưới ô vuông cạnh h: Σ max(0, mặt đất − mặt hố) · h²."""
    joint = pit_joint(mp)
    m = mp["SLOPE"]
    S, G = pit_surface(mp, joint, m), ground_fn(mp)
    bx = pit_boxes(mp)
    zmax = max(ground(t) for t in mp["TYPES"])
    e = m * (zmax - min(b[4] for b in bx)) + h
    xs = np.arange(min(b[0] for b in bx) - e, max(b[1] for b in bx) + e, h) + h / 2
    ys = np.arange(min(b[2] for b in bx) - e, max(b[3] for b in bx) + e, h) + h / 2
    v = 0.0
    for y in ys:                                   # theo từng hàng (đỡ tốn bộ nhớ)
        yy = np.full_like(xs, y)
        v += float(np.maximum(0.0, G(xs, yy) - S(xs, yy)).sum())
    return v * h * h


def vol_dao(mp) -> float:
    if uniform(mp):
        return vol_dao_joint(mp) if pit_joint(mp) else vol_dao_sep(mp)
    return vol_dao_num(mp)


def vol_dap(mp) -> float:
    return vol_dao(mp) - vol_lot(mp) - (vol_mong(mp) - vol_above(mp))


def den_bu(mp) -> float:
    """Cạnh đền bù (m): Bt + max(b2 − b1 + Bm) của 2 loại + 0.5 m mỗi bên."""
    return mp["BT"] + max(tp(t) + t["B"] for t in mp["TYPES"]) + 1.0


def pit_depth_max(mp) -> float:
    return max(ground(t) - z_pit(t) for t in mp["TYPES"])


def bolt_text(mp) -> str:
    """Bu lông cả vị trí móng, gộp theo đường kính: vd '16M36' hoặc '4M42+12M36'."""
    cnt: dict = {}
    for i, t in enumerate(mp["TYPES"]):
        d = model.bolt_dia(type_params(mp, i))
        cnt[d] = cnt.get(d, 0) + 4 * len(t["POS"])
    return "+".join(f"{n}M{d}" for d, n in sorted(cnt.items(), key=lambda x: (-x[1], x[0])))


def type_name(mp) -> str:
    """Tên móng (khung tên): ô C5, trống thì ghép từ tên 2 loại."""
    if mp.get("TENMONG"):
        return mp["TENMONG"]
    return f"MT{mp['BT'] * 10:.1f} " + "/".join(f"{len(t['POS'])}{t['NAME']}" for t in mp["TYPES"])


# ---------------------------------------------------------------------------
# tỷ lệ tờ 1
def draw_bt(mp, den) -> float:
    """Khoảng cách tim trụ THỂ HIỆN trên tờ 1 (như model.draw_bt, lấy trường hợp bất lợi của 2 loại)."""
    k = 1000.0 / den
    ts = mp["TYPES"]
    side = max(t["B"] + 2 * mp["MPIT"] + 2 * model.SLOPE_DRAW * (ground(t) - z_pit(t)) for t in ts)
    tmax = max(tp(t) for t in ts)
    hsec = max(z_top(t) for t in ts) - min(z_pit(t) for t in ts)
    bmax = max(t["B"] for t in ts)
    w = (model.PAPER_W - 14.0) / k - side - tmax            # bên phải mặt cắt có thêm kích thước, cao độ trụ phải
    h = model.PAPER_H / k - hsec - bmax - 2 * model.ML - tmax
    lo = max(bmax + 0.6, bmax + 2 * mp["MPIT"] + 0.2) - min(tp(t) for t in ts)
    return min(mp["BT"], max(lo, min(w, h)))


def auto_scale(mp) -> int:
    for d in model.SCALES:
        if draw_bt(mp, d) >= mp["BT"] - 1e-9:
            return d
    return model.SCALES[-1]


def section_pair(mp):
    """Cặp trụ mặt cắt A-A: 2 trụ khác loại cùng hàng (ưu tiên hàng trên, hàng dưới) hoặc cùng cột (trái, phải).
    Trả về (trụ trái hình, trụ phải hình, 'x' cắt theo hàng / 'y' cắt theo cột)."""
    ta = type_at(mp)
    for a, b, ax in ((1, 2, "x"), (3, 4, "x"), (3, 1, "y"), (4, 2, "y")):
        if ta[a] != ta[b]:
            return a, b, ax
    return 1, 2, "x"
