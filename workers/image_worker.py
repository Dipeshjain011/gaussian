from __future__ import annotations

import cv2

from image_processing.preprocessing import read_image


def load_image_task(path: str, resize_limit: int | None = None):
    def task(context):
        context.report(10, "Loading image...")
        image = read_image(path)
        original_shape = image.shape
        if resize_limit and max(image.shape[:2]) > resize_limit:
            scale = resize_limit / max(image.shape[:2])
            size = (max(1, round(image.shape[1] * scale)), max(1, round(image.shape[0] * scale)))
            context.report(55, "Resizing working copy...")
            image = cv2.resize(image, size, interpolation=cv2.INTER_AREA)
        context.report(100, "Image loaded")
        return {"image": image, "original_shape": original_shape}
    return task
