# Stage 1: build wheel
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt pyproject.toml README.md ./
COPY src/ src/

RUN pip install --upgrade pip \
 && pip install --no-cache-dir build \
 && python -m build --wheel --outdir /dist


# Stage 2: runtime
FROM python:3.12-slim

# ffmpeg + poppler (pdftoppm for PDF splitting)
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install the wheel built in stage 1
COPY --from=builder /dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

# Working directory — users mount their project here
WORKDIR /work

ENTRYPOINT ["demo"]
CMD ["--help"]