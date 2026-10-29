"""Dòng lệnh: giayphang anh.jpg [anh2.jpg ...] -m trangden --pdf ketqua.pdf --so-sanh"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from .compare import side_by_side
from .scanner import MODES, scan


def _read(path: Path) -> np.ndarray:
    data = np.fromfile(str(path), dtype=np.uint8)  # đọc được cả đường dẫn có dấu
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise SystemExit(f"Không đọc được ảnh: {path}")
    return img


def _write(path: Path, img: np.ndarray) -> None:
    ok, buf = cv2.imencode(path.suffix or ".jpg", img)
    if not ok:
        raise SystemExit(f"Không ghi được: {path}")
    buf.tofile(str(path))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="giayphang", description="Biến ảnh chụp giấy tờ thành bản scan phẳng, sạch – chạy offline.")
    p.add_argument("anh", nargs="+", type=Path, help="Ảnh đầu vào (jpg/png)")
    p.add_argument("-m", "--mode", choices=MODES, default="mau", help="mau | xam | trangden (mặc định: mau)")
    p.add_argument("-o", "--out", type=Path, default=Path("ket_qua"), help="Thư mục lưu kết quả")
    p.add_argument("--pdf", type=Path, help="Gộp tất cả trang vào 1 file PDF")
    p.add_argument("--so-sanh", action="store_true", help="Xuất thêm ảnh so sánh trước/sau")
    a = p.parse_args(argv)

    a.out.mkdir(parents=True, exist_ok=True)
    pages = []
    for path in a.anh:
        t = time.time()
        img = _read(path)
        out, corners = scan(img, a.mode)
        dst = a.out / f"{path.stem}_{a.mode}.png"
        _write(dst, out)
        pages.append(Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB)))
        msg = "tìm thấy trang giấy" if corners is not None else "KHÔNG thấy viền giấy, chỉ làm sạch"
        print(f"✔ {path.name}: {msg} → {dst} ({time.time() - t:.2f}s)")
        if a.so_sanh:
            cmp_path = a.out / f"{path.stem}_truoc_sau_{a.mode}.jpg"
            _write(cmp_path, side_by_side(img, out, corners))
            print(f"  ảnh so sánh → {cmp_path}")
    if a.pdf:
        pages[0].save(a.pdf, save_all=True, append_images=pages[1:], resolution=150)
        print(f"✔ Đã gộp {len(pages)} trang → {a.pdf}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
