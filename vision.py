#!/usr/bin/env python3
"""
COMPUTER VISION: từ ảnh camera ra vị trí vật trên tờ A4 (cm).

  1. Sheet: dò 4 mã ArUco ở 4 góc tờ A4 -> homography đổi pixel <-> cm, cho cả 2 camera.
     Thấy ít nhất 3 mã thì tính lại lưới; cánh tay che bớt mã thì giữ lưới cũ.
  2. find_objects: trên ảnh cam TREN, tách vật có màu nằm trên giấy trắng -> (x, y) cm, có bù thị sai theo độ cao vật.
  3. Vision.process_frame: ghép hai bước trên rồi vẽ lưới 5 cm và vật tìm thấy lên ảnh.

Hệ tọa độ tờ giấy: gốc ở góc ngoài mã ID 0 (góc dưới bên phải, sát cánh tay), X chạy ID 0 -> ID 1 (29,7 cm), Y chạy ID 0 -> ID 3 (21 cm).

NÓI KHI BỊ HỎI FILE NÀY: "vision.py biến ảnh camera thành toạ độ vật theo cm. Bước 1 dùng 4 mã ArUco ở 4 góc tờ A4
để tính homography, tức là cách đổi pixel sang cm. Bước 2 tìm vùng có màu trên giấy trắng, lấy tâm làm toạ độ vật,
rồi bù thị sai vì camera nhìn nắp vật chứ không nhìn đáy vật."
"""

import cv2
import numpy as np

SHEET_W_CM, SHEET_H_CM = 29.7, 21.0           # Tờ A4 đặt ngang
MARKER_SIZE_CM, MARKER_MARGIN_CM = 2.8, 0.25  # Mỗi mã 2,8 cm, cách mép giấy 0,25 cm
ARUCO_DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)  # Bộ mã có sẵn của OpenCV: mỗi mã 4x4 ô, 50 mã; nhóm dùng ID 0-3
DETECTOR = cv2.aruco.ArucoDetector(ARUCO_DICT)                          # Bộ dò mã ArUco có sẵn của OpenCV

PPC = 8                  # Ảnh phẳng của tờ giấy để tìm vật: 8 pixel / cm
CAM_HEIGHT_CM = 46.0     # Cam TREN treo cao 46 cm so với mặt bàn (0 = không bù thị sai)
OBJECT_HEIGHT_CM = 4.0   # Vật cao 4 cm: nhìn từ trên, nắp vật lệch ra xa tâm ảnh so với đáy vật


def marker_corners_cm(i):
    """
    TÁC DỤNG: toạ độ THẬT (cm) của 4 góc mã ArUco số i trên tờ giấy, đo bằng thước, không phụ thuộc camera.
    VÀO: i = 0, 1, 2, 3.   RA: 4 điểm (x, y) cm theo thứ tự OpenCV: trên-trái, trên-phải, dưới-phải, dưới-trái.
    NÓI: "Mã 0 và 3 nằm bên trái, mã 0 và 1 nằm phía trên; mã cách mép 0,25 cm, cạnh 2,8 cm.
    Đây là phía 'cm' của các cặp điểm dùng để tính homography."
    """
    s, m = MARKER_SIZE_CM, MARKER_MARGIN_CM
    x = m if i in (0, 3) else SHEET_W_CM - m - s  # Mã 0, 3 sát mép trái; mã 1, 2 sát mép phải
    y = m if i in (0, 1) else SHEET_H_CM - m - s  # Mã 0, 1 sát mép trên; mã 2, 3 sát mép dưới
    return np.float32([[x, y], [x + s, y], [x + s, y + s], [x, y + s]])


def px_to_cm(H_px2cm, x, y):
    """TÁC DỤNG: đổi 1 điểm pixel trên ảnh -> cm trên tờ giấy, bằng ma trận homography."""
    return tuple(float(v) for v in cv2.perspectiveTransform(np.float32([[[x, y]]]), H_px2cm)[0, 0])


def cm_to_px(H_cm2px, x, y):
    """TÁC DỤNG: chiều ngược lại, cm trên tờ giấy -> pixel trên ảnh (dùng để VẼ lưới, vòng tròn lên ảnh)."""
    return tuple(float(v) for v in cv2.perspectiveTransform(np.float32([[[x, y]]]), H_cm2px)[0, 0])


