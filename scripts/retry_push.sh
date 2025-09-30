#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p logs
LOG="logs/push_retry.log"
echo "[info] starting push retry at $(date)" >> "$LOG"
echo "[info] remote: $(git remote -v | tr '\n' ' | ')" >> "$LOG"

ATTEMPTS=0
while true; do
  ATTEMPTS=$((ATTEMPTS+1))
  echo "[attempt $ATTEMPTS] $(date): git push origin main" >> "$LOG"
  if git push origin main >> "$LOG" 2>&1; then
    echo "[success] $(date): push completed" >> "$LOG"
    exit 0
  else
    echo "[wait] $(date): push failed; will retry in 60s" >> "$LOG"
    sleep 60
  fi
done

