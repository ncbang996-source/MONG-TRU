"""VẼ MÓNG TRỤ - app vẽ nhanh bản vẽ móng trụ rời 4 trụ (móng cột đường dây) từ file Excel, xuất PDF / DXF.

Chạy:  python app.py
"""
from __future__ import annotations

import copy
import json
import os
import sys
import threading
import tkinter as tk
import traceback
from tkinter import filedialog, messagebox, ttk

from mongtru import _meta, cad, export, frame, kl_excel, model
from mongtru.ui3d import View3D

APP_NAME = "VE_MONGTRU"
APP_VER = "1.0.0"
APP_DESC = "Móng trụ rời (4 trụ) cho móng cột đường dây cao thế bằng thép hình."


def settings_path():
    base = os.environ.get("APPDATA") or os.path.expanduser("~/.config")
    d = os.path.join(base, "VE_MONGTRU")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "settings.json")


def load_settings():
    try:
        with open(settings_path(), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_settings(s):
    try:
        with open(settings_path(), "w", encoding="utf-8") as f:
            json.dump(s, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def layout_path(xls):
    return os.path.splitext(xls)[0] + ".layout.json" if xls else None


def load_layout(xls):
    """Vị trí đã dịch chuyển, lưu cạnh file Excel."""
    pth = layout_path(xls)
    try:
        with open(pth, encoding="utf-8") as f:
            d = json.load(f)
        return {k: [float(v[0]), float(v[1])] for k, v in d.get("offsets", {}).items()}
    except Exception:
        return {}


def save_layout(xls, offsets):
    pth = layout_path(xls)
    if not pth:
        return
    try:
        if offsets:
            with open(pth, "w", encoding="utf-8") as f:
                json.dump({"offsets": offsets}, f, ensure_ascii=False, indent=1)
        elif os.path.isfile(pth):
            os.remove(pth)
    except OSError:
        pass


def default_frame():
    p = os.path.join(cad.resource_dir(), "frames", "KT-A3.dxf")
    return p if os.path.isfile(p) else ""


# (khoá, nhãn, kiểu) - kiểu: f = số, s = chữ
DIM_FIELDS = [
    ("B", "Bm = Lm - cạnh bản đế (m)"), ("H1", "Hm - chiều sâu chôn móng (m)"),
    ("H2", "d - cao cổ móng trên mặt đất (m)"), ("BT", "Bt - khoảng cách tim trụ (m)"),
    ("B1", "b1 - cạnh cổ móng ở đỉnh (m)"), ("B2", "b2 - cạnh cổ móng ở chân (m)"),
    ("HB", "hb - cao bản đế tại gờ cổ móng (m)"), ("HV", "hv - cao bản đế ở mép (m)"),
    ("SLOPE", "Hệ số mở mái (tính KL)"), ("MPIT", "Mở rộng đáy hố đào (m)"),
    ("NPIER", "Số trụ móng"),
]
# (nhãn, khoá Ø, khoá bước)
REBAR_FIELDS = [
    ("Thép bản đế - lớp dưới", "RB_BOT_D", "RB_BOT_S"), ("Thép bản đế - lớp trên", "RB_TOP_D", "RB_TOP_S"),
    ("Thanh chống", "RB_CH_D", "RB_CH_S"), ("Đai cổ móng", "RT_D", "RT_S"),
    ("Đai phụ cổ móng", "RP_D", "RP_S"), ("Lưới đầu trụ", "RL_D", "RL_S"),
]
STAGES = ["TKCS", "TKBVTC", "TKKT"]

# bảng màu giao diện
C = {
    "navy": "#1F3A5F", "blue": "#2E75B6", "green": "#2E8B57", "orange": "#F28C28", "red": "#C62828",
    "bg": "#EEF3F9", "bar": "#E2EBF6", "card": "#FFFFFF", "line": "#C3D2E4", "text": "#1E2A38",
    "muted": "#5B6B80", "stage": "#3C4B5C",
    "sections": ["#2E75B6", "#138D90", "#D9822B", "#7B5EA7", "#2E8B57"],
}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} {APP_VER}")
        try:
            ico = os.path.join(cad.resource_dir(), "icon.ico")
            if sys.platform == "win32":
                self.iconbitmap(ico)
            else:
                from PIL import Image, ImageTk
                self._ico = ImageTk.PhotoImage(Image.open(ico))
                self.iconphoto(True, self._ico)
        except Exception:
            pass
        self.geometry("1400x860")
        self.minsize(1100, 700)
        self.st = load_settings()
        self.p = model.default_params()
        self.p.update({k: v for k, v in self.st.get("params", {}).items() if k in self.p})
        self.xls = self.st.get("xls", "")
        self.frame_path = self.st.get("frame", default_frame())
        if self.frame_path and not os.path.isfile(self.frame_path):
            self.frame_path = default_frame()
        self.fields = copy.deepcopy(self.st.get("fields") or frame.DEFAULT_FIELDS)
        self.vars: dict[str, tk.Variable] = {}
        self.pdf = None
        self.pages = []          # ảnh PIL từng trang
        self.page_i = 0
        self.zoom = None         # None = vừa khung
        self.busy = False
        self.dirty = True
        self.offsets: dict = load_layout(self.xls)   # dịch chuyển đã lưu {id: [dx, dy]} (mm giấy)
        self.pending: dict = {}      # dịch chuyển chưa dựng lại
        self._drag = None
        self._geom = None
        self._undo: list = []        # Ctrl+Z / Ctrl+Y khi sắp xếp
        self._redo: list = []
        self._job = None
        self._build_ui()
        self._fill()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        for k in ("<Control-z>", "<Control-Z>"):
            self.bind_all(k, lambda e: self._undo_redo(True))
        for k in ("<Control-y>", "<Control-Y>"):
            self.bind_all(k, lambda e: self._undo_redo(False))
        if self.xls and os.path.isfile(self.xls) and not self.st.get("params"):
            self.after(200, lambda: self.read_excel(self.xls))
        else:
            self.after(300, self.preview)

    # ------------------------------------------------------------------ UI
    def _theme(self):
        st = ttk.Style(self)
        try:
            st.theme_use("clam")               # theme cho phép đổi màu nút, ô nhập
        except tk.TclError:
            pass
        f = ("Segoe UI", 10) if sys.platform == "win32" else ("DejaVu Sans", 9)
        fb = (f[0], f[1], "bold")
        self.configure(background=C["bg"])
        st.configure(".", font=f, background=C["card"], foreground=C["text"])
        st.configure("TFrame", background=C["card"])
        st.configure("TLabel", background=C["card"], foreground=C["text"])
        st.configure("Bg.TFrame", background=C["bg"])
        st.configure("Bar.TFrame", background=C["bar"])
        st.configure("Bar.TLabel", background=C["bar"], foreground=C["muted"], font=(f[0], f[1] - 1))
        st.configure("Info.TLabel", background=C["bg"], foreground=C["muted"])
        st.configure("Bar.TCheckbutton", background=C["bar"], foreground=C["navy"])
        st.map("Bar.TCheckbutton", background=[("active", C["bar"])])
        st.configure("Info2.TLabel", background=C["card"], foreground=C["blue"], font=fb)
        st.configure("Err.TLabel", background=C["card"], foreground=C["red"])
        st.configure("Sub.TLabel", background=C["card"], foreground=C["muted"])
        for nm, bg, fg, hov in (("Tool", "#FFFFFF", C["navy"], "#DCE9F7"),
                                ("Primary", C["blue"], "#FFFFFF", "#245E93"),
                                ("Export", C["green"], "#FFFFFF", "#22704A"),
                                ("Small", C["bar"], C["navy"], "#C9DAEE")):
            st.configure(f"{nm}.TButton", background=bg, foreground=fg, bordercolor=C["line"],
                         lightcolor=bg, darkcolor=bg, focuscolor=bg, padding=(10, 5) if nm != "Small" else (6, 2),
                         font=fb if nm in ("Primary", "Export") else f, relief="flat")
            st.map(f"{nm}.TButton", background=[("pressed", hov), ("active", hov)],
                   lightcolor=[("active", hov)], darkcolor=[("active", hov)])
        st.configure("TEntry", fieldbackground="#FFFFFF", bordercolor=C["line"], lightcolor=C["line"], padding=3)
        st.map("TEntry", bordercolor=[("focus", C["blue"])], lightcolor=[("focus", C["blue"])])
        st.configure("TCombobox", fieldbackground="#FFFFFF", bordercolor=C["line"], lightcolor=C["line"],
                     arrowcolor=C["blue"], padding=2)
        st.map("TCombobox", bordercolor=[("focus", C["blue"])], fieldbackground=[("readonly", "#FFFFFF")])
        st.configure("Vertical.TScrollbar", background=C["bar"], troughcolor=C["bg"], bordercolor=C["bg"],
                     arrowcolor=C["blue"])
        st.configure("TPanedwindow", background=C["bg"])
        st.configure("TNotebook", background=C["card"], bordercolor=C["line"], tabmargins=(6, 6, 6, 0))
        st.configure("TNotebook.Tab", background=C["bar"], foreground=C["muted"], padding=(10, 4), font=fb,
                     bordercolor=C["line"])
        st.map("TNotebook.Tab", background=[("selected", "#FFFFFF")], foreground=[("selected", C["blue"])])
        st.configure("TRadiobutton", background=C["card"])
        st.configure("TCheckbutton", background=C["card"])
        return f, fb

    def _build_ui(self):
        f, fb = self._theme()
        self._f = f
        # dải tiêu đề
        hdr = tk.Frame(self, background=C["navy"], height=54)
        hdr.pack(side="top", fill="x")
        try:
            from PIL import Image, ImageTk
            im = Image.open(os.path.join(cad.resource_dir(), "icon.png")).convert("RGBA").resize((40, 40))
            self._logo = ImageTk.PhotoImage(im)
            tk.Label(hdr, image=self._logo, background=C["navy"]).pack(side="left", padx=(12, 8), pady=6)
        except Exception:
            pass
        tt = tk.Frame(hdr, background=C["navy"])
        tt.pack(side="left", pady=4)
        tk.Label(tt, text=APP_NAME, background=C["navy"], foreground="#FFFFFF",
                 font=(f[0], f[1] + 5, "bold")).pack(anchor="w")
        tk.Label(tt, text=f"{APP_DESC}  •  Excel → PDF / AutoCAD DXF / Excel khối lượng",
                 background=C["navy"], foreground="#A9C7EA", font=(f[0], f[1] - 1)).pack(anchor="w")
        tk.Label(hdr, text=f"phiên bản {APP_VER}", background=C["navy"], foreground="#7FA3CC",
                 font=(f[0], f[1] - 1)).pack(side="right", padx=14)
        tk.Frame(self, background=C["orange"], height=3).pack(side="top", fill="x")

        # thanh công cụ chia nhóm
        bar = ttk.Frame(self, style="Bar.TFrame", padding=(8, 4, 8, 6))
        bar.pack(side="top", fill="x")

        def group(title):
            g = ttk.Frame(bar, style="Bar.TFrame")
            g.pack(side="left", padx=(0, 14))
            ttk.Label(g, text=title.upper(), style="Bar.TLabel").pack(anchor="w")
            row = ttk.Frame(g, style="Bar.TFrame")
            row.pack(anchor="w")
            return row

        def btn(parent, t, cmd, sty="Tool"):
            ttk.Button(parent, text=t, command=cmd, style=f"{sty}.TButton").pack(side="left", padx=(0, 4))

        g1 = group("Dữ liệu")
        btn(g1, "Mở Excel...", self.pick_excel)
        btn(g1, "⟳ Đọc lại", lambda: self.read_excel(self.xls))
        g2 = group("Khung tên")
        btn(g2, "Nạp khung tên...", self.pick_frame)
        btn(g2, "⚙ Cấu hình...", self.edit_fields)
        g3 = group("Xem")
        btn(g3, "▶  Xem trước", self.preview, "Primary")
        self.v_auto = tk.BooleanVar(value=self.st.get("auto", True))
        ttk.Checkbutton(g3, text="Tự cập nhật", variable=self.v_auto, style="Bar.TCheckbutton").pack(side="left", padx=6)
        self.v_arr = tk.BooleanVar(value=False)
        ttk.Checkbutton(g3, text="Sắp xếp (kéo thả, Ctrl+Z / Ctrl+Y)", variable=self.v_arr, style="Bar.TCheckbutton",
                        command=self._redraw).pack(side="left", padx=(0, 6))
        g4 = group("Xuất")
        btn(g4, "PDF", self.export_pdf, "Export")
        btn(g4, "AutoCAD DXF", self.export_dxf, "Export")
        btn(g4, "Excel khối lượng", self.export_xlsx, "Export")

        info = ttk.Frame(self, style="Bg.TFrame", padding=(10, 3))
        info.pack(side="top", fill="x")
        self.l_xls = ttk.Label(info, text="", style="Info.TLabel")
        self.l_xls.pack(side="left")
        self.l_frame = ttk.Label(info, text="", style="Info.TLabel")
        self.l_frame.pack(side="right")

        pw = ttk.PanedWindow(self, orient="horizontal")
        pw.pack(fill="both", expand=True, padx=8, pady=(0, 6))
        left = tk.Frame(pw, background=C["card"], highlightbackground=C["line"], highlightthickness=1)
        right = tk.Frame(pw, background=C["card"], highlightbackground=C["line"], highlightthickness=1)
        pw.add(left, weight=0)
        pw.add(right, weight=1)

        # khung trái cuộn được
        cv = tk.Canvas(left, width=590, highlightthickness=0, background=C["card"])
        sb = ttk.Scrollbar(left, orient="vertical", command=cv.yview)
        body = ttk.Frame(cv, padding=(6, 4, 10, 10))
        body.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.create_window((0, 0), window=body, anchor="nw")
        cv.configure(yscrollcommand=sb.set)
        cv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self._scroll_left = cv
        # con lăn: 1 bộ xử lý chung, chọn khung theo vị trí con trỏ (không phụ thuộc Enter/Leave)
        self.bind_all("<MouseWheel>", self._wheel_any)
        self.bind_all("<Button-4>", lambda e: self._wheel_any(e, 120))
        self.bind_all("<Button-5>", lambda e: self._wheel_any(e, -120))
        # Combobox không tự đổi giá trị khi lăn qua -> cuộn khung thông số
        for ev, dl in (("<MouseWheel>", None), ("<Button-4>", 120), ("<Button-5>", -120)):
            self.bind_class("TCombobox", ev, lambda e, dl=dl: (self._wheel_any(e, dl), "break")[1])
        self._form(body)

        # xem trước: tab bản in + tab mô hình 3D
        self.nb = ttk.Notebook(right)
        self.nb.pack(fill="both", expand=True)
        tab1 = ttk.Frame(self.nb)
        self.v3d = View3D(self.nb, APP_NAME, C)
        self.nb.add(tab1, text="  Bản in (PDF)  ")
        self.nb.add(self.v3d, text="  Mô hình 3D  ")
        self.nb.bind("<<NotebookTabChanged>>", lambda e: self.v3d.refresh() if self.nb.index("current") == 1 else None)
        top = ttk.Frame(tab1, padding=(8, 6))
        top.pack(side="top", fill="x")
        ttk.Label(top, text="XEM TRƯỚC BẢN IN", style="Info2.TLabel").pack(side="left", padx=(0, 12))
        self.v_page = tk.StringVar(value="Tờ 1")
        self.cb_page = ttk.Combobox(top, textvariable=self.v_page, state="readonly", width=8, values=["Tờ 1"])
        self.cb_page.pack(side="left")
        self.cb_page.bind("<<ComboboxSelected>>", lambda e: self._show_page(self.cb_page.current()))
        ttk.Button(top, text="Vừa khung", command=self.zoom_fit, style="Small.TButton").pack(side="left", padx=(6, 2))
        ttk.Button(top, text="+", width=3, command=lambda: self.zoom_by(1.25), style="Small.TButton").pack(side="left")
        ttk.Button(top, text="−", width=3, command=lambda: self.zoom_by(0.8), style="Small.TButton").pack(side="left", padx=(2, 0))
        self.l_state = ttk.Label(top, text="", style="Sub.TLabel")
        self.l_state.pack(side="left", padx=10)
        self.pv = tk.Canvas(tab1, background=C["stage"], highlightthickness=0)
        self.pv.pack(fill="both", expand=True)
        self.pv.bind("<Configure>", lambda e: self._redraw())
        self.pv.bind("<ButtonPress-1>", self._press)
        self.pv.bind("<B1-Motion>", self._motion)
        self.pv.bind("<ButtonRelease-1>", self._release)
        self.pv.bind("<ButtonPress-2>", lambda e: self.pv.scan_mark(e.x, e.y))
        self.pv.bind("<B2-Motion>", lambda e: (self.pv.scan_dragto(e.x, e.y, gain=1),
                                              None if self._view_covered() else self._paint(fast=True)))
        self.pv.bind("<ButtonRelease-2>", lambda e: self._paint_later(60))
        self.bind("<Escape>", lambda e: (setattr(self, "_sel", []), self._overlay()))
        self.pv.bind("<ButtonPress-3>", self._context)
        self.pv.bind("<Motion>", self._hover)


        st = tk.Frame(self, background=C["navy"])
        st.pack(side="bottom", fill="x", before=pw)
        self._cr = tk.Label(st, text=_meta.credit(), background=C["navy"], foreground="#F2B36B",
                            font=(f[0], f[1] - 1, "bold"), padx=10, pady=3)
        self._cr.pack(side="left")
        tk.Frame(st, background="#3E5C82", width=1).pack(side="left", fill="y", pady=3)
        self.l_msg = tk.Label(st, text=APP_DESC, background=C["navy"], foreground="#E3ECF7", anchor="w",
                              font=(f[0], f[1] - 1), padx=10, pady=3)
        self.l_msg.pack(side="left", fill="x")

    def _inside(self, w, root):
        while w is not None:
            if w == root:
                return True
            w = getattr(w, "master", None)
        return False

    def _wheel_any(self, e, delta=None):
        delta = e.delta if delta is None else delta
        if not delta:
            return
        try:
            w = self.winfo_containing(e.x_root, e.y_root)
        except (KeyError, tk.TclError):
            return
        if w is None:
            return
        if self._inside(w, self.pv):
            self.zoom_by(1.15 if delta > 0 else 1 / 1.15, e)
        elif self._inside(w, self.v3d.cv):
            self.v3d.wheel(e, delta)
        elif self._inside(w, self._scroll_left.master):
            step = -1 if delta > 0 else 1
            n = max(1, abs(int(delta / 120)))
            self._scroll_left.yview_scroll(step * n, "units")

    def _var(self, key, kind="s"):
        v = tk.StringVar()
        v.trace_add("write", lambda *a: self._changed())
        self.vars[key] = v
        return v

    def _form(self, body):
        r = 0

        colors = iter(C["sections"])

        def head(t):
            nonlocal r
            col = next(colors)
            h = tk.Frame(body, background=col)
            h.grid(row=r, column=0, columnspan=4, sticky="we", pady=(12, 4))
            tk.Label(h, text=t.upper(), background=col, foreground="#FFFFFF",
                     font=(self._f[0], self._f[1], "bold"), padx=8, pady=3).pack(side="left")
            r += 1

        def row(lbl, key, w=12, values=None):
            nonlocal r
            ttk.Label(body, text=lbl).grid(row=r, column=0, sticky="w", padx=(10, 4), pady=1)
            if values:
                e = ttk.Combobox(body, textvariable=self._var(key), values=values, width=w - 2)
            else:
                e = ttk.Entry(body, textvariable=self._var(key), width=w)
            e.grid(row=r, column=1, columnspan=3, sticky="w", pady=1)
            r += 1
            return e

        head("1. Thông tin chung")
        row("Hình thức cột", "HT", 16, values=["Đỡ", "Néo", "Néo dừng"])
        row("Loại cột", "COT", 16)
        row("Tên móng (trống = tự đặt)", "TENMONG", 20)
        row("Giai đoạn thiết kế", "GD", 12, values=STAGES)
        row("Mã bản vẽ ghi chú chung", "CODE", 26)
        row("Mã số bản vẽ (khung tên)", "MABV", 26)
        row("Bê tông móng", "BTM", 8)
        row("Bê tông lót", "BTL", 8)
        row("Bu lông neo", "BLN", 16)
        head("2. Kích thước")
        for k, lbl in DIM_FIELDS:
            row(lbl, k, 8)
        head("3. Cốt thép (mm)")
        ttk.Label(body, text="Ø").grid(row=r, column=1, sticky="w")
        ttk.Label(body, text="@ / số thanh").grid(row=r, column=2, sticky="w")
        r += 1
        for lbl, kd, ks in REBAR_FIELDS:
            ttk.Label(body, text=lbl).grid(row=r, column=0, sticky="w", padx=(10, 4), pady=1)
            vd = self.vars[kd] if kd in self.vars else self._var(kd)
            ttk.Entry(body, textvariable=vd, width=5).grid(row=r, column=1, sticky="w")
            ttk.Entry(body, textvariable=self._var(ks), width=6).grid(row=r, column=2, sticky="w")
            r += 1
        ttk.Label(body, text="Thép chủ cổ móng: số thanh / Ø").grid(row=r, column=0, sticky="w", padx=(10, 4), pady=1)
        ttk.Entry(body, textvariable=self._var("RC_N"), width=5).grid(row=r, column=1, sticky="w")
        ttk.Entry(body, textvariable=self._var("RC_D"), width=6).grid(row=r, column=2, sticky="w")
        r += 1
        row("Số lớp lưới đầu trụ", "RL_N", 5)
        row("Lớp BT bảo vệ đáy móng (mm)", "COVER_B", 6)
        row("Lớp BT bảo vệ còn lại (mm)", "COVER", 6)
        row("Dự phòng thép (%)", "DP", 6)
        head("4. Bản vẽ")
        ttk.Label(body, text="Tỷ lệ 1/").grid(row=r, column=0, sticky="w", padx=(10, 4))
        ttk.Combobox(body, textvariable=self._var("SCALE"), values=[str(s) for s in model.SCALES], width=6,
                     state="readonly").grid(row=r, column=1, sticky="w")
        ttk.Button(body, text="Tự chọn", command=self.auto_scale, style="Small.TButton").grid(row=r, column=2, sticky="w")
        r += 1
        self.l_info = ttk.Label(body, text="", style="Info2.TLabel", wraplength=520, justify="left")
        self.l_info.grid(row=r, column=0, columnspan=4, sticky="w", padx=6, pady=(10, 2))
        r += 1
        self.l_err = ttk.Label(body, text="", style="Err.TLabel", wraplength=520, justify="left")
        self.l_err.grid(row=r, column=0, columnspan=4, sticky="w", padx=6)

    # ------------------------------------------------------------ dữ liệu
    def _fill(self):
        self._filling = True
        p = self.p
        for k, v in self.vars.items():
            if k == "HT":
                v.set(["Đỡ", "Néo", "Néo dừng"][int(p["HT"])])
            elif k in ("COVER", "COVER_B"):
                v.set(f"{p[k] * 1000:g}")
            elif k in ("SCALE",):
                v.set(str(int(p[k])))
            elif isinstance(p.get(k), float):
                v.set(f"{p[k]:g}")
            else:
                v.set(str(p.get(k, "")))
        self._filling = False
        self.l_xls.config(text=f"Excel: {self.xls or '(chưa chọn)'}")
        self.l_frame.config(text=f"Khung tên: {os.path.basename(self.frame_path) if self.frame_path else '(khung A3 đơn giản)'}")
        self._update_info()

    def _collect(self):
        p = dict(self.p)
        for k, v in self.vars.items():
            s = v.get().strip()
            if k == "HT":
                p["HT"] = {"đỡ": 0, "néo": 1, "néo dừng": 2}.get(s.lower(), model.ht_from_string(s))
            elif k in ("COVER", "COVER_B"):
                p[k] = float(s.replace(",", ".")) / 1000.0
            elif k == "SCALE":
                p[k] = int(float(s))
            elif isinstance(model.default_params().get(k), float):
                p[k] = float(s.replace(",", "."))
            else:
                p[k] = s
        return p

    def _changed(self):
        if getattr(self, "_filling", False):
            return
        self.dirty = True
        self._update_info()
        if self.v_auto.get():
            if self._job:
                self.after_cancel(self._job)
            self._job = self.after(1200, self.preview)

    def _update_info(self):
        try:
            p = self._collect()
        except ValueError:
            self.l_err.config(text="[!] Có ô nhập không phải số.")
            return None
        err = model.validate(p)
        warn = [] if err else model.warnings(p)
        self.l_err.config(text=f"[!] {err}" if err else ("".join(f"[Cảnh báo] {w}\n" for w in warn).strip()))
        if not err:
            info = f"Loại móng: {model.type_name(p)}"
            info += "\nHố đào: " + ("đào chung 1 hố cho 4 trụ" if model.pit_joint(p) else "đào riêng từng trụ")
            self.l_info.config(text=info)
        return None if err else p

    def auto_scale(self):
        try:
            p = self._collect()
            self.vars["SCALE"].set(str(model.auto_scale(p)))
        except ValueError:
            pass

    # ---------------------------------------------------------- hành động
    def pick_excel(self):
        f = filedialog.askopenfilename(title="Chọn file Excel (sheet TONG HOP)",
                                       filetypes=[("Excel", "*.xls *.xlsx *.xlsm"), ("Tất cả", "*.*")],
                                       initialdir=os.path.dirname(self.xls) if self.xls else None)
        if f:
            self.read_excel(f)

    def read_excel(self, path):
        if not path:
            return self.pick_excel()
        try:
            p, warn = model.read_excel(path, "TONG HOP", self.p)
        except Exception as ex:
            messagebox.showerror(APP_NAME, f"Không đọc được file Excel:\n{ex}")
            return
        if model.validate(p) is None and int(p["SCALE"]) < model.auto_scale(p):
            p["SCALE"] = model.auto_scale(p)          # tỷ lệ hiện tại không đủ chỗ -> tự chọn
        self.p, self.xls = p, path
        self.offsets = load_layout(path)
        self.pending = {}
        self._undo.clear()
        self._redo.clear()
        self._fill()
        msg = f"Đã đọc {os.path.basename(path)}."
        if warn:
            msg += "  Cảnh báo: " + " ".join(warn)
        self.l_msg.config(text=msg)
        self.preview()

    def pick_frame(self):
        f = filedialog.askopenfilename(title="Chọn file DXF khung tên", filetypes=[("DXF", "*.dxf")])
        if not f:
            return
        try:
            doc, tags = frame.new_output_doc(f, "TKBVTC", self.fields)
        except Exception as ex:
            messagebox.showerror(APP_NAME, f"Không nạp được khung tên:\n{ex}")
            return
        self.frame_path = f
        self._fill()
        msg = f"Đã nạp khung tên {os.path.basename(f)}."
        if tags:
            msg += " Attribute: " + ", ".join(sorted(tags))
        self.l_msg.config(text=msg)
        self.preview()

    def edit_fields(self):
        FieldsDialog(self)

    def _render(self, p, done, only=None):
        def work():
            try:
                res = export.build(p, self.frame_path or None, self.fields, dict(self.offsets))
                data = export.pdf_bytes(res, only)
                imgs = pdf_images(data)
                if only is not None:          # chỉ dựng lại tờ đang xem, các tờ khác giữ ảnh cũ
                    full = list(self.pages)
                    for k, i in enumerate(sorted(only)):
                        if i < len(full):
                            full[i] = imgs[k]
                    imgs, data = full, None
                self.after(0, lambda: done(res, data, imgs, None))
            except Exception as ex:
                err = (ex, traceback.format_exc())
                sys.stderr.write(err[1])
                self.after(0, lambda: done(None, None, None, err))
        threading.Thread(target=work, daemon=True).start()

    def preview(self, only=None):
        self._job = None
        if self.busy:
            self._job = self.after(400, lambda: self.preview(only))
            return
        p = self._update_info()
        if p is None:
            return
        self.v3d.set_params(p)
        self.busy = True
        self.l_state.config(text="Đang dựng bản vẽ...")
        self.config(cursor="watch")

        def done(res, data, imgs, err):
            self.busy = False
            self.config(cursor="")
            if err:
                self.l_state.config(text="Lỗi khi dựng bản vẽ")
                messagebox.showerror(APP_NAME, f"{err[0]}\n\n{err[1][-1500:]}")
                return
            self.res, self.pdf, self.pages = res, data, imgs
            self.dirty = data is None
            self.pending = {}
            if self.l_msg.cget("text").startswith("Đã dịch chuyển"):
                self.l_msg.config(text="")
            vals = [f"Tờ {i + 1}" for i in range(len(imgs))]
            self.cb_page.config(values=vals)
            self._show_page(min(self.page_i, len(imgs) - 1))
            self.l_state.config(text=f"{len(imgs)} tờ A3 - tỷ lệ 1/{res.geo.den}")
        if only is not None and len(self.pages) != (2 if model.is_detail(p) else 1):
            only = None
        self._render(p, done, only)

    def _ensure_fresh(self, then):
        if self.pdf is not None and not self.dirty:
            return then()
        p = self._update_info()
        if p is None:
            messagebox.showwarning(APP_NAME, self.l_err.cget("text") or "Số liệu chưa hợp lệ.")
            return
        self.busy = True
        self.l_state.config(text="Đang dựng bản vẽ...")

        def done(res, data, imgs, err):
            self.busy = False
            if err:
                messagebox.showerror(APP_NAME, f"{err[0]}")
                return
            self.res, self.pdf, self.pages, self.dirty = res, data, imgs, False
            self.pending = {}
            self.cb_page.config(values=[f"Tờ {i + 1}" for i in range(len(imgs))])
            self._show_page(min(self.page_i, len(imgs) - 1))
            then()
        self._render(p, done)

    def _default_name(self, ext):
        if self.xls:
            return os.path.splitext(os.path.basename(self.xls))[0] + ext
        p = self.p
        nm = f"MONG_{model.type_name(p)}_{p.get('COT', '')}_{p.get('GD', '')}".replace(" ", "_").replace("/", "-")
        return nm + ext

    def export_pdf(self):
        def go():
            f = filedialog.asksaveasfilename(title="Xuất PDF", defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
                                             initialfile=self._default_name(".pdf"),
                                             initialdir=os.path.dirname(self.xls) if self.xls else None)
            if f:
                try:
                    with open(f, "wb") as fh:
                        fh.write(self.pdf)
                    self.l_msg.config(text=f"Đã xuất PDF: {f}")
                except OSError as ex:
                    messagebox.showerror(APP_NAME, f"Không ghi được file:\n{ex}")
        self._ensure_fresh(go)

    def export_dxf(self):
        def go():
            f = filedialog.asksaveasfilename(title="Xuất AutoCAD (DXF)", defaultextension=".dxf",
                                             filetypes=[("AutoCAD DXF", "*.dxf")],
                                             initialfile=self._default_name(".dxf"),
                                             initialdir=os.path.dirname(self.xls) if self.xls else None)
            if f:
                try:
                    export.save_dxf(self.res, f)
                    self.l_msg.config(text=f"Đã xuất DXF: {f}  (mở bằng AutoCAD, Save As .dwg nếu cần)")
                except Exception as ex:
                    messagebox.showerror(APP_NAME, f"Không ghi được file:\n{ex}")
        self._ensure_fresh(go)

    def export_xlsx(self):
        def go():
            base = os.path.splitext(self._default_name(".xlsx"))[0] + "_KL.xlsx"
            f = filedialog.asksaveasfilename(title="Xuất Excel khối lượng", defaultextension=".xlsx",
                                             filetypes=[("Excel", "*.xlsx")], initialfile=base,
                                             initialdir=os.path.dirname(self.xls) if self.xls else None)
            if not f:
                return
            if self.xls and os.path.abspath(f) == os.path.abspath(self.xls):
                messagebox.showerror(APP_NAME, "Không được ghi đè lên file Excel đầu vào.")
                return
            try:
                kl_excel.export(self.res.geo.p, self.res.geo, f)
                self.l_msg.config(text=f"Đã xuất Excel khối lượng: {f}")
            except Exception as ex:
                messagebox.showerror(APP_NAME, f"Không ghi được file:\n{ex}")
        self._ensure_fresh(go)

    # ------------------------------------------------------------ xem trước
    def _show_page(self, i):
        if not self.pages:
            return
        self.page_i = max(0, i)
        self.v_page.set(f"Tờ {self.page_i + 1}")
        self._redraw()

    def zoom_fit(self):
        self.zoom = None
        self._redraw()

    def zoom_by(self, f, e=None):
        """Phóng to / thu nhỏ; có sự kiện chuột thì giữ nguyên điểm bản vẽ dưới con trỏ.
        Vẽ nhanh (nội suy thô) ngay, vẽ nét đẹp sau khi ngừng lăn chuột."""
        if not self.pages:
            return
        old = self._geom
        if e is not None and old:
            ex, ey = e.x_root - self.pv.winfo_rootx(), e.y_root - self.pv.winfo_rooty()
            cx, cy = self.pv.canvasx(ex), self.pv.canvasy(ey)
            ow, oh = self._zs[1], self._zs[2]
            fu, fv = (cx - old[0]) / ow, (cy - old[1]) / oh
        self.zoom = min(4.0, max(0.1, (self.zoom or self._fit_zoom()) * f))
        self._redraw(paint=False)
        if e is not None and old and self._geom:
            x0, y0, _ = self._geom
            nw, nh = self._zs[1], self._zs[2]
            sw = max(self.pv.winfo_width(), nw + 20)
            sh = max(self.pv.winfo_height(), nh + 20)
            self.pv.xview_moveto(max(0.0, (x0 + fu * nw - ex) / sw))
            self.pv.yview_moveto(max(0.0, (y0 + fv * nh - ey) / sh))
        self._paint(fast=True)
        self._paint_later()

    def _paint_later(self, ms=180):
        if getattr(self, "_pjob", None):
            self.after_cancel(self._pjob)
        self._pjob = self.after(ms, self._paint)

    def _fit_zoom(self):
        im = self.pages[self.page_i]
        w, h = max(50, self.pv.winfo_width() - 20), max(50, self.pv.winfo_height() - 20)
        return min(w / im.width, h / im.height)

    def _redraw(self, paint=True):
        """Bố trí trang trên khung xem (kích thước ảo theo zoom); chỉ dựng ảnh phần đang thấy (_paint)."""
        if not self.pages:
            return
        im = self.pages[self.page_i]
        z = self.zoom or self._fit_zoom()
        w, h = max(1, int(im.width * z)), max(1, int(im.height * z))
        self.pv.delete("all")
        cw, ch = self.pv.winfo_width(), self.pv.winfo_height()
        x0 = max(10, (cw - w) // 2)
        y0 = max(10, (ch - h) // 2)
        self.pv.create_rectangle(x0 + 4, y0 + 4, x0 + w + 4, y0 + h + 4, fill="#232E3A", outline="", tags="bg")
        self.pv.create_rectangle(x0, y0, x0 + w, y0 + h, fill="#FFFFFF", outline="", tags="bg")
        self.pv.configure(scrollregion=(0, 0, max(cw, w + 20), max(ch, h + 20)))
        self._geom = (x0, y0, w / export.PAGE_W)
        self._zs = (z, w, h)
        self._painted = None
        if paint:
            self._paint()
        self._overlay()

    def _paint(self, fast=False):
        """Dựng ảnh vùng nhìn thấy (+ lề nửa khung mỗi phía để kéo không bị trống)."""
        from PIL import Image, ImageTk
        self._pjob = None
        if not self.pages or not self._geom:
            return
        im = self.pages[self.page_i]
        x0, y0, _ = self._geom
        z, w, h = self._zs
        cw, ch = self.pv.winfo_width(), self.pv.winfo_height()
        vx, vy = self.pv.canvasx(0), self.pv.canvasy(0)
        rx0, ry0 = max(x0, int(vx - cw / 2)), max(y0, int(vy - ch / 2))
        rx1, ry1 = min(x0 + w, int(vx + 1.5 * cw)), min(y0 + h, int(vy + 1.5 * ch))
        if rx1 - rx0 < 1 or ry1 - ry0 < 1:
            return
        box = ((rx0 - x0) / z, (ry0 - y0) / z, min(im.width, (rx1 - x0) / z), min(im.height, (ry1 - y0) / z))
        self._zimg = im.resize((rx1 - rx0, ry1 - ry0), Image.BILINEAR if fast else Image.BICUBIC, box=box)
        self._zorg = (rx0, ry0)
        self._tkimg = ImageTk.PhotoImage(self._zimg)
        self.pv.delete("pg")
        self.pv.create_image(rx0, ry0, image=self._tkimg, anchor="nw", tags="pg")
        self.pv.tag_raise("pg", "bg")
        self.pv.tag_raise("ov")
        self._painted = (rx0, ry0, rx1, ry1)

    def _view_covered(self):
        p = getattr(self, "_painted", None)
        if not p:
            return False
        vx, vy = self.pv.canvasx(0), self.pv.canvasy(0)
        cw, ch = self.pv.winfo_width(), self.pv.winfo_height()
        x0, y0, _ = self._geom
        z, w, h = self._zs
        return (p[0] <= max(vx, x0) and p[1] <= max(vy, y0) and p[2] >= min(vx + cw, x0 + w)
                and p[3] >= min(vy + ch, y0 + h))

    def _zcrop(self, x1, y1, x2, y2):
        """Ảnh trang (đã zoom) trong khung toạ độ canvas, lấy thẳng từ ảnh gốc (nền trắng ngoài trang)."""
        from PIL import Image
        im = self.pages[self.page_i]
        gx, gy, _ = self._geom
        z = self._zs[0]
        out = Image.new("RGB", (max(1, int(x2 - x1)), max(1, int(y2 - y1))), "white")
        sx0, sy0 = max(0.0, (x1 - gx) / z), max(0.0, (y1 - gy) / z)
        sx1, sy1 = min(im.width, (x2 - gx) / z), min(im.height, (y2 - gy) / z)
        if sx1 > sx0 and sy1 > sy0:
            px0, py0 = int(gx + sx0 * z - x1), int(gy + sy0 * z - y1)
            part = im.resize((max(1, int((sx1 - sx0) * z)), max(1, int((sy1 - sy0) * z))), Image.BILINEAR,
                             box=(sx0, sy0, sx1, sy1))
            out.paste(part, (px0, py0))
        return out

    # ------------------------------------------------------------ sắp xếp
    def _objs(self):
        res = getattr(self, "res", None)
        if not res or not self.v_arr.get() or self.page_i >= len(res.objs):
            return []
        return res.objs[self.page_i]

    def _pend(self, o):
        """Dịch chuyển chưa dựng lại của đối tượng (cộng cả nhóm chứa nó)."""
        dx = dy = 0.0
        for oid, d in self.pending.items():
            if o.id == oid or o.id.startswith(oid + "."):
                dx += d[0]
                dy += d[1]
        return dx, dy

    def _box_px(self, o):
        x0, y0, s = self._geom
        dx, dy = self._pend(o)
        b = o.bbox
        return (x0 + (b[0] + dx) * s, y0 + (export.PAGE_H - b[3] - dy) * s,
                x0 + (b[2] + dx) * s, y0 + (export.PAGE_H - b[1] - dy) * s)

    def _overlay(self):
        self.pv.delete("ov")
        if not self._geom:
            return
        sel = set(getattr(self, "_sel", []))
        for o in self._objs():
            x1, y1, x2, y2 = self._box_px(o)
            moved = any(o.id == k or o.id.startswith(k + ".") for k in self.pending)
            if o.id in sel and len(sel) > 1:
                self.pv.create_rectangle(x1 - 3, y1 - 3, x2 + 3, y2 + 3, outline="#6A1B9A", width=2, tags="ov")
                continue
            if o.kind == "anchor" and o.id.endswith("@k"):        # điểm gãy leader
                cx_, cy_ = (x1 + x2) / 2, (y1 + y2) / 2
                self.pv.create_rectangle(cx_ - 3, cy_ - 3, cx_ + 3, cy_ + 3, outline="#1565c0", width=2, tags="ov")
                continue
            if o.kind == "group":
                self.pv.create_rectangle(x1 - 3, y1 - 3, x2 + 3, y2 + 3, outline="#1565c0", dash=(6, 3), tags="ov")
            elif o.kind == "anchor":
                cx_, cy_ = (x1 + x2) / 2, (y1 + y2) / 2
                self.pv.create_oval(cx_ - 3, cy_ - 3, cx_ + 3, cy_ + 3, outline="#2e7d32", width=2, tags="ov")
            else:
                self.pv.create_rectangle(x1 - 1, y1 - 1, x2 + 1, y2 + 1,
                                         outline="#d32f2f" if moved else "#ef6c00", tags="ov")

    def _pick(self, e):
        if not self._geom:
            return None
        x, y = self.pv.canvasx(e.x), self.pv.canvasy(e.y)
        best = None
        for pref in (("anchor",), ("item", "table"), ("group",)):
            for o in self._objs():
                if o.kind not in pref:
                    continue
                x1, y1, x2, y2 = self._box_px(o)
                pad = 3 if o.kind in ("group", "anchor") else 1
                if x1 - pad <= x <= x2 + pad and y1 - pad <= y <= y2 + pad:
                    a = (x2 - x1) * (y2 - y1)
                    if best is None or a < best[0]:
                        best = (a, o)
            if best:
                return best[1]
        return None

    def _hover(self, e):
        if not self.v_arr.get():
            return
        o = self._pick(e)
        self.l_state.config(text=f"{o.label or o.id}  (kéo để dịch chuyển, Ctrl+nhấp: chọn nhiều, "
                                 f"chuột phải: về mặc định)" if o else "")

    def _press(self, e):
        if not self.v_arr.get():
            self.pv.scan_mark(e.x, e.y)
            self._drag = "pan"
            return
        o = self._pick(e)
        self._dlast = (0.0, 0.0)
        sel = getattr(self, "_sel", [])
        if e.state & 0x0004:                      # Ctrl + nhấp: thêm / bớt khỏi nhóm chọn
            if o is not None:
                self._sel = [i for i in sel if i != o.id] if o.id in sel else sel + [o.id]
            self._drag = None
            self._overlay()
            return
        if o is None:
            self._drag = None
            if sel:
                self._sel = []
                self._overlay()
            return
        if o.id in sel and len(sel) > 1:
            objs = [ob for ob in self._objs() if ob.id in sel]
        else:
            self._sel = [o.id]
            objs = [o]
        items = []
        from PIL import ImageTk
        self._dragimgs = []
        for ob in objs:
            x1, y1, x2, y2 = self._box_px(ob)
            if ob.kind != "anchor":
                # phần hình của đối tượng đi theo chuột -> thấy kết quả ngay khi kéo
                tki = ImageTk.PhotoImage(self._zcrop(x1 - 2, y1 - 2, x2 + 3, y2 + 3))
                self._dragimgs.append(tki)
                self.pv.create_rectangle(x1 - 2, y1 - 2, x2 + 3, y2 + 3, fill="white", outline="", tags="ov")
                items.append(self.pv.create_image(x1 - 2, y1 - 2, image=tki, anchor="nw", tags="ov"))
            items.append(self.pv.create_rectangle(x1, y1, x2, y2, outline="#d32f2f", width=2, dash=(4, 2),
                                                  tags="ov"))
        self._drag = (objs, self.pv.canvasx(e.x), self.pv.canvasy(e.y), items)

    def _motion(self, e):
        if self._drag == "pan":
            self.pv.scan_dragto(e.x, e.y, gain=1)
            if not self._view_covered():
                self._paint(fast=True)
            return
        if not self._drag:
            return
        objs, sx, sy, items = self._drag
        dx, dy = self.pv.canvasx(e.x) - sx, self.pv.canvasy(e.y) - sy
        last = getattr(self, "_dlast", (0.0, 0.0))
        for it in items:                          # nền trắng (không có trong items) đứng yên che chỗ cũ
            self.pv.move(it, dx - last[0], dy - last[1])
        self._dlast = (dx, dy)

    def _release(self, e):
        d = self._drag
        self._drag = None
        if d == "pan":
            self._paint_later(60)
            return
        if not d:
            return
        objs, sx, sy, items = d
        self._dlast = (0.0, 0.0)
        s = self._geom[2]
        dx = (self.pv.canvasx(e.x) - sx) / s
        dy = -(self.pv.canvasy(e.y) - sy) / s
        if abs(dx) < 0.2 and abs(dy) < 0.2:
            self._overlay()
            return
        ids = [o.id for o in objs]
        # bỏ đối tượng con khi đã chọn cả đối tượng cha (tránh dịch 2 lần)
        ids = [i for i in ids if not any(i != j and (i.startswith(j + ".") or i.startswith(j + "@")) for j in ids)]
        self._move_many(ids, dx, dy)

    def _snap(self):
        """Lưu trạng thái sắp xếp trước khi thay đổi (cho Ctrl+Z)."""
        self._undo.append(copy.deepcopy(self.offsets))
        del self._undo[:-100]
        self._redo.clear()

    def _undo_redo(self, back):
        if not self.v_arr.get():
            return
        src, dst = (self._undo, self._redo) if back else (self._redo, self._undo)
        if not src:
            return
        dst.append(copy.deepcopy(self.offsets))
        self.offsets = src.pop()
        self.pending = {}
        self.dirty = True
        save_layout(self.xls, self.offsets)
        self.l_msg.config(text="Đã hoàn tác." if back else "Đã làm lại.")
        self.preview()

    def _move(self, oid, dx, dy):
        self._move_many([oid], dx, dy)

    def _move_many(self, ids, dx, dy):
        self._snap()                               # 1 lần hoàn tác cho cả nhóm
        for oid in ids:
            cur = self.offsets.get(oid, [0.0, 0.0])
            self.offsets[oid] = [round(cur[0] + dx, 2), round(cur[1] + dy, 2)]
            pd = self.pending.get(oid, [0.0, 0.0])
            self.pending[oid] = [pd[0] + dx, pd[1] + dy]
        self._layout_changed()

    def _layout_changed(self):
        """Dịch chuyển: dựng lại ngay tờ đang xem (phần đã kéo vẫn hiện ở vị trí mới trong lúc chờ)."""
        self.dirty = True
        save_layout(self.xls, self.offsets)
        self.preview(only={self.page_i})

    def _context(self, e):
        if not self.v_arr.get():
            return
        o = self._pick(e)
        m = tk.Menu(self, tearoff=0)
        if o is not None:
            m.add_command(label=f"Về vị trí mặc định: {o.label or o.id}", command=lambda: self._reset([o.id]))
        sheet = f"s{self.page_i + 1}."
        m.add_command(label="Về vị trí mặc định cả tờ",
                      command=lambda: self._reset([k for k in self.offsets if k.startswith(sheet)]))
        m.tk_popup(e.x_root, e.y_root)

    def _reset(self, ids):
        if any(any(k == i or k.startswith(i + ".") for i in ids) for k in self.offsets):
            self._snap()
        changed = False
        for k in list(self.offsets):
            if any(k == i or k.startswith(i + ".") for i in ids):
                del self.offsets[k]
                changed = True
        if changed:
            self.pending = {k: v for k, v in self.pending.items() if k not in ids}
            self._layout_changed()

    def _guard(self):
        """Dòng tác giả phải luôn hiển thị đúng."""
        try:
            if self._cr.cget("text") != _meta.credit() or not self._cr.winfo_ismapped():
                self._cr.config(text=_meta.credit())
                self._cr.pack(side="left", before=self._cr.master.winfo_children()[0])
        except Exception:
            self.destroy()
            return
        self.after(5000, self._guard)

    def on_close(self):
        try:
            p = self._collect()
        except ValueError:
            p = self.p
        save_settings({"xls": self.xls, "frame": self.frame_path, "fields": self.fields,
                       "auto": self.v_auto.get(), "params": p})
        self.destroy()


def pdf_images(data, dpi=150):
    import pymupdf
    from PIL import Image
    out = []
    with pymupdf.open("pdf", data) as d:
        for pg in d:
            pix = pg.get_pixmap(dpi=dpi)
            out.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
    return out


class FieldsDialog(tk.Toplevel):
    """Chỉnh vị trí các ô điền trong khung tên (toạ độ mm trong khung)."""

    COLS = [("x", 8), ("y", 8), ("h", 6), ("align", 6), ("wmax", 7)]

    def __init__(self, app: App):
        super().__init__(app)
        self.app = app
        self.title("Cấu hình khung tên")
        self.transient(app)
        self.resizable(False, False)
        f = ttk.Frame(self, padding=10)
        f.pack(fill="both")
        ttk.Label(f, text="Toạ độ (mm) tính từ góc dưới trái khung. align: L trái, C giữa (đường cơ sở), "
                          "MC giữa, R phải.\nNếu khung có attribute (TENBV, TYLE, TO, MASO...), app điền vào "
                          "attribute và bỏ qua ô tương ứng.", wraplength=560, justify="left").grid(
            row=0, column=0, columnspan=8, sticky="w", pady=(0, 8))
        ttk.Label(f, text="Ô thông tin").grid(row=1, column=0, sticky="w")
        for j, (c, _) in enumerate(self.COLS):
            ttk.Label(f, text=c).grid(row=1, column=j + 1)
        ttk.Label(f, text="đậm").grid(row=1, column=len(self.COLS) + 1)
        self.v = {}
        for i, (k, lbl) in enumerate(frame.FIELD_LABELS.items()):
            cfg = app.fields.get(k, frame.DEFAULT_FIELDS[k])
            ttk.Label(f, text=lbl).grid(row=i + 2, column=0, sticky="w", padx=(0, 8))
            for j, (c, w) in enumerate(self.COLS):
                var = tk.StringVar(value=str(cfg.get(c, "")))
                ttk.Entry(f, textvariable=var, width=w).grid(row=i + 2, column=j + 1, padx=2, pady=1)
                self.v[(k, c)] = var
            bv = tk.BooleanVar(value=bool(cfg.get("bold")))
            ttk.Checkbutton(f, variable=bv).grid(row=i + 2, column=len(self.COLS) + 1)
            self.v[(k, "bold")] = bv
        bf = ttk.Frame(f)
        bf.grid(row=20, column=0, columnspan=8, sticky="e", pady=(10, 0))
        ttk.Button(bf, text="Mặc định", command=self.reset).pack(side="left")
        ttk.Button(bf, text="Lưu", command=self.ok).pack(side="left", padx=6)
        ttk.Button(bf, text="Huỷ", command=self.destroy).pack(side="left")

    def reset(self):
        for (k, c), var in self.v.items():
            var.set(frame.DEFAULT_FIELDS[k].get(c, "") if c != "bold" else bool(frame.DEFAULT_FIELDS[k].get("bold")))

    def ok(self):
        out = copy.deepcopy(self.app.fields)
        try:
            for (k, c), var in self.v.items():
                cfg = out.setdefault(k, copy.deepcopy(frame.DEFAULT_FIELDS[k]))
                if c == "bold":
                    cfg[c] = bool(var.get())
                elif c == "align":
                    cfg[c] = var.get().strip().upper() or "L"
                else:
                    cfg[c] = float(var.get().replace(",", "."))
        except ValueError:
            messagebox.showerror(APP_NAME, "Toạ độ / chiều cao phải là số.", parent=self)
            return
        self.app.fields = out
        self.destroy()
        self.app.dirty = True
        self.app.preview()


def main():
    try:
        ok = _meta.check(cad._SIG)
    except Exception:
        ok = False
    if not ok:
        r = tk.Tk()
        r.withdraw()
        messagebox.showerror(APP_NAME, "Tệp chương trình đã bị thay đổi, không thể chạy.")
        return
    cad.init_fonts()
    app = App()
    app.after(1500, app._guard)
    app.mainloop()


if __name__ == "__main__":
    main()
