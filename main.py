import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from urllib.parse import urlparse
import cv2
import numpy as np
from grasp_assist_4dof import GraspAssist4DOF
from guide_screen import GUIDE_WINDOW, build_guide_screen

# Terminal Windows (cp1252, hoặc khi chuyển hướng ra file) không in được emoji: thay bằng '?' thay vì làm chương trình sập
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

# Kích thước hiển thị chuẩn cho mỗi góc nhìn (Rộng x Cao)
VIEW_WIDTH = 640
VIEW_HEIGHT = 480

# Thư mục lưu ảnh chụp (phím 's'), nằm cạnh main.py
CAPTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "captures")

# Camera quá số giây này không ra hình (vừa cấp quyền Camera, vừa cắm lại cáp...) thì tự mở lại
RETRY_SECONDS = 4

# Cam 1 = webcam laptop, đặt thấp nhìn NGANG vào vùng làm việc (mode "side", cửa sổ bên trái).
# Cam 2 = điện thoại làm webcam (iPhone Continuity Camera / Iriun / DroidCam / Camo...) gắn trên cao nhìn TỪ TRÊN XUỐNG
# (mode "topdown", bên phải). Tự tìm 2 camera theo tên (xem list_camera_names); không đọc được tên thì dùng 2 chỉ số
# mặc định dưới đây (Windows đo trên máy Dell: 0 = Iriun Webcam, 1 = Integrated Webcam; macOS: 0 thường là camera MacBook).
# Hình bị đảo (điện thoại hiện ở cam laptop và ngược lại): bấm 'X' để đổi chỗ 2 camera.
PHONE_NAME_KEYWORDS = ("iphone", "iriun", "droidcam", "epoccam", "camo")
# Không chọn làm webcam laptop: camera ảo (OBS Virtual Camera...) và "Desk View" (cảnh bàn cắt ra từ iPhone trên macOS)
NOT_LAPTOP_KEYWORDS = ("virtual", "desk view")
DEFAULT_LAPTOP_INDEX, DEFAULT_PHONE_INDEX = (1, 0) if sys.platform == "win32" else (0, 1)

# Điện thoại dùng app IP Webcam (Start server): điền địa chỉ app hiển thị ở đây, hoặc truyền lúc chạy
# `python main.py 192.168.1.5` / `python main.py http://192.168.1.5:8080/video`, hoặc đặt biến môi trường PHONE_URL.
# Để trống = dùng Iriun/DroidCam như một webcam (theo chỉ số). PC và điện thoại phải cùng mạng Wi-Fi.
PHONE_URL_DEFAULT = ""

# Hình điện thoại bị ngược thì đổi thành cv2.ROTATE_180 (hoặc cv2.ROTATE_90_CLOCKWISE...); None = giữ nguyên
PHONE_ROTATE = None


def letterbox(frame):
    """Thu phóng giữ nguyên tỉ lệ rồi chèn viền đen cho vừa khung chuẩn (cam 16:9 không bị ép méo về 4:3)."""
    h, w = frame.shape[:2]
    scale = min(VIEW_WIDTH / w, VIEW_HEIGHT / h)
    new_w, new_h = round(w * scale), round(h * scale)
    canvas = np.zeros((VIEW_HEIGHT, VIEW_WIDTH, 3), dtype=np.uint8)
    x, y = (VIEW_WIDTH - new_w) // 2, (VIEW_HEIGHT - new_h) // 2
    canvas[y:y + new_h, x:x + new_w] = cv2.resize(frame, (new_w, new_h))
    return canvas


def open_capture(source):
    """Mở camera theo chỉ số (Windows dùng DirectShow: mở nhanh và chỉ số ổn định hơn MSMF) hoặc theo URL luồng."""
    if isinstance(source, int) and sys.platform == "win32":
        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(source)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


