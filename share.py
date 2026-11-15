#!/usr/bin/env python3
"""
CHIA SẺ MÀN HÌNH QUA WI-FI cho máy Dell điều khiển từ xa (main.py chạy trên Mac tự bật).

    Mac (main.py) <--Wi-Fi: ảnh màn hình / phím--> laptop (remote.py) --Bluetooth: phím--> HC-05 --> Arduino

- GET  /screen.jpg : ảnh màn hình mới nhất cho laptop xem.
- POST /key/<phím> : laptop báo phím vừa gửi qua Bluetooth (a d w s i k j l h); main.py cộng / trừ góc tương ứng trên Mac.
Phím R (chụp đích) bấm trên bàn phím Mac.

NÓI KHI BỊ HỎI FILE NÀY: "share.py là một máy chủ web nhỏ chạy nền trên Mac, cổng 8000.
Laptop xin ảnh ở /screen.jpg để xem màn hình, và báo mỗi phím đã bấm ở /key/<phím> để Mac cộng trừ góc cho khớp."
"""

import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2

PORT = 8000
KEYS = "adwsikjlh"  # Phím laptop được báo qua Wi-Fi, giống phím firmware hiểu


class ScreenServer(ThreadingHTTPServer):
    """
    TÁC DỤNG: máy chủ web chạy nền, giữ ảnh màn hình mới nhất và hàng đợi phím laptop gửi tới.
    NÓI: "main.py gọi update(screen) mỗi khung hình để có ảnh mới, và pop_keys() để lấy các phím laptop vừa báo."
    """
    daemon_threads = True
    screen = None  # Ảnh màn hình mới nhất (BGR), chỉ nén JPEG khi laptop xin

    def __init__(self, *args):
        super().__init__(*args)
        self.keys = []  # Phím laptop gửi qua Wi-Fi, chờ main.py lấy
        self.lock = threading.Lock()  # Khoá: luồng web và vòng lặp chính không cùng sửa danh sách phím một lúc

    def update(self, screen):
        """TÁC DỤNG: cất ảnh màn hình mới nhất (main.py gọi mỗi khung hình)."""
        self.screen = screen

    def pop_keys(self):
        """TÁC DỤNG: lấy (và xóa) các phím laptop đã gửi tới từ lần gọi trước."""
        with self.lock:
            keys, self.keys = self.keys, []
        return keys

    def close(self):
        """TÁC DỤNG: tắt máy chủ web khi thoát chương trình."""
        self.shutdown()
        self.server_close()


class Handler(BaseHTTPRequestHandler):
    """TÁC DỤNG: trả lời từng yêu cầu của laptop: GET = xin ảnh, POST = báo phím."""

    def log_message(self, *args):  # Không in mỗi lần Dell xin ảnh ra Terminal
        pass

    def do_GET(self):
        """TÁC DỤNG: laptop xin ảnh: nén ảnh màn hình thành JPEG (chất lượng 70) rồi gửi đi."""
        if self.server.screen is None:  # main.py chưa vẽ khung nào
            self.send_error(503)
            return
        jpg = cv2.imencode(".jpg", self.server.screen, [cv2.IMWRITE_JPEG_QUALITY, 70])[1].tobytes()
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(jpg)))
        self.end_headers()
        self.wfile.write(jpg)

    def do_POST(self):
        """TÁC DỤNG: laptop báo 1 phím (địa chỉ /key/a, /key/w...): phím hợp lệ thì cho vào hàng đợi, sai thì báo lỗi 404."""
        key = self.path.rstrip("/").rsplit("/", 1)[-1].lower()  # "/key/a" -> "a"
        if not self.path.startswith("/key/") or len(key) != 1 or key not in KEYS:
            self.send_error(404)
            return
        with self.server.lock:
            self.server.keys.append(key)
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()


def lan_ip():
    """TÁC DỤNG: tìm IP của Mac trong mạng Wi-Fi (kết nối UDP không gửi gói nào, chỉ để hỏi hệ điều hành dùng card mạng nào)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:  # Không có mạng: main.py vẫn chạy bình thường, chỉ máy Dell không xem được
        return "127.0.0.1"
    finally:
        s.close()


def start(port=PORT):
    """
    TÁC DỤNG: bật máy chủ web ở một luồng nền (để vòng lặp camera không phải chờ) và in lệnh cho laptop.
    NÓI: "Chạy main.py là máy chủ tự bật; Terminal in sẵn lệnh remote.py có IP của Mac để chạy trên laptop."
    """
    server = ScreenServer(("0.0.0.0", port), Handler)  # 0.0.0.0 = nhận kết nối từ máy khác trong mạng
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"🖥️  Laptop (cùng Wi-Fi) chạy:  python remote.py --mac http://{lan_ip()}:{port}/ --port COMx")
    return server
