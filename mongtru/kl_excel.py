"""Xuất bảng khối lượng ra Excel (theo app móng bản không dầm): bê tông, lót, đất, ván khuôn tính bằng công thức
tham chiếu sheet THONG SO; cốt thép lấy chiều dài và số thanh do chương trình tính theo bố trí trên bản vẽ."""
from __future__ import annotations

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.workbook.defined_name import DefinedName

from . import model
from .geom import KGM, Geo

THIN = Side(style="thin", color="808080")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
HEAD = PatternFill("solid", fgColor="DDEBF7")
INPUT = PatternFill("solid", fgColor="FFF2CC")
B = Font(bold=True)

# (tên, ký hiệu, khoá thông số, hệ số đổi, đơn vị)
# Lưu ý: tên định danh Excel không phân biệt hoa/thường -> đặt tên khác nhau (TS_Bm, TS_b1 ...)
PARAMS = [
    ("Cạnh bản đế (Bm = Lm)", "Bm", "B", 1, "m"),
    ("Chiều sâu chôn móng", "Hm", "H1", 1, "m"),
    ("Cao cổ móng trên mặt đất", "d", "H2", 1, "m"),
    ("Khoảng cách tim trụ", "Bt", "BT", 1, "m"),
    ("Cạnh cổ móng ở đỉnh", "b1", "B1", 1, "m"),
    ("Cạnh cổ móng ở chân", "b2", "B2", 1, "m"),
    ("Cao bản đế tại gờ cổ móng", "hb", "HB", 1, "m"),
    ("Cao bản đế ở mép", "hv", "HV", 1, "m"),
    ("Gờ quanh chân cổ móng", "mpl", None, model.MPL, "m"),
    ("Dày bê tông lót", "tl", None, model.TL, "m"),
    ("Lót tràn ra mỗi bên", "ml", None, model.ML, "m"),
    ("Hệ số mở mái hố đào", "m", "SLOPE", 1, ""),
    ("Mở rộng đáy hố đào (mỗi bên)", "mp", "MPIT", 1, "m"),
    ("Số trụ móng", "n", "NPIER", 1, "trụ"),
    ("Dự phòng thép", "dp", "DP", 1, "%"),
]
NAME = {"Bm": "TS_Bm", "Hm": "TS_Hm", "d": "TS_d", "Bt": "TS_Bt", "b1": "TS_b1", "b2": "TS_b2", "hb": "TS_hb",
        "hv": "TS_hv", "mpl": "TS_mpl", "tl": "TS_tl", "ml": "TS_ml", "m": "TS_m", "mp": "TS_mp", "n": "TS_n",
        "dp": "TS_dp"}


def _cell(ws, r, c, v, fmt=None, bold=False, fill=None, align=None):
    x = ws.cell(row=r, column=c, value=v)
    x.border = BOX
    if fmt:
        x.number_format = fmt
    if bold:
        x.font = B
    if fill:
        x.fill = fill
    x.alignment = align or Alignment(vertical="center", wrap_text=True)
    return x


