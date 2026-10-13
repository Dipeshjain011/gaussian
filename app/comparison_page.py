from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QGridLayout, QHeaderView, QLabel,
    QScrollArea, QSizePolicy, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from evaluation.analysis import comparison_text
from .widgets import ImagePanel


class ComparisonPage(QWidget):
    def __init__(self, state):
        super().__init__(); self.state = state
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName("comparisonContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 18, 24, 28)
        layout.setSpacing(16)
        scroll.setWidget(content)
        outer.addWidget(scroll)
        title = QLabel("Comparison"); title.setObjectName("pageTitle"); layout.addWidget(title)
        grid = QGridLayout()
        grid.setHorizontalSpacing(16); grid.setVerticalSpacing(20)
        grid.setColumnStretch(0, 1); grid.setColumnStretch(1, 1)
        self.original = ImagePanel("ORIGINAL")
        self.degraded = ImagePanel("BLURRED / DEGRADED")
        self.inverse = ImagePanel("INVERSE FILTER")
        self.wiener = ImagePanel("WIENER FILTER")
        grid.addWidget(self.original, 0, 0); grid.addWidget(self.degraded, 0, 1)
        grid.addWidget(self.inverse, 1, 0); grid.addWidget(self.wiener, 1, 1)
        layout.addLayout(grid)

        table_title = QLabel("PERFORMANCE COMPARISON")
        table_title.setObjectName("cardTitle"); table_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(table_title)
        self.table = QTableWidget(4, 3)
        self.table.setHorizontalHeaderLabels(["Performance Metric", "Inverse Filter", "Wiener Filter"])
        self.table.verticalHeader().hide()
        for column in range(3):
            self.table.horizontalHeader().setSectionResizeMode(column, QHeaderView.Stretch)
        self.table.horizontalHeader().setMinimumSectionSize(150)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.setShowGrid(True); self.table.setWordWrap(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header_height = 44
        self.table.horizontalHeader().setFixedHeight(header_height)
        table_height = header_height + (4 * 44) + (self.table.frameWidth() * 2)
        self.table.setFixedHeight(table_height)
        layout.addWidget(self.table)

        self.analysis = QLabel(); self.analysis.setWordWrap(True)
        self.analysis.setObjectName("analysisBox")
        self.analysis.setMinimumHeight(170)
        self.analysis.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.analysis.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(self.analysis)
        state.changed.connect(self.refresh); self.refresh()

    def refresh(self):
        d = self.state.data
        self.original.set_image(d.original); self.degraded.set_image(d.degraded)
        self.inverse.set_image(d.inverse); self.wiener.set_image(d.wiener)
        for row, name in enumerate(("MSE", "PSNR (dB)", "SSIM", "Processing Time (s)")):
            item = QTableWidgetItem(name); item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.table.setItem(row, 0, item)
        if not d.controlled:
            for row in range(3):
                self._set_value(row, 1, "N/A"); self._set_value(row, 2, "N/A")
        else:
            for column, metrics in ((1, d.inverse_metrics), (2, d.wiener_metrics)):
                for row, key in enumerate(("MSE", "PSNR", "SSIM")):
                    if not metrics: value = "—"
                    elif metrics[key] == float("inf"): value = "∞"
                    else:
                        decimals = 6 if key == "MSE" else 2 if key == "PSNR" else 4
                        value = f"{metrics[key]:.{decimals}f}"
                    self._set_value(row, column, value)
        analysis = comparison_text(
            d.inverse_metrics if d.controlled else None,
            d.wiener_metrics if d.controlled else None,
            d.inverse_time, d.wiener_time,
            ground_truth_available=d.controlled,
        )
        self.analysis.setText(f"RESULT ANALYSIS\n\n{analysis}")
        self._set_value(3, 1, "—" if d.inverse_time is None else f"{d.inverse_time:.4f}")
        self._set_value(3, 2, "—" if d.wiener_time is None else f"{d.wiener_time:.4f}")

    def _set_value(self, row: int, column: int, text: str):
        item = QTableWidgetItem(text); item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, column, item)
