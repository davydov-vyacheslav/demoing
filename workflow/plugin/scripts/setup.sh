#!/usr/bin/env bash
# setup.sh — provision the demo-flow environment: python venv + deps + precached models.
# Idempotent and safe to re-run; does nothing if everything is already in place.
# No manual `source .venv/bin/activate` needed — callers use "$VENV/bin/python" directly.
#
# Usage:
#   setup.sh [models_dir] [venv_dir]
# Defaults: ./models  ./.venv  (relative to where Claude was launched)

set -euo pipefail
MODELS_DIR="${1:-./models}"
VENV="${2:-./.venv}"
PY="$VENV/bin/python"

echo "demo-flow setup"
echo "  venv   : $VENV"
echo "  models : $MODELS_DIR"
echo

# 1. python virtualenv
if [ ! -x "$PY" ]; then
  echo "→ creating virtualenv at $VENV ..."
  python3 -m venv "$VENV"
else
  echo "✓ virtualenv present"
fi

# 2. python dependencies
if ! "$PY" -c "import mlx_audio, huggingface_hub" >/dev/null 2>&1; then
  echo "→ installing python deps (huggingface_hub, mlx-audio) ..."
  "$PY" -m pip install --quiet --upgrade pip
  "$PY" -m pip install --quiet huggingface_hub mlx-audio
else
  echo "✓ python deps present (mlx-audio, huggingface_hub)"
fi

# 3. precached AI models (several GB, one-time)
need_dl=0
[ -d "$MODELS_DIR/qwen3-tts" ] || need_dl=1
[ -d "$MODELS_DIR/openai_whisper/openai_whisper-large-v3" ] || need_dl=1
if [ "$need_dl" -eq 1 ]; then
  echo "→ downloading models into $MODELS_DIR (several GB, one-time) ..."
  mkdir -p "$MODELS_DIR"
  # SSL-relaxed + proxy-aware download (mirrors the snapshot_download in ../README.md)
  "$PY" - "$MODELS_DIR" <<'PYEOF'
import sys, functools, httpx
httpx.Client = functools.partial(httpx.Client, verify=False, trust_env=True)
from huggingface_hub import snapshot_download
out = sys.argv[1]
snapshot_download('argmaxinc/whisperkit-coreml',
                  local_dir=f'{out}/openai_whisper',
                  allow_patterns=['openai_whisper-large-v3/*'])
snapshot_download('mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit',
                  local_dir=f'{out}/qwen3-tts',
                  ignore_patterns=['*.msgpack'])
PYEOF
  echo "✓ models downloaded"
else
  echo "✓ models present"
fi

echo
echo "Setup complete. Use this interpreter for TTS: $PY"
