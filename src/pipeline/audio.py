"""Audio pipeline: extract segment, normalize duration."""
from __future__ import annotations

from pathlib import Path

from .. import ffmpeg_runner as ff
from ..ffprobe_utils import probe_duration
from ..ffmpeg_utils import extract_audio, change_audio_speed, trim_audio, pad_audio

SPEED_MIN, SPEED_MAX = 0.75, 1.25


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
        _silence(src, actual, target, out)
    elif method == "change_speed":
        _speed(src, actual, target, out)
    else:
        raise ValueError(f"Unknown audio normalization method: {method!r}")


def _silence(src: Path, actual: float, target: float, out: Path) -> None:
    if actual > target:
        trim_audio(out, src, target)
    else:
        pad_audio(actual, out, src, target)


def _speed(src: Path, actual: float, target: float, out: Path) -> None:
    factor = actual / target
    if not (SPEED_MIN <= factor <= SPEED_MAX):
        raise ValueError(
            f"Audio speed factor {factor:.3f}× outside [{SPEED_MIN}–{SPEED_MAX}].\n"
            f"  actual={actual:.3f}s  target={target:.3f}s\n"
            f"Use extend_with_silence or split the topic."
        )
    change_audio_speed(src, out, factor)
