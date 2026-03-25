# demoing
ffmpeg-based MovieMaker-replacement tool to prepare pre-recorder demo based on raw data

Assemble demo videos from audio recordings, screen recordings, and presentation slides.
No video editors — just **Python + ffmpeg**.
 
Images are automatically **letterboxed / pillarboxed** to fit the output resolution,
filling empty space with black.
 
---
 
## Prerequisites (without Docker)
 
- Python 3.11+
- `ffmpeg` and `ffprobe` on PATH
- `pdftoppm` (poppler) for PDF splitting — optional
- `pip install -e .`
 
## Docker (recommended)
 
Everything — Python, ffmpeg, poppler — is bundled in the image.
 
```bash
# Build the image once
docker compose build
 
# Generate a sample project in ./sample/
docker compose run --rm demo generate-sample sample
 
# Build the sample
cd sample
docker compose -f ../docker-compose.yml run --rm demo build config.yaml -o demo.mp4
```
 
Or with plain `docker run`:
 
```bash
docker build -t demo-builder .
 
# Run any command, mounting your project directory
docker run --rm -v "$(pwd)":/work demo-builder build config.yaml -o final.mp4
docker run --rm -v "$(pwd)":/work demo-builder pdf-split slides.pdf -o slides/
docker run --rm -v "$(pwd)":/work demo-builder generate-sample
```
 
---
 
## Commands
 
### `demo build`
 
```bash
demo build config.yaml -o final.mp4
demo build config.yaml -o final.mp4 --fade 0.3        # audio fades between scenes
demo build config.yaml -o final.mp4 --no-loudnorm      # skip loudness normalization
demo build config.yaml -o final.mp4 --log ffmpeg.log   # capture ffmpeg output
demo build config.yaml -o final.mp4 --keep-temp        # keep intermediate files
demo build config.yaml -o final.mp4 --no-cache         # rebuild all scenes
demo build config.yaml -o final.mp4 --verbose          # show ffmpeg stderr live
```
 
Prints a timing report before building, warns on speed limit violations.
 
### `demo pdf-split`
 
```bash
demo pdf-split slides.pdf -o slides/ --dpi 150
demo pdf-split slides.pdf -o slides/ --format jpg
```
 
Uses `pdftoppm` (best quality) → ImageMagick → ffmpeg as fallback.
 
### `demo tts`
 
```bash
demo tts script.txt -o audio.m4a --engine edge-tts --voice en-US-AriaNeural
demo tts script.txt -o audio.m4a --engine openai    --voice alloy
```
 
Supports pause markers:
```
Hello, welcome. [pause:1.5] Let me show you the first feature.
```
 
### `demo generate-sample`
 
```bash
demo generate-sample ./my-sample
cd my-sample && demo build config.yaml -o demo.mp4
```
 
Creates a fully self-contained sample with synthetic audio, video, and slides
at three different aspect ratios to demonstrate letterboxing.
 
---
 
## Config reference
 
```yaml
default_normalization:
  audio: extend_with_silence     # extend_with_silence | change_speed (0.75×–1.25×)
  video: extend_with_last_frame  # extend_with_last_frame | change_speed (0.5×–2.0×)
  image: to_video_same_frame
 
default_configuration:
  audio_file: audio.m4a
  video_file: screen.mp4
  resolution: [1920, 1080]       # output size; images are letterboxed to fit
                                 # omit to auto-detect from video_file
 
topics:
 
  - name: intro
    audio: ["00:00.000", "00:30.250"]   # [start, end] into audio_file
    video:
      fromVideo:
        timing: ["00:00.000", "00:20.000"]
        # file: other_recording.mkv    # optional per-topic video file
    length_normalization:
      by: audio                  # audio | video | length=MM:SS.mmm
      # video: change_speed      # optional per-topic method override
 
  - name: slide_demo
    audio: ["00:30.250", "01:05.000"]
    video:
      fromImage:
        file: slides/slide-0001.png    # letterboxed to resolution above
    length_normalization:
      by: audio
 
  - name: fixed_length
    audio: ["01:05.000", "02:00.000"]
    video:
      fromVideo:
        timing: ["00:20.000", "01:30.000"]
    length_normalization:
      by: length=01:10.000       # both audio and video adjust to this
```
 
### Letterboxing
 
When `fromImage` is used, the image is scaled to fit within `resolution`
while preserving its aspect ratio. Remaining space is filled with black:
 
```
resolution: [1920, 1080]   (16:9)
 
  4:3 source  → pillarbox   [██ image ██]   (black bars left/right)
  1:1 source  → pillarbox   [███ image ███]
  2:1 source  → letterbox   [   image   ]   (black bars top/bottom)
                             [           ]
  16:9 source → no bars     [ full frame ]
```
 
The same filter is applied to extracted video segments when `resolution` is set,
ensuring all scenes have identical dimensions even if source files differ.
 
---
 
## Project structure
 
```
demo_builder/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── config.schema.json
└── demo_builder/
    ├── cli.py              # CLI commands
    ├── config.py           # Pydantic schema + YAML loader
    ├── ffmpeg_runner.py    # ffmpeg subprocess wrapper
    ├── sample.py           # sample project generator
    ├── utils.py            # timecodes, ffprobe, hashing
    └── pipeline/
        ├── audio.py        # extract + normalize audio
        ├── video.py        # extract + letterbox + normalize video
        ├── scene.py        # assemble one topic → scene.mp4
        └── concat.py       # concat + fades + loudnorm + chapters
```