from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QWidget,
)
from GUI.widgets.toast import notify
from GUI.utils.form_navigation import FormNavigation
from GUI.widgets.tx_table import DataTable


def _widgets_in_layout(layout):
    """Yield widgets in visual/layout order, including nested layouts."""
    for index in range(layout.count()):
        item = layout.itemAt(index)
        widget = item.widget()
        child_layout = item.layout()
        if widget is not None:
            yield widget
            nested = widget.layout()
            if nested is not None:
                yield from _widgets_in_layout(nested)
        elif child_layout is not None:
            yield from _widgets_in_layout(child_layout)



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
        self._form_navigation = None

    def showEvent(self, event):
        super().showEvent(event)
        if self._form_navigation is not None:
            return
        fields = [
            widget for widget in _widgets_in_layout(self.layout)
            if isinstance(widget, FormNavigation.INPUT_TYPES)
        ]
        if not fields:
            return
        # The first primary action is the natural completion action for the page's form.
        primary_buttons = [
            button for button in self.findChildren(QPushButton)
            if button.objectName() == "PrimaryButton" and button.isEnabled()
        ]
        callback = primary_buttons[0].click if primary_buttons else None
        self._form_navigation = FormNavigation(self, fields, callback)

    @staticmethod
    def section_label(text):
        label = QLabel(text)
        label.setObjectName("SectionLabel")
        return label

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
