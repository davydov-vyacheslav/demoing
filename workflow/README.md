# Demo Flow

Turn a rough draft into a narrated demo video: polish the speech, generate a Typst deck,
synthesize voice with a cloned reference, and assemble the final cut — with a human review
checkpoint between every step.

## Achtung!

> The workflow assumes that you are using a MacBook with an M chip.
> Other architectures are not supported.

---

## Project shape

The repo separates the **installable plugin** from the **workspace** (your sample inputs,
generated artifacts, downloaded models, and venv):

```
workflow/
├── plugin/                 ← the demo-flow Claude Code plugin (self-contained)
│   ├── .claude-plugin/plugin.json
│   ├── skills/             ← the three AI steps
│   ├── commands/           ← /demo-flow:run orchestrator
│   ├── scripts/            ← clean-transribe-json.sh, tts.sh
│   └── typst-styles/       ← demo-maker.typ theme, logo, diagram SVGs
├── sample/                 ← draft, speech, slides, audio, final.mov (experiments)
├── models/                 ← precached Whisper + Qwen3-TTS models (gitignored, multi-GB)
├── .venv/                  ← python env for TTS/transcribe
└── README.md
```

Everything under `plugin/` is the **Claude Code plugin** (`name: demo-flow`); nothing else
is needed to install it. The skills/command reference bundled assets via `${CLAUDE_PLUGIN_ROOT}`,
so `scripts/` and `typst-styles/` live inside the plugin and travel with it.

The three skills replace the old `prompts/*.md` files (single source of truth — no more
copy-pasting prompts between tools):

- **`generate-speech`** — draft → polished, TTS-friendly script.
- **`generate-presentation`** — script → Typst deck using the `demo-maker.typ` theme.
- **`generate-demo-config`** — PDF + Whisper transcript → `demo-builder` `config.yaml`.

### Load the plugin for local use

Point Claude Code at the `plugin/` subdirectory (not the workspace root):

```sh
claude --plugin-dir /path/to/workflow/plugin
# then, inside Claude Code:
/demo-flow:run @my-demo/   # run the full pipeline against a working folder
/demo-flow:run             # asks which folder to use (resume is automatic)
```

Run the pipeline commands themselves from the **workspace root** (`workflow/`), where `sample/`
and `models/` live.