def export(p: dict, g: Geo, path: str):
    if not getattr(g, "kl", None):
        g.calc_kl()
    wb = Workbook()
    ws = wb.active
    ws.title = "THONG SO"
    for col, w in zip("ABCDE", (6, 36, 10, 12, 8)):
        ws.column_dimensions[col].width = w
    ws["A1"] = f"THÔNG SỐ MÓNG {model.type_name(p)} - CỘT {model.HT_NAMES[int(p['HT'])]} {p['COT']} ({p['GD']})"
    ws["A1"].font = Font(bold=True, size=12)
    ws["A2"] = "Ô nền vàng là số liệu đầu vào - sửa ở đây, sheet KHOI LUONG tự tính lại."
    ws["A2"].font = Font(italic=True, color="808080")
    r = 4
    for i, h in enumerate(["STT", "Thông số", "Ký hiệu", "Giá trị", "Đơn vị"], 1):
        _cell(ws, r, i, h, bold=True, fill=HEAD, align=Alignment(horizontal="center", vertical="center"))
    for k, (nm, sym, key, f, unit) in enumerate(PARAMS, 1):
        r += 1
        v = p[key] * f if key else f
        _cell(ws, r, 1, k, align=Alignment(horizontal="center"))
        _cell(ws, r, 2, nm)
        _cell(ws, r, 3, sym, align=Alignment(horizontal="center"))
        _cell(ws, r, 4, v, "0.000", fill=INPUT)
        _cell(ws, r, 5, unit, align=Alignment(horizontal="center"))
        wb.defined_names[NAME[sym]] = DefinedName(NAME[sym], attr_text=f"'THONG SO'!$D${r}")
    r += 2
    ws.cell(row=r, column=2, value="TRỌNG LƯỢNG THÉP (TCVN 1651-2018)").font = B
    r += 1
    _cell(ws, r, 2, "Đường kính (mm)", bold=True, fill=HEAD)
    _cell(ws, r, 3, "kg/m", bold=True, fill=HEAD)
    r0 = r + 1
    for d, w in sorted(KGM.items()):
        r += 1
        _cell(ws, r, 2, d)
        _cell(ws, r, 3, w, "0.000", fill=INPUT)
    wb.defined_names["TS_KGM"] = DefinedName("TS_KGM", attr_text=f"'THONG SO'!$B${r0}:$C${r}")

    # ------------------------------------------------------------------ KHOI LUONG
    wk = wb.create_sheet("KHOI LUONG")
    for col, w in zip("ABCDEFGH", (6, 44, 10, 70, 12, 9, 12, 12)):
        wk.column_dimensions[col].width = w
    wk["A1"] = f"BẢNG KHỐI LƯỢNG CHO 01 VỊ TRÍ MÓNG {model.type_name(p)} - CỘT {p['COT']}"
    wk["A1"].font = Font(bold=True, size=12)
    r = 3
    for i, h in enumerate(["STT", "Hạng mục", "Ký hiệu", "Công thức / diễn giải", "Khối lượng", "Đơn vị"], 1):
        _cell(wk, r, i, h, bold=True, fill=HEAD, align=Alignment(horizontal="center", vertical="center"))
    rows = {}

    def line(stt, name, sym, formula, desc, unit, bold=False):
        nonlocal r
        r += 1
        _cell(wk, r, 1, stt, align=Alignment(horizontal="center"))
        _cell(wk, r, 2, name, bold=bold)
        _cell(wk, r, 3, sym, align=Alignment(horizontal="center"))
        _cell(wk, r, 4, desc)
        _cell(wk, r, 5, formula, "0.00", bold=bold)
        _cell(wk, r, 6, unit, align=Alignment(horizontal="center"))
        if sym:
            rows[sym] = f"$E${r}"
        return f"$E${r}"

    def sec(t):
        nonlocal r
        r += 1
        c = _cell(wk, r, 1, t, bold=True, fill=HEAD)
        wk.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
        c.alignment = Alignment(vertical="center")

    sec("A. KÍCH THƯỚC TRUNG GIAN")
    a = line("", "Cạnh gờ quanh chân cổ móng", "a", "=TS_b2+2*TS_mpl", "b2 + 2·mpl", "m")
    hc = line("", "Chiều cao cổ móng (từ mặt gờ)", "hc", "=TS_Hm+TS_d-TS_hb", "Hm + d − hb", "m")
    hd = line("", "Chiều sâu hố đào", "Hd", "=TS_Hm+TS_tl", "Hm + dày lót", "m")
    kh = line("", "Khoảng hở giữa miệng 2 hố đào riêng", "kh", f"=TS_Bt-2*(0.5*TS_Bm+TS_mp+{hd}*TS_m)",
              "Bt − 2·(Bm/2 + mp + Hd·m); <= 0 thì đào chung 1 hố cho 4 trụ", "m")
    a1 = line("", "Cạnh đáy hố đào", "a1", f"=IF({kh}>0,TS_Bm+2*TS_mp,TS_Bt+TS_Bm+2*TS_mp)",
              "Hố riêng: Bm + 2·mp; hố chung: Bt + Bm + 2·mp", "m")
    a2 = line("", "Cạnh miệng hố đào", "a2", f"={a1}+2*TS_m*{hd}", "a1 + 2·m·Hd", "m")
    nh = line("", "Số hố đào", "nh", f"=IF({kh}>0,TS_n,TS_n/4)", "Hố riêng: n; hố chung: n/4", "hố")
    bt_ = line("", "Cạnh cổ móng tại mặt đất", "bd", "=TS_b2+(TS_b1-TS_b2)*(TS_Hm-TS_hb)/(TS_Hm+TS_d-TS_hb)",
               "b2 + (b1 − b2)·(Hm − hb)/hc", "m")

    sec("B. BÊ TÔNG")
    vb = line(1, f"Bê tông móng {p['BTM']}", "Vbt",
              f"=TS_n*(TS_Bm^2*TS_hv+(TS_Bm^2+{a}^2+TS_Bm*{a})*(TS_hb-TS_hv)/3+(TS_b1^2+TS_b2^2+TS_b1*TS_b2)*{hc}/3)",
              "n·[Bm²·hv + (Bm² + a² + Bm·a)·(hb − hv)/3 + (b1² + b2² + b1·b2)·hc/3]", "m3", True)
    vl = line(2, f"Bê tông lót {p['BTL']}", "Vlot", "=TS_n*(TS_Bm+2*TS_ml)^2*TS_tl", "n·(Bm + 2·ml)²·tl", "m3", True)

    sec("C. ĐẤT, VÁN KHUÔN")
    vd = line(3, "Đào đất hố móng", "Vdao", f"={nh}*{hd}/3*({a1}^2+{a2}^2+{a1}*{a2})",
              "nh · Hd/3·(a1² + a2² + a1·a2)", "m3", True)
    va = line("", "Thể tích cổ móng trên mặt đất", "Vtr", f"=TS_n*TS_d/3*({bt_}^2+TS_b1^2+{bt_}*TS_b1)",
              "n·d/3·(bd² + b1² + bd·b1)", "m3")
    vdp = line(4, "Đắp đất hoàn trả hố móng", "Vdap", f"={vd}-{vl}-({vb}-{va})", "Vdao − Vlot − (Vbt − Vtr)", "m3", True)
    line(5, "Đất thừa", "Vthua", f"={vd}-{vdp}", "Vdao − Vdap", "m3", True)
    line(6, "Ván khuôn móng", "VK", f"=TS_n*(4*TS_b1*{hc}+4*TS_Bm*TS_hv)",
         "n·(4·b1·hc + 4·Bm·hv) (mặt vát không ghép ván khuôn)", "m2", True)

    sec("D. CỐT THÉP (số thanh và chiều dài do chương trình tính theo bố trí trên bản vẽ)")
    r += 1
    for i, h in enumerate(["Vị trí", "Hình dạng / ghi chú", "Ø (mm)", "Chiều dài 1 thanh (mm)", "Số lượng",
                           "kg/m", "Tổng dài (m)", "KL (kg)"], 1):
        _cell(wk, r, i, h, bold=True, fill=HEAD, align=Alignment(horizontal="center", vertical="center", wrap_text=True))
    rs0 = r + 1
    for row in g.kl:
        r += 1
        q = str(row["qty"]).replace("x", "*")
        nm = row["name"] + (" - chiều dài trung bình" if row["pos"] in (2, 3) else "")
        _cell(wk, r, 1, g.sq(row["pos"]), align=Alignment(horizontal="center"))
        _cell(wk, r, 2, nm)
        _cell(wk, r, 3, int(row["dia"] + 0.5), fill=INPUT)
        _cell(wk, r, 4, round(row["len"], 1), "0", fill=INPUT)
        _cell(wk, r, 5, f"={q}", "0")
        _cell(wk, r, 6, f"=IFERROR(VLOOKUP(C{r},TS_KGM,2,FALSE),C{r}^2/162)", "0.000")
        _cell(wk, r, 7, f"=D{r}/1000*E{r}", "0.00")
        _cell(wk, r, 8, f"=G{r}*F{r}", "0.00")
    rs1 = r
    r += 1
    _cell(wk, r, 2, "TỔNG CỘNG THÉP", bold=True)
    _cell(wk, r, 8, f"=SUM(H{rs0}:H{rs1})", "0.00", bold=True)
    r += 1
    _cell(wk, r, 2, "TỔNG CỘNG THÉP (có dự phòng)", bold=True)
    _cell(wk, r, 4, "Tổng cộng × (1 + dp/100)")
    _cell(wk, r, 8, f"=H{r - 1}*(1+TS_dp/100)", "0.00", bold=True)
    rtot = r
    r += 2
    _cell(wk, r, 2, "Phân loại theo đường kính (có dự phòng)", bold=True, fill=HEAD)
    _cell(wk, r, 3, "Ø (mm)", bold=True, fill=HEAD)
    _cell(wk, r, 7, "Tổng dài (m)", bold=True, fill=HEAD)
    _cell(wk, r, 8, "KL (kg)", bold=True, fill=HEAD)
    rdia = {}
    for d, _, _ in g.klc:
        r += 1
        rdia[int(d + 0.5)] = r
        _cell(wk, r, 2, f"Thép Ø{int(d + 0.5)}")
        _cell(wk, r, 3, int(d + 0.5))
        _cell(wk, r, 7, f"=SUMIF($C${rs0}:$C${rs1},C{r},$G${rs0}:$G${rs1})*(1+TS_dp/100)", "0.00")
        _cell(wk, r, 8, f"=SUMIF($C${rs0}:$C${rs1},C{r},$H${rs0}:$H${rs1})*(1+TS_dp/100)", "0.00")
    r += 2
    _cell(wk, r, 2, "Bu lông neo", bold=True)
    _cell(wk, r, 4, f"{model.bolt_text(p)}  ({p['BLN']})")
    _bars(wk, g, r + 2)
    wk.freeze_panes = "A4"
    _summary(wb, p, rows, rdia, rtot)
    wb.active = 0
    wb.save(path)


