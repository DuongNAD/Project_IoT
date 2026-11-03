#!/usr/bin/env python3
"""
Thị giác máy tính (phần "mắt"): từ 2 camera ra danh sách vật nằm ở đâu trên tờ giấy (cm):

  - SheetTracker: dò 4 mã ArUco THẬT (ID 0-3) ở 4 góc tờ A4 in sẵn (generate_aruco_a4.py) để tính Homography giữa
    pixel và cm trên mặt giấy, cho cả hai camera. Nhớ vị trí các mã nên cánh tay che mất 1-2 mã vẫn giữ được lưới tọa độ.
  - ObjectWorker: luồng nền tìm vật: tách vật có màu trên nền giấy trắng (mặc định) và tùy chọn thêm YOLO11.
  - find_objects: đổi các phát hiện thành vật có vị trí (x, y) cm, đã hiệu chỉnh phối cảnh theo độ cao vật.
  - ArucoYoloTracker: ghép các phần trên, vẽ lớp phủ gọn lên ảnh. Danh sách vật (tracker.objects) được main.py đưa cho control.py.

Hệ tọa độ tờ giấy: gốc ở góc ngoài mã ID 0, X chạy ID 0 -> ID 1 (29.7 cm), Y chạy ID 0 -> ID 3 (21.0 cm).
"""

import math
import threading
import time
from collections import deque
from dataclasses import dataclass, field

import cv2
import numpy as np

# Kích thước thực tế của tờ A4 đặt ngang (cm): X = 29.7, Y = 21.0
SHEET_W_CM = 29.7
SHEET_H_CM = 21.0

# Mã ArUco in trên tờ A4 (xem generate_aruco_a4.py): mỗi mã 2.8 x 2.8 cm, cách mép giấy 0.25 cm
MARKER_SIZE_CM = 2.8
MARKER_MARGIN_CM = 0.25
SHEET_MARKER_IDS = (0, 1, 2, 3)  # ID 0: Trên-Trái, ID 1: Trên-Phải, ID 2: Dưới-Phải, ID 3: Dưới-Trái (nhìn tờ giấy in)

# Tọa độ thực (cm) của 4 góc tờ giấy tương ứng với 4 mã ArUco (ID 0, 1, 2, 3)
CORNER_COORDS_CM = {
    0: (0.0, 0.0),
    1: (SHEET_W_CM, 0.0),
    2: (SHEET_W_CM, SHEET_H_CM),
    3: (0.0, SHEET_H_CM),
}

ARUCO_DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

# Nhận diện: lớp COCO không phải vật cần gắp (đồ nội thất, màn hình, chính các bộ phận đen của cánh tay robot...)
YOLO_IGNORE_CLASSES = {
    "laptop", "tv", "bed", "book", "chair", "dining table", "couch", "person",
    "keyboard", "mouse", "remote", "cell phone",
}


def make_aruco_detector():
    return cv2.aruco.ArucoDetector(ARUCO_DICT, cv2.aruco.DetectorParameters())


def marker_corners_cm(marker_id):
    """4 góc (cm) của mã ArUco ID 0-3 trên tờ A4 theo thứ tự OpenCV trả về: TL, TR, BR, BL của chính mã."""
    s, m = MARKER_SIZE_CM, MARKER_MARGIN_CM
    W, H = SHEET_W_CM, SHEET_H_CM
    boxes = {
        0: [[m, m], [m + s, m], [m + s, m + s], [m, m + s]],
        1: [[W - m - s, m], [W - m, m], [W - m, m + s], [W - m - s, m + s]],
        2: [[W - m - s, H - m - s], [W - m, H - m - s], [W - m, H - m], [W - m - s, H - m]],
        3: [[m, H - m - s], [m + s, H - m - s], [m + s, H - m], [m, H - m]],
    }
    return np.float32(boxes[marker_id])


def sheet_quad_px(H_cm2px):
    """4 góc tờ giấy (0,0), (W,0), (W,H), (0,H) chiếu lên ảnh, kiểu float32 (4, 2)."""
    corners = np.float32([[[0, 0], [SHEET_W_CM, 0], [SHEET_W_CM, SHEET_H_CM], [0, SHEET_H_CM]]])
    return cv2.perspectiveTransform(corners, H_cm2px)[0]


def px_to_cm(H_px2cm, x, y):
    pt = cv2.perspectiveTransform(np.float32([[[x, y]]]), H_px2cm)[0][0]
    return float(pt[0]), float(pt[1])


def cm_to_px(H_cm2px, x, y):
    pt = cv2.perspectiveTransform(np.float32([[[x, y]]]), H_cm2px)[0][0]
    return float(pt[0]), float(pt[1])


