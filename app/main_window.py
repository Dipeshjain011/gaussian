from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow, QStackedWidget, QStatusBar, QVBoxLayout, QWidget

from .comparison_page import ComparisonPage
from .dashboard import DashboardPage
from .experiments_page import ExperimentsPage
from .export_page import ExportPage
from .frequency_page import FrequencyPage
from .restoration_page import RestorationPage
from .state import ProjectState


STYLE = """
QMainWindow, QWidget { background: #ffffff; color: #1f2937; font-family: 'Segoe UI'; font-size: 14px; }
QListWidget { background: #f3f4f6; border: none; padding: 14px 8px; outline: 0; }
QListWidget::item { padding: 14px 12px; margin: 3px; border-radius: 7px; color: #4b5563; }
QListWidget::item:selected { background: #2563eb; color: white; }
QFrame#card { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; }
QLabel#cardTitle { font-size: 16px; font-weight: 700; color: #111827; padding-bottom: 4px; }
QLabel#pageTitle { font-size: 26px; font-weight: 750; color: #111827; padding: 8px 0; }
QLabel#heroTitle { font-size: 38px; font-weight: 800; color: #111827; }
QLabel#heroSubtitle { color: #2563eb; font-weight: 700; letter-spacing: 1px; }
QLabel#flowLabel, QLabel#analysisBox { background: #f9fafb; border: 1px solid #e5e7eb; padding: 18px; border-radius: 9px; color: #374151; }
QLabel#muted { color: #6b7280; }
QLabel#imagePanel { background: #f9fafb; border: 1px dashed #9ca3af; border-radius: 8px; color: #6b7280; }
QPushButton { background: #f3f4f6; border: 1px solid #d1d5db; padding: 9px 14px; border-radius: 7px; color: #1f2937; }
QWidget#imageToolbar QPushButton { padding: 7px 6px; min-width: 36px; }
QPushButton:hover { background: #e5e7eb; }
QPushButton#primaryButton { background: #2563eb; border: none; font-weight: 700; padding: 13px; }
QPushButton#primaryButton:hover { background: #3b82f6; }
QComboBox, QDoubleSpinBox { background: #ffffff; border: 1px solid #d1d5db; border-radius: 6px; padding: 7px; color: #1f2937; }
QTableWidget { background: #ffffff; alternate-background-color: #f9fafb; border: 1px solid #e5e7eb; gridline-color: #e5e7eb; }
QHeaderView::section { background: #f3f4f6; color: #1f2937; border: none; padding: 8px; }
QScrollArea, QWidget#comparisonContent { background: #ffffff; }
QStatusBar { background: #f3f4f6; color: #4b5563; }
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Gaussian Blur Removal — Frequency Domain Restoration")
        self.resize(1360, 860); self.setMinimumSize(1050, 700); self.setStyleSheet(STYLE)
        self.state = ProjectState()
        central = QWidget(); self.setCentralWidget(central); root = QHBoxLayout(central); root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        sidebar = QWidget(); sidebar.setFixedWidth(235); side = QVBoxLayout(sidebar); side.setContentsMargins(0,20,0,0)
        brand = QLabel("  ◉  GAUSSIAN\n      RESTORE LAB"); brand.setStyleSheet("font-size:17px;font-weight:800;color:white;padding:12px"); side.addWidget(brand)
        self.nav = QListWidget(); self.labels = ["⌂  Dashboard","▣  Image Restoration","◈  Frequency Analysis","⇄  Comparison","⚗  Experiments","⇧  Export"]
        for label in self.labels: self.nav.addItem(QListWidgetItem(label))
        side.addWidget(self.nav,1); version=QLabel("  Traditional DIP • v1.0"); version.setObjectName("muted"); side.addWidget(version); side.addSpacing(16); root.addWidget(sidebar)
        self.stack = QStackedWidget(); root.addWidget(self.stack,1)
        dashboard=DashboardPage(); restoration=RestorationPage(self.state)
        for page in (dashboard,restoration,FrequencyPage(self.state),ComparisonPage(self.state),ExperimentsPage(self.state),ExportPage(self.state)): self.stack.addWidget(page)
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex); dashboard.start_requested.connect(lambda:self.nav.setCurrentRow(1)); self.nav.setCurrentRow(0)
        status=QStatusBar(); self.setStatusBar(status); self.state.message.connect(lambda message:status.showMessage(message,5000)); status.showMessage("Ready")
