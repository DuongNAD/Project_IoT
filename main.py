#!/usr/bin/env python3
"""
Hỗ trợ điều khiển cánh tay robot 4 servo bằng 2 camera: chỉ cho biết BẤM PHÍM GÌ, MẤY LẦN, TRÁI / PHẢI BAO NHIÊU ĐỘ để đầu kẹp tới vật.

  uv run python main.py --port /dev/cu.usbmodem1101    cam TREN = camera 0, cam NGANG = camera 1, Arduino ở cổng đã ghi
  uv run python main.py                                 không ghi --port: chạy mô phỏng, không gửi phím xuống robot

Các phần nối nhau:  camera -> vision.py (vật nằm ở đâu) -> control.py (khối điều khiển: bấm phím gì) -> success.py (khối success: đã tới chưa) -> screen.py (hiện lên màn hình)
"""

import argparse
import sys

import cv2

from calibration import apply_calibration
from cameras import Camera
from control import ARM_CONFIG, Control, predict_tip
from screen import SCREEN_WINDOW, build_screen
from success import Success
from vision import Vision, draw_target

HELP_TEXT = """💡 Làm theo lệnh to ở giữa màn hình (bấm phím trên cửa sổ video):
   A / D                 : xoay đế sang PHẢI / TRÁI (nhìn theo cam NGANG), mỗi lần 2°
   W / S                 : nâng / hạ vai, mỗi lần 2°          I / K : khuỷu lên / xuống, mỗi lần 2°
   H                     : về Home (180/90/90)                 X / Z : cho servo kẹp / cả 4 servo nghỉ (ngắt xung)
   J / L                 : mở / khép kẹp, mỗi lần 5° (kẹp không tính vào thành công)
   R                     : chụp vị trí vật làm đích, tính góc cần tới một lần (vật bị dời thì bấm R lại)
   U                     : dò lại 4 mã ArUco (sau khi dời camera / tờ giấy)                       Q : thoát"""


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Điều khiển cánh tay robot 4 servo bằng 2 camera: lệnh bấm phím + kết luận đã tới chưa")
    source_help = "chỉ số camera OpenCV (0, 1, 2...) hoặc ảnh .png / .jpg để chạy thử"
    p.add_argument("--top", default="0", metavar="NGUON", help=f"Cam TREN (nhìn từ trên xuống): {source_help}")
    p.add_argument("--side", default="1", metavar="NGUON", help=f"Cam NGANG: {source_help}")
    p.add_argument("--port", default=None, help="Cổng USB của Arduino, VD /dev/cu.usbmodem1101 (macOS) hoặc COM3 (Windows); bỏ trống = mô phỏng")
    return p.parse_args(argv)


