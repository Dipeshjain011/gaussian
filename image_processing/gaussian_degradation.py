from __future__ import annotations

import cv2
import numpy as np


def gaussian_psf(kernel_size: int, sigma: float) -> np.ndarray:
    if kernel_size < 3 or kernel_size % 2 == 0:
        raise ValueError("Gaussian kernel size must be an odd number of at least 3.")
    if not np.isfinite(sigma) or sigma <= 0:
        raise ValueError("Sigma must be a finite number greater than zero.")
    kernel_1d = cv2.getGaussianKernel(kernel_size, sigma)
    psf = kernel_1d @ kernel_1d.T
    return psf / psf.sum()


def psf_to_otf(psf: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    """Convert a centred spatial PSF to an FFT-compatible optical transfer function."""
    psf = np.asarray(psf, dtype=np.float64)
    if psf.ndim != 2 or not np.all(np.isfinite(psf)) or psf.sum() <= 0:
        raise ValueError("PSF must be a finite, nonempty 2D array with positive sum.")
    if len(shape) != 2 or min(shape) < 1 or psf.shape[0] > shape[0] or psf.shape[1] > shape[1]:
        raise ValueError("PSF dimensions must fit the requested OTF dimensions.")
    psf = psf / psf.sum()
    padded = np.zeros(shape, dtype=np.float64)
    kh, kw = psf.shape
    padded[:kh, :kw] = psf
    # The centered PSF's sample at (kh//2, kw//2) is zero lag. Shift by
    # the PSF origin (not half the padded image dimensions) before FFT.
    padded = np.roll(padded, -(kh // 2), axis=0)
    padded = np.roll(padded, -(kw // 2), axis=1)
    return np.asarray(np.fft.fft2(padded), dtype=np.complex128)


def gaussian_otf(shape: tuple[int, int], kernel_size: int, sigma: float) -> np.ndarray:
    return psf_to_otf(gaussian_psf(kernel_size, sigma), shape)

