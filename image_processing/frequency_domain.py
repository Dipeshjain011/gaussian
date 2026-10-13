from __future__ import annotations

import numpy as np


def channels(image: np.ndarray):
    return [image] if image.ndim == 2 else [image[..., i] for i in range(image.shape[2])]


def fft_channels(image: np.ndarray) -> list[np.ndarray]:
    return [np.fft.fft2(channel.astype(np.float64)) for channel in channels(image)]


def log_magnitude_spectrum(image: np.ndarray) -> np.ndarray:
    gray = image if image.ndim == 2 else np.mean(image[..., :3], axis=2)
    shifted = np.fft.fftshift(np.fft.fft2(gray.astype(np.float64)))
    return np.log1p(np.abs(shifted))


def reconstruct(transforms: list[np.ndarray], reference: np.ndarray) -> np.ndarray:
    """Reconstruct channel arrays without display-range clipping or quantization."""
    restored = [np.real(np.fft.ifft2(item)) for item in transforms]
    return restored[0] if reference.ndim == 2 else np.stack(restored, axis=2)

