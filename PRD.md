# 📄 PRD: SupoClip (Hybrid Cloud-Local) - Hyper-Detailed Specification

## 1. Tầm nhìn & Mục tiêu (Vision & Objectives)
SupoClip là hệ thống AI Clipping lách bản quyền có hiệu năng cao, tối ưu cho máy tính cá nhân.
- **Phần cứng mục tiêu:** Intel Core i5, 12GB RAM.
- **Ràng buộc hiệu năng:** RAM < 8GB (luôn dư 4GB cho hệ điều hành), CPU Load < 90%.
- **Tính năng cốt lõi:** Download Đa nền tảng -> Bóc băng AI -> Chấm điểm Viral -> Dịch thuật & Lồng tiếng (TTS Local) -> Render lách bản quyền (Anti-Copyright).

---

## 2. Đặc tả kỹ thuật Module (Technical Specifications)

### 2.1. Module Ingestion (Tải & Bóc băng)
- **Công nghệ:** `yt-dlp` (phiên bản ổn định mới nhất).
- **Ràng buộc:**
    - Tải tối đa độ phân giải 1080p (Ưu tiên 720p nếu RAM > 10GB).
    - `concurrent_fragment_downloads: 5` (Để tối ưu băng thông).
    - Audio trích xuất: Mono, 16kHz (Để tiết kiệm RAM khi gửi lên AssemblyAI).
- **AssemblyAI:** Yêu cầu Word-level Timestamp (Start/End từng từ).

### 2.2. Module AI Brain (Groq & Gemini)
- **Groq (Llama 3 70B):** Dùng để chấm điểm Viral dựa trên Transcript.
    - Input: Transcript JSON + Hook Selection Prompt.
    - Output: List 5 clips chính xác đến mili giây.
- **Gemini 1.5 Flash:** Dùng để dịch kịch bản sang tiếng Việt & tạo Title hấp dẫn.
- **Rate Limit Management:** 
    - Retry tối đa 3 lần với Exponential Backoff.
    - Nếu API lỗi liên tục, tự động ghi log lỗi vào SQLite và báo về `n8n`.

### 2.3. Module Local TTS (MeloTTS)
- **Model:** `nmcuong/MeloTTS-Vietnamese`.
- **Endpoint:** `http://localhost:8880/convert` (Mặc định).
- **Ràng buộc:** 
    - Text đầu vào tối đa 500 ký tự cho mỗi lần gọi (để tránh tràn RAM).
    - Output: .wav 22050Hz hoặc 44100Hz.

### 2.4. Module Rendering & Anti-Copyright (MoviePy/OpenCV)
- **Xử lý tuần tự (Sequential):** `1 clip at a time`.
- **Quy tắc lách bản quyền (Anti-Copyright Rules):**
    - **Mirroring:** Luôn lật ngang video (Flip X).
    - **Time Scaling:** Tăng tốc cố định 1.08x.
    - **Color Grading:** Brightness +5%, Saturation +5%.
    - **Dynamic Crop:** Face-centered crop (Phát hiện khuôn mặt bằng MediaPipe nếu có thể).
    - **Auto-Transitions:** Chèn hiệu ứng mờ (Blur) hoặc Zoom mỗi 5-7 giây để thay đổi hash hình ảnh.
- **Resource Cleanup:** 
    - `threads=2` cho MoviePy encode.
    - `gc.collect()` ngay sau khi lệnh `write_videofile` hoàn tất.
    - Xóa file tạm (`.mp4`, `.wav`, `.json`) trong thư mục `temp/` ngay sau khi lưu file thành phẩm ra `outputs/`.

---

## 3. Cấu trúc Cơ sở dữ liệu (SQLite & DuckDB)
- **SQLite (Dữ liệu điều hành):**
    - `tasks`: id, status, video_url, local_path, created_at.
    - `clips`: task_id, start_time, end_time, viral_score, speech_text, translation_text, voiceover_path, output_path.
- **DuckDB (Dữ liệu phân tích):**
    - Lưu lịch sử chấm điểm Viral của hàng vạn clip để tối ưu hóa Prompt sau này.

---

## 4. Tích hợp Orchestration (n8n)
- **Webhook Endpoint:** `/api/v1/webhooks/task-update`.
- **Payload:** Gửi Task Status (Progress, Error, Completion URL) về server n8n của người dùng để quản lý tập trung.

---

## 5. Tiêu chuẩn Kiểm thử (Testing Standard)
- **Unit Test (Pytest):** Phải đạt 90% coverage cho các module logic (Downloader, AI Parser, TTS Wrapper).
- **Integration Test:** Kiểm tra luồng từ link video -> clip render hoàn chỉnh.
- **Resource Test:** Mỗi Clip render không được chiếm dụng quá 2GB RAM đỉnh (Peak RAM).
