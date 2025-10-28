from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAction,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTextEdit,
)

from .paths import assets_path, project_root
from .codex_panel import CodexPanel
from .state import get_current_dir


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        cwd = get_current_dir()
        self.setWindowTitle(f"Codex GUI — {cwd}")
        self.resize(900, 600)
        self._setup_ui()
        icon_file = assets_path("icon.svg")
        if icon_file.exists():
            self.setWindowIcon(QIcon(str(icon_file)))

    def _setup_ui(self) -> None:
        # Central widget: CodexPanel wired to backend
        from .backend import run_codex

        self.codex = CodexPanel(on_send=run_codex, parent=self)
        self.setCentralWidget(self.codex)

        # Status bar
        self.statusBar().showMessage("Ready")

        # Menus
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        edit_menu = menubar.addMenu("&Edit")
        view_menu = menubar.addMenu("&View")
        help_menu = menubar.addMenu("&Help")

        # File actions
        act_new = QAction("&New", self)
        act_new.setShortcut("Ctrl+N")
        act_new.triggered.connect(self.on_new)

        act_open = QAction("&Open...", self)
        act_open.setShortcut("Ctrl+O")
        act_open.triggered.connect(self.on_open)

        act_save = QAction("&Save As...", self)
        act_save.setShortcut("Ctrl+S")
        act_save.triggered.connect(self.on_save_as)

        act_exit = QAction("E&xit", self)
        act_exit.setShortcut("Alt+F4")
        act_exit.triggered.connect(self.close)

        file_menu.addAction(act_new)
        file_menu.addAction(act_open)
        file_menu.addAction(act_save)
        file_menu.addSeparator()
        file_menu.addAction(act_exit)

        # Edit actions (kept for convenience; operate on an internal editor window if needed)
        act_undo = QAction("&Undo", self)
        act_undo.setShortcut("Ctrl+Z")
        act_undo.triggered.connect(self._noop)

        act_redo = QAction("&Redo", self)
        act_redo.setShortcut("Ctrl+Y")
        act_redo.triggered.connect(self._noop)

        act_cut = QAction("Cu&t", self)
        act_cut.setShortcut("Ctrl+X")
        act_cut.triggered.connect(self._noop)

        act_copy = QAction("&Copy", self)
        act_copy.setShortcut("Ctrl+C")
        act_copy.triggered.connect(self._noop)

        act_paste = QAction("&Paste", self)
        act_paste.setShortcut("Ctrl+V")
        act_paste.triggered.connect(self._noop)

        edit_menu.addAction(act_undo)
        edit_menu.addAction(act_redo)
        edit_menu.addSeparator()
        edit_menu.addAction(act_cut)
        edit_menu.addAction(act_copy)
        edit_menu.addAction(act_paste)

        # View actions (theme toggle)
        from PyQt5.QtWidgets import QApplication as _QApp
        from .theme import get_theme, toggle_theme

        self._theme = get_theme()
        self.act_toggle_theme = QAction(self._toggle_title(self._theme), self)
        self.act_toggle_theme.setShortcut("Ctrl+T")
        self.act_toggle_theme.triggered.connect(self.on_toggle_theme)
        view_menu.addAction(self.act_toggle_theme)

        # Help actions
        act_about = QAction("&About", self)
        act_about.triggered.connect(self.on_about)
        help_menu.addAction(act_about)

    # Slots
    def on_new(self) -> None:
        # In Codex UI, this clears the prompt area
        self.codex.prompt.clear()
        self.statusBar().showMessage("Nouveau prompt", 2000)

    def on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            str(project_root()),
            "Text files (*.txt);;All files (*.*)",
        )
        if path:
            try:
                text = Path(path).read_text(encoding="utf-8")
                self.codex.prompt.setPlainText(text)
                self.statusBar().showMessage(f"Opened: {Path(path).name}", 2000)
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, "Error", f"Failed to open file:\n{exc}")

    def on_save_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save As",
            str(project_root() / "untitled.txt"),
            "Text files (*.txt);;All files (*.*)",
        )
        if path:
            try:
                Path(path).write_text(self.codex.prompt.toPlainText(), encoding="utf-8")
                self.statusBar().showMessage(f"Saved: {Path(path).name}", 2000)
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{exc}")

    def on_about(self) -> None:
        QMessageBox.information(
            self,
            "About",
            "PyQt5 Template\n\nA minimal starter with a menu bar,\n"
            "status bar, and simple text editor.",
        )

    # Theme helpers
    def _toggle_title(self, current: str) -> str:
        return "Switch to Light" if current == "dark" else "Switch to Dark"

    def on_toggle_theme(self) -> None:
        from PyQt5.QtWidgets import QApplication as _QApp
        from .theme import toggle_theme

        app = _QApp.instance()
        if app is None:
            return
        self._theme = toggle_theme(app)  # applies and stores
        self.act_toggle_theme.setText(self._toggle_title(self._theme))
        self.statusBar().showMessage(f"Theme: {self._theme}", 1500)

    # Generic no-op for disabled edit actions
    def _noop(self) -> None:
        pass