def perspective_strength(H_cm2px):
    """
    Độ "xiên" của góc nhìn tờ giấy: tỉ lệ độ dài hai cạnh song song (xa / gần) của tờ giấy trong ảnh trừ 1.
    Camera treo thẳng phía trên cho ~0.0x, camera nhìn xiên (MacBook đặt trên bàn) cho 0.3 trở lên.
    """
    q = sheet_quad_px(H_cm2px)
    top, right, bottom, left = (np.linalg.norm(q[(i + 1) % 4] - q[i]) for i in range(4))
    return max(max(top, bottom) / max(min(top, bottom), 1e-6), max(left, right) / max(min(left, right), 1e-6)) - 1.0


def bbox_size_mm(H_px2cm, bbox, ref_pt):
    """Kích thước (cạnh hẹp, cạnh dài) tính bằng mm của hộp bao trên mặt giấy, đo qua hai đường ngang / dọc qua tâm vật."""
    x1, y1, x2, y2 = bbox
    rx, ry = ref_pt
    pts = cv2.perspectiveTransform(np.float32([[[x1, ry], [x2, ry], [rx, y1], [rx, y2]]]), H_px2cm)[0]
    w = float(np.linalg.norm(pts[1] - pts[0])) * 10.0
    h = float(np.linalg.norm(pts[3] - pts[2])) * 10.0
    return min(w, h), max(w, h)


# ==============================================================================
# 1. Dò tờ A4 qua 4 mã ArUco thật
# ==============================================================================
@dataclass
class SheetView:
    """Kết quả dò tờ giấy trong một khung hình."""

    corners: list = field(default_factory=list)  # Góc pixel của MỌI mã ArUco thấy trong khung (kể cả ID 4, 5, 6, 10-29)
    ids: object = None                           # ndarray (N, 1) hoặc None
    H_px2cm: object = None
    H_cm2px: object = None
    source: str = "none"   # aruco: đủ mã trong khung | memory: dùng mã đã nhớ (đang bị che) | fallback: ước lượng | none
    n_seen: int = 0        # Số mã góc (ID 0-3) thấy trong khung này
    n_known: int = 0       # Số mã góc đang dùng để tính Homography (gồm cả mã nhớ lại)
    rms_px: float = 0.0    # Sai số chiếu lại 4 mã (pixel)


def order_quad_points(pts):
    """Sắp xếp 4 điểm góc theo thứ tự chuẩn: TL, TR, BR, BL (theo chiều kim đồng hồ trong ảnh)."""
    pts = np.asarray(pts, dtype=np.float32).reshape(4, 2)
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).reshape(-1)
    return np.float32([pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]])


def detect_sheet_quad_fallback(frame):
    """
    Không thấy mã ArUco: ước lượng 4 góc tờ giấy trắng bằng cách tách vùng sáng, ít màu lớn nhất (chạy trên ảnh thu nhỏ).
    Cạnh dài được gán cho trục X (0 -> 29.7 cm); gốc tọa độ chỉ là ước đoán nên kết quả chỉ để xem tạm.
    """
    scale = 0.25
    small = cv2.resize(frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (0, 0, 120), (180, 60, 255))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    h, w = mask.shape
    for c in sorted(cnts, key=cv2.contourArea, reverse=True)[:3]:
        if cv2.contourArea(c) < 0.08 * w * h:
            break
        quad = order_quad_points(cv2.boxPoints(cv2.minAreaRect(c))) / scale
        top_edge = np.linalg.norm(quad[1] - quad[0])
        right_edge = np.linalg.norm(quad[2] - quad[1])
        if top_edge < right_edge:  # Tờ giấy nằm dọc trong ảnh: xoay thứ tự góc để cạnh dài là trục X
            quad = np.float32([quad[1], quad[2], quad[3], quad[0]])
        return quad
    return None


def _fit_homography(pts_px, pts_cm):
    """Homography pixel -> cm và sai số chiếu lại (pixel), hoặc (None, inf) nếu suy biến."""
    H_px2cm, _ = cv2.findHomography(np.float32(pts_px), np.float32(pts_cm), 0)
    if H_px2cm is None:
        return None, math.inf
    try:
        H_cm2px = np.linalg.inv(H_px2cm)
    except np.linalg.LinAlgError:
        return None, math.inf
    back = cv2.perspectiveTransform(np.float32(pts_cm).reshape(-1, 1, 2), H_cm2px).reshape(-1, 2)
    rms = float(np.sqrt(np.mean(np.sum((back - np.float32(pts_px)) ** 2, axis=1))))
    return H_px2cm, rms


