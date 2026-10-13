from __future__ import annotations

import numpy as np

from .frequency_domain import fft_channels, reconstruct


def wiener_restore(image: np.ndarray, otf: np.ndarray, k: float, noise_variance: float | None = None):
    if not np.isfinite(k) or k <= 0:
        raise ValueError("Wiener K must be finite and greater than zero.")
    if image.ndim not in (2, 3) or image.shape[:2] != otf.shape:
        raise ValueError("Image and transfer-function dimensions must match.")
    if not np.all(np.isfinite(image)) or not np.all(np.isfinite(otf)):
        raise ValueError("Image and transfer function must contain only finite values.")
    data = np.asarray(image, dtype=np.float64)
    scale = 255.0 if np.max(data) > 1.0 else 1.0
    magnitude_squared = np.abs(otf) ** 2
    # K is a constant dimensionless N/S approximation on normalized [0,1]
    # image intensities; with noise variance, estimate N/S from observed power.
    if noise_variance is not None:
        if not np.isfinite(noise_variance) or noise_variance < 0:
            raise ValueError("Noise variance must be finite and nonnegative.")
        signal_power = float(np.mean(data * data))
        estimated_ns_ratio = float(noise_variance / max(signal_power, np.finfo(float).eps))
        k_effective = max(float(k), estimated_ns_ratio)
    else:
        # The UI's K is dimensionless; convert it to the 0..1 image-power scale.
        k_effective = float(k)
    denominator = magnitude_squared + k_effective
    if not np.all(np.isfinite(denominator)) or np.any(denominator <= 0):
        raise FloatingPointError("Wiener denominator is not finite and positive.")
    response = np.conj(otf) / denominator
    restored_fft = [spectrum * response for spectrum in fft_channels(image)]
    result = reconstruct(restored_fft, image)
    if not np.all(np.isfinite(result)):
        raise FloatingPointError("Wiener restoration produced NaN or infinite values.")
    return result, response, restored_fft


def noise_only_wiener(image: np.ndarray, noise_variance: float):
    """Wiener denoising for additive white noise only (assumes H=1).

    ``noise_variance`` must be expressed in squared units matching ``image``:
    for uint8-like values in 0..255 use intensity-units squared; for normalized
    float images in 0..1 use normalized-intensity squared. The periodogram below
    uses |FFT|^2 / N, so its expected white-noise level is the variance in those
    same units.
    """
    if not np.isfinite(noise_variance) or noise_variance < 0:
        raise ValueError("Noise variance must be finite and nonnegative.")
    data = np.asarray(image, dtype=np.float64)
    if data.ndim not in (2, 3) or data.size == 0 or not np.all(np.isfinite(data)):
        raise ValueError("Image must be a nonempty finite grayscale or multichannel array.")

    filtered = []
    responses = []
    channel_arrays = [data] if data.ndim == 2 else [data[..., i] for i in range(data.shape[2])]
    for channel in channel_arrays:
        spectrum = np.fft.fft2(channel)
        # Parseval-consistent periodogram: E[|FFT(noise)|^2 / N] = variance.
        observed_psd = (np.abs(spectrum) ** 2) / channel.size
        noise_psd = float(noise_variance)  # flat PSD for spatially white noise
        estimated_signal_psd = np.maximum(observed_psd - noise_psd, 0.0)
        if noise_psd == 0:
            response = np.ones_like(estimated_signal_psd)
        else:
            response = estimated_signal_psd / (estimated_signal_psd + noise_psd)
        responses.append(response)
        filtered.append(np.real(np.fft.ifft2(response * spectrum)))

    result = filtered[0] if data.ndim == 2 else np.stack(filtered, axis=2)
    if not np.all(np.isfinite(result)):
        raise FloatingPointError("Noise-only Wiener filtering produced invalid values.")
    return result, responses
