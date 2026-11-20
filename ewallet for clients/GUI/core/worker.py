from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class WorkerSignals(QObject):
    succeeded = Signal(object)
    failed = Signal(str)


class Worker(QRunnable):
    """Run a callable outside the GUI thread."""

    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        try:
            self.signals.succeeded.emit(self.function(*self.args, **self.kwargs))
        except Exception as error:
            self.signals.failed.emit(str(error))
