# Stage 1: build wheel
FROM python:3.12-alpine AS builder

WORKDIR /build
COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --upgrade pip \
 && pip install --no-cache-dir build \
 && python -m build --wheel --outdir /dist


# Stage 2: runtime
FROM python:3.12-alpine

RUN apk add --no-cache ffmpeg7 typst ttf-liberation \
    && wget -q -O /usr/share/fonts/NotoColorEmoji.ttf \
       https://github.com/googlefonts/noto-emoji/raw/main/fonts/NotoColorEmoji.ttf \
    && fc-cache -f

COPY --from=builder /dist/*.whl /tmp/

RUN pip install --no-cache-dir --no-compile /tmp/*.whl \
 && rm /tmp/*.whl \
 && pip uninstall -y pip setuptools wheel \
 && find /usr/local/lib/python3.12 -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null; \
    find /usr/local/lib/python3.12 -name '*.pyc' -delete 2>/dev/null; true

WORKDIR /work
VOLUME ["/work"]
ENTRYPOINT ["demo"]
CMD ["--help"]