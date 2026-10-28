# Hướng dẫn phát triển: dùng VE_MONGBANCOSUON làm mẫu cho app loại móng khác

> Bản sao từ repo `MONG-BAN-CO-SUON`. App VE_MONGTRU dựng theo kiến trúc này; package đổi tên thành `mongtru`
> (đọc `mongban/...` trong tài liệu là `mongtru/...`). Quy tắc riêng của móng trụ xem README và mục 10 cuối tài liệu.

Tài liệu này mô tả kiến trúc, quy ước và cách làm việc của app **VE_MONGBANCOSUON** (móng bản có dầm). Mục đích là
dùng lại khi viết app cho loại móng khác: móng trụ, móng bản không dầm, móng cọc, móng neo…

Khi bắt đầu app mới với Claude Code, đưa cho phiên mới:
1. Đường dẫn repo này (`ncbang996-source/MONG-BAN-CO-SUON`) và tài liệu này.
2. File Excel mẫu của loại móng mới, có sheet `TONG HOP` và các sheet tính khối lượng.
3. Bản vẽ PDF mẫu của loại móng mới.

---

## 1. Luồng dữ liệu

```
Excel (sheet TONG HOP)
   │  model.read_excel()          đọc ô -> dict p (đơn vị m, Ø/@ theo mm)
   ▼
p (dict thông số)  ◄──── giao diện app.py sửa p (form bên trái)
   │  model.validate() / model.warnings()
   ▼
Geo(p)  (geom.py)                 toàn bộ hình học + bố trí thép + bảng thống kê (g.kl)
   │
   ├─ export.build()              DXF trong bộ nhớ: khung tên + sheet1.draw() + sheet2.draw()
   │     ├─ export.pdf_bytes()    PDF A3 (xem trước + xuất)
   │     └─ export.save_dxf()     AutoCAD DXF
   ├─ kl_excel.export()           Excel khối lượng có công thức (_KL.xlsx)
   └─ view3d.Scene(g)             mô hình 3D (tab "Mô hình 3D", ui3d.py)
```

Nguyên tắc:
- **Một nguồn số liệu:** bản vẽ, bảng thống kê, Excel và 3D đều lấy từ cùng một `Geo`. Không tính lại ở chỗ khác.
- **Khối lượng thép tính từ đúng các thanh vẽ ra:** `geom.calc_kl()` đếm từ danh sách vị trí thanh, không dùng
  công thức riêng.
- **Bê tông, đất, ván khuôn:** công thức theo sheet `KL be tong` của Excel mẫu, trong `model.py`.

## 2. Module nào dùng lại, module nào viết mới

| File | Vai trò | App mới |
|---|---|---|
| `mongban/cad.py` | `Ctx` vẽ DXF: layer, chữ (Roboto Condensed), dim theo tỷ lệ, hatch, đối tượng kéo thả | **Dùng nguyên** |
| `mongban/frame.py` | Khung tên A3: chèn block `KHUNG_TEN`, điền attribute / toạ độ, logo OLE | **Dùng nguyên** |
| `mongban/_meta.py` | Dòng tác giả + mã kiểm tra (xem mục 7) | **Dùng nguyên** |
| `mongban/export.py` | Dựng các tờ, xuất PDF/DXF | Dùng lại, đổi `sheet1/sheet2`, `title_values` |
| `mongban/view.py` | `V` (khung nhìn m → mm giấy), ký hiệu mặt cắt, cao độ, trục đối xứng, ngắt, mũi tên, móc thép, đai, `Callouts` (tag thép) | **Dùng nguyên**, bổ sung ký hiệu mới nếu cần |
| `mongban/tables.py` | Bảng thống kê thép (vẽ hình dạng thanh), bảng tổng kê | Dùng lại khung, sửa `shape()` theo hình dạng thanh mới |
| `mongban/ui3d.py` | Tab 3D: xoay, dịch, phóng, bật/tắt nhóm, cắt 1/4, lưu PNG | **Dùng nguyên** (đổi `LAYER_UI` nếu nhóm thép khác) |
| `mongban/view3d.py` | Dựng & vẽ 3D bằng Pillow (không OpenGL) | Dùng `render()`, viết lại `Scene.build()` |
| `mongban/model.py` | Bản đồ ô Excel, thông số mặc định, khối lượng bê tông/đất, kiểm tra số liệu | **Viết mới** theo Excel của loại móng |
| `mongban/geom.py` | Hình học + bố trí thép + bảng thống kê | **Viết mới** |
| `mongban/sheet1.py`, `sheet2.py` | Nội dung từng tờ bản vẽ | **Viết mới** (tham khảo cách dàn trang, gióng, tag) |
| `mongban/kl_excel.py` | Excel khối lượng: THONG SO (tên định danh `TS_...`), KHOI LUONG (công thức + diễn giải), TONG KE | Dùng lại khung, viết lại công thức |
| `app.py` | Giao diện Tkinter: form, xem trước, zoom, kéo thả, hoàn tác, tab 3D, xuất | Dùng lại, đổi `DIM_FIELDS`, `REBAR_FIELDS`, tên app |
| `tests/smoke.py` | Kiểm tra nhanh: đọc Excel mẫu, so khối lượng, dựng PDF/DXF/Excel | Viết lại số đối chiếu |
| `tools/render_preview.py` | Render PNG xem trước (không cần giao diện) | Dùng nguyên |
| `tools/check_kl_excel.py` | Đối chiếu công thức Excel với chương trình qua LibreOffice | Dùng lại, đổi bộ thông số thử |
| `tools/make_icon.py` | Vẽ icon `.ico` | Vẽ lại hình |
| `.github/workflows/build.yml`, `*.spec`, `version_info.txt`, `build.bat` | Build exe trên GitHub Actions (windows-latest, PyInstaller) | Đổi tên app |

