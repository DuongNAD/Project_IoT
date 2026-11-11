#!/usr/bin/env python3
"""
APP ĐIỀU KHIỂN TỪ XA TRÊN MÁY DELL (đặt cách cánh tay khoảng 2 m)

    Mac (main.py: 2 camera, vision, control, success) --Wi-Fi: ảnh màn hình--> remote.py (Dell) --Bluetooth: phím--> HC-05 --> Arduino

- XEM: ảnh màn hình của Mac (2 camera + lệnh bấm phím + XONG) qua Wi-Fi, từ đường dẫn main.py in ra trên Mac.
- BẤM: A D W S I K J L H X Z trên bàn phím Dell đi qua cổng COM Bluetooth của HC-05 thẳng tới Arduino.
  H (về Home) và Z (nghỉ hết) phải bấm 2 lần trong 2 giây mới gửi, để khỏi bấm nhầm. Q / ESC: thoát.
- R (chụp đích) bấm trên bàn phím Mac: Arduino không hiểu R.

Mac vẫn cắm USB vào Arduino: sau mỗi phím Arduino báo góc mới về Mac, Mac tính lại lệnh + success rồi ảnh mới về đây.

    python remote.py --mac http://192.168.1.5:8000/ --port COM5

Cổng COM của HC-05 (Windows): Settings > Bluetooth & devices > Devices > More Bluetooth settings > tab COM Ports, dòng Outgoing tên HC-05.
Chỉ cần OpenCV, numpy, pyserial. Chữ trên cửa sổ không dấu vì font OpenCV không vẽ được dấu.
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
except ImportError:  # Thiếu pyserial: cửa sổ vẫn mở để xem, chỉ không gửi được phím
    serial = None

SERVO_KEYS = "adwsikjlhxz"  # Phím firmware hiểu, giống bàn phím trên Mac
CONFIRM_KEYS = {"h": "ve Home (de 180, vai 90, khuyu 90)", "z": "ngat xung ca 4 servo"}  # Phải bấm 2 lần
CONFIRM_S = 2.0      # Lần bấm thứ 2 phải trong ngần này giây
FRAME_GAP_S = 0.1    # Lấy ảnh từ Mac tối đa 10 lần / giây
STALE_S = 3.0        # Ảnh cũ hơn ngần này giây: coi như mất kết nối Mac
NOTE_S = 2.5         # Thông báo "DA GUI D" hiện ngần này giây
RETRY_S = 2.0        # Chưa nối được Bluetooth thì thử lại sau ngần này giây
BAR_H = 56           # Thanh trạng thái trên cùng (2 dòng: Mac, Bluetooth)
WINDOW = "DIEU KHIEN TU XA: xem qua Wi-Fi, bam phim qua Bluetooth (Q = thoat)"

BG = (30, 27, 25)
GREEN, AMBER, RED, WHITE, MUTED = (110, 215, 90), (40, 185, 255), (85, 85, 245), (245, 245, 245), (165, 160, 155)
FONT, AA = cv2.FONT_HERSHEY_SIMPLEX, cv2.LINE_AA


# ==============================================================================
# 1. Bluetooth: gửi phím tới HC-05
# ==============================================================================
class BluetoothLink:
    """Gửi phím qua cổng COM Bluetooth của HC-05. Mở cổng ở luồng nền (Windows mất vài giây để nối tới HC-05), rớt thì nối lại."""

    def __init__(self, port, baud=9600, serial_module=None, start=True):
        self.port, self.baud = port, baud
        self.serial = serial_module or serial
        self.ser = None
        self.state = f"dang noi {port}..."  # Dòng chữ cho thanh trạng thái
        self.lock = threading.Lock()
        self.running = True
        if start:
            threading.Thread(target=self._keep_open, daemon=True).start()

    @property
    def connected(self):
        return self.ser is not None

    def open_once(self):
        """Thử mở cổng một lần; True nếu đã nối."""
        if self.serial is None:
            self.state = "thieu pyserial: pip install pyserial"
            return False
        try:
            ser = self.serial.Serial(self.port, self.baud, timeout=0, write_timeout=1)
        except Exception:
            self.state = f"khong noi duoc {self.port}: HC-05 co dien? dung cong Outgoing?"
            return False
        with self.lock:
            self.ser = ser
        self.state = f"{self.port} da noi"
        return True

    def _keep_open(self):
        while self.running:
            if self.ser is None:
                self.open_once()
            time.sleep(RETRY_S)

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
    """Lấy ảnh màn hình Mac (http://<ip Mac>:8000/screen.jpg) trong luồng nền."""

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
        try:
            with urllib.request.urlopen(self.base + "screen.jpg", timeout=timeout) as r:
                data = r.read()
            img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("anh hong")
        except urllib.error.HTTPError as e:
            self.error = "Mac chua co anh" if e.code == 503 else f"loi {e.code} (xem lai duong dan Mac in ra)"
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
        screen = np.full((650, 1280, 3), BG, np.uint8)  # Cùng cỡ màn hình main.py
        text = "DANG CHO ANH TU MAC..."
        put(screen, text, (1280 - cv2.getTextSize(text, FONT, 1.2, 2)[0][0]) // 2, 325, 1.2, MUTED, 2)
    elif not mac_ok:
        screen = screen.copy()
        cv2.rectangle(screen, (0, 0), (screen.shape[1] - 1, screen.shape[0] - 1), RED, 6)  # Viền đỏ: ảnh đã cũ
    w = screen.shape[1]
    bar = np.full((BAR_H, w, 3), BG, np.uint8)
    for row, (text, ok) in enumerate(((mac_text, mac_ok), (bt_text, bt_ok))):
        y = 21 + row * 25
        cv2.circle(bar, (18, y - 5), 6, GREEN if ok else RED, -1, AA)
        put(bar, text[:80], 32, y, 0.55, GREEN if ok else AMBER)
    if note:
        put(bar, note, w - 16, 36, 0.7, note_col, 2, right=True)
    return np.vstack([bar, screen])


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Máy Dell: xem màn hình Mac qua Wi-Fi, bấm phím điều khiển cánh tay qua Bluetooth HC-05")
    p.add_argument("--mac", required=True, help="Đường dẫn main.py in ra trên Mac, VD http://192.168.1.5:8000/")
    p.add_argument("--port", required=True, help="Cổng COM Bluetooth (Outgoing) của HC-05, VD COM5")
    p.add_argument("--baud", type=int, default=9600, help="Tốc độ HC-05 (mặc định 9600, giống firmware)")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    view, bt, gate = MacView(args.mac), BluetoothLink(args.port, args.baud), KeyGate()
    note, note_col, note_at = "", WHITE, 0.0
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW, 1120, 618)
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
            if ch == "r":
                note, note_col, note_at = "R (CHUP DICH): BAM TREN BAN PHIM MAC", AMBER, time.time()
                continue
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
