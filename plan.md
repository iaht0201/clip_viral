# 🗺️ Plan: SupoClip Migration & Feature Overhaul (Hyper-Detailed)

## 🎯 Phase 1: Database & Foundation (Completed)
- [x] Chuyển đổi sang SQLite (aiosqlite) + WAL Mode.
- [x] Cấu hình SQLite performance tuning (PRAGMA journal_mode=WAL, cache_size=-64000).
- [x] Cập nhật models: `JSON` cho `List[str]`.
- [x] Tối ưu `yt-dlp` (parallel fragments + chunk size 10MB).
- [x] Triển khai `Sequential Processing` (Lần 1).

## 🚀 Phase 2: AI Brain & Orchestration (High Priority)
- [ ] Refactor `ai.py`: Mặc định dùng **Groq (Llama 3 70B)** để Viral Scoring.
- [ ] Tích hợp **Gemini 1.5 Flash** (Dịch thuật kịch bản tiếng Việt).
- [ ] Xây dựng Webhook API để gửi trạng thái về **n8n**.
- [ ] Triển khai DuckDB Analytics: Lưu trữ lịch sử viral scores để phân tích xu hướng content.

## 🎙️ Phase 3: Local TTS Module (Vietnam-Centered)
- [ ] Backend Service: Gọi `POST /convert` tới `MeloTTS-Vietnamese` local.
- [ ] Xử lý ngắt nghỉ (6 thanh điệu) và sinh `.wav` local.
- [ ] Cơ chế Fallback: Nếu MeloTTS không phản hồi trong 30s, tự động chuyển sang Edge-TTS hoặc Skip lồng tiếng (vẫn render được sub).

## 🔥 Phase 4: Anti-Copyright Rendering (Sequential & Safe)
- [ ] Hoàn thiện `create_optimized_clip` với rules:
    - `with_effects([vfx.MirrorX()])` (Flip).
    - `MultiplySpeed(1.08)` (Speedup).
    - `MultiplyColor(1.05)` (Brightness).
    - Zoom effects mỗi 5-7 giây tự động.
- [ ] **Hardsub song ngữ**: Hiển thị text Eng (trên) và Việt (dưới) với font TikTok.
- [ ] Cơ chế **Garbage Collection (gc)**: Đảm bảo giải phóng bộ nhớ ngay sau mỗi clip. `RAM check < 8GB limit`.

## 🎨 Phase 5: Astro UI & UX (Lightweight)
- [ ] Chuyển đổi sang **Astro** để giảm thiểu JavaScript payload.
- [ ] Tích hợp **Shadcn/ui** components (Tailwind CSS, Radix UI).
- [ ] Dashboard theo dõi tiến độ thời gian thực (Real-time progress via Redis).

## 🧪 Phase 6: Testing & Stability (Crucial)
- [ ] **Unit Tests**: Viết bộ test suite bằng `pytest` cho:
    - `video_download_utils.py` (Mocking yt-dlp).
    - `ai.py` (Mocking Groq/Gemini).
    - `tts.py` (Mocking MeloTTS).
- [ ] **Resource Benchmarking**: Script đo lường CPU/RAM sử dụng khi render để cảnh báo người dùng.
- [ ] **Integration Test**: Luồng hoàn tất (End-to-End) từ URL -> Clip thành phẩm (.mp4).
