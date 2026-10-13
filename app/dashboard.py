from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class DashboardPage(QWidget):
    start_requested = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(52, 52, 52, 52)
        layout.setSpacing(18)
        title = QLabel("Gaussian Blur Removal Using\nFrequency Domain Restoration")
        title.setObjectName("heroTitle")
        subtitle = QLabel("DIGITAL IMAGE PROCESSING BASED IMAGE RESTORATION SYSTEM")
        subtitle.setObjectName("heroSubtitle")
        explanation = QLabel(
            "This application demonstrates restoration of Gaussian-degraded images using the DFT, "
            "inverse filtering and Wiener filtering. It attempts to recover image information; it does not "
            "claim perfect blur removal."
        )
        explanation.setWordWrap(True)
        explanation.setMaximumWidth(850)
        flow = QLabel("IMAGE  →  GAUSSIAN BLUR  →  FFT  →  H(u,v)  →  INVERSE / WIENER  →  IFFT  →  COMPARISON")
        flow.setObjectName("flowLabel")
        flow.setWordWrap(True)
        button = QPushButton("Start Image Restoration")
        button.setObjectName("primaryButton")
        button.setFixedWidth(250)
        button.clicked.connect(self.start_requested)
        tags = QLabel("DFT / FFT     •     Frequency Domain     •     Inverse Filtering     •     Wiener Filtering")
        tags.setObjectName("muted")
        layout.addStretch()
        layout.addWidget(subtitle)
        layout.addWidget(title)
        layout.addWidget(explanation)
        layout.addSpacing(20)
        layout.addWidget(flow)
        layout.addWidget(button)
        layout.addWidget(tags)
        layout.addStretch(2)
