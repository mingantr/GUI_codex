from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QGuiApplication, QKeySequence
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
    QGridLayout,
    QMessageBox,
)

from .database import ensure_database, save_exchange
from .database_dialog import DatabaseDialog
from .state import (
    add_dir_to_history,
    get_approval_mode,
    get_current_dir,
    get_database_path,
    get_dir_history,
    set_approval_mode,
    set_current_dir,
    set_database_path,
)


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
        self._database_path: Optional[Path] = None
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

        # Checkboxes arranged in two columns
        checks = QGridLayout()
        checks.setHorizontalSpacing(12)
        checks.setVerticalSpacing(4)

        self.chk_init = QCheckBox("/init", self)
        self.chk_status = QCheckBox("/status", self)
        self.chk_json = QCheckBox("JSON", self)
        self.chk_resume = QCheckBox("Resume --last", self)

        checks.addWidget(self.chk_init, 0, 0)
        checks.addWidget(self.chk_status, 0, 1)
        checks.addWidget(self.chk_json, 1, 0)
        checks.addWidget(self.chk_resume, 1, 1)
        checks.setColumnStretch(0, 1)
        checks.setColumnStretch(1, 1)
        root.addLayout(checks)

        # Approvals and extras row
        opts = QHBoxLayout()
        opts.setSpacing(12)

        self.combo_approvals = QComboBox(self)
        self.combo_approvals.setMinimumWidth(220)
        self.combo_approvals.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        approval_options = [
            (
                "Ask – Codex can read files and answer questions.\n"
                "Codex requires approval to make edits, run commands, or access network.",
                ("ask", "on-request"),
            ),
            (
                "Auto – Codex can read files, make edits, and run commands in the workspace.\n"
                "Codex requires approval to work outside the workspace or access network.",
                ("auto", ""),
            ),
            (
                "Full Access – Codex can read files, make edits, and run commands with network access, without approval.",
                ("full-access", "never"),
            ),
        ]
        for idx, (label, data) in enumerate(approval_options):
            self.combo_approvals.addItem(label, data)
            self.combo_approvals.setItemData(idx, label, Qt.ToolTipRole)
        self.combo_approvals.setCurrentIndex(1)
        opts.addWidget(self.combo_approvals)

        self.edit_profile = QLineEdit(self)
        self.edit_profile.setPlaceholderText("profile (optionnel)")
        self.edit_profile.setMinimumWidth(160)
        opts.addWidget(self.edit_profile)
        opts.addStretch(1)
        root.addLayout(opts)

        # Database row
        db_row = QHBoxLayout()
        db_row.setSpacing(8)
        db_row.addWidget(QLabel("Base de données:", self))

        self.edit_database = QLineEdit(self)
        self.edit_database.setReadOnly(True)
        self.edit_database.setMinimumWidth(260)
        db_row.addWidget(self.edit_database, 1)

        self.btn_db_browse = QPushButton("Parcourir…", self)
        self.btn_db_browse.clicked.connect(self._pick_database)
        db_row.addWidget(self.btn_db_browse)

        self.btn_db_open = QPushButton("Ouvrir…", self)
        self.btn_db_open.clicked.connect(self._open_database)
        db_row.addWidget(self.btn_db_open)

        root.addLayout(db_row)

        # Splitter: prompt (top) and response (bottom)
        self.splitter = QSplitter(Qt.Vertical, self)

        self.prompt = QPlainTextEdit(self)
        self.prompt.setPlaceholderText("Entrez votre prompt ici… (Ctrl+Enter pour envoyer)")
        self.prompt.setTabChangesFocus(False)
        self.prompt.keyPressEvent = self._key_press_send_wrapper(self.prompt.keyPressEvent)
        self.splitter.addWidget(self.prompt)

        self.response = QPlainTextEdit(self)
        self.response.setReadOnly(True)
        self.response.installEventFilter(self)
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
        self._load_database_path()
        self._load_approval_mode()

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

    def _load_database_path(self) -> None:
        path = get_database_path()
        try:
            ensured = ensure_database(path)
        except Exception as exc:  # noqa: BLE001
            self._database_path = None
            self._append_info(f"Base de données indisponible: {exc}")
        else:
            self._database_path = ensured
            set_database_path(ensured)
        self._update_database_path_display()

    def _update_database_path_display(self) -> None:
        if self._database_path is None:
            self.edit_database.setText("(désactivée)")
            self.btn_db_open.setEnabled(False)
        else:
            self.edit_database.setText(str(self._database_path))
            self.btn_db_open.setEnabled(True)

    def _pick_database(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Choisir une base SQLite",
            str(self._database_path or get_database_path()),
            "SQLite (*.sqlite3 *.db);;All files (*.*)",
        )
        if not path:
            return
        try:
            ensured = ensure_database(Path(path))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Erreur", f"Impossible de préparer la base:\n{exc}")
            return
        self._database_path = ensured
        set_database_path(ensured)
        self._update_database_path_display()

    def _load_approval_mode(self) -> None:
        wanted = get_approval_mode()
        for idx in range(self.combo_approvals.count()):
            data = self.combo_approvals.itemData(idx)
            if isinstance(data, tuple) and data and data[0] == wanted:
                self.combo_approvals.setCurrentIndex(idx)
                break

    def _open_database(self) -> None:
        if self._database_path is None:
            QMessageBox.information(
                self,
                "Base de données",
                "Aucune base configurée. Choisissez un fichier pour activer l'historique.",
            )
            return
        dlg = DatabaseDialog(self._database_path, self)
        dlg.exec_()

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

                mode, legacy = self._selected_approval_mode()
                if legacy:
                    os.environ["CODEX_APPROVALS"] = legacy
                else:
                    os.environ.pop("CODEX_APPROVALS", None)
                set_approval_mode(mode or "auto")
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
        self._log_exchange(msg, out)

    # Helpers
    def _selected_approval_mode(self) -> tuple[str, str]:
        data = self.combo_approvals.currentData()
        if isinstance(data, tuple) and len(data) == 2:
            mode, legacy = data
            return str(mode), str(legacy)
        return ("auto", "")

    def _append_info(self, text: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.response.appendPlainText(f"[{stamp}] {text}")

    def _append_exchange(self, prompt: str, response: str) -> None:
        sep = "\n" + ("-" * 40) + "\n"
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        block = f"[{ts}] Prompt:\n{prompt}{sep}Réponse:\n{response}\n"
        self.response.appendPlainText(block)

    def _log_exchange(self, prompt: str, response: str) -> None:
        if self._database_path is None:
            return
        try:
            save_exchange(prompt, response, self._database_path)
        except Exception as exc:  # noqa: BLE001
            self._append_info(f"Enregistrement en base impossible: {exc}")

    def _key_press_send_wrapper(self, original):
        def handler(event):
            if event is not None and event.modifiers() in (Qt.ControlModifier, Qt.MetaModifier) and event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self._send()
                return
            return original(event)

        return handler

    def eventFilter(self, obj, event):  # noqa: D401, ANN001
        """Intercept copy shortcut on the response widget to copy the full text."""

        if obj is self.response and event.type() == QEvent.KeyPress:
            if event.matches(QKeySequence.Copy):
                cursor = self.response.textCursor()
                if cursor.hasSelection():
                    return super().eventFilter(obj, event)
                text = self.response.toPlainText()
                if text:
                    QGuiApplication.clipboard().setText(text)
                    return True
        return super().eventFilter(obj, event)
