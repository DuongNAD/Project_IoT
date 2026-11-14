#!/usr/bin/env python3
"""
MÀN HÌNH (chỉ vẽ, không tính gì): 2 camera ở trên, bên dưới 2 ô chữ và 1 dòng chân trang.

  [ cam NGANG                  | cam TREN                ]
  [ 1. DIEU KHIEN (từ Plan)    | 2. SUCCESS (từ Result)  ]

Ô 1 vẽ từ Plan của control.py: bấm phím gì, mấy lần; 3 dòng servo đế / vai / khuỷu.
Ô 2 vẽ từ Result của success.py: XONG! hoặc CHUA XONG, và số lần thành công.
Chữ không dấu vì font của OpenCV không vẽ được dấu tiếng Việt.
"""

import cv2
import numpy as np

SCREEN_WINDOW = "GAP DON GIAN: bam phim theo lenh (Q = thoat)"
CAM_W, CAM_H = 640, 360  # Mỗi camera một ô 16:9
SCREEN_W, SCREEN_H = 2 * CAM_W, CAM_H + 290
WHITE, GRAY, GREEN, ORANGE = (255, 255, 255), (170, 170, 170), (80, 220, 80), (0, 170, 255)  # Màu BGR

MESSAGES = {  # Trạng thái của success.py -> lời nhắn ở ô 1 (trạng thái "moving" thì hiện lệnh bấm phím)
    "done": "Khong can bam them",
    "no_target": "Chua co dich: dat vat co mau len to A4 roi bam R",
    "unreachable": "Vat ngoai tam voi: dat vat gan de robot hon",
}


def put(img, text, x, y, size=0.7, color=WHITE, thick=2):
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, size, color, thick, cv2.LINE_AA)


def cam_cell(frame, title):
    """Thu ảnh camera vào ô 640 x 360 (giữ tỉ lệ, viền đen) và ghi tên camera trên một dải đen."""
    h, w = frame.shape[:2]
    k = min(CAM_W / w, CAM_H / h)
    small = cv2.resize(frame, (round(w * k), round(h * k)), interpolation=cv2.INTER_AREA)
    cell = np.zeros((CAM_H, CAM_W, 3), np.uint8)
    y, x = (CAM_H - small.shape[0]) // 2, (CAM_W - small.shape[1]) // 2
    cell[y:y + small.shape[0], x:x + small.shape[1]] = small
    cv2.rectangle(cell, (0, 0), (CAM_W, 32), (0, 0, 0), -1)
    put(cell, title, 10, 23, 0.6, GREEN)
    return cell


def build_screen(view_left, view_right, plan, result, titles=("CAM NGANG", "CAM TREN")):
    img = np.full((SCREEN_H, SCREEN_W, 3), 30, np.uint8)
    img[:CAM_H] = np.hstack([cam_cell(view_left, titles[0]), cam_cell(view_right, titles[1])])
    y = CAM_H + 40

    # Ô 1: ĐIỀU KHIỂN
    put(img, "1. DIEU KHIEN (A sang trai, D sang phai)", 20, y, 0.8, ORANGE)
    if result.state == "moving":
        m = result.next_move
        put(img, f"BAM {m.key.upper()} x{m.steps}: {m.words} {m.degrees} do", 20, y + 50, 1.2, ORANGE, 3)
    else:
        put(img, MESSAGES[result.state], 20, y + 50)
    for i, (m, ok) in enumerate(zip(plan.moves, result.joints_ok)):  # Đế, vai, khuỷu
        todo = "DA DUNG" if ok else f"bam {m.key.upper()} x{m.steps}"
        put(img, f"{m.label}: {m.now} -> {m.goal} do   {todo}", 20, y + 100 + 36 * i, 0.7, GREEN if ok else WHITE)

    # Ô 2: SUCCESS
    x = 840
    put(img, "2. SUCCESS", x, y, 0.8, GREEN if result.done else ORANGE)
    if result.done:
        put(img, "XONG!", x, y + 70, 2.0, GREEN, 5)
    else:
        put(img, "CHUA XONG", x, y + 60, 1.2, ORANGE, 3)
        if result.state == "moving":
            put(img, f"con {result.remaining} lan bam", x, y + 100)
    put(img, f"Thanh cong: {result.count} lan", x, y + 150)

    # Chân trang: USB, phím tắt
    usb = "USB Arduino: DA KET NOI" if plan.usb_ok else "USB Arduino: MO PHONG (chua ket noi)"
    put(img, f"{usb}    [R] chup dich  [H] ve Home  [U] do lai ma  [Q] thoat", 20, SCREEN_H - 40, 0.55, GRAY, 1)
    return img
