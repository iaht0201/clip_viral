#!/bin/bash
# Local start script for SupoClip without Docker

echo "Starting SupoClip locally..."

# 1. Start Backend API
echo "Starting Backend API on port 8000..."
cd backend
source venv/bin/activate
nohup uvicorn src.main:app --port 8000 --host 0.0.0.0 > backend_api.log 2>&1 &
echo $! > ../backend_api.pid

# 2. Start Worker
echo "Starting Worker..."
nohup arq src.workers.tasks.WorkerSettings > backend_worker.log 2>&1 &
echo $! > ../backend_worker.pid

# 3. Start Frontend
echo "Starting Frontend on port 3000..."
cd ../frontend
nohup npm run dev > frontend.log 2>&1 &
echo $! > ../frontend.pid

cd ..
echo "SupoClip is starting!"
echo "- Frontend: http://localhost:3000"
echo "- Backend: http://localhost:8000"
echo "- Logs: backend/backend_api.log, backend/backend_worker.log, frontend/frontend.log"
