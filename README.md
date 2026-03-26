# demoing
ffmpeg-based MovieMaker-replacement tool to prepare pre-recorder demo based on raw data

Assemble demo videos from audio recordings, screen recordings, and presentation slides.
No video editors — just **Python + ffmpeg**.
 
Images are automatically **letterboxed / pillarboxed** to fit the output resolution,
filling empty space with black.

 
## Prerequisites (without Docker)
 
- Python 3.11+
- `ffmpeg` and `ffprobe` on PATH
- `pdftoppm` (https://github.com/UB-Mannheim/zotero-ocr/wiki/Install-pdftoppm) for PDF splitting — optional
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
```

Prints a timing report before building, warns on speed limit violations.

### `demo pdf-split`
 
```bash
# Docker
demo pdf-split sample/sample.pdf -o sample/slides --dpi 150 --format png --prefix slide

# Local
./.venv/bin/python -m src.cli pdf-split sample/sample.pdf -o sample/slides --dpi 150 --format png --prefix slide
```
 
Uses `pdftoppm` underhood
 
## Config reference

see [the sample](./sample/sample.yaml) 

## Letterboxing
 
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