## 3. Quy ước vẽ

### Toạ độ và đơn vị
- Giấy A3 ngang 420 × 297 mm. Mỗi tờ đặt cạnh nhau theo X (`SHEET_DX = 420`), gốc là góc dưới trái khung.
- Trong `Ctx`, toạ độ là **mm giấy**. Hình học móng dùng **m**, đổi sang giấy qua `V(c, ox, oy, den)`:
  `v.x(u)`, `v.y(v)`, `v.P(u, v)`, với `k = 1000 / den` (mm giấy cho 1 m thực).
- Tỷ lệ tờ 1 tự chọn bằng `model.auto_scale()` trong `SCALES = [50, 75, 100, 125, 150, 200, 250]`.
  Mặt cắt chi tiết dùng tỷ lệ cố định (1:25, 1:50).

### Layer và nét in (`cad.LAYERS`)
| Layer | Nét (mm) | Dùng cho |
|---|---|---|
| TRUC, HATCH | 0,13 | trục, hatch |
| DIM, CHU, HINH THUC, BANG | 0,18 | kích thước, chữ, leader, bảng |
| MAIN, MAT CAT, VAI DIA | 0,30 | bao bê tông, ký hiệu mặt cắt |
| DAI | 0,35 | đai, thép phân bố, lưới |
| COTTHEP | 0,50 | thép chủ |

### Chữ
- Chữ bản vẽ và chữ trong bảng cao **2,0 mm**. Tên hình (`view.title`) cao 4 mm, có gạch chân, dòng tỷ lệ
  "TL:1/xx" cao 2 mm bên dưới. Chữ "GHI CHÚ" cao 3,5 mm.
- Đo bề rộng chữ bằng `cad.txtw(s, h)` để tránh đè. Luôn kiểm tra chồng chữ trên ảnh 300 dpi.

### Kích thước
- `v.dimH(p1, p2, y_giấy, tp=None)` và `v.dimV(...)`. Điểm đo tính bằng m, đường kích thước tính bằng mm giấy.
- Mỗi tỷ lệ có dimstyle riêng (`cad.ensure_dimstyle`). Khi cần, đặt chữ ở vị trí khác bằng `tp`.
- Đường gióng của 2 kích thước không được cắt nhau. Gióng xuyên qua lớp đệm cát thì đo từ đáy đệm cát.

