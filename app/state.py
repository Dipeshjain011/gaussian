from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from PySide6.QtCore import QObject, Signal


@dataclass
class ProjectData:
    path: str | None = None
    controlled: bool = True
    original: np.ndarray | None = None
    degraded: np.ndarray | None = None
    inverse: np.ndarray | None = None
    wiener: np.ndarray | None = None
    otf: np.ndarray | None = None
    inverse_response: np.ndarray | None = None
    wiener_response: np.ndarray | None = None
    inverse_metrics: dict | None = None
    wiener_metrics: dict | None = None
    inverse_time: float | None = None
    wiener_time: float | None = None
    kernel_size: int = 15
    sigma: float = 3.0
    noise: float = 0.0
    experiments: pd.DataFrame = field(default_factory=pd.DataFrame)


class ProjectState(QObject):
    changed = Signal()
    message = Signal(str)

    def __init__(self):
        super().__init__()
        self.data = ProjectData()

    def notify(self, message: str = ""):
        self.changed.emit()
        if message:
            self.message.emit(message)

