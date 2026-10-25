from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem


class DataTable(QTableWidget):
    def __init__(self, columns, parent=None):
        super().__init__(0, len(columns), parent)
        self.columns = columns
        self.setHorizontalHeaderLabels([label for label, _ in columns])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

    def set_rows(self, rows):
        self.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            for col_index, (_, key) in enumerate(self.columns):
                value = key(row) if callable(key) else row.get(key)
                self.setItem(row_index, col_index, QTableWidgetItem("-" if value is None else str(value)))
        self.resizeRowsToContents()
