#!/bin/bash

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <input.json>"
  exit 1
fi

INPUT="$1"
DIR="$(dirname "$INPUT")"
BASENAME="$(basename "$INPUT" .json)"
ORIGIN="${DIR}/${BASENAME}-origin.json"

mv "$INPUT" "$ORIGIN"

jq '{
  language,
  text,
  segments: [.segments[] | {
    id, text, start, end
  }]
}' "$ORIGIN" > "$INPUT"

echo "Done: '$INPUT' → '$ORIGIN' (origin), result saved to '$INPUT'"