# VE_MONGTRU

App Windows chạy offline, vẽ nhanh bản vẽ **móng trụ rời 4 trụ** (móng cột đường dây) từ file Excel. Kiến trúc và cách dùng giống app VE_MONGBANCOSUON / VE_MONGBANKOSUON.

## Chức năng
- **Đọc Excel:** lấy số liệu từ sheet `TONG HOP` (các ô liệt kê bên dưới). Đọc được cả `.xls` và `.xlsx` / `.xlsm`. Mỗi lần mở file, mọi thông số và lựa chọn (kể cả trình bày hố đào) về mặc định rồi mới đọc file (ô trống không giữ số của file trước, có cảnh báo). Tỷ lệ tờ 1 luôn tự chọn lại.
- **Hiệu chỉnh:** sửa mọi thông số trên giao diện. App kiểm tra số liệu và cập nhật khối lượng; khi đang gõ, thông báo lỗi chờ khoảng 1,2 s sau lần gõ cuối mới hiện.
- **Khung tên:** mặc định dùng `assets/frames/KT-A3.dxf` (block KHUNG_TEN). App điền attribute nếu có, nếu không thì điền theo toạ độ. Logo OLE được chèn vào PDF.
- **Bản vẽ:**
  - TKCS có 1 tờ: mặt cắt A-A (qua 2 trụ, hố đào, cao độ), mặt bằng móng 4 trụ, bảng tổng kê.
  - TKBVTC và TKKT có 2 tờ.
    - Tờ 1/2: như TKCS.
    - Tờ 2/2: bố trí thép trụ, thép bản đế (nửa trái lớp trên, nửa phải lớp dưới), mặt cắt cổ móng 1-1, lưới thép đầu trụ, bảng thống kê cốt thép, bảng kích thước từng thanh (thép lớp trên, thanh chống; cổ móng vát thêm thép chủ cổ, đai, đai bát giác, đai phụ).
    - Bảng kích thước từng thanh không đủ chỗ ở khoảng giữa tờ 2 (thường gặp khi cổ móng vát): nếu tờ 1 còn chỗ dưới bảng tổng kê thì đưa bảng thống kê cốt thép sang tờ 1 (tờ 2 ghi chú "BẢNG THỐNG KÊ CỐT THÉP XEM TỜ 1/2"), các bảng kích thước xếp vào khoảng giữa và cột phải tờ 2. Vẫn không đủ thì mới chuyển hết bảng kích thước sang tờ 3/3 (tờ 2 ghi chú "BẢNG KÍCH THƯỚC TỪNG THANH XEM TỜ 3/3").
    - TKKT: chỉ 2 tờ, tờ 2/2 không có bảng thống kê cốt thép và bảng kích thước từng thanh, tag thép không ghi số hiệu (giữ Ø/@ và tên thép). Excel khối lượng xuất bình thường.
  - Tỷ lệ tờ 1 tự chọn: tỷ lệ lớn nhất trong danh sách (1/50 … 1/250) vẽ được đúng tỷ lệ. Chỉ khi 1/250 vẫn không đủ chỗ (hoặc người dùng chọn tỷ lệ lớn hơn mức vừa khổ giấy) thì thu gọn khoảng cách giữa các trụ trên hình, chữ kích thước vẫn ghi giá trị thật.
  - Trình bày hố đào (ô dưới "Mở rộng đáy hố đào"): Tự động / Đào chung 1 hố / Đào riêng từng trụ. Chỉ đổi hình vẽ (mái tượng trưng 1:0,5), không đổi khối lượng.
- **Xuất file:** PDF A3, AutoCAD DXF, Excel khối lượng (`_KL.xlsx`, gồm các sheet TONG KE, THONG SO, KHOI LUONG). Tên file xuất trùng tên file Excel. Trong Excel, Ø, chiều dài và số lượng từng vị trí thép đều là công thức theo thông số (sheet THONG SO), có diễn giải: sửa thông số thì khối lượng tự tính lại.
- **Mô hình 3D:** tab riêng, bê tông trong suốt, bật/tắt từng nhóm thép, xem toàn móng hoặc 1 trụ.
- **Sắp xếp (kéo thả):** nhấp chọn rồi kéo, hoặc dùng phím mũi tên (1 mm, giữ Shift: 5 mm). Ctrl+Z / Ctrl+Y hoàn tác / làm lại. Vị trí lưu vào `<tên Excel>.layout.json`.

