# Quy tắc chung khi lập app vẽ móng (rút ra từ VE_MONGTRU) - dùng cho app Móng bản không sườn

Tài liệu này gom các quy tắc làm việc, quy ước kỹ thuật và chức năng chung đã thống nhất trong quá trình lập app
**VE_MONGTRU** (móng trụ rời 4 trụ, repo `ncbang996-source/MONG-TRU`). Dùng để cập nhật app **Móng bản không sườn**
(VE_MONGBANKOSUON) và các app móng sau này.

- Kiến trúc gốc (luồng dữ liệu, module, quy ước vẽ, Excel khối lượng, dòng tác giả): xem
  [HUONG_DAN_PHAT_TRIEN.md](HUONG_DAN_PHAT_TRIEN.md). Tài liệu này **bổ sung** phần làm thêm sau đó.
- Quy tắc khóa định dạng của móng trụ: xem [KHOA_DINH_DANG.md](KHOA_DINH_DANG.md).

**Cách dùng:** chép file này (và `HUONG_DAN_PHAT_TRIEN.md`) vào thư mục `docs/` của repo app móng bản không sườn. Ở
phiên làm việc mới, đưa đường dẫn 2 file này kèm repo `MONG-TRU` để tham chiếu mã nguồn.

---

## 1. Quy trình làm việc với người dùng

### 1.1 Nguyên tắc
- **Hỏi lại nếu chưa rõ, đừng đoán.** Ý nào có từ 2 cách hiểu trở lên (hướng mũi tên, vị trí, số lượng lấy từ đâu…)
  thì hỏi trước khi code: nêu các phương án, có phương án đề xuất.
