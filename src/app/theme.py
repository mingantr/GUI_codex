from pathlib import Path
from typing import Literal

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication

from .paths import assets_path

Theme = Literal["dark", "light"]


ORG = "TemplateApp"
APP = "PyQt5Template"
KEY = "theme"


def settings() -> QSettings:
    return QSettings(ORG, APP)


def get_theme() -> Theme:
    value = settings().value(KEY, "dark")
    return "light" if str(value).lower() == "light" else "dark"


def set_theme(theme: Theme) -> None:
    s = settings()
    s.setValue(KEY, theme)
    s.sync()


def qss_path(theme: Theme) -> Path:
    filename = "dark.qss" if theme == "dark" else "light.qss"
    return assets_path(filename)


def apply_theme(app: QApplication, theme: Theme) -> None:
    qss = qss_path(theme)
    if qss.exists():
        try:
            app.setStyleSheet(qss.read_text(encoding="utf-8"))
        except Exception:
            app.setStyleSheet("")
    else:
        app.setStyleSheet("")


def toggle_theme(app: QApplication) -> Theme:
    theme = get_theme()
    new_theme: Theme = "light" if theme == "dark" else "dark"
    apply_theme(app, new_theme)
    set_theme(new_theme)
    return new_theme

