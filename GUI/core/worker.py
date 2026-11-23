"""Small Qt worker used to keep HTTP requests off the GUI thread."""
from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class WorkerSignals(QObject):
    succeeded = Signal(object)
    failed = Signal(str)
    finished = Signal()


class Worker(QRunnable):
    """Run a callable outside the GUI thread and report its result safely."""

    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.setAutoDelete(True)

    @Slot()
    def run(self):
        try:
            self.signals.succeeded.emit(self.function(*self.args, **self.kwargs))
        except Exception as error:
            self.signals.failed.emit(str(error))
        finally:
            self.signals.finished.emit()