### Tag thép (`view.Callouts`)
- `co(targets, bx, by, side, num, txt1, txt2=None, tick=True, mode=False)`:
  - `targets`: các điểm chạm thép (mm giấy).
  - `bx, by`: đầu đường tag phía hình.
  - `side`: hướng tag chạy ra (+1 phải, −1 trái).
  - `num`: số vị trí **nội bộ** (pos). Số hiển thị là `g.sq(pos)`, đánh lại liên tục, bỏ qua vị trí không có thép.
  - `mode=True`: leader ngang rồi đứng, vuông góc với thanh. `mode=False`: leader xiên.
  - `tick`: có nét xẹt tại điểm chạm. Nếu thanh thép xiên 45° thì dùng `view.tick_at(c, x, y, góc)` để nét xẹt
    không trùng thanh.
- Mỗi tag là 1 đối tượng kéo thả được. Điểm chạm thép (`...@t<i>`) và điểm gãy leader (`...@k`) kéo riêng được.

### Đối tượng kéo thả (chế độ "Sắp xếp")
- `with c.group("tên", "nhãn"):` bọc cả 1 hình. `with c.item("tên", "nhãn"):` bọc chữ, dim, tag, bảng.
- Dịch chuyển lưu theo id (`s1.plan.callout3`…) vào `<file Excel>.layout.json`. Điểm có `fixed=True` (mũi leader,
  điểm đo dim) không đi theo item.
- App hỗ trợ: Ctrl+nhấp để chọn nhiều đối tượng, Ctrl+Z / Ctrl+Y, chuột phải để về vị trí mặc định.

## 4. Excel khối lượng (`kl_excel.py`)

- **Sheet THONG SO:** mỗi thông số là 1 ô vàng có tên định danh `TS_<ký hiệu>`.
  - Tên định danh Excel **không phân biệt hoa/thường**: `TS_b` (cổ móng) trùng `TS_B` (bề rộng móng), nên phải
    đặt tên khác (`TS_bc`).
- **Sheet KHOI LUONG:** mỗi dòng có ký hiệu, công thức và diễn giải.
  - Phần thép gồm các đại lượng trung gian (số thanh từng vùng, số hàng, số mức…) và 1 dòng cho mỗi vị trí thép.
  - Ø, chiều dài, số lượng đều là công thức theo `TS_...`. Cột I, J là diễn giải.
  - Đưa đủ mọi vị trí thép, kể cả vị trí có số lượng bằng 0. Số hiệu là công thức
    `=IF(E>0,COUNTIF(E$đầu:E,">0"),"—")` để tự đánh lại khi sửa số liệu.
  - Quy tắc rải thép viết thành hàm Excel giống hệt Python: `lin` → `ROUND(w/@)+1`, `cells` → `ROUNDUP(w/@)`,
    `stations` → `1+ROUNDUP(w/@)`. Bố trí phức tạp (đai phụ cổ móng) dùng bảng tra do chương trình lập trong
    THONG SO, kết hợp `VLOOKUP`.
- **Sheet TONG KE:** bảng tổng kê 1 vị trí móng, tham chiếu sang KHOI LUONG.
- **Kiểm tra bắt buộc sau mỗi lần sửa công thức:** chạy `python tools/check_kl_excel.py`. Công cụ này cho
  LibreOffice tính lại rồi so từng vị trí với chương trình. Phải ra 0 lỗi.

## 5. Quy trình làm việc đã thống nhất với người dùng

1. **Đọc kỹ Excel mẫu:** sheet `TONG HOP` (ô nhập), `KL be tong`, `KL thep mong` (công thức khối lượng), và bản
   vẽ PDF mẫu.
2. **Hỏi lại trước khi code** mọi điểm chưa rõ. Mỗi đợt góp ý (file CMT*.docx): đọc hết, liệt kê cách hiểu từng ý,
   hỏi các ý chưa rõ, rồi mới sửa.
3. **Gửi ảnh xem trước trước khi xuất:** dùng `tools/render_preview.py`, kiểm tra ở 300 dpi. Thử cả móng mẫu và
   một móng lớn hoặc bất thường (nhiều thanh, không lỗ, không vát…).
4. **Đối chiếu số:** khối lượng bê tông/đất phải khớp Excel mẫu (ghi vào `tests/smoke.py`). Thép khớp
   `KL thep mong`, trừ các quy tắc người dùng đã chốt khác. Ghi rõ lý do khác trong comment của smoke test.