def _bars(wk, g, r):
    """Bảng kích thước từng thanh (thép lớp trên uốn theo mặt vát, thanh chống)."""
    for pos, hd in ((2, ["Thanh", "Đoạn phẳng L1", "Đoạn xiên L2 (mỗi bên)", "Chân móc L3 (mỗi bên)"]),
                    (3, ["Thanh", "Thân L1", "Chân L2", "Chân L3"])):
        rows = g.klb.get(pos)
        if not rows or pos not in g.seq:
            continue
        c = _cell(wk, r, 1, f"KÍCH THƯỚC TỪNG THANH SỐ {g.sq(pos)} (mm)", bold=True, fill=HEAD)
        wk.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)
        c.alignment = Alignment(vertical="center")
        r += 1
        for i, h in enumerate(hd + ["Dài (mm)", "Số lượng", "Tổng dài (m)"], 1):
            _cell(wk, r, i + (1 if i > 1 else 0), h, bold=True, fill=HEAD,
                  align=Alignment(horizontal="center", vertical="center", wrap_text=True))
        for i, x in enumerate(rows, 1):
            r += 1
            _cell(wk, r, 1, f"{g.sq(pos)}.{i}", align=Alignment(horizontal="center"))
            for j, v in enumerate(x[:5]):
                _cell(wk, r, 3 + j, round(v), "0")
            _cell(wk, r, 8, f"=F{r}/1000*G{r}", "0.00")
        r += 2


