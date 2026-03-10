from __future__ import annotations

import os
from pathlib import Path

DEFAULT_GUIDE_CANDIDATES = (
    "data/3D-printing-troubleshooting-guide",
    "data/3d-printing-troubleshooting-guide",
    "data/troubleshooting-guide",
    "3D-printing-troubleshooting-guide",
    "3d-printing-troubleshooting-guide",
    "troubleshooting-guide",
)


def detect_troubleshooting_guide(start_dir: str | Path = ".") -> Path | None:
    env_path = os.getenv("TROUBLESHOOTING_GUIDE_DIR")
    if env_path:
        p = Path(env_path).expanduser().resolve()
        if p.is_dir():
            return p

    root = Path(start_dir).resolve()
    for rel in DEFAULT_GUIDE_CANDIDATES:
        candidate = root / rel
        if candidate.is_dir():
            return candidate

    return None
