from PySide6.QtWidgets import QComboBox,QHBoxLayout,QLabel,QMessageBox,QProgressBar,QPushButton,QTableWidget,QTableWidgetItem,QVBoxLayout,QWidget
from utils.thread_utils import TaskController
from visualization.plots import PlotCanvas
from workers.experiment_worker import experiment_task

class ExperimentsPage(QWidget):
    def __init__(self,state):
        super().__init__();self.state=state;self.controller=TaskController(self);layout=QVBoxLayout(self);title=QLabel("Experiments");title.setObjectName("pageTitle");layout.addWidget(title);controls=QHBoxLayout();self.kind=QComboBox();self.kind.addItems(["Blur levels: σ = 1, 2, 3, 5, 7","Noise levels: 0, .01, .03, .05, .1"]);self.run_btn=QPushButton("Run Experiment");self.cancel_btn=QPushButton("Cancel Processing");self.save_btn=QPushButton("Save Graph");self.cancel_btn.setEnabled(False);self.run_btn.clicked.connect(self.run);self.cancel_btn.clicked.connect(self.controller.cancel);self.save_btn.clicked.connect(self.save_graph);controls.addWidget(self.kind,1);controls.addWidget(self.run_btn);controls.addWidget(self.cancel_btn);controls.addWidget(self.save_btn);layout.addLayout(controls);self.progress=QProgressBar();self.progress.setRange(0,100);layout.addWidget(self.progress);self.status=QLabel("Ready");self.status.setObjectName("muted");layout.addWidget(self.status);self.table=QTableWidget();layout.addWidget(self.table,1);self.canvas=PlotCanvas(1,3,3);layout.addWidget(self.canvas,1)
        self.controller.progress.connect(self.progressed);self.controller.result.connect(self.completed);self.controller.error.connect(lambda m:QMessageBox.warning(self,"Experiment failed",m));self.controller.cancelled.connect(self.cancelled);self.controller.busy_changed.connect(self.busy)
    def busy(self,value):self.run_btn.setEnabled(not value);self.kind.setEnabled(not value);self.cancel_btn.setEnabled(value)
    def progressed(self,value,message):self.progress.setValue(value);self.status.setText(message);self.state.message.emit(message)
    def cancelled(self):self.status.setText("Processing cancelled.");self.state.message.emit("Processing cancelled.")
    def run(self):
        d=self.state.data
        if d.original is None or not d.controlled:return QMessageBox.information(self,"Experiments","Controlled Experiment mode with an original image is required.")
        self.progress.setValue(0);self.controller.start(experiment_task(d.original,"Blur" if self.kind.currentIndex()==0 else "Noise"))
    def completed(self,frame):
        self.state.data.experiments=frame;self.fill_table(frame);self.plot(frame);self.progress.setValue(100);self.status.setText("Experiment completed");self.state.notify("Experiment completed")
    def fill_table(self,frame):
        columns=["Level","Method","MSE","PSNR","SSIM","Time"];self.table.setRowCount(len(frame));self.table.setColumnCount(len(columns));self.table.setHorizontalHeaderLabels(columns)
        for r,(_,row) in enumerate(frame.iterrows()):
            for c,key in enumerate(columns):self.table.setItem(r,c,QTableWidgetItem(str(row[key]) if key=="Method" else f"{float(row[key]):.5f}"))
        self.table.resizeColumnsToContents()
    def plot(self,frame):
        self.canvas.figure.clear();axes=self.canvas.figure.subplots(1,3);x_label="Sigma" if frame.iloc[0]["Experiment"]=="Blur" else "Noise"
        for method,group in frame.groupby("Method"):
            for ax,metric in zip(axes,("PSNR","MSE","SSIM")):ax.plot(group.Level,group[metric],"o-",label=method)
        for ax,metric in zip(axes,("PSNR","MSE","SSIM")):ax.set_xlabel(x_label);ax.set_ylabel(metric);ax.grid(alpha=.25);ax.legend()
        self.canvas.figure.tight_layout();self.canvas.draw_idle()
    def save_graph(self):
        from PySide6.QtWidgets import QFileDialog
        path,_=QFileDialog.getSaveFileName(self,"Save experiment graph","experiment_graph.png","PNG (*.png);;PDF (*.pdf);;SVG (*.svg)")
        if path:self.canvas.figure.savefig(path,dpi=180,bbox_inches="tight");self.state.notify("Experiment graph saved")