def _summary(wb, p, rows, rdia, rtot):
    """Sheet TONG KE: bảng tổng kê khối lượng 1 vị trí móng, mỗi số liệu 1 ô."""
    ws = wb.create_sheet("TONG KE", 0)
    K = "'KHOI LUONG'!"
    cols = [(f"{p['BTM']} (m³)", f"={K}{rows['Vbt']}", "0.00"),
            (f"{p['BTL']} (m³)", f"={K}{rows['Vlot']}", "0.00")]
    for d in sorted(rdia):
        cols.append((f"Ø{d} (kg)", f"={K}$H${rdia[d]}", "0.00"))
    cols += [("TỔNG K.LƯỢNG THÉP (kg)", f"={K}$H${rtot}", "0.00"),
             ("BULONG NEO", model.bolt_text(p), None),
             ("Đào đất (m³)", f"={K}{rows['Vdao']}", "0.00"),
             ("Đắp đất (m³)", f"={K}{rows['Vdap']}", "0.00"),
             ("Ván khuôn (m²)", f"={K}{rows['VK']}", "0.00"),
             ("Rộng đền bù (m)", "=TS_Bt+TS_Bm+2*0.5", "0.00"),
             ("Dài đền bù (m)", "=TS_Bt+TS_Bm+2*0.5", "0.00"),
             ("Diện đền bù (m²)", None, "0.00"),
             ("Chiều sâu hố đào (m)", f"={K}{rows['Hd']}", "0.00")]
    n = len(cols)
    ws.page_setup.orientation = "landscape"
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.row_dimensions[1].height = 34
    ws.row_dimensions[2].height = 64
    ws.row_dimensions[3].height = 24
    c = ws.cell(row=1, column=1, value="BẢNG TỔNG KÊ KHỐI LƯỢNG CHO 01 VỊ TRÍ MÓNG")
    c.font = Font(size=14)
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n)
    for j in range(1, n + 1):
        ws.cell(row=1, column=j).border = BOX
    from openpyxl.utils import get_column_letter as L
    for j, (h, f, fmt) in enumerate(cols, 1):
        ws.column_dimensions[L(j)].width = 11 if len(h) < 14 else 12.5
        _cell(ws, 2, j, h, align=Alignment(horizontal="center", vertical="center", wrap_text=True))
        if h.startswith("Diện đền bù"):
            f = f"={L(j - 2)}3*{L(j - 1)}3"
        _cell(ws, 3, j, f, fmt, align=Alignment(horizontal="center", vertical="center"))
    ws.cell(row=5, column=1, value=f"Khối lượng thép đã gồm {p.get('DP', 0):g}% dự phòng.").font = \
        Font(italic=True, color="808080")
