#!/usr/bin/env python3
"""
KHỐI ĐIỀU KHIỂN: vật ở đâu -> servo phải quay tới góc nào -> bấm phím gì, mấy lần.

    vật (x, y cm trên tờ giấy) --IK--> 3 góc servo cần tới --so với góc hiện tại--> "bấm phím D x8, S x16 ..."

Phần này lo toàn bộ việc ĐIỀU KHIỂN cánh tay:
  1. Hình học cánh tay: động học thuận / ngược (FK / IK), đổi góc khớp <-> góc servo Arduino, đổi tọa độ tờ giấy <-> hệ robot.
  2. Cổng USB tới Arduino: gửi phím (W A S D I K J L H X Z), đọc góc servo thật mà firmware báo về.
  3. Phím R chụp vị trí vật gần đế nhất làm đích và tính góc cần tới MỘT lần; mỗi khung so góc servo hiện tại với góc đó ra lệnh bấm phím (Move).
Kết quả mỗi khung hình là một Plan, chuyển cho khối success (success.py) để kết luận "đã tới chưa".
Phần nhìn (camera, ArUco, tìm vật) nằm ở vision.py; phần vẽ màn hình ở screen.py; main.py nối các phần lại.
"""

import glob
import json
import math
import os
import threading
import time
from dataclasses import dataclass, field

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
    "base": (0, 180, 180),      # Kênh 0: Đế (a: +2° , d: -2°); Home 180° = quay hết sang phải, không che vật ở cam TRÊN
    "shoulder": (25, 155, 90),  # Kênh 1: Vai (w: +2° nâng lên, s: -2° hạ xuống)
    "elbow": (25, 155, 90),     # Kênh 2: Khuỷu (i: +2° lên, k: -2° xuống)
    "grip": (95, 160, 95),      # Kênh 3: Kẹp (j: -5° mở ra, l: +5° kẹp vào)
}
SERVO_STEPS = {"base": 2, "shoulder": 2, "elbow": 2, "grip": 5}
SERVO_ANCHORS = {"base": 90, "shoulder": 90, "elbow": 90, "grip": 95}  # Neo lưới góc: mọi góc bấm tới được = neo + k * bước (Home ở cột 3 của SERVO_LIMITS)
GRIP_OPEN_DEG = 95

GRASP_Z_MM = 25.0        # Độ cao điểm kẹp mục tiêu (mm): nửa thân cốc, đúng độ cao dùng khi hiệu chỉnh hình học bằng các lần ôm


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
WORDS = {"d": "SANG TRAI", "a": "SANG PHAI", "w": "NANG LEN", "s": "HA XUONG", "i": "KHUYU LEN", "k": "KHUYU XUONG"}  # phím -> lời chỉ
# Phím -> (servo, +1 tăng góc / -1 giảm góc), giống switch(cmd) trong firmware: dùng để MÔ PHỎNG khi chưa cắm USB
KEY_MOVES = {"a": ("base", 1), "d": ("base", -1), "w": ("shoulder", 1), "s": ("shoulder", -1),
             "i": ("elbow", 1), "k": ("elbow", -1), "l": ("grip", 1), "j": ("grip", -1)}
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


