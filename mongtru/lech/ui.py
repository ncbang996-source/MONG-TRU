"""Giao diện chế độ móng 2 loại (gọi từ app.py): ghép / tách thông số giữa ô nhập và mp.

Ô nhập dùng chung với chế độ 4 trụ giống nhau; các ô của loại (kích thước, thép, bu lông...) hiện số liệu của
loại đang chọn ("Loại móng đang sửa"), thêm ô Vị trí trụ và Cao độ thiết kế."""
from __future__ import annotations

import copy
import re

from . import model as lm

MIX_KEYS = ("POS", "CD")
STEP_KEYS = tuple(lm.STEP_DEF)            # hạ cao độ mặt đất / bậc đáy hố chung (chỉ ở chế độ 2 loại)


def type_labels(mp) -> list:
    return [f"Loại {i + 1}: {len(t['POS'])}{t['NAME']}" for i, t in enumerate(mp["TYPES"])]


def fill_params(mp, ti) -> dict:
    """Thông số hiển thị trên ô nhập: chung + loại ti + vị trí, cao độ."""
    p = lm.type_params(mp, ti)
    t = mp["TYPES"][ti]
    p["POS"] = ", ".join(str(q) for q in t["POS"])
    p["CD"] = float(t["CD"])
    return p


def parse_pos(s) -> list:
    out = []
    for x in re.split(r"[,;\s]+", str(s).strip()):
        if x:
            q = int(float(x))
            if q not in lm.QUAD:
                raise ValueError("Vị trí trụ phải là 1..4.")
            out.append(q)
    return sorted(set(out))


def merge(mp, ti, p, pos_txt, cd_txt) -> dict:
    """mp mới: thông số chung từ p, loại ti từ p + vị trí, cao độ (ValueError nếu ô không phải số)."""
    out = copy.deepcopy(mp)
    for k in lm.COMMON:
        if k in p:
            out[k] = p[k]
    t = out["TYPES"][ti]
    for k in lm.TYPE_KEYS:
        if k in p:
            t[k] = p[k]
    t["POS"] = parse_pos(pos_txt)
    t["CD"] = float(str(cd_txt).replace(",", "."))
    # vị trí loại kia: phần còn lại của 1..4
    o = out["TYPES"][1 - ti]
    o["POS"] = [q for q in (1, 2, 3, 4) if q not in t["POS"]]
    return out


def pit_text(mp) -> str:
    j, jd = lm.pit_joint(mp), lm.pit_joint_draw(mp)
    txt = "Hố đào (tính khối lượng): " + ("đào chung 1 hố, đáy bậc theo độ sâu" if j else "đào riêng từng trụ")
    if jd != j:
        txt += "  (hình vẽ thể hiện: " + ("đào chung" if jd else "đào riêng") + ")"
    return txt


def restore(d):
    """mp lưu ở settings (có thể từ bản cũ thiếu khoá mới) -> mp đủ khoá, hoặc None nếu không dùng được."""
    try:
        base = lm.default_mp()
        out = {k: d.get(k, base[k]) for k in lm.COMMON}
        out["TYPES"] = []
        for i in range(2):
            t = d["TYPES"][i]
            nt = dict(base["TYPES"][i])
            nt.update({k: t[k] for k in nt if k in t})
            out["TYPES"].append(nt)
        return out if valid_saved(out) else None
    except (KeyError, TypeError, IndexError, AttributeError):
        return None


def valid_saved(d) -> bool:
    try:
        return isinstance(d, dict) and len(d["TYPES"]) == 2 and all(k in d for k in lm.COMMON) and \
            all(all(k in t for k in lm.TYPE_KEYS + ("NAME", "POS", "CD")) for t in d["TYPES"])
    except (KeyError, TypeError):
        return False
