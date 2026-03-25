import subprocess
from pathlib import Path
import json

def probe_duration(path: str | Path) -> float:
    """Return media duration in seconds via ffprobe."""
    out = subprocess.check_output(
        ["ffprobe", "-v", "error",
         "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1",
         str(path)],
        stderr=subprocess.DEVNULL,
    )
    return float(out.strip())


def probe_video_resolution(path: str | Path) -> tuple[int, int]:
    """Return (width, height) of first video stream."""
    out = subprocess.check_output(
        ["ffprobe", "-v", "error",
         "-select_streams", "v:0",
         "-show_entries", "stream=width,height",
         "-of", "json",
         str(path)],
        stderr=subprocess.DEVNULL,
    )
    s = json.loads(out)["streams"][0]
    return s["width"], s["height"]
