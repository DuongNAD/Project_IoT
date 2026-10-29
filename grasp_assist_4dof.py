#!/usr/bin/env python3
"""
Bộ tính toán Động học ngược (IK 4-DOF), Giao tiếp USB Serial Arduino,
Nhận diện ArUco (Đế ID 4, Kẹp ID 5-6, Vật ID 10-29) kết hợp YOLO11,
Máy trạng thái 5 bước gắp & Xác nhận gắp (S1 Cam ngang + S2 Cam trên),
và Thanh giao diện Gợi ý bấm phím (WASD / IK / JL) cho Cánh tay Robot 4 Servo.
"""

from collections import deque
import csv
from datetime import datetime
import glob
import json
import math
import os
import re
import threading
import time
import cv2
import numpy as np

try:
    import serial
except ImportError:
    serial = None


# ==============================================================================
# 1. CẤU HÌNH HÌNH HỌC CÁNH TAY 4 SERVO (MG996R + PCA9685)
#    Nhóm chỉ cần lấy thước đo 4 thông số thực tế dưới đây (đơn vị: mm)
# ==============================================================================
ARM_CONFIG = {
    "d1_mm": 70.0,      # Chiều cao từ mặt bàn đến trục khớp Vai (mm)
    "L2_mm": 105.0,     # Chiều dài khâu Vai -> Khuỷu (mm)
    "L3_mm": 100.0,     # Chiều dài khâu Khuỷu -> Cổ tay/Giá kẹp (mm)
    "L4_r_mm": 65.0,    # Độ vươn ngang từ khớp giá kẹp tới tâm 2 ngón kẹp (mm)
    "L4_z_mm": 25.0,    # Độ trễ dọc từ khớp giá kẹp xuống tâm 2 ngón kẹp (mm)
    # Vị trí mặc định của trục xoay Đế Robot trên hệ tọa độ tờ giấy A4 (29.7 x 21.0 cm)
    # Mặc định đặt ở chính giữa mép dưới tờ A4 (X = 14.85 cm, Y = 22.0 cm), hướng nhìn lên (-Y)
    "base_x_cm": 14.85,
    "base_y_cm": 22.0,
    # Góc khớp chuẩn (độ) khi 3 servo Đế, Vai, Khuỷu đang ở vị trí mặc định 90° của code Arduino
    "theta2_at_90_deg": 45.0,   # Khi angleShoulder = 90° thì khâu L2 nghiêng +45° so với phương ngang
    "theta3_at_90_deg": -45.0,  # Khi angleElbow = 90° thì khâu L3 gập -45° so với khâu L2
}

# Giới hạn an toàn và bước nhảy khớp 100% với code Arduino của bạn
SERVO_STEP_DEG = 5
SERVO_LIMITS = {
    "base": (0, 180, 90),       # Kênh 0: Đế (a: +5° Trái, d: -5° Phải)
    "shoulder": (25, 155, 90),  # Kênh 1: Vai (w: +5° Lên, s: -5° Xuống)
    "elbow": (25, 155, 90),     # Kênh 2: Khuỷu (i: +5° Gập lên, k: -5° Gập xuống)
    "grip": (95, 175, 95),      # Kênh 3: Kẹp (j: -5° Mở ra, l: +5° Kẹp vào)
}

# Bảng kích thước vật thể dán mã ArUco (ID 10 -> 29) theo kế hoạch (đơn vị: mm)
OBJECT_SPECS = {
    10: {"name": "Hop_Vuong_ID10", "w_mm": 40.0, "l_mm": 40.0, "h_mm": 40.0},
    11: {"name": "Hop_Xanh_ID11", "w_mm": 35.0, "l_mm": 50.0, "h_mm": 35.0},
    12: {"name": "Hop_Do_ID12", "w_mm": 30.0, "l_mm": 60.0, "h_mm": 40.0},
    13: {"name": "Khoi_Tru_ID13", "w_mm": 35.0, "l_mm": 35.0, "h_mm": 50.0},
}
DEFAULT_OBJ_SPEC = {"name": "Vat_ArUco", "w_mm": 35.0, "l_mm": 35.0, "h_mm": 40.0}

# Đường dẫn file log kết quả gắp theo đúng tài liệu Kế hoạch
LOG_CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "attempts.csv")

# Biểu ngữ kết quả (THÀNH CÔNG / THẤT BẠI / ĐÃ RESET) tự tắt sau số giây này để không che gợi ý của lần gắp tiếp theo
BANNER_SECONDS = 8.0


# ==============================================================================
# 2. ĐỘNG HỌC THUẬN (FK) & ĐỘNG HỌC NGƯỢC (IK) CHO CÁNH TAY 4 SERVO
# ==============================================================================
def fk_4dof_joint(theta1_deg, theta2_deg, theta3_deg, cfg=None):
    """
    Động học thuận (Forward Kinematics) từ góc khớp hình học (theta1, theta2, theta3) (độ)
    sang tọa độ điểm kẹp (x, y, z) (mm) trong hệ tọa độ gốc Robot:
      +x: hướng thẳng về phía trước mặt đế robot
      +y: hướng sang bên trái đế robot
      +z: hướng thẳng đứng lên trên từ mặt bàn
    """
    c = cfg or ARM_CONFIG
    t1 = math.radians(theta1_deg)
    t2 = math.radians(theta2_deg)
    t23 = math.radians(theta2_deg + theta3_deg)

    r_w = c["L2_mm"] * math.cos(t2) + c["L3_mm"] * math.cos(t23)
    z_w = c["L2_mm"] * math.sin(t2) + c["L3_mm"] * math.sin(t23)

    r = r_w + c["L4_r_mm"]
    z = c["d1_mm"] + z_w - c["L4_z_mm"]
    x = r * math.cos(t1)
    y = r * math.sin(t1)
    return x, y, z