## Ô đọc từ sheet TONG HOP
| Ô | Thông số | Ô | Thông số |
|---|---|---|---|
| B4 | Hình thức cột (ĐỠ / NÉO GÓC / NÉO DỪNG) | C4, C5, C6 | Tên cột, tên móng, giai đoạn |
| J4, J5 | Bê tông móng, bê tông lót | J6 | Mã bản vẽ ghi chú chung |
| J7 + K7 | Mã số bản vẽ ghi khung tên (vd `2511TNC2.F.NM.C.` + `201`) | | |
| B9 | Bm = Lm: cạnh bản đế | B10, B11 | Hm: chôn sâu, d: cao trên mặt đất |
| B12 | Bt: khoảng cách tim trụ | B13, B14 | b1, b2: cạnh cổ móng ở đỉnh / chân (b1 ≤ b2) |
| B15, B16 | hb: cao bản đế tại gờ cổ móng, hv: cao ở mép | C18, C19 | Hệ số mở mái, mở rộng đáy hố đào |
| C20 + D20 | Bu lông neo (vd `BLN-` `M36-250`: M36, cụm cách nhau 250) | C22, C23 | Lớp bảo vệ đáy / còn lại (mm) |
| C24 | Số trụ móng (bội số của 4) | H29 | Dự phòng thép (%) |
| H21 / I21, H22 / I22 | Thép bản đế lớp dưới, lớp trên: Ø / bước | H23 / I23 | Thanh chống: Ø / bước |
| H25 / I25 | Thép chủ cổ móng: Ø / tổng số thanh | H26..I28, K28 | Đai, đai phụ, lưới đầu trụ, số lớp lưới |

## Quy tắc tính
- **Bê tông, lót, đào, đắp, ván khuôn:** theo công thức sheet `KL` của Excel mẫu (cho cả móng = số trụ × 1 trụ).
  - Gờ phẳng quanh chân cổ móng 100, lót dày 100 tràn ra 100 mỗi bên.
  - Hố đào (tính khối lượng): nếu miệng các hố riêng chạm nhau (theo hệ số mái C18) thì đào chung 1 hố cho 4 trụ, ngược lại đào riêng từng trụ. Không phụ thuộc lựa chọn trình bày hố đào trên hình. Mái hố vẽ 1:0,5.
  - Đền bù: cạnh Bt + (b2 − b1) + Bm + 1.
- **Cổ móng vát (b1 < b2):**
  - 2 mặt phía trong (hướng về tim móng) thẳng đứng, 2 mặt phía ngoài vát. Bt là khoảng cách tim đỉnh cổ móng (tim chân cột, cụm bu lông); tim các bản đế cách nhau Bt + (b2 − b1).
  - Ván khuôn cổ móng tính theo diện tích vát thật: 2 mặt đứng + 2 mặt vát (chiều cao xiên).
  - Mặt cắt 1-1 cắt sát đỉnh cổ móng: tiết diện thể hiện và ghi kích thước b1; thấy thêm đường bao chân cổ b2.
  - Thép chủ cổ móng chạy theo mặt vát, đai / đai bát giác / đai phụ thu nhỏ theo cao độ. Thép có chiều dài thay đổi ghi chiều dài trung bình trong bảng thống kê, kèm bảng kích thước từng thanh. Excel khối lượng tính các chiều dài này bằng công thức theo thông số.
- **Thép:** tính và trình bày như app móng bản không dầm: khối lượng tính từ đúng các thanh vẽ ra.
  - Thép bản đế 2 lớp, rải riêng vùng gờ cổ móng và vùng vát. Lớp trên uốn theo mặt vát, 2 đầu móc xuống: dài hv − cv − cvb − (Ø dưới + Ø trên), làm tròn xuống tới 5 mm (vd 187 → 185, 182 → 180). Bảng thống kê ghi chiều dài trung bình (không ghi chữ Ltb), kèm bảng kích thước từng thanh.
  - Thanh chống: lưới theo bước (cả phần dưới cổ móng), chân 100; thân = chiều cao bản đế tại vị trí thanh − 2 lớp bảo vệ (cv + cvb) − 2Ø (Ø lớp dưới + Ø lớp trên); vị trí sát hàng thép chủ cổ móng được dời vào trong / ra ngoài để tránh thép chủ.
  - Thép chủ cổ móng: neo chân 500 (như app móng bản có dầm), đoạn neo tựa trên cả 2 phương thép lớp dưới (tim đoạn neo cao cvb + 2Ø lớp dưới + Ø chủ/2).
  - Đai cổ móng: 2 đai (bằng số lớp lưới) đỡ các lớp lưới thép đầu trụ, còn lại theo bước đai.
  - Đai phụ, đai bát giác: theo quy tắc app cũ (giữ các thanh cách nhau ≤ 400).
  - Số thanh 1 cạnh chẵn (không có thanh nằm giữa trục): nếu theo quy tắc trên không cần giữ cặp thanh giữa thì không thêm đai; nếu cần thì cổ vát dùng mỗi phương 1 đai thẳng đặt xiên nối 2 thanh giữa của 2 cạnh đối diện (lệch 1 bước thanh) - đai xiên dài khác đai phụ nên có số hiệu riêng; cổ thẳng dùng đai bát giác.
  - Leader chú thích không chạy trùng nét thép (vd nhánh đứng của tag đai phụ đặt giữa 2 thanh chủ).
  - Tag thép bản đế trên hình bố trí thép trụ: 1 nhánh chỉ chấm tròn, 1 nhánh chỉ thanh nằm ngang, 2 nhánh cách nhau ≥ 1 bước rải.
  - Bảng tổng kê và Excel khối lượng cộng thêm dự phòng thép (ô H29), không ghi chú trên bản vẽ. Bảng thống kê cốt thép không cộng dự phòng.
  - Excel: mục phân loại theo đường kính liệt kê đủ các Ø trong bảng tra. Đổi Ø ở THONG SO sang đường kính không có cột ở sheet TONG KE thì TONG KE hiện "Có đường kính mới - xuất lại file".

