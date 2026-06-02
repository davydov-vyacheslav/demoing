# demo-flow (Claude Code plugin)

Turn a rough draft into a narrated demo video — speech → slide deck → cloned-voice narration →
assembled video — driven from Claude Code, with an interactive review at every step.

> This is the **plugin** half of the project. It provisions its own python venv and ML models on
> first run (see Prerequisites). The parent [`../README.md`](../README.md) covers the broader
> project, the bundled `sample/` example, and the manual step-by-step.

## What's inside

| Component | Path | Role |
|---|---|---|
| Manifest | `.claude-plugin/plugin.json` | Plugin metadata (`name: demo-flow`) |
| Skills | `skills/*/SKILL.md` | The AI steps (auto-invoked by description) |
| Command | `commands/demo-flow.md` | `/demo-flow` — orchestrates the whole pipeline |
| Theme | `typst-styles/` | `demo-maker.typ` theme, logo, diagram SVGs |
| Scripts | `scripts/` | `setup.sh` (provision venv+models), `preflight.sh` (verify), `clean-transribe-json.sh`, `tts.sh` |

### Skills

- **`generate-speech`** — rough draft → polished, TTS-friendly spoken script.
- **`generate-presentation`** — script → Typst deck using the `demo-maker.typ` theme.
- **`generate-demo-config`** — presentation PDF + Whisper transcript → `demo-builder` `config.yaml`.

Each skill auto-triggers when you ask for the matching task (e.g. "polish this draft for TTS"),
and is also addressable as `/demo-flow:generate-speech`.

## Install

```sh
claude --plugin-dir /path/to/workflow/plugin
/reload-plugins        # after editing plugin files, no restart needed
```

## Prerequisites (host machine)

**You install only the host tools that can't be provisioned automatically:**

- Docker (for the `davs87/demo-builder` image) with the daemon running
- `python3` (3.14)
- `brew install whisperkit-cli jq`

**Everything else is auto-provisioned** by `scripts/setup.sh`, which `/demo-flow` runs in Step 0:
the python `.venv`, the `mlx-audio` / `huggingface_hub` deps, and the multi-GB models (Qwen3-TTS
+ Whisper large-v3) are created/downloaded on first run if missing. No env vars, and no manual
`source .venv/bin/activate` — the pipeline calls the venv's interpreter directly. You can also
provision ahead of time (args: `models_dir`, `venv_dir`):

```sh
scripts/setup.sh ./models ./.venv
```

## Usage: `/demo-flow`

`/demo-flow` runs the full pipeline against a **working directory** you choose. All inputs and
**all generated files — including `final.mov` — live in that one folder.**

```
/demo-flow @my-demo/        # use ./my-demo as the working dir
/demo-flow @my-demo/ 0.1.5  # also pin the demo-builder docker image tag
/demo-flow                  # asks which folder to use (or current dir)
```

**Docker image version:** the optional second argument pins the `davs87/demo-builder` tag. If
omitted it defaults to `latest`. The resolved tag is reported back before any docker step runs.

**Step 0 — provision + preflight:** before doing anything, `/demo-flow` runs
[`scripts/setup.sh`](scripts/setup.sh) (creates the venv, installs deps, downloads missing
models) and then [`scripts/preflight.sh`](scripts/preflight.sh) (verifies docker + daemon,
`whisperkit-cli`, `jq`, the venv interpreter, the chosen image, the models, and the working-dir
inputs). Preflight prints an `[ OK ] / [WARN] / [FAIL]` report and stops on any hard failure so
you fix the environment before the pipeline burns time. Run it standalone with
(args: `workdir`, `models_dir`, `venv_dir`, `builder_version`):

```sh
scripts/preflight.sh ./my-demo ./models ./.venv 0.1.5
```

**Put these in the working folder before you start:**

- `0.draft.txt` — your rough speech draft
- `0.my_reference.wav` + `0.my_reference.txt` — ~12s reference voice clip + its transcript

**What gets produced there:** `1.speech.txt`, `2.presentation.typ`, `2.presentation.pdf`,
`slides/*.png`, `4.presentation.wav`, `4.presentation.json`, `5.demo.yaml`, and **`final.mov`**.

### How the steps go

`/demo-flow` walks 7 steps and **stops after each one as a refine loop**: it shows you the
result and asks "approve, or what should I change?". You can simply **ask for corrections in
chat** — reword a slide, shorten the intro, fix a timing — and Claude applies them and
re-presents, looping until you approve. It never auto-advances, and you never have to hand-edit
files yourself unless you want to.

| # | Step | Tool | Output (in working dir) |
|---|------|------|----------|
| 1 | Speech | `generate-speech` skill | `1.speech.txt` |
| 2 | Deck markup | `generate-presentation` skill | `2.presentation.typ` |
| 3 | Render | docker `demo-builder` | `2.presentation.pdf`, `slides/*.png` |
| 4 | Voice | `mlx_audio` (TTS) | `4.presentation.wav` |
| 5 | Transcribe | `whisperkit-cli` + clean script | `4.presentation.json` |
| 6 | Config | `generate-demo-config` skill | `5.demo.yaml` |
| 7 | Build | docker `demo-builder` | **`final.mov`** |

Resume is automatic: if a step's output already exists in the folder, `/demo-flow` offers to
reuse or regenerate it.

> **Status:** the image-slides + narration path works end to end. Mixing in a screen recording
> (screencast) is still under construction — see the FIXMEs in [`../README.md`](../README.md).

## Using the skills in Claude Desktop

Plugins (and the `/demo-flow` command) are Claude Code–only. The three **skills**, however, can
be uploaded to Claude Desktop / claude.ai as Custom Skills (they're pure text generation):

```sh
cd skills && zip -r generate-speech.zip generate-speech
```

Upload at **Settings → Capabilities → Skills** (requires Pro/Max/Team + code execution). The
local tooling (docker, TTS, transcribe) can't run in Desktop's sandbox — bring it in via a local
MCP server instead. See [`../README.md`](../README.md) for details.
