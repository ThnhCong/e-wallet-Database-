from PySide6.QtWidgets import QDoubleSpinBox


class AmountInput(QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(0, 999999999999.99)
        self.setDecimals(2)
        self.setSingleStep(10000)
        self.setGroupSeparatorShown(True)
        self.setMinimumHeight(40)
        self.setSpecialValueText("Enter amount")
