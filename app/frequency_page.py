import logging
import numpy as np

from PySide6.QtWidgets import QLabel,QMessageBox,QProgressBar,QPushButton,QVBoxLayout,QWidget
from utils.thread_utils import TaskController
from visualization.plots import PlotCanvas,show_heatmap
from workers.restoration_worker import frequency_task

logger = logging.getLogger(__name__)

class FrequencyPage(QWidget):
    def __init__(self,state):
        super().__init__();self.state=state;self.controller=TaskController(self);layout=QVBoxLayout(self);title=QLabel("Frequency Analysis");title.setObjectName("pageTitle");layout.addWidget(title);text=QLabel("Spatial: g(x,y) = h(x,y) * f(x,y)\nFrequency: G(u,v) = H(u,v)F(u,v) + N(u,v)");layout.addWidget(text);self.button=QPushButton("Analyze Frequency Domain");self.button.clicked.connect(self.analyze);layout.addWidget(self.button);self.progress=QProgressBar();self.progress.hide();layout.addWidget(self.progress);self.canvas=PlotCanvas(2,3,7);layout.addWidget(self.canvas,1);self.controller.progress.connect(self.progressed);self.controller.result.connect(self.render);self.controller.error.connect(lambda m:QMessageBox.warning(self,"Frequency analysis failed",m));self.controller.busy_changed.connect(self.busy)
    def busy(self,value):self.button.setEnabled(not value);self.progress.setVisible(value)
    def progressed(self,v,m):self.progress.setValue(v);self.state.message.emit(m)
    def analyze(self):
        d=self.state.data
        if d.original is None or d.degraded is None:return QMessageBox.information(self,"Frequency analysis","Load an image and create or select a degraded image first.")
        logger.debug("Frequency analysis input: original=%s %s, degraded=%s %s", d.original.shape, d.original.dtype, d.degraded.shape, d.degraded.dtype)
        response=d.wiener_response if d.wiener_response is not None else d.inverse_response;self.controller.start(frequency_task(d.original,d.degraded,d.otf,d.kernel_size,d.sigma,response))
    def render(self,r):
        try:
            degraded=r["degraded"]
            if degraded is None or degraded.size == 0 or not np.all(np.isfinite(degraded)):
                raise ValueError("Generated degraded image is empty or contains invalid values.")
            logger.debug("Rendering degraded image: shape=%s dtype=%s axes=%s", degraded.shape, degraded.dtype, (1, 0))
            self.state.data.otf=r["otf"]
            self.canvas.figure.clear();axes=self.canvas.figure.subplots(2,3)
            show_heatmap(axes[0,0],r["original"],"Original image","gray" if r["original"].ndim==2 else None)
            show_heatmap(axes[0,1],r["original_spectrum"],"Original DFT spectrum")
            show_heatmap(axes[0,2],r["h_display"],"Gaussian H(u,v)","viridis")
            show_heatmap(axes[1,0],degraded,"Degraded image","gray" if degraded.ndim==2 else None)
            show_heatmap(axes[1,1],r["degraded_spectrum"],"Degraded DFT spectrum")
            if r["response"] is None:axes[1,2].text(.5,.5,"Run a restoration to view\nits filter response",ha="center",va="center");axes[1,2].axis("off")
            else:show_heatmap(axes[1,2],r["response"],"Restoration filter response")
            self.canvas.figure.tight_layout();self.canvas.draw();logger.debug("Degraded image preview rendered successfully")
            self.state.notify("Frequency analysis updated")
        except Exception as exc:
            logger.exception("Frequency analysis preview rendering failed")
            QMessageBox.warning(self,"Frequency analysis failed",f"Could not display the analyzed images: {exc}")
