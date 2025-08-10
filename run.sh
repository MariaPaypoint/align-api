#!/usr/bin/env bash
set -euo pipefail

# Project root (directory containing this script)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Configuration (can be overridden by env vars)
VENV_DIR="${VENV_DIR:-venv}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8002}"
ENVIRONMENT="${ENV:-dev}"  # set ENV=prod to disable --reload

# 1) Create venv if missing
if [[ ! -d "$VENV_DIR" ]]; then
  echo "[run.sh] Creating virtual environment in '$VENV_DIR'..."
  python3 -m venv "$VENV_DIR"
fi

# 2) Activate venv
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"

# Resolve venv python explicitly
PY="$VENV_DIR/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "[run.sh] ERROR: Python interpreter not found at $PY" >&2
  exit 1
fi

# 3) Upgrade pip tooling and install deps
"$PY" -m pip install --upgrade pip setuptools wheel >/dev/null
if [[ -f requirements.txt ]]; then
  echo "[run.sh] Installing dependencies from requirements.txt..."
  "$PY" -m pip install -r requirements.txt
fi

# 4) Load environment variables from .env if present
if [[ -f .env ]]; then
  echo "[run.sh] Loading environment variables from .env"
  set -a
  # shellcheck disable=SC1091
  source ./.env
  set +a
fi

# 5) Run DB migrations if Alembic is configured
if [[ -f alembic.ini ]]; then
  if [[ "${SKIP_MIGRATIONS:-0}" == "1" ]]; then
    echo "[run.sh] SKIP_MIGRATIONS=1 -> skipping alembic migrations"
  else
    echo "[run.sh] Applying database migrations (alembic upgrade head)"
    "$PY" -m alembic upgrade head
  fi
fi

# 6) Start the FastAPI app with Uvicorn
RELOAD_FLAG=""
if [[ "$ENVIRONMENT" == "dev" ]]; then
  RELOAD_FLAG="--reload"
fi

echo "[run.sh] Starting Uvicorn on ${HOST}:${PORT} (env=$ENVIRONMENT)"
exec "$PY" -m uvicorn app.main:app --host "$HOST" --port "$PORT" ${RELOAD_FLAG}
