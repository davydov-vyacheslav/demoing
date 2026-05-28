# Demo Flow. p.2

## Achtung!

> The workflow assumes that you are using MacBook with M chip. 
> Other architecture is not supported.

## Before you start

### Software Prerequisites
1. gh copilot / claude (Tested with Claude + Sonnet 4.6 Adaptive)
2. python (3.14)
3. docker
4. `export DEMO_BUILDER_VERSION=0.1.5`
5. `brew install whisperkit-cli` (technically, in future will support tts with voice clone: https://github.com/argmaxinc/argmax-oss-swift)
6. `brew install js`

### AI Models precache, other python dependencies and configuration

Environment setup and download dependencies (verified on M-chip Macs):
```shell
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install huggingface_hub mlx-audio
```

NOTE:
- `mlx-audio` is used for TTS
- `huggingface_hub` is used as source for the models (used both by mlx-audio and to download ai models)

We need to precache AI models as there may be issues with coporate policies, and we'd need to download ones
bypass ssl verification.

Models to pre-download:
- whisperkit's transcribe large v3 model (see https://huggingface.co/argmaxinc/whisperkit-coreml/tree/main):
- Qwen3 TTS model (see https://huggingface.co/collections/Qwen/qwen3-tts)

```shell
python -c "import httpx, functools; httpx.Client = functools.partial(httpx.Client, verify=False, trust_env=True); from huggingface_hub import snapshot_download; \
snapshot_download('argmaxinc/whisperkit-coreml', local_dir='./models/openai_whisper', allow_patterns=['openai_whisper-large-v3/*']); \
snapshot_download('mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit', local_dir='./models/qwen3-tts', ignore_patterns=['*.msgpack'])"
```

### Input
1. Draft Speech text
2. (optional) Screencast video

### Generate Reference audio

- Create reference voice sample (with `Voice Memos` application) with text (~12sec). See `reference speech` for sample text
- convert m4a file to 24kHz Mono wav (good for TTS): 

```sh
docker run --rm -v "$(pwd)/sample":/work davs87/demo-builder:$DEMO_BUILDER_VERSION ref-audio-normalize 0.my_reference.m4a
```

See:
- input:  [reference speech](./sample/0.my_reference.txt)
- Input:  [original voice](./sample/0.my_reference.m4a)
- Output: [normalized reference voice](./sample/0.my_reference.wav)


## Prepare the Speech

We need to ~~make a silk purrse out of sow's ear~~ prettify our draft speech. In order to do that we propose to use prompt.
See:
- Input:  [Generate the Speech prompt](./.copilot/prompts/1. Generate Speech.md)
- Input:  [Sample draft speech](./sample/0.draft.txt)
- Output: [Prettified speech](./sample/1.speech.txt)
**Post Action**: Please double-check output file and clean up it if required.

## Generate the presentation

In order to generate the presentation, we will use `typst` utility underhood the demo-maker. 
It supports styles. There prepared predefined styles are located at ./typst-styles folder.

**NOTE**: the style provided is quite simple one. No slide-wide image or animations (so far)

**NOTE**: you can replace [logo](./typst-styles/logo.svg) with your company's logo, along with updating
the [template](./typst-styles/demo-maker.typ) with your company color schema

### Generate Typst-compatible typ file

Delegate AI to prepare presentation for you.
See:
- Input:  [Generate Typst presentation prompt](./.copilot/prompts/2. Generate Typst presentation.md)
- Input:  [User speech](./sample/1.speech.txt)
- Output: [Raw presentation](./sample/2.presentation.typ)
**Post Action**: Please double-check output file and clean up it if required.

### Generate Presentation PDF file and set of PNG pages

Assuming we are in the root of current project:

```sh
docker run --rm -v "$(pwd)":/work davs87/demo-builder:$DEMO_BUILDER_VERSION presentation ./workflow/sample/2.presentation.typ --styles ./workflow/typst-styles
```

See:
- Input:  [Typst styles](./typst-styles)
- Input:  [Prepared speech](./sample/2.presentation.typ)
- Output: [The presentation](./sample/2.presentation.pdf)
- Output: [The presentation png slides](./sample/slides)
**Post Action**: Please review the presentation

## (optional) Cleanup input screencast

This step is needed when you want to move your screencast speech to AI based

`FIXME: UNDER THE CONSTRUCTION`

### Cleanup screencast voice

`FIXME: UNDER THE CONSTRUCTION`
>> FIXME: Screencast. how to cleanup the json file finely?

- [ ] extract audio from video
  - `ffmpeg -i video.mp4 -vn -ac 1 -ar 16000 output.wav`
    - ^^ need to delegate to demo-maker oO (ffmpeg dependency)
  - `afconvert -f caff -d LEI16 input.aac output.caf`
- [ ] transcribe audio
- [ ] cleanup and refine text
  - `./scripts/clean-transcribe-json.sh ./sample/3.????.json`
  - FIXME: don't use words audio length. just sentences; 
  - ensure that there are no time spaces within segments
- [ ] dictate text
  - if dictated audio exceed timeframe - show error
  - resegment - delegate to AI ??
  - create script to dictate each section
  - add command to combine all together



## Combine all together

As part of combine all-in-one we need:
- generate speech voice
- grab slides (PNG files) - already done in `Generate Presentation` section
- ask AI to generate speech voice timestamps according to the slides
- optionally - insert demo screencast
- compose demo-maker YAML file (with AI)
- run demo maker to build the scene

### Generate presentation speech

Assuming you're already did `source .venv/bin/activate`.

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

See:
- input:  [reference voice test](./sample/0.my_reference.txt)
- input:  [reference voice](./sample/0.my_reference.wav) . See `Generate Reference audio` section how to generate one
- input:  [the speech](./sample/1.speech.txt) . See `Prepare the Speech` section
- output: [presentation speech](./sample/4.presentation.wav)

### Generate speech word-based transcribe

We need to transcribe audio back from the text beacuse we need words timestampts. 

```shell
whisperkit-cli transcribe \
 --audio-path ./sample/4.presentation.wav \
 --model-path ./models/openai_whisper/openai_whisper-large-v3 \
 --word-timestamps \
 --report \
 --report-path ./sample/
```

Cleanup json to make it more compact for further AI processing
```shell
./scripts/clean-transcribe-json.sh ./sample/4.presentation.json
```

See:
- input:  [presentation speech](./sample/4.presentation.wav)
- output: [transcribed presentation speech](./sample/4.presentation.json)

### Generate demo-maker configuration file

`FIXME: UNDER THE CONSTRUCTION`

> TODO: combine with screencast info (if exists)
> FIXME: ensure that voice level is the same across the presentation
> 
> Not sure whether we need to process screeencast part manually


Delegate AI to prepare the file for you.
See:
- Input:  [Generate Demo-Maker Configuration prompt](./.copilot/prompts/5. Generate Demo-Maker Configuration.md)
- Input:  [Presentation](./sample/2.presentation.pdf)
- Input:  [User speech timestamps](./sample/4.presentation.json)
- Output: [Configuration](./sample/5.demo.yaml)

**Post Action**: Please double-check output file and refine it if required.
- For example, `audio_file` name may be wrong (contains unnecessary underscores)
- Please consider to change `default_configuration.resolution` to screencast video's resolution (if applicable)


### Combine all together

See:
- Input:  [Configuration file](./sample/5.demo.yaml)
- Input:  Resource files: slides, 4.presentation.wav, 3.x (custom screencast processed files)
- Output: [Output Video](./sample/final.mov)

```sh
docker run --rm -v "$(pwd)/sample":/work davs87/demo-builder:$DEMO_BUILDER_VERSION build 5.demo.yaml -o final.mov --fps 60
```


## Other FAQs

### Image (draw io) hints:
- to highlight specific block we can opaque everything else (to 40%:
	- Style -> `Fill Opacity`, `Stroke Opacity`
	- Text -> `Opacity`)



