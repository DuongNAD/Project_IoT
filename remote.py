#!/usr/bin/env python3
"""
APP ĐIỀU KHIỂN TRÊN MÁY DELL (đặt cách cánh tay khoảng 2 m)

    Mac (main.py, 2 camera)  --Wi-Fi: ảnh màn hình-->  remote.py (Dell)  --Bluetooth: phím-->  HC-05  -->  Arduino

- XEM: lấy ảnh màn hình của Mac (2 camera + lệnh bấm phím + XONG) qua Wi-Fi, từ đường dẫn main.py in ra trên Mac.
- BẤM: gõ A D W S I K J L H X Z trên bàn phím Dell -> gửi qua cổng COM Bluetooth của HC-05 thẳng tới Arduino.
  H (về Home) và Z (nghỉ hết) phải bấm 2 lần trong 2 giây mới gửi, để khỏi bấm nhầm. Q / ESC: thoát.

Mac vẫn cắm USB vào Arduino: sau mỗi phím Arduino báo góc mới về Mac, Mac tính lại lệnh + success rồi màn mới về đây.

    uv run python remote.py --mac http://192.168.1.5:8000/123456/              tự tìm cổng Bluetooth của HC-05
    uv run python remote.py --mac http://192.168.1.5:8000/123456/ --port COM5
    uv run python remote.py --list-ports                                        xem các cổng COM / Bluetooth

Chỉ cần OpenCV, numpy, pyserial (có sẵn trong dự án). Chữ trên cửa sổ không dấu vì font OpenCV không vẽ được dấu.
"""

import argparse
import threading
import time
import urllib.error
import urllib.request

import cv2
import numpy as np

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # pragma: no cover - pyserial nằm trong dependencies của dự án
    serial = list_ports = None

SERVO_KEYS = "adwsikjlhxz"  # Phím firmware hiểu, giống bàn phím trên Mac
CONFIRM_KEYS = {"h": "ve Home (90/90/90)", "z": "ngat xung ca 4 servo"}  # Phải bấm 2 lần
CONFIRM_S = 2.0      # Lần bấm thứ 2 phải trong ngần này giây
FRAME_GAP_S = 0.1    # Lấy ảnh từ Mac tối đa 10 lần / giây
STALE_S = 3.0        # Ảnh cũ hơn ngần này giây: coi như mất kết nối Mac
NOTE_S = 2.5         # Thông báo "DA GUI D" hiện ngần này giây
BAR_H = 56           # Thanh trạng thái trên cùng (2 dòng: Mac, Bluetooth)
WINDOW = "DIEU KHIEN TU XA: xem qua Wi-Fi, bam phim qua Bluetooth (Q = thoat)"

BG = (30, 27, 25)
GREEN, AMBER, RED, WHITE, MUTED = (110, 215, 90), (40, 185, 255), (85, 85, 245), (245, 245, 245), (165, 160, 155)
FONT, AA = cv2.FONT_HERSHEY_SIMPLEX, cv2.LINE_AA


# ==============================================================================
# 1. Bluetooth: cổng COM của HC-05
# ==============================================================================
def bluetooth_ports(ports=None):
    """
    Các cổng có thể là HC-05, cổng hợp nhất đứng đầu.
    Windows: ghép đôi HC-05 tạo 2 cổng "Standard Serial over Bluetooth link"; cổng Outgoing (Dell gọi đi) có địa chỉ HC-05 trong hwid,
    cổng Incoming có 000000000000 nên bỏ. macOS: /dev/cu.HC-05...
    """
    if ports is None:
        ports = list_ports.comports() if list_ports is not None else []
    found = []
    for p in ports:
        text = f"{p.device} {p.description} {p.hwid}".lower()
        if not any(w in text for w in ("bluetooth", "bthenum", "hc-0", "hc0")):
            continue
        if "000000000000" in text or "incoming" in text or p.device.startswith("/dev/tty."):
            continue
        found.append(p)
    found.sort(key=lambda p: (0 if any(h in f"{p.device} {p.description}".lower() for h in ("hc-05", "hc05", "hc-06", "hc06")) else 1, p.device))
    return [p.device for p in found]


