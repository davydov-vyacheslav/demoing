# demoing
ffmpeg-based MovieMaker-replacement tool to prepare pre-recorder demo based on raw data

Assemble demo videos from audio recordings, screen recordings, and presentation slides.
No video editors — just **Python + ffmpeg**.

 
## Build (Docker)

The application wil be build (and push to Docker Hub) automatically on push the tag in the repo.

Build locally:
```bash
docker build -t demo-builder .
```
 
Or with plain `docker run`:
 
```bash
docker run --rm -v "$(pwd)":/work demo-builder build config.yaml -o final.mp4
docker run --rm -v "$(pwd)":/work demo-builder pdf-split slides.pdf -o slides/
```

Docker Hub PAT token url: https://app.docker.com/accounts/davs87/settings/personal-access-tokens/

---

## Commands

### `demo build`
 
```bash
demo build config.yaml -o final.mp4
```

### `demo pdf-split`

Splits pdf into image files

```bash
# Docker
demo pdf-split sample/sample.pdf -o sample/slides --dpi 150 --format png --prefix slide

# Local
./.venv/bin/python -m src.cli pdf-split sample/sample.pdf -o sample/slides --dpi 150 --format png --prefix slide
```
 
Uses `pdftoppm` underhood

## Config reference

see [the sample](./sample/sample.yaml) 
