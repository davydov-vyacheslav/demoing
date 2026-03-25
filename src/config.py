"""
Pydantic v2 config schema for demo-builder.

New in this version:
  default_configuration.resolution: [width, height]
    Sets the output frame size used for letterboxing images.
    Falls back to the resolution of the first video file if omitted.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

from .utils import parse_timecode


# ── Types ──────────────────────────────────────────────────────────────────

AudioNormMethod = Literal["extend_with_silence", "change_speed"]
VideoNormMethod = Literal["extend_with_last_frame", "change_speed"]
ImageNormMethod = Literal["to_video_same_frame"]


# ── Sub-models ─────────────────────────────────────────────────────────────

class DefaultNorm(BaseModel):
    audio: AudioNormMethod = "extend_with_silence"
    video: VideoNormMethod = "extend_with_last_frame"
    image: ImageNormMethod = "to_video_same_frame"


class DefaultConfig(BaseModel):
    audio_file: str
    video_file: Optional[str] = None
    resolution: Optional[tuple[int, int]] = None   # [width, height] for letterbox

    @field_validator("resolution", mode="before")
    @classmethod
    def _parse_res(cls, v: Any) -> Optional[tuple[int, int]]:
        if v is None:
            return None
        if isinstance(v, (list, tuple)) and len(v) == 2:
            return int(v[0]), int(v[1])
        raise ValueError("resolution must be [width, height]")


class FromVideo(BaseModel):
    timing: tuple[float, float]
    file: Optional[str] = None

    @field_validator("timing", mode="before")
    @classmethod
    def _parse(cls, v: Any) -> tuple[float, float]:
        if not (isinstance(v, (list, tuple)) and len(v) == 2):
            raise ValueError("timing must be [start, end]")
        a = parse_timecode(str(v[0])) if isinstance(v[0], str) else float(v[0])
        b = parse_timecode(str(v[1])) if isinstance(v[1], str) else float(v[1])
        if b <= a:
            raise ValueError(f"end ({b}s) must be after start ({a}s)")
        return a, b

    @property
    def duration(self) -> float:
        return self.timing[1] - self.timing[0]


class FromImage(BaseModel):
    file: str


class VideoSource(BaseModel):
    fromVideo: Optional[FromVideo] = None
    fromImage: Optional[FromImage] = None

    @model_validator(mode="after")
    def _exactly_one(self) -> "VideoSource":
        if self.fromVideo is None and self.fromImage is None:
            raise ValueError("video requires fromVideo or fromImage")
        if self.fromVideo and self.fromImage:
            raise ValueError("video cannot have both fromVideo and fromImage")
        return self


class TopicNorm(BaseModel):
    """
    by: "audio" | "video" | "length=MM:SS.mmm"
    Optional per-source method overrides.
    """
    by: str = "audio"
    audio: Optional[AudioNormMethod] = None
    video: Optional[VideoNormMethod] = None
    image: Optional[ImageNormMethod] = None

    @field_validator("by")
    @classmethod
    def _validate_by(cls, v: str) -> str:
        v = v.strip()
        if v in ("audio", "video"):
            return v
        if v.startswith("length="):
            parse_timecode(v[7:])
            return v
        raise ValueError(f"by must be 'audio', 'video', or 'length=MM:SS.mmm'")

    @property
    def fixed_duration(self) -> Optional[float]:
        if self.by.startswith("length="):
            return parse_timecode(self.by[7:])
        return None


class Topic(BaseModel):
    name: str
    audio: tuple[float, float]
    video: VideoSource
    length_normalization: Optional[TopicNorm] = None
    audio_file: Optional[str] = None     # per-topic override

    @field_validator("audio", mode="before")
    @classmethod
    def _parse_audio(cls, v: Any) -> tuple[float, float]:
        if not (isinstance(v, (list, tuple)) and len(v) == 2):
            raise ValueError("audio must be [start, end]")
        a = parse_timecode(str(v[0])) if isinstance(v[0], str) else float(v[0])
        b = parse_timecode(str(v[1])) if isinstance(v[1], str) else float(v[1])
        if b <= a:
            raise ValueError(f"audio end ({b}s) must be after start ({a}s)")
        return a, b

    @property
    def audio_duration(self) -> float:
        return self.audio[1] - self.audio[0]


# ── Root ───────────────────────────────────────────────────────────────────

class DemoConfig(BaseModel):
    default_normalization: DefaultNorm = Field(default_factory=DefaultNorm)
    default_configuration: DefaultConfig
    topics: list[Topic]

    @model_validator(mode="after")
    def _check(self) -> "DemoConfig":
        if not self.topics:
            raise ValueError("topics must not be empty")
        return self

    # ── Accessors ──────────────────────────────────────────────────────────

    def audio_file(self, t: Topic) -> str:
        return t.audio_file or self.default_configuration.audio_file

    def video_file(self, t: Topic) -> Optional[str]:
        if t.video.fromVideo:
            return t.video.fromVideo.file or self.default_configuration.video_file
        return None

    def resolution(self) -> Optional[tuple[int, int]]:
        """Return configured resolution, or None (pipeline probes video at build time)."""
        return self.default_configuration.resolution

    def resolved_norm(self, t: Topic) -> TopicNorm:
        """Merge topic-level norm with global defaults."""
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