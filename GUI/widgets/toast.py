from PySide6.QtWidgets import QMessageBox


def notify(parent, title, message, error=False):
    box = QMessageBox(parent)
    box.setWindowTitle(title)
    box.setText(str(message))
    box.setIcon(QMessageBox.Icon.Critical if error else QMessageBox.Icon.Information)
    box.exec()
