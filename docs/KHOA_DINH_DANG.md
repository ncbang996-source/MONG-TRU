# Khóa định dạng bản 1.0.0 (4 trụ giống nhau)

Bản móng trụ 4 trụ giống nhau đã ổn định và được lưu ở tag git `v1.0.0` (lấy lại đúng mã nguồn lúc đó:
`git checkout v1.0.0`).

## Quy tắc khi phát triển phần mới
- Phần mới (vd móng 4 trụ có 2 loại kích thước) viết ở package / thư mục riêng, **không sửa** các file của bản
  1.0.0 (`mongtru/*.py`, `app.py`) trừ khi người dùng đã xác nhận.
- Phần mới được phép *gọi lại* (import) hàm của bản cũ. Nếu cần sửa hàm dùng chung thì phải giữ nguyên kết quả của
  bản cũ, và báo người dùng trước.
- Trước mỗi lần commit chạy `python tests/regression.py`: so dấu vân tay từng tờ bản vẽ (mọi nét, chữ, kích thước),
  bảng thép, khối lượng và công thức Excel của 12 trường hợp mẫu với `tests/golden.json`. Phải ra 0 chỗ khác.
- Chỉ chạy `python tests/regression.py --update` (ghi lại mẫu) khi người dùng đã đồng ý thay đổi định dạng cũ.
- Số phiên bản (`APP_VER`, `version_info.txt`) chỉ đổi khi người dùng yêu cầu.
