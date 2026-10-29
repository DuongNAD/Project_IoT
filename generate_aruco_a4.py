#!/usr/bin/env python3
"""
Tạo file tờ giấy A4 đặt ngang (297 x 210 mm, chuẩn 300 DPI) chứa 4 mã ArUco (DICT_4X4_50: ID 0, 1, 2, 3)
đặt SÁT 4 GÓC tờ giấy A4 để in ra sử dụng cho hệ thống Camera + YOLO + Robot Arm.

Xuất ra 2 phiên bản (cả PDF chuẩn kích thước thật lẫn PNG nét cao):
1. aruco_A4_grid.pdf / .png  : Có thước đo cm/mm ở viền và lưới tọa độ mờ 1cm/5cm.
2. aruco_A4_clean.pdf / .png : Nền trắng tinh, chỉ có 4 mã ArUco sát 4 góc.
"""

import os
import cv2
import numpy as np
from PIL import Image

# Kích thước chuẩn giấy A4 đặt ngang (Landscape)
A4_W_MM = 297.0
A4_H_MM = 210.0
A4_W_CM = 29.7
A4_H_CM = 21.0

# Độ phân giải in ấn chuẩn 300 DPI
DPI = 300
PX_PER_MM = DPI / 25.4
PX_PER_CM = DPI / 2.54

IMG_W = int(round(A4_W_MM * PX_PER_MM))  # 3508 px
IMG_H = int(round(A4_H_MM * PX_PER_MM))  # 2480 px

# Cấu hình mã ArUco khớp với main.py (DICT_4X4_50, ID 0 -> 3)
ARUCO_DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

# Đặt SÁT 4 GÓC tờ giấy A4:
# - Kích thước mỗi mã ArUco: 2.8 cm (28 mm)
# - Khoảng cách từ mép giấy A4 vào mã: 0.25 cm (2.5 mm - viền trắng tối thiểu để OpenCV nhận diện được cạnh đen ngoài cùng)
MARKER_SIZE_CM = 2.8
MARGIN_CM = 0.25


def cm_to_px(cm):
    return int(round(cm * PX_PER_CM))