class SheetTracker:
    """
    Theo dõi tờ A4 trong ảnh của MỘT camera cố định.
    - Nhớ góc pixel (làm mượt bằng trung bình trượt) của từng mã nên khi cánh tay che mất 1-2 mã vẫn giữ được Homography.
    - Camera hoặc tờ giấy bị xô lệch (các mã đang thấy nhảy quá bump_px so với bộ nhớ, liên tiếp vài khung)
      thì xóa bộ nhớ và tính lại từ các mã đang thấy.
    - allow_fallback: không có đủ mã thì ước lượng tạm bằng cách tách tờ giấy trắng (dùng cho cam TREN).
    """

    def __init__(self, allow_fallback=False, alpha=0.35, min_markers=2, bump_px=12.0, memory_s=120.0, max_rms_px=4.0):
        self.detector = make_aruco_detector()
        self.allow_fallback = allow_fallback
        self.alpha = alpha
        self.min_markers = min_markers
        self.bump_px = bump_px
        self.memory_s = memory_s
        self.max_rms_px = max_rms_px
        self.memory = {}  # id -> {"pts": float32 (4, 2), "t": thời điểm thấy gần nhất}
        self.last = SheetView()
        self._bump_frames = 0

    def reset(self):
        """Xóa bộ nhớ các mã (phím U): dùng khi vừa dời camera hoặc dời tờ giấy."""
        self.memory.clear()
        self._bump_frames = 0

    def _merge(self, seen, now):
        shifts = [float(np.abs(pts - self.memory[i]["pts"]).max()) for i, pts in seen.items() if i in self.memory]
        if shifts and float(np.median(shifts)) > self.bump_px:
            self._bump_frames += 1
            if self._bump_frames >= 3:  # Thật sự bị xô lệch (không phải một khung nhiễu)
                self.memory.clear()
                self._bump_frames = 0
        else:
            self._bump_frames = 0
        for i, pts in seen.items():
            m = self.memory.get(i)
            if m is None:
                self.memory[i] = {"pts": pts.copy(), "t": now}
            else:
                m["pts"] = (1.0 - self.alpha) * m["pts"] + self.alpha * pts
                m["t"] = now
        for i in [i for i, m in self.memory.items() if now - m["t"] > self.memory_s]:
            del self.memory[i]

    def correspondences(self, ids=None):
        """Cặp điểm (pixel, cm) của các mã đang nhớ (hoặc chỉ các mã trong ids)."""
        pts_px, pts_cm = [], []
        for i, m in self.memory.items():
            if ids is not None and i not in ids:
                continue
            pts_px.extend(m["pts"])
            pts_cm.extend(marker_corners_cm(i))
        return np.float32(pts_px).reshape(-1, 2), np.float32(pts_cm).reshape(-1, 2)

    def _solve(self, view, frame):
        if len(self.memory) >= self.min_markers:
            pts_px, pts_cm = self.correspondences()
            H_px2cm, rms = _fit_homography(pts_px, pts_cm)
            # Một mã nhận nhầm làm lệch hẳn: thử bỏ lần lượt từng mã và giữ cách tốt nhất
            if rms > self.max_rms_px and len(self.memory) >= 3:
                best = (H_px2cm, rms, None)
                for drop in list(self.memory):
                    keep = [i for i in self.memory if i != drop]
                    H2, rms2 = _fit_homography(*self.correspondences(keep))
                    if H2 is not None and rms2 < best[1]:
                        best = (H2, rms2, drop)
                if best[2] is not None and best[1] < 0.5 * rms:
                    H_px2cm, rms = best[0], best[1]
                    self.memory.pop(best[2], None)
                    view.n_known = len(self.memory)
            if H_px2cm is not None:
                view.H_px2cm = H_px2cm
                view.H_cm2px = np.linalg.inv(H_px2cm)
                view.rms_px = rms
                view.source = "aruco" if view.n_seen >= self.min_markers else "memory"
                return
        if self.allow_fallback:
            quad = detect_sheet_quad_fallback(frame)
            if quad is not None:
                dst = np.float32([[0, 0], [SHEET_W_CM, 0], [SHEET_W_CM, SHEET_H_CM], [0, SHEET_H_CM]])
                view.H_px2cm = cv2.getPerspectiveTransform(quad, dst)
                view.H_cm2px = cv2.getPerspectiveTransform(dst, quad)
                view.source = "fallback"

    def update(self, frame):
        corners, ids, _ = self.detector.detectMarkers(frame)
        seen = {}
        if ids is not None:
            for c, i in zip(corners, ids.flatten()):
                if int(i) in SHEET_MARKER_IDS:
                    seen[int(i)] = np.asarray(c, dtype=np.float32).reshape(4, 2)
        self._merge(seen, time.time())
        view = SheetView(
            corners=list(corners) if ids is not None else [], ids=ids, n_seen=len(seen), n_known=len(self.memory)
        )
        self._solve(view, frame)
        self.last = view
        return view


# ==============================================================================
# 2. Tìm vật thể: tách vật có màu trên giấy trắng + YOLO11 (tùy chọn)
# ==============================================================================
# Vật cần gắp phải lọt vào miệng kẹp (mở tối đa 60 mm, chừa dư cho sai số đo): khối màu rộng hơn hẳn là bàn tay hay đồ vật khác
COLOR_MAX_NARROW_MM = 80.0
COLOR_MAX_LONG_MM = 180.0


