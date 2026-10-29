# Việc chờ làm (gộp vào đợt sửa cổ móng vát)

Người dùng yêu cầu ghi lại, chờ gửi mẫu cổ móng vát (b1 ≠ b2) rồi làm cùng 1 lần.

## 1. Hướng phân giác quá ngắn (mặt bằng móng, tờ 1, cột NÉO - HT = 1)
- Hiện trạng (commit 41dd192): trong `sheet1.draw_plan`, mũi tên phân giác dài `lx = max(8.0, k·(Bt/2 − Bm/2) − 1)`,
  tức chỉ bằng khe hở giữa 2 hàng trụ → rất ngắn khi các trụ gần nhau.
- Chữ "HƯỚNG PHÂN GIÁC" đặt ngay cạnh tim móng nên đè lên mũi tên hướng tuyến và chữ / leader "TIM MÓNG"
  (ảnh người dùng gửi: khung đỏ quanh tim móng, móng Bm = 4,0, Bt = 7,5).
- Cần sửa: kéo dài mũi tên phân giác (vượt qua khe hở, có thể chạy qua vùng bản đế như mũi tên hướng tuyến), đặt chữ
  "HƯỚNG PHÂN GIÁC" dọc mũi tên ở chỗ trống, và dời ghi chú "TIM MÓNG" (néo: đang ghi phía dưới trục) để không chồng nhau.

## 2. Cổ móng vát (b1 ≠ b2)
- Chờ bản vẽ mẫu của người dùng. Hiện `model.validate` báo "Chương trình chưa hỗ trợ cổ móng vát (b1 khác b2)".
- Khối lượng bê tông / ván khuôn trong `model.py` và Excel đã tính theo chóp cụt b2 → b1; hình vẽ, thép cổ móng,
  đai, 3D chưa hỗ trợ.
