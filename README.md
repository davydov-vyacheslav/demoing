# demoing
ffmpeg-based MovieMaker-replacement tool to prepare pre-recorder demo based on raw data

Assemble demo videos from audio recordings, screen recordings, and presentation slides.
No video editors — just **Python + ffmpeg**.

This project consider the workflow to have pre-recorded demo (screencast) based on some inputs
 
## Build (Docker)

The application wil be build (and push to Docker Hub) automatically on push the tag in the repo.

Build locally:
```bash
docker build -t davs87/demo-builder .
```
 
Or with plain `docker run`:
 
```bash
docker run --rm -v "$(pwd)":/work davs87/demo-builder build config.yaml -o final.mov
docker run --rm -v "$(pwd)":/work davs87/demo-builder ref-audio-normalize my_reference.m4a
docker run --rm -v "$(pwd)":/work davs87/demo-builder presentation presentation.typ --styles styles
```

You may check commands samples in workflow sample [readme file](./workflow/README.md)

Docker Hub PAT token url: https://app.docker.com/accounts/davs87/settings/personal-access-tokens/
