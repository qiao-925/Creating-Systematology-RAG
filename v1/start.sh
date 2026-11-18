#!/bin/bash
set -e

# Start FastAPI backend on port 8000
uvicorn backend.fastapi.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start Next.js frontend (standalone) on port 7860
cd /app/web
PORT=7860 node .next/standalone/server.js &
FRONTEND_PID=$!

# Wait for either process to exit
wait -n $BACKEND_PID $FRONTEND_PID
exit $?
