from __future__ import annotations

import math
import numpy as np
from skimage.metrics import structural_similarity


def _intensity_range(reference: np.ndarray, candidate: np.ndarray) -> tuple[float, float, float]:
    """Return valid low/high bounds and data_range for metric/display consistency.

    Integer reference images define the expected image range (e.g. uint8 -> 0..255).
    Floating references in [0, 1] use that range; other floating references use 0..255
    when their observed scale exceeds 1.
    """
    if np.issubdtype(reference.dtype, np.integer):
        info = np.iinfo(reference.dtype)
        low, high = float(max(0, info.min)), float(info.max)
    else:
        combined_max = max(float(np.max(reference)), float(np.max(candidate)))
        low, high = (0.0, 1.0) if combined_max <= 1.0 else (0.0, 255.0)
    return low, high, high - low


def image_metrics(reference: np.ndarray, candidate: np.ndarray) -> dict[str, float]:
    """Calculate reference-based metrics on valid, consistently scaled image values.

    Candidate restoration values are clipped to the reference image's valid intensity
    range for evaluation, matching the image that can actually be displayed/saved.
    The raw restoration array itself is not modified.
    """
    reference_raw = np.asarray(reference)
    candidate_raw = np.asarray(candidate)
    if reference_raw.shape != candidate_raw.shape:
        raise ValueError("Images must have matching dimensions to calculate metrics.")
    if reference_raw.ndim not in (2, 3):
        raise ValueError("Metrics require a grayscale or color image.")
    if not np.all(np.isfinite(reference_raw)) or not np.all(np.isfinite(candidate_raw)):
        raise ValueError("Images must contain only finite values to calculate metrics.")

    low, high, data_range = _intensity_range(reference_raw, candidate_raw)
    ref = np.clip(reference_raw.astype(np.float64), low, high)
    cand = np.clip(candidate_raw.astype(np.float64), low, high)
    mse = float(np.mean((ref - cand) ** 2))
    psnr = float("inf") if mse == 0 else 10.0 * math.log10((data_range ** 2) / mse)
    kwargs = {"data_range": data_range}
    if ref.ndim == 3:
        kwargs["channel_axis"] = -1
    # SSIM requires a window no larger than the smallest image dimension.
    min_dim = min(ref.shape[:2])
    win_size = min(7, min_dim if min_dim % 2 else min_dim - 1)
    if win_size < 3:
        raise ValueError("Images must be at least 3 pixels wide and high for SSIM.")
    ssim = float(structural_similarity(ref, cand, win_size=win_size, **kwargs))
    return {"MSE": mse, "PSNR": psnr, "SSIM": ssim}
