"""Ghép ảnh trước/sau có nhãn tiếng Việt để quay Reel."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/sand-box/google/Be Vietnam Pro/BeVietnamPro-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]


def _font(size: int):
    here = Path(__file__).parent / "fonts" / "BeVietnamPro-Bold.ttf"
    for p in [str(here), *FONT_CANDIDATES]:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def side_by_side(before: np.ndarray, after: np.ndarray, corners=None, height: int = 1100) -> np.ndarray:
    b = before.copy()
    if corners is not None:
        cv2.polylines(b, [corners.astype(np.int32)], True, (60, 220, 60), max(4, b.shape[1] // 200))

    def fit(im):
        s = height / im.shape[0]
        return cv2.resize(im, (int(im.shape[1] * s), height), interpolation=cv2.INTER_AREA)

    b, a = fit(b), fit(after)
    pad, top = 30, 110
    w = b.shape[1] + a.shape[1] + pad * 3
    canvas = np.full((height + top + pad, w, 3), 24, np.uint8)
    canvas[top:top + height, pad:pad + b.shape[1]] = b
    x2 = pad * 2 + b.shape[1]
    canvas[top:top + height, x2:x2 + a.shape[1]] = a

    pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(pil)
    f = _font(52)
    d.text((pad + b.shape[1] // 2, top // 2), "TRƯỚC: ảnh chụp nghiêng", font=f, fill=(255, 120, 120), anchor="mm")
    d.text((x2 + a.shape[1] // 2, top // 2), "SAU: bản scan phẳng", font=f, fill=(120, 255, 150), anchor="mm")
    return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
