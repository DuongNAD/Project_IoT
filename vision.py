#!/usr/bin/env python3
"""
COMPUTER VISION: từ ảnh camera ra vị trí vật trên tờ A4 (cm).

  1. Sheet: dò 4 mã ArUco ở 4 góc tờ A4 -> homography đổi pixel <-> cm, cho cả 2 camera.
     Thấy ít nhất 3 mã thì tính lại lưới; cánh tay che bớt mã thì giữ lưới cũ.
  2. find_objects: trên ảnh cam TREN, tách màu, lấy khối màu lớn nhất (giấy chỉ đặt một vật) -> (x, y) cm, có bù thị sai theo độ cao vật.
  3. Vision.process_frame: ghép hai bước trên rồi vẽ lưới 5 cm và vật tìm thấy lên ảnh.

Hệ tọa độ tờ giấy: gốc ở góc ngoài mã ID 0 (góc dưới bên phải, sát cánh tay), X chạy ID 0 -> ID 1 (29,7 cm), Y chạy ID 0 -> ID 3 (21 cm).
"""

import cv2
import numpy as np

SHEET_W_CM, SHEET_H_CM = 29.7, 21.0           # Tờ A4 đặt ngang
MARKER_SIZE_CM, MARKER_MARGIN_CM = 2.8, 0.25  # Mỗi mã 2,8 cm, cách mép giấy 0,25 cm
ARUCO_DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)  # Bộ mã có sẵn của OpenCV, dùng ID 0-3
DETECTOR = cv2.aruco.ArucoDetector(ARUCO_DICT)

PPC = 8                  # Ảnh phẳng của tờ giấy để tìm vật: 8 pixel / cm
CAM_HEIGHT_CM = 46.0     # Cam TREN treo cao 46 cm so với mặt bàn (0 = không bù thị sai)
OBJECT_HEIGHT_CM = 4.0   # Vật cao 4 cm: nhìn từ trên, nắp vật lệch ra xa tâm ảnh so với đáy vật
MIN_OBJECT_CM2 = 8       # Khối màu nhỏ hơn 8 cm² không phải cốc: ảnh thật đo cốc 14-19 cm², dây servo / nhiễu dưới 5 cm²


def marker_corners_cm(i):
    """Tọa độ thật (cm) 4 góc của mã ID i (0-3) trên tờ giấy, theo thứ tự OpenCV trả về: trên-trái, trên-phải, dưới-phải, dưới-trái."""
    s, m = MARKER_SIZE_CM, MARKER_MARGIN_CM
    x = m if i in (0, 3) else SHEET_W_CM - m - s  # Mã 0, 3 sát mép trái; mã 1, 2 sát mép phải
    y = m if i in (0, 1) else SHEET_H_CM - m - s  # Mã 0, 1 sát mép trên; mã 2, 3 sát mép dưới
    return np.float32([[x, y], [x + s, y], [x + s, y + s], [x, y + s]])


def px_to_cm(H_px2cm, x, y):
    """Đổi một điểm pixel trên ảnh sang cm trên tờ giấy."""
    return tuple(float(v) for v in cv2.perspectiveTransform(np.float32([[[x, y]]]), H_px2cm)[0, 0])


def cm_to_px(H_cm2px, x, y):
    """Đổi một điểm cm trên tờ giấy sang pixel trên ảnh (để vẽ)."""
    return tuple(float(v) for v in cv2.perspectiveTransform(np.float32([[[x, y]]]), H_cm2px)[0, 0])