## Móng 2 loại (4 trụ có 2 loại móng khác nhau)
Mở file Excel có 2 khối "Móng:" ở sheet `TONG HOP` (mẫu `samples/N112-52(60) - 3T-1T.xls`) thì app tự chuyển sang chế độ 2 loại: 3 trụ giống nhau + 1 trụ khác, hoặc 2 + 2 song song. Mã nguồn tách riêng ở `mongtru/lech/`, dùng lại phần tính / vẽ 1 trụ của bản 4 trụ giống nhau (bản này đã khóa định dạng, xem [docs/KHOA_DINH_DANG.md](docs/KHOA_DINH_DANG.md)).
- **Ô đọc:** khối loại 1 như hình mẫu trong Excel (B8 tên móng, B10..B17 kích thước, C21/D21 bu lông, C23/C24 lớp bảo vệ, H22..I29 thép, K29 số lớp lưới, B26.. vị trí trụ, C27 cao độ thiết kế); khối loại 2 cùng cột, lùi xuống 22 dòng (B30 ...). Dùng chung: B4, C4, C5, C6, J4..J7, K7, hệ số mở mái C19, mở rộng đáy hố C20, dự phòng thép H52. Ô của loại 2 trống / lỗi thì lấy theo loại 1 (có cảnh báo).
- **Vị trí trụ:** 1 trái trên, 2 phải trên, 3 trái dưới, 4 phải dưới (như hình trong Excel). Bt là khoảng cách tim đỉnh trụ; tim bản đế mỗi loại lệch theo b2 − b1 của loại đó.
- **Cao độ:** cao độ thiết kế = mặt đất tại trụ; đỉnh cổ móng = cao độ thiết kế + d; đáy bản đế = cao độ thiết kế − Hm.
- **Giao diện:** thêm ô "Loại móng đang sửa" (các ô kích thước, thép, bu lông hiện số liệu của loại đang chọn), "Vị trí trụ" (loại kia tự nhận các vị trí còn lại), "Cao độ thiết kế".
- **Bản vẽ:**
  - Tờ 1: mặt cắt A-A qua 2 trụ khác loại (cùng hàng; nếu 2 hàng đều cùng loại thì cắt theo cột), mỗi trụ theo cao độ riêng: mặt đất 2 mức nối bằng mái 1:1 qua trục tim móng, kích thước và cao độ trụ trái ở bên trái, trụ phải ở bên phải. Mặt bằng ghi tên loại trong từng bản đế, kích thước cổ móng trên 1 trụ mỗi loại. Bảng tổng kê cho cả vị trí móng (bu lông gộp theo đường kính).
  - TKBVTC / TKKT: mỗi loại 1 tờ cốt thép (vẽ như tờ 2 bản 4 trụ giống nhau, số lượng thép theo số trụ của loại). Bảng kích thước từng thanh không đủ chỗ thì thêm tờ ngay sau tờ thép của loại đó (không đưa bảng thống kê thép sang tờ 1).
- **Khối lượng:** bê tông, lót, ván khuôn, thép = cộng 2 loại. Đào: mỗi trụ hố từ đáy lót lên mặt đất tại trụ đó; miệng hố 2 trụ cạnh nhau chạm nhau thì đào chung 1 hố, đáy bậc theo độ sâu từng trụ (tính theo lát cắt: tại mỗi cao độ, hố chung là hình chữ nhật bao các hố riêng có ở cao độ đó). Đắp = đào − lót − phần bê tông dưới mặt đất. Đền bù: Bt + max(b2 − b1 + Bm) + 1.
- **Excel khối lượng:** sheet THONG SO 1 / KHOI LUONG 1 (loại 1), THONG SO 2 / KHOI LUONG 2 (loại 2) như file của bản 4 trụ giống nhau; sheet DAT (đào / đắp cả vị trí: công thức khi đào riêng, giá trị do chương trình tính khi đào chung đáy bậc - sửa thông số thì xuất lại); sheet TONG KE cho cả vị trí móng.
- **3D:** 4 trụ đúng loại và cao độ.

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
- `python tests/smoke_lech.py`, `python tools/check_kl_lech.py`: kiểm tra móng 2 loại (Excel khối lượng phải ra 0 lỗi).
- `python tests/regression.py`: khóa định dạng bản 1.0.0 (phải ra 0 chỗ khác mẫu) - xem [docs/KHOA_DINH_DANG.md](docs/KHOA_DINH_DANG.md).
- Kiến trúc chung: xem [docs/HUONG_DAN_PHAT_TRIEN.md](docs/HUONG_DAN_PHAT_TRIEN.md) (viết cho app móng bản có dầm; package ở app này tên `mongtru`).