class CameraStream:
    """Đọc camera trên luồng riêng (Thread) để luôn lấy frame mới nhất, triệt tiêu độ trễ (delay)."""

    def __init__(self, source, name, hint="", rotate=None):
        self.source = source
        self.name = name
        self.hint = hint
        self.rotate = rotate
        self.cap = None  # Mở trong luồng nền: mở camera mất 1-3 giây, không để nó làm đơ cửa sổ chính
        self.ret = False
        self.frame = None
        self.last_frame_time = time.time()
        self.running = True
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        while self.running:
            if self.cap is None:
                cap = open_capture(self.source)
                if not self.running:  # Bị đóng trong lúc đang mở: nhả camera ngay, đừng giữ khóa thiết bị
                    cap.release()
                    break
                self.cap = cap
                self.last_frame_time = time.time()
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret and self.rotate is not None:
                    frame = cv2.rotate(frame, self.rotate)
                with self.lock:
                    self.ret = ret
                    if ret:
                        self.frame = frame
                        self.last_frame_time = time.time()
                if ret:
                    continue
            # Camera chưa mở được hoặc mất tín hiệu: nghỉ một nhịp, tránh vòng lặp chạy 100% CPU
            time.sleep(0.1)
            if self.is_stalled():
                # Quá RETRY_SECONDS vẫn không có hình (cắm lại cáp, vừa cấp quyền Camera...): đóng để vòng lặp mở lại
                self.cap.release()
                self.cap = None

    def is_stalled(self):
        """Quá RETRY_SECONDS chưa có frame mới: camera chưa mở được hoặc đã mất tín hiệu."""
        return time.time() - self.last_frame_time > RETRY_SECONDS

    def get_frame(self):
        with self.lock:
            if self.ret and self.frame is not None:
                # Đưa về cùng khung (640x480) để ghép ngang 2 màn hình không bị lệch
                resized = letterbox(self.frame)
            else:
                # Tạo khung nền đen thông báo nếu camera đang chờ tín hiệu
                resized = np.zeros((VIEW_HEIGHT, VIEW_WIDTH, 3), dtype=np.uint8)
                cv2.putText(
                    resized,
                    f"Dang cho tin hieu: {self.name}",
                    (60, VIEW_HEIGHT // 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 165, 255),
                    2,
                )
                if self.hint:
                    cv2.putText(
                        resized,
                        self.hint,
                        (20, VIEW_HEIGHT // 2 + 35),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (200, 200, 200),
                        1,
                    )

            # Vẽ nhãn tên góc nhìn ở góc trên bên trái mỗi khung hình
            cv2.putText(
                resized,
                self.name,
                (15, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )
            return resized

    def get_raw_frame(self):
        """Frame gốc (chưa thu nhỏ) mới nhất để lưu ảnh, hoặc None nếu chưa có tín hiệu."""
        with self.lock:
            if self.ret and self.frame is not None:
                return self.frame.copy()
            return None

    def release(self):
        self.running = False
        self.thread.join(timeout=1.0)
        cap = self.cap  # Luồng nền có thể đang đặt lại self.cap = None nếu join quá hạn
        if cap is not None:
            cap.release()


def save_snapshots(cameras):
    """Lưu frame gốc của từng camera vào CAPTURE_DIR, chung một mốc thời gian để dễ ghép cặp ảnh."""
    os.makedirs(CAPTURE_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for tag, cam in cameras:
        frame = cam.get_raw_frame()
        if frame is None:
            print(f"⚠️ {cam.name}: chưa có tín hiệu, không chụp được")
            continue
        path = os.path.join(CAPTURE_DIR, f"{stamp}_{tag}.jpg")
        if cv2.imwrite(path, frame):
            print(f"📸 Đã lưu {path}")
        else:
            print(f"⚠️ Không ghi được {path}")


def list_camera_names():
    """
    Tên các camera theo thứ tự chỉ số của OpenCV, [] nếu không đọc được.
    Windows: thứ tự cv2.CAP_DSHOW (cần pygrabber). macOS: danh sách camera của system_profiler, giả định cùng thứ tự
    với AVFoundation của OpenCV (như bản chạy trên Mac trước đây); chọn sai thì bấm 'X' hoặc '0'-'3' để chọn lại.
    """
    if sys.platform == "win32":
        try:
            from pygrabber.dshow_graph import FilterGraph
            return list(FilterGraph().get_input_devices())
        except Exception:
            return []
    if sys.platform == "darwin":
        try:
            out = subprocess.run(
                ["system_profiler", "SPCameraDataType", "-json"], capture_output=True, text=True, timeout=15
            ).stdout
            return [cam["_name"] for cam in json.loads(out)["SPCameraDataType"]]
        except (OSError, subprocess.TimeoutExpired, ValueError, KeyError, TypeError):
            return []
    return []


def find_camera_indices(want_phone=True):
    """
    Trả về (chỉ số webcam laptop, chỉ số camera điện thoại): tìm theo tên, không đọc được tên thì dùng chỉ số mặc định.
    want_phone=False (điện thoại dùng IP Webcam qua URL): không cần Iriun nên bỏ qua cảnh báo thiếu camera điện thoại.
    """
    names = list_camera_names()
    if not names:
        hint = " (cài `pip install pygrabber` để tự nhận)" if sys.platform == "win32" else ""
        print(
            f"ℹ️ Chưa đọc được tên camera{hint}: "
            f"dùng mặc định laptop=Index {DEFAULT_LAPTOP_INDEX}, điện thoại=Index {DEFAULT_PHONE_INDEX}"
        )
        return DEFAULT_LAPTOP_INDEX, DEFAULT_PHONE_INDEX
    print(f"📷 Camera: {', '.join(f'{i}={n}' for i, n in enumerate(names))}")
    # "Desk View" cũng là camera của iPhone nhưng chỉ là cảnh bàn cắt ra, không dùng làm camera điện thoại hay laptop
    is_phone = [any(k in n.lower() for k in PHONE_NAME_KEYWORDS) and "desk view" not in n.lower() for n in names]
    others = [i for i, p in enumerate(is_phone) if not p]
    laptop = next(
        (i for i in others if not any(k in names[i].lower() for k in NOT_LAPTOP_KEYWORDS)), others[0] if others else 0
    )
    if True in is_phone:
        return laptop, is_phone.index(True)
    if want_phone:
        print("⚠️ Không thấy camera điện thoại (iPhone/Iriun/DroidCam...): mở app trên điện thoại và trên máy tính rồi chạy lại")
    return laptop, len(names)  # Chỉ số chưa có thiết bị: khung hình báo "đang chờ tín hiệu"


def open_laptop(index):
    return CameraStream(index, f"Cam 1: Laptop (Index {index})", "Kiem tra webcam laptop (quyen Camera cho Terminal)")


def normalize_phone_url(text):
    """'192.168.1.5' / '192.168.1.5:8080' / URL đầy đủ -> URL luồng video của IP Webcam (mặc định cổng 8080, đường dẫn /video); rỗng -> ''."""
    text = text.strip()
    if not text:
        return ""
    if "://" not in text:
        text = "http://" + text
    u = urlparse(text)
    host = u.netloc if ":" in u.netloc else f"{u.netloc}:8080"
    return f"{u.scheme}://{host}{u.path if u.path not in ('', '/') else '/video'}"


def open_phone(source):
    """source: URL luồng IP Webcam (str) hoặc chỉ số webcam Iriun/DroidCam (int)."""
    if isinstance(source, str):
        return CameraStream(
            source, "Cam 2: Dien Thoai (IP Webcam)", "Mo IP Webcam > Start server, cung Wi-Fi voi PC", PHONE_ROTATE
        )
    return CameraStream(
        source, f"Cam 2: Dien Thoai (Index {source})", "iPhone: dat gan Mac (Continuity Camera); Android: mo Iriun 2 ben", PHONE_ROTATE
    )


# Kích thước thực tế của quyển vở khổ A4 210x297mm đặt ngang (cm): Ngang W_CM = 29.7 x Dọc H_CM = 21.0
NOTEBOOK_W_CM = 29.7
NOTEBOOK_H_CM = 21.0

# Cấu hình bộ từ điển ArUco 4x4 (ID 0: Trên-Trái, ID 1: Trên-Phải, ID 2: Dưới-Phải, ID 3: Dưới-Trái)
ARUCO_DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
ARUCO_PARAMS = cv2.aruco.DetectorParameters()
ARUCO_DETECTOR = cv2.aruco.ArucoDetector(ARUCO_DICT, ARUCO_PARAMS)


def _make_aruco_tile(marker_id, size=120, border=16):
    """Tạo ảnh mã ArUco kèm viền trắng (Quiet Zone) để ArucoDetector nhận diện chính xác."""
    inner = cv2.aruco.generateImageMarker(ARUCO_DICT, marker_id, size)
    full = np.full((size + 2 * border, size + 2 * border), 255, dtype=np.uint8)
    full[border:border + size, border:border + size] = inner
    return cv2.cvtColor(full, cv2.COLOR_GRAY2BGR)


ARUCO_TILES = {i: _make_aruco_tile(i) for i in range(4)}

# Tọa độ thực (cm) của 4 góc quyển vở tương ứng với tâm/góc chuẩn của 4 mã ArUco (ID 0, 1, 2, 3)
CORNER_COORDS_CM = {
    0: (0.0, 0.0),
    1: (NOTEBOOK_W_CM, 0.0),
    2: (NOTEBOOK_W_CM, NOTEBOOK_H_CM),
    3: (0.0, NOTEBOOK_H_CM),
}


def order_quad_points(pts):
    """Sắp xếp 4 điểm góc theo thứ tự chuẩn: ID 0 (TL), ID 1 (TR), ID 2 (BR), ID 3 (BL)."""
    pts = np.asarray(pts, dtype=np.float32).reshape(4, 2)
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).reshape(-1)
    return np.float32([
        pts[np.argmin(s)],  # TL (ID 0)
        pts[np.argmin(d)],  # TR (ID 1)
        pts[np.argmax(s)],  # BR (ID 2)
        pts[np.argmax(d)],  # BL (ID 3)
    ])


def detect_notebook_corners_topdown(frame):
    """Tìm 4 góc quyển vở từ góc nhìn trên xuống (Điện thoại) qua phân đoạn màu LAB."""
    h, w = frame.shape[:2]
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    mask = cv2.inRange(lab, (130, 0, 125), (255, 134, 255))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25)))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11)))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in sorted(cnts, key=cv2.contourArea, reverse=True):
        if cv2.contourArea(c) > 0.12 * (w * h):
            rect = cv2.minAreaRect(c)
            return order_quad_points(cv2.boxPoints(rect))
    # Fallback theo vị trí quyển vở chuẩn trên khung 1920x1080
    sx, sy = w / 1920.0, h / 1080.0
    return np.float32([[505 * sx, 118 * sy], [1380 * sx, 70 * sy], [1405 * sx, 678 * sy], [535 * sx, 718 * sy]])


