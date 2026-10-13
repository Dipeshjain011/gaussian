from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFileDialog, QFrame, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

from utils.image_utils import set_label_image


class Card(QFrame):
    def __init__(self, title: str = ""):
        super().__init__()
        self.setObjectName("card")
        self.layout = QVBoxLayout(self)
        if title:
            heading = QLabel(title)
            heading.setObjectName("cardTitle")
            self.layout.addWidget(heading)


class ImagePanel(Card):
    def __init__(self, title: str):
        super().__init__(title)
        self.image = None
        self.zoom = 1.0
        self.label = QLabel("No image")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setMinimumSize(0, 240)
        # Ignore the pixmap's size hint. Otherwise every rescale changes the
        # label's preferred size and can trigger a resize/render feedback loop.
        self.label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.label.setObjectName("imagePanel")
        self.layout.addWidget(self.label, 1)
        toolbar = QWidget()
        toolbar.setObjectName("imageToolbar")
        controls = QHBoxLayout(toolbar)
        controls.setContentsMargins(0, 6, 0, 0)
        controls.setSpacing(8)
        for text, tooltip, slot in (("−", "Zoom out", self.zoom_out), ("Fit", "Fit image to preview", self.fit)):
            button = QPushButton(text); button.setToolTip(tooltip); button.setAccessibleName(tooltip)
            button.clicked.connect(slot); controls.addWidget(button)
        self.zoom_button = QPushButton("100%")
        self.zoom_button.setToolTip("Reset zoom to 100%")
        self.zoom_button.clicked.connect(self.reset_zoom)
        controls.addWidget(self.zoom_button)
        for text, tooltip, slot in (("+", "Zoom in", self.zoom_in), ("Save", "Save image", self.save)):
            button = QPushButton(text); button.setToolTip(tooltip); button.setAccessibleName(tooltip)
            button.clicked.connect(slot); controls.addWidget(button)
        self.layout.addWidget(toolbar)
        self.setMinimumHeight(350)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_image(self, image):
        self.image = image
        self.render()

    def render(self):
        set_label_image(self.label, self.image, self.zoom)
        self.zoom_button.setText(f"{round(self.zoom * 100)}%")

    def zoom_in(self): self.zoom = min(5.0, self.zoom * 1.25); self.render()
    def zoom_out(self): self.zoom = max(.2, self.zoom / 1.25); self.render()
    def reset_zoom(self): self.zoom = 1.0; self.render()
    def fit(self): self.zoom = 1.0; self.render()
    def save(self):
        if self.image is None: return
        path, _ = QFileDialog.getSaveFileName(self, "Save image", "image.png", "PNG (*.png);;JPEG (*.jpg);;TIFF (*.tiff)")
        if path:
            from utils.image_utils import save_image
            save_image(path, self.image)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.image is not None:
            self.render()
