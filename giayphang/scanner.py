"""Lõi xử lý: tìm trang giấy, nắn phẳng phối cảnh, làm sạch bóng đổ."""
from __future__ import annotations

import cv2
import numpy as np

MODES = ("mau", "xam", "trangden")


def _order(pts: np.ndarray) -> np.ndarray:
    """Sắp 4 góc theo thứ tự: trên-trái, trên-phải, dưới-phải, dưới-trái."""
    pts = pts.reshape(4, 2).astype("float32")
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).ravel()
    return np.array([pts[s.argmin()], pts[d.argmin()], pts[s.argmax()], pts[d.argmax()]], dtype="float32")


def find_page(img: np.ndarray) -> np.ndarray | None:
    """Trả về 4 góc của tờ giấy (toạ độ ảnh gốc) hoặc None nếu không tìm thấy."""
    h, w = img.shape[:2]
    scale = 800.0 / max(h, w)
    small = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    area_total = small.shape[0] * small.shape[1]

    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    # Đóng hình thái để xoá chữ bên trong trang, chỉ giữ khối giấy
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    closed = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel, iterations=2)

    candidates = []
    edges = cv2.dilate(cv2.Canny(closed, 30, 120), np.ones((3, 3), np.uint8))
    candidates.append(edges)
    _, otsu = cv2.threshold(closed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    candidates.append(otsu)

    best, best_area = None, 0.0
    for binimg in candidates:
        cnts, _ = cv2.findContours(binimg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in sorted(cnts, key=cv2.contourArea, reverse=True)[:5]:
            peri = cv2.arcLength(c, True)
            for eps in (0.02, 0.03, 0.05):
                approx = cv2.approxPolyDP(c, eps * peri, True)
                if len(approx) == 4 and cv2.isContourConvex(approx):
                    a = cv2.contourArea(approx)
                    if a > 0.15 * area_total and a > best_area:
                        best, best_area = approx, a
                    break
    if best is None:
        return None
    return _order(best / scale)


def warp_page(img: np.ndarray, corners: np.ndarray) -> np.ndarray:
    """Nắn phẳng phối cảnh theo 4 góc."""
    tl, tr, br, bl = corners
    width = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    height = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
    dst = np.array([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]], dtype="float32")
    m = cv2.getPerspectiveTransform(corners.astype("float32"), dst)
    return cv2.warpPerspective(img, m, (width, height), flags=cv2.INTER_CUBIC)


def _flatten_light(channel: np.ndarray) -> np.ndarray:
    """Chia cho nền ước lượng để xoá bóng đổ / ánh sáng không đều."""
    k = max(31, (min(channel.shape[:2]) // 12) | 1)
    bg = cv2.morphologyEx(channel, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    bg = cv2.medianBlur(bg, 21)
    out = cv2.divide(channel, bg, scale=255)
    return out


def enhance(page: np.ndarray, mode: str = "mau") -> np.ndarray:
    """Làm sạch trang: 'mau' (giữ màu), 'xam' (thang xám), 'trangden' (đen trắng sắc nét)."""
    if mode not in MODES:
        raise ValueError(f"mode phải là một trong {MODES}")
    if mode == "mau":
        chans = [_flatten_light(c) for c in cv2.split(page)]
        out = cv2.merge(chans)
        # tăng tương phản nhẹ
        return cv2.convertScaleAbs(out, alpha=1.15, beta=-25)
    gray = cv2.cvtColor(page, cv2.COLOR_BGR2GRAY)
    flat = _flatten_light(gray)
    if mode == "xam":
        out = cv2.normalize(flat, None, 0, 255, cv2.NORM_MINMAX)
    else:
        out = cv2.adaptiveThreshold(flat, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 25, 12)
        out = cv2.medianBlur(out, 3)
    return cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)


def scan(img: np.ndarray, mode: str = "mau") -> tuple[np.ndarray, np.ndarray | None]:
    """Toàn bộ quy trình. Trả về (ảnh scan, 4 góc tìm được hoặc None)."""
    corners = find_page(img)
    page = warp_page(img, corners) if corners is not None else img.copy()
    return enhance(page, mode), corners
