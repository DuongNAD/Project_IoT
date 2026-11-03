#!/usr/bin/env python3
"""
NHÓM 1 - ĐIỀU KHIỂN: vật ở đâu -> servo phải quay tới góc nào -> bấm phím gì, mấy lần.

    vật (x, y cm trên tờ giấy) --IK--> 3 góc servo cần tới --so với góc hiện tại--> "bấm phím D x8, S x16 ..."

Phần này lo toàn bộ việc ĐIỀU KHIỂN cánh tay:
  1. Hình học cánh tay: động học thuận / ngược (FK / IK), đổi góc khớp <-> góc servo Arduino, đổi tọa độ tờ giấy <-> hệ robot.
  2. Cổng USB tới Arduino: gửi phím (W A S D I K J L H X Z), đọc góc servo thật mà firmware báo về.
  3. Chọn vật mục tiêu trong các vật camera thấy và tính ra danh sách lệnh bấm phím (Move).
Kết quả mỗi khung hình là một Plan, chuyển cho NHÓM 2 (success.py) để kết luận "đã tới chưa".
Phần nhìn (camera, ArUco, tìm vật) nằm ở vision.py; phần vẽ màn hình ở screen.py; main.py nối các phần lại.
"""

import glob
import json
import math
import os
import re
import threading
import time
from collections import deque
from dataclasses import dataclass, field

import numpy as np

try:
    import serial
except ImportError:
    serial = None


# ==============================================================================
# 1. HÌNH HỌC CÁNH TAY 4 SERVO (MG996R + PCA9685)
# ==============================================================================
ARM_CONFIG = {
    "d1_mm": 70.0,      # Chiều cao từ mặt bàn đến trục khớp Vai (mm)
    "L2_mm": 105.0,     # Chiều dài khâu Vai -> Khuỷu (mm)
    "L3_mm": 100.0,     # Chiều dài khâu Khuỷu -> Cổ tay / giá kẹp (mm)
    "L4_r_mm": 65.0,    # Độ vươn ngang từ khớp giá kẹp tới tâm 2 ngón kẹp (mm)
    "L4_z_mm": 25.0,    # Độ trễ dọc từ khớp giá kẹp xuống tâm 2 ngón kẹp (mm)
    # Vị trí trục xoay Đế Robot trên hệ tọa độ tờ giấy A4 (xem calibration.py): gốc ở góc ngoài mã ArUco ID 0,
    # X chạy ID 0 -> ID 1 (29.7 cm), Y chạy ID 0 -> ID 3 (21.0 cm). Mặc định: robot đứng NGOÀI mép Y = 0, giữa mép, nhìn vào tờ giấy (+Y).
    # Bấm phím B trong main.py rồi click vào trục xoay đế để hiệu chỉnh lại (lưu vào calibration.json).
    "base_x_cm": 14.85,
    "base_y_cm": -7.5,
    "base_heading_deg": 90.0,   # Hướng robot nhìn, đo từ +X quay về +Y (90 = nhìn vào +Y, -90 = nhìn lên -Y)
    # Góc khớp chuẩn (độ) khi 3 servo Đế, Vai, Khuỷu đang ở góc mặc định 90° của code Arduino
    "theta2_at_90_deg": 45.0,   # Khi angleShoulder = 90° thì khâu L2 nghiêng +45° so với phương ngang
    "theta3_at_90_deg": -45.0,  # Khi angleElbow = 90° thì khâu L3 gập -45° so với khâu L2
}
# Giá trị mặc định trong code (trước khi nạp calibration.json): dùng để biết khi nào hiệu chỉnh trở về đúng mặc định
ARM_CONFIG_DEFAULTS = dict(ARM_CONFIG)

