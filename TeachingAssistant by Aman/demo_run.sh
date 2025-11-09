#!/usr/bin/env bash
export $(grep -v '^#' .env | xargs) 2>/dev/null || true
echo "Starting uvicorn on port ${PORT:-8000}"
python -m uvicorn app.main:app --reload --port ${PORT:-8000}