5. **Build:** đẩy lên nhánh `claude/...`. GitHub Actions chạy smoke test rồi đóng exe, tải exe ở mục Artifacts.
6. **Gọi tên:** dùng "dầm" (không dùng "sườn") trong tên gọi và trên bản vẽ.

## 6. Kiểm thử giao diện trên máy cloud (không có Windows)

- Python mặc định trên máy cloud không có Tkinter. Dùng `python3.12`, cài `python3-tk` và `xvfb`, tạo venv có
  `--system-site-packages`, rồi cài lại Pillow trong venv (bản Pillow hệ thống thiếu `ImageTk`).
- Chạy app dưới `xvfb-run -a -s "-screen 0 1700x1000x24"`, điều khiển bằng các hàm của `App`. Các bước phải chạy
  trong `mainloop` (luồng dựng bản vẽ gọi `after()`, chỉ hoạt động khi có mainloop). Chụp ảnh bằng
  `PIL.ImageGrab`.
- Trên GitHub Actions (Windows), console dùng cp1252: in tiếng Việt phải đặt
  `sys.stdout.reconfigure(encoding="utf-8")`.
- Máy cloud không tải được artifact / log của Actions (host blob bị chặn), nên chỉ đọc kết quả qua API.

## 7. Dòng tác giả và mã kiểm tra

- `_meta.credit()` giải mã dòng tác giả hiện ở thanh trạng thái và kiểm tra bằng SHA-256.
- `export.build()` và `main()` gọi `_meta.check(cad._SIG)`. `App._guard()` định kỳ đảm bảo dòng tác giả luôn hiện.
- Khi copy sang app mới, **giữ nguyên** `_meta.py` và `cad._SIG`. Sửa dòng tác giả phải tạo lại `_K/_D/_H` và
  `_SIG` cho khớp, nếu không app báo "Tệp chương trình đã bị thay đổi".

## 8. Bài học và lỗi đã gặp

- **Zoom chậm:** phóng ảnh cả trang ở zoom lớn rất nặng (zoom 4× ≈ 70 triệu điểm ảnh). Chỉ dựng phần đang
  thấy (`App._paint`), vẽ nhanh khi đang lăn chuột, vẽ nét đẹp khi dừng.
- **Lăn chuột:** dùng 1 bộ xử lý chung `bind_all`, chọn khung theo vị trí con trỏ. Combobox không được tự đổi giá
  trị khi lăn qua.
- **Nét xẹt 45° bị che** khi thanh thép cũng xiên 45° (mặt cắt vát nách): xoay nét xẹt theo đường gióng.
- **Đường gióng có đầu thừa** sau thanh cuối: cắt đúng tại thanh đầu và thanh cuối.
- **Chữ đè chữ / đè ký hiệu:** tag nào có khả năng đè thì tính chỗ trống, thử lần lượt các ô ứng viên, không có ô
  nào đủ chỗ thì dùng vị trí dự phòng (xem tag 5 và tag 4 trong `sheet1.plan_bars`).
- **Hai kích thước cùng một góc** (vát nách): cho đường gióng xuất phát từ mút vát để không cắt nhau.
- **Chrome chặn tải exe:** do exe PyInstaller chưa ký số. Người dùng bấm Ctrl+J → Giữ lại. Muốn bị chặn ít hơn
  thì đóng gói dạng thư mục (onedir) rồi nén zip, tự build bootloader, hoặc ký số.

## 9. Quy tắc kỹ thuật đã chốt cho móng bản có dầm (tham khảo cho loại móng tương tự)

- **Thép bản:**
  - 2 lớp. Lớp ngoài cùng là thanh theo phương cạnh dài.
  - Ô 2 cạnh ngàm dùng @2, ô 4 cạnh ngàm dùng @1.
  - Có lỗ thì thép ngắt tại lỗ, cộng thép xiên 4 góc lỗ (dài c·√2 + 800, số thanh là bội số của 8).
- **Thanh chống:**
  - Chia ô theo `ROUNDUP(w/@)`.
  - Thân dài h1 − 2 lớp bảo vệ − 2Ø, chân 100. Đỡ thanh ngoài cùng của lớp dưới và lớp trên.
  - Ở mặt cắt thấy chữ C thì chấm thép bản nằm giữa nhịp chân C.
