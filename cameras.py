#!/usr/bin/env python3
"""
Tìm và mở camera cho hệ thống 2 góc nhìn:
  - Cam TREN  (nhìn từ trên xuống): OBSBOT Meet SE treo phía trên tờ A4.
  - Cam NGANG (nhìn ngang): camera MacBook (mặc định) hoặc điện thoại qua adb + IP Webcam.

Chỉ số camera của OpenCV trên macOS: OpenCV gọi +[AVCaptureDevice devicesWithMediaType:] rồi SẮP XẾP THEO uniqueID
(trong mã nhị phân cv2 có sortedArrayUsingComparator + uniqueID; đo thực tế khớp 100% qua nhiều lần chạy), nên chỉ số ổn định.
Còn chính danh sách AVFoundation và system_profiler thì xếp camera "dùng gần nhất" lên đầu nên đổi liên tục, có lúc MacBook
đứng trước OBSBOT, có lúc ngược lại. Vì vậy chỉ số luôn được suy ra từ TÊN + uniqueID theo đúng cách OpenCV sắp, không cố định
số cũng không tin thứ tự thô của hệ điều hành.
"""

import json
import os
import shutil
import subprocess
import threading
import time

import cv2
import numpy as np

# Kích thước hiển thị chuẩn cho mỗi góc nhìn (Rộng x Cao)
VIEW_WIDTH = 640
VIEW_HEIGHT = 480

# Camera quá số giây này không ra hình (vừa cấp quyền Camera, vừa cắm lại cáp...) thì tự mở lại
RETRY_SECONDS = 4

# Điện thoại chạy IP Webcam, bắc cầu cổng 8080 qua cáp USB bằng adb
PHONE_URL = "http://127.0.0.1:8080/video"
PHONE_ROTATE = cv2.ROTATE_180  # Điện thoại đang đặt ngược nên xoay hình 180 độ (đổi bằng --rotate-side)

# Từ khóa nhận diện camera theo tên (chữ thường)
TOP_KEYWORDS = ("obsbot",)
BUILTIN_KEYWORDS = ("macbook", "facetime", "built-in", "imac")
VIRTUAL_KEYWORDS = ("virtual", "desk view")  # Camera ảo (OBS Virtual Camera, Desk View), không phải thiết bị thật

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp")
ROTATIONS = {
    0: None,
    90: cv2.ROTATE_90_CLOCKWISE,
    180: cv2.ROTATE_180,
    270: cv2.ROTATE_90_COUNTERCLOCKWISE,
}


def letterbox(frame, width=VIEW_WIDTH, height=VIEW_HEIGHT):
    """Thu phóng giữ nguyên tỉ lệ rồi chèn viền đen cho vừa khung chuẩn (cam 16:9 không bị ép méo về 4:3)."""
    h, w = frame.shape[:2]
    scale = min(width / w, height / h)
    new_w, new_h = round(w * scale), round(h * scale)
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    x, y = (width - new_w) // 2, (height - new_h) // 2
    canvas[y:y + new_h, x:x + new_w] = cv2.resize(frame, (new_w, new_h))
    return canvas


def letterbox_inverse(x, y, frame_shape, width=VIEW_WIDTH, height=VIEW_HEIGHT):
    """Đổi điểm (x, y) trên khung đã letterbox về tọa độ pixel của frame gốc, None nếu điểm rơi vào viền đen."""
    h, w = frame_shape[:2]
    scale = min(width / w, height / h)
    new_w, new_h = round(w * scale), round(h * scale)
    ox, oy = (width - new_w) // 2, (height - new_h) // 2
    fx, fy = (x - ox) / scale, (y - oy) / scale
    if 0 <= fx < w and 0 <= fy < h:
        return fx, fy
    return None


# ==============================================================================
# 1. Danh sách camera (đúng thứ tự chỉ số của OpenCV) và chọn theo tên
# ==============================================================================
def sort_like_opencv(devices):
    """Sắp [(tên, uniqueID), ...] theo uniqueID: đúng thứ tự OpenCV dùng để đánh chỉ số camera trên macOS. Trả về danh sách tên."""
    return [name for name, _ in sorted(devices, key=lambda device: device[1])]