def ik_4dof_joint(x_mm, y_mm, z_mm, cfg=None):
    """
    Động học ngược giải tích (Analytical Inverse Kinematics) cho cánh tay 4 bậc tự do.
    Trả về dict:
      - reachable (bool): Điểm (x, y, z) có nằm trong tầm với hình học không
      - theta1_deg, theta2_deg, theta3_deg: Góc khớp hình học (độ)
      - r_mm: Khoảng cách ngang từ tâm đế đến vật (mm)
      - move_closer_mm: Số mm cần dịch vật lại gần đế nếu ngoài tầm với
    """
    c = cfg or ARM_CONFIG
    L2 = c["L2_mm"]
    L3 = c["L3_mm"]

    r = math.hypot(x_mm, y_mm)
    theta1_deg = math.degrees(math.atan2(y_mm, x_mm)) if r > 1e-6 else 0.0

    r_w = max(5.0, r - c["L4_r_mm"])
    z_w = (z_mm + c["L4_z_mm"]) - c["d1_mm"]

    dist_sq = r_w * r_w + z_w * z_w
    dist = math.sqrt(dist_sq)
    max_reach = L2 + L3
    min_reach = abs(L2 - L3)

    D = (dist_sq - L2 * L2 - L3 * L3) / (2.0 * L2 * L3)
    reachable = abs(D) <= 1.0
    move_closer_mm = max(0.0, dist - (max_reach - 2.0)) if dist > max_reach else 0.0

    # Kẹp D trong [-1, 1] để luôn tính ra bộ góc gần mục tiêu nhất ngay cả khi hơi quá tầm
    D_clamped = max(-1.0, min(1.0, D))
    # Nghiệm khuỷu hướng lên (elbow-up): sin(theta3) <= 0
    theta3_rad = math.atan2(-math.sqrt(max(0.0, 1.0 - D_clamped * D_clamped)), D_clamped)
    theta2_rad = math.atan2(z_w, r_w) - math.atan2(
        L3 * math.sin(theta3_rad), L2 + L3 * math.cos(theta3_rad)
    )

    return {
        "reachable": reachable and (r >= c["L4_r_mm"] + min_reach * 0.5),
        "theta1_deg": theta1_deg,
        "theta2_deg": math.degrees(theta2_rad),
        "theta3_deg": math.degrees(theta3_rad),
        "r_mm": r,
        "move_closer_mm": move_closer_mm,
    }


def joint_to_arduino_servo(theta1_deg, theta2_deg, theta3_deg, grip_open_mm=45.0, close_grip=False, cfg=None):
    """
    Chuyển góc khớp hình học (theta1, theta2, theta3) và trạng thái kẹp sang
    góc lệnh 4 servo trong code Arduino: [angleBase, angleShoulder, angleElbow, angleGrip]
    và làm tròn theo bước STEP = 5° để khớp tuyệt đối với phím bấm WASD + IK + JL.
    """
    c = cfg or ARM_CONFIG

    # 1. Đế (Kênh 0): 90° là hướng thẳng phía trước; 'a' (+5°) quay Trái (+theta1), 'd' (-5°) quay Phải (-theta1)
    raw_base = 90.0 + theta1_deg
    # 2. Vai (Kênh 1): 90° ứng với góc nghiêng chuẩn theta2_at_90_deg; 'w' (+5°) nâng lên, 's' (-5°) hạ xuống
    raw_shoulder = 90.0 + (theta2_deg - c["theta2_at_90_deg"])
    # 3. Khuỷu (Kênh 2): 90° ứng với góc gập chuẩn theta3_at_90_deg; 'i' (+5°) nâng lên, 'k' (-5°) hạ xuống
    raw_elbow = 90.0 + (theta3_deg - c["theta3_at_90_deg"])

    # 4. Kẹp (Kênh 3): 95° là mở rộng nhất ('j' giảm góc), 175° là kẹp chặt nhất ('l' tăng góc)
    if close_grip:
        raw_grip = 165.0
    else:
        # Nội suy độ mở kẹp (mm) -> góc servo trong khoảng [95, 135]
        # Mở 60mm -> 95°, Mở 20mm -> 130°
        ratio = max(0.0, min(1.0, (60.0 - grip_open_mm) / 40.0))
        raw_grip = 95.0 + ratio * 30.0

    def snap_and_clamp(val, lim_key):
        lo, hi, _ = SERVO_LIMITS[lim_key]
        clamped = max(lo, min(hi, val))
        # Làm tròn về bội số của STEP = 5° tính từ góc khởi tạo (90° hoặc 95° đều chia hết cho 5)
        snapped = int(round(clamped / SERVO_STEP_DEG) * SERVO_STEP_DEG)
        return max(lo, min(hi, snapped))

    return [
        snap_and_clamp(raw_base, "base"),
        snap_and_clamp(raw_shoulder, "shoulder"),
        snap_and_clamp(raw_elbow, "elbow"),
        snap_and_clamp(raw_grip, "grip"),
    ]


def servo_limit_overshoot(theta1_deg, theta2_deg, theta3_deg, cfg=None):
    """
    Khớp nào mà IK đòi góc servo vượt giới hạn cứng (quá nửa bước STEP): trả về {'base': độ vượt, ...}.
    Khi đó servo bị chặn ở giới hạn nên đầu kẹp không tới đúng điểm dù cờ 'reachable' của IK vẫn đúng.
    """
    c = cfg or ARM_CONFIG
    raw = {
        "base": 90.0 + theta1_deg,
        "shoulder": 90.0 + (theta2_deg - c["theta2_at_90_deg"]),
        "elbow": 90.0 + (theta3_deg - c["theta3_at_90_deg"]),
    }
    over = {}
    for key, val in raw.items():
        lo, hi, _ = SERVO_LIMITS[key]
        if val < lo - SERVO_STEP_DEG / 2:
            over[key] = lo - val
        elif val > hi + SERVO_STEP_DEG / 2:
            over[key] = val - hi
    return over


def arduino_servo_to_joint(servo_angles, cfg=None):
    """Đổi ngược từ 4 góc servo Arduino [base, shoulder, elbow, grip] sang góc khớp (theta1, theta2, theta3)."""
    c = cfg or ARM_CONFIG
    b, s, e, _ = servo_angles
    theta1 = float(b) - 90.0
    theta2 = c["theta2_at_90_deg"] + (float(s) - 90.0)
    theta3 = c["theta3_at_90_deg"] + (float(e) - 90.0)
    return theta1, theta2, theta3


def table_cm_to_robot_mm(x_cm, y_cm, cfg=None):
    """
    Đổi tọa độ điểm (X_cm, Y_cm) trên tờ giấy A4 sang tọa độ (x_mm, y_mm) trong hệ gốc Đế Robot.
    Trên tờ A4 đặt ngang (29.7 x 21.0 cm):
      - Đế robot đặt ở (base_x_cm, base_y_cm) (mặc định: mép dưới tờ A4, nhìn lên trên)
      - Trục +x_robot (vươn tới trước) = hướng từ đế lên phía trên tờ A4 (-Y_A4)
      - Trục +y_robot (sang trái của đế) = hướng sang bên trái tờ A4 (-X_A4)
    """
    c = cfg or ARM_CONFIG
    x_robot_mm = (c["base_y_cm"] - y_cm) * 10.0
    y_robot_mm = (c["base_x_cm"] - x_cm) * 10.0
    return x_robot_mm, y_robot_mm