- **Thép chủ dầm (mỗi mặt):**
  - Khoảng hở ngang ≥ 40 mm, không đủ thì thêm hàng. Hàng dưới tối thiểu 2 thanh, đặt 2 bên.
  - Hàng dưới ≤ 2 thanh thì xếp đầy hàng ngoài và không cần đai phụ giữ lớp 2.
  - Hàng dưới > 2 thanh thì người dùng chọn "các hàng đều nhau" hoặc "đầy hàng ngoài".
  - Dưới 5 thanh: không cắt. Từ 5 thanh: số thanh dài suốt n/2 nếu n chia hết 4, ngược lại INT(n/2) + 1. Còn lại
    là thanh ngắt.
  - Hàng có 1 phần thanh ngắt: thanh góc dài suốt, thanh ngắt xen kẽ ở cột trong (so le), ví dụ 5 thanh thì cắt
    cột 2 và 4.
  - Thanh ngắt cắt mỗi đầu ½ khoảng mép dầm → mép móng, làm tròn lên 100, tính từ mép móng.
  - Từ 10 thanh trở lên (nhiều hàng): mỗi hàng >= 3 thanh giữ thanh góc dài suốt, ngắt xen kẽ từ 2 phía vào
    (5 thanh: vị trí 2, 4; 4 thanh: 2, 3; 3 thanh: thanh giữa). Hàng 2 thanh (xét từ trong ra) ngắt cả 2 nếu số
    thanh dài suốt vẫn >= số thanh ngắt. Ví dụ 5+4+2: 7 dài suốt / 4 ngắt; 5+5+2: 6 / 6.
  - Số thanh dài suốt luôn >= số thanh ngắt.
  - Thép đáy dầm tựa trên lớp thép bản vuông góc với dầm.
- **Thép giá:**
  - Theo TCVN 5574:2018 mục 10.3.3.3: h > 700 thì số mức mỗi bên = ROUNDUP((z_trên − z_dưới)/400) − 1.
  - Ø thép giá bằng Ø thép bản.
- **Đai phụ:**
  - Móc 2 đầu bằng nhau, tổng dài (kể cả móc) bằng bề rộng đai chính.
  - Đai phụ giữ lớp 2 chỉ rải trong đoạn thanh ngắt, trừ khi thanh biên lớp 2 là thanh dài suốt.
- **Cổ móng:**
  - Thép chủ neo chân 500 (cố định). Khoảng hở thép chủ < 40 mm thì cảnh báo.
  - Đai phụ giữ các thanh cách nhau ≤ 400 mm. Mặt cắt 5-5 ghi tổng số thanh, đai phụ ghi "SO LE".
- **Thang leo:** đặt ở 2 trụ chéo nhau khi H2 > 1,5 m.
- **Khối lượng:**
  - Vải địa tính theo cách trải phẳng 1 tấm chữ nhật. Mái hố đào vẽ 1:0,5.
  - Hệ số mái trong Excel chỉ dùng để tính khối lượng.
  - Đền bù: rộng B + 1, dài L + 1.

## 10. Quy tắc đã chốt cho móng trụ rời (VE_MONGTRU)

- Excel mẫu `samples/D112-30.xls` (đọc thẳng `.xls` bằng `xlrd`). Ô sheet `TONG HOP` xem README.
- Khối lượng thép tính và trình bày như app móng bản không dầm: lớp trên uốn theo mặt vát và thanh chống có chiều
  dài từng thanh khác nhau → bảng thống kê ghi chiều dài trung bình (Ltb) + bảng kích thước từng thanh.
- Excel khối lượng như app móng bản không dầm: bê tông / đất / ván khuôn là công thức theo `TS_...`; thép lấy
  chiều dài, số thanh từ chương trình.
- Đai cổ móng: số đai trên cùng = số lớp lưới đầu trụ (đặt dưới từng lớp lưới, cách theo bước lưới), còn lại @ đai.
- Đai phụ, đai bát giác, neo chân thép chủ 500: như app móng bản có dầm.
- Dự phòng thép (ô H29) chỉ cộng vào bảng tổng kê và Excel khối lượng.
- Cổ móng vát (b1 ≠ b2): chưa hỗ trợ, chờ bản vẽ mẫu.