def list_camera_names():
    """
    Tên các camera theo ĐÚNG thứ tự chỉ số của cv2.VideoCapture(index) trên macOS (xem đầu tệp: sắp theo uniqueID).
    Dùng PyObjC (AVFoundation); không có thì dùng system_profiler (cũng có uniqueID nên sắp được y hệt).
    Trả về (danh sách tên, nguồn: 'avfoundation' | 'system_profiler' | 'none').
    """
    try:
        import AVFoundation

        devices = AVFoundation.AVCaptureDevice.devicesWithMediaType_(AVFoundation.AVMediaTypeVideo)
        return sort_like_opencv([(str(d.localizedName()), str(d.uniqueID())) for d in devices]), "avfoundation"
    except Exception:  # Không phải macOS, chưa cài PyObjC hoặc AVFoundation lỗi
        pass
    try:
        out = subprocess.run(
            ["system_profiler", "SPCameraDataType", "-json"], capture_output=True, text=True, timeout=15
        ).stdout
        cams = json.loads(out)["SPCameraDataType"]
        return sort_like_opencv([(cam["_name"], cam.get("spcamera_unique-id", "")) for cam in cams]), "system_profiler"
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError):
        return [], "none"


def pick_camera_index(names, keywords, exclude=()):
    """Chỉ số camera đầu tiên có tên chứa một trong keywords (không phân biệt hoa thường), bỏ camera ảo và exclude."""
    for index, name in enumerate(names):
        low = name.lower()
        if any(k in low for k in VIRTUAL_KEYWORDS) or any(k in low for k in exclude):
            continue
        if any(k in low for k in keywords):
            return index
    return None


# ==============================================================================
# 2. Điện thoại Android qua adb
# ==============================================================================
def find_adb():
    candidates = [shutil.which("adb")]
    for env in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        if os.environ.get(env):
            candidates.append(os.path.join(os.environ[env], "platform-tools", "adb"))
    candidates.append(os.path.expanduser("~/Library/Android/sdk/platform-tools/adb"))
    return next((p for p in candidates if p and os.path.exists(p)), None)


def phone_ready():
    """True nếu có điện thoại Android đã bấm Allow gỡ lỗi USB (adb devices báo 'device', không phải 'unauthorized')."""
    adb = find_adb()
    if adb is None:
        return False
    try:
        out = subprocess.run([adb, "devices"], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.TimeoutExpired):
        return False
    return any(line.split("\t")[-1].strip() == "device" for line in out.splitlines()[1:] if "\t" in line)


