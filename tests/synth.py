"""
Cảnh tổng hợp cho test: tờ A4 có 4 mã ArUco được chiếu vào khung hình bởi một camera giả lập biết trước thông số
(tiêu cự, vị trí, hướng nhìn) nên có đáp án chính xác để so sánh với kết quả của vision.py.
Không cần camera, không cần ảnh thật (ảnh thật chứa màn hình / đồ cá nhân nên không đưa vào repo).
"""

import cv2
import numpy as np

import vision as V

PPC = 40  # pixel / cm của ảnh phẳng tờ giấy (texture)
SHEET_W_PX = int(round(V.SHEET_W_CM * PPC))
SHEET_H_PX = int(round(V.SHEET_H_CM * PPC))
FRAME_W, FRAME_H = 1920, 1080
BACKGROUND = (70, 80, 90)


def look_at(position_mm, target_mm):
    """(R, t) world -> camera theo quy ước OpenCV (x phải, y xuống, z phía trước); 'xuống' của camera là hướng xuống mặt bàn."""
    pos = np.asarray(position_mm, float)
    z = np.asarray(target_mm, float) - pos
    z /= np.linalg.norm(z)
    down = np.array([0.0, 0.0, 1.0])  # Trục Z của hệ tờ giấy hướng XUỐNG mặt bàn
    y = down - np.dot(down, z) * z
    y /= np.linalg.norm(y)
    x = np.cross(y, z)
    R = np.vstack([x, y, z])
    return R, -R @ pos


class SyntheticCamera:
    """Camera lỗ kim (không méo) với điểm chính ở giữa ảnh."""

    def __init__(self, f, R, t, size=(FRAME_W, FRAME_H)):
        self.f = float(f)
        self.size = size
        self.R = R
        self.t = t
        self.K = np.array([[f, 0, size[0] / 2.0], [0, f, size[1] / 2.0], [0, 0, 1]], float)
        self.rvec, _ = cv2.Rodrigues(R)

    def project(self, x_cm, y_cm, z_mm=0.0):
        """Điểm trên tờ giấy (cm), cao z_mm phía trên mặt giấy -> pixel (u, v)."""
        obj = np.float64([[x_cm * 10.0, y_cm * 10.0, -float(z_mm)]])
        pt, _ = cv2.projectPoints(obj, self.rvec, self.t, self.K, None)
        return float(pt[0, 0, 0]), float(pt[0, 0, 1])


def top_camera():
    """Camera treo thẳng phía trên giữa tờ giấy; trục X của tờ giấy chạy từ dưới lên trên ảnh, Y chạy sang phải (như OBSBOT thật)."""
    R = np.array([[0.0, 1.0, 0.0], [-1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
    pos = np.array([148.5, 105.0, -450.0])
    return SyntheticCamera(1000.0, R, -R @ pos)


def side_camera(f=1400.0):
    """Camera nhìn xiên từ ngoài mép Y = 21 cm, cao 25 cm, ngẩng xuống ~34 độ (giống camera MacBook đặt trên bàn)."""
    R, t = look_at([148.5, 480.0, -250.0], [148.5, 105.0, 0.0])
    return SyntheticCamera(f, R, t)


def sheet_texture(extra=None):
    """Ảnh phẳng tờ A4 màu trắng với 4 mã ArUco đúng vị trí / kích thước như generate_aruco_a4.py; extra(img) vẽ thêm vật lên giấy."""
    img = np.full((SHEET_H_PX, SHEET_W_PX, 3), 245, np.uint8)
    size = int(round(V.MARKER_SIZE_CM * PPC))
    for marker_id in range(4):
        x0, y0 = (V.marker_corners_cm(marker_id)[0] * PPC).round().astype(int)
        tile = cv2.aruco.generateImageMarker(V.ARUCO_DICT, marker_id, size)
        img[y0:y0 + size, x0:x0 + size] = cv2.cvtColor(tile, cv2.COLOR_GRAY2BGR)
    if extra is not None:
        extra(img)
    return img


def render(camera, texture):
    """Chiếu ảnh phẳng tờ giấy vào khung hình của camera (mặt phẳng chiếu lên ảnh đúng là một Homography)."""
    corners_cm = [(0, 0), (V.SHEET_W_CM, 0), (V.SHEET_W_CM, V.SHEET_H_CM), (0, V.SHEET_H_CM)]
    src = np.float32([[0, 0], [SHEET_W_PX, 0], [SHEET_W_PX, SHEET_H_PX], [0, SHEET_H_PX]])
    dst = np.float32([camera.project(x, y) for x, y in corners_cm])
    M = cv2.getPerspectiveTransform(src, dst)
    w, h = camera.size
    frame = np.full((h, w, 3), BACKGROUND, np.uint8)
    warped = cv2.warpPerspective(texture, M, (w, h), flags=cv2.INTER_LINEAR)
    mask = cv2.warpPerspective(np.full(texture.shape[:2], 255, np.uint8), M, (w, h)) > 0
    frame[mask] = warped[mask]
    return frame


def cm_to_texture_px(x_cm, y_cm):
    return int(round(x_cm * PPC)), int(round(y_cm * PPC))


def draw_disc(img, x_cm, y_cm, radius_cm, color=(40, 90, 235)):
    """Đĩa màu cam (BGR) nằm trên giấy, ví dụ nắp cốc nhìn từ trên xuống."""
    cv2.circle(img, cm_to_texture_px(x_cm, y_cm), int(radius_cm * PPC), color, -1, cv2.LINE_AA)


def occlude_markers(frame, camera, marker_ids):
    """Che các mã ArUco bằng màu nền (cánh tay robot che khuất mã)."""
    out = frame.copy()
    for marker_id in marker_ids:
        poly = np.int32([camera.project(x, y) for x, y in V.marker_corners_cm(marker_id)])
        cv2.fillConvexPoly(out, cv2.convexHull(poly), BACKGROUND)
    return out


def corner_error_px(view, camera):
    """Sai số trung bình (pixel) khi chiếu 4 góc tờ giấy bằng Homography dò được so với camera thật."""
    errors = []
    for x, y in ((0, 0), (V.SHEET_W_CM, 0), (V.SHEET_W_CM, V.SHEET_H_CM), (0, V.SHEET_H_CM), (14.85, 10.5)):
        u, v = V.cm_to_px(view.H_cm2px, x, y)
        tu, tv = camera.project(x, y)
        errors.append(np.hypot(u - tu, v - tv))
    return float(np.mean(errors))
