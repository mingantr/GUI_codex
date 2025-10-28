from __future__ import annotations

from pathlib import Path
from typing import List

from PyQt5.QtCore import QSettings


ORG = "TemplateApp"
APP = "PyQt5Template"

KEY_CWD = "codex/current_dir"
KEY_HISTORY = "codex/dir_history"


def _settings() -> QSettings:
    return QSettings(ORG, APP)


def get_current_dir() -> Path:
    value = str(_settings().value(KEY_CWD, str(Path.cwd())))
    try:
        p = Path(value)
        return p if p.exists() else Path.cwd()
    except Exception:
        return Path.cwd()


def set_current_dir(path: Path) -> None:
    s = _settings()
    s.setValue(KEY_CWD, str(path))
    s.sync()


def get_dir_history() -> List[str]:
    s = _settings()
    raw = s.value(KEY_HISTORY, [])
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if raw is None:
        return []
    return [str(raw)]


def add_dir_to_history(path: Path, max_len: int = 10) -> List[str]:
    s = _settings()
    current = get_dir_history()
    spath = str(path)
    # Move to front and deduplicate
    new_list = [spath] + [p for p in current if p != spath]
    if max_len > 0:
        new_list = new_list[:max_len]
    s.setValue(KEY_HISTORY, new_list)
    s.sync()
    return new_list

