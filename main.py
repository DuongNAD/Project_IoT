#!/usr/bin/env python3
"""
Hỗ trợ điều khiển cánh tay robot 4 servo bằng 2 camera: chỉ cho biết BẤM PHÍM GÌ, MẤY LẦN, TRÁI / PHẢI BAO NHIÊU ĐỘ để đầu kẹp tới vật.

  uv run python main.py            cam TREN = OBSBOT, cam NGANG = camera MacBook
  uv run python main.py --help     đổi nguồn camera, chạy không cần robot / camera...

Các phần nối nhau:  camera -> vision.py (vật nằm ở đâu) -> control.py (NHÓM 1: bấm phím gì) -> success.py (NHÓM 2: đã tới chưa) -> screen.py (hiện lên màn hình)
Điều khiển từ xa:   phone.py chia sẻ màn hình qua Wi-Fi; máy Dell chạy remote.py để xem và bấm phím qua Bluetooth HC-05
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime

import cv2

from calibration import apply_calibration, heading_toward, store_base_pose
from cameras import Camera, list_camera_names
from control import ARM_CONFIG, Control, predict_tip
from phone import PhoneServer, qr_text, status_of, stored_pin
from screen import CAM_H, CAM_W, SCREEN_WINDOW, build_screen
from success import Success
from vision import Vision, draw_target, px_to_cm

CAPTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "captures")  # Ảnh chụp (phím C), nằm cạnh main.py
PIN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".phone_pin")  # Mã 6 số của đường dẫn cho Dell / điện thoại, giữ nguyên giữa các lần chạy

HELP_TEXT = """💡 Làm theo lệnh to ở giữa màn hình (bấm phím trên cửa sổ video):
   A / D                 : xoay đế sang PHẢI / TRÁI (nhìn theo cam NGANG), mỗi lần 2°
   W / S                 : nâng / hạ vai, mỗi lần 2°          I / K : khuỷu lên / xuống, mỗi lần 2°
   H                     : về Home (90/90/90)                  X / Z : cho servo kẹp / cả 4 servo nghỉ (ngắt xung)
   J / L                 : mở / khép kẹp, mỗi lần 5° (kẹp không tính vào thành công)
   TAB                   : đổi vật mục tiêu
   B                     : hiệu chỉnh đế robot (click vào trục xoay đế trên hình cam TREN)      U : dò lại 4 mã ArUco
   C                     : chụp ảnh gốc 2 camera vào captures/                                  Q : thoát
   Máy Dell / điện thoại : xem đường dẫn in ở trên (cùng Wi-Fi): Dell chạy remote.py, điện thoại mở bằng trình duyệt"""


def slug(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Điều khiển cánh tay robot 4 servo bằng 2 camera: lệnh bấm phím + kết luận đã tới chưa")
    source_help = "obsbot | mac | 0,1,2... (chỉ số OpenCV) | một phần tên camera | ảnh .png / .jpg để chạy thử"
    p.add_argument("--top", default="obsbot", metavar="NGUON", help=f"Cam TREN (nhìn từ trên xuống): {source_help}")
    p.add_argument("--side", default="mac", metavar="NGUON", help=f"Cam NGANG: {source_help}")
    p.add_argument("--no-serial", action="store_true", help="Không mở cổng USB Arduino (chạy mô phỏng, không gửi phím xuống robot)")
    p.add_argument("--no-phone", action="store_true", help="Không chia sẻ màn hình qua Wi-Fi (cho máy Dell / điện thoại)")
    p.add_argument("--phone-port", type=int, default=8000, help="Cổng chia sẻ màn hình qua Wi-Fi (mặc định 8000; khác mạng thì: ngrok http 8000)")
    p.add_argument("--list-cameras", action="store_true", help="In danh sách camera theo chỉ số OpenCV rồi thoát")
    p.add_argument("--headless", action="store_true", help="Không mở cửa sổ: chạy --seconds giây rồi lưu ảnh + summary.json vào --dump-dir")
    p.add_argument("--seconds", type=float, default=12.0, help="Thời gian chạy của --headless (giây)")
    p.add_argument("--dump-dir", default=None, help="Thư mục lưu kết quả --headless (mặc định captures/headless)")
    return p.parse_args(argv)


def start_phone(port):
    """Chia sẻ màn hình qua Wi-Fi (cho remote.py trên máy Dell và trang web dự phòng), in đường dẫn + mã QR. None nếu cổng bận."""
    try:
        phone = PhoneServer(port, pin=stored_pin(PIN_FILE))
    except OSError as e:
        print(f"⚠️ Không chia sẻ được màn hình ở cổng {port} ({e}): chạy lại với --phone-port khác")
        return None
    url = phone.url()
    print(f"🖥️  Chạy trên máy Dell (không chạy trên Mac): python remote.py --mac {url}")
    print(f"📱 Điện thoại / trình duyệt (dự phòng): mở {url}  hoặc quét mã QR dưới đây")
    print(qr_text(url))
    print(f"   Khác mạng: chạy  ngrok http {phone.port}  rồi dùng đường dẫn ngrok + /{phone.pin}/")
    print(f"   Mã {phone.pin} giữ nguyên mỗi lần chạy (đổi mạng thì chỉ IP đổi); muốn đổi mã: xóa tệp .phone_pin")
    return phone


def report_cameras():
    """In danh sách camera theo thứ tự chỉ số của OpenCV (số dùng được cho --top / --side)."""
    listing = ", ".join(f"[{i}] {n}" for i, n in enumerate(list_camera_names())) or "(không thấy camera nào)"
    print(f"📷 Camera theo thứ tự chỉ số OpenCV: {listing}")


def screen_to_frame(x, y, frame_shape):
    """Điểm click (x, y) trong ô camera 640 x 360 của màn hình -> pixel trên khung gốc, None nếu rơi vào viền đen."""
    h, w = frame_shape[:2]
    k = min(CAM_W / w, CAM_H / h)
    fx, fy = (x - (CAM_W - round(w * k)) // 2) / k, (y - (CAM_H - round(h * k)) // 2) / k
    return (fx, fy) if 0 <= fx < w and 0 <= fy < h else None


def save_snapshots(cameras):
    """Lưu frame gốc của từng camera vào CAPTURE_DIR, chung một mốc thời gian để dễ ghép cặp ảnh."""
    os.makedirs(CAPTURE_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for cam in cameras:
        frame = cam.get_raw_frame()
        if frame is None:
            print(f"⚠️ Cam {cam.role}: chưa có tín hiệu, không chụp được")
            continue
        path = os.path.join(CAPTURE_DIR, f"{stamp}_cam_{slug(cam.role)}_{slug(cam.label)}.jpg")
        if cv2.imwrite(path, frame):
            print(f"📸 Đã lưu {path}")
        else:
            print(f"⚠️ Không ghi được {path}")


class App:
    """Vòng lặp chính: 2 camera -> vision (vật ở đâu) -> control (bấm phím gì) -> success (đã tới chưa) -> màn hình."""

    def __init__(self, args):
        self.args = args
        if apply_calibration(ARM_CONFIG):
            print(
                f"📐 Đã nạp hiệu chỉnh từ calibration.json: đế ({ARM_CONFIG['base_x_cm']:.1f}, {ARM_CONFIG['base_y_cm']:.1f}) cm, "
                f"hướng {ARM_CONFIG['base_heading_deg']:.0f}°, góc chuẩn vai {ARM_CONFIG['theta2_at_90_deg']:.1f}°, khuỷu {ARM_CONFIG['theta3_at_90_deg']:.1f}°"
            )
        report_cameras()
        self.cam_side = Camera(args.side, "NGANG")
        self.cam_top = Camera(args.top, "TREN")
        self.vision = Vision()                                     # Vision: tờ giấy + vật nằm ở đâu
        self.control = Control(serial_enabled=not args.no_serial)  # NHÓM 1: bấm phím gì
        self.success = Success()                                   # NHÓM 2: đã tới chưa
        self.phone = None if (args.no_phone or args.headless) else start_phone(args.phone_port)  # Chia sẻ màn hình qua Wi-Fi
        self.calib_base = False   # Đang chờ click vào trục xoay đế robot (phím B)
        self.cache = {}           # Khung đã xử lý gần nhất của mỗi góc nhìn, dùng lại khi camera chưa có khung mới
        self.top_shape = None     # Kích thước khung gốc cam TREN, để đổi vị trí click chuột thành pixel ảnh gốc

    # ------------------------------------------------------------------ hiển thị
    def _frame(self, cam, mode):
        """Khung đã vẽ lớp phủ của một camera. Chỉ xử lý nặng (ArUco + tìm vật) khi camera có khung mới."""
        cached = self.cache.get(mode)
        if cam.stalled() or cached is None or cached["id"] != cam.frame_id:
            frame_id, raw = cam.frame_id, cam.get_raw_frame()
            if raw is None:  # Chưa có hình hoặc mất tín hiệu: hiện "Dang cho tin hieu" thay vì ảnh đứng hình, quên vật cũ
                self.cache.pop(mode, None)
                if mode == "topdown":
                    self.top_shape, self.vision.objects = None, []
                return cam.waiting_image()
            cached = self.cache[mode] = {"id": frame_id, "annotated": self.vision.process_frame(raw, mode=mode)}
        if mode == "topdown":
            self.top_shape = cached["annotated"].shape
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
        plan = self.control.update(self.vision.objects)  # NHÓM 1: vật ở đâu -> góc cần tới -> bấm phím gì
        result = self.success.update(plan)                # NHÓM 2: đã tới chưa
        titles = (f"CAM NGANG: {self.cam_side.label}", f"CAM TREN: {self.cam_top.label} (nhin tu tren)")
        screen = build_screen(self._with_target(left, "side", plan), self._with_target(right, "topdown", plan), plan, result, titles=titles)
        if self.calib_base:
            y = CAM_H - 8
            cv2.rectangle(screen, (0, y - 26), (screen.shape[1], y + 6), (0, 0, 0), -1)
            cv2.putText(screen, "HIEU CHINH DE: CLICK VAO TRUC XOAY DE ROBOT TREN HINH CAM TREN (ESC = huy)",
                        (12, y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 255, 255), 2, cv2.LINE_AA)
        if self.phone is not None:
            self.phone.update(status_of(plan, result), screen)  # Gửi màn hình + trạng thái cho máy Dell / điện thoại
        return screen, plan, result

    # ------------------------------------------------------------------ chuột: hiệu chỉnh đế robot
    def on_mouse(self, event, x, y, flags, window):
        if event != cv2.EVENT_LBUTTONDOWN or not self.calib_base:
            return
        px = None
        if self.top_shape is not None and x >= CAM_W and y < CAM_H:
            px = screen_to_frame(x - CAM_W, y, self.top_shape)  # Nửa phải của ô camera là cam TREN
        if px is None:
            print("⚠️ Hãy click vào hình cam TREN (nửa bên phải)")
            return
        H_px2cm = self.vision.sheets["topdown"].H_px2cm
        if H_px2cm is None:
            print("⚠️ Cam TREN chưa thấy ≥ 2 mã ArUco 0-3 nên chưa tính được vị trí trên tờ giấy, chưa hiệu chỉnh được")
            return
        bx, by = px_to_cm(H_px2cm, *px)
        heading = heading_toward(bx, by)
        self.control.set_base_pose(bx, by, heading)
        store_base_pose(bx, by, heading)
        self.calib_base = False
        print(f"📐 Đã hiệu chỉnh đế robot: ({bx:.1f}, {by:.1f}) cm trên tờ giấy, hướng {heading:.0f}° (đã lưu calibration.json)")

    # ------------------------------------------------------------------ phím
    def handle_key(self, key):
        """Xử lý phím; trả về False khi cần thoát."""
        if key in (ord("q"), ord("Q")):
            return False
        if key == 27 and self.calib_base:  # ESC
            self.calib_base = False
            print("↩️ Đã hủy hiệu chỉnh đế robot")
        elif key < 0 or key == 255:
            return True
        elif self.control.press(chr(key & 0xFF)):
            pass  # Phím điều khiển servo
        elif key == 9 or key in (ord("v"), ord("V")):  # TAB
            self.control.next_target()
        elif key in (ord("b"), ord("B")):
            self.calib_base = not self.calib_base
            print("📐 Click vào trục xoay đế robot trên hình cam TREN..." if self.calib_base else "↩️ Đã hủy hiệu chỉnh đế robot")
        elif key in (ord("u"), ord("U")):
            self.vision.reset_sheet()
            self.cache.clear()
            print("🔄 Đã quên vị trí các mã ArUco, đang dò lại tờ giấy")
        elif key in (ord("c"), ord("C")):
            save_snapshots([self.cam_side, self.cam_top])
        return True

    # ------------------------------------------------------------------ chạy
    def run(self):
        print("✅ Đang mở màn hình: 2 camera + lệnh bấm phím (phần 1) + kết luận đã tới chưa (phần 2)...")
        print(HELP_TEXT)
        cv2.namedWindow(SCREEN_WINDOW)
        cv2.setMouseCallback(SCREEN_WINDOW, self.on_mouse, SCREEN_WINDOW)
        while True:
            screen, _, _ = self.render()
            cv2.imshow(SCREEN_WINDOW, screen)
            for key in self.phone.pop_keys() if self.phone is not None else []:
                self.control.press(key)  # Nút bấm trên trang web dự phòng, gửi như phím bàn phím
            if not self.handle_key(cv2.waitKey(5) & 0xFF):
                break

    def summary(self, plan, result):
        """Tóm tắt trạng thái hệ thống (dùng cho --headless và khi cần gỡ lỗi)."""
        def sheet_info(mode):
            sheet = self.vision.sheets[mode]
            return {"co_luoi": sheet.H_px2cm is not None, "so_ma_thay": sheet.n_seen, "so_ma_da_nho": len(sheet.markers)}

        return {
            "camera": {
                "TREN": {"nhan": self.cam_top.label, "nguon": str(self.cam_top.source), "kich_thuoc": self.top_shape[:2][::-1] if self.top_shape else None},
                "NGANG": {"nhan": self.cam_side.label, "nguon": str(self.cam_side.source)},
            },
            "to_giay": {"cam_tren": sheet_info("topdown"), "cam_ngang": sheet_info("side")},
            "de_robot": {k: ARM_CONFIG[k] for k in ("base_x_cm", "base_y_cm", "base_heading_deg")},
            "vat_the": [{"ten": o["name"], "x_cm": round(o["x_cm"], 1), "y_cm": round(o["y_cm"], 1)} for o in self.control.objects],
            "nhom_1_dieu_khien": {
                "vat_muc_tieu": plan.target_name,
                "vi_tri_cm": [round(v, 1) for v in plan.target_cm] if plan.target_cm else None,
                "trong_tam_voi": bool(plan.reachable),
                "servo_hien_tai": plan.now,
                "servo_can_toi": plan.goal,
                "lenh": [{"servo": m.label, "phim": m.key, "so_lan": m.steps, "huong": m.words, "do": m.degrees} for m in plan.moves],
            },
            "nhom_2_success": {"trang_thai": result.state, "xong": bool(result.done), "con_lai_lan_bam": result.remaining, "servo_dung": result.joints_ok},
        }

    def run_headless(self):
        """Không mở cửa sổ: chạy args.seconds giây rồi lưu ảnh màn hình và summary.json."""
        print(f"🧪 Chạy không cửa sổ {self.args.seconds:.0f} giây...")
        end = time.time() + self.args.seconds
        screen = plan = result = None
        loops = 0
        while time.time() < end:
            screen, plan, result = self.render()
            loops += 1
            time.sleep(0.04)
        out = self.args.dump_dir or os.path.join(CAPTURE_DIR, "headless")
        os.makedirs(out, exist_ok=True)
        cv2.imwrite(os.path.join(out, "dual_view.png"), screen)
        for mode, tag in (("side", "cam_ngang"), ("topdown", "cam_tren")):
            cached = self.cache.get(mode)
            if cached is not None:
                cv2.imwrite(os.path.join(out, f"{tag}_annotated.jpg"), cached["annotated"])
        summary = self.summary(plan, result)
        summary["khung_xu_ly_moi_giay"] = {"cam_tren": round(self.cam_top.frame_id / self.args.seconds, 1),
                                          "cam_ngang": round(self.cam_side.frame_id / self.args.seconds, 1),
                                          "vong_lap": round(loops / self.args.seconds, 1)}
        with open(os.path.join(out, "summary.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        print(f"💾 Đã lưu kết quả vào {out}")

    def close(self):
        """Giải phóng cả 2 camera, cổng Serial, máy chủ Wi-Fi và đóng cửa sổ."""
        if self.phone is not None:
            self.phone.close()
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
    if args.list_cameras:
        report_cameras()
        return
    app = App(args)
    try:
        app.run_headless() if args.headless else app.run()
    finally:
        app.close()


if __name__ == "__main__":
    main()
