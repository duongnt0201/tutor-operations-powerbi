# Sanitization

Repo này là bản portfolio của một báo cáo nội bộ. Trước khi public, nội dung đã được xử lý như sau.

## Đã loại bỏ

| Hạng mục | Cách xử lý |
|---|---|
| Dữ liệu (`.pbix`, `cache.abf`) | Không đưa vào repo |
| Kết nối database, câu SQL nguồn | Thay bằng đọc CSV từ tham số `SampleDataPath` |
| Kết nối Google Sheets | Thay bằng CSV |
| Bảng nhúng dữ liệu (Enter data) | Thay bằng CSV |
| Tên thương hiệu, tên sản phẩm | Đổi sang tên trung tính (`Tutor Basic`, `Tutor Pro`...) |
| Tên bảng/cột nội bộ | Đổi sang tên trung tính |
| Logo | Thay bằng logo placeholder |
| ID workspace / item Fabric | Xóa / tạo mới |
| Linguistic schema (Q&A) | Xóa |
| Custom visual bên thứ ba | Không phân phối lại |
| `localSettings.json`, cache | Không đưa vào repo |

## Dữ liệu mẫu

`data/sample/*.csv` được sinh hoàn toàn ngẫu nhiên (seed cố định) bởi `scripts/generate_sample_data.py`:

- Tên gia sư có dạng `Gia sư 001`, số điện thoại có dạng `0900xxxxxx` / `0911xxxxxx`. Không có thông tin nào của người thật.
- Phân phối trạng thái được chọn để report hiển thị hợp lý. Đây **không** phải số liệu thực tế.

## Giữ nguyên

- Cấu trúc model (bảng, quan hệ), logic DAX và bố cục report, vì đây là phần thể hiện kỹ năng.
- Các mã trạng thái chung (`DONE`, `SUCCESS`, `FAILED_*`...) mà measure dùng để lọc.
