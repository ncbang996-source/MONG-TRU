"""Bảng thống kê cốt thép (có hình dạng thanh), bảng kích thước từng thanh và bảng tổng kê 01 vị trí móng.
Cách trình bày theo app móng bản không dầm."""
from __future__ import annotations

from . import model
from .cad import Ctx, txtw
from .view import ni, rpl, tie

T_TBL = "BẢNG THỐNG KÊ CỐT THÉP (CHO 01 MÓNG)"
T_TBLH = ["SỐ HIỆU", "HÌNH DẠNG - KÍCH THƯỚC (mm)", "%%C (mm)", "CHIỀU DÀI 1 THANH (mm)", "SỐ LƯỢNG",
          "TỔNG C.DÀI (m)", "KL (kg)"]
CW = [10.0, 46.0, 10.0, 18.0, 16.0, 19.0, 18.0]
TH = 2.0                                  # chiều cao chữ trong bảng = chữ trong bản vẽ
STRAIGHT = (1, 8)
TALL = (5, 6)


def lbl(c: Ctx, x, y, s, rot=0.0):
    if rot:
        c.txr("BANG", x, y, TH, s, rot)
    else:
        c.txc("BANG", x, y, TH, s)


def row_h(pos, base):
    if pos in STRAIGHT:
        return base
    if pos in TALL:
        return base * 1.9
    return base * 1.45


def shape(c: Ctx, r, x, y, w, h):
    """Hình dạng thanh thép trong ô (x, y) rộng w cao h."""
    pos, d, ln = r["pos"], r["dims"], r["len"]
    yc, xm, lay = y + h / 2, x + w / 2, "BANG"
    if pos in STRAIGHT:
        c.ln(lay, x + 4, yc - 0.6, x + w - 4, yc - 0.6)
        lbl(c, xm, yc + 1.2, ni(ln))
    elif pos == 2:
        # thanh uốn theo mặt vát: chân móc d2, đoạn xiên d0 (trung bình), đoạn phẳng d1 (trung bình)
        yt = yc + 1.2
        yb = yt - 2.6
        sl, x0, x1 = 6.0, x + 8.0, x + w - 8.0
        rpl(c, lay, [(x0, yb - 2.2), (x0, yb), (x0 + sl, yt), (x1 - sl, yt), (x1, yb), (x1, yb - 2.2)], False, 0.3)
        lbl(c, xm, yt + 1.2, "Ltb=" + ni(d[1]))
        lbl(c, x0 - 0.5, yt + 1.2, ni(d[0]))
        lbl(c, x0 - 2.6, yb - 1.4, ni(d[2]))
        lbl(c, x1 + 2.6, yb - 1.4, ni(d[3]))
    elif pos == 3:
        # thanh chống chữ U: thân (trung bình) nằm ngang, 2 chân đứng
        hu = min(h - 3.2, 4.0)
        x0, x1 = xm - 8.0, xm + 8.0
        y0 = yc - hu / 2 - 0.6
        rpl(c, lay, [(x0, y0 + hu), (x0, y0), (x1, y0), (x1, y0 + hu)], False, 0.4)
        lbl(c, xm, y0 + 1.3, "Ltb=" + ni(d[2]))
        lbl(c, x0 - 3.0, y0 + hu / 2, ni(d[0]))
        lbl(c, x1 + 3.0, y0 + hu / 2, ni(d[1]))
    elif pos == 4:
        x0, x1 = x + 5.0, x + w - 5.0
        yb = yc - 1.6
        rpl(c, lay, [(x0, yb + 3.2), (x0, yb), (x1, yb)], False, 0.4)
        lbl(c, xm, yb + 1.2, ni(d[1]))
        lbl(c, x0 + 3.0, yb + 3.0, ni(d[0]))
    elif pos == 5:
        s = min(h - 3.5, 9.0)
        x0, y0 = xm - s / 2, yc - s / 2
        rpl(c, lay, [(x0, y0), (x0 + s, y0), (x0 + s, y0 + s), (x0, y0 + s)], True, 0.06 * s)
        c.ln(lay, x0 + s, y0 + 0.14 * s, x0 + 0.87 * s, y0 + 0.27 * s)
        c.ln(lay, x0 + 0.86 * s, y0, x0 + 0.73 * s, y0 + 0.13 * s)
        lbl(c, xm, y0 + s + 0.9, ni(d[1]))
        lbl(c, x0 - 1.9, yc, ni(d[1]), 90.0)
        lbl(c, x0 + s + 3.5, y0 + 0.8, ni(d[0]))
    elif pos == 6:
        s = min(h - 3.5, 9.0) / 2
        x0 = s * (0.5 * d[0] / (0.5 * d[0] + d[1] / 1.41421))
        c.pl(lay, True, [(xm - x0, yc + s), (xm + x0, yc + s), (xm + s, yc + x0), (xm + s, yc - x0),
                         (xm + x0, yc - s), (xm - x0, yc - s), (xm - s, yc - x0), (xm - s, yc + x0)])
        lbl(c, xm, yc + s + 0.9, ni(d[0]))
        lbl(c, xm + s + 3.5, yc + s - 1.0, ni(d[1]))
        lbl(c, xm - s - 3.0, yc - s + 1.0, ni(d[2]))
    elif pos == 7:
        x0, x1 = x + 0.15 * w + 3.0, x + w - 0.15 * w - 3.0
        tie(c, lay, x0, yc - 1.5, 1.0, 0.0, x1 - x0, 0.7, 2.0)
        lbl(c, xm, yc + 0.2, ni(d[1]))
        lbl(c, x0 - 3.0, yc - 1.3, ni(d[0]))
        lbl(c, x1 + 3.0, yc - 1.3, ni(d[2]))


