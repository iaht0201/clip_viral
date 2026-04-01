# 📜 Rules: SupoClip AI Development Guidelines (Hyper-Strict)

## 0. GIỚI HẠN PHẦN CỨNG (HARDWARE QUOTA)
- **RAM Peak:** Tuyệt đối không vượt quá **3.5GB** cho bất kỳ tiến trình xử lý đơn lẻ nào.
- **CPU Threads:** Luôn sử dụng `threads=2` cho MoviePy. KHÔNG dùng `threads=os.cpu_count()`.
- **Temp Storage:** Phải dọn dẹp thư mục `temp/` định kỳ sau mỗi job hoàn thành.

---

## 🛠️ QUY TẮC CÔNG NGHỆ (TECH RULES)

### 1. Database (SQLite/DuckDB)
- Dùng `aiosqlite` + `WAL` mode.
- Dùng `DuckDB` cho dữ liệu lịch sử phân tích trên vạn bản ghi.
- Các hằng số `String(x)` phải có độ dài an toàn (`id` là `String(36)` UUID).

### 2. Video Rendering (MoviePy & Anti-Copyright)
- **Xử lý tuần tự (Sequential only)**: Xử lý xong clip I mới bốc clip II.
- **Anti-Copyright rules (Bắt buộc)**: 
    - `MirrorX()` (Flip).
    - `MultiplySpeed(1.08)` (Speedup).
    - `MultiplyColor(1.05)` (Brightness).
    - Tự động chèn transition/fade 0.5s ở đầu/cuối mỗi clip.
- **Garbage Collection**: Phải gọi `gc.collect()` sau mỗi clip render xong.

### 3. AI API (Reliability First)
- **Dùng Groq cho tốc độ**: Ưu tiên Llama 3 70B (Fast Mode).
- **Dùng Gemini cho ngôn ngữ**: Priority cao nhất cho dịch thuật/giật tít.
- Phải có cơ chế `Circuit Breaker`: Nếu API lỗi 5 lần liên tục, tạm dừng Task và thông báo về n8n Dashboard.

### 4. Tên biến & Quy ước Code (Coding Standards)
- Variable naming: `snake_case`.
- Class names: `PascalCase`.
- Constants: `SCREAMING_SNAKE_CASE`.
- **Phải có Unit Test cho mọi hàm xử lý dữ liệu mới.**

### 5. Frontend (Astro + Shadcn)
- Tuân thủ cấu trúc Astro Component.
- Dùng Shadcn Components (`npx shadcn-ui@latest add [component]`).
- Hạn chế Client-side JS, dùng Server Islands khi có thể.

---

## 🚨 KIỂM THỬ (TESTING RULES)
- **Unit Test (Bắt buộc)**: Mọi module logic phải có file `.tests.py` đi kèm.
- **Mocking**: Phải dùng `pytest-mock` cho các cuộc gọi API ngoài (Groq, Gemini, AssemblyAI).
- **Benchmarking**: Trước khi release module render mới, phải chạy script đo RAM peak.

---

## ❌ NHỮNG ĐIỀU CẤM KỴ (PROHIBITED)
1. Tuyệt đối không dùng `ARRAY` của Postgres trong Models.
2. Không dùng `ThreadPoolExecutor` cho các tiến trình render video (MoviePy).
3. Không lưu mật khẩu/API Key trực tiếp trong code (Chỉ dùng `.env`).
4. Không để lộ server filesystem path lên API response (Dùng `resolve_local_video_path`).
