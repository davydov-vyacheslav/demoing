"""Concatenation: merge scenes."""
from __future__ import annotations

from pathlib import Path

from .scene import SceneInfo
from ..ffmpeg_utils import concat_items_from_file


def concatenate(
    scenes: list[SceneInfo],
    output: Path,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = output.parent / "_concat_tmp"
    tmp_dir.mkdir(exist_ok=True)

    paths = [s.output for s in scenes]

    list_file = tmp_dir / "concat.txt"
    list_file.write_text(
        "\n".join(f"file '{p.resolve()}'" for p in paths)
    )
    merged = tmp_dir / output
    concat_items_from_file(list_file, merged)

# FIXME
#    shutil.rmtree(tmp_dir, ignore_errors=True)
