#!/usr/bin/env bash
# 启动寻梦后端（首次会自动建 venv 并装依赖）
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt
exec uvicorn app.main:app --host 0.0.0.0 --port "${APP_PORT:-8000}" --reload
