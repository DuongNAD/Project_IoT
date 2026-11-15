#!/usr/bin/env python3
"""
CAMERA: mở camera theo CHỈ SỐ OpenCV (0, 1, 2...) hoặc một ảnh .png / .jpg để chạy thử không cần camera.
  Cam TREN  = OBSBOT treo phía trên tờ A4 (--top).      Cam NGANG = camera MacBook đặt trước robot (--side).
macOS có thể đổi thứ tự camera giữa các lần chạy: nhìn hai khung hình, thấy đảo thì chạy lại với --top / --side đổi chỗ.
Bản đơn giản: vòng lặp chính đọc thẳng từng khung, không có luồng riêng; rút cáp camera thì chạy lại chương trình.
"""

import os
import sys

import cv2
import numpy as np


class Camera:
    """Một camera (hoặc một ảnh tĩnh để chạy thử). source: "0", "1"... hoặc đường dẫn ảnh. role: "TREN" | "NGANG"."""

    def __init__(self, source, role):
        """Mở camera một lần lúc khởi động: nguồn là số thì mở bằng cv2.VideoCapture, nguồn là file ảnh thì đọc ảnh."""
        self.role = role
        self.label = f"camera {source}" if source.isdigit() else os.path.basename(source)  # Tên hiện trên màn hình
        self.cap = self.image = None
        if source.lower().endswith((".png", ".jpg", ".jpeg")):  # Ảnh tĩnh: lần đọc nào cũng trả lại đúng ảnh đó
            self.image = cv2.imread(source)
        elif source.isdigit():  # Windows mở qua DirectShow (cv2.CAP_DSHOW), macOS dùng mặc định của OpenCV
            index = int(source)
            self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW) if sys.platform == "win32" else cv2.VideoCapture(index)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Giữ ít khung trong bộ đệm để hình không bị trễ

    def get_raw_frame(self):
        """Khung mới nhất của camera (ảnh BGR), None nếu chưa mở được camera hoặc mất tín hiệu."""
        if self.image is not None:
            return self.image.copy()  # Trả bản sao để phần vẽ phía sau không sửa ảnh gốc
        ok, frame = self.cap.read() if self.cap is not None else (False, None)
        return frame if ok else None

    def waiting_image(self):
        """Ô đen ghi "Dang cho tin hieu", hiện thay ảnh khi camera không có hình."""
        img = np.zeros((360, 640, 3), np.uint8)
        cv2.putText(img, f"Dang cho tin hieu: Cam {self.role} ({self.label})", (20, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
        return img

    def release(self):
        """Trả camera cho hệ điều hành khi thoát."""
        if self.cap is not None:
            self.cap.release()
