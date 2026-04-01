#!/bin/bash
echo "Stopping all SupoClip processes..."
# Kill uvicorn (backend API)
pkill -f "uvicorn src.main:app"
# Kill arq (backend worker)
pkill -f "arq src.workers.tasks.WorkerSettings"
# Kill npm/next (frontend)
pkill -f "next dev"

# Remove pid files
rm -f *.pid
echo "Stopped."
