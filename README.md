# VE_MONGTRU

App Windows chạy offline, vẽ nhanh bản vẽ **móng trụ rời 4 trụ** (móng cột đường dây) từ file Excel. Kiến trúc và cách dùng giống app VE_MONGBANCOSUON / VE_MONGBANKOSUON.

## Chức năng
- **Đọc Excel:** lấy số liệu từ sheet `TONG HOP` (các ô liệt kê bên dưới). Đọc được cả `.xls` và `.xlsx` / `.xlsm`.
- **Hiệu chỉnh:** sửa mọi thông số trên giao diện. App kiểm tra số liệu và cập nhật khối lượng ngay.
- **Khung tên:** mặc định dùng `assets/frames/KT-A3.dxf` (block KHUNG_TEN). App điền attribute nếu có, nếu không thì điền theo toạ độ. Logo OLE được chèn vào PDF.
- **Bản vẽ:**
  - TKCS có 1 tờ: mặt cắt A-A (qua 2 trụ, hố đào, cao độ), mặt bằng móng 4 trụ, bảng tổng kê.
  - TKBVTC có 2 tờ.
    - Tờ 1/2: như TKCS.
    - Tờ 2/2: bố trí thép trụ, thép bản đế (nửa trái lớp trên, nửa phải lớp dưới), mặt cắt cổ móng 1-1, lưới thép đầu trụ, bảng thống kê cốt thép, bảng kích thước từng thanh (thép lớp trên, thanh chống).
  - Khoảng cách tim trụ lớn không vừa khổ giấy: tờ 1 thu gọn khoảng cách giữa các trụ trên hình, chữ kích thước vẫn ghi giá trị thật. Tự chọn tỷ lệ không nhỏ hơn 1/100 trước khi thu gọn.
- **Xuất file:** PDF A3, AutoCAD DXF, Excel khối lượng (`_KL.xlsx`, gồm các sheet TONG KE, THONG SO, KHOI LUONG). Tên file xuất trùng tên file Excel. Trong Excel, Ø, chiều dài và số lượng từng vị trí thép đều là công thức theo thông số (sheet THONG SO), có diễn giải: sửa thông số thì khối lượng tự tính lại.
- **Mô hình 3D:** tab riêng, bê tông trong suốt, bật/tắt từng nhóm thép, xem toàn móng hoặc 1 trụ.
- **Sắp xếp (kéo thả):** vị trí lưu vào `<tên Excel>.layout.json`.

## Ô đọc từ sheet TONG HOP
| Ô | Thông số | Ô | Thông số |
|---|---|---|---|
| B4 | Hình thức cột (ĐỠ / NÉO / NÉO DỪNG) | C4, C5, C6 | Tên cột, tên móng, giai đoạn |
| J4, J5 | Bê tông móng, bê tông lót | J6 | Mã bản vẽ ghi chú chung |
| B9 | Bm = Lm: cạnh bản đế | B10, B11 | Hm: chôn sâu, d: cao trên mặt đất |
| B12 | Bt: khoảng cách tim trụ | B13, B14 | b1, b2: cạnh cổ móng ở đỉnh / chân (hiện phải bằng nhau) |
| B15, B16 | hb: cao bản đế tại gờ cổ móng, hv: cao ở mép | C18, C19 | Hệ số mở mái, mở rộng đáy hố đào |
| C20 + D20 | Bu lông neo (vd `BLN-` `M36-250`: M36, cụm cách nhau 250) | C22, C23 | Lớp bảo vệ đáy / còn lại (mm) |
| C24 | Số trụ móng (bội số của 4) | H29 | Dự phòng thép (%) |
| H21 / I21, H22 / I22 | Thép bản đế lớp dưới, lớp trên: Ø / bước | H23 / I23 | Thanh chống: Ø / bước |
| H25 / I25 | Thép chủ cổ móng: Ø / tổng số thanh | H26..I28, K28 | Đai, đai phụ, lưới đầu trụ, số lớp lưới |

## Quy tắc tính
- **Bê tông, lót, đào, đắp, ván khuôn:** theo công thức sheet `KL` của Excel mẫu (cho cả móng = số trụ × 1 trụ).
  - Gờ phẳng quanh chân cổ móng 100, lót dày 100 tràn ra 100 mỗi bên.
  - Hố đào: nếu miệng các hố riêng chạm nhau thì đào chung 1 hố cho 4 trụ, ngược lại đào riêng từng trụ. Mái hố vẽ 1:0,5; hệ số mái trong Excel chỉ dùng tính khối lượng.
  - Đền bù: cạnh Bt + Bm + 1.
- **Thép:** tính và trình bày như app móng bản không dầm: khối lượng tính từ đúng các thanh vẽ ra.
  - Thép bản đế 2 lớp, rải riêng vùng gờ cổ móng và vùng vát. Lớp trên uốn theo mặt vát, 2 đầu móc xuống (làm tròn lên 100). Bảng thống kê ghi chiều dài trung bình (không ghi chữ Ltb), kèm bảng kích thước từng thanh.
  - Thanh chống: lưới theo bước (cả phần dưới cổ móng), chân 100, thân cao theo mặt vát; vị trí sát hàng thép chủ cổ móng được dời vào trong / ra ngoài để tránh thép chủ.
  - Thép chủ cổ móng: neo chân 500 (như app móng bản có dầm).
  - Đai cổ móng: 2 đai (bằng số lớp lưới) đỡ các lớp lưới thép đầu trụ, còn lại theo bước đai.
  - Đai phụ, đai bát giác: theo quy tắc app cũ (giữ các thanh cách nhau ≤ 400).
  - Bảng tổng kê và Excel khối lượng cộng thêm dự phòng thép (ô H29), không ghi chú trên bản vẽ. Bảng thống kê cốt thép không cộng dự phòng.

## Tải file .exe
Vào tab **Actions** của repo, mở lần build mới nhất và tải mục **VE_MONGTRU-exe** ở phần *Artifacts*.

## Chạy từ mã nguồn
```
pip install -r requirements.txt
python app.py
```

## Công cụ
- `python tools/render_preview.py [file.xls] [KEY=VAL ...] --out thư_mục`: render ảnh xem trước.
- `python tests/smoke.py`: kiểm tra nhanh (đọc Excel mẫu, so khối lượng, dựng PDF/DXF/Excel).
- `python tools/check_kl_excel.py`: đối chiếu công thức Excel khối lượng với chương trình qua LibreOffice (phải ra 0 lỗi).
- Kiến trúc chung: xem [docs/HUONG_DAN_PHAT_TRIEN.md](docs/HUONG_DAN_PHAT_TRIEN.md) (viết cho app móng bản có dầm; package ở app này tên `mongtru`).
