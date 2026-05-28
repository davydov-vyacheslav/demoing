#!/usr/bin/env bash
# tts.sh — synthesize every segment in a transcript JSON
#
# Requires: jq  (brew install jq)
#
# Usage:
#   ./tts.sh <transcript.json> <ref_audio.wav> <ref_text.txt> [model_dir] [chunks_dir]
#
# Output: <chunks_dir>/00/audio.wav, 01/audio.wav, ...
# Resumable: skips segments whose audio.wav already exists.

set -euo pipefail

JSON="${1:?Usage: tts.sh transcript.json ref_audio.wav ref_text.txt [model_dir] [chunks_dir]}"
REF_AUDIO="${2:?missing ref_audio.wav}"
REF_TEXT_FILE="${3:?missing ref_text.txt}"
MODEL="${4:-./models/qwen3-tts}"
CHUNKS="${5:-./chunks}"

REF_TEXT="$(cat "$REF_TEXT_FILE")"
TOTAL=$(jq '.segments | length' "$JSON")

mkdir -p "$CHUNKS"
echo "Synthesizing $TOTAL segments → $CHUNKS"

while IFS=$'\t' read -r ID TEXT; do
    OUT="$CHUNKS/$(printf '%02d' "$ID")"
    WAV="$OUT/audio.wav"

    if [[ -f "$WAV" ]]; then
        echo "  [$ID/$((TOTAL-1))] skip  $TEXT" | cut -c1-72
        continue
    fi

    echo "  [$ID/$((TOTAL-1))] tts   $TEXT" | cut -c1-72
    mkdir -p "$OUT"

    python -m mlx_audio.tts.generate \
        --model       "$MODEL"     \
        --text        "$TEXT"      \
        --ref_audio   "$REF_AUDIO" \
        --ref_text    "$REF_TEXT"  \
        --output_path "$OUT"       \
        --join_audio               \
        --max_tokens  30000

    [[ -f "$WAV" ]] || echo "  [$ID] WARNING: no audio.wav produced"

done < <(jq -r '.segments[] | [.id, .text] | @tsv' "$JSON")

echo "Done."