#!/usr/bin/env bash
set -euo pipefail

CMD=${1:-start}

export GEMINI_API_KEY="${GEMINI_API_KEY:-}"
export GEMINI_MOCK="${GEMINI_MOCK:-false}"

function start() {
  echo "Starting Teaching Assistant (mock=$GEMINI_MOCK)..."
  python -u -c "from TeachingAssistant.src.gemini_stream.websocket_client import GeminiWebSocketClient, asyncio; import asyncio as _a; print('spawned noop');"
  # Use a simple demo runner if you want
  python -u -m TeachingAssistant.src.teaching_assistant._demo || true
}

function test() {
  echo "Running tests..."
  pytest -q TeachingAssistant/src/tests
}

case "$CMD" in
  start) start ;;
  test) test ;;
  *) echo "Unknown command. Use start or test." ; exit 1 ;;
esac
