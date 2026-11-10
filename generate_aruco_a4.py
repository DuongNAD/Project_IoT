#!/usr/bin/env python3
"""
Tạo tờ A4 đặt ngang (300 DPI) có 4 mã ArUco ID 0-3 ở 4 góc, đúng vị trí và kích thước mà vision.py dùng.
In aruco_A4_clean.pdf ở tỉ lệ 100% (không "co cho vừa trang"): cạnh mỗi mã phải đo được đúng 2,8 cm.
"""

import cv2
import numpy as np
from PIL import Image

from vision import ARUCO_DICT, MARKER_MARGIN_CM, MARKER_SIZE_CM, SHEET_H_CM, SHEET_W_CM

PPC = 300 / 2.54  # 300 DPI = 118,1 pixel / cm


def make_sheet():
    H, W = round(SHEET_H_CM * PPC), round(SHEET_W_CM * PPC)  # 2480 x 3508 pixel
    m, s = round(MARKER_MARGIN_CM * PPC), round(MARKER_SIZE_CM * PPC)
    sheet = np.full((H, W), 255, np.uint8)
    for i, (x, y) in enumerate([(m, m), (W - m - s, m), (W - m - s, H - m - s), (m, H - m - s)]):  # ID 0-3 theo chiều kim đồng hồ
        sheet[y:y + s, x:x + s] = cv2.aruco.generateImageMarker(ARUCO_DICT, i, s)
    return sheet


if __name__ == "__main__":
    sheet = make_sheet()
    cv2.imwrite("aruco_A4_clean.png", sheet)
    Image.fromarray(sheet).save("aruco_A4_clean.pdf", resolution=300)
    print("Đã lưu aruco_A4_clean.png và aruco_A4_clean.pdf")