# ==============================================================================
# 1. Tờ A4 trong ảnh của một camera
# ==============================================================================
class Sheet:
    """
    TÁC DỤNG: giữ "lưới toạ độ" của tờ A4 trong ảnh của MỘT camera (mỗi camera một Sheet).
    Lưới toạ độ = 2 ma trận homography 3x3: H_px2cm (pixel -> cm) và H_cm2px (cm -> pixel).
    NÓI: "Thấy ít nhất 3 mã thì tính lại lưới; cánh tay che bớt mã thì giữ lưới cũ."
    """

    def __init__(self):
        self.n_seen = 0    # Số mã thấy trong khung vừa xử lý
        self.H_px2cm = self.H_cm2px = None  # None = chưa có lưới (chưa từng thấy đủ 3 mã)

    def update(self, frame):
        """
        TÁC DỤNG: dò mã ArUco trong ảnh, đủ 3 mã thì tính lại homography.
        VÀO: ảnh camera.   RA: góc các mã tìm được (để process_frame vẽ khung quanh mã).
        NÓI: "Mỗi mã cho 4 góc. Bên pixel là góc OpenCV dò được trên ảnh, bên cm là góc thật do marker_corners_cm cho.
        cv2.findHomography tìm ma trận 3x3 khớp các cặp điểm đó. 3 mã là 12 cặp điểm, homography cần ít nhất 4 cặp."
        """
        corners, ids, _ = DETECTOR.detectMarkers(frame)  # corners: 4 góc pixel của mỗi mã; ids: số của mã
        ids = [] if ids is None else ids.ravel()
        seen = {int(i): c.reshape(4, 2) for c, i in zip(corners, ids) if i in (0, 1, 2, 3)}  # Chỉ lấy 4 mã của tờ giấy
        self.n_seen = len(seen)
        if len(seen) >= 3:  # Cần 3 mã: chỉ 2 mã (nhất là 2 mã cùng một mép) thì lưới tính ra bị méo
            px = np.concatenate(list(seen.values()))                     # Các góc mã trên ẢNH (pixel)
            cm = np.concatenate([marker_corners_cm(i) for i in seen])   # Cùng các góc đó trên GIẤY (cm)
            self.H_px2cm = cv2.findHomography(px, cm)[0]               # Ma trận đổi pixel -> cm
            self.H_cm2px = np.linalg.inv(self.H_px2cm)                 # Nghịch đảo: cm -> pixel
        return corners


