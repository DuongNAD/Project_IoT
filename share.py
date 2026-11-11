#!/usr/bin/env python3
"""
CHIA SẺ MÀN HÌNH QUA WI-FI cho máy Dell điều khiển từ xa (main.py chạy trên Mac tự bật).

    Mac (main.py: 2 camera, vision, control, success, USB Arduino) --Wi-Fi: ảnh màn hình--> Dell (remote.py) --Bluetooth: phím--> HC-05 --> Arduino

Chỉ cho XEM: máy chủ trả ảnh màn hình mới nhất ở http://<ip Mac>:8000/screen.jpg và không nhận lệnh nào.
Phím di chuyển đi thẳng từ Dell qua Bluetooth tới Arduino; phím R (chụp đích) bấm trên bàn phím Mac.
Chỉ dùng thư viện chuẩn của Python (http.server) và OpenCV.
"""

import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2

PORT = 8000
JPEG_QUALITY = 70


def lan_ip():
    """Địa chỉ IP của Mac trong mạng Wi-Fi (kết nối UDP không gửi gói nào, chỉ để hỏi hệ điều hành dùng card mạng nào)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


class ScreenServer:
    """Máy chủ web chạy nền. main.py gọi update(screen) mỗi khung hình; Dell lấy ảnh ở /screen.jpg."""

    def __init__(self, port=PORT, host="0.0.0.0"):
        self.lock = threading.Lock()
        self.screen = None  # Ảnh màn hình mới nhất (BGR), chỉ nén JPEG khi Dell xin
        self.httpd = ThreadingHTTPServer((host, port), self._handler())
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def url(self, host=None):
        return f"http://{host or lan_ip()}:{self.port}/"

    def update(self, screen):
        with self.lock:
            self.screen = screen

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    def _handler(self):
        server = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):  # Không in mỗi yêu cầu ra Terminal
                pass

            def _send(self, code, body, ctype="text/plain; charset=utf-8"):
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path.split("?")[0] != "/screen.jpg":
                    return self._send(404, b"Chi co /screen.jpg")
                with server.lock:
                    screen = server.screen
                if screen is None:
                    return self._send(503, b"Chua co anh")
                ok, jpg = cv2.imencode(".jpg", screen, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
                return self._send(200, jpg.tobytes() if ok else b"", "image/jpeg")

        return Handler


def start(port=PORT):
    """Bật chia sẻ màn hình và in lệnh cho máy Dell; None nếu cổng đang bận (chương trình vẫn chạy, chỉ không chia sẻ)."""
    try:
        server = ScreenServer(port)
    except OSError as e:
        print(f"⚠️ Không chia sẻ được màn hình qua Wi-Fi ở cổng {port} ({e}): máy Dell sẽ không xem được")
        return None
    print(f"🖥️  Máy Dell (cùng Wi-Fi) chạy:  python remote.py --mac {server.url()} --port COMx")
    return server
