"""
Pydantic v2 config schema for demo-builder.

Topic structure:

  - name: intro
    audioSource:
      file: audio.m4a          # optional — falls back to default_configuration.audio_file
      timing: ["00:00.000", "00:09.000"]
    video:
      file: screen.mp4         # optional — falls back to default_configuration.video_file
      timing: ["00:00.000", "00:08.000"]
      type: video              # video (default) | image
    length_normalization:
      by: audio                # audio | video | fixed
      length: "00:10.000"      # required when by=fixed

Resolution rules:
  - Optional when at least one topic uses a video source (probed at build time).
  - Required when every topic uses a static image (no video to probe from).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from .utils import parse_timecode


# ── Norm method aliases ────────────────────────────────────────────────────

AudioNormMethod = Literal["extend_with_silence", "change_speed"]
VideoNormMethod = Literal["extend_with_last_frame", "change_speed"]
ImageNormMethod = Literal["to_video_same_frame"]


# ── Default norm / config ──────────────────────────────────────────────────

class DefaultNorm(BaseModel):
    audio: AudioNormMethod = "extend_with_silence"
    video: VideoNormMethod = "extend_with_last_frame"
    image: ImageNormMethod = "to_video_same_frame"


class DefaultConfig(BaseModel):
    audio_file: str
    video_file: Optional[str] = None
    resolution: Optional[tuple[int, int]] = None  # [width, height]; see module docstring

    @field_validator("resolution", mode="before")
    @classmethod
    def _parse_resolution(cls, v: Any) -> Optional[tuple[int, int]]:
        if v is None:
            return None
        if isinstance(v, (list, tuple)) and len(v) == 2:
            return int(v[0]), int(v[1])
        raise ValueError("resolution must be [width, height]")


# ── Shared helpers ─────────────────────────────────────────────────────────

def _parse_timing(v: Any, *, label: str = "timing") -> tuple[float, float]:
    """Parse a [start, end] timecode pair into float seconds."""
    if not (isinstance(v, (list, tuple)) and len(v) == 2):
        raise ValueError(f"{label} must be [start, end]")
    a = parse_timecode(str(v[0])) if isinstance(v[0], str) else float(v[0])
    b = parse_timecode(str(v[1])) if isinstance(v[1], str) else float(v[1])
    if b <= a:
        raise ValueError(f"{label}: end ({b}s) must be after start ({a}s)")
    return a, b


# ── Audio / video sources ──────────────────────────────────────────────────

class AudioSource(BaseModel):
    """Audio segment for a topic."""
    file: Optional[str] = None      # overrides default_configuration.audio_file
    timing: tuple[float, float]     # [start, end] in seconds

    @field_validator("timing", mode="before")
    @classmethod
    def _parse(cls, v: Any) -> tuple[float, float]:
        return _parse_timing(v, label="audio.timing")

    @property
    def duration(self) -> float:
        return self.timing[1] - self.timing[0]


class VideoSource(BaseModel):
    """
    Video clip or static image for a topic.

    type=video (default): extract a clip from a video file.
      - timing: required — [start, end] within the video file
      - file:   optional — falls back to default_configuration.video_file

    type=image: use a static image (PNG/JPG), letterboxed to output resolution.
      - file:   required — path to the image
      - timing: not used
    """
    file: Optional[str] = None
    timing: Optional[tuple[float, float]] = None
    typeOf: Literal["video", "image"] = "video"

    @field_validator("timing", mode="before")
    @classmethod
    def _parse(cls, v: Any) -> Optional[tuple[float, float]]:
        if v is None:
            return None
        return _parse_timing(v, label="video.timing")

    @model_validator(mode="after")
    def _validate_constraints(self) -> "VideoSource":
        if self.typeOf == "video" and self.timing is None:
            raise ValueError("video.timing is required when typeOf=video")
        if self.typeOf == "image" and self.file is None:
            raise ValueError("video.file is required when typeOf=image")
        return self

    @property
    def duration(self) -> Optional[float]:
        """Duration of the video clip; None for image sources."""
        if self.timing is not None:
            return self.timing[1] - self.timing[0]
        return None


# ── Normalization ──────────────────────────────────────────────────────────

class TopicNorm(BaseModel):
    """Duration reconciliation settings for one topic."""
    by: Literal["audio", "video", "fixed"] = "audio"
    length: Optional[float] = None      # target duration; required when by=fixed
    audio: Optional[AudioNormMethod] = None
    video: Optional[VideoNormMethod] = None
    image: Optional[ImageNormMethod] = None

    @field_validator("length", mode="before")
    @classmethod
    def _parse_length(cls, v: Any) -> Optional[float]:
        if v is None:
            return None
        if isinstance(v, str):
            return parse_timecode(v)
        return float(v)

    @model_validator(mode="after")
    def _validate_fixed(self) -> "TopicNorm":
        if self.by == "fixed" and self.length is None:
            raise ValueError("length_normalization.length is required when by=fixed")
        return self

    @property
    def fixed_duration(self) -> Optional[float]:
        return self.length if self.by == "fixed" else None


# ── Topic ──────────────────────────────────────────────────────────────────

class Topic(BaseModel):
    name: str
    audio: AudioSource
    video: VideoSource
    length_normalization: Optional[TopicNorm] = None

    @property
    def audio_duration(self) -> float:
        return self.audio.duration


# ── Root config ────────────────────────────────────────────────────────────

class DemoConfig(BaseModel):
    default_normalization: DefaultNorm = Field(default_factory=DefaultNorm)
    default_configuration: DefaultConfig
    topics: list[Topic]

    @model_validator(mode="after")
    def _validate(self) -> "DemoConfig":
        if not self.topics:
            raise ValueError("topics must not be empty")

        # Resolution must be explicit when there is no video file to probe.
        all_images = all(t.video.typeOf == "image" for t in self.topics)
        if all_images and self.default_configuration.resolution is None:
            raise ValueError(
                "default_configuration.resolution is required when all topics use "
                "images — there is no video file to probe the resolution from."
            )
        return self

    # ── Accessors ──────────────────────────────────────────────────────────

    def audio_file(self, t: Topic) -> str:
        return t.audio.file or self.default_configuration.audio_file

    def video_file(self, t: Topic) -> Optional[str]:
        if t.video.typeOf == "video":
            return t.video.file or self.default_configuration.video_file
        return None

    def resolution(self) -> Optional[tuple[int, int]]:
        """Return configured resolution, or None (pipeline probes video at build time)."""
        return self.default_configuration.resolution

    def resolved_norm(self, t: Topic) -> TopicNorm:
        """Merge topic-level norm overrides with global defaults."""
        tn = t.length_normalization or TopicNorm()
        d = self.default_normalization
        return tn.model_copy(update={
            "audio": tn.audio or d.audio,
            "video": tn.video or d.video,
            "image": tn.image or d.image,
        })


# ── Loader ─────────────────────────────────────────────────────────────────

def load_config(path: str | Path) -> DemoConfig:
    with open(path) as f:
        raw = yaml.safe_load(f)
    return DemoConfig.model_validate(raw)