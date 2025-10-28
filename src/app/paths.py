from pathlib import Path
import sys


def project_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[2]


def assets_path(*parts: str) -> Path:
    return project_root().joinpath("assets", *parts)
