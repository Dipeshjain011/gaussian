def comparison_text(inverse: dict | None, wiener: dict | None,
                    inverse_time: float | None = None,
                    wiener_time: float | None = None,
                    ground_truth_available: bool = True) -> str:
    """Describe image quality and processing speed as separate comparisons."""
    if not ground_truth_available:
        quality = ("Ground truth is unavailable, so MSE, PSNR, and SSIM are N/A. "
                   "Image quality cannot be compared reliably.")
    elif not inverse or not wiener:
        quality = "Run both restoration methods to generate an image-quality comparison."
    else:
        outcomes = []
        for metric, higher_is_better, decimals in (("MSE", False, 6), ("PSNR", True, 2), ("SSIM", True, 4)):
            left, right = inverse[metric], wiener[metric]
            left_text = "∞" if left == float("inf") else f"{left:.{decimals}f}"
            right_text = "∞" if right == float("inf") else f"{right:.{decimals}f}"
            if left == right:
                outcomes.append(f"{metric}: both filters scored {left_text}")
            elif (left > right) == higher_is_better:
                outcomes.append(f"{metric}: Inverse is better ({left_text} vs {right_text})")
            else:
                outcomes.append(f"{metric}: Wiener is better ({right_text} vs {left_text})")
        quality = "; ".join(outcomes) + ". Lower MSE and higher PSNR/SSIM indicate better quality."
    if inverse_time is None or wiener_time is None:
        speed = "Run both restoration methods to compare processing speed."
    elif inverse_time == wiener_time:
        speed = f"Both filters completed in approximately {inverse_time:.4f} seconds."
    elif inverse_time < wiener_time:
        speed = f"Inverse filtering was faster ({inverse_time:.4f} s vs {wiener_time:.4f} s)."
    else:
        speed = f"Wiener filtering was faster ({wiener_time:.4f} s vs {inverse_time:.4f} s)."
    return f"IMAGE QUALITY\n{quality}\n\nPROCESSING SPEED\n{speed}"