# ==============================================================================
# 2. Tìm vật có màu trên giấy trắng (ảnh cam TREN)
# ==============================================================================
def find_objects(frame, sheet):
    """
    TÁC DỤNG: tìm các vật có màu trên tờ giấy trắng, trả về toạ độ cm của từng vật.
    VÀO: ảnh cam TRÊN + Sheet (đã có homography).
    RA: danh sách [{"name", "x_cm", "y_cm", "px"}]; px là tâm vật trên ảnh, chỉ để vẽ.
    NÓI: "4 bước. Một, nắn ảnh tờ giấy cho phẳng như nhìn thẳng từ trên, 1 cm = 8 pixel.
    Hai, đổi sang HSV và giữ vùng có độ bão hoà màu cao, vì giấy trắng gần như không có màu.
    Ba, bỏ khối quá nhỏ, quá to, sát mép giấy hoặc dính vào tay robot màu đen.
    Bốn, lấy tâm khối màu làm toạ độ rồi bù thị sai."
    """
    # --- Bước 1: nắn phẳng tờ giấy ---
    W, H = round(SHEET_W_CM * PPC), round(SHEET_H_CM * PPC)  # Ảnh phẳng 238 x 168 pixel
    flat = cv2.warpPerspective(frame, np.diag([PPC, PPC, 1.0]) @ sheet.H_px2cm, (W, H))  # Ảnh phẳng tờ giấy: 1 cm = PPC pixel
    # --- Bước 2: tách vùng có màu ---
    hsv = cv2.cvtColor(flat, cv2.COLOR_BGR2HSV)  # HSV: H = màu gì, S = màu đậm hay nhạt, V = sáng hay tối
    colored = cv2.inRange(hsv, (0, 90, 60), (180, 255, 255))                     # Có màu: độ bão hòa >= 90, đủ sáng
    colored = cv2.morphologyEx(colored, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))  # Bỏ nhiễu và dây điện mảnh
    dark = cv2.dilate(cv2.inRange(hsv, (0, 0, 0), (180, 255, 69)), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))  # Vùng đen = cánh tay robot

    # Chuẩn bị bù thị sai: camera nhìn NẮP vật (cao 4 cm) nên nắp lệch ra xa tâm ảnh hơn đáy vật
    h, w = frame.shape[:2]
    nadir = px_to_cm(sheet.H_px2cm, w / 2, h / 2)  # Điểm cam TREN nhìn thẳng xuống = tâm ảnh
    k = (CAM_HEIGHT_CM - OBJECT_HEIGHT_CM) / CAM_HEIGHT_CM if CAM_HEIGHT_CM > 0 else 1.0  # (46 - 4) / 46 ≈ 0,91
    objects = []
    # --- Bước 3: xét từng khối màu (contour = đường viền của một khối) ---
    for c in cv2.findContours(colored, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
        x, y, bw, bh = cv2.boundingRect(c)  # Hình chữ nhật bao quanh khối
        if not 1.5 <= cv2.contourArea(c) / PPC**2 <= 50:
            continue  # Nhỏ hơn 1,5 cm² là nhiễu; to hơn 50 cm² là bàn tay, không lọt miệng kẹp
        if x < PPC or y < PPC or x + bw > W - PPC or y + bh > H - PPC:
            continue  # Sát mép giấy (dưới 1 cm): tay hoặc đồ vật thò từ ngoài vào
        blob = np.zeros_like(colored)
        cv2.drawContours(blob, [c], -1, 255, -1)  # Tô kín khối này để đếm điểm ảnh
        if cv2.countNonZero(blob & dark) > 0.3 * cv2.countNonZero(blob):
            continue  # Dính vào cánh tay đen: dây, nhãn servo
        # --- Bước 4: tâm khối màu -> toạ độ cm, rồi bù thị sai ---
        m = cv2.moments(c)  # Mô-men ảnh: m10 / m00 và m01 / m00 là toạ độ tâm khối
        top = (m["m10"] / m["m00"] / PPC, m["m01"] / m["m00"] / PPC)  # Tâm khối màu (cm) = nắp vật nhìn từ trên
        # Bù thị sai: vị trí thật = nadir + (vị trí đo - nadir) * (H - h) / H
        x_cm, y_cm = (nadir[j] + (top[j] - nadir[j]) * k for j in (0, 1))
        objects.append({"name": "Vat mau", "x_cm": x_cm, "y_cm": y_cm, "px": cm_to_px(sheet.H_cm2px, *top)})
    return objects


# ==============================================================================
# 3. Vẽ lên ảnh camera (chỉ để người xem, không ảnh hưởng tính toán)
# ==============================================================================
def text(img, s, p, color):
    """TÁC DỤNG: viết chữ có viền đen cho dễ đọc trên mọi nền; chữ to theo độ rộng ảnh. Chữ không dấu vì font OpenCV không có dấu."""
    k = max(1.0, img.shape[1] / 1280)
    for col, thick in (((0, 0, 0), 6), (color, 2)):  # Vẽ 2 lần: viền đen dày trước, chữ màu mảnh sau
        cv2.putText(img, s, (int(p[0]), int(p[1])), cv2.FONT_HERSHEY_SIMPLEX, 1.0 * k, col, int(thick * k), cv2.LINE_AA)


def point(H_cm2px, x, y):
    """TÁC DỤNG: như cm_to_px nhưng làm tròn ra số nguyên, vì hàm vẽ của OpenCV cần pixel nguyên."""
    return tuple(int(v) for v in cm_to_px(H_cm2px, x, y))


def draw_grid(img, H_cm2px, k):
    """
    TÁC DỤNG: vẽ viền tờ giấy, lưới 5 cm, gốc (0, 0) và trục X, Y lên ảnh camera.
    NÓI: "Lưới này để người nhìn kiểm tra bằng mắt: lưới bám đúng mép tờ giấy là homography đúng."
    """
    for x in (0, 5, 10, 15, 20, 25, SHEET_W_CM):  # Đường dọc mỗi 5 cm
        cv2.line(img, point(H_cm2px, x, 0), point(H_cm2px, x, SHEET_H_CM), (200, 200, 200), int(2 * k))
    for y in (0, 5, 10, 15, SHEET_H_CM):          # Đường ngang mỗi 5 cm
        cv2.line(img, point(H_cm2px, 0, y), point(H_cm2px, SHEET_W_CM, y), (200, 200, 200), int(2 * k))
    # Gốc toạ độ CỐ ĐỊNH: góc ngoài mã ID 0 = góc dưới cùng bên phải, sát cánh tay (vị trí đế trong control.py tính theo gốc này).
    # Tờ giấy bị xoay thì nhãn "0,0" rời khỏi chỗ sát cánh tay: đặt lại tờ giấy, đừng đo lại vị trí đế.
    o = point(H_cm2px, 0, 0)
    for end, name in (((6, 0), "X"), ((0, 6), "Y")):  # Mũi tên dài 6 cm cho trục X và trục Y
        tip = point(H_cm2px, *end)
        cv2.arrowedLine(img, o, tip, (255, 0, 255), int(4 * k), cv2.LINE_AA, tipLength=0.2)
        text(img, name, (tip[0] + 8 * k, tip[1] - 8 * k), (255, 0, 255))
    cv2.circle(img, o, int(9 * k), (255, 0, 255), -1)
    text(img, "0,0", (o[0] + 12 * k, o[1] + 30 * k), (255, 0, 255))


def draw_target(img, H_cm2px, target_cm):
    """TÁC DỤNG: vẽ vòng cam chữ "DICH" quanh vật đã chốt bằng phím R (vị trí lúc bấm R, không chạy theo camera)."""
    k = max(1.0, img.shape[1] / 1280)
    p = point(H_cm2px, *target_cm)
    cv2.circle(img, p, int(26 * k), (0, 165, 255), int(3 * k))
    text(img, "DICH", (p[0] + 30 * k, p[1]), (0, 165, 255))


class Vision:
    """
    TÁC DỤNG: phần "nhìn" của cả chương trình. Giữ 2 Sheet (cam TRÊN, cam NGANG) và danh sách vật cam TRÊN thấy.
    NÓI: "main.py gọi process_frame cho từng camera; kết quả vision.objects được đưa sang control.py."
    """

    def __init__(self):
        self.sheets = {"topdown": Sheet(), "side": Sheet()}  # Mỗi camera một lưới toạ độ riêng
        self.objects = []  # Vật cam TRÊN thấy ở khung mới nhất

    def process_frame(self, frame, mode="topdown"):
        """
        TÁC DỤNG: xử lý 1 ảnh: dò tờ giấy -> (cam TRÊN thì) tìm vật -> vẽ mã, lưới, vật lên một bản sao của ảnh.
        VÀO: ảnh camera; mode = "topdown" (cam TRÊN) hoặc "side" (cam NGANG).   RA: ảnh đã vẽ để hiện lên màn hình.
        NÓI: "Cả hai camera đều dò tờ giấy và vẽ lưới, nhưng chỉ cam TRÊN mới tìm vật, vì nhìn từ trên mới đo được X, Y."
        """
        if frame is None:
            return None
        sheet = self.sheets[mode]
        corners = sheet.update(frame)  # Bước 1: dò mã ArUco, cập nhật homography
        img = frame.copy()             # Vẽ lên bản sao, ảnh gốc giữ nguyên để tìm vật
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
            self.objects = find_objects(frame, sheet)  # Bước 2: tìm vật, chỉ trên ảnh cam TRÊN
            for o in self.objects:  # Vòng xanh + toạ độ quanh mỗi vật
                cv2.circle(img, (int(o["px"][0]), int(o["px"][1])), int(30 * k), (0, 255, 128), int(3 * k))
                text(img, f"X={o['x_cm']:.1f} Y={o['y_cm']:.1f} cm", (o["px"][0] + 36 * k, o["px"][1] - 36 * k), (0, 255, 128))
        text(img, f"Luoi A4: thay {sheet.n_seen}/4 ma ArUco", status, (0, 230, 100))
        return img