def generate_sheet(with_grid=True):
    # Tạo nền trắng chuẩn A4 (BGR)
    canvas = np.full((IMG_H, IMG_W, 3), 255, dtype=np.uint8)

    m_px = cm_to_px(MARGIN_CM)
    s_px = cm_to_px(MARKER_SIZE_CM)
    quiet_px = cm_to_px(0.25)  # Vùng trắng bảo vệ quanh mỗi mã ArUco (2.5mm)

    if with_grid:
        # 1. Vẽ lưới milimet/centimet rất mờ
        # Lưới 1 cm (màu xám rất nhạt #F0F0F0)
        for x_cm in range(1, int(A4_W_CM) + 1):
            x = cm_to_px(x_cm)
            cv2.line(canvas, (x, 0), (x, IMG_H), (240, 240, 240), 1)
        for y_cm in range(1, int(A4_H_CM) + 1):
            y = cm_to_px(y_cm)
            cv2.line(canvas, (0, y), (IMG_W, y), (240, 240, 240), 1)

        # Lưới 5 cm (màu xám nhạt #DCDCDC)
        for x_cm in range(5, int(A4_W_CM), 5):
            x = cm_to_px(x_cm)
            cv2.line(canvas, (x, 0), (x, IMG_H), (215, 215, 215), 2)
        for y_cm in range(5, int(A4_H_CM), 5):
            y = cm_to_px(y_cm)
            cv2.line(canvas, (0, y), (IMG_W, y), (215, 215, 215), 2)

        # Vạch thước chia độ dọc theo cạnh trên (Trục X: từ 3.5cm đến 26.5cm để không đè vào mã ArUco ở góc)
        for x_mm in range(35, int(A4_W_MM) - 34):
            x = int(round(x_mm * PX_PER_MM))
            if x_mm % 50 == 0:
                tick_len = cm_to_px(0.35)
                thickness = 3
                color = (120, 120, 120)
            elif x_mm % 10 == 0:
                tick_len = cm_to_px(0.22)
                thickness = 2
                color = (160, 160, 160)
            elif x_mm % 5 == 0:
                tick_len = cm_to_px(0.14)
                thickness = 1
                color = (190, 190, 190)
            else:
                tick_len = cm_to_px(0.08)
                thickness = 1
                color = (210, 210, 210)
            cv2.line(canvas, (x, 0), (x, tick_len), color, thickness)

        # Vạch thước chia độ dọc theo cạnh trái (Trục Y: từ 3.5cm đến 17.5cm)
        for y_mm in range(35, int(A4_H_MM) - 34):
            y = int(round(y_mm * PX_PER_MM))
            if y_mm % 50 == 0:
                tick_len = cm_to_px(0.35)
                thickness = 3
                color = (120, 120, 120)
            elif y_mm % 10 == 0:
                tick_len = cm_to_px(0.22)
                thickness = 2
                color = (160, 160, 160)
            elif y_mm % 5 == 0:
                tick_len = cm_to_px(0.14)
                thickness = 1
                color = (190, 190, 190)
            else:
                tick_len = cm_to_px(0.08)
                thickness = 1
                color = (210, 210, 210)
            cv2.line(canvas, (0, y), (tick_len, y), color, thickness)

        # Ghi số đo cm dọc theo trục X (cạnh trên) và trục Y (cạnh trái)
        for x_cm in (5, 10, 15, 20, 25):
            x = cm_to_px(x_cm)
            cv2.putText(
                canvas,
                f"{x_cm}cm",
                (x - 35, cm_to_px(0.70)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.68,
                (110, 110, 110),
                2,
                cv2.LINE_AA,
            )
        for y_cm in (5, 10, 15):
            y = cm_to_px(y_cm)
            cv2.putText(
                canvas,
                f"{y_cm}cm",
                (cm_to_px(0.45), y + 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.68,
                (110, 110, 110),
                2,
                cv2.LINE_AA,
            )

        # Dấu cộng (+) nhỏ chính giữa tờ giấy A4 (14.85 cm, 10.50 cm)
        cx, cy = IMG_W // 2, IMG_H // 2
        arm = cm_to_px(0.4)
        cv2.line(canvas, (cx - arm, cy), (cx + arm, cy), (180, 180, 180), 2, cv2.LINE_AA)
        cv2.line(canvas, (cx, cy - arm), (cx, cy + arm), (180, 180, 180), 2, cv2.LINE_AA)
        cv2.circle(canvas, (cx, cy), cm_to_px(0.15), (180, 180, 180), 1, cv2.LINE_AA)
        cv2.putText(
            canvas,
            "TAM A4 (14.85, 10.5 cm)",
            (cx - 135, cy + cm_to_px(0.65)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (170, 170, 170),
            1,
            cv2.LINE_AA,
        )

    # 2. Vị trí 4 mã ArUco đặt SÁT 4 GÓC (cách mép 2.5mm):
    # ID 0: Trên-Trái (TL)
    # ID 1: Trên-Phải (TR)
    # ID 2: Dưới-Phải (BR)
    # ID 3: Dưới-Trái (BL)
    positions = {
        0: (m_px, m_px, "ID:0 (0, 0 cm) - GOC O"),
        1: (IMG_W - m_px - s_px, m_px, "ID:1 (29.7, 0 cm) - TRUC X"),
        2: (IMG_W - m_px - s_px, IMG_H - m_px - s_px, "ID:2 (29.7, 21.0 cm)"),
        3: (m_px, IMG_H - m_px - s_px, "ID:3 (0, 21.0 cm) - TRUC Y"),
    }

    for marker_id, (x, y, label) in positions.items():
        # Đảm bảo vùng Quiet Zone quanh mã ArUco trắng tinh 100%
        qx1 = max(0, x - quiet_px)
        qy1 = max(0, y - quiet_px)
        qx2 = min(IMG_W, x + s_px + quiet_px)
        qy2 = min(IMG_H, y + s_px + quiet_px)
        canvas[qy1:qy2, qx1:qx2] = 255

        # Sinh mã ArUco sắc nét tuyệt đối
        marker_img = cv2.aruco.generateImageMarker(ARUCO_DICT, marker_id, s_px)
        marker_bgr = cv2.cvtColor(marker_img, cv2.COLOR_GRAY2BGR)
        canvas[y:y + s_px, x:x + s_px] = marker_bgr

        # Ghi nhãn nhỏ bên dưới/trên mã ArUco
        if marker_id in (0, 1):
            lbl_y = y + s_px + quiet_px + 20
        else:
            lbl_y = y - quiet_px - 8
        lbl_x = x if marker_id in (0, 3) else x + s_px - 265
        cv2.putText(
            canvas,
            label,
            (max(m_px, lbl_x), lbl_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.54,
            (90, 90, 90),
            2,
            cv2.LINE_AA,
        )

    return canvas


def verify_and_save(canvas, base_name, out_dir):
    detector = cv2.aruco.ArucoDetector(ARUCO_DICT, cv2.aruco.DetectorParameters())
    corners, ids, _ = detector.detectMarkers(canvas)
    detected_ids = sorted(ids.flatten().tolist()) if ids is not None else []
    print(f"🔍 Kiểm tra nhận diện [{base_name}]: Phát hiện {len(detected_ids)} mã -> IDs = {detected_ids}")
    assert detected_ids == [0, 1, 2, 3], f"Lỗi: Không nhận diện đủ 4 mã ArUco! ({detected_ids})"

    png_path = os.path.join(out_dir, f"{base_name}.png")
    pdf_path = os.path.join(out_dir, f"{base_name}.pdf")

    rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)
    pil_img.save(png_path, "PNG", dpi=(DPI, DPI))
    pil_img.save(pdf_path, "PDF", resolution=float(DPI))
    print(f"✅ Đã tạo: {png_path}")
    print(f"✅ Đã tạo: {pdf_path}")
    return png_path, pdf_path


if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    sheet_grid = generate_sheet(with_grid=True)
    verify_and_save(sheet_grid, "aruco_A4_grid", out_dir)

    sheet_clean = generate_sheet(with_grid=False)
    verify_and_save(sheet_clean, "aruco_A4_clean", out_dir)