def _head(c: Ctx, tx, ty, cw, hh, heads, th=TH):
    xs = tx
    for i, w in enumerate(cw):
        words = heads[i].split(" ")
        lines, cur = [], ""
        for wd in words:                  # ngắt dòng tiêu đề theo bề rộng cột
            t = (cur + " " + wd).strip()
            if cur and txtw(t, th) > w - 1.5:
                lines.append(cur)
                cur = wd
            else:
                cur = t
        lines.append(cur)
        y0 = ty - hh / 2 + (len(lines) - 1) * 1.35 * th / 2.0
        for j, t in enumerate(lines):
            c.txc("BANG", xs + w / 2, y0 - 2.7 * th / 2.0 * j, th, t)
        xs += w


def steel_table(c: Ctx, g, tx, ty, ybot):
    """Bảng thống kê thép, đỉnh tại ty, co chiều cao dòng để đáy bảng không thấp hơn ybot."""
    rows = g.kl
    hh = 13.0
    tot = sum(row_h(r["pos"], 1.0) for r in rows)
    base = max(4.6, min(7.0, (ty - hh - 6.0 - ybot) / tot))
    hs = [row_h(r["pos"], base) for r in rows]
    wcol = sum(CW)
    with c.table("table", "Bảng thống kê cốt thép"):
        c.txj("BANG", tx + wcol / 2, ty + 2.2, 2.5, T_TBL, 1, underline=True)
        c.ln("BANG", tx, ty, tx + wcol, ty)
        c.ln("BANG", tx, ty - hh, tx + wcol, ty - hh)
        y = ty - hh
        for h in hs:
            y -= h
            c.ln("BANG", tx, y, tx + wcol, y)
        yend = y
        xs = tx
        c.ln("BANG", xs, ty, xs, yend - 6.0)
        for i, w in enumerate(CW):
            xs += w
            c.ln("BANG", xs, ty, xs, yend if i < len(CW) - 2 else yend - 6.0)
        _head(c, tx, ty, CW, hh, T_TBLH)
        y = ty - hh
        ssum = 0.0
        for r, h in zip(rows, hs):
            y -= h
            ym = y + h / 2
            ssum += r["kg"]
            c.txc("BANG", tx + CW[0] / 2, ym, TH, g.sq(r["pos"]))
            shape(c, r, tx + CW[0], y, CW[1], h)
            xs = tx + CW[0] + CW[1]
            vals = [ni(r["dia"]), ni(r["len"]), r["qty"], f"{r['tot']:.2f}", f"{r['kg']:.2f}"]
            for v, w in zip(vals, CW[2:]):
                c.txc("BANG", xs + w / 2, ym, TH, v)
                xs += w
        c.ln("BANG", tx, yend - 6.0, tx + wcol, yend - 6.0)
        c.txj("BANG", tx + 3.0, yend - 4.2, TH, "CỘNG", 0)
        c.txc("BANG", tx + wcol - CW[-1] / 2, yend - 3.0, TH, f"{ssum:.2f}")
        c.txj("BANG", tx + wcol, yend - 9.5, TH, "(Ltb: CHIỀU DÀI TRUNG BÌNH)", 2)
    return yend - 11.0


# ---------------------------------------------------------------------------
BT_CW = [10.0, 20.0, 10.0, 10.0, 10.0, 12.0, 9.0, 14.0]