def adb_forward(port=8080):
    """Bắc cầu cổng 8080 của điện thoại qua cáp USB (phải làm lại mỗi khi rút cáp cắm lại)."""
    adb = find_adb()
    if adb is None:
        return
    try:
        subprocess.run([adb, "forward", f"tcp:{port}", f"tcp:{port}"], capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        pass


# ==============================================================================
# 3. Mô tả nguồn camera
# ==============================================================================
class CameraSpec:
    """
    Cách tìm một camera. kind:
      name  - theo tên trong danh sách AVFoundation (chỉ số tìm lại mỗi lần mở vì macOS đổi thứ tự)
      index - chỉ số cố định (phím 0-3 hoặc --top 1)
      phone - điện thoại IP Webcam qua adb forward
      url   - luồng mạng (http / rtsp)
      file  - tệp video (phát lặp lại, dùng để chạy thử không cần camera)
      image - ảnh tĩnh (lặp mãi một khung, dùng để chạy thử / xem lại ảnh trong captures/)
    """

    def __init__(self, label, kind, value=None, keywords=(), fallback_keywords=(), exclude=(), rotate=None, hint=""):
        self.label = label
        self.kind = kind
        self.value = value
        self.keywords = tuple(keywords)
        self.fallback_keywords = tuple(fallback_keywords)  # Dùng khi không thấy keywords (VD: không có OBSBOT)
        self.exclude = tuple(exclude)
        self.rotate = rotate
        self.hint = hint

    def current_source(self):
        """Nguồn để mở lúc này (chỉ số / URL / đường dẫn) hoặc None nếu chưa thấy thiết bị."""
        if self.kind == "name":
            names, _ = list_camera_names()
            index = pick_camera_index(names, self.keywords, self.exclude)
            if index is None and self.fallback_keywords:
                index = pick_camera_index(names, self.fallback_keywords, self.exclude)
            return index
        if self.kind == "phone":
            adb_forward()
            return PHONE_URL
        return self.value

    def __repr__(self):
        return f"CameraSpec({self.label!r}, {self.kind})"


def top_spec(rotate=None):
    return CameraSpec(
        "OBSBOT", "name", keywords=TOP_KEYWORDS, fallback_keywords=("",), exclude=BUILTIN_KEYWORDS, rotate=rotate,
        hint="Kiem tra cap USB OBSBOT; macOS hoi quyen Camera thi bam OK",
    )


def builtin_spec(rotate=None):
    return CameraSpec(
        "MacBook", "name", keywords=BUILTIN_KEYWORDS, fallback_keywords=("",), exclude=TOP_KEYWORDS, rotate=rotate,
        hint="Camera tich hop cua MacBook; macOS hoi quyen Camera thi bam OK",
    )


def phone_spec(rotate=PHONE_ROTATE):
    return CameraSpec(
        "Dien Thoai", "phone", rotate=rotate, hint="Kiem tra cap USB, Allow tren dien thoai, IP Webcam"
    )


def parse_camera_arg(arg, role, rotate=None):
    """
    Đổi tham số dòng lệnh (--top / --side) thành CameraSpec. role: 'top' hoặc 'side'.
      auto                         cam trên = OBSBOT; cam ngang = điện thoại nếu adb thấy máy, không thì MacBook
      obsbot | mac | phone         theo tên thiết bị
      0, 1, 2 ...                  chỉ số OpenCV cố định
      http://... | rtsp://...      luồng mạng
      đường/dẫn/tệp.mp4 | .jpg     video phát lặp hoặc ảnh tĩnh
      chuỗi khác                   một phần tên camera (VD: logitech)
    rotate: 0/90/180/270 độ (None = mặc định theo loại camera).
    """
    text = (arg or "auto").strip()
    low = text.lower()
    rot = ROTATIONS.get(rotate) if rotate is not None else None

    if low == "auto":
        if role == "top":
            return top_spec(rot)
        return phone_spec(PHONE_ROTATE if rotate is None else rot) if phone_ready() else builtin_spec(rot)
    if low == "obsbot":
        return top_spec(rot)
    if low in ("mac", "macbook", "builtin", "built-in", "laptop", "facetime"):
        return builtin_spec(rot)
    if low in ("phone", "dienthoai", "android"):
        return phone_spec(PHONE_ROTATE if rotate is None else rot)
    if text.isdigit():
        return CameraSpec(f"Index {text}", "index", int(text), rotate=rot)
    if low.startswith(("http://", "https://", "rtsp://", "rtmp://")):
        return CameraSpec("Luong mang", "url", text, rotate=rot)
    if os.path.isfile(text):
        kind = "image" if low.endswith(IMAGE_EXTENSIONS) else "file"
        return CameraSpec(os.path.basename(text), kind, os.path.abspath(text), rotate=rot)
    return CameraSpec(text, "name", keywords=(low,), exclude=VIRTUAL_KEYWORDS, rotate=rot)


# ==============================================================================
# 4. Luồng đọc camera
# ==============================================================================
class CameraStream:
    """Đọc camera trên luồng riêng (Thread) để luôn lấy frame mới nhất, triệt tiêu độ trễ (delay)."""

    def __init__(self, spec, role):
        self.spec = spec
        self.role = role  # 'TREN' hoặc 'NGANG', hiện trên nhãn góc nhìn
        self.source = None  # Chỉ số / URL / tệp đang mở (None nếu chưa mở được)
        self.cap = None
        self.static_frame = None
        self.ret = False
        self.frame = None
        self.frame_id = 0  # Tăng mỗi khi có khung hình mới: vòng lặp chính chỉ xử lý nặng khi khung đã đổi
        self.last_frame_time = time.time()
        self.reopen_requested = False
        self.running = True
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    @property
    def name(self):
        return f"Cam {self.role}: {self.spec.label}"

    # --- luồng nền ---
    def _close_cap(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.static_frame = None

    def _open(self):
        """Mở (lại) camera: tìm nguồn theo spec NGAY LÚC NÀY (chỉ số có thể đã đổi) rồi tạo VideoCapture."""
        self._close_cap()
        self.reopen_requested = False
        self.source = None
        with self.lock:
            self.ret = False  # Mở lại thì khung của lần mở trước không còn đúng nữa
        source = self.spec.current_source()
        self.last_frame_time = time.time()
        if source is None:
            return
        if self.spec.kind == "image":
            self.static_frame = cv2.imread(source)
            self.source = source if self.static_frame is not None else None
            return
        cap = cv2.VideoCapture(source)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap = cap
        self.source = source
        self.last_frame_time = time.time()  # Việc mở camera có thể mất cả giây (hộp thoại quyền Camera), tính giờ lại từ lúc xong

    def _read(self):
        """Một frame mới hoặc None (chưa mở được / mất tín hiệu / hết video)."""
        if self.static_frame is not None:
            time.sleep(0.05)  # Ảnh tĩnh: không cần đọc nhanh
            return self.static_frame.copy()
        if self.cap is None or not self.cap.isOpened():
            return None
        ok, frame = self.cap.read()
        if ok:
            if self.spec.kind == "file":
                time.sleep(1.0 / max(1.0, self.cap.get(cv2.CAP_PROP_FPS) or 30.0))  # Phát đúng tốc độ video
            return frame
        if self.spec.kind == "file":
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Hết video: phát lại từ đầu
        return None

    def _update(self):
        self._open()
        while self.running:
            if self.reopen_requested:
                self._open()
            frame = self._read()
            if frame is not None:
                if self.spec.rotate is not None:
                    frame = cv2.rotate(frame, self.spec.rotate)
                with self.lock:
                    self.ret = True
                    self.frame = frame
                    self.frame_id += 1
                    self.last_frame_time = time.time()
                continue
            with self.lock:
                self.ret = False
            # Camera chưa mở được hoặc mất tín hiệu: nghỉ một nhịp (tránh vòng lặp chạy 100% CPU) rồi tự mở lại
            time.sleep(0.1)
            if self.is_stalled():
                self._open()

    # --- giao diện cho vòng lặp chính ---
    def _fresh_locked(self):
        """Có khung hợp lệ VÀ còn mới (chưa quá RETRY_SECONDS): rút cáp thì khung cuối vẫn nằm đó nhưng đã cũ, không dùng nữa. Gọi khi giữ self.lock."""
        return self.ret and self.frame is not None and time.time() - self.last_frame_time <= RETRY_SECONDS

    def is_stalled(self):
        """Quá RETRY_SECONDS chưa có frame mới: camera chưa mở được hoặc đã mất tín hiệu."""
        return time.time() - self.last_frame_time > RETRY_SECONDS

    def set_spec(self, spec):
        """Đổi sang camera khác (phím 0-3): luồng nền tự đóng camera cũ và mở camera mới."""
        self.spec = spec
        self.reopen_requested = True

    def get_frame(self):
        with self.lock:
            if self._fresh_locked():
                # Đưa về cùng khung (640x480) để ghép ngang 2 màn hình không bị lệch
                resized = letterbox(self.frame)
            else:
                # Tạo khung nền đen thông báo nếu camera đang chờ tín hiệu
                resized = np.zeros((VIEW_HEIGHT, VIEW_WIDTH, 3), dtype=np.uint8)
                cv2.putText(
                    resized,
                    f"Dang cho tin hieu: {self.name}",
                    (30, VIEW_HEIGHT // 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 165, 255),
                    2,
                )
                if self.spec.hint:
                    cv2.putText(
                        resized,
                        self.spec.hint,
                        (20, VIEW_HEIGHT // 2 + 35),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (200, 200, 200),
                        1,
                    )

            # Vẽ nhãn tên góc nhìn ở góc trên bên trái mỗi khung hình
            cv2.putText(resized, self.name, (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            return resized

    def get_raw_frame(self):
        """Frame gốc (chưa thu nhỏ) mới nhất để xử lý / lưu ảnh, hoặc None nếu chưa có tín hiệu."""
        with self.lock:
            if self._fresh_locked():
                return self.frame.copy()
            return None

    def release(self):
        self.running = False
        self.thread.join(timeout=1.0)
        if not self.thread.is_alive():  # Luồng còn kẹt trong lúc mở camera thì để nó tự chết theo tiến trình
            self._close_cap()
