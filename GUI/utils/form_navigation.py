from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDoubleSpinBox,
    QLineEdit,
    QSpinBox,
    QTimeEdit,
)


class FormNavigation(QObject):
    """Move through form fields with Enter and submit from the last field."""

    INPUT_TYPES = (
        QLineEdit,
        QComboBox,
        QSpinBox,
        QDoubleSpinBox,
        QDateEdit,
        QTimeEdit,
        QDateTimeEdit,
    )

    def __init__(self, parent, fields, submit_callback=None, loop=False):
        super().__init__(parent)
        self.fields = list(dict.fromkeys(
            field for field in fields if isinstance(field, self.INPUT_TYPES)
        ))
        self.submit_callback = submit_callback
        self.loop = loop

        for field in self.fields:
            field.installEventFilter(self)

    def _active_fields(self):
        active = []
        for field in self.fields:
            is_read_only = getattr(field, "isReadOnly", lambda: False)()
            if field.isVisible() and field.isEnabled() and not is_read_only:
                active.append(field)
        return active

    def eventFilter(self, watched, event):
        if watched not in self.fields or event.type() != QEvent.Type.KeyPress:
            return super().eventFilter(watched, event)

        if event.key() not in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            return super().eventFilter(watched, event)

        # Keep the normal Enter behavior while a combo-box popup is open.
        if isinstance(watched, QComboBox) and watched.view().isVisible():
            return super().eventFilter(watched, event)

        fields = self._active_fields()
        if watched not in fields:
            return True

        index = fields.index(watched)
        if index + 1 < len(fields):
            fields[index + 1].setFocus(Qt.FocusReason.TabFocusReason)
        elif self.loop and fields:
            fields[0].setFocus(Qt.FocusReason.TabFocusReason)
        elif self.submit_callback:
            self.submit_callback()

        # Consume Enter so QLineEdit.returnPressed and default-button behavior
        # cannot submit the form a second time.
        return True
