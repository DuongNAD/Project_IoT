#!/usr/bin/env python3
"""
CAMERA: mở camera theo CHỈ SỐ OpenCV (0, 1, 2...) hoặc một ảnh .png / .jpg để chạy thử không cần camera.
  Cam TREN  = OBSBOT treo phía trên tờ A4 (--top).      Cam NGANG = camera MacBook đặt trước robot (--side).
macOS có thể đổi thứ tự camera giữa các lần chạy: nhìn hai khung hình, thấy đảo thì chạy lại với --top / --side đổi chỗ.
Bản đơn giản: vòng lặp chính đọc thẳng từng khung, không có luồng riêng; rút cáp camera thì chạy lại chương trình.

NÓI KHI BỊ HỎI FILE NÀY: "cameras.py chỉ làm một việc: mở camera và mỗi vòng lặp trả về một ảnh mới nhất.
Ảnh là mảng numpy cao x rộng x 3 màu (BGR). Không có hình thì trả về None để màn hình hiện chữ 'đang chờ tín hiệu'."
"""

import os
import sys

import cv2
import numpy as np


class Camera:
    """
    TÁC DỤNG: gói một camera (hoặc một ảnh tĩnh) thành một đối tượng, để main.py chỉ cần gọi get_raw_frame().
    VÀO: source = "0", "1"... (số thứ tự camera OpenCV) hoặc đường dẫn ảnh; role = "TREN" hoặc "NGANG" (để ghi lên màn hình).
    NÓI: "Mỗi camera là một đối tượng Camera. main.py tạo 2 cái: cam TRÊN để tìm vật, cam NGANG để người nhìn độ cao tay kẹp."
    """

    def __init__(self, source, role):
        """
        TÁC DỤNG: mở camera một lần lúc chạy chương trình.
        NÓI: "Nguồn là số thì mở camera bằng cv2.VideoCapture; nguồn là file ảnh thì đọc ảnh, dùng để chạy thử không cần camera."
        """
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
        """
        TÁC DỤNG: lấy 1 khung hình mới nhất.
        RA: ảnh numpy (BGR), hoặc None nếu camera chưa mở được / mất tín hiệu.
        NÓI: "Mỗi vòng lặp gọi hàm này một lần. cap.read() trả về (ok, ảnh); ok sai thì trả None."
        """
        if self.image is not None:
            return self.image.copy()  # Trả bản sao để phần vẽ phía sau không làm bẩn ảnh gốc
        ok, frame = self.cap.read() if self.cap is not None else (False, None)
        return frame if ok else None

    def waiting_image(self):
        """
        TÁC DỤNG: ô đen ghi "Dang cho tin hieu", hiện thay ảnh khi camera không có hình.
        NÓI: "Rút cáp camera thì chương trình không sập, chỉ hiện ô chờ này."
        """
        img = np.zeros((360, 640, 3), np.uint8)  # Ảnh đen 640 x 360
        cv2.putText(img, f"Dang cho tin hieu: Cam {self.role} ({self.label})", (20, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
        return img

    def release(self):
        """TÁC DỤNG: trả camera cho hệ điều hành khi thoát chương trình."""
        if self.cap is not None:
            self.cap.release()