def sheet_quad_from_markers(frame):
    """
    4 góc tờ A4 (TL, TR, BR, BL, đơn vị px) suy ra từ các mã ArUco THẬT ID 0-3 (2.8 cm, cách mép 0.25 cm, xem generate_aruco_a4.py).
    None nếu thấy dưới 3 mã: không đủ để tính chính xác, lúc đó dùng cách ước lượng theo màu.
    """
    corners, ids, _ = ARUCO_DETECTOR.detectMarkers(frame)
    if ids is None:
        return None
    W, H, s, m = NOTEBOOK_W_CM, NOTEBOOK_H_CM, 2.8, 0.25
    boxes_cm = {
        0: [[m, m], [m + s, m], [m + s, m + s], [m, m + s]],
        1: [[W - m - s, m], [W - m, m], [W - m, m + s], [W - m - s, m + s]],
        2: [[W - m - s, H - m - s], [W - m, H - m - s], [W - m, H - m], [W - m - s, H - m]],
        3: [[m, H - m - s], [m + s, H - m - s], [m + s, H - m], [m, H - m]],
    }
    img_pts, cm_pts, seen = [], [], set()
    for c, mid in zip(corners, ids.flatten()):
        if int(mid) in boxes_cm:
            seen.add(int(mid))
            img_pts.extend(c[0])
            cm_pts.extend(boxes_cm[int(mid)])
    if len(seen) < 3:
        return None
    H_cm2px, _ = cv2.findHomography(np.float32(cm_pts), np.float32(img_pts), 0)
    if H_cm2px is None:
        return None
    return cv2.perspectiveTransform(np.float32([[[0, 0], [W, 0], [W, H], [0, H]]]), H_cm2px)[0]


def detect_notebook_corners_side(frame):
    """
    Tìm 4 góc mặt quyển vở từ góc nhìn ngang (Webcam laptop).
    LƯU Ý: 4 tọa độ pixel bên dưới đo theo cảnh quay cũ, chỉ dùng khi KHÔNG thấy mã ArUco thật; đặt lại laptop thì đo lại.
    Ánh xạ đúng 4 góc vật lý trùng với Cam trên xuống:
      ID 0: Góc Trước-Phải (0, 0)
      ID 1: Góc Trước-Trái (W, 0)
      ID 2: Góc Sau-Trái   (W, H)
      ID 3: Góc Sau-Phải   (0, H)
    """
    h, w = frame.shape[:2]
    sx, sy = w / 1440.0, h / 1080.0
    return np.float32([
        [1330 * sx, 595 * sy],  # ID 0 (0, 0)
        [95 * sx, 600 * sy],    # ID 1 (W, 0)
        [265 * sx, 485 * sy],   # ID 2 (W, H)
        [1065 * sx, 475 * sy],  # ID 3 (0, H)
    ])


def overlay_virtual_aruco_topdown(frame, quad_pts):
    """Gán 4 mã ArUco (ID 0, 1, 2, 3) phẳng theo phối cảnh vào 4 góc quyển vở trên ảnh Top-Down."""
    out = frame.copy()
    H_to_img = cv2.getPerspectiveTransform(
        np.float32([[0, 0], [NOTEBOOK_W_CM, 0], [NOTEBOOK_W_CM, NOTEBOOK_H_CM], [0, NOTEBOOK_H_CM]]),
        quad_pts,
    )
    # Mỗi mã ArUco có kích thước 2.8 x 2.8 cm đặt sát 4 góc quyển vở
    s = 2.8
    m = 0.25
    W, H = NOTEBOOK_W_CM, NOTEBOOK_H_CM
    boxes_cm = {
        0: [[m, m], [m + s, m], [m + s, m + s], [m, m + s]],
        1: [[W - m - s, m], [W - m, m], [W - m, m + s], [W - m - s, m + s]],
        2: [[W - m - s, H - m - s], [W - m, H - m - s], [W - m, H - m], [W - m - s, H - m]],
        3: [[m, H - m - s], [m + s, H - m - s], [m + s, H - m], [m, H - m]],
    }
    for mid, cm_box in boxes_cm.items():
        tile = ARUCO_TILES[mid]
        th, tw = tile.shape[:2]
        src = np.float32([[0, 0], [tw, 0], [tw, th], [0, th]])
        dst = cv2.perspectiveTransform(np.float32([cm_box]), H_to_img)[0]
        M = cv2.getPerspectiveTransform(src, dst)
        warped = cv2.warpPerspective(tile, M, (out.shape[1], out.shape[0]))
        poly_mask = np.zeros((out.shape[0], out.shape[1]), dtype=np.uint8)
        cv2.fillConvexPoly(poly_mask, np.int32(dst), 255)
        out[poly_mask > 0] = warped[poly_mask > 0]
    return out


