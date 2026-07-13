#!/bin/bash
# Kaizen AI — Start Script
# Runs backend + frontend in parallel

set -e

echo ""
echo "⚙  Kaizen AI — Industrial Knowledge Intelligence Platform"
echo "─────────────────────────────────────────────────────────"
echo ""

# Check .env
if [ ! -f .env ]; then
  echo "⚠  No .env found — copying from .env.example"
  cp .env.example .env
  echo "   Add your GEMINI_API_KEY to .env before running"
  echo ""
fi

# Install Python deps
echo "▶  Installing Python dependencies..."
pip install -r requirements.txt --quiet --break-system-packages 2>/dev/null || pip install -r requirements.txt --quiet

# Install frontend deps
echo "▶  Installing frontend dependencies..."
cd frontend && npm install --silent && cd ..

echo ""
echo "▶  Starting Kaizen AI..."
echo "   Backend:   http://localhost:8000"
echo "   Frontend:  http://localhost:3000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""

# Start both
(cd api && python main.py) &
BACKEND_PID=$!

(cd frontend && npm run dev) &
FRONTEND_PID=$!

# Cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped.'" EXIT

wait
