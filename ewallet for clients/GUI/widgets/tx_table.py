import json
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QHeaderView, QLabel, QPushButton, QScrollArea,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)


def _display_value(value):
    if value is None or value == "":
        return "—"
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, indent=2, default=str)
    return str(value)


def show_record_details(parent, title, fields):
    """Show a read-only, scrollable detail window for a record or metric."""
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.resize(680, 560)
    dialog.setMinimumSize(440, 320)
    outer = QVBoxLayout(dialog)
    scroll = QScrollArea(dialog)
    scroll.setWidgetResizable(True)
    content = QWidget()
    form = QFormLayout(content)
    form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
    form.setHorizontalSpacing(18)
    form.setVerticalSpacing(12)
    for label, value in fields:
        value_label = QLabel(_display_value(value))
        value_label.setWordWrap(True)
        value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        value_label.setMinimumWidth(180)
        form.addRow(str(label), value_label)
    scroll.setWidget(content)
    outer.addWidget(scroll, 1)
    close_button = QPushButton("Close")
    close_button.setMinimumHeight(38)
    close_button.clicked.connect(dialog.accept)
    outer.addWidget(close_button)
    dialog.exec()


class DataTable(QTableWidget):
    def __init__(self, columns, parent=None):
        super().__init__(0, len(columns), parent)
        self.columns = columns
        self._rows = []
        self._detail_handler = None
        self.setHorizontalHeaderLabels([label for label, _ in columns])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setMinimumSectionSize(82)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(42)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self.setMinimumHeight(280)
        self.setSortingEnabled(False)
        self.cellDoubleClicked.connect(self._open_row_details)

    def set_detail_handler(self, callback):
        """Override the default detail window with a page-specific detail action."""
        self._detail_handler = callback

    def _open_row_details(self, row_index, column_index):
        if not (0 <= row_index < len(self._rows)):
            return
        if self._detail_handler is not None:
            self._detail_handler(row_index, column_index)
            return
        row = self._rows[row_index]
        fields = []
        represented_keys = set()
        for column_index, (label, key) in enumerate(self.columns):
            item = self.item(row_index, column_index)
            value = item.text() if item is not None else None
            fields.append((label, value))
            if isinstance(key, str):
                represented_keys.add(key)
        # Include fields returned by the API even when the compact table hides them.
        if isinstance(row, dict):
            extra = [(key.replace("_", " ").title(), value)
                     for key, value in row.items() if key not in represented_keys]
            if extra:
                fields.append(("Additional information", ""))
                fields.extend(extra)
        title = "Record details"
        if isinstance(row, dict):
            for candidate in ("transaction_id", "wallet_id", "bank_account_id", "user_id", "audit_log_id", "bank_id"):
                if row.get(candidate) is not None:
                    title = f"Details · {candidate.replace('_', ' ').title()} #{row[candidate]}"
                    break
        show_record_details(self, title, fields)

    def set_rows(self, rows):
        self._rows = list(rows or [])
        self.setSortingEnabled(False)
        self.setRowCount(len(self._rows))
        for row_index, row in enumerate(self._rows):
            for col_index, (_, key) in enumerate(self.columns):
                value = key(row) if callable(key) else row.get(key)
                item = QTableWidgetItem("—" if value is None else str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.setItem(row_index, col_index, item)
        self.resizeRowsToContents()
