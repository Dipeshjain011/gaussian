from __future__ import annotations

import time
import pandas as pd

from evaluation.metrics import image_metrics
from image_processing.gaussian_degradation import gaussian_otf
from image_processing.inverse_filter import inverse_restore
from image_processing.preprocessing import gaussian_blur
from image_processing.wiener_filter import wiener_restore


def run_blur_experiment(image, sigmas=(1,2,3,5,7), kernel_size=21, threshold=.01, wiener_k=.01):
    records = []
    for sigma in sigmas:
        degraded = gaussian_blur(image, kernel_size, float(sigma))
        otf = gaussian_otf(image.shape[:2], kernel_size, float(sigma))
        for method in ("Inverse", "Wiener"):
            start = time.perf_counter()
            restored = inverse_restore(degraded, otf, threshold)[0] if method == "Inverse" else wiener_restore(degraded, otf, wiener_k)[0]
            elapsed = time.perf_counter() - start; metrics = image_metrics(image, restored)
            records.append({"Experiment":"Blur", "Level":sigma, "Sigma":sigma, "Noise":0.0, "Method":method, **metrics, "Time":elapsed})
    return pd.DataFrame(records)

