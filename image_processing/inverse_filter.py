from __future__ import annotations

import numpy as np

from .frequency_domain import fft_channels, reconstruct


def inverse_restore(image: np.ndarray, otf: np.ndarray, threshold: float):
    if not np.isfinite(threshold) or not 0 < threshold < 1:
        raise ValueError("Inverse-filter relative H threshold must be between zero and one.")
    if image.ndim not in (2, 3) or image.shape[:2] != otf.shape:
        raise ValueError("Image and transfer-function dimensions must match.")
    if not np.all(np.isfinite(image)) or not np.all(np.isfinite(otf)):
        raise ValueError("Image and transfer function must contain only finite values.")
    magnitude = np.abs(otf)
    cutoff = float(threshold) * float(np.max(magnitude))
    mask = magnitude >= cutoff
    # Relative cutoff avoids amplifying frequencies unsupported by H. epsilon
    # is the squared cutoff in |H|^2 units, so the requested stabilized form
    # remains bounded and complex-valued.
    epsilon = cutoff * cutoff
    denominator = magnitude ** 2 + epsilon
    response = np.zeros_like(otf, dtype=np.complex128)
    response[mask] = np.conj(otf[mask]) / denominator[mask]
    restored_fft = [spectrum * response for spectrum in fft_channels(image)]
    result = reconstruct(restored_fft, image)
    if not np.all(np.isfinite(result)):
        raise FloatingPointError("Inverse restoration produced NaN or infinite values.")
    return result, response, restored_fft