class App:
    """Vòng lặp chính: 2 camera -> vision (vật ở đâu) -> control (bấm phím gì) -> success (đã tới chưa) -> màn hình."""

    def __init__(self, args):
        if apply_calibration(ARM_CONFIG):
            print(
                f"📐 Đã nạp hiệu chỉnh từ calibration.json: đế ({ARM_CONFIG['base_x_cm']:.1f}, {ARM_CONFIG['base_y_cm']:.1f}) cm, "
                f"hướng {ARM_CONFIG['base_heading_deg']:.0f}°, góc chuẩn vai {ARM_CONFIG['theta2_at_90_deg']:.1f}°, khuỷu {ARM_CONFIG['theta3_at_90_deg']:.1f}°"
            )
        if args.port is None:
            print("ℹ️ Chưa ghi --port: chạy mô phỏng, phím không xuống robot")
        self.cam_side = Camera(args.side, "NGANG")
        self.cam_top = Camera(args.top, "TREN")
        self.vision = Vision()                  # Vision: tờ giấy + vật nằm ở đâu
        self.control = Control(port=args.port)  # Khối điều khiển: bấm phím gì
        self.success = Success()                # Khối success: đã tới chưa
        self.cache = {}  # Khung đã xử lý gần nhất của mỗi góc nhìn, dùng lại khi camera chưa có khung mới

    # ------------------------------------------------------------------ hiển thị
    def _frame(self, cam, mode):
        """Khung đã vẽ lớp phủ của một camera. Chỉ xử lý nặng (ArUco + tìm vật) khi camera có khung mới."""
        cached = self.cache.get(mode)
        if cam.stalled() or cached is None or cached["id"] != cam.frame_id:
            frame_id, raw = cam.frame_id, cam.get_raw_frame()
            if raw is None:  # Chưa có hình hoặc mất tín hiệu: hiện "Dang cho tin hieu" thay vì ảnh đứng hình, quên vật cũ
                self.cache.pop(mode, None)
                if mode == "topdown":
                    self.vision.objects = []
                return cam.waiting_image()
            cached = self.cache[mode] = {"id": frame_id, "annotated": self.vision.process_frame(raw, mode=mode)}
        return cached["annotated"]

    def _with_target(self, annotated, mode, plan):
        """Bản sao khung với vòng 'DICH' (chỗ vật) và dấu 'KEP' (chỗ đầu kẹp theo mô hình) vẽ trên mặt giấy."""
        H_cm2px = self.vision.sheets[mode].H_cm2px
        if H_cm2px is None or plan.target_cm is None or annotated is None or annotated.ndim != 3:
            return annotated
        out = annotated.copy()
        draw_target(out, H_cm2px, plan.target_cm, predict_tip(plan.now[:3])[:2])
        return out

    def render(self):
        """Dựng một khung màn hình: (ảnh màn hình, Plan của control, Result của success)."""
        left, right = self._frame(self.cam_side, "side"), self._frame(self.cam_top, "topdown")
        plan = self.control.update(self.vision.objects)  # Khối điều khiển: vật ở đâu -> góc cần tới -> bấm phím gì
        result = self.success.update(plan)                # Khối success: đã tới chưa
        titles = (f"CAM NGANG: {self.cam_side.label}", f"CAM TREN: {self.cam_top.label} (nhin tu tren)")
        screen = build_screen(self._with_target(left, "side", plan), self._with_target(right, "topdown", plan), plan, result, titles=titles)
        return screen, plan, result

    # ------------------------------------------------------------------ phím
    def lock_target(self):
        """Phím R: chụp vị trí vật gần đế nhất làm đích, tính góc cần tới một lần (vật bị dời thì bấm R lại)."""
        state = self.control.lock_target()
        print({"locked": "📌 Đã chụp đích: góc cần tới tính một lần theo vị trí vật lúc này, không theo camera nữa",
               "no_target": "⚠️ Camera chưa thấy vật nên chưa chụp được đích: đặt vật có màu lên tờ giấy rồi bấm R"}[state])
        return state

    def handle_key(self, key):
        """Xử lý phím; trả về False khi cần thoát."""
        if key in (ord("q"), ord("Q")):
            return False
        if key < 0 or key == 255:
            return True
        if self.control.press(chr(key & 0xFF)):
            pass  # Phím điều khiển servo
        elif key in (ord("r"), ord("R")):
            self.lock_target()
        elif key in (ord("u"), ord("U")):
            self.vision.reset_sheet()
            self.cache.clear()
            print("🔄 Đã quên vị trí các mã ArUco, đang dò lại tờ giấy")
        return True

    # ------------------------------------------------------------------ chạy
    def run(self):
        print("✅ Đang mở màn hình: 2 camera + lệnh bấm phím (phần 1) + kết luận đã tới chưa (phần 2)...")
        print(HELP_TEXT)
        from share import start as start_share  # Chia sẻ màn hình chỉ khi mở cửa sổ
        share = start_share()  # Máy Dell xem màn hình này qua Wi-Fi (remote.py), phím đi qua Bluetooth HC-05; R bấm trên Mac
        cv2.namedWindow(SCREEN_WINDOW)
        try:
            while True:
                screen, _, _ = self.render()
                cv2.imshow(SCREEN_WINDOW, screen)
                if share is not None:
                    share.update(screen)
                if not self.handle_key(cv2.waitKey(5) & 0xFF):
                    break
        finally:
            if share is not None:
                share.close()

    def close(self):
        """Giải phóng cả 2 camera, cổng Serial và đóng cửa sổ."""
        self.control.release()
        self.cam_side.release()
        self.cam_top.release()
        cv2.destroyAllWindows()


def main(argv=None):
    args = parse_args(argv)
    try:
        # Chạy qua pipe (| tee) vẫn thấy log ngay, không đợi đầy bộ đệm. Terminal Windows (cp1252) không in được emoji:
        # thay bằng '?' thay vì làm chương trình sập
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
