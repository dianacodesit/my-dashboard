#!/bin/bash
# Keep the dashboard on http://127.0.0.1:8080/ even after Cursor quits.
set -u
ROOT="/Users/diana/my-dashboard"
PORT="${PORT:-8080}"
PY="${PYTHON:-/usr/bin/python3}"
LOG="$ROOT/.serve.watch.log"
cd "$ROOT" || exit 1

healthy() {
  curl -sf -o /dev/null --max-time 2 "http://127.0.0.1:${PORT}/"
}

echo "$(date '+%F %T') watchdog up" >> "$LOG"
while true; do
  if healthy; then
    sleep 8
    continue
  fi
  echo "$(date '+%F %T') 8080 down — starting serve.py" >> "$LOG"
  "$PY" "$ROOT/serve.py"
  echo "$(date '+%F %T') serve.py exited $?" >> "$LOG"
  sleep 2
done
