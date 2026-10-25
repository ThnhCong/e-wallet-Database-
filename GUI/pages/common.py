from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QWidget,
)
from GUI.widgets.toast import notify
from GUI.widgets.tx_table import DataTable


class Page(QWidget):
    def __init__(self, title, subtitle="", parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 28, 30, 28)
        self.layout.setSpacing(16)
        heading = QLabel(title)
        heading.setObjectName("PageTitle")
        self.layout.addWidget(heading)
        if subtitle:
            hint = QLabel(subtitle)
            hint.setObjectName("MutedLabel")
            hint.setWordWrap(True)
            self.layout.addWidget(hint)

    def show_error(self, error):
        notify(self, "Operation failed", error, True)

    def show_success(self, message):
        notify(self, "Success", message)


def make_button(text, callback, object_name="PrimaryButton"):
    button = QPushButton(text)
    button.setObjectName(object_name)
    button.setMinimumHeight(40)
    button.clicked.connect(callback)
    return button


def make_combo(values, placeholder=None):
    combo = QComboBox()
    if placeholder:
        combo.addItem(placeholder, None)
    for value in values:
        combo.addItem(value, value)
    combo.setMinimumHeight(40)
    return combo


def make_input(placeholder=""):
    field = QLineEdit()
    field.setPlaceholderText(placeholder)
    field.setMinimumHeight(40)
    return field


def add_form(page, fields):
    form = QFormLayout()
    form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
    form.setFormAlignment(Qt.AlignmentFlag.AlignTop)
    form.setHorizontalSpacing(18)
    form.setVerticalSpacing(12)
    for label, widget in fields:
        form.addRow(label, widget)
    page.layout.addLayout(form)
    return form


def add_table(page, columns):
    table = DataTable(columns)
    page.layout.addWidget(table, 1)
    return table