# Servo: giới hạn an toàn và bước mỗi lần bấm phím, khớp robot_arm_4dof.ino (STEP_ARM = 2, STEP_GRIP = 5, GRIP_CLOSE_LIMIT = 160)
CHANNEL_KEYS = ("base", "shoulder", "elbow", "grip")  # Thứ tự kênh 0..3 của Arduino
SERVO_LIMITS = {
    "base": (0, 180, 90),       # Kênh 0: Đế (a: +2° , d: -2°)
    "shoulder": (25, 155, 90),  # Kênh 1: Vai (w: +2° nâng lên, s: -2° hạ xuống)
    "elbow": (25, 155, 90),     # Kênh 2: Khuỷu (i: +2° lên, k: -2° xuống)
    "grip": (95, 160, 95),      # Kênh 3: Kẹp (j: -5° mở ra, l: +5° kẹp vào)
}
SERVO_STEPS = {"base": 2, "shoulder": 2, "elbow": 2, "grip": 5}
SERVO_ANCHORS = {"base": 90, "shoulder": 90, "elbow": 90, "grip": 95}  # Góc lúc khởi động: mọi góc bấm tới được = neo + k * bước
GRIP_OPEN_DEG = 95

GRASP_Z_MM = 25.0        # Độ cao điểm kẹp mục tiêu (mm): nửa thân cốc, đúng độ cao dùng khi hiệu chỉnh hình học bằng các lần ôm
TARGET_MEMORY_S = 120.0  # Càng kẹp che mất vật (không còn thấy) thì nhớ vị trí vật vừa thấy trong ngần này giây
SELECT_TRACK_CM = 4.0    # Vật đang chọn được nhận lại ở khung sau nếu tâm dời không quá ngần này (cm)


# ==============================================================================
# 2. ĐỘNG HỌC THUẬN (FK) & NGƯỢC (IK), ĐỔI GÓC KHỚP <-> GÓC SERVO, ĐỔI TỌA ĐỘ
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


