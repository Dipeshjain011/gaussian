from __future__ import annotations

import traceback
from threading import Event
from typing import Any, Callable

from PySide6.QtCore import QObject, QThread, Signal, Slot


class CancelledError(Exception):
    """Raised by a background task after a cooperative cancellation request."""


class TaskContext:
    def __init__(self, cancelled: Event, progress: Signal):
        self._cancelled = cancelled
        self._progress = progress

    def check_cancelled(self) -> None:
        if self._cancelled.is_set():
            raise CancelledError()

    def report(self, value: int, message: str) -> None:
        self.check_cancelled()
        self._progress.emit(max(0, min(100, int(value))), message)


class Worker(QObject):
    progress = Signal(int, str)
    result = Signal(object)
    error = Signal(str)
    cancelled = Signal()
    finished = Signal()

    def __init__(self, function: Callable[[TaskContext], Any]):
        super().__init__()
        self.function = function
        self._cancel_event = Event()

    def cancel(self) -> None:
        self._cancel_event.set()

    @Slot()
    def run(self) -> None:
        try:
            context = TaskContext(self._cancel_event, self.progress)
            context.check_cancelled()
            value = self.function(context)
            context.check_cancelled()
            self.result.emit(value)
        except CancelledError:
            self.cancelled.emit()
        except Exception as exc:
            # Keep the traceback out of the user interface, but retain it for developers.
            traceback.print_exc()
            self.error.emit(str(exc) or "The operation could not be completed.")
        finally:
            self.finished.emit()


class TaskController(QObject):
    progress = Signal(int, str)
    result = Signal(object)
    error = Signal(str)
    cancelled = Signal()
    busy_changed = Signal(bool)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.thread: QThread | None = None
        self.worker: Worker | None = None

    @property
    def busy(self) -> bool:
        return self.thread is not None and self.thread.isRunning()

    def start(self, function: Callable[[TaskContext], Any]) -> bool:
        if self.busy:
            return False
        thread = QThread(self)
        worker = Worker(function)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self.progress)
        worker.result.connect(self.result)
        worker.error.connect(self.error)
        worker.cancelled.connect(self.cancelled)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._thread_finished)
        self.thread, self.worker = thread, worker
        self.busy_changed.emit(True)
        thread.start()
        return True

    @Slot()
    def cancel(self) -> None:
        if self.worker is not None:
            self.worker.cancel()

    @Slot()
    def _thread_finished(self) -> None:
        old_thread = self.thread
        self.thread = None
        self.worker = None
        if old_thread is not None:
            old_thread.deleteLater()
        self.busy_changed.emit(False)

