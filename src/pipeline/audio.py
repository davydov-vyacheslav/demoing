"""Audio pipeline: extract segment, normalize duration."""
from __future__ import annotations

from pathlib import Path

from .. import ffmpeg_runner as ff
from ..ffprobe_utils import probe_duration
from ..ffmpeg_utils import extract_audio, pad_audio


def extract_segment(src: str | Path, start: float, end: float, out: Path) -> float:
    """Cut [start, end] from src → out (aac). Returns actual duration."""
    ff.ensure_dir(out)
    extract_audio(src, start, end, out)
    return probe_duration(out)


def normalize(src: Path, target: float, method: str, out: Path) -> None:
    """Adjust audio clip to exactly target seconds."""
    ff.ensure_dir(out)
    actual = probe_duration(src)

    if abs(target - actual) < 0.01:
        import shutil; shutil.copy(src, out)
        return

    if method == "extend_with_silence":
        pad_audio(actual, out, src, target)
    else:
        raise ValueError(f"Unknown audio normalization method: {method!r}")

