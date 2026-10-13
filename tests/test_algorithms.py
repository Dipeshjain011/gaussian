import numpy as np

from evaluation.metrics import image_metrics
from image_processing.gaussian_degradation import gaussian_otf, gaussian_psf
from image_processing.inverse_filter import inverse_restore
from image_processing.preprocessing import gaussian_blur
from image_processing.wiener_filter import wiener_restore


def sample():
    image = np.zeros((64, 64), np.uint8)
    image[16:48, 16:48] = 220
    image[25:39, :] = 100
    return image


def test_gaussian_psf_is_normalized():
    assert np.isclose(gaussian_psf(15, 3).sum(), 1.0)


def test_restoration_shapes_and_finite_metrics():
    image = sample(); degraded = gaussian_blur(image, 15, 3); otf = gaussian_otf(image.shape, 15, 3)
    inverse = inverse_restore(degraded, otf, .01)[0]
    wiener = wiener_restore(degraded, otf, .01)[0]
    assert inverse.shape == image.shape == wiener.shape
    for result in (inverse, wiener):
        metrics = image_metrics(image, result)
        assert metrics["MSE"] >= 0 and np.isfinite(metrics["SSIM"])



def test_otf_has_unit_dc_and_blur_is_finite():
    image = sample()
    otf = gaussian_otf(image.shape, 15, 3)
    assert otf.shape == image.shape
    assert np.isclose(otf[0, 0], 1.0 + 0j, atol=1e-10)
    degraded = gaussian_blur(image, 15, 3)
    assert degraded.shape == image.shape
    assert np.all(np.isfinite(degraded))


def test_metrics_evaluate_displayable_clipped_result():
    reference = sample()
    candidate = reference.astype(float).copy()
    candidate[0, 0] = -30
    candidate[0, 1] = 300
    metrics = image_metrics(reference, candidate)
    clipped = np.clip(candidate, 0, 255)
    expected_mse = float(np.mean((reference.astype(float) - clipped) ** 2))
    assert np.isclose(metrics["MSE"], expected_mse)
    assert np.isfinite(metrics["SSIM"])


def test_noise_only_wiener_zero_noise_is_identity():
    from image_processing.wiener_filter import noise_only_wiener
    image = sample().astype(float)
    restored, _ = noise_only_wiener(image, 0.0)
    assert np.allclose(restored, image, atol=1e-10)


def test_restoration_metrics_use_original_sharp_reference():
    """Controlled-mode worker metrics must compare against the sharp original."""
    from workers.restoration_worker import restore_task

    class Context:
        def report(self, value, message):
            pass
        def check_cancelled(self):
            pass

    original = sample()
    degraded = gaussian_blur(original, 15, 3.0)
    otf = gaussian_otf(original.shape, 15, 3.0)
    result = restore_task(
        "wiener", degraded, original, True, 15, 3.0, 0.01, otf, 0.0
    )(Context())

    expected_against_original = image_metrics(original, result["image"])
    wrong_against_degraded = image_metrics(degraded, result["image"])
    assert result["metrics"] == expected_against_original
    assert result["metrics"] != wrong_against_degraded


def test_real_blurred_mode_does_not_report_reference_metrics():
    """A real blurred input without ground truth must not claim reference metrics."""
    from workers.restoration_worker import restore_task

    class Context:
        def report(self, value, message):
            pass
        def check_cancelled(self):
            pass

    degraded = gaussian_blur(sample(), 15, 3.0)
    otf = gaussian_otf(degraded.shape, 15, 3.0)
    result = restore_task(
        "wiener", degraded, None, False, 15, 3.0, 0.01, otf, 0.0
    )(Context())
    assert result["metrics"] is None
