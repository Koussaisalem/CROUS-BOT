#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

cd "$HOME/crous-bot"

if [[ ! -f ".env" ]]; then
  echo "Missing .env file in $HOME/crous-bot"
  exit 1
fi

mkdir -p logs

termux-wake-lock || true

python -m src.main >> logs/monitor.log 2>&1
