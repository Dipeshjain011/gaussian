from pathlib import Path
import numpy as np
from PySide6.QtWidgets import QFileDialog, QFormLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from utils.image_utils import save_image


class ExportPage(QWidget):
    def __init__(self,state):
        super().__init__(); self.state=state
        layout=QVBoxLayout(self); title=QLabel("Export"); title.setObjectName("pageTitle"); layout.addWidget(title)
        text=QLabel("Save restored images, a four-panel comparison, or experiment results. Exports contain only results calculated in this session."); text.setWordWrap(True); layout.addWidget(text)
        form=QFormLayout()
        for label,key in (("Original image","original"),("Degraded image","degraded"),("Inverse result","inverse"),("Wiener result","wiener")):
            button=QPushButton(f"Save {label}"); button.clicked.connect(lambda checked=False,k=key:self.save_one(k)); form.addRow(label,button)
        compare=QPushButton("Save Comparison Image"); compare.clicked.connect(self.save_comparison); form.addRow("All major images",compare)
        csv=QPushButton("Save Experiment CSV"); csv.clicked.connect(self.save_csv); form.addRow("Experiment data",csv)
        layout.addLayout(form); layout.addStretch()

    def save_one(self,key):
        image=getattr(self.state.data,key)
        if image is None: QMessageBox.information(self,"Export",f"No {key} image is available yet."); return
        path,_=QFileDialog.getSaveFileName(self,"Save image",f"{key}.png","PNG (*.png);;JPEG (*.jpg);;TIFF (*.tiff)")
        if path and not save_image(path,image): QMessageBox.warning(self,"Export failed","The image could not be saved.")
        elif path: self.state.notify(f"Saved {Path(path).name}")

    def save_comparison(self):
        d=self.state.data; images=[d.original,d.degraded,d.inverse,d.wiener]
        if any(item is None for item in images): QMessageBox.information(self,"Export","Run both restoration methods first."); return
        import cv2
        h=max(i.shape[0] for i in images); w=max(i.shape[1] for i in images)
        normalized=[]
        for image in images:
            item=image if image.ndim==3 else cv2.cvtColor(image,cv2.COLOR_GRAY2RGB)
            normalized.append(cv2.resize(item,(w,h)))
        canvas=np.vstack((np.hstack(normalized[:2]),np.hstack(normalized[2:])))
        path,_=QFileDialog.getSaveFileName(self,"Save comparison","comparison.png","PNG (*.png);;JPEG (*.jpg)")
        if path and save_image(path,canvas): self.state.notify(f"Saved {Path(path).name}")

    def save_csv(self):
        frame=self.state.data.experiments
        if frame.empty: QMessageBox.information(self,"Export","Run an experiment first."); return
        path,_=QFileDialog.getSaveFileName(self,"Save experiment data","experiment_results.csv","CSV (*.csv)")
        if path:
            try: frame.to_csv(path,index=False); self.state.notify(f"Saved {Path(path).name}")
            except Exception as exc: QMessageBox.warning(self,"Export failed",str(exc))

