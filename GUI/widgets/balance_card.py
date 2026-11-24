from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout
from GUI.widgets.tx_table import show_record_details


class BalanceCard(QFrame):
    def __init__(self, title, value="—", parent=None):
        super().__init__(parent)
        self.setObjectName("BalanceCard")
        layout = QVBoxLayout(self)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("MutedLabel")
        self.value_label = QLabel(value)
        self.value_label.setObjectName("MetricValue")
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)

    def set_value(self, value):
        self.value_label.setText(str(value))

    def mouseDoubleClickEvent(self, event):
        show_record_details(self, self.title_label.text().title(), [
            ("Metric", self.title_label.text()),
            ("Current value", self.value_label.text()),
        ])
        super().mouseDoubleClickEvent(event)
