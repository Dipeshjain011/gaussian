from __future__ import annotations

import time
import numpy as np

from evaluation.metrics import image_metrics
from image_processing.frequency_domain import log_magnitude_spectrum
from image_processing.gaussian_degradation import gaussian_otf
from image_processing.inverse_filter import inverse_restore
from image_processing.preprocessing import add_gaussian_noise, gaussian_blur
from image_processing.wiener_filter import wiener_restore


def blur_task(image, kernel, sigma):
    def task(context):
        context.report(15, "Applying Gaussian blur...")
        degraded = gaussian_blur(image, kernel, sigma)
        context.report(65, "Creating degradation model H(u,v)...")
        otf = gaussian_otf(image.shape[:2], kernel, sigma)
        context.report(100, "Gaussian blur completed")
        return {"degraded": degraded, "otf": otf}
    return task


def noise_task(image, level):
    def task(context):
        context.report(20, "Generating Gaussian noise...")
        result = add_gaussian_noise(image, level)
        context.report(100, "Noise applied")
        return result
    return task


def restore_task(method, degraded, reference, controlled, kernel, sigma, parameter, otf=None, noise_level=0.0):
    # Snapshot the sharp reference before the worker runs. In controlled mode this
    # must be the original image, never the blurred/degraded image.
    ground_truth_reference = None if reference is None else np.asarray(reference).copy()
    degraded_input = np.asarray(degraded).copy()

    if controlled and ground_truth_reference is None:
        raise ValueError("Ground-truth metrics require the original sharp reference image.")
    if controlled and ground_truth_reference.shape != degraded_input.shape:
        raise ValueError("The sharp reference and degraded image must have matching dimensions.")

    def task(context):
        context.report(10, "Creating degradation model H(u,v)...")
        # Reuse the exact OTF generated alongside the controlled blur when
        # available; for an externally loaded blurred image, controls describe
        # the assumed degradation model.
        transfer_function = otf if otf is not None else gaussian_otf(degraded_input.shape[:2], kernel, sigma)
        context.report(30, f"Applying {method} filter...")
        start = time.perf_counter()
        if method == "inverse":
            restored, response, spectrum = inverse_restore(degraded_input, transfer_function, parameter)
        else:
            noise_variance = None
            if noise_level and noise_level > 0:
                scale = 255.0 if np.max(degraded_input) > 1 else 1.0
                noise_variance = (noise_level * scale) ** 2
            restored, response, spectrum = wiener_restore(degraded_input, transfer_function, parameter, noise_variance)
        if method == "inverse":
            cutoff = float(parameter) * float(np.max(np.abs(transfer_function)))
            denominator = np.abs(transfer_function) ** 2 + cutoff ** 2
        else:
            scale = 255.0 if np.max(degraded_input) > 1 else 1.0
            k_effective = float(parameter)
            if noise_level and noise_level > 0:
                estimated_noise_variance = (noise_level * scale) ** 2
                k_effective = max(k_effective, estimated_noise_variance / max(float(np.mean(np.asarray(degraded_input, dtype=np.float64) ** 2)), np.finfo(float).eps))
            denominator = np.abs(transfer_function) ** 2 + k_effective
        logger = __import__("logging").getLogger(__name__)
        logger.info("%s restoration diagnostics: degraded[min,max]=(%g,%g), |H|[min,max]=(%g,%g), denominator[min,max]=(%g,%g), output[min,max]=(%g,%g), shape=%s",
                    method, float(np.min(degraded_input)), float(np.max(degraded_input)), float(np.min(np.abs(transfer_function))), float(np.max(np.abs(transfer_function))),
                    float(np.min(denominator)), float(np.max(denominator)), float(np.min(restored)), float(np.max(restored)), restored.shape)
        if restored.shape != degraded_input.shape or not np.all(np.isfinite(restored)):
            raise FloatingPointError("Restoration output failed shape or finite-value checks.")
        elapsed = time.perf_counter() - start
        context.report(75, "Calculating quality metrics...")
        # Metrics are always computed against the preserved original sharp image in
        # controlled experiments. Real-blurred mode has no ground truth and must
        # never report reference-based MSE/PSNR/SSIM.
        metrics = image_metrics(ground_truth_reference, restored) if controlled else None
        context.report(100, "Restoration completed")
        return {"method": method, "image": restored, "response": response,
                "spectrum": spectrum, "otf": transfer_function, "time": elapsed, "metrics": metrics}
    return task


def frequency_task(original, degraded, otf, kernel, sigma, response):
    """Build a worker for frequency analysis without shadowing closure inputs."""
    # Copy references into the closure under distinct names. Assigning to a name
    # inside task() that also exists in the enclosing scope makes it local to
    # task(), which caused UnboundLocalError before np.asarray could run.
    original_input = original
    degraded_input = degraded

    def task(context):
        original_array = np.asarray(original_input)
        degraded_array = np.asarray(degraded_input)
        if original_array.ndim not in (2, 3) or degraded_array.ndim not in (2, 3):
            raise ValueError("Frequency analysis expects grayscale or color images.")
        if degraded_array.size == 0 or degraded_array.shape[0] == 0 or degraded_array.shape[1] == 0:
            raise ValueError("The degraded image has no pixels to analyze.")
        if not np.all(np.isfinite(degraded_array)) or not np.all(np.isfinite(original_array)):
            raise ValueError("The original or degraded image contains invalid numerical values.")
        if original_array.shape[:2] != degraded_array.shape[:2]:
            raise ValueError("Original and degraded images must have matching dimensions.")
        context.report(15, "Calculating original FFT...")
        original_spectrum = log_magnitude_spectrum(original_array)
        context.report(45, "Calculating degraded FFT...")
        # Spectrum is calculated from the exact degraded image returned for preview.
        degraded_spectrum = log_magnitude_spectrum(degraded_array)
        if otf is None:
            otf_value = gaussian_otf(degraded_array.shape[:2], kernel, sigma)
        else:
            otf_value = otf
        result = {"original": original_array.copy(), "degraded": degraded_array.copy(),
                  "original_spectrum": original_spectrum, "degraded_spectrum": degraded_spectrum,
                  "otf": otf_value, "h_display": np.fft.fftshift(np.abs(otf_value)),
                  "response": None if response is None else np.fft.fftshift(np.log1p(np.abs(response)))}
        context.report(100, "Frequency analysis completed")
        return result
    return task
