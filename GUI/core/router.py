from PySide6.QtWidgets import QStackedWidget


class Router(QStackedWidget):
    """Simple named-page router backed by QStackedWidget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pages = {}

    def register(self, name, page):
        self._pages[name] = page
        self.addWidget(page)

    def go(self, name):
        page = self._pages.get(name)
        if page is not None:
            self.setCurrentWidget(page)
