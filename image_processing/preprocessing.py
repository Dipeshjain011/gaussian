from __future__ import annotations

import cv2
import numpy as np


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def read_image(path: str) -> np.ndarray:
    data = np.fromfile(path, dtype=np.uint8)
    image = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError("The selected file is not a valid or readable image.")
    if image.ndim == 2:
        return image
    if image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def gaussian_blur(image: np.ndarray, kernel_size: int, sigma: float) -> np.ndarray:
    if image.ndim not in (2, 3) or image.shape[0] < kernel_size or image.shape[1] < kernel_size:
        raise ValueError("Image dimensions must be at least as large as the Gaussian kernel.")
    if kernel_size < 3 or kernel_size % 2 == 0:
        raise ValueError("Gaussian kernel size must be an odd number of at least 3.")
    if not np.isfinite(sigma) or sigma <= 0:
        raise ValueError("Sigma must be greater than zero.")
    from .gaussian_degradation import gaussian_psf, psf_to_otf
    # Match psf_to_otf: periodic (circular) convolution with this exact discrete PSF.
    psf = gaussian_psf(kernel_size, sigma)
    otf = psf_to_otf(psf, image.shape[:2])
    source = np.asarray(image, dtype=np.float64)
    if source.ndim == 2:
        return np.real(np.fft.ifft2(np.fft.fft2(source) * otf))
    channels = [np.real(np.fft.ifft2(np.fft.fft2(source[..., i]) * otf)) for i in range(source.shape[2])]
    return np.stack(channels, axis=2)


def add_gaussian_noise(image: np.ndarray, level: float, rng=None) -> np.ndarray:
    """Add zero-mean Gaussian noise; level is sigma as a fraction of 255."""
    if not np.isfinite(level) or not 0 <= level <= 1:
        raise ValueError("Noise level must be between 0 and 1.")
    if level == 0:
        return image.copy()
    rng = rng or np.random.default_rng()
    source = np.asarray(image, dtype=np.float64)
    scale = 255.0 if np.max(source) > 1.0 else 1.0
    noisy = source + rng.normal(0.0, level * scale, source.shape)
    return np.clip(noisy, 0.0, scale)