def detect_color_objects(frame, H_px2cm, H_cm2px, ppc=8):
    """
    Vật có màu (độ bão hòa cao) nằm trên giấy trắng: dựng ảnh phẳng của tờ A4 (ppc pixel / cm) rồi tách theo HSV.
    Bỏ qua dây điện mảnh (phép mở ảnh), mọi khối dính vào phần đen của cánh tay robot, khối chạm mép giấy hoặc to hơn miệng kẹp
    (bàn tay người đưa vào cũng là một khối màu da rất bão hòa).
    Trả về danh sách {"bbox", "ref_pt", "cls", "conf", "source", "size_mm"} trên TỌA ĐỘ PIXEL ẢNH GỐC.
    """
    W, H = SHEET_W_CM, SHEET_H_CM
    big = 2 * ppc
    M = np.diag([big, big, 1.0]) @ H_px2cm
    flat = cv2.warpPerspective(frame, M, (int(round(W * big)), int(round(H * big))), flags=cv2.INTER_LINEAR)
    flat = cv2.resize(flat, (int(round(W * ppc)), int(round(H * ppc))), interpolation=cv2.INTER_AREA)

    hsv = cv2.cvtColor(flat, cv2.COLOR_BGR2HSV)
    sat, val = hsv[..., 1], hsv[..., 2]
    colored = (((sat >= 90) & (val >= 60)).astype(np.uint8)) * 255
    dark = ((val < 70).astype(np.uint8)) * 255

    margin = int(round(1.0 * ppc))  # Bỏ viền 1 cm sát mép giấy (nền bàn lọt vào khi lưới lệch nhẹ)
    border = np.zeros_like(colored)
    border[margin:-margin, margin:-margin] = 255
    colored = cv2.bitwise_and(colored, border)

    k_open = int(0.7 * ppc) | 1
    colored = cv2.morphologyEx(colored, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_open, k_open)))
    colored = cv2.morphologyEx(colored, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    k_dark = int(1.2 * ppc) | 1
    dark_near = cv2.dilate(dark, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_dark, k_dark)))

    found = []
    rows, cols = colored.shape
    edge = margin + 2  # Khối chạm vạch cắt viền (phần sát mép giấy đã bỏ) là vật đưa từ ngoài vào, kích thước thật chưa biết
    cnts, _ = cv2.findContours(colored, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in cnts:
        area_cm2 = cv2.contourArea(c) / float(ppc * ppc)
        if not 1.5 <= area_cm2 <= 150.0:
            continue
        x, y, bw, bh = cv2.boundingRect(c)
        if x <= edge or y <= edge or x + bw >= cols - edge or y + bh >= rows - edge:
            continue  # Bàn tay / ngón tay thò từ ngoài vào: không phải vật đang nằm trên giấy chờ gắp
        (_, _), (rw, rh), _ = cv2.minAreaRect(c)
        narrow_mm, long_mm = min(rw, rh) / ppc * 10.0, max(rw, rh) / ppc * 10.0
        if narrow_mm > COLOR_MAX_NARROW_MM or long_mm > COLOR_MAX_LONG_MM:
            continue  # To hơn miệng kẹp nhiều: bàn tay hay đồ vật khác đặt trên giấy
        blob = np.zeros_like(colored)
        cv2.drawContours(blob, [c], -1, 255, -1)
        if cv2.countNonZero(cv2.bitwise_and(blob, dark_near)) > 0.30 * cv2.countNonZero(blob):
            continue  # Dính vào cánh tay đen: là bộ phận của robot (dây, nhãn servo), không phải vật cần gắp
        m = cv2.moments(c)
        if m["m00"] <= 0:
            continue
        cx, cy = m["m10"] / m["m00"] / ppc, m["m01"] / m["m00"] / ppc
        box_cm = np.float32([[[x / ppc, y / ppc], [(x + bw) / ppc, y / ppc], [(x + bw) / ppc, (y + bh) / ppc], [x / ppc, (y + bh) / ppc]]])
        box_px = cv2.perspectiveTransform(box_cm, H_cm2px)[0]
        center_px = cm_to_px(H_cm2px, cx, cy)
        found.append({
            "bbox": (float(box_px[:, 0].min()), float(box_px[:, 1].min()), float(box_px[:, 0].max()), float(box_px[:, 1].max())),
            "ref_pt": center_px,
            "cls": "vat mau",
            "conf": 0.6,
            "source": "color",
            "size_mm": (narrow_mm, long_mm),
        })
    return found


class ObjectWorker:
    """
    Luồng nền tìm vật trên ảnh cam TREN để không làm chậm hình hiển thị: tách vật có màu trên giấy trắng
    (luôn chạy) và YOLO11 trên vùng tờ giấy (chỉ khi use_yolo, bắt được cả vật không có màu).
    """

    def __init__(self, use_yolo=False):
        self.use_yolo = use_yolo
        self.model = None
        self.device = "cpu"
        self.lock = threading.Lock()
        self.latest = {"topdown": None}
        self.detections = {"topdown": []}
        self._seq = {"topdown": 0}
        self._done = {"topdown": 0}
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _init_model(self):
        try:
            import os

            import torch
            from ultralytics import YOLO

            model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yolo11s.pt")
            self.model = YOLO(model_path if os.path.exists(model_path) else "yolo11s.pt")
            # GPU NVIDIA (Windows / Linux) cần bản torch có CUDA; pip mặc định cài bản chỉ chạy CPU
            if torch.cuda.is_available():
                self.device = "cuda:0"
            elif torch.backends.mps.is_available():
                self.device = "mps"
        except Exception as e:
            print(f"⚠️ Không tải được YOLO, chỉ còn tách vật theo màu: {e}")
            self.model = None

    def submit(self, mode, frame, H_px2cm=None, H_cm2px=None):
        with self.lock:
            self.latest[mode] = (frame, H_px2cm, H_cm2px)
            self._seq[mode] += 1

    def get(self, mode):
        with self.lock:
            return list(self.detections.get(mode, []))

    def _infer(self, image, conf, imgsz):
        """Chạy YOLO; lỗi trên GPU (MPS) thì chuyển sang CPU, vẫn lỗi thì tắt YOLO."""
        try:
            return self.model(image, conf=conf, imgsz=imgsz, device=self.device, verbose=False)[0]
        except Exception as e:
            if self.device != "cpu":
                print(f"⚠️ YOLO lỗi trên {self.device}, chuyển sang CPU: {e}")
                self.device = "cpu"
                return self._infer(image, conf, imgsz)
            print(f"⚠️ YOLO lỗi, tắt YOLO: {e}")
            self.model = None
            return None

    def _yolo_top(self, frame, quad):
        """Chạy YOLO trên vùng quyển vở để phát hiện vật thể nằm trên mặt giấy."""
        h, w = frame.shape[:2]
        x1 = max(0, int(quad[:, 0].min()) - 10)
        y1 = max(0, int(quad[:, 1].min()) - 10)
        x2 = min(w, int(quad[:, 0].max()) + 10)
        y2 = min(h, int(quad[:, 1].max()) + 10)
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return []
        results = self._infer(crop, 0.12, 960)
        if results is None:
            return []
        sheet_area = cv2.contourArea(quad)
        poly = quad.reshape(-1, 1, 2)
        margin = 0.6 * math.sqrt(sheet_area / (SHEET_W_CM * SHEET_H_CM))  # Tâm vật cách mép giấy ít nhất 0.6 cm
        found = []
        for box in results.boxes:
            cls_name = results.names[int(box.cls[0])]
            if cls_name in YOLO_IGNORE_CLASSES:
                continue
            bx1, by1, bx2, by2 = box.xyxy[0].tolist()
            fx1, fy1, fx2, fy2 = bx1 + x1, by1 + y1, bx2 + x1, by2 + y1
            area = (fx2 - fx1) * (fy2 - fy1)
            if area > 0.40 * sheet_area or area < 400:
                continue
            cx, cy = (fx1 + fx2) / 2.0, (fy1 + fy2) / 2.0
            if cv2.pointPolygonTest(poly, (cx, cy), True) >= margin:
                found.append({
                    "bbox": (fx1, fy1, fx2, fy2), "ref_pt": (cx, cy),
                    "cls": cls_name, "conf": float(box.conf[0]), "source": "yolo",
                })
        return found

    def _detect_top(self, frame, H_px2cm, H_cm2px):
        if H_px2cm is None or H_cm2px is None:
            return []
        quad = sheet_quad_px(H_cm2px)
        yolo = self._yolo_top(frame, quad) if self.model is not None else []
        for det in yolo:  # Đo kích thước thật (mm) của vật trên mặt giấy, không phụ thuộc YOLO gọi tên lớp gì
            det["size_mm"] = bbox_size_mm(H_px2cm, det["bbox"], det["ref_pt"])
        blobs = detect_color_objects(frame, H_px2cm, H_cm2px)
        for b in blobs:  # Vật đã có YOLO đặt tên thì không thêm lần nữa
            bx, by = b["ref_pt"]
            if not any(d["bbox"][0] <= bx <= d["bbox"][2] and d["bbox"][1] <= by <= d["bbox"][3] for d in yolo):
                yolo.append(b)
        return yolo

    def _loop(self):
        if self.use_yolo:
            self._init_model()
        while self.running:
            worked = False
            for mode in ("topdown",):
                with self.lock:
                    item, seq = self.latest[mode], self._seq[mode]
                if item is None or seq == self._done[mode]:
                    continue
                self._done[mode] = seq
                frame, H_px2cm, H_cm2px = item
                try:
                    dets = self._detect_top(frame, H_px2cm, H_cm2px)
                except Exception as e:
                    print(f"⚠️ Lỗi nhận diện vật thể ({mode}): {e}")
                    dets = []
                with self.lock:
                    self.detections[mode] = dets
                worked = True
            if not worked:
                time.sleep(0.03)

    def stop(self):
        self.running = False


# ==============================================================================
# 3. Từ các phát hiện tới danh sách vật có vị trí trên tờ giấy
# ==============================================================================
# Kích thước (mm) vật theo mã ArUco ID 10-29 dán trên vật, theo lớp YOLO, và mặc định cho vật tách theo màu
OBJECT_SPECS = {
    10: {"name": "Hop_Vuong_ID10", "w_mm": 40.0, "l_mm": 40.0, "h_mm": 40.0},
    11: {"name": "Hop_Xanh_ID11", "w_mm": 35.0, "l_mm": 50.0, "h_mm": 35.0},
    12: {"name": "Hop_Do_ID12", "w_mm": 30.0, "l_mm": 60.0, "h_mm": 40.0},
    13: {"name": "Khoi_Tru_ID13", "w_mm": 35.0, "l_mm": 35.0, "h_mm": 50.0},
}
DEFAULT_OBJ_SPEC = {"name": "Vat_ArUco", "w_mm": 35.0, "l_mm": 35.0, "h_mm": 40.0}
CLASS_SPECS = {
    # Cốc đỏ số 3 trên bàn thử (đo ngày 2026-11-02: thân ~34 mm, nắp ~40 mm, cao ~50 mm). Cốc khác thì sửa số ở đây.
    "cup": {"w_mm": 34.0, "h_mm": 50.0},
}

# Cam TREN treo cao ~46 cm nhìn thẳng xuống: tâm nắp cốc cao 5 cm hiện lệch ra xa tâm ảnh ~11% khoảng cách tới tâm, nên vị trí đo được nằm xa hơn
# vị trí thật dưới đáy cốc ~1 cm. Đo 2026-11-02: cam TREN (20.6, 6.8) cm, cam MacBook (đáy cốc) (20.0, 7.8) cm; sau hiệu chỉnh còn lệch 0.2 cm.
PARALLAX_CAM_HEIGHT_CM = 46.0   # Độ cao cam TREN so với mặt bàn (cm); 0 = không hiệu chỉnh
COLORFUL_MIN_SATURATION = 90    # Vật YOLO phải CÓ MÀU (HSV: bão hòa >= 90, sáng >= 90): YOLO hay gọi thân servo đen là "traffic light" / "motorcycle"
COLORFUL_MIN_VALUE = 90


def correct_parallax(point_cm, nadir_cm, obj_height_cm, cam_height_cm=None):
    """
    Vật cao obj_height_cm nhìn từ cam treo cao cam_height_cm bị đẩy ra xa điểm nhìn thẳng xuống (nadir): đưa vị trí đo được (đỉnh vật chiếu
    xuống mặt giấy) về vị trí thật của vật trên mặt giấy: p_thật = nadir + (p_đo - nadir) * (H - h) / H.
    """
    H = PARALLAX_CAM_HEIGHT_CM if cam_height_cm is None else cam_height_cm
    if H <= 0 or obj_height_cm <= 0 or obj_height_cm >= H:
        return float(point_cm[0]), float(point_cm[1])
    k = (H - obj_height_cm) / H
    return (float(nadir_cm[0] + (point_cm[0] - nadir_cm[0]) * k), float(nadir_cm[1] + (point_cm[1] - nadir_cm[1]) * k))


def is_colorful(img, px):
    """Điểm px trên ảnh có màu (bão hòa và sáng đủ): cốc đỏ / hộp màu là True, thân servo đen, giấy trắng, kim loại xám là False."""
    h, w = img.shape[:2]
    x, y = int(round(float(px[0]))), int(round(float(px[1])))
    if not (0 <= x < w and 0 <= y < h):
        return False
    patch = img[max(0, y - 6):y + 7, max(0, x - 6):x + 7]
    hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV).reshape(-1, 3)
    return bool(np.median(hsv[:, 1]) >= COLORFUL_MIN_SATURATION and np.median(hsv[:, 2]) >= COLORFUL_MIN_VALUE)


