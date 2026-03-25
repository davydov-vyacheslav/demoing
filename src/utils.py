"""Utility helpers: timecode parsing, ffprobe, file hashing."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


# ── Timecode

_TC_RE = re.compile(r"^(?:(?P<h>\d+):)?(?P<m>\d{1,2}):(?P<s>\d{1,2}(?:\.\d+)?)$")


def parse_timecode(value: str) -> float:
    """Parse MM:SS.mmm or HH:MM:SS.mmm → float seconds."""
    m = _TC_RE.match(value.strip())
    if not m:
        raise ValueError(f"Invalid timecode {value!r} — expected MM:SS.mmm")
    return (float(m.group("h") or 0) * 3600
            + float(m.group("m")) * 60
            + float(m.group("s")))


def format_timecode(s: float) -> str:
    """Float seconds → MM:SS.mmm string."""
    ms = round(s * 1000)
    return f"{ms // 60000:02d}:{ms // 1000 % 60:02d}.{ms % 1000:03d}"


# ── Hashing (scene cache)

def file_hash(path: str | Path, max_bytes: int = 4 << 20) -> str:
    """SHA-1 of first max_bytes of a file (fast cache key)."""
    h = hashlib.sha1()
    with open(path, "rb") as f:
        data = f.read(max_bytes)
        h.update(data)
    return h.hexdigest()


def dict_hash(d: dict) -> str:
    """SHA-1 of a JSON-serialisable dict."""
    raw = json.dumps(d, sort_keys=True, default=str).encode()
    return hashlib.sha1(raw).hexdigest()