from __future__ import annotations

import time
import pandas as pd

from evaluation.metrics import image_metrics
from image_processing.gaussian_degradation import gaussian_otf
from image_processing.inverse_filter import inverse_restore
from image_processing.preprocessing import add_gaussian_noise, gaussian_blur
from image_processing.wiener_filter import wiener_restore


def run_noise_experiment(image, levels=(0,.01,.03,.05,.1), sigma=3.0, kernel_size=15, threshold=.01, wiener_k=.01):
    records = []; base = gaussian_blur(image, kernel_size, sigma); otf = gaussian_otf(image.shape[:2], kernel_size, sigma)
    rng = __import__("numpy").random.default_rng(42)
    for level in levels:
        degraded = add_gaussian_noise(base, level, rng)
        for method in ("Inverse", "Wiener"):
            start = time.perf_counter()
            restored = inverse_restore(degraded, otf, threshold)[0] if method == "Inverse" else wiener_restore(degraded, otf, wiener_k)[0]
            elapsed = time.perf_counter() - start; metrics = image_metrics(image, restored)
            records.append({"Experiment":"Noise", "Level":level, "Sigma":sigma, "Noise":level, "Method":method, **metrics, "Time":elapsed})
    return pd.DataFrame(records)