def robot_mm_to_table_cm(x_robot_mm, y_robot_mm, cfg=None):
    """Đổi ngược từ tọa độ (x_mm, y_mm) hệ gốc Robot sang tọa độ (X_cm, Y_cm) trên tờ giấy A4."""
    c = cfg or ARM_CONFIG
    x_cm = c["base_x_cm"] - (y_robot_mm / 10.0)
    y_cm = c["base_y_cm"] - (x_robot_mm / 10.0)
    return x_cm, y_cm


def format_key_hint(channel_idx, current_deg, target_deg):
    """
    Tính độ lệch góc Δ và sinh câu lệnh gợi ý bấm phím cụ thể (VD: 'Bấm [A] x4' hoặc 'ĐÃ ĐẠT').
    Khớp chính xác với switch(cmd) trong code Arduino:
      - Kênh 0 (Đế):    +STEP -> 'A' (Trái),     -STEP -> 'D' (Phải)
      - Kênh 1 (Vai):   +STEP -> 'W' (Lên),      -STEP -> 'S' (Xuống)
      - Kênh 2 (Khuỷu): +STEP -> 'I' (Gập lên),  -STEP -> 'K' (Gập xuống)
      - Kênh 3 (Kẹp):   +STEP -> 'L' (Kẹp vào),  -STEP -> 'J' (Mở ra)
    """
    key_map = {
        0: ("A", "D", "Trai", "Phai"),
        1: ("W", "S", "Len", "Xuong"),
        2: ("I", "K", "Gap len", "Ha xuong"),
        3: ("L", "J", "Kep vao", "Mo ra"),
    }
    pos_key, neg_key, pos_desc, neg_desc = key_map[channel_idx]
    delta = int(round(target_deg - current_deg))
    steps = abs(delta) // SERVO_STEP_DEG
    if abs(delta) < SERVO_STEP_DEG:
        return delta, 0, "OK", "DA CAN (OK)", True
    if delta > 0:
        return delta, steps, pos_key.lower(), f"Bam [{pos_key}] x{steps} ({pos_desc})", False
    return delta, steps, neg_key.lower(), f"Bam [{neg_key}] x{steps} ({neg_desc})", False


# ==============================================================================
# 3. LUỒNG GIAO TIẾP USB SERIAL VỚI ARDUINO (TƯƠNG THÍCH CẢ CODE CŨ LẪN MỚI)
# ==============================================================================
class ArduinoSerialLink:
    """
    Luồng nền đọc/gửi tín hiệu qua cáp USB với Arduino (9600 baud):
    - Tương thích NGAY LẬP TỨC với code Arduino gốc của bạn: tự bắt dòng "Phím bấm: <cmd>"
      khi bạn bấm Bluetooth HC-05 để cộng/trừ 5 độ theo thời gian thực.
    - Nếu bạn nạp thêm hàm sendServoState() (JSON), luồng sẽ đồng bộ chính xác tuyệt đối
      mảng 4 góc {"servo":[base, shoulder, elbow, grip]}.
    - Nếu chưa cắm cáp USB Arduino, tự động chạy ở chế độ Mô phỏng (Simulation) để vẫn
      test được toàn bộ Camera + IK + Gợi ý trên màn hình.
    """

    def __init__(self, baud=9600):
        self.baud = baud
        self.port = None
        self.ser = None
        self.connected = False
        self.servo = [90, 90, 90, 95]  # [angleBase, angleShoulder, angleElbow, angleGrip]
        self.last_cmd = ""
        self.last_rx_time = 0.0
        self.lock = threading.Lock()
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _find_port(self):
        ports = sorted(glob.glob("/dev/cu.usbmodem*") + glob.glob("/dev/cu.usbserial*"))
        return ports[0] if ports else None

    def apply_key_locally(self, cmd):
        """Áp dụng đúng logic switch(cmd) của Arduino để cập nhật góc servo."""
        c = cmd.lower()
        with self.lock:
            b, s, e, g = self.servo
            if c == "a":
                b = min(180, max(0, b + SERVO_STEP_DEG))
            elif c == "d":
                b = min(180, max(0, b - SERVO_STEP_DEG))
            elif c == "w":
                s = min(155, max(25, s + SERVO_STEP_DEG))
            elif c == "s":
                s = min(155, max(25, s - SERVO_STEP_DEG))
            elif c == "i":
                e = min(155, max(25, e + SERVO_STEP_DEG))
            elif c == "k":
                e = min(155, max(25, e - SERVO_STEP_DEG))
            elif c == "j":
                g = min(175, max(95, g - SERVO_STEP_DEG))
            elif c == "l":
                g = min(175, max(95, g + SERVO_STEP_DEG))
            elif c == "h":
                b, s, e, g = 90, 90, 90, 95
            self.servo = [b, s, e, g]
            self.last_cmd = c.upper()

    def send_key(self, cmd):
        """Gửi 1 ký tự lệnh ('w','a','s','d','i','k','j','l','h') xuống Arduino (hoặc cập nhật mô phỏng)."""
        if not cmd:
            return
        ch = cmd[0]
        if self.connected and self.ser is not None:
            try:
                self.ser.write(ch.encode("utf-8"))
                self.ser.flush()
                return
            except Exception:
                self.connected = False
        # Nếu chưa cắm USB hoặc đang mô phỏng thì cập nhật trực tiếp
        self.apply_key_locally(ch)

    def _parse_line(self, line):
        line = line.strip()
        if not line:
            return
        # 1. Gói JSON từ hàm sendServoState(): {"t":1234,"servo":[90,90,90,95]}
        if line.startswith("{") and "servo" in line:
            try:
                data = json.loads(line)
                arr = data.get("servo", [])
                if len(arr) >= 4:
                    with self.lock:
                        self.servo = [int(arr[0]), int(arr[1]), int(arr[2]), int(arr[3])]
                        self.last_rx_time = time.time()
                return
            except Exception:
                pass

        # 2. Thông báo khởi động lại từ Arduino: "Robot Arm Ready! WASD + IK + JL"
        if "Robot Arm Ready" in line:
            with self.lock:
                self.servo = [90, 90, 90, 95]
                self.last_rx_time = time.time()
            return

        # 3. Tương thích trực tiếp với dòng Serial.print("Phím bấm: "); Serial.println(cmd); trong code gốc!
        m = re.search(r"Ph.*m\s*b.*m:\s*([a-zA-Z])", line)
        if m:
            cmd_char = m.group(1)
            self.apply_key_locally(cmd_char)
            with self.lock:
                self.last_rx_time = time.time()

    def _loop(self):
        if serial is None:
            return
        while self.running:
            if not self.connected or self.ser is None:
                port = self._find_port()
                if port:
                    try:
                        self.ser = serial.Serial(port, self.baud, timeout=0.15)
                        self.port = port
                        self.connected = True
                        print(f"🔌 Đã kết nối USB Serial Arduino tại {port} @ {self.baud} baud")
                    except Exception:
                        self.connected = False
                        time.sleep(1.5)
                        continue
                else:
                    time.sleep(1.5)
                    continue

            try:
                raw = self.ser.readline()
                if raw:
                    text = raw.decode("utf-8", errors="ignore")
                    self._parse_line(text)
            except Exception:
                self.connected = False
                try:
                    self.ser.close()
                except Exception:
                    pass
                self.ser = None
                time.sleep(1.0)

    def get_state(self):
        with self.lock:
            return list(self.servo), self.connected, self.port, self.last_cmd

    def release(self):
        self.running = False
        if self.ser is not None:
            try:
                self.ser.close()
            except Exception:
                pass


