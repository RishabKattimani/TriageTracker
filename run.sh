#!/usr/bin/env bash
# One-command macOS launcher. Idempotent. Cleans up the server on interrupt.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

SKIP_BROWSER="${TRIAGETRACKER_SKIP_BROWSER:-0}"
CHECK_ONLY=0
PROBE_CAMERA=0

usage() {
  cat <<'EOF'
TriageTracker launcher

Usage:
  ./run.sh                 Create/reuse .venv, install deps, start server, open browser
  ./run.sh --no-browser    Same, but do not open a browser
  ./run.sh --check         Diagnose Python, deps, and assets; do not start the server
  ./run.sh --probe-camera  Include a webcam probe in the printed health check

Environment:
  TRIAGETRACKER_SKIP_BROWSER=1   Same as --no-browser
  TRIAGETRACKER_PORT             Force a port (must be free)
EOF
}

for arg in "${@:-}"; do
  case "$arg" in
    -h|--help)
      usage
      exit 0
      ;;
    --no-browser)
      SKIP_BROWSER=1
      ;;
    --check)
      CHECK_ONLY=1
      ;;
    --probe-camera)
      PROBE_CAMERA=1
      ;;
    "")
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      usage >&2
      exit 2
      ;;
  esac
done

fail() {
  echo "TriageTracker: $1" >&2
  exit 1
}

find_python() {
  local candidate version major minor
  for candidate in python3.11 python3.12 python3.13 python3; do
    if command -v "$candidate" >/dev/null 2>&1; then
      version="$("$candidate" -c 'import sys; print("%d.%d" % (sys.version_info.major, sys.version_info.minor))')"
      major="${version%%.*}"
      minor="${version#*.}"
      if [[ "$major" -eq 3 && "$minor" -ge 11 ]]; then
        echo "$candidate"
        return 0
      fi
    fi
  done
  return 1
}

if ! PY="$(find_python)"; then
  fail "Python 3.11+ is required. On macOS with Homebrew: brew install python@3.11"
fi

if [[ ! -d .venv ]]; then
  echo "Creating virtual environment with $PY ..."
  "$PY" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

if ! python -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
  fail "The virtual environment is not Python 3.11+. Delete .venv and rerun ./run.sh"
fi

python -m pip install --upgrade pip >/dev/null
if ! python -c 'import fastapi, uvicorn, cv2, numpy, scipy, jinja2' >/dev/null 2>&1; then
  echo "Installing pinned dependencies from requirements.txt ..."
  python -m pip install -r requirements.txt
else
  python -m pip install -r requirements.txt >/dev/null
fi

mkdir -p models fixtures

download_model() {
  local url="$1"
  local dest="$2"
  if [[ -s "$dest" ]]; then
    return 0
  fi
  echo "Downloading $(basename "$dest") ..."
  if command -v curl >/dev/null 2>&1; then
    curl -L --fail --retry 3 -o "$dest" "$url" || {
      rm -f "$dest"
      echo "Could not download $dest. The app will start and /health will mark this asset missing."
    }
  else
    python - "$url" "$dest" <<'PY'
import sys, urllib.request
url, dest = sys.argv[1], sys.argv[2]
try:
    urllib.request.urlretrieve(url, dest)
except Exception as exc:
    print(f"Could not download {dest}: {exc}")
PY
  fi
}

download_model \
  "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task" \
  "models/face_landmarker.task"
download_model \
  "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task" \
  "models/pose_landmarker_lite.task"

if [[ ! -f fixtures/controlled_change.mp4 ]]; then
  echo "Generating synthetic optical fixtures (not clinical recordings) ..."
  python scripts/generate_fixtures.py || echo "Could not generate fixtures. Guided Demo will explain the gap instead of inventing measurements."
fi

PORT="${TRIAGETRACKER_PORT:-}"
if [[ -z "$PORT" ]]; then
  PORT="$(python -c 'from app.diagnostics import pick_port; print(pick_port())')"
fi
export TRIAGETRACKER_PORT="$PORT"

if [[ "$CHECK_ONLY" -eq 1 ]]; then
  python - <<PY
from app.diagnostics import collect_diagnostics
import json
print(json.dumps(collect_diagnostics(probe_camera=${PROBE_CAMERA}), indent=2))
PY
  exit 0
fi

SERVER_PID=""
cleanup() {
  if [[ -n "${SERVER_PID}" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "Starting TriageTracker on http://127.0.0.1:${PORT}/ ..."
python -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT" --log-level warning &
SERVER_PID=$!

ready=0
for _ in $(seq 1 80); do
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    fail "Server exited before becoming healthy. Check the traceback above."
  fi
  if python - "$PORT" <<'PY'
import json, sys, urllib.request
port = sys.argv[1]
try:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1) as resp:
        payload = json.load(resp)
    raise SystemExit(0 if payload.get("ready") else 2)
except Exception:
    raise SystemExit(1)
PY
  then
    ready=1
    break
  fi
  sleep 0.25
done

if [[ "$ready" -ne 1 ]]; then
  fail "Server did not become ready on port ${PORT}. See /health after fixing dependencies."
fi

echo "Health ready: http://127.0.0.1:${PORT}/health"
if [[ "$SKIP_BROWSER" -ne 1 ]]; then
  if command -v open >/dev/null 2>&1; then
    open "http://127.0.0.1:${PORT}/"
  else
    echo "Open http://127.0.0.1:${PORT}/ in a browser."
  fi
fi

wait "$SERVER_PID"