def _bar_shape(c: Ctx, pos, x0, x1, yc):
    if pos == 2:
        yt, hd, sl, dh = yc + 2.2, 2.2, 3.5, 2.6
        c.pl("BANG", False, [(x0, yt - hd - dh), (x0, yt - hd), (x0 + sl, yt), (x1 - sl, yt), (x1, yt - hd),
                             (x1, yt - hd - dh)])
        c.txc("BANG", 0.5 * (x0 + x1), yt + 1.4, 1.6, "L1")
        c.txc("BANG", x0 + 0.6, yt + 1.4, 1.6, "L2")
        c.txc("BANG", x0 - 2.0, yt - hd - 0.5 * dh, 1.6, "L3")
    else:
        yb = yc - 2.0
        c.pl("BANG", False, [(x0, yb + 4.0), (x0, yb), (x1, yb), (x1, yb + 4.0)])
        c.txc("BANG", 0.5 * (x0 + x1), yb + 1.4, 1.6, "L1")
        c.txc("BANG", x0 - 2.0, yb + 2.0, 1.6, "L2")
        c.txc("BANG", x1 + 2.0, yb + 2.0, 1.6, "L3")


def bar_table(c: Ctx, g, tx, ty, pos, ybot=None):
    """Bảng kích thước từng thanh (thép lớp trên uốn theo mặt vát, thanh chống). Trả về đáy bảng."""
    rows = g.klb.get(pos)
    if not rows or pos not in g.seq:
        return ty
    cw = BT_CW
    wtot = sum(cw)
    n = len(rows)
    hh = 9.0
    rh = 5.0
    if ybot is not None:                     # co chiều cao dòng để bảng không tràn
        rh = max(3.6, min(rh, (ty - hh - ybot) / n))
    with c.table(f"bar{pos}", f"Bảng kích thước thanh số {g.sq(pos)}"):
        c.txj("BANG", tx, ty + 2.2, TH, f"BẢNG KÍCH THƯỚC TỪNG THANH SỐ {g.sq(pos)} (mm)", 0, underline=True)
        c.ln("BANG", tx, ty, tx + wtot, ty)
        c.ln("BANG", tx, ty - hh, tx + wtot, ty - hh)
        xw = tx + cw[0]
        x1 = xw + cw[1]
        for i in range(1, n + 1):
            y = ty - hh - i * rh
            c.ln("BANG", tx, y, xw, y)
            c.ln("BANG", x1, y, tx + wtot, y)
        xs = tx
        c.ln("BANG", xs, ty, xs, ty - hh - n * rh)
        for w in cw:
            xs += w
            c.ln("BANG", xs, ty, xs, ty - hh - n * rh)
        c.ln("BANG", xw, ty - hh - n * rh, x1, ty - hh - n * rh)
        _head(c, tx, ty, cw, hh, ["THANH", "HÌNH DẠNG", "L1", "L2", "L3", "DÀI", "SL", "TỔNG (m)"])
        _bar_shape(c, pos, xw + 3.5, x1 - 3.5, ty - hh - 0.5 * n * rh)
        for ri, r in enumerate(rows):
            ym = ty - hh - (ri + 0.5) * rh
            c.txc("BANG", tx + cw[0] / 2, ym, TH, f"{g.sq(pos)}.{ri + 1}")
            xs = x1
            for i, v in enumerate([ni(r[0]), ni(r[1]), ni(r[2]), ni(r[3]), ni(r[4]), f"{r[5]:.2f}"], start=2):
                c.txc("BANG", xs + cw[i] / 2, ym, TH, v)
                xs += cw[i]
    return ty - hh - n * rh


# ---------------------------------------------------------------------------
def summary_cols(g):
    p = g.p
    k = g.dp()
    cls = [x for x in g.klc if x[2] > 1e-6]
    tot = sum(x[2] for x in cls) * k
    cols = [(p["BTM"], "(m3)", 14.0, f"{model.vol_mong(p):.2f}"),
            (p["BTL"], "(m3)", 13.0, f"{model.vol_lot(p):.2f}")]
    for d, _, w in cls:
        cols.append((f"%%C{int(d + 0.5)}", "(kg)", 14.0, f"{w * k:.2f}"))
    if cls:
        cols.append(("TỔNG K.LƯỢNG", "THÉP (kg)", 19.0, f"{tot:.2f}"))
    cols.append(("BULONG", "NEO", 14.0, model.bolt_text(p)))
    return cols


def summary(c: Ctx, g, xr, y0):
    """Bảng tổng kê, mép phải tại xr, đỉnh tại y0. Thép đã gồm dự phòng."""
    cols = summary_cols(g)
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
        dp = g.g("DP")
        if dp > 1e-6:
            c.txj("BANG", xr, y0 - hh - rh - 3.5, TH, f"(Khối lượng thép đã gồm {dp:g}% dự phòng)", 2)
    return y0 - hh - rh - 5.0