def spec_for_detection(det):
    """Tên và kích thước (mm) của vật do YOLO / tách màu tìm được: theo lớp YOLO nếu đã biết, không thì đo từ chính vật."""
    spec = dict(DEFAULT_OBJ_SPEC)
    cls = det.get("cls", "")
    spec["name"] = f"YOLO:{cls}" if det.get("source") == "yolo" else "Vat mau"
    if cls in CLASS_SPECS:
        spec.update(CLASS_SPECS[cls])
    elif det.get("size_mm"):
        spec["w_mm"] = max(15.0, min(60.0, float(det["size_mm"][0])))  # Cạnh hẹp nhất, kẹp không mở quá 60 mm
    return spec


def find_objects(corners, ids, dets, H_px2cm, frame_shape, raw_img=None):
    """
    Danh sách vật trên ảnh cam TREN, mỗi vật {"name", "x_cm", "y_cm", "w_mm", "h_mm", "px", "source"}:
      1. Vật dán mã ArUco ID 10-29 (tâm mã).
      2. Vật tách theo màu và (nếu bật) YOLO. Vật YOLO phải có màu (is_colorful trên raw_img), không thì bỏ.
    Vị trí đã hiệu chỉnh phối cảnh theo độ cao vật: tâm ảnh coi là điểm cam nhìn thẳng xuống.
    """
    found = []
    if ids is not None and len(ids) > 0:
        for c, mid in zip(corners, ids.flatten()):
            mid = int(mid)
            if 10 <= mid <= 29:
                center = np.asarray(c).reshape(4, 2).mean(axis=0)
                x_cm, y_cm = px_to_cm(H_px2cm, float(center[0]), float(center[1]))
                spec = OBJECT_SPECS.get(mid, DEFAULT_OBJ_SPEC)
                found.append({"name": f"{spec['name']} (ArUco #{mid})", "x_cm": x_cm, "y_cm": y_cm, "w_mm": spec["w_mm"],
                              "h_mm": spec["h_mm"], "px": center, "source": "aruco"})
    for det in dets:
        rx, ry = det["ref_pt"]
        x_cm, y_cm = px_to_cm(H_px2cm, rx, ry)
        if any(math.hypot(x_cm - o["x_cm"], y_cm - o["y_cm"]) < 2.5 for o in found):
            continue  # Vật đã có mã ArUco
        if det.get("source") == "yolo" and raw_img is not None and not is_colorful(raw_img, (rx, ry)):
            continue
        spec = spec_for_detection(det)
        found.append({"name": spec["name"], "x_cm": x_cm, "y_cm": y_cm, "w_mm": spec["w_mm"], "h_mm": spec["h_mm"],
                      "px": (rx, ry), "source": det.get("source", "color")})
    if PARALLAX_CAM_HEIGHT_CM > 0 and found:
        h, w = frame_shape[:2]
        nadir = px_to_cm(H_px2cm, w / 2.0, h / 2.0)  # Điểm cam nhìn thẳng xuống = tâm ảnh
        for o in found:
            o["x_cm"], o["y_cm"] = correct_parallax((o["x_cm"], o["y_cm"]), nadir, o["h_mm"] / 10.0)
    return found