The skills also trigger on their own when you ask for the matching task (e.g. "polish this
draft for TTS"). `/reload-plugins` picks up edits without restarting.

> **Future:** the deterministic steps (`presentation`, `build`, `tts`, `transcribe`) are good
> candidates to promote into a bundled **MCP server** (typed args, reusable from any MCP client).
> For now they run as plain commands via the orchestration above. See `plugin/.claude-plugin/plugin.json`
> `mcpServers` for where that wiring would live.

---

## Before you start

### Software prerequisites

1. `claude` (tested with Claude + Sonnet 4.6 Adaptive) or `gh copilot`
2. python (3.14)
3. docker
4. `export DEMO_BUILDER_VERSION=$(cat plugin/builder-version)` — the pinned demo-builder tag (single source of truth)
5. `brew install whisperkit-cli` (TTS voice clone support planned: https://github.com/argmaxinc/argmax-oss-swift)
6. `brew install jq`

### AI models precache, python dependencies and configuration

Environment setup and download dependencies (verified on M-chip Macs):

```shell
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install huggingface_hub mlx-audio
```

NOTE:
- `mlx-audio` is used for TTS.
- `huggingface_hub` is the source for the models (used both by mlx-audio and to download AI models).

We precache AI models because corporate policies may block downloads, and we may need to
bypass SSL verification.

Models to pre-download:
- whisperkit's transcribe large v3 model (see https://huggingface.co/argmaxinc/whisperkit-coreml/tree/main)
- Qwen3 TTS model (see https://huggingface.co/collections/Qwen/qwen3-tts)

```shell
python -c "import httpx, functools; httpx.Client = functools.partial(httpx.Client, verify=False, trust_env=True); from huggingface_hub import snapshot_download; \
snapshot_download('argmaxinc/whisperkit-coreml', local_dir='./models/openai_whisper', allow_patterns=['openai_whisper-large-v3/*']); \
snapshot_download('mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit', local_dir='./models/qwen3-tts', ignore_patterns=['*.msgpack'])"
```

### Input
1. Draft speech text
2. (optional) Screencast video

### Generate reference audio

- Create a reference voice sample (with the `Voice Memos` app) reading ~12 sec of text. See `sample/0.my_reference.txt` for sample text.
- Convert the m4a file to 24kHz Mono wav (good for TTS):

```sh
docker run --rm -v "$(pwd)/sample":/work davs87/demo-builder:$DEMO_BUILDER_VERSION ref-audio-normalize 0.my_reference.m4a
```

See:
- Input:  [reference speech](./sample/0.my_reference.txt)
- Input:  [original voice](./sample/0.my_reference.m4a)
- Output: [normalized reference voice](./sample/0.my_reference.wav)

---

## Pipeline

Run end-to-end with `/demo-flow:run`, or step through manually as below. Each step has a
**post action** — review the output before continuing.

### 1. Prepare the speech

Prettify the draft into a TTS-ready script.

- Skill:  **`generate-speech`** (auto-invoked, part of `/demo-flow:run`, or `/demo-flow:generate-speech`)
- Input:  [sample draft speech](./sample/0.draft.txt)
- Output: [prettified speech](./sample/1.speech.txt)

**Post action**: double-check the output file and clean it up if required.

### 2. Generate the presentation

We render the presentation with the `typst` utility under the hood of demo-maker. It supports
styles; predefined styles live in [`./plugin/typst-styles`](./plugin/typst-styles).

> **NOTE**: the provided style is simple — no slide-wide images or animations (so far).
> You can replace [logo](./plugin/typst-styles/logo.svg) with your company's logo and update the
> [template](./plugin/typst-styles/demo-maker.typ) with your company color scheme.

**Generate the Typst-compatible `.typ` file:**

- Skill:  **`generate-presentation`** (auto-invoked, part of `/demo-flow:run`, or `/demo-flow:generate-presentation`)
- Input:  [user speech](./sample/1.speech.txt)
- Output: [raw presentation](./sample/2.presentation.typ)

**Post action**: double-check the output file and clean it up if required.

**Render the PDF and PNG pages** (from the workspace root, `workflow/`):

```sh
docker run --rm -v "$(pwd)":/work davs87/demo-builder:$DEMO_BUILDER_VERSION presentation ./sample/2.presentation.typ --styles ./plugin/typst-styles
```

- Input:  [Typst styles](./plugin/typst-styles)
- Input:  [prepared presentation](./sample/2.presentation.typ)
- Output: [the presentation](./sample/2.presentation.pdf)
- Output: [the presentation PNG slides](./sample/slides)

**Post action**: review the presentation.

### (optional) Cleanup input screencast

This step is needed when you want to move your screencast speech to AI-based narration.

> FIXME: UNDER CONSTRUCTION

#### Cleanup screencast voice

> FIXME: UNDER CONSTRUCTION
>> FIXME: Screencast — how to clean up the JSON file finely?
> `plugin/scripts/tts.sh` can synthesize per-segment audio from a transcript JSON (resumable) if you
> prefer chunked generation over a single pass.

- [ ] extract audio from video
  - `ffmpeg -i video.mp4 -vn -ac 1 -ar 16000 output.wav`
    - ^^ should be delegated to demo-maker (ffmpeg dependency)
  - `afconvert -f caff -d LEI16 input.aac output.caf`
- [ ] transcribe audio
- [ ] cleanup and refine text
  - `./plugin/scripts/clean-transcribe-json.sh ./sample/3.????.json`
  - FIXME: don't use word-level audio length, just sentences
  - ensure there are no time gaps within segments
- [ ] dictate text
  - if dictated audio exceeds the timeframe, show an error
  - resegment — delegate to AI?
  - create a script to dictate each section
  - add a command to combine all together

## Combine all together

As part of combine-all-in-one we need to:
- generate the speech voice
- grab slides (PNG files) — already done in the `Generate the presentation` step
- ask AI to generate speech voice timestamps according to the slides
- optionally insert demo screencast
- compose the demo-maker YAML file (with AI)
- run demo maker to build the scene

### Generate the presentation speech

Assuming you already ran `source .venv/bin/activate`:

```sh
python -m mlx_audio.tts.generate \
 --model ./models/qwen3-tts \
 --text "$(cat ./sample/1.speech.txt)" \
 --ref_audio ./sample/0.my_reference.wav \
 --ref_text "$(cat ./sample/0.my_reference.txt)" \
 --output_path ./sample/output \
 --join_audio \
 --max_tokens 30000

mv ./sample/output/audio.wav ./sample/4.presentation.wav \
 && rm -rf ./sample/output
```

- Input:  [reference voice text](./sample/0.my_reference.txt)
- Input:  [reference voice](./sample/0.my_reference.wav) — see `Generate reference audio`
- Input:  [the speech](./sample/1.speech.txt) — see `Prepare the speech`
- Output: [presentation speech](./sample/4.presentation.wav)

### Generate the speech word-based transcript

We transcribe the audio back from text because we need word-level timestamps.

```shell
whisperkit-cli transcribe \
 --audio-path ./sample/4.presentation.wav \
 --model-path ./models/openai_whisper/openai_whisper-large-v3 \
 --word-timestamps \
 --report \
 --report-path ./sample/
```

Compact the JSON for downstream AI processing:

```shell
./plugin/scripts/clean-transribe-json.sh ./sample/4.presentation.json
```

- Input:  [presentation speech](./sample/4.presentation.wav)
- Output: [transcribed presentation speech](./sample/4.presentation.json)

### Generate the demo-maker configuration file

>> `FIXME: UNDER THE CONSTRUCTION`

>> TODO: combine with screencast info (if exists)
>> FIXME: ensure that voice level is the same across the presentation
>> 
>> Not sure whether we need to process screeencast part manually

- Skill:  **`generate-demo-config`** (auto-invoked, part of `/demo-flow:run`, or `/demo-flow:generate-demo-config`)
- Input:  [presentation](./sample/2.presentation.pdf)
- Input:  [user speech timestamps](./sample/4.presentation.json)
- Output: [configuration](./sample/5.demo.yaml)

**Post action**: double-check the output file and refine it if required.
- For example, the `audio_file` name may be wrong (contains unnecessary underscores).
- Consider changing `default_configuration.resolution` to the screencast video's resolution (if applicable).

### Combine all together

```sh
docker run --rm -v "$(pwd)/sample":/work davs87/demo-builder:$DEMO_BUILDER_VERSION build 5.demo.yaml -o final.mov --fps 60
```

- Input:  [configuration file](./sample/5.demo.yaml)
- Input:  resource files: slides, `4.presentation.wav`, `3.x` (custom screencast processed files)
- Output: [output video](./sample/final.mov)

---

## Other FAQs

### Image (draw.io) hints
- To highlight a specific block, make everything else opaque (e.g. to 40%):
  - Style → `Fill Opacity`, `Stroke Opacity`
  - Text → `Opacity`