# ==============================================================================
# 1. Tờ A4 trong ảnh của một camera
# ==============================================================================
class Sheet:
    """Lưới tọa độ của tờ A4 trong ảnh: thấy ít nhất 3 mã thì tính lại, thiếu (cánh tay che) thì giữ lưới cũ."""

    def __init__(self):
        self.n_seen = 0    # Số mã thấy trong khung vừa xử lý
        self.H_px2cm = self.H_cm2px = None  # Homography 3x3; None = chưa có lưới

    def update(self, frame):
        """Dò mã ArUco; đủ 3 mã thì tính homography từ các cặp góc (pixel trên ảnh, cm trên giấy). Trả về góc các mã để vẽ."""
        corners, ids, _ = DETECTOR.detectMarkers(frame)
        ids = [] if ids is None else ids.ravel()
        seen = {int(i): c.reshape(4, 2) for c, i in zip(corners, ids) if i in (0, 1, 2, 3)}
        self.n_seen = len(seen)
        if len(seen) >= 3:  # Cần 3 mã: chỉ 2 mã (nhất là 2 mã cùng một mép) thì lưới tính ra bị méo
            px = np.concatenate(list(seen.values()))                     # Góc các mã trên ảnh (pixel)
            cm = np.concatenate([marker_corners_cm(i) for i in seen])   # Cùng các góc đó trên giấy (cm)
            self.H_px2cm = cv2.findHomography(px, cm)[0]
            self.H_cm2px = np.linalg.inv(self.H_px2cm)
        return corners


# ==============================================================================
# 2. Tìm vật có màu trên giấy trắng (ảnh cam TREN)
# ==============================================================================
def find_objects(frame, sheet):
    """Vật trên giấy [{"name", "x_cm", "y_cm", "px"}] (rỗng khi không thấy cốc); px là tâm vật trên ảnh, để vẽ.
    Giấy chỉ đặt MỘT vật có màu nên vật = khối màu lớn nhất (dây servo màu cam cũng qua ngưỡng màu nhưng chỉ vài cm²)."""
    # Bước 1: nắn phẳng tờ giấy
    W, H = round(SHEET_W_CM * PPC), round(SHEET_H_CM * PPC)
    flat = cv2.warpPerspective(frame, np.diag([PPC, PPC, 1.0]) @ sheet.H_px2cm, (W, H))  # Ảnh phẳng tờ giấy: 1 cm = PPC pixel
    # Bước 2: tách vùng có màu
    colored = cv2.inRange(cv2.cvtColor(flat, cv2.COLOR_BGR2HSV), (0, 90, 60), (180, 255, 255))  # Có màu: độ bão hòa >= 90, đủ sáng
    # Bước 3: lấy khối màu lớn nhất
    c = max(cv2.findContours(colored, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0], key=cv2.contourArea, default=None)
    if c is None or cv2.contourArea(c) / PPC**2 < MIN_OBJECT_CM2:
        return []  # Không có cốc: khối màu lớn nhất chỉ là dây điện, nhiễu

    h, w = frame.shape[:2]
    nadir = px_to_cm(sheet.H_px2cm, w / 2, h / 2)  # Điểm cam TREN nhìn thẳng xuống = tâm ảnh
    k = (CAM_HEIGHT_CM - OBJECT_HEIGHT_CM) / CAM_HEIGHT_CM if CAM_HEIGHT_CM > 0 else 1.0
    # Bước 4: tâm khối màu -> tọa độ cm, có bù thị sai
    m = cv2.moments(c)
    top = (m["m10"] / m["m00"] / PPC, m["m01"] / m["m00"] / PPC)  # Tâm khối màu (cm) = nắp vật nhìn từ trên
    # Bù thị sai: vị trí thật = nadir + (vị trí đo - nadir) * (H - h) / H
    x_cm, y_cm = (nadir[j] + (top[j] - nadir[j]) * k for j in (0, 1))
    return [{"name": "Vat mau", "x_cm": x_cm, "y_cm": y_cm, "px": cm_to_px(sheet.H_cm2px, *top)}]


# ==============================================================================
# 3. Vẽ lên ảnh camera
# ==============================================================================
def text(img, s, p, color):
    """Chữ có viền đen cho dễ đọc trên mọi nền; to theo độ rộng ảnh."""
    k = max(1.0, img.shape[1] / 1280)
    for col, thick in (((0, 0, 0), 6), (color, 2)):
        cv2.putText(img, s, (int(p[0]), int(p[1])), cv2.FONT_HERSHEY_SIMPLEX, 1.0 * k, col, int(thick * k), cv2.LINE_AA)


def point(H_cm2px, x, y):
    """Như cm_to_px nhưng làm tròn ra pixel nguyên cho các hàm vẽ của OpenCV."""
    return tuple(int(v) for v in cm_to_px(H_cm2px, x, y))


