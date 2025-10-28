from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QPlainTextEdit,
    QSplitter,
    QComboBox,
    QFileDialog,
    QLineEdit,
)

from .state import add_dir_to_history, get_current_dir, get_dir_history, set_current_dir


class CodexPanel(QWidget):
    """Main panel for interacting with Codex-like commands.

    Provides:
    - Current folder selector with history and a browse button
    - Checkboxes for /init, /status, /approvals
    - Prompt input and read-only response
    - Send button and Ctrl+Enter shortcut

    A real backend can be wired via `on_send` callback. By default, it
    echoes the composed request into the response area with a timestamp.
    """

    def __init__(self, on_send: Optional[Callable[[str, Path], str]] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._on_send = on_send
        self._setup_ui()
        self._load_state()

    # UI
    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # Top bar: folder history + browse
        bar = QHBoxLayout()
        bar.setSpacing(6)
        bar.addWidget(QLabel("Dossier:", self))

        self.combo_dirs = QComboBox(self)
        self.combo_dirs.setEditable(False)
        self.combo_dirs.setMinimumWidth(380)
        self.combo_dirs.activated.connect(self._on_history_selected)
        bar.addWidget(self.combo_dirs, 1)

        self.btn_browse = QPushButton("Changer…", self)
        self.btn_browse.clicked.connect(self._pick_directory)
        bar.addWidget(self.btn_browse)

        root.addLayout(bar)

        # Options/checks
        opts = QHBoxLayout()
        opts.setSpacing(12)
        self.chk_init = QCheckBox("/init", self)
        self.chk_status = QCheckBox("/status", self)
        opts.addWidget(self.chk_init)
        opts.addWidget(self.chk_status)

        # Approvals mode (non-interactif)
        self.combo_approvals = QComboBox(self)
        self.combo_approvals.setMinimumWidth(160)
        self.combo_approvals.addItem("Approvals: auto", "")
        self.combo_approvals.addItem("Approvals: never", "never")
        self.combo_approvals.addItem("Approvals: on-request", "on-request")
        self.combo_approvals.addItem("Approvals: on-failure", "on-failure")
        self.combo_approvals.addItem("Approvals: untrusted", "untrusted")
        opts.addWidget(self.combo_approvals)

        # JSON output toggle
        self.chk_json = QCheckBox("JSON", self)
        opts.addWidget(self.chk_json)

        # Profile name (optional)
        self.edit_profile = QLineEdit(self)
        self.edit_profile.setPlaceholderText("profile (optionnel)")
        self.edit_profile.setMinimumWidth(140)
        opts.addWidget(self.edit_profile)

        # Resume last toggle
        self.chk_resume = QCheckBox("Resume --last", self)
        opts.addWidget(self.chk_resume)
        opts.addStretch(1)
        root.addLayout(opts)

        # Splitter: prompt (top) and response (bottom)
        self.splitter = QSplitter(Qt.Vertical, self)

        self.prompt = QPlainTextEdit(self)
        self.prompt.setPlaceholderText("Entrez votre prompt ici… (Ctrl+Enter pour envoyer)")
        self.prompt.setTabChangesFocus(False)
        self.prompt.keyPressEvent = self._key_press_send_wrapper(self.prompt.keyPressEvent)
        self.splitter.addWidget(self.prompt)

        self.response = QPlainTextEdit(self)
        self.response.setReadOnly(True)
        self.splitter.addWidget(self.response)
        self.splitter.setSizes([200, 400])

        root.addWidget(self.splitter, 1)

        # Bottom bar: send/clear
        bb = QHBoxLayout()
        bb.addStretch(1)
        # Output capture to file (optional)
        self._output_path = None
        self.btn_output = QPushButton("Sortie: (aucun)", self)
        self.btn_output.clicked.connect(self._pick_output)
        bb.addWidget(self.btn_output)

        self.btn_clear = QPushButton("Effacer réponse", self)
        self.btn_clear.clicked.connect(self.response.clear)
        bb.addWidget(self.btn_clear)

        self.btn_send = QPushButton("Envoyer", self)
        self.btn_send.setDefault(True)
        self.btn_send.clicked.connect(self._send)
        bb.addWidget(self.btn_send)

        root.addLayout(bb)

    # State
    def _load_state(self) -> None:
        # Populate history combo and set current directory
        history = get_dir_history()
        self.combo_dirs.clear()
        for item in history:
            self.combo_dirs.addItem(item)
        cur = get_current_dir()
        self._set_current_dir(cur)

    def _set_current_dir(self, path: Path) -> None:
        # Persist and refresh history
        set_current_dir(path)
        history = add_dir_to_history(path)
        # Refresh combo preserving selection
        self.combo_dirs.blockSignals(True)
        self.combo_dirs.clear()
        for item in history:
            self.combo_dirs.addItem(item)
        idx = self.combo_dirs.findText(str(path))
        self.combo_dirs.setCurrentIndex(max(0, idx))
        self.combo_dirs.blockSignals(False)
        # Hint on response area
        self._append_info(f"Dossier courant: {path}")

    # Directory handling
    def _pick_directory(self) -> None:
        start = str(get_current_dir())
        path = QFileDialog.getExistingDirectory(self, "Choisir un dossier", start)
        if path:
            self._set_current_dir(Path(path))

    def _on_history_selected(self, index: int) -> None:  # noqa: ARG002
        text = self.combo_dirs.currentText().strip()
        if text:
            p = Path(text)
            if p.exists():
                self._set_current_dir(p)
            else:
                self._append_info(f"Dossier inexistant: {text}")

    def _pick_output(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Choisir fichier de sortie (-o)", str(get_current_dir()))
        if path:
            self._output_path = path
            from pathlib import Path as _P

            self.btn_output.setText(f"Sortie: {_P(path).name}")
        else:
            self._output_path = None
            self.btn_output.setText("Sortie: (aucun)")

    # Sending
    def _compose_message(self) -> str:
        lines = []
        if self.chk_init.isChecked():
            lines.append("/init")
        if self.chk_status.isChecked():
            lines.append("/status")
        body = self.prompt.toPlainText().strip()
        if body:
            lines.append(body)
        return "\n".join(lines).strip()

    def _send(self) -> None:
        msg = self._compose_message()
        if not msg:
            self._append_info("(Prompt vide – rien à envoyer)")
            return
        cwd = get_current_dir()
        # If a backend is provided, use it; else echo
        if self._on_send is not None:
            try:
                # Pass approvals via environment for the backend
                import os

                appr = self.combo_approvals.currentData()
                if appr:
                    os.environ["CODEX_APPROVALS"] = str(appr)
                else:
                    # Ensure default behavior if previously set
                    os.environ.pop("CODEX_APPROVALS", None)
                # Force non-interactive exec mode by default
                os.environ.setdefault("CODEX_MODE", "exec")
                os.environ.setdefault("CODEX_NO_TUI", "1")
                # JSON toggle
                if self.chk_json.isChecked():
                    os.environ["CODEX_JSON"] = "1"
                else:
                    os.environ.pop("CODEX_JSON", None)
                # Profile
                prof = self.edit_profile.text().strip()
                if prof:
                    os.environ["CODEX_PROFILE"] = prof
                else:
                    os.environ.pop("CODEX_PROFILE", None)
                # Output path
                if self._output_path:
                    os.environ["CODEX_OUTPUT"] = self._output_path
                else:
                    os.environ.pop("CODEX_OUTPUT", None)
                # Resume last
                if self.chk_resume.isChecked():
                    os.environ["CODEX_RESUME_LAST"] = "1"
                else:
                    os.environ.pop("CODEX_RESUME_LAST", None)
                out = self._on_send(msg, cwd)
            except Exception as exc:  # noqa: BLE001
                out = f"Erreur d’envoi: {exc}"
        else:
            out = msg
        self._append_exchange(msg, out)

    # Helpers
    def _append_info(self, text: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.response.appendPlainText(f"[{stamp}] {text}")

    def _append_exchange(self, prompt: str, response: str) -> None:
        sep = "\n" + ("-" * 40) + "\n"
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        block = f"[{ts}] Prompt:\n{prompt}{sep}Réponse:\n{response}\n"
        self.response.appendPlainText(block)

    def _key_press_send_wrapper(self, original):
        def handler(event):
            if event is not None and event.modifiers() in (Qt.ControlModifier, Qt.MetaModifier) and event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self._send()
                return
            return original(event)

        return handler
