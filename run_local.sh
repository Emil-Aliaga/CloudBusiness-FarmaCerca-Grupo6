#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
("$ROOT/backend/run_local.sh") &
BACK_PID=$!
sleep 4
("$ROOT/frontend/run_local.sh") &
FRONT_PID=$!
echo "Frontend: http://127.0.0.1:5500"
echo "Backend:  http://127.0.0.1:8000"
wait $BACK_PID $FRONT_PID