# ==============================================================================
# 4. BỘ ĐIỀU PHỐI GỢI Ý GẮP 5 BƯỚC & XÁC NHẬN GẮP (CAM A + CAM B)
# ==============================================================================
STAGE_NAMES = [
    "1. DIEM CHO (Cao +60mm, Mo kep J)",
    "2. HA XUONG DIEM KEP (Cao +20mm)",
    "3. DONG KEP (Bam L kep chat vat)",
    "4. NANG VAT LEN (Cao +80mm)",
    "5. XAC NHAN GAP (Cam A + Cam B)",
]


class GraspAssist4DOF:
    """
    Tích hợp vào main.py:
    - Nhận diện thêm mã ArUco ID 4 (Đế robot), ID 5-6 (Đầu kẹp), ID 10-29 (Vật thể)
      song song với các vật thể do YOLO11 phát hiện trên tờ giấy A4.
    - Tính IK 4-DOF cho điểm dừng hiện tại trong quy trình 5 bước gắp.
    - Hiệu chỉnh vòng kín (Closed-loop) nếu thấy mã ArUco ID 5 trên đầu kẹp.
    - Kiểm tra tín hiệu S1 (Cam ngang thấy vật nâng >= 20mm) và S2 (Cam trên thấy chỗ cũ trống)
      để kết luận "GẮP THÀNH CÔNG" hay "THẤT BẠI (Kẹp trượt / Rơi)".
    """

    def __init__(self):
        self.serial_link = ArduinoSerialLink(baud=9600)
        self.lock = threading.Lock()

        # Danh sách vật thể phát hiện được trên bàn (gộp cả ArUco ID 10..29 và YOLO11)
        self.objects = []
        self.selected_idx = 0
        self.stage = 0  # 0..4 tương ứng 5 bước trong STAGE_NAMES
        self.auto_step_enabled = False
        self.last_auto_step_ts = 0.0

        # Vị trí đầu kẹp thực tế nhìn thấy qua ArUco ID 5 (Cam A) và ID 6 (Cam B)
        self.gripper_top_cm = None
        self.gripper_side_px = None
        self.closed_loop_offset_mm = np.zeros(2, dtype=np.float32)

        # Bộ lọc trung bình trượt tọa độ vật mục tiêu (10 khung hình theo kế hoạch)
        self.target_history_cm = deque(maxlen=10)
        self.locked_grasp_cm = None  # Lưu vị trí cũ của vật lúc bắt đầu đóng kẹp để kiểm tra S2 (chỗ cũ trống)

        # Cửa sổ 30 khung hình kiểm tra xác nhận gắp (S1: Cam ngang, S2: Cam trên)
        self.s1_window = deque(maxlen=30)
        self.s2_window = deque(maxlen=30)
        self.verify_start_ts = None
        self.verify_banner = ""
        self.verify_color = (200, 200, 200)
        self.verify_banner_ts = 0.0

        # Tên vật bị khóa lúc đóng kẹp (nâng lên rồi vật rời bàn nên không còn trong danh sách) + thống kê kết quả gắp
        self.locked_obj_name = None
        self.success_count = 0
        self.fail_count = 0
        self.last_result = None  # {"ok", "reason", "detail", "obj", "s1", "s2", "ts"} của lần gắp gần nhất

        # Khởi tạo file log CSV nếu chưa có
        self._init_csv_log()

    def _init_csv_log(self):
        os.makedirs(os.path.dirname(LOG_CSV_PATH), exist_ok=True)
        if not os.path.exists(LOG_CSV_PATH):
            with open(LOG_CSV_PATH, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "object_name", "target_x_mm", "target_y_mm",
                    "align_error_mm", "s1_ratio", "s2_ratio", "result", "reason"
                ])

    def _log_attempt(self, obj_name, tx_mm, ty_mm, err_mm, s1_ratio, s2_ratio, result, reason):
        try:
            with open(LOG_CSV_PATH, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    obj_name,
                    f"{tx_mm:.1f}",
                    f"{ty_mm:.1f}",
                    f"{err_mm:.1f}",
                    f"{s1_ratio:.2f}",
                    f"{s2_ratio:.2f}",
                    result,
                    reason,
                ])
            print(f"📝 Đã ghi kết quả gắp vào {LOG_CSV_PATH}: {result} ({reason})")
        except Exception as e:
            print(f"⚠️ Không ghi được log CSV: {e}")

    def _set_banner(self, text, color):
        self.verify_banner = text
        self.verify_color = color
        self.verify_banner_ts = time.time()

    def _record_result(self, ok, reason, obj_name, s1_ratio, s2_ratio):
        if ok:
            self.success_count += 1
        else:
            self.fail_count += 1
        self.last_result = {
            "ok": ok, "reason": reason, "detail": self.verify_banner, "obj": obj_name,
            "s1": s1_ratio, "s2": s2_ratio, "ts": time.time(),
        }

    def cycle_target(self):
        with self.lock:
            if self.objects:
                self.selected_idx = (self.selected_idx + 1) % len(self.objects)
                self.target_history_cm.clear()
                self.stage = 0
                self.verify_banner = ""

    def next_stage(self):
        with self.lock:
            if self.stage == 1 and self.target_history_cm:
                # Trước khi đóng kẹp (chuyển sang bước 2), khóa vị trí cũ của vật để lát kiểm tra chỗ cũ trống (S2)
                avg_cm = np.mean(self.target_history_cm, axis=0)
                self.locked_grasp_cm = (float(avg_cm[0]), float(avg_cm[1]))
                self.locked_obj_name = (
                    self.objects[min(self.selected_idx, len(self.objects) - 1)]["name"] if self.objects else None
                )
            self.stage = (self.stage + 1) % len(STAGE_NAMES)
            if self.stage == 4:
                self.s1_window.clear()
                self.s2_window.clear()
                self.verify_start_ts = time.time()

    def reset_workflow(self):
        with self.lock:
            self.stage = 0
            self.locked_grasp_cm = None
            self.s1_window.clear()
            self.s2_window.clear()
            self.verify_start_ts = None
            self.locked_obj_name = None
            self._set_banner("DA RESET QUY TRINH GAP VE BUOC 1", (0, 220, 255))

    def update_topdown_observations(self, work_img, corners, ids, dets_yolo, H_px2cm, H_cm2px):
        """
        Cập nhật quan sát từ Cam A (Nhìn từ trên xuống - OBSBOT):
        1. Mã ID 4 -> Cập nhật vị trí Đế Robot trên tờ A4.
        2. Mã ID 5 -> Vị trí thực của Đầu kẹp (Closed-loop).
        3. Mã ID 10..29 + YOLO11 -> Danh sách vật thể cần gắp.
        4. Vẽ hình chiếu Cánh tay Robot (FK) và khung mục tiêu lên ảnh Cam A.
        """
        if H_px2cm is None or H_cm2px is None:
            return

        detected_objs = []
        gripper_cm = None

        # 1. Quét các mã ArUco đặc biệt (ID 4, ID 5, ID 10..29)
        if ids is not None and len(ids) > 0:
            for c, mid in zip(corners, ids.flatten()):
                mid = int(mid)
                pts = c[0]
                center_px = pts.mean(axis=0)
                center_cm = cv2.perspectiveTransform(
                    np.float32([[[center_px[0], center_px[1]]]]), H_px2cm
                )[0][0]
                cx_cm, cy_cm = float(center_cm[0]), float(center_cm[1])

                if mid == 4:
                    # ID 4: Đế robot
                    ARM_CONFIG["base_x_cm"] = cx_cm
                    ARM_CONFIG["base_y_cm"] = cy_cm
                elif mid == 5:
                    # ID 5: Đầu kẹp nhìn từ Cam A
                    gripper_cm = (cx_cm, cy_cm)
                    p_grip = tuple(np.int32(center_px))
                    cv2.circle(work_img, p_grip, 10, (255, 255, 0), -1)
                    cv2.putText(
                        work_img,
                        f"KEP THUC ID:5 ({cx_cm:.1f},{cy_cm:.1f}cm)",
                        (p_grip[0] + 12, p_grip[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        (255, 255, 0),
                        2,
                        cv2.LINE_AA,
                    )
                elif 10 <= mid <= 29:
                    spec = OBJECT_SPECS.get(mid, DEFAULT_OBJ_SPEC)
                    detected_objs.append({
                        "name": f"{spec['name']} (ArUco #{mid})",
                        "x_cm": cx_cm,
                        "y_cm": cy_cm,
                        "w_mm": spec["w_mm"],
                        "h_mm": spec["h_mm"],
                        "px": center_px,
                        "source": "aruco",
                    })

        # 2. Gộp thêm các vật thể từ YOLO11 trên mặt tờ giấy A4
        for det in dets_yolo:
            rx, ry = det["ref_pt"]
            pt_cm = cv2.perspectiveTransform(np.float32([[[rx, ry]]]), H_px2cm)[0][0]
            ox_cm, oy_cm = float(pt_cm[0]), float(pt_cm[1])
            # Tránh trùng lặp nếu vật đó đã có mã ArUco ID 10..29
            if any(math.hypot(ox_cm - o["x_cm"], oy_cm - o["y_cm"]) < 2.5 for o in detected_objs):
                continue
            detected_objs.append({
                "name": f"YOLO:{det['cls']}",
                "x_cm": ox_cm,
                "y_cm": oy_cm,
                "w_mm": 35.0,
                "h_mm": 40.0,
                "px": (rx, ry),
                "source": "yolo",
            })

        # Sắp xếp vật ưu tiên gần Đế Robot nhất (như tài liệu Kế hoạch trang 9)
        detected_objs.sort(
            key=lambda o: math.hypot(
                o["x_cm"] - ARM_CONFIG["base_x_cm"],
                o["y_cm"] - ARM_CONFIG["base_y_cm"],
            )
        )

        # Kiểm tra tín hiệu S2 (Chỗ cũ trống trên Cam A sau khi nâng vật)
        s2_empty = False
        if self.locked_grasp_cm is not None:
            lx_cm, ly_cm = self.locked_grasp_cm
            # Chỗ cũ trống nếu không còn vật nào nằm trong bán kính 3.0 cm (30 mm) quanh vị trí gắp cũ
            near_old = any(
                math.hypot(o["x_cm"] - lx_cm, o["y_cm"] - ly_cm) <= 3.0
                for o in detected_objs
            )
            s2_empty = not near_old
            # Vẽ vòng tròn kiểm tra vị trí cũ (S2) trên Cam A
            old_px = cv2.perspectiveTransform(np.float32([[[lx_cm, ly_cm]]]), H_cm2px)[0][0]
            p_old = tuple(np.int32(old_px))
            s2_col = (0, 255, 0) if s2_empty else (0, 0, 255)
            cv2.circle(work_img, p_old, 28, s2_col, 2, cv2.LINE_AA)
            cv2.putText(
                work_img,
                f"Cho cu S2: {'TRONG' if s2_empty else 'CON VAT'}",
                (p_old[0] - 65, p_old[1] - 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.52,
                s2_col,
                2,
                cv2.LINE_AA,
            )

        with self.lock:
            self.gripper_top_cm = gripper_cm
            self.objects = detected_objs
            if self.stage == 4:
                self.s2_window.append(1 if s2_empty else 0)

            if self.objects:
                self.selected_idx = min(self.selected_idx, len(self.objects) - 1)
                sel = self.objects[self.selected_idx]
                self.target_history_cm.append((sel["x_cm"], sel["y_cm"]))

        # 3. Vẽ Đế Robot và Hình chiếu Cánh tay (Động học thuận FK từ 4 góc servo hiện tại) lên Cam A
        servo_now, _, _, _ = self.serial_link.get_state()
        t1, t2, t3 = arduino_servo_to_joint(servo_now)
        fk_x_mm, fk_y_mm, fk_z_mm = fk_4dof_joint(t1, t2, t3)
        fk_x_cm, fk_y_cm = robot_mm_to_table_cm(fk_x_mm, fk_y_mm)

        pts_arm_cm = np.float32([[
            [ARM_CONFIG["base_x_cm"], ARM_CONFIG["base_y_cm"]],
            [fk_x_cm, fk_y_cm],
        ]])
        pts_arm_px = np.int32(cv2.perspectiveTransform(pts_arm_cm, H_cm2px)[0])
        p_base_px = tuple(pts_arm_px[0])
        p_fk_px = tuple(pts_arm_px[1])

        # Vẽ đoạn thẳng nối từ Đế Robot tới vị trí Đầu kẹp hiện tại (màu Xanh lá mạ / Cyan)
        cv2.line(work_img, p_base_px, p_fk_px, (255, 255, 0), 3, cv2.LINE_AA)
        cv2.circle(work_img, p_base_px, 12, (0, 140, 255), -1)
        cv2.circle(work_img, p_base_px, 14, (255, 255, 255), 2)
        cv2.putText(
            work_img,
            "DE ROBOT",
            (p_base_px[0] - 45, p_base_px[1] - 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 200, 255),
            2,
            cv2.LINE_AA,
        )
        # Vẽ tâm Đầu kẹp dự tính theo góc Servo hiện tại
        cv2.drawMarker(
            work_img, p_fk_px, (255, 255, 0), cv2.MARKER_CROSS, 22, 2, cv2.LINE_AA
        )
        cv2.putText(
            work_img,
            f"Dau kep FK (Z={fk_z_mm:.0f}mm)",
            (p_fk_px[0] + 12, p_fk_px[1] + 6),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            (255, 255, 0),
            2,
            cv2.LINE_AA,
        )

    def update_side_observations(self, work_img, corners, ids, dets_side):
        """
        Cập nhật quan sát từ Cam B (Nhìn ngang - Điện thoại):
        - Đo độ cao vật thể so với đường mặt bàn để tính tín hiệu S1 (Vật đã rời mặt bàn >= 20mm).
        - Vẽ vạch chuẩn mặt bàn và vạch ngưỡng nâng +20mm lên khung Cam B.
        """
        h, w = work_img.shape[:2]
        # Đường mặt bàn tham chiếu trên góc nhìn ngang (nằm tại y ~ 55% chiều cao khung hình)
        table_y_px = int(h * 0.54)
        lift_thresh_y_px = int(table_y_px - h * 0.065)  # Tương đương cao hơn mặt bàn ~20mm

        cv2.line(work_img, (40, table_y_px), (w - 40, table_y_px), (0, 180, 255), 2, cv2.LINE_AA)
        cv2.line(
            work_img, (40, lift_thresh_y_px), (w - 40, lift_thresh_y_px), (0, 255, 128), 2, cv2.LINE_AA
        )
        cv2.putText(
            work_img,
            "Nguong nhac vat S1 (+20mm)",
            (48, lift_thresh_y_px - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.52,
            (0, 255, 128),
            2,
            cv2.LINE_AA,
        )

        s1_lifted = False
        # Kiểm tra qua mã ArUco mặt hông (ID 6 hoặc ID 10..29)
        if ids is not None and len(ids) > 0:
            for c, mid in zip(corners, ids.flatten()):
                mid = int(mid)
                cy = float(c[0].mean(axis=0)[1])
                if mid == 6 or (10 <= mid <= 29):
                    if cy < lift_thresh_y_px:
                        s1_lifted = True

        # Hoặc kiểm tra qua đáy bounding box YOLO trên góc nhìn ngang
        for det in dets_side:
            _, fy1, _, fy2 = det["bbox"]
            bottom_y = fy2
            if bottom_y < lift_thresh_y_px:
                s1_lifted = True

        with self.lock:
            if self.stage == 4:
                self.s1_window.append(1 if s1_lifted else 0)
                self._evaluate_verification_locked()

    def _evaluate_verification_locked(self):
        """Đánh giá kết quả gắp theo bảng quy tắc trang 6 & 11 của tài liệu Kế hoạch."""
        if len(self.s1_window) < 10 and (
            self.verify_start_ts is None or time.time() - self.verify_start_ts < 1.5
        ):
            return

        s1_cnt = sum(self.s1_window)
        s2_cnt = sum(self.s2_window)
        n1 = max(1, len(self.s1_window))
        n2 = max(1, len(self.s2_window))
        s1_ratio = s1_cnt / n1
        s2_ratio = s2_cnt / n2

        # Sau khi nâng, vật đã rời bàn nên danh sách vật lúc này không còn đúng: ưu tiên tên/vị trí đã khóa lúc đóng kẹp
        obj_name = self.locked_obj_name or (
            self.objects[self.selected_idx]["name"]
            if self.objects and self.selected_idx < len(self.objects)
            else "Vat_Demo"
        )
        tx_mm, ty_mm = (0.0, 0.0)
        if self.locked_grasp_cm is not None:
            tx_mm, ty_mm = table_cm_to_robot_mm(*self.locked_grasp_cm)
        elif self.target_history_cm:
            avg_cm = np.mean(self.target_history_cm, axis=0)
            tx_mm, ty_mm = table_cm_to_robot_mm(float(avg_cm[0]), float(avg_cm[1]))

        # Thành công khi cả S1 (Cam B) và S2 (Cam A) cùng đúng >= 80% số khung (~25/30 khung)
        if len(self.s1_window) >= 15 and s1_ratio >= 0.80 and s2_ratio >= 0.80:
            self._set_banner("KET LUAN: GAP THANH CONG! (Cam A + Cam B dong y)", (0, 255, 100))
            self._record_result(True, "ok", obj_name, s1_ratio, s2_ratio)
            self._log_attempt(obj_name, tx_mm, ty_mm, 0.0, s1_ratio, s2_ratio, "SUCCESS", "ok")
            self.stage = 0
            self.s1_window.clear()
            self.s2_window.clear()
        elif self.verify_start_ts and (time.time() - self.verify_start_ts >= 3.0):
            # Hết 3 giây kiểm tra: phân loại lý do thất bại
            if s2_ratio < 0.40:
                reason = "kep_truot_vat_van_o_cho_cu"
                self.verify_banner = "THAT BAI: KEP TRUOT (Vat van nam o cho cu tren Cam A)"
            elif s1_ratio < 0.40:
                reason = "roi_khi_nang_hoac_chua_nhac_len"
                self.verify_banner = "THAT BAI: ROI KHI NANG (Cam B khong thay vat o tren cao)"
            else:
                reason = "khong_xac_dinh_bi_che"
                self.verify_banner = "KHONG XAC DINH -> Thu lai voi tu the vat moi"
            self._set_banner(self.verify_banner, (0, 80, 255))
            self._record_result(False, reason, obj_name, s1_ratio, s2_ratio)
            self._log_attempt(obj_name, tx_mm, ty_mm, 0.0, s1_ratio, s2_ratio, "FAIL", reason)
            self.stage = 0
            self.s1_window.clear()
            self.s2_window.clear()

    def compute_current_suggestion(self):
        """
        Tính toán bộ góc gợi ý [angleBase, angleShoulder, angleElbow, angleGrip]
        cho bước hiện tại (stage 0..4) và vật đang chọn.
        """
        servo_now, usb_ok, port_name, last_cmd = self.serial_link.get_state()
        with self.lock:
            has_obj = len(self.objects) > 0 and len(self.target_history_cm) > 0
            stage = self.stage
            if has_obj:
                sel = self.objects[min(self.selected_idx, len(self.objects) - 1)]
                avg_cm = np.mean(self.target_history_cm, axis=0)
                obj_x_cm, obj_y_cm = float(avg_cm[0]), float(avg_cm[1])
                obj_h_mm = float(sel.get("h_mm", 40.0))
                obj_w_mm = float(sel.get("w_mm", 35.0))
                obj_name = sel["name"]
            else:
                obj_x_cm, obj_y_cm = 14.85, 10.5  # Tâm tờ giấy A4 mặc định
                obj_h_mm, obj_w_mm = 40.0, 35.0
                obj_name = "Chua co vat (Tam A4 mac dinh)"

            grip_cm = self.gripper_top_cm
            now = time.time()
            banner = self.verify_banner if now - self.verify_banner_ts <= BANNER_SECONDS else ""
            banner_col = self.verify_color
            # Tiến độ kiểm tra S1/S2 đang chạy ở bước 5 (cửa sổ hướng dẫn hiện thanh tiến độ)
            verify = None
            if stage == 4:
                verify = {
                    "s1": sum(self.s1_window), "n1": len(self.s1_window),
                    "s2": sum(self.s2_window), "n2": len(self.s2_window),
                    "elapsed": (now - self.verify_start_ts) if self.verify_start_ts else 0.0,
                }
            result = dict(self.last_result, age=now - self.last_result["ts"]) if self.last_result else None
            success_count, fail_count = self.success_count, self.fail_count
            n_objects, selected_idx = len(self.objects), self.selected_idx

        x_rob_mm, y_rob_mm = table_cm_to_robot_mm(obj_x_cm, obj_y_cm)

        # Sai số căn đầu kẹp (nếu có mã ArUco ID 5 trên đầu kẹp, ngược lại tính theo FK)
        if grip_cm is not None:
            gx_mm, gy_mm = table_cm_to_robot_mm(grip_cm[0], grip_cm[1])
        else:
            t1, t2, t3 = arduino_servo_to_joint(servo_now)
            gx_mm, gy_mm, _ = fk_4dof_joint(t1, t2, t3)
        align_err_mm = math.hypot(x_rob_mm - gx_mm, y_rob_mm - gy_mm)

        # Độ cao mục tiêu z_mm và trạng thái đóng/mở kẹp theo từng bước trong 5 bước
        grasp_z_mm = max(12.0, obj_h_mm * 0.5)
        if stage == 0:
            # Bước 1: Điểm chờ phía trên vật +60mm, mở kẹp
            target_z_mm = grasp_z_mm + 60.0
            close_grip = False
        elif stage == 1:
            # Bước 2: Hạ xuống điểm kẹp, kẹp vẫn mở
            target_z_mm = grasp_z_mm
            close_grip = False
        elif stage == 2:
            # Bước 3: Đóng kẹp tại điểm kẹp
            target_z_mm = grasp_z_mm
            close_grip = True
        else:
            # Bước 4 & 5: Nâng vật lên +80mm và giữ kẹp đóng để xác nhận
            target_z_mm = grasp_z_mm + 80.0
            close_grip = True

        ik_res = ik_4dof_joint(x_rob_mm, y_rob_mm, target_z_mm)
        servo_target = joint_to_arduino_servo(
            ik_res["theta1_deg"],
            ik_res["theta2_deg"],
            ik_res["theta3_deg"],
            grip_open_mm=obj_w_mm + 18.0,
            close_grip=close_grip,
        )

        clamped = servo_limit_overshoot(ik_res["theta1_deg"], ik_res["theta2_deg"], ik_res["theta3_deg"])

        hints = [
            format_key_hint(i, servo_now[i], servo_target[i]) for i in range(4)
        ]
        all_aligned = all(h[4] for h in hints)

        # Tự động gửi từng bước lệnh nếu người dùng bật chế độ Auto-Step (phím 'p')
        if self.auto_step_enabled and (time.time() - self.last_auto_step_ts >= 0.28):
            self.last_auto_step_ts = time.time()
            # Thứ tự ưu tiên an toàn theo Kế hoạch trang 10: Đế (0) -> Kẹp (3) -> Vai (1) -> Khuỷu (2)
            for idx in (0, 3, 1, 2):
                _, steps, cmd_key, _, ok = hints[idx]
                if not ok and steps > 0:
                    self.serial_link.send_key(cmd_key)
                    break

        return {
            "obj_name": obj_name,
            "has_obj": has_obj,
            "obj_cm": (obj_x_cm, obj_y_cm),
            "rob_mm": (x_rob_mm, y_rob_mm, target_z_mm),
            "ik": ik_res,
            "servo_now": servo_now,
            "servo_target": servo_target,
            "hints": hints,
            "all_aligned": all_aligned,
            "align_err_mm": align_err_mm,
            "usb_ok": usb_ok,
            "port_name": port_name,
            "last_cmd": last_cmd,
            "stage": stage,
            "stage_name": STAGE_NAMES[stage],
            "banner": banner,
            "banner_col": banner_col,
            "auto_step": self.auto_step_enabled,
            "clamped": clamped,
            "verify": verify,
            "result": result,
            "success_count": success_count,
            "fail_count": fail_count,
            "n_objects": n_objects,
            "selected_idx": selected_idx,
        }

    def render_hud_bar(self, width=1280, height=175, info=None):
        """
        Vẽ thanh bảng điều khiển Gợi ý Gắp 4 Servo (1280 x 175) gắn vào cạnh dưới cửa sổ Dual Camera.
        Hiển thị trực quan:
          - 4 ô Servo: Góc hiện tại -> Góc gợi ý (Δ) + Phím cần bấm (WASD / IK / JL)
          - Bước hiện tại trong 5 bước + Thông báo "ĐÃ CĂN — ĐÓNG KẸP" khi lệch <= 8mm
        info: kết quả compute_current_suggestion() đã tính sẵn trong khung hình này (None thì tự tính).
        """
        hud = np.full((height, width, 3), (24, 26, 30), dtype=np.uint8)
        cv2.line(hud, (0, 0), (width, 0), (90, 200, 255), 2)

        if info is None:
            info = self.compute_current_suggestion()
        rx, ry, rz = info["rob_mm"]
        ik = info["ik"]

        # --- DÒNG TRÊN CÙNG: Trạng thái kết nối Arduino, Vật mục tiêu, Bước gắp ---
        usb_txt = (
            f"USB Arduino: DA KET NOI ({info['port_name']})"
            if info["usb_ok"]
            else "USB Arduino: MO PHONG (Bam WASD/IK/JL tren ban phim de thu)"
        )
        usb_col = (0, 255, 128) if info["usb_ok"] else (0, 200, 255)
        cv2.putText(hud, usb_txt, (16, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.54, usb_col, 2, cv2.LINE_AA)

        reach_txt = (
            f"TRONG TAM VOI (r={ik['r_mm']:.0f}mm)"
            if ik["reachable"]
            else f"NGOAI TAM! Doi vat gan de them {ik['move_closer_mm']:.0f}mm"
        )
        reach_col = (0, 255, 128) if ik["reachable"] else (0, 80, 255)
        target_str = (
            f"Muc tieu: {info['obj_name']} | Toa do Robot: X={rx:.0f}mm, Y={ry:.0f}mm, Z={rz:.0f}mm | {reach_txt}"
        )
        cv2.putText(hud, target_str, (475, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.54, reach_col, 2, cv2.LINE_AA)

        # --- DÃY 4 Ô SERVO: KÊNH 0 (ĐẾ), KÊNH 1 (VAI), KÊNH 2 (KHUỶU), KÊNH 3 (KẸP) ---
        titles = [
            "KENH 0: DE XOAY (A / D)",
            "KENH 1: CANH TAY / VAI (W / S)",
            "KENH 2: KHUYU TAY (I / K)",
            "KENH 3: KEP GAP (J / L)",
        ]
        card_w = (width - 40) // 4
        for i in range(4):
            x1 = 14 + i * (card_w + 4)
            y1 = 38
            x2 = x1 + card_w
            y2 = 132

            cur = info["servo_now"][i]
            tgt = info["servo_target"][i]
            delta, _, _, action_txt, is_ok = info["hints"][i]

            border_col = (0, 230, 100) if is_ok else (0, 180, 255)
            bg_col = (28, 52, 34) if is_ok else (36, 38, 46)
            cv2.rectangle(hud, (x1, y1), (x2, y2), bg_col, -1)
            cv2.rectangle(hud, (x1, y1), (x2, y2), border_col, 2)

            cv2.putText(
                hud, titles[i], (x1 + 10, y1 + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (210, 210, 210), 1, cv2.LINE_AA
            )
            ang_str = f"Hien tai: {cur:3d} deg -> Goi y: {tgt:3d} deg ({delta:+d})"
            cv2.putText(
                hud, ang_str, (x1 + 10, y1 + 52), cv2.FONT_HERSHEY_SIMPLEX, 0.53, (255, 255, 255), 2, cv2.LINE_AA
            )
            act_col = (0, 255, 128) if is_ok else (0, 230, 255)
            cv2.putText(
                hud,
                f"=> {action_txt}",
                (x1 + 10, y1 + 82),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.60,
                act_col,
                2,
                cv2.LINE_AA,
            )

        # --- DÒNG DƯỚI CÙNG: Quy trình 5 bước + Biểu ngữ ĐÃ CĂN / KẾT QUẢ GẮP ---
        stage_str = f"QUY TRINH GAP: [{info['stage_name']}]"
        cv2.putText(hud, stage_str, (16, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.56, (255, 220, 80), 2, cv2.LINE_AA)

        if info["banner"]:
            status_msg = info["banner"]
            status_col = info["banner_col"]
        elif info["all_aligned"] and info["stage"] == 1:
            status_msg = "DA CAN DUNG VI TRI! -> Bam SPACE sang Buoc 3 roi bam 'L' de DONG KEP"
            status_col = (0, 255, 100)
        elif info["all_aligned"]:
            status_msg = "4 SERVO DA DAT GOC GOI Y! -> Bam SPACE de sang buoc tiep theo"
            status_col = (0, 255, 100)
        else:
            auto_state = "BAT" if self.auto_step_enabled else "TAT"
            status_msg = (
                f"Sai so dau kep: {info['align_err_mm']:.0f}mm | "
                f"[SPACE]: Qua buoc | [TAB]: Doi vat | [P]: Tu dong ({auto_state}) | [R]: Reset"
            )
            status_col = (220, 220, 220)

        cv2.putText(hud, status_msg, (475, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.54, status_col, 2, cv2.LINE_AA)
        return hud

    def handle_key(self, key_code):
        """
        Xử lý phím bấm trên cửa sổ OpenCV:
        - Các phím 'w','a','s','d','i','k','j','l','h': gửi lệnh điều khiển tới Arduino (hoặc mô phỏng)
        - Phím Space (32) hoặc 'n': Chuyển sang bước gắp tiếp theo (1 -> 5)
        - Phím Tab (9) hoặc 'v': Đổi vật mục tiêu
        - Phím 'p': Bật/tắt chế độ Tự động bước (Auto-Step)
        - Phím 'r': Reset quy trình gắp về Bước 1
        """
        if key_code < 0 or key_code == 255:
            return False
        ch = chr(key_code & 0xFF).lower()
        if ch in ("w", "a", "s", "d", "i", "k", "j", "l", "h"):
            self.serial_link.send_key(ch)
            return True
        if key_code == 32 or ch == "n":  # Space hoặc 'n'
            self.next_stage()
            return True
        if key_code == 9 or ch == "v":   # Tab hoặc 'v'
            self.cycle_target()
            return True
        if ch == "p":
            self.auto_step_enabled = not self.auto_step_enabled
            print(f"🤖 Chế độ Tự động gắp (Auto-Step): {'BẬT' if self.auto_step_enabled else 'TẮT'}")
            return True
        if ch == "r":
            self.reset_workflow()
            return True
        return False

    def release(self):
        self.serial_link.release()