class BluetoothLink:
    """Gửi phím qua cổng COM Bluetooth. Mở cổng trong luồng nền (Windows mất vài giây để nối tới HC-05) và tự nối lại khi rớt."""

    RETRY_S = 2.0

    def __init__(self, port=None, baud=9600, serial_module=None, start=True):
        self.port_arg, self.port, self.baud = port, port, baud
        self.serial = serial_module or serial
        self.ser = None
        self.state = "dang tim cong..."  # Dòng chữ cho thanh trạng thái
        self.lock = threading.Lock()
        self.running = True
        if start:
            threading.Thread(target=self._keep_open, daemon=True).start()

    @property
    def connected(self):
        return self.ser is not None

    def open_once(self):
        """Thử mở cổng một lần; True nếu đã nối."""
        port = self.port_arg or next(iter(bluetooth_ports()), None)
        if port is None:
            self.state = "chua thay cong Bluetooth (da ghep doi HC-05 chua?)"
            return False
        self.port, self.state = port, f"dang noi {port}..."
        try:
            ser = self.serial.Serial(port, self.baud, timeout=0, write_timeout=1)
        except Exception:
            self.state = f"khong noi duoc {port} (HC-05 co dien? xa qua?)"
            return False
        with self.lock:
            self.ser = ser
        self.state = f"{port} da noi"
        return True

    def _keep_open(self):
        while self.running:
            if self.ser is None:
                self.open_once()
            time.sleep(self.RETRY_S)

    def send(self, key):
        """Gửi một phím; False nếu chưa nối hoặc vừa rớt kết nối (luồng nền sẽ nối lại)."""
        with self.lock:
            ser = self.ser
            if ser is None:
                return False
            try:
                ser.write(key.encode("ascii"))
                ser.flush()
                return True
            except Exception:
                try:
                    ser.close()
                except Exception:
                    pass
                self.ser = None
                self.state = f"{self.port} rot ket noi, dang noi lai..."
                return False

    def close(self):
        self.running = False
        with self.lock:
            if self.ser is not None:
                try:
                    self.ser.close()
                except Exception:
                    pass
                self.ser = None


class KeyGate:
    """Phím nào được gửi: phím servo gửi ngay; H và Z phải bấm 2 lần trong CONFIRM_S giây."""

    def __init__(self):
        self.pending, self.pending_at = None, 0.0

    def press(self, key, now=None):
        """Trả về (phím cần gửi hoặc None, lời nhắc)."""
        now = time.time() if now is None else now
        k = (key or "")[:1].lower()
        if not k or k not in SERVO_KEYS:
            return None, ""
        if k in CONFIRM_KEYS:
            if self.pending == k and now - self.pending_at <= CONFIRM_S:
                self.pending = None
                return k, ""
            self.pending, self.pending_at = k, now
            return None, f"BAM {k.upper()} LAN NUA de {CONFIRM_KEYS[k]}"
        self.pending = None
        return k, ""


