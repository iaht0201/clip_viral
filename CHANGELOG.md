# CHANGELOG - SupoClip

## [Unreleased] - 2026-03-30
### Added
- Dự án chính thức áp dụng phương pháp **Vibe Coding**.
- Tích hợp bộ tài liệu khởi động: `PRD.md`, `plan.md`, `rules.md`.
- File hướng dẫn chạy local: `LOCAL_SETUP.md`.

### Changed
- **Đợt cải tổ lớn (Major Overhaul)**:
    - Chuyển đổi Database từ **PostgreSQL** sang **SQLite**.
    - Cập nhật thư viện `asyncpg` sang `aiosqlite`.
    - Điều chỉnh Models để hỗ trợ `JSON` thay cho `ARRAY` (để tương thích SQLite).
    - Cập nhật `database.py` để tự động nhận diện và cấu hình cho SQLite.

### Optimized
- **Tăng tốc độ Render**: Song song hóa (Parallelize) quá trình tạo clip bằng `ThreadPoolExecutor`. Giờ đây hệ thống có thể xử lý nhiều clip cùng lúc thay vì đợi từng cái một.
- **Tối ưu Database**: Kích hoạt **WAL (Write-Ahead Logging)** mode cho SQLite, giúp tăng tốc độ ghi và cho phép đọc/ghi đồng thời tốt hơn.
- **Tải Video nhanh hơn**: Cấu hình `yt-dlp` tải đồng thời các fragment video (parallel fragments).
- **Video Processing**: Tối ưu hóa cài đặt encoding (preset `superfast`) và tự động sử dụng số lượng thread tối đa từ CPU.

### Fixed
- Lỗi không thể chạy local mà không có Docker.
- Hỗ trợ tốt hơn cho việc lưu trữ video nội bộ (local data storage).
