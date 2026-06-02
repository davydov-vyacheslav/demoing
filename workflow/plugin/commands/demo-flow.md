---
description: Drive the end-to-end demo-video pipeline (speech → deck → voice → assembled video) inside a working folder, refining each step interactively with the user.
argument-hint: "[working-dir] [builder-version] e.g. /demo-flow @my-demo/ 0.1.5"
disable-model-invocation: true
---

# /demo-flow

Orchestrate the demo-video production pipeline. Walk the steps **in order**; after each step
**stop and collaborate with the user** until they approve, then move on. Never auto-advance.

## Working directory

The pipeline reads inputs from and writes ALL outputs (including the final video) into a single
**working directory**, `WORKDIR`.

- `WORKDIR` = the folder in `$ARGUMENTS` (e.g. `/demo-flow @my-demo/`). Resolve it to an
  absolute path.
- If `$ARGUMENTS` is empty, **ask the user** which folder to use, or default to the current
  directory. Confirm the resolved path back to the user before running anything.

Expected inputs already in `WORKDIR`:
- `0.draft.txt` — the rough speech draft.
- `0.my_reference.wav` + `0.my_reference.txt` — the cloned reference voice and its text.

All generated files (`1.speech.txt`, `2.presentation.*`, `slides/`, `4.presentation.*`,
`5.demo.yaml`, and **`final.mov`**) are created **in `WORKDIR` alongside the inputs** — not in
any `sample/` subfolder.

## Environment

The plugin manages its own environment — no env vars, and **never** rely on a pre-activated
venv. Resolve these once and reuse:

- **`BUILDER_VER`** = the `davs87/demo-builder` image tag: a version token in `$ARGUMENTS`
  (e.g. `/demo-flow @my-demo/ 0.1.5`), else `latest`. Report the resolved tag before any docker
  step and use `davs87/demo-builder:$BUILDER_VER` everywhere below.
- **`VENV`** = `./.venv`, **`MODELS_DIR`** = `./models` (both relative to where Claude was
  launched). `setup.sh` creates them if absent. Call python as **`"$VENV/bin/python"`** directly
  — do not `source activate`. Models are shared here, **not** copied into `WORKDIR`.
- Bundled plugin assets live under `${CLAUDE_PLUGIN_ROOT}` (`typst-styles/`, `scripts/`).

## Step 0 — Provision, then preflight (always run first)

First **provision** the venv, python deps, and models (idempotent — auto-downloads anything
missing, including the multi-GB models):

```sh
"${CLAUDE_PLUGIN_ROOT}/scripts/setup.sh" "$MODELS_DIR" "$VENV"
```

Then **verify** the rest (docker, whisperkit-cli, jq, image, inputs):

```sh
"${CLAUDE_PLUGIN_ROOT}/scripts/preflight.sh" "$WORKDIR" "$MODELS_DIR" "$VENV" "$BUILDER_VER"
```

Show both reports. If preflight exits non-zero (`[FAIL]`), **stop** and help the user resolve
the remaining host-tool items (docker / whisperkit-cli / jq can't be auto-installed). `[WARN]`
items are fine to continue past (image pulled on first use; reference voice only needed at step 4).

## Resume

Before running a step, check whether its output already exists in `WORKDIR`. If it does, ask
the user whether to **reuse it and skip**, or **regenerate**. This lets the flow resume midway.

## Interaction model (applies to every step)

Each step is a **refine loop**, not a one-shot:

1. Run the step and surface the result faithfully (show the text, open/describe the PDF,
   point to the audio/video file, print command output and any errors).
2. Ask: **"Approve and continue, or what should I change?"**
3. If the user requests changes, **make them yourself** — re-run the skill with their feedback,
   or edit the generated file directly, or re-run the command with adjusted parameters — then
   re-present. Loop here until the user explicitly approves.
4. Only on approval, advance to the next step.

Do not tell the user to go edit files by hand; they direct, you apply.

## Pipeline

1. **Speech** — invoke the `generate-speech` skill: `WORKDIR/0.draft.txt` → `WORKDIR/1.speech.txt`.
   Refine loop: tone, length, wording, structure.

2. **Presentation (typ)** — invoke the `generate-presentation` skill:
   `WORKDIR/1.speech.txt` → `WORKDIR/2.presentation.typ`.
   Refine loop: slide splits, bullet wording, image placeholders.

3. **Render deck**:
   ```sh
   docker run --rm -v "$WORKDIR":/work \
     -v "${CLAUDE_PLUGIN_ROOT}/typst-styles":/work/typst-styles \
     davs87/demo-builder:$BUILDER_VER \
     presentation ./2.presentation.typ --styles ./typst-styles
   ```
   Produces `WORKDIR/2.presentation.pdf` and `WORKDIR/slides/*.png`.
   Refine loop: if the user wants layout/content changes, go back to step 2 and re-render.

4. **Voice** — synthesize narration with the cloned reference voice:
   ```sh
   "$VENV/bin/python" -m mlx_audio.tts.generate \
     --model "$MODELS_DIR/qwen3-tts" \
     --text "$(cat "$WORKDIR/1.speech.txt")" \
     --ref_audio "$WORKDIR/0.my_reference.wav" \
     --ref_text "$(cat "$WORKDIR/0.my_reference.txt")" \
     --output_path "$WORKDIR/output" --join_audio --max_tokens 30000
   mv "$WORKDIR/output/audio.wav" "$WORKDIR/4.presentation.wav" && rm -rf "$WORKDIR/output"
   ```
   Refine loop: if pacing/wording is off, adjust `1.speech.txt` (step 1) and resynthesize.

5. **Transcribe for word timestamps** (no checkpoint — mechanical):
   ```sh
   whisperkit-cli transcribe \
     --audio-path "$WORKDIR/4.presentation.wav" \
     --model-path "$MODELS_DIR/openai_whisper/openai_whisper-large-v3" \
     --word-timestamps --report --report-path "$WORKDIR/"
   "${CLAUDE_PLUGIN_ROOT}/scripts/clean-transribe-json.sh" "$WORKDIR/4.presentation.json"
   ```

6. **Config** — invoke the `generate-demo-config` skill:
   `WORKDIR/2.presentation.pdf` + `WORKDIR/4.presentation.json` → `WORKDIR/5.demo.yaml`.
   Refine loop: verify `audio_file`, `resolution`, slide↔cue mapping, and per-topic timings.

7. **Build** — assemble the final video into `WORKDIR`:
   ```sh
   docker run --rm -v "$WORKDIR":/work davs87/demo-builder:$BUILDER_VER \
     build 5.demo.yaml -o final.mov --fps 60
   ```
   Output: **`WORKDIR/final.mov`** (next to the other generated files). Refine loop: if timing or
   ordering is wrong, adjust `5.demo.yaml` (step 6) and rebuild.

After every command, surface its output and any errors before asking to proceed.