# ==============================================================================
# 4. Vẽ lớp phủ gọn lên ảnh (viền tờ giấy, lưới 5 cm, vật tìm thấy)
# ==============================================================================
def _t(value, k):
    """Độ dày / bán kính đã phóng theo độ phân giải ảnh (tối thiểu 1 px)."""
    return max(1, int(round(value * k)))


def ui_scale(frame):
    """Hệ số phóng chữ và nét vẽ theo độ rộng ảnh: ảnh 1920 px sau khi thu về 640 px vẫn đọc được."""
    return max(1.0, frame.shape[1] / 1280.0)


def put_outlined(img, text, org, scale, color, thick, k, outline=(0, 0, 0)):
    """Chữ có viền đen cho dễ đọc trên mọi nền."""
    x, y = int(org[0]), int(org[1])
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale * k, outline, _t(thick + 2, k), cv2.LINE_AA)
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale * k, color, _t(thick, k), cv2.LINE_AA)


def draw_sheet_overlay(work, H_cm2px, k):
    """Viền tờ giấy và lưới 5 cm (mờ) để thấy ngay lưới tọa độ có bám đúng tờ giấy không."""
    W, H = SHEET_W_CM, SHEET_H_CM
    border_px = np.int32(cv2.perspectiveTransform(np.float32([[[0, 0], [W, 0], [W, H], [0, H]]]), H_cm2px)[0])
    cv2.polylines(work, [border_px], True, (200, 200, 200), _t(2, k), cv2.LINE_AA)
    for gx in (5.0, 10.0, 15.0, 20.0, 25.0):
        seg = np.int32(cv2.perspectiveTransform(np.float32([[[gx, 0], [gx, H]]]), H_cm2px)[0])
        cv2.line(work, tuple(seg[0]), tuple(seg[1]), (150, 150, 150), _t(1, k), cv2.LINE_AA)
    for gy in (5.0, 10.0, 15.0):
        seg = np.int32(cv2.perspectiveTransform(np.float32([[[0, gy], [W, gy]]]), H_cm2px)[0])
        cv2.line(work, tuple(seg[0]), tuple(seg[1]), (150, 150, 150), _t(1, k), cv2.LINE_AA)


