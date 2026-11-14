#!/usr/bin/env python3
"""
APP ĐIỀU KHIỂN TỪ XA TRÊN MÁY DELL (đặt cách cánh tay khoảng 2 m)

    Mac (main.py: 2 camera, vision, control, success) --Wi-Fi: ảnh màn hình--> remote.py (Dell) --Bluetooth: phím--> HC-05 --> Arduino

- XEM: ảnh màn hình của Mac (2 camera + lệnh bấm phím + XONG) qua Wi-Fi, từ đường dẫn main.py in ra trên Mac.
- BẤM: A D W S I K J L H trên bàn phím Dell đi qua cổng COM Bluetooth của HC-05 thẳng tới Arduino.
  H (về Home) phải bấm 2 lần trong 2 giây mới gửi, để khỏi bấm nhầm. Q / ESC: thoát.
- R (chụp đích) bấm trên bàn phím Mac: Arduino không hiểu R.

Mac vẫn cắm USB vào Arduino: sau mỗi phím Arduino báo góc mới về Mac, Mac tính lại lệnh + success rồi ảnh mới về đây.

    python remote.py --mac http://192.168.1.5:8000/ --port COM5

Cổng COM của HC-05 (Windows): Settings > Bluetooth & devices > Devices > More Bluetooth settings > tab COM Ports, dòng Outgoing tên HC-05.
Không mở được cổng Bluetooth thì chương trình dừng và báo lỗi của pyserial. Chữ trên cửa sổ không dấu vì font OpenCV không vẽ được dấu.
"""

import argparse
import threading
import time
import urllib.request

import cv2
import numpy as np
import serial

SERVO_KEYS = "adwsikjlh"  # Phím firmware hiểu, giống bàn phím trên Mac
CONFIRM_KEYS = {"h": "ve Home"}  # Phím này phải bấm 2 lần
CONFIRM_S = 2.0  # Lần bấm thứ 2 phải trong ngần này giây
WINDOW = "DIEU KHIEN TU XA: xem qua Wi-Fi, bam phim qua Bluetooth (Q = thoat)"


class MacView:
    """Luồng nền lấy ảnh màn hình Mac (http://<ip Mac>:8000/screen.jpg) khoảng 10 lần / giây."""

    def __init__(self, url):
        self.url = url.rstrip("/") + "/screen.jpg"
        self.frame = None  # Ảnh mới nhất; mất Wi-Fi thì giữ ảnh cũ
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while True:
            try:
                data = urllib.request.urlopen(self.url, timeout=2).read()
                self.frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            except Exception:
                time.sleep(1)  # Mac chưa chạy main.py hoặc chưa cùng Wi-Fi: thử lại sau 1 giây
            time.sleep(0.1)


def confirm(key, pending, now):
    """H phải bấm 2 lần trong CONFIRM_S giây. Trả về (gửi được chưa, lần bấm đang chờ xác nhận)."""
    if key not in CONFIRM_KEYS:
        return True, None
    if pending and pending[0] == key and now - pending[1] <= CONFIRM_S:
        return True, None
    return False, (key, now)


def main(argv=None):
    p = argparse.ArgumentParser(description="Máy Dell: xem màn hình Mac qua Wi-Fi, bấm phím điều khiển cánh tay qua Bluetooth HC-05")
    p.add_argument("--mac", required=True, help="Đường dẫn main.py in ra trên Mac, VD http://192.168.1.5:8000/")
    p.add_argument("--port", required=True, help="Cổng COM Bluetooth (Outgoing) của HC-05, VD COM5")
    args = p.parse_args(argv)

    bt = serial.Serial(args.port, 9600, write_timeout=1)  # HC-05 chạy 9600 baud như firmware
    view = MacView(args.mac)
    note, pending = "", None  # Dòng nhắc trên cùng; phím H đang chờ bấm lần 2
    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    while True:
        screen = view.frame if view.frame is not None else np.zeros((650, 1280, 3), np.uint8)
        bar = np.full((44, screen.shape[1], 3), 30, np.uint8)
        text = note or ("Bam A D W S I K J L H de dieu khien, Q de thoat" if view.frame is not None
                        else "Dang cho anh tu Mac (cung Wi-Fi chua? main.py dang chay?)")
        cv2.putText(bar, text, (16, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (90, 220, 110), 2, cv2.LINE_AA)
        cv2.imshow(WINDOW, np.vstack([bar, screen]))
        key = cv2.waitKey(15) & 0xFF
        if cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
            break  # Đóng cửa sổ bằng nút X
        ch = chr(key).lower()
        if ch == "q" or key == 27:
            break
        if ch == "r":
            note = "R (chup dich): bam tren ban phim Mac"
        elif ch in SERVO_KEYS:
            ok, pending = confirm(ch, pending, time.time())
            if ok:
                bt.write(ch.encode())
                note = f"Da gui {ch.upper()}"
            else:
                note = f"Bam {ch.upper()} lan nua trong 2 giay de {CONFIRM_KEYS[ch]}"
    bt.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
