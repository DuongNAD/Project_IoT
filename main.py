#!/usr/bin/env python3
"""
Hỗ trợ điều khiển cánh tay robot 4 servo bằng 2 camera: chỉ cho biết BẤM PHÍM GÌ, MẤY LẦN, TRÁI / PHẢI BAO NHIÊU ĐỘ để đầu kẹp tới vật.

  uv run python main.py --port /dev/cu.usbmodem1101    cam TREN = camera 0, cam NGANG = camera 1, Arduino ở cổng đã ghi
  uv run python main.py                                 không ghi --port: chạy mô phỏng, không gửi phím xuống robot

Các phần nối nhau:  camera -> vision.py (vật nằm ở đâu) -> control.py (khối điều khiển: bấm phím gì) -> success.py (khối success: đã tới chưa) -> screen.py (hiện lên màn hình)

NÓI KHI BỊ HỎI FILE NÀY: "main.py là file chạy chính, nó không tự tính gì. Nó nối các phần lại thành một vòng lặp:
mỗi khung hình đọc 2 camera, đưa ảnh cho vision tìm vật, đưa vật cho control tính lệnh bấm phím,
đưa lệnh cho success xét xong chưa, rồi vẽ màn hình và gửi màn hình sang laptop qua Wi-Fi."
"""

import argparse
import sys

import cv2

from cameras import Camera
from control import Control
from screen import SCREEN_WINDOW, build_screen
from success import Success
from vision import Vision, draw_target

HELP_TEXT = """💡 Làm theo lệnh to ở giữa màn hình (bấm phím trên cửa sổ video):
   A / D                 : xoay đế sang TRÁI / PHẢI, mỗi lần 2°
   W / S                 : nâng / hạ vai, mỗi lần 2°          I / K : khuỷu lên / xuống, mỗi lần 2°
   H                     : về Home (0/90/90/95)
   J / L                 : mở / khép kẹp, mỗi lần 5° (kẹp không tính vào thành công)
   R                     : chụp vị trí vật làm đích, tính góc cần tới một lần (vật bị dời thì bấm R lại)"""


def parse_args(argv=None):
    """
    TÁC DỤNG: đọc tham số dòng lệnh: --top (cam TRÊN), --side (cam NGANG), --port (cổng USB Arduino).
    NÓI: "Không ghi --port thì chạy mô phỏng: Mac tự cộng trừ góc, không gửi gì xuống robot."
    """
    p = argparse.ArgumentParser(description="Điều khiển cánh tay robot 4 servo bằng 2 camera: lệnh bấm phím + kết luận đã tới chưa")
    source_help = "chỉ số camera OpenCV (0, 1, 2...) hoặc ảnh .png / .jpg để chạy thử"
    p.add_argument("--top", default="0", metavar="NGUON", help=f"Cam TREN (nhìn từ trên xuống): {source_help}")
    p.add_argument("--side", default="1", metavar="NGUON", help=f"Cam NGANG: {source_help}")
    p.add_argument("--port", default=None, help="Cổng USB của Arduino, VD /dev/cu.usbmodem1101 (macOS) hoặc COM3 (Windows); bỏ trống = mô phỏng")
    return p.parse_args(argv)


