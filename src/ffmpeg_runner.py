"""
Thin subprocess wrapper for ffmpeg/ffprobe.

Usage:
    from demo_builder import ffmpeg_runner as ff
    ff.configure(verbose=True, log_file="build.log")
    ff.run(["ffmpeg", "-i", "in.mp4", "out.mp4"], desc="My step")
"""
from __future__ import annotations

import shlex
import subprocess
import sys
from pathlib import Path
from typing import Optional

# ── Configuration (set once from CLI) ─────────────────────────────────────

_verbose: bool = False
_log_file: Optional[Path] = None


def configure(*, verbose: bool = False, log_file: Optional[str | Path] = None) -> None:
    global _verbose, _log_file
    _verbose = verbose
    _log_file = Path(log_file) if log_file else None
    if _log_file:
        _log_file.parent.mkdir(parents=True, exist_ok=True)
        _log_file.write_text("")  # truncate / create


# ── Core runner ────────────────────────────────────────────────────────────

class FFmpegError(Exception):
    """Raised when ffmpeg exits non-zero."""


def run(args: list[str], *, desc: str = "") -> None:
    """Execute an ffmpeg command, log it, raise FFmpegError on failure."""
    if desc:
        _print(f"  → {desc}")
    _print(f"    $ {shlex.join(args)}", dim=True)

    stderr_target: int | None
    if _verbose:
        stderr_target = None          # pass through to terminal
    elif _log_file:
        stderr_target = subprocess.PIPE   # captured below
    else:
        stderr_target = subprocess.DEVNULL

    try:
        result = subprocess.run(args, stderr=stderr_target, check=False)
    except FileNotFoundError:
        raise FFmpegError(f"Binary not found: {args[0]!r} — is ffmpeg on PATH?")

    if _log_file and result.stderr:
        with open(_log_file, "ab") as f:
            f.write(f"\n### {shlex.join(args)}\n".encode())
            f.write(result.stderr)

    if result.returncode != 0:
        msg = f"ffmpeg exited {result.returncode}"
        if result.stderr:
            tail = result.stderr.decode(errors="replace").strip().splitlines()[-15:]
            msg += "\n" + "\n".join(tail)
        raise FFmpegError(msg)


def ensure_dir(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


# ── Logging helpers ────────────────────────────────────────────────────────

def info(msg: str)    -> None: print(f"\033[36m[info]\033[0m  {msg}")
def ok(msg: str)      -> None: print(f"\033[32m[ok]\033[0m    {msg}")
def warn(msg: str)    -> None: print(f"\033[33m[warn]\033[0m  {msg}", file=sys.stderr)
def error(msg: str)   -> None: print(f"\033[31m[error]\033[0m {msg}", file=sys.stderr)

def _print(msg: str, *, dim: bool = False) -> None:
    if dim:
        print(f"\033[2m{msg}\033[0m")
    else:
        print(msg)