def overlay_virtual_aruco_side(frame, corner_pts):
    """Gán 4 mã ArUco (ID 0, 1, 2, 3) tại 4 góc quyển vở trên góc nhìn ngang để ArucoDetector giải mã."""
    out = frame.copy()
    h, w = out.shape[:2]
    for mid in range(4):
        cx, cy = int(round(corner_pts[mid][0])), int(round(corner_pts[mid][1]))
        sz = 72 if mid in (0, 1) else 60
        tile = _make_aruco_tile(mid, size=sz, border=10)
        th, tw = tile.shape[:2]
        x1 = max(0, min(w - tw, cx - tw // 2))
        y1 = max(0, min(h - th, cy - th // 2))
        out[y1:y1 + th, x1:x1 + tw] = tile
    return out


def draw_dashed_line(img, pt1, pt2, color, thickness=2, gap=12):
    """Vẽ đường gióng nét đứt từ vật thể tới trục tọa độ X, Y."""
    p1 = np.array(pt1, dtype=np.float32)
    p2 = np.array(pt2, dtype=np.float32)
    dist = np.linalg.norm(p2 - p1)
    if dist < 1:
        return
    vec = (p2 - p1) / dist
    for start in np.arange(0, dist, gap * 2):
        end = min(start + gap, dist)
        a = tuple(np.int32(p1 + vec * start))
        b = tuple(np.int32(p1 + vec * end))
        cv2.line(img, a, b, color, thickness, cv2.LINE_AA)


class ArucoYoloTracker:
    """
    Kết hợp ArUco (4 góc quyển vở) + Homography + YOLO:
    - Chạy YOLO trên luồng nền (không làm giảm FPS hiển thị camera).
    - Tự động gán & phát hiện 4 mã ArUco (ID 0, 1, 2, 3) ở 4 góc quyển vở.
    - Nội suy tọa độ thực (X, Y) (cm) và kích thước của vật thể đặt trên vở.
    """

    def __init__(self, assist=None):
        self.assist = assist
        self.model = None
        self.device = "cpu"
        self.lock = threading.Lock()
        self.latest_raw = {"topdown": None, "side": None}
        self.detections = {"topdown": [], "side": []}
        self.notebook_quad_topdown = None
        self.running = True
        self.worker = threading.Thread(target=self._yolo_loop, daemon=True)
        self.worker.start()

    def _init_model(self):
        if self.model is not None:
            return
        try:
            import torch
            from ultralytics import YOLO
            model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yolo11s.pt")
            self.model = YOLO(model_path if os.path.exists(model_path) else "yolo11s.pt")
            # GPU NVIDIA (Windows/Linux) cần bản torch có CUDA; pip mặc định cài bản chỉ chạy CPU
            if torch.cuda.is_available():
                self.device = "cuda:0"
            elif torch.backends.mps.is_available():
                self.device = "mps"
            print(f"🧠 YOLO chạy trên: {self.device}")
        except Exception as e:
            print(f"⚠️ Không tải được YOLO: {e}")

    def update_raw_frame(self, mode, raw_frame):
        if raw_frame is None:
            return
        with self.lock:
            self.latest_raw[mode] = raw_frame

    def _yolo_loop(self):
        self._init_model()
        while self.running:
            with self.lock:
                td_frame = self.latest_raw["topdown"]
                sd_frame = self.latest_raw["side"]
            if self.model is None or (td_frame is None and sd_frame is None):
                time.sleep(0.05)
                continue

            if td_frame is not None:
                # Có mã ArUco thật thì lấy chính tờ A4 làm vùng lọc vật (tay, cáp, mặt bàn ngoài giấy không bị nhận nhầm)
                quad = sheet_quad_from_markers(td_frame)
                if quad is None:
                    quad = detect_notebook_corners_topdown(td_frame)
                dets = self._detect_objects_topdown(td_frame, quad)
                with self.lock:
                    self.notebook_quad_topdown = quad
                    self.detections["topdown"] = dets

            if sd_frame is not None:
                dets_side = self._detect_objects_side(sd_frame)
                with self.lock:
                    self.detections["side"] = dets_side

            time.sleep(0.03)

    def _detect_objects_topdown(self, frame, quad):
        """Chạy YOLO trên vùng quyển vở để phát hiện vật thể nằm trên mặt vở."""
        h, w = frame.shape[:2]
        xs, ys = quad[:, 0], quad[:, 1]
        x1 = max(0, int(np.min(xs)) - 10)
        y1 = max(0, int(np.min(ys)) - 10)
        x2 = min(w, int(np.max(xs)) + 10)
        y2 = min(h, int(np.max(ys)) + 10)
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return []

        nb_area = cv2.contourArea(quad)
        poly = quad.reshape(-1, 1, 2)
        results = self.model(crop, conf=0.12, imgsz=960, device=self.device, verbose=False)[0]
        found = []
        for box in results.boxes:
            bx1, by1, bx2, by2 = box.xyxy[0].tolist()
            fx1, fy1, fx2, fy2 = bx1 + x1, by1 + y1, bx2 + x1, by2 + y1
            bw, bh = fx2 - fx1, fy2 - fy1
            if bw * bh > 0.40 * nb_area or bw * bh < 400:
                continue
            cx, cy = (fx1 + fx2) / 2.0, (fy1 + fy2) / 2.0
            # Kiểm tra tâm vật thể nằm bên trong quyển vở (cách mép ít nhất 15 px)
            if cv2.pointPolygonTest(poly, (cx, cy), True) >= 15:
                cls_name = results.names[int(box.cls[0])]
                conf = float(box.conf[0])
                found.append({
                    "bbox": (fx1, fy1, fx2, fy2),
                    "ref_pt": (cx, cy),
                    "cls": cls_name,
                    "conf": conf,
                })
        return found

    def _detect_objects_side(self, frame):
        """Chạy YOLO trên khung hình góc ngang (Webcam laptop), lọc vật thể nằm trên mặt vở."""
        results = self.model(frame, conf=0.20, imgsz=640, device=self.device, verbose=False)[0]
        # Cam ngang thấy được từ 3 mã ArUco góc thật thì lấy đúng tờ A4 làm vùng lọc; không thì dùng 4 góc đo tay theo cảnh quay cũ
        quad_side = sheet_quad_from_markers(frame)
        if quad_side is None:
            quad_side = detect_notebook_corners_side(frame)
        poly = quad_side.reshape(-1, 1, 2)
        found = []
        for box in results.boxes:
            cls_name = results.names[int(box.cls[0])]
            if cls_name in ("laptop", "tv", "bed", "book", "chair", "dining table"):
                continue
            fx1, fy1, fx2, fy2 = box.xyxy[0].tolist()
            cx = (fx1 + fx2) / 2.0
            # Điểm tiếp xúc chân đế vật thể với mặt vở ở góc nhìn ngang
            cy_base = fy2 - 0.30 * (fy2 - fy1)
            if cv2.pointPolygonTest(poly, (cx, cy_base), True) >= -25:
                found.append({
                    "bbox": (fx1, fy1, fx2, fy2),
                    "ref_pt": (cx, cy_base),
                    "cls": cls_name,
                    "conf": float(box.conf[0]),
                })
        return found

    def process_frame(self, raw_frame, mode="topdown"):
        """
        1. Gán 4 mã ArUco vào 4 góc vở (nếu trên vở chưa dán mã giấy thật).
        2. Dùng cv2.aruco.ArucoDetector phát hiện 4 mã ArUco (ID 0, 1, 2, 3).
        3. Tính Homography từ 4 mã ArUco -> Hệ tọa độ thực trên vở (24.0 x 16.5 cm).
        4. Vẽ lưới tọa độ, bounding box YOLO và tọa độ (X, Y) của vật thể trên vở.
        """
        if raw_frame is None:
            return None
        self.update_raw_frame(mode, raw_frame)

        # YOLO chỉ chạy ở luồng nền (_yolo_loop): ở đây chỉ lấy kết quả mới nhất, không gọi model để khung hình không bị chậm
        with self.lock:
            dets = list(self.detections.get(mode, []))
            cached_quad = self.notebook_quad_topdown

        # Ưu tiên phát hiện 4 mã ArUco THẬT in trên tờ giấy A4 (m=0.25cm, s=2.8cm, xem generate_aruco_a4.py)
        real_corners, real_ids, _ = ARUCO_DETECTOR.detectMarkers(raw_frame)
        has_real_aruco = real_ids is not None and len(real_ids) >= 2
        quad = None  # 4 góc vở ước lượng, chỉ cần khi không có mã góc nào để tính Homography

        if has_real_aruco:
            work = raw_frame.copy()
            corners, ids = real_corners, real_ids
        elif mode == "topdown":
            quad = cached_quad if cached_quad is not None else detect_notebook_corners_topdown(raw_frame)
            work = overlay_virtual_aruco_topdown(raw_frame, quad)
            corners, ids, _ = ARUCO_DETECTOR.detectMarkers(work)
        else:
            quad = detect_notebook_corners_side(raw_frame)
            work = overlay_virtual_aruco_side(raw_frame, quad)
            corners, ids, _ = ARUCO_DETECTOR.detectMarkers(work)

        img_pts = []
        cm_pts = []
        W, H = NOTEBOOK_W_CM, NOTEBOOK_H_CM

        if ids is not None and len(ids) > 0:
            cv2.aruco.drawDetectedMarkers(work, corners, ids, (0, 255, 0))
            if has_real_aruco:
                # Tờ giấy A4 in thật: mỗi mã ArUco 2.8x2.8 cm, đặt sát 4 góc (cách mép giấy 0.25 cm)
                s, m = 2.8, 0.25
                marker_cm_boxes = {
                    0: [[m, m], [m + s, m], [m + s, m + s], [m, m + s]],
                    1: [[W - m - s, m], [W - m, m], [W - m, m + s], [W - m - s, m + s]],
                    2: [[W - m - s, H - m - s], [W - m, H - m - s], [W - m, H - m], [W - m - s, H - m]],
                    3: [[m, H - m - s], [m + s, H - m - s], [m + s, H - m], [m, H - m]],
                }
                for c, mid in zip(corners, ids.flatten()):
                    mid = int(mid)
                    if mid in marker_cm_boxes:
                        for pt_px, pt_cm in zip(c[0], marker_cm_boxes[mid]):
                            img_pts.append(pt_px)
                            cm_pts.append(pt_cm)
            elif mode == "topdown":
                # Dùng toàn bộ các góc mã ArUco ảo (4 góc x 4 mã = 16 điểm chuẩn) để tính Homography chính xác
                # Tính cả phần viền trắng Quiet Zone (16px trên tổng 152px của tile)
                s_tile, m_tile = 2.8, 0.25
                pad = s_tile * (16.0 / 152.0)
                s = s_tile * (120.0 / 152.0)
                m = m_tile + pad
                marker_cm_boxes = {
                    0: [[m, m], [m + s, m], [m + s, m + s], [m, m + s]],
                    1: [[W - m - s, m], [W - m, m], [W - m, m + s], [W - m - s, m + s]],
                    2: [[W - m - s, H - m - s], [W - m, H - m - s], [W - m, H - m], [W - m - s, H - m]],
                    3: [[m, H - m - s], [m + s, H - m - s], [m + s, H - m], [m, H - m]],
                }
                for c, mid in zip(corners, ids.flatten()):
                    mid = int(mid)
                    if mid in marker_cm_boxes:
                        for pt_px, pt_cm in zip(c[0], marker_cm_boxes[mid]):
                            img_pts.append(pt_px)
                            cm_pts.append(pt_cm)
            else:
                # Góc nhìn ngang (mã ảo): tâm mỗi mã ArUco đặt tại đúng 4 góc quyển vở
                for c, mid in zip(corners, ids.flatten()):
                    mid = int(mid)
                    if mid in CORNER_COORDS_CM:
                        center_px = c[0].mean(axis=0)
                        img_pts.append(center_px)
                        cm_pts.append(CORNER_COORDS_CM[mid])

            # Vẽ nhãn tọa độ thực tại 4 góc ArUco
            for c, mid in zip(corners, ids.flatten()):
                mid = int(mid)
                if mid in CORNER_COORDS_CM:
                    cx, cy = np.int32(c[0].mean(axis=0))
                    gx, gy = CORNER_COORDS_CM[mid]
                    label = f"ID:{mid} ({gx:g},{gy:g}cm)"
                    ty_lbl = cy - 48 if mid in (0, 1) else cy + 62
                    cv2.putText(work, label, (cx - 75, ty_lbl), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 4, cv2.LINE_AA)
                    cv2.putText(work, label, (cx - 75, ty_lbl), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 255, 255), 2, cv2.LINE_AA)

        if len(img_pts) >= 4:
            H_px2cm, _ = cv2.findHomography(np.float32(img_pts), np.float32(cm_pts), 0)
            H_cm2px = np.linalg.inv(H_px2cm) if H_px2cm is not None else None
        else:
            if quad is None:
                # Thấy mã ArUco thật (VD: chỉ mã vật / đầu kẹp) nhưng không thấy mã góc 0-3 nào: dùng 4 góc vở ước lượng
                if mode == "topdown":
                    quad = cached_quad if cached_quad is not None else detect_notebook_corners_topdown(raw_frame)
                else:
                    quad = detect_notebook_corners_side(raw_frame)
            dst_cm = np.float32([[0, 0], [W, 0], [W, H], [0, H]])
            H_px2cm = cv2.getPerspectiveTransform(quad, dst_cm)
            H_cm2px = cv2.getPerspectiveTransform(dst_cm, quad)

        # Vẽ lưới tọa độ quyển vở và hệ trục Oxy từ Homography
        if H_cm2px is not None:
            nb_border_cm = np.float32([[[0, 0], [W, 0], [W, H], [0, H]]])
            nb_border_px = np.int32(cv2.perspectiveTransform(nb_border_cm, H_cm2px)[0])
            cv2.polylines(work, [nb_border_px], True, (200, 200, 200), 2, cv2.LINE_AA)

            # Lưới chia ô trên mặt vở 29.7 x 21.0 cm (mỗi 5 cm = 50 mm)
            for gx in (5.0, 10.0, 15.0, 20.0, 25.0):
                seg = cv2.perspectiveTransform(np.float32([[[gx, 0], [gx, H]]]), H_cm2px)[0]
                p_top, p_bot = tuple(np.int32(seg[0])), tuple(np.int32(seg[1]))
                cv2.line(work, p_top, p_bot, (150, 150, 150), 1, cv2.LINE_AA)
                if mode == "topdown":
                    cv2.circle(work, p_top, 4, (0, 140, 255), -1)
                    cv2.putText(work, f"{int(gx)}cm", (p_top[0] - 18, p_top[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 0, 0), 3, cv2.LINE_AA)
                    cv2.putText(work, f"{int(gx)}cm", (p_top[0] - 18, p_top[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (100, 220, 255), 1, cv2.LINE_AA)

            for gy in (5.0, 10.0, 15.0):
                seg = cv2.perspectiveTransform(np.float32([[[0, gy], [W, gy]]]), H_cm2px)[0]
                p_left, p_right = tuple(np.int32(seg[0])), tuple(np.int32(seg[1]))
                cv2.line(work, p_left, p_right, (150, 150, 150), 1, cv2.LINE_AA)
                if mode == "topdown":
                    cv2.circle(work, p_left, 4, (255, 220, 0), -1)
                    cv2.putText(work, f"{int(gy)}cm", (p_left[0] - 52, p_left[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 0, 0), 3, cv2.LINE_AA)
                    cv2.putText(work, f"{int(gy)}cm", (p_left[0] - 52, p_left[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 230, 100), 1, cv2.LINE_AA)

            # Tô đậm Trục OX (Đỏ Cam: ID 0 -> ID 1) và Trục OY (Xanh Cyan: ID 0 -> ID 3)
            p_o = tuple(nb_border_px[0])
            p_x_end = tuple(nb_border_px[1])
            p_y_end = tuple(nb_border_px[3])
            cv2.arrowedLine(work, p_o, p_x_end, (0, 90, 255), 4, cv2.LINE_AA, tipLength=0.025)
            cv2.arrowedLine(work, p_o, p_y_end, (255, 200, 0), 4, cv2.LINE_AA, tipLength=0.035)
            cv2.circle(work, p_o, 8, (0, 255, 255), -1)
            cv2.circle(work, p_o, 10, (0, 0, 0), 2)

            if mode == "topdown":
                mid_x_axis = np.int32((nb_border_px[0] + nb_border_px[1]) / 2)
                cv2.putText(work, "TRUC X (Ngang: 0 -> 29.7cm / 297mm)", (mid_x_axis[0] - 165, mid_x_axis[1] - 28), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 4, cv2.LINE_AA)
                cv2.putText(work, "TRUC X (Ngang: 0 -> 29.7cm / 297mm)", (mid_x_axis[0] - 165, mid_x_axis[1] - 28), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 140, 255), 2, cv2.LINE_AA)
                cv2.putText(work, "TRUC Y (0->21cm)", (p_y_end[0] - 165, (p_o[1] + p_y_end[1]) // 2 - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 0, 0), 4, cv2.LINE_AA)
                cv2.putText(work, "TRUC Y (0->21cm)", (p_y_end[0] - 165, (p_o[1] + p_y_end[1]) // 2 - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (255, 220, 0), 2, cv2.LINE_AA)

        # Tính tọa độ (X, Y) thực tế và TÔ ĐẬM 2 ĐƯỜNG ĐO X, Y cho từng vật thể YOLO phát hiện
        if H_px2cm is not None and H_cm2px is not None:
            for det in dets:
                x1, y1, x2, y2 = det["bbox"]
                rx, ry = det["ref_pt"]
                pt_cm = cv2.perspectiveTransform(np.float32([[[rx, ry]]]), H_px2cm)[0][0]
                obj_x, obj_y = float(pt_cm[0]), float(pt_cm[1])
                dx_center = obj_x - W / 2.0
                dy_center = obj_y - H / 2.0

                # Ước lượng kích thước vật thể trên mặt vở (cm)
                corners_box = np.float32([[[x1, ry], [x2, ry], [rx, y1], [rx, y2]]])
                box_cm = cv2.perspectiveTransform(corners_box, H_px2cm)[0]
                obj_w_cm = np.linalg.norm(box_cm[1] - box_cm[0])
                obj_h_cm = np.linalg.norm(box_cm[3] - box_cm[2])

                # Điểm chiếu trên Trục X (tại y=0) và trên Trục Y (tại x=0)
                pt_on_x_axis = cv2.perspectiveTransform(np.float32([[[obj_x, 0.0]]]), H_cm2px)[0][0]
                pt_on_y_axis = cv2.perspectiveTransform(np.float32([[[0.0, obj_y]]]), H_cm2px)[0][0]
                p_center = (int(round(rx)), int(round(ry)))
                p_x_proj = tuple(np.int32(pt_on_x_axis))
                p_y_proj = tuple(np.int32(pt_on_y_axis))

                # Tô vùng chữ nhật tọa độ (0,0) -> (X,0) -> (X,Y) -> (0,Y) mờ để dễ nhìn hình chiếu
                rect_cm = np.float32([[[0, 0], [obj_x, 0], [obj_x, obj_y], [0, obj_y]]])
                rect_px = np.int32(cv2.perspectiveTransform(rect_cm, H_cm2px)[0])
                overlay_rect = work.copy()
                cv2.fillConvexPoly(overlay_rect, rect_px, (0, 200, 255))
                cv2.addWeighted(overlay_rect, 0.14, work, 0.86, 0, work)

                # 1. ĐƯỜNG XÁC ĐỊNH X (Màu VÀNG ĐẬM): Đo khoảng cách NGANG từ Mép Trái (Trục Y, x=0) đến Tâm vật thể (x=X)
                cv2.arrowedLine(work, p_y_proj, p_center, (0, 255, 255), 4, cv2.LINE_AA, tipLength=0.05)
                cv2.arrowedLine(work, p_center, p_y_proj, (0, 255, 255), 4, cv2.LINE_AA, tipLength=0.05)
                cv2.circle(work, p_y_proj, 8, (0, 255, 255), -1)
                cv2.circle(work, p_y_proj, 10, (0, 0, 0), 2)

                # 2. ĐƯỜNG XÁC ĐỊNH Y (Màu HỒNG MAGENTA ĐẬM): Đo khoảng cách DỌC từ Mép Trên (Trục X, y=0) xuống Tâm vật thể (y=Y)
                cv2.arrowedLine(work, p_x_proj, p_center, (255, 0, 255), 4, cv2.LINE_AA, tipLength=0.05)
                cv2.arrowedLine(work, p_center, p_x_proj, (255, 0, 255), 4, cv2.LINE_AA, tipLength=0.05)
                cv2.circle(work, p_x_proj, 8, (255, 0, 255), -1)
                cv2.circle(work, p_x_proj, 10, (0, 0, 0), 2)

                # Vẽ Bounding Box YOLO & Tâm vật thể P(X, Y)
                cv2.rectangle(work, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 128), 3)
                cv2.circle(work, p_center, 8, (0, 0, 255), -1)
                cv2.circle(work, p_center, 12, (255, 255, 255), 3)

                # Ghi nhãn trực tiếp lên ĐƯỜNG X (Màu Vàng) và ĐƯỜNG Y (Màu Hồng)
                mid_x_line = ((p_y_proj[0] + p_center[0]) // 2, (p_y_proj[1] + p_center[1]) // 2)
                mid_y_line = ((p_x_proj[0] + p_center[0]) // 2, (p_x_proj[1] + p_center[1]) // 2)

                lbl_x = f"X={obj_x:.1f}cm ({obj_x*10:.0f}mm)"
                cv2.rectangle(work, (mid_x_line[0] - 115, mid_x_line[1] - 34), (mid_x_line[0] + 125, mid_x_line[1] - 4), (15, 15, 15), -1)
                cv2.rectangle(work, (mid_x_line[0] - 115, mid_x_line[1] - 34), (mid_x_line[0] + 125, mid_x_line[1] - 4), (0, 255, 255), 2)
                cv2.putText(work, lbl_x, (mid_x_line[0] - 108, mid_x_line[1] - 11), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2, cv2.LINE_AA)

                lbl_y = f"Y={obj_y:.1f}cm ({obj_y*10:.0f}mm)"
                cv2.rectangle(work, (mid_y_line[0] + 14, mid_y_line[1] - 18), (mid_y_line[0] + 245, mid_y_line[1] + 14), (15, 15, 15), -1)
                cv2.rectangle(work, (mid_y_line[0] + 14, mid_y_line[1] - 18), (mid_y_line[0] + 245, mid_y_line[1] + 14), (255, 0, 255), 2)
                cv2.putText(work, lbl_y, (mid_y_line[0] + 22, mid_y_line[1] + 6), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 100, 255), 2, cv2.LINE_AA)

                # Đặt bảng tổng hợp ở PHÍA DƯỚI vật thể để KHÔNG che khuất đường đo X và Y
                coord_text = f"Tam P: X={obj_x:.1f}cm ({obj_x*10:.0f}mm), Y={obj_y:.1f}cm ({obj_y*10:.0f}mm)"
                sub_text = (
                    f"Kho A4 (297x210mm) | Tam vo: dX={dx_center:+.1f}cm, dY={dy_center:+.1f}cm | R={obj_w_cm:.1f}cm"
                    if mode == "side"
                    else f"Kho A4 (297x210mm) | So voi tam vo: ({dx_center:+.1f}, {dy_center:+.1f})cm | KT: {obj_w_cm:.1f}x{obj_h_cm:.1f}cm"
                )
                tx = max(20, min(work.shape[1] - 730, int(rx) - 270))
                ty = min(work.shape[0] - 55, int(y2) + 42)
                cv2.rectangle(work, (tx - 10, ty - 32), (tx + 725, ty + 36), (20, 20, 20), -1)
                cv2.rectangle(work, (tx - 10, ty - 32), (tx + 725, ty + 36), (0, 255, 128), 2)
                cv2.putText(work, coord_text, (tx, ty - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (0, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(work, sub_text, (tx, ty + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 255, 220), 2, cv2.LINE_AA)

        # Cập nhật dữ liệu cho Bộ Gợi ý Gắp 4 Servo (IK 4-DOF + Xác nhận gắp S1/S2)
        if self.assist is not None:
            obs_corners = real_corners if (real_ids is not None and len(real_ids) > 0) else corners
            obs_ids = real_ids if (real_ids is not None and len(real_ids) > 0) else ids
            if mode == "topdown":
                self.assist.update_topdown_observations(work, obs_corners, obs_ids, dets, H_px2cm, H_cm2px)
            else:
                self.assist.update_side_observations(work, real_corners, real_ids, dets)

        return work


def render_camera_panel(cam, tracker, mode):
    """
    Lấy frame gốc từ camera, xử lý ArUco + YOLO rồi đưa về khung chuẩn 640x480.
    Trả về (khung 640x480 cho cửa sổ ghép, khung đã vẽ chưa thu nhỏ cho cửa sổ hướng dẫn).
    """
    raw = cam.get_raw_frame()
    if raw is None:
        waiting = cam.get_frame()
        return waiting, waiting
    annotated = tracker.process_frame(raw, mode=mode)
    panel = letterbox(annotated)
    cv2.putText(panel, cam.name, (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2, cv2.LINE_AA)
    return panel, annotated


def main():
    # BƯỚC 1: Mở đồng thời 2 Camera + Bộ Gợi ý Gắp 4 Servo (Arduino WASD/IK/JL)
    phone_url = normalize_phone_url(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PHONE_URL", PHONE_URL_DEFAULT))
    laptop_index, phone_index = find_camera_indices(want_phone=not phone_url)
    cam_laptop = open_laptop(laptop_index)
    cam_phone = open_phone(phone_url or phone_index)
    if phone_url:
        print(f"📱 Điện thoại: IP Webcam tại {phone_url}")
    assist = GraspAssist4DOF()
    tracker = ArucoYoloTracker(assist=assist)
    aruco_enabled = True
    guide_enabled = True        # Cửa sổ HƯỚNG DẪN GẮP (2 cam + bảng thao tác to), phím G để ẩn/hiện
    guide_placed = False        # Đã dời cửa sổ hướng dẫn ra vị trí mặc định chưa
    guide_seen_visible = False  # Đã thấy cửa sổ hiện ra chưa (để biết khi nào người dùng bấm nút đóng cửa sổ)

    print("✅ Đang mở màn hình ghép 2 góc nhìn + Gợi ý Gắp 4 Servo (WASD / IK / JL)...")
    print("🖥️ Đồng thời bật cửa sổ HƯỚNG DẪN GẮP: 2 camera ở trên, bên dưới là việc cần làm (phím nào, bấm mấy lần) và kết quả gắp")
    print("💡 Phím tắt trên cửa sổ video:")
    print("   - Các phím 'W/A/S/D', 'I/K', 'J/L', 'H' (Home): Điều khiển trực tiếp 4 Servo qua USB (hoặc tay cầm Bluetooth)")
    print("   - Phím 'SPACE' (hoặc 'N'): Chuyển sang bước tiếp theo trong quy trình 5 bước gắp")
    print("   - Phím 'TAB' (hoặc 'V'): Đổi vật mục tiêu cần gắp")
    print("   - Phím 'P': Bật/Tắt tự động gửi từng bước phím gợi ý (Auto-Step)")
    print("   - Phím 'R': Reset quy trình gắp về Bước 1")
    print("   - Phím 'M': Bật/Tắt lớp phủ ArUco 4 góc + YOLO tính tọa độ (X, Y)")
    print("   - Phím 'G': Ẩn/Hiện cửa sổ HƯỚNG DẪN GẮP (phím bấm ở cửa sổ nào cũng được)")
    print("   - Phím 'C': Chụp ảnh gốc của cả 2 camera, lưu vào thư mục captures/")
    print("   - Phím 'X': Đổi chỗ 2 camera (chỉ khi điện thoại dùng Iriun: bên trái hiện hình điện thoại, bên phải hiện laptop)")
    print("   - Nhấn phím '0' đến '3': Đổi chỉ số camera ĐIỆN THOẠI (Iriun) hoặc chỉ số WEBCAM LAPTOP (khi điện thoại dùng IP Webcam)")
    print("   - Nhấn phím 'Q': Thoát chương trình")
    print("ℹ️ Camera nào chưa lên hình sẽ tự thử mở lại sau vài giây (VD: sau khi bạn mở app Iriun trên điện thoại)")

    # BƯỚC 2: Vòng lặp lấy hình từ 2 Camera và ghép ngang vào 1 cửa sổ kèm thanh Gợi ý Gắp 4 Servo
    while True:
        # Trái = webcam laptop nhìn ngang ("side"), phải = điện thoại nhìn từ trên xuống ("topdown")
        if aruco_enabled:
            frame_left, view_left = render_camera_panel(cam_laptop, tracker, mode="side")
            frame_right, view_right = render_camera_panel(cam_phone, tracker, mode="topdown")
        else:
            frame_left = view_left = cam_laptop.get_frame()
            frame_right = view_right = cam_phone.get_frame()

        # BƯỚC 3: Ghép ngang 2 ma trận ảnh (Trái + Phải) (1280x480) + Thanh Gợi ý Gắp ở dưới (1280x175)
        combined_screen = cv2.hconcat([frame_left, frame_right])
        cv2.line(combined_screen, (VIEW_WIDTH, 0), (VIEW_WIDTH, VIEW_HEIGHT), (255, 255, 255), 2)

        # Tính gợi ý 1 lần mỗi khung hình rồi dùng chung cho thanh HUD và cửa sổ hướng dẫn (Auto-Step chỉ gửi phím 1 lần)
        info = assist.compute_current_suggestion()
        hud_bar = assist.render_hud_bar(width=combined_screen.shape[1], info=info)
        full_screen = cv2.vconcat([combined_screen, hud_bar])

        cv2.imshow("Dual Camera View: Laptop (Trai) | Dien Thoai (Phai)", full_screen)

        # Cửa sổ HƯỚNG DẪN GẮP: 2 camera ở trên + bảng "việc cần làm / kết quả gắp" ở dưới
        if guide_enabled:
            cv2.imshow(GUIDE_WINDOW, build_guide_screen(view_left, view_right, info))
            if not guide_placed:
                cv2.moveWindow(GUIDE_WINDOW, 60, 60)  # lệch một chút để vẫn thấy mép cửa sổ ghép nằm phía sau
                guide_placed = True
            try:
                guide_visible = cv2.getWindowProperty(GUIDE_WINDOW, cv2.WND_PROP_VISIBLE)
            except cv2.error:
                guide_visible = 0.0
            if guide_visible >= 1:
                guide_seen_visible = True
            elif guide_seen_visible:
                # Cửa sổ từng hiện nhưng giờ không còn: người dùng đã bấm nút đóng, đừng tự mở lại
                guide_enabled = guide_seen_visible = False
                print("🖥️ Đã đóng cửa sổ HƯỚNG DẪN GẮP (bấm 'G' để mở lại)")

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), ord("Q")):
            break
        elif assist.handle_key(key):
            pass
        elif key in (ord("m"), ord("M")):
            aruco_enabled = not aruco_enabled
            print(f"🎯 Chế độ ArUco + YOLO: {'BẬT' if aruco_enabled else 'TẮT'}")
        elif key in (ord("g"), ord("G")):
            guide_enabled = not guide_enabled
            if guide_enabled:
                guide_placed = guide_seen_visible = False
            else:
                try:
                    cv2.destroyWindow(GUIDE_WINDOW)
                except cv2.error:
                    pass
            print(f"🖥️ Cửa sổ HƯỚNG DẪN GẮP: {'BẬT' if guide_enabled else 'TẮT'}")
        elif key in (ord("c"), ord("C")):
            save_snapshots([("cam1_laptop", cam_laptop), ("cam2_phone", cam_phone)])
        elif key in (ord("x"), ord("X")):
            if isinstance(cam_phone.source, str):
                print("⚠️ Điện thoại đang dùng IP Webcam (URL) nên không đổi chỗ được; webcam laptop sai thì bấm '0'-'3' để chọn lại chỉ số")
            else:
                laptop_index, phone_index = cam_phone.source, cam_laptop.source
                print(f"🔄 Đổi chỗ 2 camera: laptop -> Index {laptop_index}, điện thoại -> Index {phone_index}")
                cam_laptop.release()
                cam_phone.release()
                cam_laptop, cam_phone = open_laptop(laptop_index), open_phone(phone_index)
        elif key in (ord("0"), ord("1"), ord("2"), ord("3")):
            new_index = int(chr(key))
            if isinstance(cam_phone.source, str):
                # Điện thoại là IP Webcam (không có chỉ số): phím số chọn chỉ số webcam laptop
                if new_index != cam_laptop.source:
                    print(f"🔄 Đang chuyển webcam laptop (bên trái) sang Index {new_index}...")
                    cam_laptop.release()
                    cam_laptop = open_laptop(new_index)
            elif new_index == cam_laptop.source:
                print(f"⚠️ Index {new_index} đang là webcam laptop, bấm 'X' nếu muốn đổi chỗ 2 camera")
            elif new_index != cam_phone.source:
                print(f"🔄 Đang chuyển Camera điện thoại (bên phải) sang Index {new_index}...")
                cam_phone.release()
                cam_phone = open_phone(new_index)

    # BƯỚC 4: Giải phóng cả 2 Camera, cổng Serial và đóng cửa sổ
    tracker.running = False
    assist.release()
    cam_laptop.release()
    cam_phone.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