def joint_to_servo(theta1_deg, theta2_deg, theta3_deg, cfg=None):
    """
    Đổi góc khớp hình học (theta1, theta2, theta3) sang góc 3 servo [angleBase, angleShoulder, angleElbow] của Arduino, làm tròn về góc
    bấm phím tới được (neo + k * bước, đế / vai / khuỷu bước 2°) và kẹp trong giới hạn an toàn.
    """
    c = cfg or ARM_CONFIG
    raw = {
        "base": 90.0 + theta1_deg,                                          # 90° = thẳng phía trước; a (+) quay trái, d (-) quay phải
        "shoulder": 90.0 + (theta2_deg - c["theta2_at_90_deg"]),            # 90° ứng với góc nghiêng chuẩn theta2_at_90_deg
        "elbow": 90.0 + (theta3_deg - c["theta3_at_90_deg"]),               # 90° ứng với góc gập chuẩn theta3_at_90_deg
    }
    servo = []
    for key, val in raw.items():
        lo, hi, _ = SERVO_LIMITS[key]
        val = max(lo, min(hi, val))
        step, anchor = SERVO_STEPS[key], SERVO_ANCHORS[key]
        servo.append(max(lo, min(hi, int(anchor + round((val - anchor) / step) * step))))
    return servo


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
    Trên tờ A4 đặt ngang (29.7 x 21.0 cm), đế robot ở (base_x_cm, base_y_cm) và nhìn theo base_heading_deg:
      - Trục +x_robot (vươn tới trước) = hướng nhìn của robot f = (cos h, sin h) trong hệ tờ giấy
      - Trục +y_robot (sang trái của đế) = f quay trái 90° = (f_y, -f_x) (X sang phải, Y xuống dưới nên quay trái là (f_y, -f_x))
    Với h = -90° (đế ở mép dưới nhìn lên) công thức này trở về: x_robot = (base_y - Y), y_robot = (base_x - X).
    """
    c = cfg or ARM_CONFIG
    h = math.radians(c.get("base_heading_deg", -90.0))
    fx, fy = math.cos(h), math.sin(h)
    dx, dy = x_cm - c["base_x_cm"], y_cm - c["base_y_cm"]
    return (dx * fx + dy * fy) * 10.0, (dx * fy - dy * fx) * 10.0


def robot_mm_to_table_cm(x_robot_mm, y_robot_mm, cfg=None):
    """Đổi ngược từ tọa độ (x_mm, y_mm) hệ gốc Robot sang tọa độ (X_cm, Y_cm) trên tờ giấy A4."""
    c = cfg or ARM_CONFIG
    h = math.radians(c.get("base_heading_deg", -90.0))
    fx, fy = math.cos(h), math.sin(h)
    xr, yr = x_robot_mm / 10.0, y_robot_mm / 10.0
    return c["base_x_cm"] + xr * fx + yr * fy, c["base_y_cm"] + xr * fy - yr * fx


def predict_tip(servo_angles, cfg=None):
    """Điểm kẹp theo mô hình ứng với góc 3 servo đế / vai / khuỷu: (X_cm, Y_cm trên tờ giấy, z_mm so với mặt bàn)."""
    c = cfg or ARM_CONFIG
    theta1, theta2, theta3 = arduino_servo_to_joint((servo_angles[0], servo_angles[1], servo_angles[2], GRIP_OPEN_DEG), c)
    x_mm, y_mm, z_mm = fk_4dof_joint(theta1, theta2, theta3, c)
    x_cm, y_cm = robot_mm_to_table_cm(x_mm, y_mm, c)
    return x_cm, y_cm, z_mm


# ==============================================================================
# 3. LỆNH BẤM PHÍM: từ góc hiện tại tới góc cần tới
# ==============================================================================
# Khớp -> (phím tăng góc, phím giảm góc). Trái / phải nhìn theo cam NGANG (MacBook nhìn từ phía trước vào robot): D = sang trái, A = sang phải
KEYS = {"base": ("a", "d"), "shoulder": ("w", "s"), "elbow": ("i", "k")}
WORDS = {  # phím -> (lời chỉ, hướng mũi tên)
    "d": ("SANG TRAI", "left"), "a": ("SANG PHAI", "right"),
    "w": ("NANG LEN", "up"), "s": ("HA XUONG", "down"),
    "i": ("KHUYU LEN", "up"), "k": ("KHUYU XUONG", "down"),
}
LABELS = {"base": "DE (xoay)", "shoulder": "VAI", "elbow": "KHUYU"}
ARM_JOINTS = ("base", "shoulder", "elbow")  # Kẹp không tính trong bản đơn giản


@dataclass
class Move:
    """Việc cần làm với MỘT servo: bấm phím `key` `steps` lần để đi từ góc `now` tới góc `goal`."""
    joint: str      # "base" | "shoulder" | "elbow"
    label: str      # Tên hiện trên màn hình
    now: int        # Góc hiện tại (độ)
    goal: int       # Góc cần tới (độ)
    step: int       # Mỗi lần bấm phím quay bao nhiêu độ
    key: str        # Phím cần bấm ("a", "d", "w", "s", "i", "k"); None khi đã đúng góc
    steps: int      # Số lần bấm (làm tròn xuống, phần lẻ nhỏ hơn 1 bước bỏ qua)
    degrees: int    # Độ lệch thật |goal - now|
    words: str      # Lời chỉ ("SANG TRAI")
    arrow: str      # Hướng mũi tên ("left", "right", "up", "down")


def plan_moves(now, goal):
    """3 Move (đế, vai, khuỷu) từ góc hiện tại `now` tới góc cần tới `goal` (mỗi danh sách ít nhất 3 góc)."""
    moves = []
    for ch, joint in enumerate(ARM_JOINTS):
        delta = int(round(goal[ch] - now[ch]))
        step = SERVO_STEPS[joint]
        key = None if delta == 0 else KEYS[joint][0 if delta > 0 else 1]
        words, arrow = WORDS.get(key, ("", ""))
        moves.append(Move(joint, LABELS[joint], int(now[ch]), int(goal[ch]), step, key, abs(delta) // step, abs(delta), words, arrow))
    return moves


# ==============================================================================
# 4. CỔNG USB SERIAL TỚI ARDUINO (TƯƠNG THÍCH CẢ FIRMWARE CŨ LẪN MỚI)
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

    READ_RETRY_S = 0.3             # Lỗi đọc tạm thời: đợi chừng này rồi đọc lại, không đóng cổng
    READ_ERRORS_BEFORE_REOPEN = 5  # Lỗi đọc liên tiếp ngần này lần mà cổng vẫn còn thì mới mở lại cổng
    PORT_WAIT_S = 1.5              # Chưa thấy / chưa mở được cổng: đợi chừng này rồi thử lại
    RESET_UPTIME_DROP_MS = 1500    # Thời gian chạy "t" của firmware tụt quá ngần này ms: Arduino vừa reset

    def __init__(self, baud=9600, enabled=True):
        self.baud = baud
        self.enabled = enabled  # False: không bao giờ mở cổng Serial (test, chạy thử khi đang ngắt cánh tay)
        self.port = None
        self.ser = None
        self.connected = False
        self.servo = [90, 90, 90, 95]  # [angleBase, angleShoulder, angleElbow, angleGrip]
        self.last_cmd = ""
        self.last_rx_time = 0.0
        self.relaxed = False  # Servo kẹp đang nghỉ (firmware đã ngắt xung PWM để nguội)
        self.arm_relaxed = False  # Firmware đã ngắt xung 3 servo đế / vai / khuỷu (phím z): góc báo về chỉ là góc lệnh cuối, cánh tay có thể đã sụp xuống
        self.firmware_has_arm_relax = False  # Đã thấy trường "armrelax" trong JSON: firmware đang chạy có phím z (firmware cũ bỏ qua phím z)
        # Arduino Uno tự reset mỗi khi đường DTR của cổng USB bị hạ rồi nâng lên (VD chương trình khác mở / đóng cổng): cả 4 servo giật về
        # 90/90/90/95. Nhận ra bằng thời gian chạy "t" (millis) trong gói JSON bất ngờ tụt về gần 0.
        self.last_firmware_ms = None
        self.reset_count = 0
        self.lock = threading.Lock()
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        if enabled:
            self.thread.start()

    def _find_port(self):
        ports = sorted(glob.glob("/dev/cu.usbmodem*") + glob.glob("/dev/cu.usbserial*"))
        return ports[0] if ports else None

    def apply_key_locally(self, cmd):
        """Áp dụng đúng logic switch(cmd) của Arduino (bước SERVO_STEPS) để cập nhật góc servo."""
        c = cmd.lower()
        lim = SERVO_LIMITS
        with self.lock:
            b, s, e, g = self.servo
            if c in ("a", "d", "w", "s", "i", "k", "h"):
                self.arm_relaxed = False  # Phím di chuyển đế / vai / khuỷu (hoặc h) cấp xung lại cho cánh tay đang nghỉ
            if c == "a":
                b = min(lim["base"][1], max(lim["base"][0], b + SERVO_STEPS["base"]))
            elif c == "d":
                b = min(lim["base"][1], max(lim["base"][0], b - SERVO_STEPS["base"]))
            elif c == "w":
                s = min(lim["shoulder"][1], max(lim["shoulder"][0], s + SERVO_STEPS["shoulder"]))
            elif c == "s":
                s = min(lim["shoulder"][1], max(lim["shoulder"][0], s - SERVO_STEPS["shoulder"]))
            elif c == "i":
                e = min(lim["elbow"][1], max(lim["elbow"][0], e + SERVO_STEPS["elbow"]))
            elif c == "k":
                e = min(lim["elbow"][1], max(lim["elbow"][0], e - SERVO_STEPS["elbow"]))
            elif c == "j":
                g = min(lim["grip"][1], max(lim["grip"][0], g - SERVO_STEPS["grip"]))
                self.relaxed = False
            elif c == "l":
                g = min(lim["grip"][1], max(lim["grip"][0], g + SERVO_STEPS["grip"]))
                self.relaxed = False
            elif c == "h":
                b, s, e, g = 90, 90, 90, GRIP_OPEN_DEG
                self.relaxed = False
            elif c == "x":
                self.relaxed = True
            elif c == "z":
                self.arm_relaxed = True
                self.relaxed = True
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

    def _track_firmware_uptime(self, t_ms):
        """Gọi khi đang giữ self.lock: thời gian chạy "t" của firmware tụt xuống nghĩa là Arduino vừa reset (kể cả do chương trình khác)."""
        if not isinstance(t_ms, (int, float)):
            return
        last, self.last_firmware_ms = self.last_firmware_ms, float(t_ms)
        if last is not None and t_ms < last - self.RESET_UPTIME_DROP_MS:
            self.reset_count += 1
            print("⚠️ Arduino vừa reset (thời gian chạy của firmware quay về 0): cánh tay giật về 90/90/90/95, kiểm tra trước khi bấm tiếp")

    def _parse_line(self, line):
        line = line.strip()
        if not line:
            return
        # 1. Gói JSON từ hàm sendServoState(): {"t":1234,"servo":[90,90,90,95],"relax":0} ("relax" chỉ có ở firmware mới)
        if line.startswith("{") and "servo" in line:
            try:
                data = json.loads(line)
                arr = data.get("servo", [])
                if len(arr) >= 4:
                    with self.lock:
                        self.servo = [int(arr[0]), int(arr[1]), int(arr[2]), int(arr[3])]
                        self.relaxed = bool(data.get("relax", 0))
                        self.arm_relaxed = bool(data.get("armrelax", 0))  # Chỉ có ở firmware có phím z
                        self.firmware_has_arm_relax = self.firmware_has_arm_relax or "armrelax" in data
                        self._track_firmware_uptime(data.get("t"))
                        self.last_rx_time = time.time()
                return
            except Exception:
                pass

        # 2. Thông báo khởi động lại từ Arduino: "Robot Arm Ready! WASD + IK + JL + X (nghi kep) + Z (nghi het)"
        if "Robot Arm Ready" in line:
            print(f"🤖 Arduino báo: {line}")  # Banner cho biết đang chạy bản firmware nào (có phím X / Z hay chưa)
            with self.lock:
                self.servo = [90, 90, 90, 95]
                self.relaxed = False
                self.arm_relaxed = False
                self.last_rx_time = time.time()
            return

        # 3. Tương thích trực tiếp với dòng Serial.print("Phím bấm: "); Serial.println(cmd); trong code gốc!
        m = re.search(r"Ph.*m\s*b.*m:\s*([a-zA-Z])", line)
        if m:
            cmd_char = m.group(1)
            self.apply_key_locally(cmd_char)
            with self.lock:
                self.last_rx_time = time.time()

    def _port_exists(self):
        return self.port is not None and os.path.exists(self.port)

    def _open_port(self):
        """
        Mở cổng Serial rồi thay tay cầm cũ (nếu có) bằng tay cầm mới; True nếu mở được. Luôn mở tay cầm MỚI trước rồi mới đóng tay cầm
        cũ: lúc đó đường DTR không bị hạ xuống rồi nâng lên, đúng nhịp làm Arduino Uno tự reset và cả 4 servo giật về 90/90/90/95.
        """
        port = self._find_port()
        new = None
        if port:
            try:
                new = serial.Serial(port, self.baud, timeout=0.15)
            except Exception:
                new = None
        old, self.ser = self.ser, new
        self.connected = new is not None
        if old is not None:
            try:
                old.close()
            except Exception:
                pass
        if new is None:
            return False
        self.port = port
        print(f"🔌 Đã kết nối USB Serial Arduino tại {port} @ {self.baud} baud")
        return True

    def _loop(self):
        if serial is None:
            return
        read_errors = 0
        while self.running:
            if not self.connected or self.ser is None:
                if not self._open_port():
                    time.sleep(self.PORT_WAIT_S)
                    continue
                read_errors = 0

            try:
                raw = self.ser.readline()
                read_errors = 0
                if raw:
                    text = raw.decode("utf-8", errors="ignore")
                    self._parse_line(text)
            except Exception:
                read_errors += 1
                if self._port_exists() and read_errors < self.READ_ERRORS_BEFORE_REOPEN:
                    # Lỗi đọc thoáng qua (VD chương trình khác vừa mở cổng): đọc lại, đừng đóng cổng kẻo Arduino bị reset
                    time.sleep(self.READ_RETRY_S)
                    continue
                read_errors = 0
                if not self._open_port():
                    time.sleep(self.PORT_WAIT_S)

    def get_state(self):
        with self.lock:
            return list(self.servo), self.connected, self.port, self.last_cmd

    def get_arm_relaxed(self):
        """True khi cả cánh tay đang nghỉ (đã ngắt xung bằng phím z): đừng tin góc servo báo về, bấm phím di chuyển để cấp xung lại."""
        with self.lock:
            return self.arm_relaxed

    def get_reset_count(self):
        """Số lần Arduino bị reset bất ngờ kể từ khi chạy chương trình (thấy qua thời gian chạy của firmware tụt về 0)."""
        with self.lock:
            return self.reset_count

    def release(self):
        self.running = False
        if self.ser is not None:
            try:
                self.ser.close()
            except Exception:
                pass


# ==============================================================================
# 5. ĐIỀU KHIỂN: chọn vật mục tiêu rồi lập kế hoạch bấm phím
# ==============================================================================
@dataclass
class Plan:
    """Kết quả của NHÓM 1 mỗi khung hình, chuyển sang NHÓM 2 (success.py)."""
    found: bool                 # Có vật mục tiêu không
    target_name: str            # Tên vật mục tiêu
    target_cm: tuple            # (x, y) vật trên tờ giấy (cm), None khi chưa thấy vật
    reachable: bool             # Vật nằm trong tầm với của cánh tay
    move_closer_mm: float       # Nếu ngoài tầm: cần dời vật lại gần đế thêm bao nhiêu mm
    relaxed: bool               # Cánh tay đang nghỉ (đã ngắt xung bằng phím Z)
    now: list                   # 4 góc servo hiện tại [đế, vai, khuỷu, kẹp]
    goal: list                  # 3 góc cần tới [đế, vai, khuỷu]
    moves: list                 # 3 Move (đế, vai, khuỷu)
    usb_ok: bool = False
    port: str = None
    n_objects: int = 0
    selected_idx: int = 0
    banner: str = ""


class Control:
    """Gom cổng USB + chọn vật + tính góc cần tới. Gọi update(objects) mỗi khung hình, press(key) khi có phím."""

    def __init__(self, serial_enabled=True):
        self.link = ArduinoSerialLink(baud=9600, enabled=serial_enabled)
        self.objects = []            # Các vật camera đang thấy, đã sắp theo khoảng cách tới đế
        self.selected = None         # Vật đang chọn lần cuối thấy rõ: {"x_cm", "y_cm", "name", "ts"}
        self.selected_idx = 0
        self.history = deque(maxlen=10)  # Trung bình trượt 10 khung vị trí vật cho khỏi nhảy theo nhiễu
        self.seen_resets = 0
        self.banner = ""

    # --- chọn vật mục tiêu -------------------------------------------------
    def _pick(self, objects):
        """Chỉ số vật cần chọn: vật gần vị trí vật chọn trước đó nhất (trong SELECT_TRACK_CM), không có thì vật gần đế nhất."""
        if self.selected is not None:
            dists = [math.hypot(o["x_cm"] - self.selected["x_cm"], o["y_cm"] - self.selected["y_cm"]) for o in objects]
            best = int(np.argmin(dists))
            if dists[best] <= SELECT_TRACK_CM:
                return best
        return 0

    def _track(self, objects, now):
        """Cập nhật vật đang chọn từ các vật mới thấy. Không thấy vật nào (càng kẹp che mất) thì giữ vật cũ TARGET_MEMORY_S giây."""
        base = (ARM_CONFIG["base_x_cm"], ARM_CONFIG["base_y_cm"])
        self.objects = sorted(objects, key=lambda o: math.hypot(o["x_cm"] - base[0], o["y_cm"] - base[1]))
        if not self.objects:
            return
        idx = self._pick(self.objects)
        obj = self.objects[idx]
        moved = self.selected is None or math.hypot(obj["x_cm"] - self.selected["x_cm"], obj["y_cm"] - self.selected["y_cm"]) > SELECT_TRACK_CM
        if moved:
            self.history.clear()  # Đổi sang vật khác / vật bị dời đi: bỏ trung bình của vị trí cũ
        self.history.append((obj["x_cm"], obj["y_cm"]))
        mean = np.mean(self.history, axis=0)
        self.selected_idx = idx
        self.selected = {"x_cm": float(mean[0]), "y_cm": float(mean[1]), "name": obj["name"], "ts": now}

    def next_target(self):
        """Phím TAB: chuyển sang vật tiếp theo trong danh sách."""
        if self.objects:
            self.selected_idx = (self.selected_idx + 1) % len(self.objects)
            obj = self.objects[self.selected_idx]
            self.history.clear()
            self.selected = {"x_cm": obj["x_cm"], "y_cm": obj["y_cm"], "name": obj["name"], "ts": time.time()}

    def set_base_pose(self, x_cm, y_cm, heading_deg):
        """Đặt lại vị trí trục xoay đế robot trên tờ giấy (từ hiệu chỉnh bằng chuột hoặc file calibration.json)."""
        ARM_CONFIG["base_x_cm"], ARM_CONFIG["base_y_cm"], ARM_CONFIG["base_heading_deg"] = float(x_cm), float(y_cm), float(heading_deg)

    # --- kế hoạch ----------------------------------------------------------
    def update(self, objects, now=None):
        """Nhận các vật camera thấy (x_cm, y_cm, name) và trả về Plan: góc cần tới và việc cần bấm."""
        now = time.time() if now is None else now
        self._track(objects, now)
        servo_now, usb_ok, port, _ = self.link.get_state()
        resets = self.link.get_reset_count()
        if resets != self.seen_resets:  # Cánh tay vừa giật về 90/90/90/95 mà người dùng không bấm gì: báo để kiểm tra trước khi bấm tiếp
            self.seen_resets = resets
            self.banner = "ARDUINO VUA RESET: canh tay giat ve 90/90/90, kiem tra truoc khi bam tiep"
        target = self.selected if self.selected is not None and now - self.selected["ts"] <= TARGET_MEMORY_S else None
        base = dict(now=list(servo_now), usb_ok=usb_ok, port=port, n_objects=len(self.objects), selected_idx=self.selected_idx,
                    relaxed=self.link.get_arm_relaxed(), banner=self.banner)
        if target is None:
            return Plan(found=False, target_name="", target_cm=None, reachable=True, move_closer_mm=0.0, goal=list(servo_now[:3]),
                        moves=plan_moves(servo_now, servo_now), **base)
        rx, ry = table_cm_to_robot_mm(target["x_cm"], target["y_cm"])
        ik = ik_4dof_joint(rx, ry, GRASP_Z_MM)
        goal = joint_to_servo(ik["theta1_deg"], ik["theta2_deg"], ik["theta3_deg"])
        return Plan(found=True, target_name=target["name"], target_cm=(target["x_cm"], target["y_cm"]), reachable=bool(ik["reachable"]),
                    move_closer_mm=float(ik["move_closer_mm"]), goal=goal, moves=plan_moves(servo_now, goal), **base)

    def press(self, key):
        """Gửi một phím điều khiển xuống Arduino (hoặc cập nhật mô phỏng nếu chưa nối USB). Trả về True nếu là phím điều khiển."""
        ch = (key or "")[:1].lower()
        if not ch or ch not in "wasdikjlhxz":
            return False
        if ch == "z" and self.link.connected and not self.link.firmware_has_arm_relax:
            # Firmware cũ bỏ qua phím z: gửi đi cũng không ngắt xung, mà người dùng sẽ tưởng servo đã nghỉ nên phải nói rõ
            self.banner = "FIRMWARE CU KHONG CO PHIM Z: servo van co xung. Nap lai bang flash.sh"
            print("⚠️ Firmware đang chạy chưa có phím Z (nghỉ hết): servo vẫn còn xung. Nạp lại bằng ./robot_arm_4dof/flash.sh (phím X chỉ cho servo kẹp nghỉ)")
            return True
        self.link.send_key(ch)
        return True

    def release(self):
        self.link.release()
