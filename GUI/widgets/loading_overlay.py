from PySide6.QtWidgets import QProgressDialog


class LoadingOverlay(QProgressDialog):
    def __init__(self, parent=None, message="Please wait..."):
        super().__init__(message, None, 0, 0, parent)
        self.setWindowTitle("Working")
        self.setCancelButton(None)
        self.setMinimumDuration(250)
        self.setWindowModality(self.windowModality())
