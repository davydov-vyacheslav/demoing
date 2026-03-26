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

RUN apk add --no-cache ffmpeg poppler-utils

COPY --from=builder /dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

WORKDIR /work
ENTRYPOINT ["demo"]
CMD ["--help"]