- **Báo cáo bằng tiếng Việt:** ngắn gọn, nói rõ đã làm gì, kiểm tra thế nào, còn gì chưa làm hoặc chưa chắc.
- **Gửi ảnh kết quả** (render 300 dpi) cho mọi thay đổi về hình vẽ / giao diện.
- **Không tự đổi số phiên bản.** `__version__` / `version_info.txt` chỉ đổi khi người dùng yêu cầu (ví dụ "tạo
  version 1.1.0"). Ghi lại thay đổi của từng phiên bản trong README (mục "Phiên bản").
- **Giữ dòng tác giả** (`_meta.credit()`, thanh trạng thái, thông tin file exe) trừ khi người dùng yêu cầu khác.
  Thao tác đổi qua lại (ẩn rồi giữ lại tác giả) phải khôi phục đúng nguyên bản cũ.

### 1.2 Mỗi đợt góp ý (file `cmt*.docx`)
1. Giải nén docx, đọc **toàn bộ** chữ và **từng ảnh** (khoanh đỏ, gạch đỏ là chỗ cần sửa / xoá).
2. Lập bảng *# - nội dung - cách hiểu* cho từng ý. Ý chưa rõ thì hỏi trước.
3. Sửa, chạy đủ kiểm thử (mục 1.4), cập nhật README và `docs/`.
4. Commit, đẩy lên nhánh `claude/...`, chờ GitHub Actions build exe xong (thành công) rồi mới báo.
5. Báo cáo theo đúng bảng ý ở bước 2. Ghi thêm chỗ tự phát hiện và sửa (ví dụ file khối lượng bị liệt kê như móng).

### 1.3 Giữ ổn định bản đã chốt
- Bản ổn định được lưu ở nhánh riêng (ví dụ `ban-on-dinh-1.0.0`). Proxy chặn đẩy tag nên dùng nhánh.
- Phần mới viết ở module / package riêng (ví dụ móng 2 loại: `mongtru/lech/`). Chỉ **gọi lại** hàm của bản ổn định.
  Cần sửa hàm dùng chung thì phải giữ nguyên kết quả cũ.
- **Khóa định dạng:** `tests/regression.py` so dấu vân tay từng tờ (mọi nét, chữ, kích thước), bảng thép, khối
  lượng, công thức Excel của các trường hợp mẫu với `tests/golden.json`. Phải ra **0 chỗ khác**.
  - Người dùng yêu cầu đổi định dạng → chạy `--update` (ghi lại mẫu) và ghi thay đổi vào `docs/KHOA_DINH_DANG.md`.
  - Regression chỉ kiểm DXF. Thay đổi cách in PDF (chữ, font, ảnh) phải tự kiểm bằng ảnh chồng (mục 5.2).

### 1.4 Kiểm thử bắt buộc trước mỗi commit
| Lệnh | Kiểm |
|---|---|
| `python tests/regression.py` | khóa định dạng: 0 chỗ khác |
| `python tests/smoke.py` (+ `smoke_*.py`) | đọc Excel mẫu, khối lượng khớp Excel mẫu, dựng PDF / DXF / Excel / 3D, các trường hợp đặc biệt |
| `python tools/check_kl_excel.py` | LibreOffice tính lại Excel khối lượng, so với chương trình: 0 lỗi |
| `python -m pyflakes <package> app.py tests` | không lỗi |
| Thử giao diện thật (mục 6) | mọi thay đổi ở `app.py` |

- Mỗi chức năng mới có 1 file test riêng (`smoke_frame`, `smoke_ifc`, `smoke_batch`, `smoke_plan11`…) và thêm vào
  `.github/workflows/build.yml`. CI chạy trên Windows nên kiểm được cả font, đường dẫn của Windows.
- Test so số liệu với **nguồn gốc** (bảng tổng kê tờ 1, Excel mẫu), không so với chính nó.

---

## 2. Giao diện (app.py)

### 2.1 Bố cục, màu
- Bảng màu `C`: nền tối là **xanh navy sậm** (`navy #0E1E3E`, nút xuất `green #1A3263`, nền xem trước
  `stage #14264A`); điểm nhấn nâu / cam giữ nguyên. Không dùng màu đen.
- Mô tả phần mềm (`APP_DESC`) ghi ở dải tiêu đề và thanh trạng thái.
- Thanh công cụ chia nhóm, tự xuống dòng khi hẹp:
  - **Dữ liệu:** Mở Excel…, ⟳ Đọc lại, Dự án ▾, Thư mục…
  - **Khung tên:** Khung tên…, ⚙ Cấu hình…
  - **Xem:** ▶ Xem trước, ☐ Tự cập nhật, ☐ Sắp xếp
  - **Xuất:** một nút **"Xuất file ▾"** sổ xuống: PDF, AutoCAD DXF, Excel khối lượng, IFC, Tất cả…, Xuất đồng loạt
    (dự án / thư mục).
- **Nhãn nút ngắn** (dài thì cắt, có dấu "…"). Rê chuột hiện **chú giải kiểu AutoCAD** (lớp `Tip`: tên đầy đủ in
  đậm + 1 dòng mô tả), áp dụng cho mọi nút và ô tích trên thanh công cụ và thanh dự án.
- Hộp thoại không ghi chú thích thừa trong tiêu đề (ví dụ chỉ "Dự án", không "Dự án - xuất đồng loạt").
- Số phiên bản đặt **một chỗ**: `<package>/__init__.py` (`__version__`). App, IFC, ... đều đọc từ đây.

### 2.2 Dự án (nhiều móng)
- Dự án = danh sách file Excel móng + số lượng từng móng + móng đang xem, lưu thành **file dự án** JSON
  (`*.mongtru`; app móng bản đặt đuôi riêng, ví dụ `*.mongban`, cần hỏi người dùng).
  - Đường dẫn Excel lưu **tương đối** với file dự án: chép cả thư mục sang máy khác vẫn mở được. File thiếu thì
    báo và bỏ qua. File không đúng định dạng thì báo lỗi.
  - Dự án đã lưu **tự lưu** khi đổi danh sách, thứ tự, móng đang xem, số lượng.
- Menu **Dự án ▾**: Tạo dự án từ nhiều file Excel… / Mở file dự án… / Lưu dự án / Lưu dự án thành… / Đóng dự án.
- **Thanh DỰ ÁN** (chỉ hiện khi có dự án):
  - tên file dự án (hoặc "Dự án chưa lưu");
  - danh sách móng, ◀ ▶, số thứ tự "i/N móng";
  - các nút + Thêm…, − Bớt (không xoá file Excel), Lưu, Đóng. Không đặt nút xuất ở đây vì đã có trong menu Xuất.
- Chọn móng thì mở file Excel đó, kèm vị trí sắp xếp và tỷ lệ chọn tay đã lưu riêng của nó (`<file>.layout.json`, khoá `offsets`, `scale`). Mọi lựa chọn người dùng sửa tay mà Excel không có phải lưu theo file như vậy, không được mất khi chuyển móng.

### 2.3 Bảng xuất đồng loạt (Thư mục dự án / Dự án) - `BatchDialog`
- Thư mục: quét file Excel (tuỳ chọn gồm thư mục con), **xếp theo số tự nhiên** (1, 2, …, 9, 10 - hàm
  `batch.natural_key`). Bỏ file tạm `~$`, file đã xuất `*_KL.xlsx` và file khối lượng tổng hợp.
- Bảng có các cột: tên file, **SL** (nhấp đúp để nhập số lượng ngay tại ô), Loại, Trạng thái.
  - Nút **▲ ▼** đưa các dòng đang chọn lên / xuống. Ở chế độ dự án, thứ tự mới lưu vào dự án.
  - Thư mục: có nút "Mở file đang chọn" và "Nhập các file đang chọn vào dự án". Dự án: bỏ "Mở file".
- Loại file xuất: PDF, DXF, Excel khối lượng, IFC, **Khối lượng tổng hợp** (mục 4.5). Thư mục xuất mặc định `XUAT`,
  giữ cấu trúc thư mục con, tên file = tên file Excel.
- Chạy nền (luồng phụ + `queue` + `after()`), có thanh tiến độ, trạng thái từng file, nút Dừng. File lỗi ghi lý do
  bằng tiếng Việt, không làm dừng các file khác.
- Xuất đồng loạt đọc số liệu **từ file Excel** (ô sửa tay trên giao diện không ghi vào Excel). Phải ghi rõ trong README.
- Phần xử lý (đọc, dựng, ghi, tổng hợp) đặt ở module `batch.py`, không phụ thuộc giao diện, để test tự động được.

### 2.4 Lưu cài đặt
- `settings.json` trong `%APPDATA%/<APP>`: file Excel gần nhất, khung tên, cấu hình khung (cả logo), số liệu, dự án
  (`files`, `i`, `file`), lựa chọn xuất (`export_all`, `batch`), số lượng (`qty` theo đường dẫn tuyệt đối).
- Thêm khoá mới vào `save_settings` trong `on_close`. Đọc khoá cũ phải chịu được thiếu khoá (bản cũ).

---

## 3. Khung tên (frame.py)

- **Khung khác mẫu:** nếu khung có sẵn chữ nhãn "TL:" / "TỜ:" và ô cấu hình đè lên nhãn, thì bỏ nhãn trong khung,
  mỗi tờ ghi lại "TL: 1/xx", "TỜ: i/n" tại chỗ nhãn, cùng kiểu chữ / cỡ chữ (`_auto_labels`). Khung mẫu KT-A3 giữ
  nguyên cách cũ.
- **Chữ giai đoạn** (TKCS, TKBVTC, TKKT…) trong khung thay theo ô Giai đoạn của Excel.
- **Ô tỷ lệ, số tờ kéo dịch được** (đối tượng `s<i>.tl`, `s<i>.to` trong `Ctx`) để chỉnh khi app đặt lệch.
- **Logo:**
  - Khung có ảnh OLE: trích ảnh (DIB → PNG) chèn vào PDF.
  - Khung có chỗ logo OLE **nhưng file DXF mất dữ liệu ảnh** (AutoCAD xuất DXF làm mất): **tự chèn logo SEIAC** kèm
    chương trình (`assets/frames/SEIAC_logo.png`, ô đặt mặc định như khung SEIAC), không cần cấu hình.
  - Người dùng chọn file logo khác trong ⚙ Cấu hình… thì dùng file đó. Chèn vào DXF thành IMAGE, chép file ảnh cạnh
    file DXF, tham chiếu theo tên file.
- **Font chữ khung:** MTEXT gọi font theo họ (`\fRoboto Condensed|b1`, `\fRoboto SemiBold`…) luôn được trỏ về font
  Roboto **tĩnh** kèm chương trình (vá `font_manager.find_best_match` và `find_font_name` trong `cad.init_fonts`).
  Font Roboto bản variable cài trên máy làm chữ PDF bị chấm trắng.

---

## 4. Đầu ra

### 4.1 PDF
- **Chữ thật** (chọn, tìm, sửa được), font Roboto nhúng vào file. Chặn `pipeline.draw_text` của ezdxf để lấy
  dòng chữ đã dàn trang, ghi bằng `page.insert_text` của PyMuPDF:
  - cỡ chữ khớp bề rộng dòng;
  - ma trận `morph` tính theo hệ toạ độ PDF gốc (y lên);
  - chuẩn hoá chữ về NFC (khung tên có chữ dấu rời);
  - font nét SHX vẫn vẽ nét như cũ.
- Kiểm tra chồng hình với bản vẽ nét: lệch < 0,1 mm ở mọi góc xoay. File nhỏ khoảng 2,5 lần.

### 4.2 DXF
- Các tờ đặt cạnh nhau theo X. **Mặt bằng 1:1 đơn vị mét** đặt ngoài các tờ (bên trái tờ 1), không in ra PDF
  (`plan11.py`):
  - **Hình:** kích thước thật (không rút ngắn khoảng tim như tờ in), gốc toạ độ tại tim móng.
  - **Ghi chú:** chỉ trục qua tim móng; hướng tuyến / phân giác như tờ in (mục 4.6); chữ cao 0,2 m (in 1:100 ra
    2 mm); kích thước ghi mm (DIMLFAC 1000).
  - **Đường bao đền bù:** nét đứt cách mép bê tông móng 0,5 m, ghi kích thước × diện tích (cùng công thức với
    Excel khối lượng).
  - **Dưới hình:** tên cột, tên móng.
  - **Quy ước cho phần mềm nhận** (phải giữ đúng):

    | Đối tượng | Trong DXF |
    |---|---|
    | Chân móng | block `BLN` tại tim cụm bu lông neo từng chân (4 block) |
    | Tim trụ (tim móng) | block `TIM TRU`, gốc (0,0), hình bên trong (POINT, vòng tròn) ở toạ độ thật, chèn tại 0,0 |
    | Bản đế | polyline kín layer `MAIN` (ô vuông lớn nhất quanh mỗi chân) |
    | Bê tông lót | polyline kín layer `THIN` |
    | Mã cột | chữ layer `COT`, nguyên mã |
    | Tên móng | chữ layer `MONG` |
    | Tên vị trí | không ghi `VI TRI` (phần mềm nhận lấy tên file DXF) |
    | Số trụ từng chân | chữ `M1`…`M4` layer `TEN TRU` (tạo nếu chưa có), cao như chữ `COT`, góc 0, đặt **trong ô bản đế của đúng chân** (giữa dải vát phía ngoài, không đè `BLN`) |

  - **Số trụ trong DXF phải trùng IFC xuất cùng lúc:** chữ `Mk` ↔ khối IfcFooting tên "Móng trụ k - <loại>", tag
    `Mk`. Quy ước vị trí (một nguồn `lech.model.QUAD`, dùng chung cho DXF, IFC, móng 2 loại): trụ 1 (−X, +Y), trụ 2
    (+X, +Y), trụ 3 (−X, −Y), trụ 4 (+X, −Y). Móng chân lệch (vd `MT65.0 3T35-35/1T35-45`, trụ 2 là T35-45): `M2` nằm
    ở chân có móng T35-45. Đổi chân lệch (ô Vị trí trụ) thì DXF và IFC đổi cùng lúc vì cùng đọc một số liệu.
  - Chữ nằm cùng hình móng: copy, xoay mặt bằng vào bình đồ thì chữ đi theo chân (không lật gương). App san gạt đọc
    chữ `Mk` để đặt đúng khối IFC vào chân.

### 4.3 Excel khối lượng
- **Phá đá** (ô C25, 0 / trống = không có đá): phần dưới cùng của hố dày t phá đá thành đứng, riêng từng trụ `n·(Bm + 2·mp)²·t`; phần trên `Hm + 0.1 − t` đào đất mở mái từ mặt đá, xét đào chung / riêng theo phần đất; đắp hoàn trả cả phần đá (đá phá tận dụng để đắp). Chỉ thêm dòng / cột Phá đá khi t > 0 (file cũ giữ nguyên). Bản vẽ không đổi. Móng 2 loại: chưa tính.
- Như HUONG_DAN_PHAT_TRIEN mục 4. Khối lượng thép trong bảng tổng kê đã gồm dự phòng. Dự phòng = 0 thì không ghi chú.

### 4.4 IFC (BIM) - `ifc.py`
- Tự ghi IFC4 (định dạng STEP, Reference View), **không cần thư viện IFC** (exe không nặng thêm). Đơn vị mm.
  Cao độ: mặt đất tự nhiên = 0.
- **Phần tử:**
  - IfcFooting (PAD_FOOTING) cho phần bê tông móng; IfcSlab (BASESLAB) cho bê tông lót. Đều là IfcPolygonalFaceSet.
  - IfcReinforcingBar gom theo cấu kiện + loại thép + Ø: IfcSweptDiskSolid chạy theo đường tim đã bo cung. Vòng
    kín (đai, đai ốc) chừa chỗ nối 1Ø, nếu không bộ dựng hình không quét được.
  - IfcMechanicalFastener (ANCHORBOLT) cho bu lông neo, gộp thân + đai ốc **1 phần tử** (tránh trùng GlobalId).
  - IfcGrid cho trục.
- **Thuộc tính:** vật liệu, màu, lớp (S-FOOTING, S-REBAR, S-GRID); thể tích (Qto); số thanh, tổng dài, khối lượng thép.
- **GlobalId** cố định theo tên (uuid5), xuất lại không đổi. OwnerHistory dùng `.NOCHANGE.`.
- **Kiểm tra:** cài ifcopenshell (+ pytest) vào thư mục tạm, không đưa vào app. Chạy `ifcopenshell.validate`
  (gồm luật EXPRESS) phải ra 0 lỗi, và `geom.create_shape` dựng được mọi phần tử.

### 4.5 Khối lượng tổng hợp phần móng (dự án) - `batch.write_summary`
- Theo mẫu "KHỐI LƯỢNG PHẦN MÓNG (TÍNH CHO 01 MÓNG)", mỗi dòng 1 file Excel móng. Các cột:
  - tên cột, tên móng, số lượng (SL);
  - bê tông theo từng mác, thép từng Ø (cột tự động theo các Ø có trong dự án), tổng thép;
  - bu lông neo, đào, đắp, ván khuôn;
  - chiều sâu chôn móng, dài / rộng / diện tích đền bù.
- Số liệu 01 móng lấy đúng **bảng tổng kê tờ 1** (test tự động so sánh). Dòng **TỔNG** là công thức
  `SUMPRODUCT(SL, cột)`. Cột xếp liền nhau, không có cột ẩn.

### 4.6 Hình thức cột và hướng tuyến (mặt bằng tờ 1 + mặt bằng 1:1)
| Hình thức | Ô B4 (Excel) | Tên trên bản vẽ | Hướng tuyến | Phân giác |
|---|---|---|---|---|
| Đỡ | ĐỠ | ĐỠ | 2 chiều thẳng theo Y | không |
| Néo góc | NÉO GÓC | NÉO GÓC | 2 tia lệch 10° | có, sang trái |
| Néo dừng | NÉO DỪNG | NÉO DỪNG | 1 chiều | không |
| Néo thẳng | NÉO THẲNG | NÉO THẲNG | 2 chiều thẳng | có, sang trái |
| Néo hãm | NÉO HÃM | NÉO HÃM | như néo góc | có |
| Néo góc 90° | NÉO GÓC 90 | **NÉO GÓC** | lên (+Y) và sang trái (−X) | không |

- Loại mới thêm vào **cuối** danh sách (giữ số thứ tự cũ).
- Ghi chú "TIM MÓNG" có đường dẫn. Khi mũi tên chạy sang trái (néo góc, néo thẳng, néo hãm, néo góc 90°) thì ghi
  phía dưới bên phải.

### 4.7 Mô hình 3D
- Bê tông trong suốt; bê tông lót là khối dày 100 mm; nét trục tim cột (gạch chấm).
- **Thép bo cung tại chỗ uốn** (theo mô hình Revit tham khảo), bán kính tới tim thanh: Ø ≤ 10 là 1,5d; Ø ≤ 16 là 2,5d;
  lớn hơn là 3,5d (`view3d.fillet`, `bend_r`).
- `Scene` lưu thêm `bars` (đường tim từng thanh), `solids` (khối bê tông kín), `axes` để xuất IFC.

---

## 5. Kỹ thuật kiểm tra

### 5.1 Ảnh xem trước
- `tools/render_preview.py` hoặc `export.pdf_bytes` → PyMuPDF `get_pixmap(dpi=300, clip=...)`.
- Kiểm chồng chữ, nét thừa, khoảng cách tag: thử móng mẫu + móng lớn / nhỏ / bất thường.

### 5.2 So hai cách vẽ
- Ghép 2 ảnh: kênh đỏ = bản cũ, kênh xanh = bản mới. Viền màu là chỗ lệch.
- Muốn đo lệch thì tìm khung bao điểm ảnh tối ở 600-1200 dpi.

### 5.3 Đọc lại file đầu ra
- DXF: đọc lại bằng ezdxf, kiểm block, layer, chữ đúng như phần mềm nhận sẽ đọc.
- Excel: LibreOffice `--convert-to` để tính công thức.
- IFC: ifcopenshell (mục 4.4).

---

## 6. Thử giao diện thật trên máy cloud
- Venv Python 3.12 có Tkinter (`python3-tk`, `--system-site-packages`, cài lại Pillow), chạy dưới
  `xvfb-run -a -s "-screen 0 1600x1000x24"`.
- Script thử dùng hàm `run(steps)`:
  - `steps(app)` là generator, `yield "idle"` để chờ dựng xong, `yield <giây>` để chờ;
  - các bước chạy trong `mainloop`;
  - chụp ảnh bằng `PIL.ImageGrab`.
- Thay hộp thoại bằng hàm giả (`filedialog.askopenfilenames = lambda **k: [...]`, `messagebox.showinfo = ...`).
- Gửi phím vào ô nhập: phải `focus_force()` + `update()` trước `event_generate("<Return>")`. Không làm vậy thì phím
  không tới ô (lỗi của test, không phải của app).

---

## 7. Lỗi đã gặp - tránh lặp lại
- **Sửa nửa vời:** đã "sửa" logo bằng một tuỳ chọn phải bấm tay, người dùng tưởng đã xong. Lỗi do dữ liệu đầu vào
  (khung mất ảnh) thì phải **tự xử lý mặc định**, tuỳ chọn chỉ để thay đổi.
- **Đổi quy tắc hình vẽ phải đổi cả khối lượng:** dời thanh chống trên hình làm L1 trong bảng sai. Vị trí thanh phải
  tính trong `geom` (một nguồn) để hình, bảng, Excel, 3D cùng dùng.
- **Đối xứng:** quy tắc dời / bám thép phải tính theo |x| rồi lấy dấu, dùng như nhau cho x và y. Nếu không, bản vẽ
  lệch và bảng thép thừa loại chiều dài.
- **Sắp xếp tên file:** sắp chuỗi thường cho ra 1, 10, 2…. Phải dùng số tự nhiên.
- **Tách nhãn và giá trị** khi phần mềm khác cần đọc nguyên giá trị (mã cột trên layer COT).
- Có 2 phiên Claude cùng đẩy vào một nhánh: luôn `git fetch` + `rebase` trước khi đẩy.

---

## 8. Áp dụng cho Móng bản không sườn (VE_MONGBANKOSUON)

Móng bản không sườn có dạng **hình nấm** giống móng trụ: bản đế có mặt vát, cổ móng, thép lớp trên uốn theo mặt
vát, thanh chống. Khác ở chỗ **4 trụ quá gần nhau nên gộp thành 1 bản móng có 4 cổ móng**. Cách trình bày bản vẽ và
đầu ra tương tự móng trụ.

### 8.1 Dùng lại nguyên từ VE_MONGTRU
- **Hạ tầng:**
  - `cad.py` (gồm vá font Roboto);
  - `frame.py` (nhãn TL / TỜ, logo tự động, ô TL / TỜ kéo được);
  - `export.pdf_bytes` (chữ thật), `export.save_dxf` (chép logo);
  - `view.py`, `ui3d.py`, `view3d.render`.
- **Chức năng chung:**
  - `batch.py`: thư mục / dự án, file dự án, khối lượng tổng hợp, natural sort;
  - giao diện: menu Dự án, thanh DỰ ÁN, `BatchDialog`, menu Xuất file, `Tip`, bảng màu navy, `__version__`;
  - `plan11.py` theo quy ước phần mềm nhận (đổi phần hình);
  - `ifc.py` (đổi cách gom phần tử).
- **Hình thức cột và hướng tuyến:** bảng mục 4.6, hàm `draw_route`.
- **Kiểm thử:** `regression.py` (golden mới của app móng bản), các `smoke_*.py`, `check_kl_excel.py`, CI.

### 8.2 Dùng lại có chỉnh (phần giống móng trụ)
- **Bê tông** hình nấm: mặt vát + gờ quanh cổ. Thép lớp trên uốn theo mặt vát, móc 2 đầu (`hook_top`), Ltb + bảng
  kích thước từng thanh. Thanh chống có thân theo chiều cao tại vị trí thanh, bám thép chấm khi xoay (`chair_snap`),
  đối xứng.
- **Cổ móng:** thép chủ neo chân 500, đai / đai phụ / đai bát giác, lưới đầu trụ, bu lông neo theo bảng `BOLT_TABLE`
  (h, t).
- **Tờ thép:** bố trí thép trụ, thép bản đế (nửa lớp trên / nửa lớp dưới), mặt cắt cổ, lưới đầu trụ, bảng thống kê,
  tỷ lệ từng hình.

### 8.3 Phải viết mới / cần hỏi người dùng (chưa có số liệu)
- **Hình học bản chung:** 1 bản B × L chứa 4 cổ móng.
  - Mặt vát chạy quanh **cụm 4 cổ** hay quanh **từng cổ**, phần giữa 4 cổ phẳng hay vát → cần Excel mẫu và bản vẽ PDF
    mẫu.
  - Thép lớp trên giữa các cổ có thêm thép mũ / thép tăng cường không.
- **Khối lượng:** bê tông, đất, ván khuôn theo sheet `KL be tong` của Excel mẫu móng bản không sườn.
- **Mặt bằng 1:1:** 4 block `BLN` vẫn đặt tại tim cụm bu lông từng cổ; chữ `M1`…`M4` (layer `TEN TRU`) theo cổ, trùng
  khối IFC. Bản móng chung là **1** polyline `MAIN` bao cả
  4 chân: phải xác nhận phần mềm nhận chấp nhận 1 ô chung cho cả 4 chân. Đường bao đền bù B + 1 × L + 1.
- **IFC:** 1 IfcFooting cho cả bản + 4 cổ (hay bản và cổ tách riêng) → hỏi người dùng.
- **Khối lượng tổng hợp:** cột chiều sâu chôn móng, dài / rộng đền bù lấy theo bản chung.
- **Đuôi file dự án** của app móng bản (ví dụ `*.mongban`) → hỏi người dùng.
- **Excel đầu vào:** bản đồ ô sheet `TONG HOP` của móng bản (ô B4 hình thức cột, J7 + K7 mã số bản vẽ… như móng trụ
  nếu cùng mẫu).