class App:
    """
    TÁC DỤNG: gom mọi phần (2 camera, vision, control, success) vào một chỗ và chạy vòng lặp chính.
    NÓI: "App giữ các khối; mỗi khung hình gọi render() một lần."
    """

    def __init__(self, args):
        """TÁC DỤNG: tạo các khối một lần lúc khởi động: 2 camera, Vision, Control (mở cổng USB nếu có --port), Success."""
        if args.port is None:
            print("ℹ️ Chưa ghi --port: chạy mô phỏng, phím không xuống robot")
        self.cam_side = Camera(args.side, "NGANG")
        self.cam_top = Camera(args.top, "TREN")
        self.vision = Vision()                  # Vision: tờ giấy + vật nằm ở đâu
        self.control = Control(port=args.port)  # Khối điều khiển: bấm phím gì
        self.success = Success()                # Khối success: đã tới chưa

    # ------------------------------------------------------------------ hiển thị
    def _frame(self, cam, mode):
        """
        TÁC DỤNG: lấy 1 ảnh từ camera rồi đưa cho vision.py (dò tờ giấy, tìm vật, vẽ lưới).
        VÀO: cam = camera nào; mode = "topdown" (cam TRÊN) hoặc "side" (cam NGANG).   RA: ảnh đã vẽ.
        NÓI: "Mất hình thì hiện ô 'đang chờ tín hiệu' và xoá vật cũ, để không gợi ý theo dữ liệu đã cũ."
        """
        raw = cam.get_raw_frame()
        if raw is None:
            if mode == "topdown":
                self.vision.objects = []  # Không có hình thì không gợi ý theo vật đã thấy từ trước
            return cam.waiting_image()
        return self.vision.process_frame(raw, mode=mode)

    def _with_target(self, annotated, mode, plan):
        """TÁC DỤNG: vẽ thêm vòng 'DICH' quanh chỗ vật lúc bấm R. Chưa bấm R hoặc chưa có lưới toạ độ thì để nguyên ảnh."""
        H_cm2px = self.vision.sheets[mode].H_cm2px
        if H_cm2px is None or plan.target_cm is None or annotated.ndim != 3:
            return annotated
        draw_target(annotated, H_cm2px, plan.target_cm)
        return annotated

    def render(self):
        """
        TÁC DỤNG: MỘT khung hình của cả hệ thống, đây là hàm quan trọng nhất của main.py.
        RA: (ảnh màn hình, Plan của control, Result của success).
        NÓI: "Đúng 5 bước trên sơ đồ luồng dữ liệu: đọc ảnh 2 camera -> vision tìm vật -> control.update ra Plan
        (bấm phím gì) -> success.update ra Result (xong chưa) -> build_screen ghép thành màn hình."
        """
        left, right = self._frame(self.cam_side, "side"), self._frame(self.cam_top, "topdown")  # Bước 1 + 2: đọc ảnh, tìm vật
        plan = self.control.update(self.vision.objects)  # Bước 3, khối điều khiển: vật ở đâu -> góc cần tới -> bấm phím gì
        result = self.success.update(plan)                # Bước 4, khối success: đã tới chưa
        titles = (f"CAM NGANG: {self.cam_side.label}", f"CAM TREN: {self.cam_top.label} (nhin tu tren)")
        screen = build_screen(self._with_target(left, "side", plan), self._with_target(right, "topdown", plan), plan, result, titles=titles)  # Bước 5
        return screen, plan, result

    # ------------------------------------------------------------------ phím
    def lock_target(self):
        """
        TÁC DỤNG: phím R: nhờ control.py chốt vật gần đế nhất làm đích và tính góc cần tới một lần.
        NÓI: "Chỉ tính một lần vì lúc cánh tay di chuyển nó có thể che vật; vật bị dời thì bấm R lại."
        """
        state = self.control.lock_target()
        print({"locked": "📌 Đã chụp đích: góc cần tới tính một lần theo vị trí vật lúc này, không theo camera nữa",
               "no_target": "⚠️ Camera chưa thấy vật nên chưa chụp được đích: đặt vật có màu lên tờ giấy rồi bấm R"}[state])
        return state

    def handle_key(self, key):
        """
        TÁC DỤNG: xử lý phím bấm trên bàn phím Mac. Trả về False khi cần thoát (ESC).
        NÓI: "Phím di chuyển (W A S D I K J L H) gửi xuống Arduino qua USB; R chốt đích; ESC thoát."
        """
        if key == 27:  # 27 = mã phím ESC
            return False
        if key < 0 or key == 255:  # 255 = không có phím nào được bấm trong lần chờ này
            return True
        if self.control.press(chr(key & 0xFF)):
            pass  # Phím điều khiển servo: đã gửi xuống Arduino
        elif key in (ord("r"), ord("R")):
            self.lock_target()
        return True

    # ------------------------------------------------------------------ chạy
    def run(self):
        """
        TÁC DỤNG: vòng lặp chính, chạy tới khi bấm ESC hoặc đóng cửa sổ.
        NÓI: "Mỗi vòng: render() ra màn hình -> hiện lên Mac -> gửi sang laptop qua Wi-Fi ->
        nhận các phím laptop báo về để Mac cộng trừ góc -> đọc phím trên bàn phím Mac."
        """
        print(HELP_TEXT)
        from share import start as start_share
        share = start_share()  # Laptop (remote.py) xem màn hình qua Wi-Fi và báo phím; phím tới cánh tay qua Bluetooth HC-05; R bấm trên Mac
        cv2.namedWindow(SCREEN_WINDOW)
        try:
            while True:
                screen, _, _ = self.render()          # 1 khung hình
                cv2.imshow(SCREEN_WINDOW, screen)     # Hiện trên Mac
                share.update(screen)                  # Laptop lấy ảnh này qua Wi-Fi
                for ch in share.pop_keys():  # Laptop báo phím qua Wi-Fi: Mac cộng / trừ góc
                    self.control.count_key(ch)
                key = cv2.waitKey(5) & 0xFF  # Chờ 5 ms xem bàn phím Mac có phím nào không
                if cv2.getWindowProperty(SCREEN_WINDOW, cv2.WND_PROP_VISIBLE) < 1 or not self.handle_key(key):
                    break  # Đóng cửa sổ hoặc bấm ESC thì thoát vòng lặp
        finally:
            share.close()

    def close(self):
        """TÁC DỤNG: giải phóng cả 2 camera, cổng Serial và đóng cửa sổ khi thoát."""
        self.control.release()
        self.cam_side.release()
        self.cam_top.release()
        cv2.destroyAllWindows()


def main(argv=None):
    """TÁC DỤNG: điểm bắt đầu chương trình: đọc tham số -> tạo App -> chạy vòng lặp -> luôn dọn dẹp khi thoát (kể cả khi lỗi)."""
    args = parse_args(argv)
    try:
        # In log ngay cả khi chạy qua pipe (| tee); terminal Windows (cp1252) không in được emoji: thay bằng '?' thay vì sập chương trình
        sys.stdout.reconfigure(line_buffering=True, errors="replace")
    except (AttributeError, ValueError):
        pass
    app = App(args)
    try:
        app.run()
    finally:
        app.close()


if __name__ == "__main__":
    main()
