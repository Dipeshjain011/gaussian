<<<<<<< HEAD
﻿# Gaussian Blur Removal Using Frequency Domain Restoration

A native PySide6 desktop application for demonstrating Gaussian degradation and image restoration with traditional Digital Image Processing techniques. It supports controlled experiments with a known original image and restoration of real blurred images without claiming unavailable ground-truth metrics.

## Features

- Gaussian blur and optional Gaussian noise controls
- FFT/DFT spectra and the Gaussian degradation response `H(u,v)`
- Stabilized inverse filtering and regularized Wiener filtering
- Dynamic MSE, PSNR, SSIM, and processing-time comparison
- Automated blur-level and noise-level experiments with graphs
- PNG/JPEG/TIFF image export, comparison export, and CSV experiment export
- Friendly validation for missing images and invalid parameters
- Reusable `QThread`/worker architecture with progress signals and cooperative cancellation
- Large-image processing copies bounded to 2048 px while preserving the source file
- Zoom, fit, reset, and save controls on result viewers

## Install and run

Python 3.10 or later is recommended.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

## Suggested demonstration

1. Open **Image Restoration**, keep **Controlled experiment**, and choose a sharp image.
2. Select a kernel and sigma, then apply Gaussian blur.
3. Open **Frequency Analysis** to inspect the original/degraded spectra and `H(u,v)`.
4. Run inverse and Wiener restoration.
5. Open **Comparison** to inspect computed metrics.
6. Run either automated experiment and export its graph/data.

All image loading, blur/noise generation, FFT analysis, restoration, metric calculation,
and batch experiments run outside the GUI thread. Cancel requests are checked between
experiment stages; an FFT already executing is allowed to finish safely before cancellation.

In **Real blurred image** mode, the selected file is treated as the degraded observation. Metrics are intentionally unavailable because no true original is known.

## Scientific model

The controlled degraded image is created by circular convolution with a normalized, finite, odd-sized discrete Gaussian point-spread function. The same PSF is zero-padded and circularly shifted before FFT to form its optical transfer function. This periodic boundary model is used consistently. Restoration uses:

- Stabilized inverse: `F_hat = H*G / (|H|² + epsilon)`, only where `|H|` meets the selected threshold.
- Wiener: `F_hat = [H* / (|H|² + K)] G`.

The restored image remains floating point through metric calculation. Values are clipped and converted to 8-bit only for display or image export. Constant `K` is a regularization approximation, not a measured frequency-dependent noise-to-signal spectrum. A separate noise-only Wiener implementation in `image_processing.wiener_filter.noise_only_wiener` uses a white-noise PSD and a periodogram estimate of signal power; it assumes no blur and is not used as the deconvolution method. These methods do not guarantee complete blur removal.

## Build a Windows executable

```powershell
python -m PyInstaller --noconfirm --clean --windowed --name GaussianBlurRestoration --collect-all skimage --collect-all matplotlib main.py
```

The executable is created at `dist\GaussianBlurRestoration\GaussianBlurRestoration.exe`. Build on Windows for a Windows executable. Test exports and image codecs on the target system before distribution.

## Project layout

GUI code is in `app/`; algorithms are in `image_processing/`; metric logic is in `evaluation/`; repeatable experiments are in `experiments/`; plotting and file helpers are separate modules.


## Validation updates

- Reference-based MSE, PSNR, and SSIM use the reference image's expected intensity range and evaluate clipped values that can be displayed/exported. The raw floating-point restoration remains unchanged.
- The noise-only Wiener function documents that its noise variance must use the same squared intensity scale as the image and uses a periodogram normalization whose expected white-noise level equals that variance.
- Algorithm tests include OTF DC normalization, finite blur output, metric clipping consistency, and the zero-noise identity case.
=======
# gaussian
>>>>>>> b4eb811a2fbc57d10a6b9aefc4eb9a5cbedd9c7c
