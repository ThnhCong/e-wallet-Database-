from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QStackedWidget, QGraphicsOpacityEffect


class Router(QStackedWidget):
    """Named-page router with a smooth, restrained fade transition."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pages = {}
        self._animation = None
        self.setContentsMargins(0, 0, 0, 0)

    def register(self, name, page):
        self._pages[name] = page
        self.addWidget(page)

    def go(self, name):
        page = self._pages.get(name)
        if page is None or page is self.currentWidget():
            return
        self.setCurrentWidget(page)
        effect = QGraphicsOpacityEffect(page)
        page.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(240)
        animation.setStartValue(0.58)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.finished.connect(lambda p=page: p.setGraphicsEffect(None))
        self._animation = animation
        animation.start()
