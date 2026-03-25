"""
Scene builder.

For each topic:
  1. Extract audio segment
  2. Extract video segment OR create video from image (with letterbox)
  3. Compute target duration
  4. Normalize audio and video to target
  5. Mux → scene_NNN_name/scene.mp4

Caching: a .cache_key file stores a hash of all inputs.
Re-runs skip unchanged scenes automatically.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..config import DemoConfig, Topic
from .. import ffmpeg_runner as ff
from ..ffmpeg_utils import mux_audio_video
from ..ffprobe_utils import probe_duration
from ..utils import dict_hash, file_hash, format_timecode
from . import audio as a_pipe
from . import video as v_pipe


@dataclass
class SceneInfo:
    index: int
    name: str
    audio_dur: float
    video_dur: float
    target_dur: float
    norm_by: str
    audio_method: str
    video_method: str
    output: Path
    cached: bool = False


def build_all(
    config: DemoConfig,
    work_dir: Path,
    *,
    fps: int = 25,
) -> list[SceneInfo]:
    work_dir.mkdir(parents=True, exist_ok=True)

    # Resolve output resolution once (shared across all scenes)
    any_video = next(
        (config.video_file(t) for t in config.topics if t.video.fromVideo), None
    )
    resolution = v_pipe.resolve_resolution(
        config.default_configuration.resolution, any_video
    )
    ff.info(f"Output resolution: {resolution[0]}×{resolution[1]}")

    scenes: list[SceneInfo] = []
    for i, topic in enumerate(config.topics):
        ff.info(f"Scene {i + 1}/{len(config.topics)}: {topic.name!r}")
        info = _build_scene(config, topic, i, work_dir, resolution=resolution, fps=fps)
        tag = "[cached]" if info.cached else "[built]"
        ff.ok(f"{tag} {topic.name!r} → {format_timecode(info.target_dur)}")
        scenes.append(info)

    return scenes


def _build_scene(
    config: DemoConfig,
    topic: Topic,
    idx: int,
    work_dir: Path,
    *,
    resolution: tuple[int, int],
    fps: int,
) -> SceneInfo:
    norm = config.resolved_norm(topic)
    audio_src = config.audio_file(topic)
    video_src = config.video_file(topic)
    scene_dir = work_dir / f"{idx:03d}_{topic.name}"
    scene_dir.mkdir(exist_ok=True)
    final = scene_dir / "scene.mp4"

    # ── Cache check ────────────────────────────────────────────────────────
    cache_key = _make_cache_key(topic, config, audio_src, video_src, resolution, fps)
    cache_file = scene_dir / ".cache_key"
    if final.exists() and cache_file.exists() and cache_file.read_text().strip() == cache_key:
        actual_dur = probe_duration(final)
        v_dur = topic.video.fromVideo.duration if topic.video.fromVideo else topic.audio_duration
        return SceneInfo(
            index=idx, name=topic.name,
            audio_dur=topic.audio_duration, video_dur=v_dur,
            target_dur=actual_dur, norm_by=norm.by,
            audio_method=norm.audio,
            video_method=norm.video if topic.video.fromVideo else norm.image,
            output=final, cached=True,
        )

    # ── Step 1: extract audio ──────────────────────────────────────────────
    raw_audio = scene_dir / "raw_audio.aac"
    a_dur = a_pipe.extract_segment(audio_src, topic.audio[0], topic.audio[1], raw_audio)

    # ── Step 2: get raw video ──────────────────────────────────────────────
    raw_video = scene_dir / "raw_video.mp4"
    v_dur: Optional[float] = None

    if topic.video.fromVideo:
        vt = topic.video.fromVideo
        v_dur = v_pipe.extract_segment(
            video_src, vt.timing[0], vt.timing[1], raw_video,
            resolution=resolution, fps=fps,
        )

    # ── Step 3: target duration ────────────────────────────────────────────
    if norm.fixed_duration is not None:
        target = norm.fixed_duration
    elif norm.by == "audio":
        target = a_dur
    elif norm.by == "video":
        if v_dur is None:
            ff.warn(f"{topic.name!r}: by=video but source is image — using audio duration")
            target = a_dur
        else:
            target = v_dur
    else:
        target = a_dur

    # ── Step 4a: image → video (now we know target duration)
    if topic.video.fromImage:
        v_pipe.image_to_video(
            topic.video.fromImage.file, target, raw_video,
            resolution=resolution, fps=fps,
        )
        v_dur = target

    # ── Step 4b: normalize audio
    norm_audio = scene_dir / "norm_audio.aac"
    a_pipe.normalize(raw_audio, target, norm.audio, norm_audio)

    # ── Step 4c: normalize video
    norm_video = scene_dir / "norm_video.mp4"
    if topic.video.fromVideo:
        v_pipe.normalize(raw_video, target, norm.video, norm_video, fps=fps)
    else:
        shutil.copy(raw_video, norm_video)

    # ── Step 5: mux
    mux_audio_video(final, norm_audio, norm_video)

    cache_file.write_text(cache_key)

    return SceneInfo(
        index=idx, name=topic.name,
        audio_dur=a_dur, video_dur=v_dur if v_dur is not None else target,
        target_dur=target, norm_by=norm.by,
        audio_method=norm.audio,
        video_method=norm.video if topic.video.fromVideo else norm.image,
        output=final, cached=False,
    )


def _make_cache_key(
    topic: Topic,
    config: DemoConfig,
    audio_src: str,
    video_src: Optional[str],
    resolution: tuple[int, int],
    fps: int,
) -> str:
    params: dict = {
        "topic": topic.model_dump(),
        "default_norm": config.default_normalization.model_dump(),
        "resolution": resolution,
        "fps": fps,
    }
    for f in filter(None, [audio_src, video_src]):
        try:
            params[f"hash:{f}"] = file_hash(f)
        except FileNotFoundError:
            params[f"hash:{f}"] = "missing"
    if topic.video.fromImage:
        try:
            params[f"hash:{topic.video.fromImage.file}"] = file_hash(topic.video.fromImage.file)
        except FileNotFoundError:
            params[f"hash:{topic.video.fromImage.file}"] = "missing"
    return dict_hash(params)