#!/usr/bin/env python3
"""
CHIA SẺ MÀN HÌNH QUA WI-FI cho máy Dell điều khiển từ xa (main.py chạy trên Mac tự bật).

    Mac (main.py: 2 camera, vision, control, success, USB Arduino) --Wi-Fi: ảnh màn hình--> Dell (remote.py) --Bluetooth: phím--> HC-05 --> Arduino

Chỉ cho XEM: máy chủ trả ảnh màn hình mới nhất ở http://<ip Mac>:8000/screen.jpg và không nhận lệnh nào.
Phím di chuyển đi thẳng từ Dell qua Bluetooth tới Arduino; phím R (chụp đích) bấm trên bàn phím Mac.
"""

import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2

PORT = 8000


class ScreenServer(ThreadingHTTPServer):
    """Máy chủ web chạy nền. main.py gọi update(screen) mỗi khung hình; Dell lấy ảnh ở /screen.jpg."""
    daemon_threads = True
    screen = None  # Ảnh màn hình mới nhất (BGR), chỉ nén JPEG khi Dell xin

    def update(self, screen):
        self.screen = screen

    def close(self):
        self.shutdown()
        self.server_close()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # Không in mỗi lần Dell xin ảnh ra Terminal
        pass

    def do_GET(self):
        if self.server.screen is None:  # main.py chưa vẽ khung nào
            self.send_error(503)
            return
        jpg = cv2.imencode(".jpg", self.server.screen, [cv2.IMWRITE_JPEG_QUALITY, 70])[1].tobytes()
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(jpg)))
        self.end_headers()
        self.wfile.write(jpg)


def lan_ip():
    """IP của Mac trong mạng Wi-Fi (kết nối UDP không gửi gói nào, chỉ để hỏi hệ điều hành dùng card mạng nào)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:  # Không có mạng: main.py vẫn chạy bình thường, chỉ máy Dell không xem được
        return "127.0.0.1"
    finally:
        s.close()


def start(port=PORT):
    """Bật chia sẻ màn hình ở luồng nền và in lệnh cho máy Dell."""
    server = ScreenServer(("0.0.0.0", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"🖥️  Máy Dell (cùng Wi-Fi) chạy:  python remote.py --mac http://{lan_ip()}:{port}/ --port COMx")
    return server
