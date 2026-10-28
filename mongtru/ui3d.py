"""Khung xem mô hình 3D cốt thép trong ứng dụng (Tkinter): xoay, dịch, phóng to, bật/tắt nhóm, cắt 1/4."""
from __future__ import annotations

import tkinter as tk
import traceback
from tkinter import filedialog, messagebox, ttk

from . import view3d
from .geom import Geo

LAYER_UI = (("bt", "Bê tông", "#B0B660"), ("slab", "Thép bản đế", "#C81E28"), ("pier", "Thép cổ móng", "#DC5A14"),
            ("dai", "Đai cổ móng", "#2850E6"))
VIEWS = (("Trục đo", None), ("Mặt bằng", (0.0, 90.0)), ("Chính diện", (0.0, 0.0)), ("Cạnh", (-90.0, 0.0)))
ISO = {False: (-35.0, 28.0), True: (35.0, 26.0)}      # góc trục đo: toàn móng / cắt 1/4 (nhìn vào mặt cắt)
HINT = "Chuột trái: xoay  ·  Chuột phải / giữa: dịch  ·  Lăn chuột: phóng to, thu nhỏ  ·  Nhấp đúp: góc nhìn mặc định"


class View3D(ttk.Frame):
    def __init__(self, master, app_name="", colors=None):
        super().__init__(master)
        self.app_name = app_name
        c = colors or {}
        self.p = None
        self.scenes = {}
        self.stale = True
        self.yaw, self.pitch = ISO[False]
        self.zoom, self.pan = 1.0, [0.0, 0.0]
        self._drag = None
        self._job = None
        self._img = None

        r1 = ttk.Frame(self, padding=(8, 6, 8, 2))
        r1.pack(side="top", fill="x")
        ttk.Label(r1, text="HIỂN THỊ:", style="Sub.TLabel").pack(side="left", padx=(0, 6))
        self.v_lay = {}
        for key, txt, col in LAYER_UI:
            tk.Frame(r1, background=col, width=10, height=10).pack(side="left", padx=(6, 2))
            v = tk.BooleanVar(value=True)
            ttk.Checkbutton(r1, text=txt, variable=v, command=self.refresh).pack(side="left")
            self.v_lay[key] = v
        ttk.Label(r1, text="PHẠM VI:", style="Sub.TLabel").pack(side="left", padx=(18, 6))
        self.v_q = tk.BooleanVar(value=False)
        ttk.Radiobutton(r1, text="Toàn móng", value=False, variable=self.v_q, command=self._scope).pack(side="left")
        ttk.Radiobutton(r1, text="Cắt 1/4 trụ", value=True, variable=self.v_q, command=self._scope).pack(
            side="left", padx=(6, 0))

        r2 = ttk.Frame(self, padding=(8, 2, 8, 6))
        r2.pack(side="top", fill="x")
        ttk.Label(r2, text="GÓC NHÌN:", style="Sub.TLabel").pack(side="left", padx=(0, 6))
        for txt, ang in VIEWS:
            ttk.Button(r2, text=txt, style="Small.TButton",
                       command=lambda a=ang: self.set_view(a)).pack(side="left", padx=(0, 3))
        ttk.Button(r2, text="Vừa khung", style="Small.TButton", command=self.fit).pack(side="left", padx=(10, 3))
        ttk.Button(r2, text="+", width=3, style="Small.TButton",
                   command=lambda: self.zoom_at(1.25)).pack(side="left")
        ttk.Button(r2, text="−", width=3, style="Small.TButton",
                   command=lambda: self.zoom_at(0.8)).pack(side="left", padx=(2, 0))
        ttk.Button(r2, text="Lưu ảnh PNG...", style="Small.TButton", command=self.save_png).pack(side="right")

        self.cv = tk.Canvas(self, background="#FFFFFF", highlightthickness=0)
        self.cv.pack(fill="both", expand=True)
        self.l_hint = tk.Label(self, text=HINT, background="#FFFFFF", foreground=c.get("muted", "#5B6B80"),
                               anchor="w", padx=8)
        self.l_hint.pack(side="bottom", fill="x")
        self.cv.bind("<Configure>", lambda e: self.refresh())
        self.cv.bind("<ButtonPress-1>", lambda e: self._start(e, "rot"))
        self.cv.bind("<B1-Motion>", self._move)
        self.cv.bind("<ButtonRelease-1>", self._end)
        for b in (2, 3):
            self.cv.bind(f"<ButtonPress-{b}>", lambda e: self._start(e, "pan"))
            self.cv.bind(f"<B{b}-Motion>", self._move)
            self.cv.bind(f"<ButtonRelease-{b}>", self._end)
        self.cv.bind("<Double-Button-1>", lambda e: self.set_view(None))

    # ---------------------------------------------------------------- dữ liệu
    def set_params(self, p):
        """Nhận bộ thông số mới; chỉ dựng lại mô hình khi đang hiển thị (lười)."""
        self.p = dict(p)
        self.scenes = {}
        self.stale = True
        if self.winfo_ismapped():
            self.refresh()

    def scene(self):
        q = self.v_q.get()
        if q not in self.scenes:
            self.scenes[q] = view3d.Scene(Geo(self.p), quarter=q)
        return self.scenes[q]

    # ---------------------------------------------------------------- vẽ
    def refresh(self, fast=False):
        if self._job:
            self.after_cancel(self._job)
            self._job = None
        if fast:
            self._draw(True)
        else:
            self._job = self.after(60, self._draw)

    def _draw(self, fast=False):
        from PIL import ImageTk
        self._job = None
        w, h = self.cv.winfo_width(), self.cv.winfo_height()
        if w < 20 or h < 20:
            return
        self.cv.delete("all")
        if self.p is None:
            self.cv.create_text(w / 2, h / 2, text="Chưa có số liệu - mở file Excel để xem mô hình 3D.",
                                fill="#5B6B80")
            return
        try:
            lay = tuple(k for k, v in self.v_lay.items() if v.get())
            im = view3d.render(self.scene(), w, h, self.yaw, self.pitch, self.zoom, lay, pan=tuple(self.pan),
                               fast=fast)
        except Exception as ex:
            traceback.print_exc()
            self.cv.create_text(w / 2, h / 2, text=f"Không dựng được mô hình 3D:\n{ex}", fill="#C62828")
            return
        self.stale = False
        self._img = ImageTk.PhotoImage(im)
        self.cv.create_image(0, 0, image=self._img, anchor="nw")
        self._gizmo(w, h)

    def _gizmo(self, w, h):
        gx, gy, L = w - 46, h - 40, 26
        for (ax, ay), t, col in zip(view3d.axes2d(self.yaw, self.pitch), "XYZ", ("#C62828", "#2E8B57", "#2E75B6")):
            if abs(ax) + abs(ay) < 0.05:
                continue
            x1, y1 = gx + L * ax, gy - L * ay
            self.cv.create_line(gx, gy, x1, y1, fill=col, width=2)
            self.cv.create_text(gx + 1.35 * L * ax, gy - 1.35 * L * ay, text=t, fill=col, font=("", 9, "bold"))

    # ---------------------------------------------------------------- thao tác
    def _scope(self):
        self.set_view(None)

    def set_view(self, ang):
        self.yaw, self.pitch = ang if ang else ISO[self.v_q.get()]
        self.fit()

    def fit(self):
        self.zoom, self.pan = 1.0, [0.0, 0.0]
        self.refresh()

    def zoom_at(self, f, x=None, y=None):
        w, h = self.cv.winfo_width(), self.cv.winfo_height()
        x = w / 2 if x is None else x
        y = h / 2 if y is None else y
        nz = min(40.0, max(0.2, self.zoom * f))
        f = nz / self.zoom
        self.zoom = nz
        # giữ điểm dưới con trỏ đứng yên
        self.pan[0] = x + f * (w / 2 + self.pan[0] - x) - w / 2
        self.pan[1] = y + f * (h / 2 + self.pan[1] - y) - h / 2
        self.refresh(fast=True)
        self.refresh()

    def wheel(self, e, delta):
        self.zoom_at(1.15 if delta > 0 else 1 / 1.15, e.x, e.y)

    def _start(self, e, mode):
        self._drag = (mode, e.x, e.y, self.yaw, self.pitch, list(self.pan))

    def _move(self, e):
        if not self._drag:
            return
        mode, x0, y0, yaw0, pit0, pan0 = self._drag
        if mode == "rot":
            self.yaw = yaw0 - 0.4 * (e.x - x0)
            self.pitch = min(90.0, max(-30.0, pit0 + 0.4 * (e.y - y0)))
        else:
            self.pan = [pan0[0] + e.x - x0, pan0[1] + e.y - y0]
        self._draw(True)

    def _end(self, e):
        if self._drag:
            self._drag = None
            self.refresh()

    def save_png(self):
        if self.p is None:
            return
        fn = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("Ảnh PNG", "*.png")],
                                          initialfile="mo_hinh_3D.png")
        if not fn:
            return
        try:
            w, h = self.cv.winfo_width(), self.cv.winfo_height()
            s = max(1.0, 2400.0 / max(1, w))
            lay = tuple(k for k, v in self.v_lay.items() if v.get())
            im = view3d.render(self.scene(), int(w * s), int(h * s), self.yaw, self.pitch, self.zoom, lay,
                               pan=(self.pan[0] * s, self.pan[1] * s))
            im.save(fn)
        except Exception as ex:
            messagebox.showerror(self.app_name, f"Không lưu được ảnh:\n{ex}")
