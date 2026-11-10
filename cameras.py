#!/usr/bin/env python3
"""
CAMERA: mỗi camera đọc trên một luồng riêng để luôn có khung hình mới nhất.
  Cam TREN  = OBSBOT treo phía trên tờ A4.      Cam NGANG = camera MacBook đặt trước robot.
macOS đổi thứ tự camera giữa các lần chạy, nên mỗi lần mở đều tìm camera theo TÊN.
Mất tín hiệu quá RETRY_SECONDS (rút cáp...) thì tự mở lại. Chạy thử không cần camera: --top anh.png --side anh.png
"""

import json
import os
import subprocess
import sys
import threading
import time

import cv2
import numpy as np

RETRY_SECONDS = 4
CAMERAS = {  # Tên dùng ở --top / --side -> (nhãn, từ khóa tìm trong tên camera)
    "obsbot": ("OBSBOT", ("obsbot",)),
    "mac": ("MacBook", ("macbook", "facetime", "built-in", "integrated")),  # "integrated": webcam laptop Windows
}


def list_camera_names():
    """Tên các camera theo đúng thứ tự chỉ số của cv2.VideoCapture."""
    try:
        if sys.platform == "win32":  # Thứ tự DirectShow, khớp với cv2.CAP_DSHOW
            from pygrabber.dshow_graph import FilterGraph

            return FilterGraph().get_input_devices()
        out = subprocess.run(["system_profiler", "SPCameraDataType", "-json"], capture_output=True, text=True, timeout=15).stdout
        cams = sorted(json.loads(out)["SPCameraDataType"], key=lambda c: c.get("spcamera_unique-id", ""))  # OpenCV trên macOS đánh số theo uniqueID
        return [c["_name"] for c in cams]
    except Exception:
        return []


def find_camera(keywords):
    """Chỉ số camera đầu tiên có tên chứa một từ khóa, bỏ camera ảo (OBSBOT Virtual Camera, Desk View); None nếu không thấy."""
    for i, name in enumerate(list_camera_names()):
        name = name.lower()
        if any(k in name for k in keywords) and "virtual" not in name and "desk view" not in name:
            return i
    return None


class Camera:
    """source: "obsbot" | "mac" (tìm theo tên) | "0", "1"... (chỉ số OpenCV) | đường dẫn ảnh. role: "TREN" | "NGANG"."""

    def __init__(self, source, role):
        self.arg, self.role = source, role
        self.label = CAMERAS[source][0] if source in CAMERAS else os.path.basename(source)
        self.source = None  # Chỉ số / tệp đang mở, None nếu chưa thấy camera
        self.cap = self.image = self.frame = None
        self.frame_id = 0   # Tăng mỗi khi có khung mới: main.py chỉ xử lý lại khi khung đã đổi
        self.last_time = self.opened_time = time.time()  # Lúc có khung cuối cùng / lúc mở camera gần nhất
        self.running = True
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _open(self):
        if self.cap is not None:
            self.cap.release()
        self.cap = self.image = None
        self.opened_time = time.time()
        if self.arg.lower().endswith((".png", ".jpg", ".jpeg")):  # Ảnh tĩnh: lặp lại mãi một khung
            self.image = cv2.imread(self.arg)
            self.source = self.arg if self.image is not None else None
            return
        if self.arg.isdigit():
            self.source = int(self.arg)
        else:  # obsbot / mac, hoặc một phần tên camera (VD: logitech)
            self.source = find_camera(CAMERAS.get(self.arg, ("", (self.arg.lower(),)))[1])
        if self.source is not None:
            self.cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW) if sys.platform == "win32" else cv2.VideoCapture(self.source)

    def _read(self):
        """Một khung mới, hoặc None (chưa thấy camera / mất tín hiệu)."""
        if self.image is not None:
            time.sleep(0.05)
            return self.image.copy()
        ok, frame = self.cap.read() if self.cap is not None else (False, None)
        return frame if ok else None

    def _loop(self):
        self._open()
        while self.running:
            if self.stalled() and time.time() - self.opened_time > RETRY_SECONDS:  # Mất tín hiệu: thử mở lại sau mỗi RETRY_SECONDS
                self._open()
            frame = self._read()
            if frame is None:
                time.sleep(0.1)
                continue
            with self.lock:
                self.frame, self.frame_id, self.last_time = frame, self.frame_id + 1, time.time()
        if self.cap is not None:
            self.cap.release()

    def stalled(self):
        """Quá RETRY_SECONDS không có khung mới: chưa mở được camera hoặc đã mất tín hiệu."""
        return time.time() - self.last_time > RETRY_SECONDS

    def get_raw_frame(self):
        """Khung gốc mới nhất, None nếu chưa có hoặc đã cũ (rút cáp thì khung cuối vẫn còn nhưng không dùng nữa)."""
        with self.lock:
            return None if self.frame is None or self.stalled() else self.frame.copy()

    def waiting_image(self):
        img = np.zeros((360, 640, 3), np.uint8)
        cv2.putText(img, f"Dang cho tin hieu: Cam {self.role} ({self.label})", (20, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
        return img

    def release(self):
        self.running = False
        self.thread.join(timeout=1.0)
