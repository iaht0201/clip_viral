# 🚀 Hướng dẫn chạy SupoClip Local (Không Docker)

Tài liệu này hướng dẫn bạn cách thiết lập và chạy SupoClip trực tiếp trên máy tính cá nhân dùng hệ điều hành Linux/macOS.

## 1. Yêu cầu hệ thống
- **Python**: 3.11 trở lên.
- **Node.js**: 20.x trở lên (cho Frontend).
- **Redis**: Để quản lý hàng đợi công việc (Worker).
- **FFmpeg**: Để xử lý video.
- **SQLite**: (Đã tích hợp sẵn trong Python).

### Cài đặt công cụ hỗ trợ (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install redis-server ffmpeg python3-pip python3-venv
```

## 2. Thiết lập Backend

### Bước 2.1: Tạo môi trường ảo và cài đặt dependencies
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -e .
# Hoặc nếu dùng 'uv' (khuyên dùng):
# uv sync
```

### Bước 2.2: Cấu hình Environment
Copy file `.env.example` thành `.env` và điền các API Key cần thiết (OpenAI, Google, Groq...):
```bash
cp .env.example .env
```
Đảm bảo dòng sau có trong `.env`:
```env
DATABASE_URL=sqlite+aiosqlite:///./supoclip.db
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Bước 2.3: Khởi tạo Database
```bash
# Chạy script khởi tạo thủ công (đã được cập nhật cho SQLite)
python3 -c "import asyncio; from src.database import init_db; asyncio.run(init_db())"
```

## 3. Thiết lập Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local
```

## 4. Khởi chạy ứng dụng

Bạn cần chạy 3 tiến trình song song:

### 4.1. Chạy Backend API
```bash
cd backend
source venv/bin/activate
uvicorn src.main:app --reload --port 8000
```

### 4.2. Chạy Worker (Xử lý video)
```bash
cd backend
source venv/bin/activate
arq src.workers.tasks.WorkerSettings
```

### 4.3. Chạy Frontend
```bash
cd frontend
npm run dev
```

---

## 💡 Lưu ý quan trọng
- **SQLite**: File dữ liệu sẽ được lưu tại `backend/supoclip.db`. Bạn có thể dùng [SQLite Browser](https://sqlitebrowser.org/) để xem dữ liệu.
- **Video Temp**: Video tải về và clip render sẽ nằm trong thư mục `backend/temp` và `backend/outputs`.
- **Redis**: Đảm bảo Redis đang chạy (`sudo service redis-server start`).
