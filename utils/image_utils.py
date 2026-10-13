from __future__ import annotations

import cv2
import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap


def to_qimage(image: np.ndarray) -> QImage:
    array = np.asarray(image)
    if not np.all(np.isfinite(array)):
        raise ValueError("Cannot display an image containing NaN or infinite values.")
    array = np.ascontiguousarray(np.clip(np.rint(array), 0, 255).astype(np.uint8))
    if array.ndim == 2:
        return QImage(array.data, array.shape[1], array.shape[0], array.strides[0], QImage.Format_Grayscale8).copy()
    fmt = QImage.Format_RGBA8888 if array.shape[2] == 4 else QImage.Format_RGB888
    return QImage(array.data, array.shape[1], array.shape[0], array.strides[0], fmt).copy()


def set_label_image(label, image: np.ndarray | None, zoom: float = 1.0):
    if image is None:
        label.setPixmap(QPixmap())
        label.setText("No image")
        return
    pixmap = QPixmap.fromImage(to_qimage(image))
    target = label.size() * zoom
    label.setPixmap(pixmap.scaled(target, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    label.setText("")
    label._source_pixmap = pixmap


def save_image(path: str, image: np.ndarray) -> bool:
    image = np.asarray(image)
    if not np.all(np.isfinite(image)):
        return False
    image = np.clip(np.rint(image), 0, 255).astype(np.uint8)
    if image.ndim == 3:
        data = cv2.cvtColor(image, cv2.COLOR_RGBA2BGRA if image.shape[2] == 4 else cv2.COLOR_RGB2BGR)
    else:
        data = image
    ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ".png"
    ok, encoded = cv2.imencode(ext, data)
    if ok:
        encoded.tofile(path)
    return bool(ok)