def plan_moves(now, goal):
    """3 Move (đế, vai, khuỷu) từ góc hiện tại `now` tới góc cần tới `goal` (mỗi danh sách ít nhất 3 góc)."""
    moves = []
    for ch, joint in enumerate(ARM_JOINTS):
        delta = int(round(goal[ch] - now[ch]))
        step = SERVO_STEPS[joint]
        key = None if delta == 0 else KEYS[joint][0 if delta > 0 else 1]
        moves.append(Move(joint, LABELS[joint], int(now[ch]), int(goal[ch]), step, key, abs(delta) // step, abs(delta), WORDS.get(key, "")))
    return moves


# ==============================================================================
# 4. CỔNG USB SERIAL TỚI ARDUINO
# ==============================================================================
# Windows / Linux: chỉ xét cổng USB thật (có VID), bỏ cổng Bluetooth ảo và cổng modem của điện thoại cắm USB
NOT_ARDUINO_PORT_WORDS = ("modem", "mobile", "bluetooth")
ARDUINO_PORT_HINTS = ("arduino", "ch340", "ch341", "cp210", "ftdi", "usb serial", "usb-serial")


def find_arduino_port():
    """
    Cổng USB của Arduino, None nếu chưa cắm cáp. macOS: /dev/cu.usbmodem* / /dev/cu.usbserial* (như trước);
    Windows: COMx, Linux: /dev/ttyACM* ... lấy từ danh sách cổng của pyserial, ưu tiên cổng có tên Arduino / CH340 / CP210x / FTDI.
    """
    mac_ports = sorted(glob.glob("/dev/cu.usbmodem*") + glob.glob("/dev/cu.usbserial*"))
    if mac_ports:
        return mac_ports[0]
    if serial is None:
        return None
    try:
        from serial.tools import list_ports

        ports = [
            p for p in list_ports.comports()
            if p.vid is not None and not any(w in f"{p.description} {p.manufacturer or ''}".lower() for w in NOT_ARDUINO_PORT_WORDS)
        ]
    except Exception:
        return None

    def rank(p):
        text = f"{p.description} {p.manufacturer or ''}".lower()
        return (0 if any(h in text for h in ARDUINO_PORT_HINTS) else 1, p.device)

    return min(ports, key=rank).device if ports else None


class ArduinoSerialLink:
    """
    Cổng USB tới Arduino (9600 baud), đọc ở luồng nền.
    - Gửi phím: mỗi lần bấm một ký tự (w a s d i k j l h x z).
    - Nhận gói JSON firmware gửi ngay sau mỗi phím và 5 lần / giây: {"t": ms, "servo": [đế, vai, khuỷu, kẹp], "relax": 0|1, "armrelax": 0|1}.
    - Chưa cắm cáp (hoặc enabled=False): MÔ PHỎNG, tự cộng / trừ góc như firmware để vẫn chạy được camera + IK + màn hình.
    - Arduino Uno tự reset mỗi khi đường DTR của cổng USB hạ rồi nâng (VD chương trình khác mở / đóng cổng): cả 4 servo giật về Home.
      Nhận ra bằng thời gian chạy "t" tụt về gần 0; khi phải mở lại cổng thì mở tay cầm MỚI trước rồi mới đóng tay cầm cũ.
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
        self.servo = [SERVO_LIMITS[k][2] for k in CHANNEL_KEYS]  # [đế, vai, khuỷu, kẹp] = Home lúc Arduino khởi động
        self.relaxed = False      # Servo kẹp đang nghỉ (firmware đã ngắt xung PWM để nguội)
        self.arm_relaxed = False  # Cả cánh tay đang nghỉ (phím z): góc báo về chỉ là góc lệnh cuối, cánh tay có thể đã sụp xuống
        self.last_firmware_ms = None
        self.reset_count = 0
        self.lock = threading.Lock()
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        if enabled:
            self.thread.start()

    def _find_port(self):
        return find_arduino_port()

    def apply_key_locally(self, cmd):
        """MÔ PHỎNG một phím như firmware: đổi góc trong giới hạn, H về Home, X cho kẹp nghỉ, Z cho cả 4 servo nghỉ."""
        c = cmd.lower()
        with self.lock:
            if c in KEY_MOVES:
                joint, sign = KEY_MOVES[c]
                ch = CHANNEL_KEYS.index(joint)
                lo, hi, _ = SERVO_LIMITS[joint]
                self.servo[ch] = min(hi, max(lo, self.servo[ch] + sign * SERVO_STEPS[joint]))
            elif c == "h":
                self.servo = [SERVO_LIMITS[k][2] for k in CHANNEL_KEYS]
            if c in ("a", "d", "w", "s", "i", "k", "h"):
                self.arm_relaxed = False  # Phím di chuyển (hoặc h) cấp xung lại cho cánh tay đang nghỉ
            if c in ("j", "l", "h"):
                self.relaxed = False
            if c in ("x", "z"):
                self.relaxed = True
            if c == "z":
                self.arm_relaxed = True

    def send_key(self, cmd):
        """Gửi 1 ký tự lệnh xuống Arduino; chưa cắm USB thì cập nhật mô phỏng."""
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
        self.apply_key_locally(ch)

    def _track_firmware_uptime(self, t_ms):
        """Gọi khi đang giữ self.lock: thời gian chạy "t" của firmware tụt xuống nghĩa là Arduino vừa reset (kể cả do chương trình khác)."""
        if not isinstance(t_ms, (int, float)):
            return
        last, self.last_firmware_ms = self.last_firmware_ms, float(t_ms)
        if last is not None and t_ms < last - self.RESET_UPTIME_DROP_MS:
            self.reset_count += 1
            print("⚠️ Arduino vừa reset (thời gian chạy của firmware quay về 0): cánh tay giật về Home 180/90/90/95, kiểm tra trước khi bấm tiếp")

    def _parse_line(self, line):
        """Đọc gói JSON trạng thái. Dòng khác (banner khởi động, "Phím bấm: x") bỏ qua: gói JSON luôn đến ngay sau đó."""
        line = line.strip()
        if not line.startswith("{"):
            return
        try:
            data = json.loads(line)
            servo = [int(v) for v in data["servo"]]
        except (ValueError, KeyError, TypeError):
            return
        if len(servo) < 4:
            return
        with self.lock:
            self.servo = servo[:4]
            self.relaxed = bool(data.get("relax", 0))
            self.arm_relaxed = bool(data.get("armrelax", 0))
            self._track_firmware_uptime(data.get("t"))

    def _port_exists(self):
        if self.port is None:
            return False
        if not self.port.upper().startswith("COM"):
            return os.path.exists(self.port)
        # Windows: COMx không phải đường dẫn tệp nên hỏi danh sách cổng (không thì lỗi đọc thoáng qua nào cũng mở lại cổng, Arduino bị reset)
        try:
            from serial.tools import list_ports

            return any(p.device.upper() == self.port.upper() for p in list_ports.comports())
        except Exception:
            return False

    def _open_port(self):
        """
        Mở cổng Serial rồi thay tay cầm cũ (nếu có) bằng tay cầm mới; True nếu mở được. Luôn mở tay cầm MỚI trước rồi mới đóng tay cầm
        cũ: lúc đó đường DTR không bị hạ xuống rồi nâng lên, đúng nhịp làm Arduino Uno tự reset và cả 4 servo giật về Home 180/90/90/95.
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
        """(4 góc servo, đã nối USB chưa, tên cổng)."""
        with self.lock:
            return list(self.servo), self.connected, self.port

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
# 5. ĐIỀU KHIỂN: phím R chụp đích rồi lập kế hoạch bấm phím
# ==============================================================================
@dataclass
class Plan:
    """Kết quả của khối điều khiển mỗi khung hình, chuyển sang khối success (success.py)."""
    found: bool                 # Đã có đích chưa (bấm R lúc camera thấy vật)
    target_name: str            # Tên vật làm đích
    target_cm: tuple            # (x, y) vật trên tờ giấy (cm) lúc bấm R, None khi chưa có đích
    reachable: bool             # Vật nằm trong tầm với của cánh tay
    move_closer_mm: float       # Nếu ngoài tầm: cần dời vật lại gần đế thêm bao nhiêu mm
    relaxed: bool               # Cánh tay đang nghỉ (đã ngắt xung bằng phím Z)
    now: list                   # 4 góc servo hiện tại [đế, vai, khuỷu, kẹp]
    goal: list                  # 3 góc cần tới [đế, vai, khuỷu]
    moves: list                 # 3 Move (đế, vai, khuỷu)
    usb_ok: bool = False
    port: str = None
    n_objects: int = 0
    banner: str = ""


class Control:
    """Gom cổng USB + đích chụp bằng phím R + so góc servo với góc đích. Gọi update(objects) mỗi khung hình, press(key) khi có phím."""

    def __init__(self, serial_enabled=True):
        self.link = ArduinoSerialLink(baud=9600, enabled=serial_enabled)
        self.objects = []    # Các vật camera đang thấy, đã sắp theo khoảng cách tới đế
        self.target = None   # Đích chụp bằng phím R (vị trí vật + góc cần tới tính một lần); None = chưa chụp
        self.seen_resets = 0
        self.banner = ""

    # --- đích: phím R ----------------------------------------------------------
    def lock_target(self):
        """Phím R: lấy vật gần đế nhất trong ảnh lúc bấm làm đích và tính góc cần tới MỘT lần (không theo camera nữa).
        Vật bị dời thì bấm R lại. Trả về "locked" hoặc "no_target" (camera chưa thấy vật nào)."""
        if not self.objects:
            return "no_target"
        obj = self.objects[0]
        rx, ry = table_cm_to_robot_mm(obj["x_cm"], obj["y_cm"])
        ik = ik_4dof_joint(rx, ry, GRASP_Z_MM)
        self.target = {"name": obj["name"], "cm": (obj["x_cm"], obj["y_cm"]), "reachable": bool(ik["reachable"]),
                       "move_closer_mm": float(ik["move_closer_mm"]),
                       "goal": joint_to_servo(ik["theta1_deg"], ik["theta2_deg"], ik["theta3_deg"])}
        return "locked"

    def set_base_pose(self, x_cm, y_cm, heading_deg):
        """Đặt lại vị trí trục xoay đế robot trên tờ giấy (hiệu chỉnh bằng chuột). Góc đích cũ không còn đúng: bỏ, bấm R lại."""
        ARM_CONFIG["base_x_cm"], ARM_CONFIG["base_y_cm"], ARM_CONFIG["base_heading_deg"] = float(x_cm), float(y_cm), float(heading_deg)
        self.target = None

    # --- kế hoạch ----------------------------------------------------------
    def update(self, objects):
        """Nhận các vật camera thấy (x_cm, y_cm, name) và trả về Plan: góc servo hiện tại so với góc đích đã chụp bằng R."""
        base_xy = (ARM_CONFIG["base_x_cm"], ARM_CONFIG["base_y_cm"])
        self.objects = sorted(objects, key=lambda o: math.hypot(o["x_cm"] - base_xy[0], o["y_cm"] - base_xy[1]))
        servo_now, usb_ok, port = self.link.get_state()
        resets = self.link.get_reset_count()
        if resets != self.seen_resets:  # Cánh tay vừa giật về Home 180/90/90/95 mà người dùng không bấm gì: báo để kiểm tra trước khi bấm tiếp
            self.seen_resets = resets
            self.banner = "ARDUINO VUA RESET: canh tay giat ve Home 180/90/90, kiem tra truoc khi bam tiep"
        base = dict(now=list(servo_now), usb_ok=usb_ok, port=port, n_objects=len(self.objects),
                    relaxed=self.link.get_arm_relaxed(), banner=self.banner)
        t = self.target
        if t is None:
            return Plan(found=False, target_name="", target_cm=None, reachable=True, move_closer_mm=0.0, goal=list(servo_now[:3]),
                        moves=plan_moves(servo_now, servo_now), **base)
        return Plan(found=True, target_name=t["name"], target_cm=t["cm"], reachable=t["reachable"], move_closer_mm=t["move_closer_mm"],
                    goal=list(t["goal"]), moves=plan_moves(servo_now, t["goal"]), **base)

    def press(self, key):
        """Gửi một phím điều khiển xuống Arduino (hoặc cập nhật mô phỏng nếu chưa nối USB). Trả về True nếu là phím điều khiển."""
        ch = (key or "")[:1].lower()
        if not ch or ch not in "wasdikjlhxz":
            return False
        self.link.send_key(ch)
        return True

    def release(self):
        self.link.release()
