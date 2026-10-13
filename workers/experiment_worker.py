from __future__ import annotations

import time
import pandas as pd
import numpy as np

from evaluation.metrics import image_metrics
from image_processing.gaussian_degradation import gaussian_otf
from image_processing.inverse_filter import inverse_restore
from image_processing.preprocessing import add_gaussian_noise, gaussian_blur
from image_processing.wiener_filter import wiener_restore


def experiment_task(image, kind):
    def task(context):
        levels = (1, 2, 3, 5, 7) if kind == "Blur" else (0, .01, .03, .05, .1)
        records, total, done = [], len(levels) * 2, 0
        base = gaussian_blur(image, 15, 3.0) if kind == "Noise" else None
        rng = np.random.default_rng(42)
        for level in levels:
            context.check_cancelled()
            sigma = float(level) if kind == "Blur" else 3.0
            degraded = gaussian_blur(image, 21, sigma) if kind == "Blur" else add_gaussian_noise(base, level, rng)
            kernel = 21 if kind == "Blur" else 15
            otf = gaussian_otf(image.shape[:2], kernel, sigma)
            for method in ("Inverse", "Wiener"):
                context.report(round(done / total * 100), f"Experiment {done + 1} / {total}: {method}")
                start = time.perf_counter()
                restored = inverse_restore(degraded, otf, .01)[0] if method == "Inverse" else wiener_restore(degraded, otf, .01)[0]
                elapsed = time.perf_counter() - start
                metrics = image_metrics(image, restored)
                records.append({"Experiment": kind, "Level": level, "Sigma": sigma,
                                "Noise": level if kind == "Noise" else 0.0,
                                "Method": method, **metrics, "Time": elapsed})
                done += 1
        context.report(100, "Experiment completed")
        return pd.DataFrame(records)
    return task
