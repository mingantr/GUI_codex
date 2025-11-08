from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView

from .database import fetch_recent


class DatabaseDialog(QDialog):
    """Simple dialog displaying stored exchanges in two columns."""

    def __init__(self, db_path: Path, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._db_path = db_path
        self.setWindowTitle("Base de données des échanges")
        self.resize(820, 520)
        self._build_ui()
        self._load_entries()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        header = QLabel(f"Base de données: {self._db_path}", self)
        header.setTextInteractionFlags(Qt.TextSelectableByMouse)
        header.setWordWrap(True)
        layout.addWidget(header)

        self.table = QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Prompt", "Réponse"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setWordWrap(True)
        layout.addWidget(self.table, 1)

        self.btn_refresh = QPushButton("Rafraîchir", self)
        self.btn_refresh.clicked.connect(self._load_entries)

        self.btn_close = QPushButton("Fermer", self)
        self.btn_close.clicked.connect(self.accept)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(self.btn_refresh)
        buttons.addWidget(self.btn_close)
        layout.addLayout(buttons)

    def _load_entries(self) -> None:
        entries = fetch_recent(path=self._db_path)
        self.table.setRowCount(len(entries))
        for row_index, (created_at, prompt, response) in enumerate(entries):
            prompt_item = QTableWidgetItem(prompt)
            prompt_item.setToolTip(prompt)
            response_item = QTableWidgetItem(response)
            response_item.setToolTip(response)
            self.table.setItem(row_index, 0, prompt_item)
            self.table.setItem(row_index, 1, response_item)
            header_item = QTableWidgetItem(created_at)
            header_item.setToolTip(created_at)
            self.table.setVerticalHeaderItem(row_index, header_item)
        self.table.resizeRowsToContents()
