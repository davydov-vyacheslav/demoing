"""
demo-builder CLI

Commands:
  build            Build final video from a config file
  pdf-split        Split PDF into per-page PNG images
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import click

from .config import load_config
from . import ffmpeg_runner as ff
from .ffmpeg_runner import FFmpegError
from .utils import format_timecode
from .pipeline.scene import build_all
from .pipeline.concat import concatenate


# ── CLI group

@click.group()
def cli():
    """Assemble demo videos from audio, screen recordings, and slides."""


# ── build

@cli.command()
@click.argument("config_file", type=click.Path(exists=True, dir_okay=False))
@click.option("-o", "--output",      default="final.mp4",   show_default=True)
@click.option("--work-dir",          default=".demo_build", show_default=True)
@click.option("--verbose",           is_flag=True,  help="Show ffmpeg output")
@click.option("--log",               default=None,  help="Write ffmpeg log to file")
@click.option("--keep-temp",         is_flag=True,  help="Keep intermediate files")
@click.option("--no-cache",          is_flag=True,  help="Rebuild all scenes")
@click.option("--fps",               default=25,    show_default=True)
def build(config_file, output, work_dir, verbose, log, keep_temp, no_cache, fps):
    """Build the final demo video from CONFIG_FILE."""
    ff.configure(verbose=verbose, log_file=log)

    try:
        config = load_config(config_file)
    except Exception as e:
        ff.error(f"Config error: {e}")
        sys.exit(1)

    # Always print validation table before building
    _print_validation(config)

    work = Path(work_dir)
    if no_cache and work.exists():
        shutil.rmtree(work)

    try:
        scenes = build_all(config, work, fps=fps)
    except (FFmpegError, ValueError) as e:
        ff.error(str(e))
        sys.exit(1)

    ff.info("Concatenating scenes…")
    try:
        concatenate(scenes, Path(output))
    except (FFmpegError, ValueError) as e:
        ff.error(str(e))
        sys.exit(1)

    total = sum(s.target_dur for s in scenes)
    ff.ok(f"Done → {output}  ({format_timecode(total)} total)")

    if not keep_temp:
        shutil.rmtree(work, ignore_errors=True)


# ── validation table (also called inside build)

def _print_validation(config) -> None:
    B, R, Y, C, D = "\033[1m", "\033[0m", "\033[33m", "\033[36m", "\033[2m"
    print(f"\n  {B}{'#':<4}{'Topic':<22}{'Audio':>8}{'Video':>9}{'Target':>9}  {'By':<7} Methods{R}")
    print("  " + "─" * 72)
    total = 0.0
    warnings: list[str] = []
    for i, t in enumerate(config.topics):
        n = config.resolved_norm(t)
        a = t.audio_duration
        v = t.video.duration if t.video.typeOf == "video" else None
        tgt = (n.fixed_duration or
               (a if n.by != "video" else (v or a)))
        total += tgt
        v_str = format_timecode(v) if v else f"{D}(image){R}"
        by_str = "fixed" if n.fixed_duration else n.by
        vmeth = n.video if t.video.typeOf == "video" else n.image

        w: list[str] = []
        if n.audio == "change_speed" and a > 0 and tgt > 0:
            f_ = a / tgt
            if not (0.75 <= f_ <= 1.25):
                w.append(f"audio speed {f_:.2f}× outside [0.75–1.25]")
        if v and n.video == "change_speed" and tgt > 0:
            spd = tgt / v
            if not (0.5 <= spd <= 2.0):
                w.append(f"video speed {spd:.2f}× outside [0.5–2.0]")

        flag = f" {Y}⚠{R}" if w else ""
        print(f"  {C}{i+1:<4}{R}{t.name:<22}{format_timecode(a):>8}"
              f"{v_str:>9}{format_timecode(tgt):>9}  {by_str:<7} A:{n.audio} / V:{vmeth}{flag}")
        for msg in w:
            warnings.append(f"  {Y}⚠  {t.name!r}: {msg}{R}")

    print("  " + "─" * 72)
    print(f"  {B}{'':4}{'TOTAL':<22}{'':>8}{'':>9}{format_timecode(total):>9}{R}\n")
    for w in warnings:
        print(w)
    if warnings:
        print()


# ── pdf-split ──────────────────────────────────────────────────────────────

@cli.command("pdf-split")
@click.argument("pdf_file", type=click.Path(exists=True, dir_okay=False))
@click.option("-o", "--output-dir", default="slides",  show_default=True)
@click.option("--dpi",              default=150,       show_default=True)
@click.option("--prefix",           default="slide",   show_default=True)
@click.option("--format", "fmt",    default="png", type=click.Choice(["png", "jpg"]))
def pdf_split(pdf_file, output_dir, dpi, prefix, fmt):
    """Split PDF_FILE into per-page images."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    flag = "-png" if fmt == "png" else "-jpeg"
    subprocess.run(["pdftoppm", flag, "-r", str(dpi), pdf_file, str(out / prefix)], check=True)

    files = sorted(out.glob(f"{prefix}*.{fmt}"))
    ff.ok(f"{len(files)} images → {output_dir}/")
    for f in files:
        print(f"    {f.name}")


# ── Entry point

def main():
    cli()


if __name__ == "__main__":
    main()