# ==============================================================================
# 2. Wi-Fi: ảnh màn hình của Mac
# ==============================================================================
class MacView:
    """Lấy ảnh màn hình Mac (http://<ip Mac>:8000/<mã>/screen.jpg) trong luồng nền."""

    def __init__(self, url, start=True):
        self.base = url if url.endswith("/") else url + "/"
        self.frame, self.frame_at = None, 0.0
        self.error = "dang noi..."
        self.fps = 0.0
        self.running = True
        if start:
            threading.Thread(target=self._loop, daemon=True).start()

    @property
    def ok(self):
        return self.frame is not None and time.time() - self.frame_at <= STALE_S

    def fetch_once(self, timeout=2.0):
        req = urllib.request.Request(self.base + "screen.jpg", headers={"ngrok-skip-browser-warning": "1"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
            img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("anh hong")
        except urllib.error.HTTPError as e:
            self.error = {404: "sai ma trong duong dan (xem lai link Mac in ra)", 503: "Mac chua co anh"}.get(e.code, f"loi {e.code}")
            return False
        except Exception:
            self.error = "khong thay Mac (cung Wi-Fi chua? main.py dang chay?)"
            return False
        self.frame, self.frame_at, self.error = img, time.time(), ""
        return True

    def _loop(self):
        count, t0 = 0, time.time()
        while self.running:
            start = time.time()
            count += self.fetch_once()
            if time.time() - t0 >= 2.0:
                self.fps, count, t0 = count / (time.time() - t0), 0, time.time()
            time.sleep(1.0 if self.error else max(0.0, FRAME_GAP_S - (time.time() - start)))


# ==============================================================================
# 3. Cửa sổ
# ==============================================================================
def put(img, text, x, y, scale, color, thick=1, right=False):
    if right:
        x -= cv2.getTextSize(text, FONT, scale, thick)[0][0]
    cv2.putText(img, text, (int(x), int(y)), FONT, scale, color, thick, AA)


def compose(screen, mac_text, mac_ok, bt_text, bt_ok, note="", note_col=WHITE):
    """Thanh trạng thái (Mac / Bluetooth / thông báo) + ảnh màn hình Mac, hoặc ô chờ khi chưa có ảnh."""
    if screen is None:
        screen = np.full((728, 1280, 3), BG, np.uint8)  # Cùng cỡ màn hình main.py
        text = "DANG CHO ANH TU MAC..."
        put(screen, text, (1280 - cv2.getTextSize(text, FONT, 1.2, 2)[0][0]) // 2, 364, 1.2, MUTED, 2)
    elif not mac_ok:
        screen = screen.copy()
        cv2.rectangle(screen, (0, 0), (screen.shape[1] - 1, screen.shape[0] - 1), RED, 6)  # Viền đỏ: ảnh đã cũ
    w = screen.shape[1]
    bar = np.full((BAR_H, w, 3), BG, np.uint8)
    for row, (text, ok) in enumerate(((mac_text, mac_ok), (bt_text, bt_ok))):
        y = 21 + row * 25
        cv2.circle(bar, (18, y - 5), 6, GREEN if ok else RED, -1, AA)
        put(bar, text[:70], 32, y, 0.55, GREEN if ok else AMBER)
    if note:
        put(bar, note, w - 16, 36, 0.7, note_col, 2, right=True)
    return np.vstack([bar, screen])


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Máy Dell: xem màn hình Mac qua Wi-Fi, bấm phím điều khiển cánh tay qua Bluetooth HC-05")
    p.add_argument("--mac", help="Đường dẫn main.py in ra trên Mac, VD http://192.168.1.5:8000/123456/")
    p.add_argument("--port", help="Cổng COM Bluetooth của HC-05, VD COM5 (mặc định tự tìm)")
    p.add_argument("--baud", type=int, default=9600, help="Tốc độ HC-05 (mặc định 9600, giống firmware)")
    p.add_argument("--list-ports", action="store_true", help="In các cổng COM / Bluetooth rồi thoát")
    args = p.parse_args(argv)
    if not args.list_ports and not args.mac:
        p.error("thiếu --mac: chép đường dẫn main.py in ra trên Mac (dạng http://<ip>:8000/<mã>/)")
    return args


def main(argv=None):
    args = parse_args(argv)
    if args.list_ports:
        for p in (list_ports.comports() if list_ports is not None else []):
            print(f"{p.device:14s} {p.description}  [{p.hwid}]")
        print("Cổng Bluetooth sẽ dùng:", ", ".join(bluetooth_ports()) or "chưa có (ghép đôi HC-05 trong cài đặt Bluetooth trước)")
        return
    view, bt, gate = MacView(args.mac), BluetoothLink(args.port, args.baud), KeyGate()
    note, note_col, note_at = "", WHITE, 0.0
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW, 1120, 686)
    try:
        while True:
            mac_text = f"MAC (Wi-Fi): da noi, {view.fps:.0f} anh/giay" if view.ok else f"MAC (Wi-Fi): {view.error or 'mat ket noi'}"
            if time.time() - note_at > NOTE_S:
                note = ""
            cv2.imshow(WINDOW, compose(view.frame, mac_text, view.ok, f"BLUETOOTH: {bt.state}", bt.connected, note, note_col))
            key = cv2.waitKey(15)
            if cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
                break  # Đóng cửa sổ bằng nút X
            if key == -1 or key & 0xFF == 255:
                continue
            ch = chr(key & 0xFF).lower()
            if ch == "q" or key & 0xFF == 27:
                break
            send, msg = gate.press(ch)
            if send:
                sent = bt.send(send)
                note, note_col = (f"DA GUI {send.upper()}", GREEN) if sent else (f"CHUA GUI {send.upper()}: CHUA NOI BLUETOOTH", RED)
            elif msg:
                note, note_col = msg, AMBER
            if send or msg:
                note_at = time.time()
    finally:
        view.running = False
        bt.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
