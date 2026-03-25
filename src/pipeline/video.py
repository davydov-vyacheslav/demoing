"""
Video pipeline: extract segment, image→video with letterbox, normalize duration.

Letterbox / pillarbox:
  Images are scaled to fit within the target resolution while preserving their
  aspect ratio. Empty space is filled with black.

  ffmpeg filter:
    scale=W:H:force_original_aspect_ratio=decrease,
    pad=W:H:(ow-iw)/2:(oh-ih)/2:black

  This means:
    - A 4:3 slide on a 16:9 canvas gets black bars on left & right (pillarbox).
    - A 16:9 slide on a 4:3 canvas gets black bars top & bottom (letterbox).
    - An already-matching aspect ratio gets no bars at all.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from .. import ffmpeg_runner as ff
from ..ffmpeg_utils import extract_video, convert_image_to_video, trim_video, freeze_last_video_frame, \
    change_video_speed
from ..ffprobe_utils import probe_duration, probe_video_resolution

SPEED_MIN, SPEED_MAX = 0.5, 2.0

def extract_segment(
    src: str | Path,
    start: float,
    end: float,
    out: Path,
    *,
    resolution: Optional[tuple[int, int]] = None,
    fps: int = 25,
) -> float:
    """
    Cut [start, end] from src → out.mp4 (video only, no audio).
    If resolution is given, scale+pad to that size (letterbox).
    Returns actual output duration.
    """
    ff.ensure_dir(out)
    vf = _letterbox_filter(resolution, fps) if resolution else f"fps={fps}"
    extract_video(end, out, src, start, vf)
    return probe_duration(out)



def image_to_video(
    src: str | Path,
    duration: float,
    out: Path,
    *,
    resolution: tuple[int, int],
    fps: int = 25,
) -> None:
    """
    Create a video clip from a static image (PNG/JPG/etc.).

    The image is scaled to fill resolution while preserving aspect ratio;
    remaining space is padded with black (letterbox / pillarbox).
    """
    ff.ensure_dir(out)
    w, h = resolution
    vf = _letterbox_filter(resolution, fps)
    convert_image_to_video(duration, fps, h, out, src, vf, w)


def normalize(
    src: Path,
    target: float,
    method: str,
    out: Path,
    *,
    fps: int = 25,
) -> None:
    """Adjust video clip to exactly target seconds."""
    ff.ensure_dir(out)
    actual = probe_duration(src)

    if abs(target - actual) < 0.04:
        shutil.copy(src, out)
        return

    if method == "extend_with_last_frame":
        _freeze(src, actual, target, out, fps)
    elif method == "change_speed":
        _speed(src, actual, target, out, fps)
    else:
        raise ValueError(f"Unknown video normalization method: {method!r}")


def _freeze(src: Path, actual: float, target: float, out: Path, fps: int) -> None:
    if actual > target:
        trim_video(out, src, target)
    else:
        pad_frames = int((target - actual) * fps) + 1
        freeze_last_video_frame(actual, out, pad_frames, src, target)


def _speed(src: Path, actual: float, target: float, out: Path, fps: int) -> None:
    real_speed = target / actual   # <1 = slow down, >1 = speed up
    pts_factor = actual / target   # setpts factor (inverse of speed)
    if not (SPEED_MIN <= real_speed <= SPEED_MAX):
        raise ValueError(
            f"Video speed {real_speed:.3f}× outside [{SPEED_MIN}–{SPEED_MAX}].\n"
            f"  actual={actual:.3f}s  target={target:.3f}s\n"
            f"Use extend_with_last_frame or split the topic."
        )
    change_video_speed(fps, out, pts_factor, real_speed, src, target)


def _letterbox_filter(resolution: tuple[int, int], fps: int) -> str:
    """
    Build a vf filter string that scales src to fit resolution with black padding.

    scale=W:H:force_original_aspect_ratio=decrease   — fit within bounds
    pad=W:H:(ow-iw)/2:(oh-ih)/2:black               — center + fill black
    fps=N                                             — ensure frame rate
    """
    w, h = resolution
    # Ensure even dimensions (required by yuv420p / libx264)
    w = w - (w % 2)
    h = h - (h % 2)
    return (
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,"
        f"fps={fps}"
    )


def resolve_resolution(
    cfg_resolution: Optional[tuple[int, int]],
    video_file: Optional[str],
) -> tuple[int, int]:
    """
    Determine output resolution:
      1. Use explicit config resolution if provided.
      2. Fall back to probing the first video file.
      3. Default to 1920×1080 if neither is available.
    """
    if cfg_resolution:
        return cfg_resolution
    if video_file:
        try:
            return probe_video_resolution(video_file)
        except Exception:
            pass
    return (1920, 1080)