def draw_object(work, obj, k):
    """Vòng xanh quanh vật tìm thấy kèm tên và tọa độ (cm) trên tờ giấy."""
    center = (int(obj["px"][0]), int(obj["px"][1]))
    cv2.circle(work, center, _t(22, k), (0, 255, 128), _t(3, k), cv2.LINE_AA)
    cv2.circle(work, center, _t(4, k), (0, 0, 255), -1)
    put_outlined(work, f"{obj['name']}  X={obj['x_cm']:.1f} Y={obj['y_cm']:.1f}cm", (center[0] + 28 * k, center[1] - 6 * k), 0.55, (0, 255, 128), 2, k)


def draw_target(work, H_cm2px, target_cm, claw_cm, k):
    """Chỗ vật cần tới (vòng cam trên mặt giấy) và chỗ đầu kẹp theo mô hình (dấu + vàng) để thấy khoảng cách còn lại."""
    if target_cm is not None:
        p = tuple(np.int32(cm_to_px(H_cm2px, *target_cm)))
        cv2.circle(work, p, _t(26, k), (0, 165, 255), _t(3, k), cv2.LINE_AA)
        put_outlined(work, "DICH", (p[0] + 30 * k, p[1] + 8 * k), 0.55, (0, 165, 255), 2, k)
    if claw_cm is not None:
        q = tuple(np.int32(cm_to_px(H_cm2px, *claw_cm)))
        cv2.drawMarker(work, q, (0, 255, 255), cv2.MARKER_CROSS, _t(24, k), _t(2, k), cv2.LINE_AA)
        put_outlined(work, "KEP", (q[0] + 14 * k, q[1] - 8 * k), 0.5, (0, 255, 255), 2, k)