def draw_grid(img, H_cm2px, k):
    """Viền tờ giấy, lưới 5 cm, gốc (0, 0) và trục X, Y: nhìn là biết lưới tọa độ có bám đúng tờ giấy và tờ giấy có đặt đúng chiều không."""
    for x in (0, 5, 10, 15, 20, 25, SHEET_W_CM):
        cv2.line(img, point(H_cm2px, x, 0), point(H_cm2px, x, SHEET_H_CM), (200, 200, 200), int(2 * k))
    for y in (0, 5, 10, 15, SHEET_H_CM):
        cv2.line(img, point(H_cm2px, 0, y), point(H_cm2px, SHEET_W_CM, y), (200, 200, 200), int(2 * k))
    # Gốc toạ độ CỐ ĐỊNH: góc ngoài mã ID 0 = góc dưới cùng bên phải, sát cánh tay (vị trí đế trong control.py tính theo gốc này).
    # Tờ giấy bị xoay thì nhãn "0,0" rời khỏi chỗ sát cánh tay: đặt lại tờ giấy, đừng đo lại vị trí đế.
    o = point(H_cm2px, 0, 0)
    for end, name in (((6, 0), "X"), ((0, 6), "Y")):
        tip = point(H_cm2px, *end)
        cv2.arrowedLine(img, o, tip, (255, 0, 255), int(4 * k), cv2.LINE_AA, tipLength=0.2)
        text(img, name, (tip[0] + 8 * k, tip[1] - 8 * k), (255, 0, 255))
    cv2.circle(img, o, int(9 * k), (255, 0, 255), -1)
    text(img, "0,0", (o[0] + 12 * k, o[1] + 30 * k), (255, 0, 255))


def draw_target(img, H_cm2px, target_cm):
    """DICH: vòng cam quanh vật cần tới (vị trí lúc bấm R)."""
    k = max(1.0, img.shape[1] / 1280)
    p = point(H_cm2px, *target_cm)
    cv2.circle(img, p, int(26 * k), (0, 165, 255), int(3 * k))
    text(img, "DICH", (p[0] + 30 * k, p[1]), (0, 165, 255))


class Vision:
    """Hai camera: lưới tọa độ cho cả hai, danh sách vật từ cam TREN (main.py đưa vision.objects cho control.py)."""

    def __init__(self):
        self.sheets = {"topdown": Sheet(), "side": Sheet()}  # Mỗi camera một lưới tọa độ
        self.objects = []

    def process_frame(self, frame, mode="topdown"):
        """Dò tờ giấy, tìm vật (chỉ cam TREN), trả về bản sao ảnh đã vẽ: mã ArUco, lưới 5 cm, vật, dòng trạng thái."""
        if frame is None:
            return None
        sheet = self.sheets[mode]
        corners = sheet.update(frame)
        img = frame.copy()
        cv2.aruco.drawDetectedMarkers(img, corners)
        k = max(1.0, img.shape[1] / 1280)  # Ảnh 1920 px thu về ô 640 px trên màn hình: nét vẽ phải dày theo
        status = (15, img.shape[0] - 20)
        if sheet.H_px2cm is None:
            if mode == "topdown":
                self.objects = []  # Không có lưới tọa độ thì không biết vật ở đâu
            text(img, "KHONG THAY TO A4: kiem tra 4 ma ArUco", status, (60, 60, 255))
            return img
        draw_grid(img, sheet.H_cm2px, k)
        if mode == "topdown":
            self.objects = find_objects(frame, sheet)
            for o in self.objects:
                cv2.circle(img, (int(o["px"][0]), int(o["px"][1])), int(30 * k), (0, 255, 128), int(3 * k))
                text(img, f"X={o['x_cm']:.1f} Y={o['y_cm']:.1f} cm", (o["px"][0] + 36 * k, o["px"][1] - 36 * k), (0, 255, 128))
        text(img, f"Luoi A4: thay {sheet.n_seen}/4 ma ArUco", status, (0, 230, 100))
        return img
