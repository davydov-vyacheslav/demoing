from . import ffmpeg_runner as ff
from pathlib import Path

# Common encode flags reused across all video-output steps.
_VIDEO = ["-an", "-c:v", "libx264", "-profile:v", "main", "-preset", "fast", "-crf", "18"]
_AUDIO = ["-c:a", "aac", "-b:a", "128k", "-profile:a", "aac_low", "-ar", "48000", "-ac", "1"]

def extract_audio(src: str | Path, start: float, end: float, out: Path):
    """Cut [start, end] from src → out (aac). Returns actual duration."""
    ff.run(
        ["ffmpeg", "-y",
         "-ss", str(start), "-to", str(end),
         "-i", str(src),
         *_AUDIO, str(out)],
        desc=f"Extract audio {start:.3f}s–{end:.3f}s",
    )

def pad_audio(actual: float, out: Path, src: Path, target: float):
    ff.run(["ffmpeg", "-y", "-i", str(src),
            "-af", f"apad=pad_dur={target - actual:.3f}",
            "-t", str(target), *_AUDIO, str(out)],
           desc=f"Pad audio +{target - actual:.3f}s silence")

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
         *_VIDEO, str(out)],
        desc=f"Extract video {start:.3f}s–{end:.3f}s",
    )

def convert_image_to_video(duration: float, fps: int, h: int, out: Path, src: str | Path, vf: str, w: int):
    ff.run(
        ["ffmpeg", "-y",
         "-loop", "1", "-framerate", str(fps),
         "-i", str(src),
         "-t", str(duration),
         "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
         "-vf", vf,
         "-pix_fmt", "yuv420p",
         *_VIDEO, str(out)],
        desc=f"Image → video {w}×{h} letterbox ({duration:.2f}s)",
    )

def mux_audio_video(final: Path, norm_audio: Path, norm_video: Path):
    ff.run(
        ["ffmpeg", "-y",
         "-i", str(norm_video), "-i", str(norm_audio),
         "-map", "0:v", "-map", "1:a", "-c", "copy", "-shortest",
         str(final)],
        desc="Mux audio + video",
    )

def normalize_audio_wav(src: Path, out: Path, *, sample_rate: int = 24000) -> None:
    """Convert audio to mono WAV at given sample rate (s16).
    Suitable for preparing TTS reference audio (mlx-audio, Qwen3-TTS, etc.).
    """
    ff.run(
        ["ffmpeg", "-y", "-i", str(src),
         "-af", f"aformat=channel_layouts=mono,aresample={sample_rate}",
         "-ar", str(sample_rate),
         "-sample_fmt", "s16",
         str(out)],
        desc=f"Normalize audio → mono s16 {sample_rate}Hz WAV",
    )