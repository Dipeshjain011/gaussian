from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import numpy as np


class PlotCanvas(FigureCanvasQTAgg):
    def __init__(self, rows=1, cols=1, height=4):
        self.figure = Figure(figsize=(8, height), tight_layout=True)
        self.axes = self.figure.subplots(rows, cols, squeeze=False)
        super().__init__(self.figure)

    def clear(self):
        self.figure.clear()
        self.draw_idle()


def show_heatmap(axis, data: np.ndarray, title: str, cmap="magma"):
    axis.clear()
    image = np.asarray(data)
    if image.ndim == 3:
        # Matplotlib expects floating RGB(A) channels in [0, 1]. The
        # processing pipeline intentionally keeps intensities in [0, 255].
        if image.shape[2] not in (3, 4):
            raise ValueError(f"Unsupported image channel count: {image.shape[2]}")
        if not np.all(np.isfinite(image)):
            raise ValueError("Image preview contains NaN or infinite values.")
        image = np.clip(image.astype(np.float64) / 255.0, 0.0, 1.0)
        axis.imshow(image)
    elif image.ndim == 2:
        if not np.all(np.isfinite(image)):
            raise ValueError("Image preview contains NaN or infinite values.")
        axis.imshow(image, cmap=cmap)
    else:
        raise ValueError(f"Expected a 2D grayscale or 3D color image, got shape {image.shape}.")
    axis.set_title(title)
    axis.axis("off")