def draw_sheet_status(work, view, k):
    """Dòng trạng thái lưới tọa độ ở góc dưới trái: cho biết lưới đang dựa vào mã ArUco thật, mã đã nhớ hay chỉ là ước lượng."""
    if view.source == "aruco":
        text, color = f"Luoi A4: {view.n_known}/4 ma ArUco (sai so {view.rms_px:.1f}px)", (0, 230, 100)
    elif view.source == "memory":
        text, color = f"Luoi A4: dung {view.n_known}/4 ma da nho (dang bi che)", (0, 200, 255)
    elif view.source == "fallback":
        text, color = "UOC LUONG goc giay: khong thay ma ArUco 0-3", (0, 120, 255)
    else:
        text, color = "KHONG THAY TO A4: kiem tra 4 ma ArUco 0-3", (60, 60, 255)
    put_outlined(work, text, (15 * k, work.shape[0] - 18 * k), 0.62, color, 2, k)


# ==============================================================================
# 5. Bộ theo dõi tổng hợp
# ==============================================================================
class ArucoYoloTracker:
    """
    Ghép ArUco (4 góc tờ A4) + Homography + tìm vật:
      - process_frame(frame, "topdown" | "side") trả về ảnh đã vẽ lớp phủ gọn; cam TREN còn cập nhật danh sách vật self.objects.
      - Tìm vật chạy trên luồng nền (không làm giảm FPS hiển thị camera).
    """

    def __init__(self, use_yolo=False):
        # Cam NGANG nhìn xiên nên sai số chiếu lại lớn hơn cam TREN
        self.sheets = {
            "topdown": SheetTracker(allow_fallback=True),
            "side": SheetTracker(allow_fallback=False, max_rms_px=15.0),
        }
        self.worker = ObjectWorker(use_yolo=use_yolo)
        self.latest_view = {"topdown": SheetView(), "side": SheetView()}
        self.objects = []  # Vật thấy ở khung cam TREN gần nhất: {"name", "x_cm", "y_cm", "w_mm", "h_mm", "px", "source"}
        self.running = True

    def reset_sheet(self):
        """Phím U: quên vị trí các mã ArUco đã nhớ (vừa dời camera hoặc tờ giấy)."""
        for sheet in self.sheets.values():
            sheet.reset()

    def forget_objects(self):
        """Cam TREN mất tín hiệu: bỏ danh sách vật cũ để không gợi ý theo dữ liệu đã cũ."""
        self.objects = []

    def stop(self):
        self.running = False
        self.worker.stop()

    def process_frame(self, raw_frame, mode="topdown"):
        """
        1. Dò 4 mã ArUco thật (ID 0-3) -> Homography pixel <-> cm của tờ A4 (nhớ lại khi bị che).
        2. Vẽ viền tờ giấy, lưới 5 cm; cam TREN: tìm vật, vẽ vòng quanh vật và cập nhật self.objects.
        """
        if raw_frame is None:
            return None
        view = self.sheets[mode].update(raw_frame)
        self.latest_view[mode] = view
        k = ui_scale(raw_frame)
        work = raw_frame.copy()
        if view.ids is not None and len(view.ids) > 0:
            cv2.aruco.drawDetectedMarkers(work, view.corners, view.ids, (0, 255, 0))
        if view.H_px2cm is not None and view.H_cm2px is not None:
            draw_sheet_overlay(work, view.H_cm2px, k)
            if mode == "topdown":
                self.worker.submit(mode, raw_frame, view.H_px2cm, view.H_cm2px)
                self.objects = find_objects(view.corners, view.ids, self.worker.get(mode), view.H_px2cm, raw_frame.shape, raw_img=raw_frame)
                for obj in self.objects:
                    draw_object(work, obj, k)
        elif mode == "topdown":
            self.objects = []  # Không có lưới tọa độ thì không biết vật nằm ở đâu
        draw_sheet_status(work, view, k)
        return work
