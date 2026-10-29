"""Tạo ảnh mẫu 'chụp nghiêng trên bàn gỗ, có bóng đổ' để thử giayphang."""
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FONTS = ROOT.parent / "giayphang" / "fonts"


def trang_giay(w=1240, h=1754):
    im = Image.new("RGB", (w, h), (250, 248, 242))
    d = ImageDraw.Draw(im)
    fb = ImageFont.truetype(str(FONTS / "BeVietnamPro-Bold.ttf"), 64)
    fr = ImageFont.truetype(str(FONTS / "BeVietnamPro-Regular.ttf"), 34)
    d.text((w // 2, 140), "HOÁ ĐƠN BÁN HÀNG", font=fb, fill=(20, 20, 20), anchor="mm")
    d.text((w // 2, 220), "Cửa hàng Điện tử Phương Nam – Số 0001234", font=fr, fill=(60, 60, 60), anchor="mm")
    y = 320
    d.line((100, y, w - 100, y), fill=(0, 0, 0), width=3)
    rows = [("Tai nghe không dây", "1", "1.250.000đ"), ("Sạc nhanh 65W", "2", "780.000đ"),
            ("Cáp USB-C dài 2m", "3", "270.000đ"), ("Ốp lưng điện thoại", "1", "150.000đ"),
            ("Bàn phím cơ tiếng Việt", "1", "1.890.000đ")]
    y += 40
    for col, x in (("Sản phẩm", 110), ("SL", 760), ("Thành tiền", 900)):
        d.text((x, y), col, font=fb.font_variant(size=38), fill=(0, 0, 0))
    y += 80
    for name, q, price in rows:
        d.text((110, y), name, font=fr, fill=(30, 30, 30))
        d.text((770, y), q, font=fr, fill=(30, 30, 30))
        d.text((900, y), price, font=fr, fill=(30, 30, 30))
        y += 70
    d.line((100, y, w - 100, y), fill=(0, 0, 0), width=3)
    y += 40
    d.text((110, y), "TỔNG CỘNG:", font=fb.font_variant(size=46), fill=(0, 0, 0))
    d.text((900, y), "4.340.000đ", font=fb.font_variant(size=46), fill=(180, 20, 20))
    y += 120
    for line in ["Cảm ơn quý khách đã mua hàng!", "Đổi trả trong vòng 7 ngày kèm hoá đơn.",
                 "Ghi chú: hàng chính hãng, bảo hành 12 tháng."]:
        d.text((110, y), line, font=fr, fill=(50, 50, 50))
        y += 60
    d.rectangle((820, 1420, 1140, 1640), outline=(30, 60, 200), width=4)
    d.text((980, 1530), "ĐÃ THANH TOÁN", font=fb.font_variant(size=32), fill=(30, 60, 200), anchor="mm")
    return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)


def ban_go(w=2000, h=2400, seed=3):
    rng = np.random.default_rng(seed)
    y = np.arange(h)[:, None]
    x = np.arange(w)[None, :]
    grain = np.sin(x / 9.0 + 6 * np.sin(y / 180.0)) * 18 + rng.normal(0, 6, (h, w))
    base = np.stack([60 + grain * 0.5, 95 + grain * 0.8, 140 + grain], -1)
    return np.clip(base, 0, 255).astype(np.uint8)


def main():
    page = trang_giay()
    bg = ban_go()
    h, w = page.shape[:2]
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([[430, 260], [1620, 420], [1760, 2130], [250, 1980]])
    m = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(page, m, (bg.shape[1], bg.shape[0]))
    mask = cv2.warpPerspective(np.full((h, w), 255, np.uint8), m, (bg.shape[1], bg.shape[0]))
    # bóng đổ của giấy lên bàn
    shadow = cv2.GaussianBlur(np.roll(mask, (25, 25), (0, 1)), (61, 61), 0)
    out = (bg * (1 - 0.5 * shadow[..., None] / 255)).astype(np.uint8)
    m3 = mask[..., None] / 255.0
    out = (out * (1 - m3) + warped * m3).astype(np.float32)
    # ánh sáng không đều + bóng tay/điện thoại
    H, W = out.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W]
    light = 0.55 + 0.45 * np.clip(1 - np.hypot(xx - 1500, yy - 300) / 2600, 0, 1)
    hand = np.exp(-(((xx - 600) / 520.0) ** 2 + ((yy - 1750) / 380.0) ** 2)) * 0.45
    out = out * (light - hand)[..., None]
    out = np.clip(out + np.random.default_rng(1).normal(0, 4, out.shape), 0, 255).astype(np.uint8)
    out = cv2.GaussianBlur(out, (3, 3), 0)
    dst_path = ROOT / "hoa_don_chup_nghieng.jpg"
    cv2.imwrite(str(dst_path), out, [cv2.IMWRITE_JPEG_QUALITY, 88])
    print("Đã tạo", dst_path)


if __name__ == "__main__":
    main()
