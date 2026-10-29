# Khóa định dạng bản 1.0.0 (4 trụ giống nhau)

Bản móng trụ 4 trụ giống nhau đã ổn định và được lưu ở nhánh git `ban-on-dinh-1.0.0` (không commit thêm vào
nhánh này; lấy lại đúng mã nguồn lúc đó: `git checkout ban-on-dinh-1.0.0`).

## Quy tắc khi phát triển phần mới
- Phần mới (vd móng 4 trụ có 2 loại kích thước) viết ở package / thư mục riêng, **không sửa** các file của bản
  1.0.0 (`mongtru/*.py`, `app.py`) trừ khi người dùng đã xác nhận.
- Phần mới được phép *gọi lại* (import) hàm của bản cũ. Nếu cần sửa hàm dùng chung thì phải giữ nguyên kết quả của
  bản cũ, và báo người dùng trước.
- Trước mỗi lần commit chạy `python tests/regression.py`: so dấu vân tay từng tờ bản vẽ (mọi nét, chữ, kích thước),
  bảng thép, khối lượng và công thức Excel của 12 trường hợp mẫu với `tests/golden.json`. Phải ra 0 chỗ khác.
- Chỉ chạy `python tests/regression.py --update` (ghi lại mẫu) khi người dùng đã đồng ý thay đổi định dạng cũ.
- Số phiên bản (`APP_VER`, `version_info.txt`) chỉ đổi khi người dùng yêu cầu.

## Móng 2 loại (`mongtru/lech/`)
- Phát triển theo quy tắc trên: chỉ gọi lại hàm của bản 1.0.0.
- Những chỗ đã thêm vào file của bản 1.0.0 (kết quả bản cũ không đổi, `tests/regression.py` = 0 chỗ khác):
  - `mongtru/sheet2.py`: `table_plan` bỏ qua phương án đưa bảng thống kê thép sang tờ 1 khi `g.no_s1`; ghi chú
    "BẢNG KÍCH THƯỚC TỪNG THANH XEM TỜ ..." lấy số tờ từ `g.tables_ref` (mặc định "3/3").
  - `mongtru/ui3d.py`: thông số có khoá "TYPES" thì dựng mô hình 3D móng 2 loại.
  - `app.py`: nhận dạng file Excel móng 2 loại và các nhánh của chế độ 2 loại (ô loại đang sửa, vị trí trụ, cao độ).
