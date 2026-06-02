#!/usr/bin/env bash
# preflight.sh — verify prerequisites for the demo-flow pipeline (no side effects).
#
# Usage:
#   preflight.sh <workdir> [models_dir] [venv_dir] [builder_version]
# Defaults: models_dir=./models  venv_dir=./.venv  builder_version=latest
#
# Run scripts/setup.sh first to auto-provision the venv + models; this script only checks.
# Prints [ OK ] / [WARN] / [FAIL]. Exits non-zero if any hard requirement fails.

WORKDIR="${1:?Usage: preflight.sh <workdir> [models_dir] [venv_dir] [builder_version]}"
MODELS_DIR="${2:-./models}"
VENV="${3:-./.venv}"
BUILDER_VER="${4:-latest}"
IMAGE="davs87/demo-builder:${BUILDER_VER}"
PY="$VENV/bin/python"

fail=0
ok()   { printf '  [ OK ] %s\n' "$1"; }
warn() { printf '  [WARN] %s\n' "$1"; }
bad()  { printf '  [FAIL] %s\n' "$1"; fail=1; }

echo "demo-flow preflight"
echo "  workdir      : $WORKDIR"
echo "  models_dir   : $MODELS_DIR"
echo "  venv         : $VENV"
echo "  builder image: $IMAGE"
echo

echo "Host tools (cannot be auto-installed)"
command -v docker >/dev/null 2>&1 && ok "docker present" || bad "docker not found (required for render + build)"
if command -v docker >/dev/null 2>&1; then
  docker info >/dev/null 2>&1 && ok "docker daemon running" || bad "docker daemon not reachable (is Docker Desktop running?)"
fi
command -v whisperkit-cli >/dev/null 2>&1 && ok "whisperkit-cli present" || bad "whisperkit-cli not found — brew install whisperkit-cli (transcribe, step 5)"
command -v jq >/dev/null 2>&1 && ok "jq present" || bad "jq not found — brew install jq (step 5 cleanup)"

echo
echo "Python env (auto-provisioned by setup.sh)"
if [ -x "$PY" ]; then
  ok "venv interpreter present ($PY)"
  "$PY" -c "import mlx_audio" >/dev/null 2>&1 \
    && ok "mlx_audio importable" \
    || bad "mlx_audio missing in venv — run scripts/setup.sh (TTS, step 4)"
else
  bad "venv not found at $VENV — run scripts/setup.sh"
fi

echo
echo "Docker image"
if command -v docker >/dev/null 2>&1; then
  if docker image inspect "$IMAGE" >/dev/null 2>&1; then
    ok "image $IMAGE available locally"
  else
    warn "image $IMAGE not local — will be pulled on first use (needs network). Pre-pull: docker pull $IMAGE"
  fi
fi

echo
echo "Models ($MODELS_DIR) — auto-downloaded by setup.sh"
[ -d "$MODELS_DIR/qwen3-tts" ] \
  && ok "Qwen3-TTS model found" \
  || bad "missing $MODELS_DIR/qwen3-tts — run scripts/setup.sh (TTS, step 4)"
[ -d "$MODELS_DIR/openai_whisper/openai_whisper-large-v3" ] \
  && ok "Whisper large-v3 model found" \
  || bad "missing $MODELS_DIR/openai_whisper/openai_whisper-large-v3 — run scripts/setup.sh (transcribe, step 5)"

echo
echo "Working-dir inputs ($WORKDIR)"
[ -d "$WORKDIR" ] || bad "working directory does not exist: $WORKDIR"
[ -f "$WORKDIR/0.draft.txt" ]        && ok "0.draft.txt present"        || bad "missing 0.draft.txt (your speech draft)"
[ -f "$WORKDIR/0.my_reference.wav" ] && ok "0.my_reference.wav present" || warn "missing 0.my_reference.wav (needed from step 4 — generate via ref-audio-normalize)"
[ -f "$WORKDIR/0.my_reference.txt" ] && ok "0.my_reference.txt present" || warn "missing 0.my_reference.txt (needed from step 4)"

echo
if [ "$fail" -eq 0 ]; then
  echo "Preflight: all hard requirements satisfied."
else
  echo "Preflight: FAILED — resolve the [FAIL] items above (most are fixed by scripts/setup.sh)."
fi
exit "$fail"
