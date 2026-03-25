import ffmpeg_runner as ff
from pathlib import Path

# Common encode flags reused across all video-output steps.
_ENC = ["-an", "-c:v", "libx264", "-preset", "fast", "-crf", "18"]

def extract_audio(src: str | Path, start: float, end: float, out: Path):
    """Cut [start, end] from src → out (aac). Returns actual duration."""
    ff.run(
        ["ffmpeg", "-y",
         "-ss", str(start), "-to", str(end),
         "-i", str(src),
         "-c:a", "aac", "-b:a", "192k", str(out)],
        desc=f"Extract audio {start:.3f}s–{end:.3f}s",
    )

def change_audio_speed(src: Path, out: Path, factor: float):
    ff.run(["ffmpeg", "-y", "-i", str(src),
            "-af", f"atempo={factor:.6f}",
            "-c:a", "aac", "-b:a", "192k", str(out)],
           desc=f"Change audio speed {factor:.3f}×")


def pad_audio(actual: float, out: Path, src: Path, target: float):
    ff.run(["ffmpeg", "-y", "-i", str(src),
            "-af", f"apad=pad_dur={target - actual:.3f}",
            "-t", str(target), "-c:a", "aac", "-b:a", "192k", str(out)],
           desc=f"Pad audio +{target - actual:.3f}s silence")


def trim_audio(out: Path, src: Path, target: float):
    ff.run(["ffmpeg", "-y", "-i", str(src),
            "-t", str(target), "-c:a", "aac", "-b:a", "192k", str(out)],
           desc=f"Trim audio to {target:.3f}s")

def concat_items_from_file(list_file: Path, merged: Path):
    ff.run(
        ["ffmpeg", "-y",
         "-f", "concat", "-safe", "0", "-i", str(list_file),
         "-c", "copy", str(merged)],
        desc="Concatenate all scenes",
    )

def extract_video(end: float, out: Path, src: str | Path, start: float, vf: str):
    ff.run(
        ["ffmpeg", "-y",
         "-ss", str(start), "-to", str(end),
         "-i", str(src),
         "-vf", vf,
         *_ENC, str(out)],
        desc=f"Extract video {start:.3f}s–{end:.3f}s",
    )

def convert_image_to_video(duration: float, fps: int, h: int, out: Path, src: str | Path, vf: str, w: int):
    ff.run(
        ["ffmpeg", "-y",
         "-loop", "1", "-framerate", str(fps),
         "-i", str(src),
         "-t", str(duration),
         "-vf", vf,
         "-pix_fmt", "yuv420p",
         *_ENC, str(out)],
        desc=f"Image → video {w}×{h} letterbox ({duration:.2f}s)",
    )

def freeze_last_video_frame(actual: float, out: Path, pad_frames: int, src: Path, target: float):
    ff.run(["ffmpeg", "-y", "-i", str(src),
            "-vf", f"tpad=stop_mode=clone:stop={pad_frames}",
            "-t", str(target), *_ENC, str(out)],
           desc=f"Freeze last frame +{target - actual:.3f}s")


def trim_video(out: Path, src: Path, target: float):
    ff.run(["ffmpeg", "-y", "-i", str(src),
            "-t", str(target), *_ENC, str(out)],
           desc=f"Trim video to {target:.3f}s")

def change_video_speed(fps: int, out: Path, pts_factor: float, real_speed: float, src: Path, target: float):
    ff.run(["ffmpeg", "-y", "-i", str(src),
            "-vf", f"setpts={pts_factor:.6f}*PTS,fps={fps}",
            "-t", str(target), *_ENC, str(out)],
           desc=f"Change video speed {real_speed:.3f}×")

def mux_audio_video(final: Path, norm_audio: Path, norm_video: Path):
    ff.run(
        ["ffmpeg", "-y",
         "-i", str(norm_video), "-i", str(norm_audio),
         "-c:v", "copy", "-c:a", "copy", "-shortest",
         str(final)],
        desc="Mux audio + video",
    )
