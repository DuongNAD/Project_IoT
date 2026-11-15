#!/usr/bin/env python3
"""
KHỐI ĐIỀU KHIỂN: vật ở đâu -> servo phải quay tới góc nào -> bấm phím gì, mấy lần.

    vật (x, y cm trên tờ giấy) --IK--> 3 góc servo cần tới --so với góc hiện tại--> "bấm phím A x55, S x6, K x24"

Phần này lo toàn bộ việc ĐIỀU KHIỂN cánh tay:
  1. Hình học cánh tay: đổi tọa độ tờ giấy -> hệ robot, động học ngược (IK) bằng hai tam giác, đổi góc khớp -> góc servo Arduino.
  2. Cổng USB tới Arduino: gửi phím (W A S D I K J L H), đọc góc servo firmware báo về (góc đã ra lệnh: MG996R không đo được góc thật).
  3. Phím R chụp vị trí vật gần đế nhất làm đích và tính góc cần tới MỘT lần; mỗi khung so góc servo hiện tại với góc đó ra lệnh bấm phím (Move).
Kết quả mỗi khung hình là một Plan, chuyển cho khối success (success.py) để kết luận "đã tới chưa".
Phần nhìn (camera, ArUco, tìm vật) nằm ở vision.py; phần vẽ màn hình ở screen.py; main.py nối các phần lại.
"""

import json
import math
import threading
from dataclasses import dataclass

import serial


# ==============================================================================
# 1. HÌNH HỌC CÁNH TAY 4 SERVO (MG996R + PCA9685)
# ==============================================================================
# SỐ ĐO CÁNH TAY: số đã KHỚP từ 10 lần ôm cốc thật (sai số ~8,5 mm), bù vai +2° sau lần gắp thử; vị trí đế kiểm tra lại 15/11 (lệch 0,6 cm).
# Không thay bằng số đo thước: d1 / L3 / góc chuẩn là số "tương đương" đã bù lệch thật của cánh tay. Sửa số thì sửa ngay tại đây.
ARM_CONFIG = {
    "d1_mm": 70.0,              # Mặt bàn -> trục vai
    "L2_mm": 105.0,             # Vai -> khuỷu
    "L3_mm": 183.7,             # Khuỷu -> tâm 2 ngón kẹp (kẹp gắn cứng vào khâu khuỷu nên gộp vào đây)
    # Trục xoay đế trên tờ giấy (gốc = góc ngoài mã ArUco ID 0, X: ID 0 -> ID 1, Y: ID 0 -> ID 3) và hướng robot nhìn
    "base_x_cm": 15.87,
    "base_y_cm": -10.67,        # Robot đứng ngoài mép Y = 0 (phía mã ID 0, 1), nhìn vào tờ giấy
    "base_heading_deg": 87.6,
    "theta2_at_90_deg": 62.2,   # Khâu vai nghiêng 62,2° khi servo vai ở 90°
    "theta3_at_90_deg": -58.6,  # Khâu khuỷu gập -58,6° so với khâu vai khi servo khuỷu ở 90°
}
MAX_MISS_MM = 20  # Vật quá gần đế: khuỷu chạm giới hạn mà đầu kẹp vẫn hụt hơn ngần này thì báo ngoài tầm

# Servo: giới hạn an toàn và bước mỗi lần bấm phím, khớp robot_arm_4dof.ino (STEP_ARM = 2, STEP_GRIP = 5, GRIP_CLOSE_LIMIT = 160)
CHANNEL_KEYS = ("base", "shoulder", "elbow", "grip")  # Thứ tự kênh 0..3 của Arduino
SERVO_LIMITS = {
    "base": (0, 180, 0),        # Kênh 0: Đế (a: +2° sang trái, d: -2° sang phải); Home 0° = quay hết sang phải, không che vật ở cam TRÊN
    "shoulder": (25, 155, 90),  # Kênh 1: Vai (w: +2° nâng lên, s: -2° hạ xuống)
    "elbow": (25, 155, 90),     # Kênh 2: Khuỷu (i: +2° lên, k: -2° xuống)
    "grip": (95, 160, 95),      # Kênh 3: Kẹp (j: -5° mở ra, l: +5° kẹp vào)
}
SERVO_STEPS = {"base": 2, "shoulder": 2, "elbow": 2, "grip": 5}
SERVO_ANCHORS = {"base": 90, "shoulder": 90, "elbow": 90, "grip": 95}  # Neo lưới góc: mọi góc bấm tới được = neo + k * bước (Home ở cột 3 của SERVO_LIMITS)

GRASP_Z_MM = 25.0  # Độ cao điểm kẹp (mm): nửa thân cốc, đúng độ cao dùng lúc khớp số đo ở trên


# ==============================================================================
# 2. ĐỘNG HỌC NGƯỢC (IK), ĐỔI GÓC KHỚP -> GÓC SERVO, ĐỔI TỌA ĐỘ
# ==============================================================================
def ik_4dof_joint(x_mm, y_mm, z_mm, cfg=None):
    """
    Động học ngược giải tích (Analytical Inverse Kinematics) cho cánh tay 4 bậc tự do.
    Trả về dict:
      - reachable (bool): Điểm (x, y, z) có nằm trong tầm với hình học không
      - theta1_deg, theta2_deg, theta3_deg: Góc khớp hình học (độ)
    """
    c = cfg or ARM_CONFIG
    L2 = c["L2_mm"]
    L3 = c["L3_mm"]

    r = math.hypot(x_mm, y_mm)
    theta1_deg = math.degrees(math.atan2(y_mm, x_mm)) if r > 1e-6 else 0.0

    r_w = max(5.0, r)          # Khoảng cách ngang vai -> đầu kẹp
    z_w = z_mm - c["d1_mm"]    # Chênh cao vai -> đầu kẹp

    D = (r_w * r_w + z_w * z_w - L2 * L2 - L3 * L3) / (2.0 * L2 * L3)  # Định lý côsin trong tam giác vai - khuỷu - đầu kẹp
    reachable = abs(D) <= 1.0

    # Kẹp D trong [-1, 1] để luôn tính ra bộ góc gần mục tiêu nhất ngay cả khi hơi quá tầm
    D_clamped = max(-1.0, min(1.0, D))
    # Nghiệm khuỷu hướng lên (elbow-up): sin(theta3) <= 0
    theta3_rad = math.atan2(-math.sqrt(max(0.0, 1.0 - D_clamped * D_clamped)), D_clamped)
    theta2_rad = math.atan2(z_w, r_w) - math.atan2(
        L3 * math.sin(theta3_rad), L2 + L3 * math.cos(theta3_rad)
    )

    return {
        "reachable": reachable,
        "theta1_deg": theta1_deg,
        "theta2_deg": math.degrees(theta2_rad),
        "theta3_deg": math.degrees(theta3_rad),
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


def tip_mm(shoulder, elbow, cfg=None):
    """Động học thuận: góc servo vai, khuỷu -> đầu kẹp (khoảng cách ngang tới trục đế, độ cao) tính bằng mm."""
    c = cfg or ARM_CONFIG
    t2 = math.radians(c["theta2_at_90_deg"] + shoulder - 90)
    t3 = t2 + math.radians(c["theta3_at_90_deg"] + elbow - 90)
    r = c["L2_mm"] * math.cos(t2) + c["L3_mm"] * math.cos(t3)
    z = c["d1_mm"] + c["L2_mm"] * math.sin(t2) + c["L3_mm"] * math.sin(t3)
    return r, z


def goal_angles(x_mm, y_mm, z_mm=None, cfg=None):
    """Điểm (x, y, z) hệ robot -> (3 góc servo cần tới, có với tới không).
    Vật gần đế: khuỷu cần gập quá giới hạn 25° nên giữ khuỷu ở giới hạn, chọn lại góc vai cho đầu kẹp tới gần vật nhất."""
    c = cfg or ARM_CONFIG
    z_mm = GRASP_Z_MM if z_mm is None else z_mm
    ik = ik_4dof_joint(x_mm, y_mm, z_mm, c)
    goal = joint_to_servo(ik["theta1_deg"], ik["theta2_deg"], ik["theta3_deg"], c)
    reachable = bool(ik["reachable"])
    elbow_raw = 90.0 + ik["theta3_deg"] - c["theta3_at_90_deg"]
    lo, hi, _ = SERVO_LIMITS["shoulder"]
    if elbow_raw < SERVO_LIMITS["elbow"][0]:
        target = (math.hypot(x_mm, y_mm), z_mm)
        miss = lambda sh: math.dist(tip_mm(sh, goal[2], c), target)
        goal[1] = min(range(lo + 1, hi, SERVO_STEPS["shoulder"]), key=miss)
        reachable = reachable and miss(goal[1]) <= MAX_MISS_MM
    return goal, reachable


def table_cm_to_robot_mm(x_cm, y_cm, cfg=None):
    """
    Đổi tọa độ điểm (X_cm, Y_cm) trên tờ giấy A4 sang tọa độ (x_mm, y_mm) trong hệ gốc Đế Robot.
    Trên tờ A4 đặt ngang (29.7 x 21.0 cm), đế robot ở (base_x_cm, base_y_cm) và nhìn theo base_heading_deg:
      - Trục +x_robot (vươn tới trước) = hướng nhìn của robot f = (cos h, sin h) trong hệ tờ giấy
      - Trục +y_robot (sang trái của đế) = f quay trái 90° = (f_y, -f_x) (X sang phải, Y xuống dưới nên quay trái là (f_y, -f_x))
    Với h = 90° (đế ở ngoài mép Y = 0 nhìn vào +Y): x_robot = (Y - base_y), y_robot = (X - base_x);
    với h = -90° (đế ở mép dưới nhìn lên): x_robot = (base_y - Y), y_robot = (base_x - X).
    """
    c = cfg or ARM_CONFIG
    h = math.radians(c.get("base_heading_deg", 90.0))
    fx, fy = math.cos(h), math.sin(h)
    dx, dy = x_cm - c["base_x_cm"], y_cm - c["base_y_cm"]
    return (dx * fx + dy * fy) * 10.0, (dx * fy - dy * fx) * 10.0


# ==============================================================================
# 3. LỆNH BẤM PHÍM: từ góc hiện tại tới góc cần tới
# ==============================================================================
# Khớp -> (phím tăng góc, phím giảm góc): A (+2°) = sang trái, D (-2°) = sang phải
KEYS = {"base": ("a", "d"), "shoulder": ("w", "s"), "elbow": ("i", "k")}
WORDS = {"a": "SANG TRAI", "d": "SANG PHAI", "w": "NANG LEN", "s": "HA XUONG", "i": "KHUYU LEN", "k": "KHUYU XUONG"}  # phím -> lời chỉ
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
class ArduinoSerialLink:
    """
    Cổng USB tới Arduino (9600 baud).
    - Gửi phím: mỗi lần bấm một ký tự (w a s d i k j l h).
    - Nhận gói JSON firmware gửi ngay sau mỗi phím và 5 lần / giây: {"servo": [đế, vai, khuỷu, kẹp]}.
      Đọc ở một luồng nền để vòng lặp chính không phải đứng chờ Arduino.
    - Không ghi cổng (port=None): MÔ PHỎNG, tự cộng / trừ góc như firmware để vẫn chạy được camera + IK + màn hình.
    - Mở cổng MỘT lần lúc chạy và không mở lại: Arduino Uno tự reset (cả 4 servo giật về Home) mỗi lần cổng được mở.
      Rút cáp USB thì cắm lại rồi chạy lại chương trình.
    """

    def __init__(self, port=None, baud=9600):
        self.servo = [SERVO_LIMITS[k][2] for k in CHANNEL_KEYS]  # [đế, vai, khuỷu, kẹp] = Home lúc Arduino khởi động
        self.ser = None
        if port is not None:
            self.ser = serial.Serial(port, baud, timeout=0.2)  # Không mở được cổng thì chương trình dừng, báo lỗi của pyserial
            print(f"🔌 Đã kết nối USB Serial Arduino tại {port} @ {baud} baud")
            threading.Thread(target=self._read_loop, daemon=True).start()
        self.connected = self.ser is not None  # Đã nối USB chưa (chân trang màn hình)

    def send_key(self, cmd):
        """Gửi 1 ký tự lệnh xuống Arduino; chưa nối USB thì cập nhật mô phỏng."""
        if self.connected:
            self.ser.write(cmd[:1].encode())
        else:
            self.apply_key_locally(cmd[:1])

    def apply_key_locally(self, c):
        """MÔ PHỎNG một phím như firmware: đổi góc trong giới hạn, H về Home."""
        if c in KEY_MOVES:
            joint, sign = KEY_MOVES[c]
            ch = CHANNEL_KEYS.index(joint)
            lo, hi, _ = SERVO_LIMITS[joint]
            self.servo[ch] = min(hi, max(lo, self.servo[ch] + sign * SERVO_STEPS[joint]))
        elif c == "h":
            self.servo = [SERVO_LIMITS[k][2] for k in CHANNEL_KEYS]

    def _read_loop(self):
        """Luồng nền: đọc từng dòng firmware gửi lên, lấy góc 4 servo."""
        while True:
            line = self.ser.readline().decode("utf-8", errors="ignore").strip()
            if not line.startswith("{"):
                continue  # Bỏ qua dòng không phải JSON (nếu Arduino đang chạy firmware cũ)
            try:
                data = json.loads(line)
                self.servo = [int(v) for v in data["servo"]][:4]
            except (ValueError, KeyError, TypeError):
                continue  # Dòng bị cắt dở: bỏ qua, 0,2 giây sau có gói mới

    def release(self):
        if self.ser is not None:
            self.ser.close()


# ==============================================================================
# 5. ĐIỀU KHIỂN: phím R chụp đích rồi lập kế hoạch bấm phím
# ==============================================================================
@dataclass
class Plan:
    """Kết quả của khối điều khiển mỗi khung hình, chuyển sang khối success (success.py)."""
    found: bool                 # Đã có đích chưa (bấm R lúc camera thấy vật)
    target_cm: tuple            # (x, y) vật trên tờ giấy (cm) lúc bấm R, None khi chưa có đích
    reachable: bool             # Vật nằm trong tầm với của cánh tay
    now: list                   # 4 góc servo hiện tại [đế, vai, khuỷu, kẹp]
    goal: list                  # 3 góc cần tới [đế, vai, khuỷu]
    moves: list                 # 3 Move (đế, vai, khuỷu)
    usb_ok: bool = False        # Đã nối USB tới Arduino chưa (chân trang màn hình)


class Control:
    """Gom cổng USB + đích chụp bằng phím R + so góc servo với góc đích. Gọi update(objects) mỗi khung hình, press(key) khi có phím."""

    def __init__(self, port=None):
        self.link = ArduinoSerialLink(port)  # port=None: mô phỏng, không gửi phím xuống robot
        self.objects = []    # Các vật camera đang thấy, đã sắp theo khoảng cách tới đế
        self.target = None   # Đích chụp bằng phím R (vị trí vật + góc cần tới tính một lần); None = chưa chụp

    # --- đích: phím R ----------------------------------------------------------
    def lock_target(self):
        """Phím R: lấy vật gần đế nhất trong ảnh lúc bấm làm đích và tính góc cần tới MỘT lần (không theo camera nữa).
        Vật bị dời thì bấm R lại. Trả về "locked" hoặc "no_target" (camera chưa thấy vật nào)."""
        if not self.objects:
            return "no_target"
        obj = self.objects[0]
        rx, ry = table_cm_to_robot_mm(obj["x_cm"], obj["y_cm"])
        goal, reachable = goal_angles(rx, ry)
        self.target = {"cm": (obj["x_cm"], obj["y_cm"]), "reachable": reachable, "goal": goal}
        return "locked"

    # --- kế hoạch ----------------------------------------------------------
    def update(self, objects):
        """Nhận các vật camera thấy (x_cm, y_cm, name) và trả về Plan: góc servo hiện tại so với góc đích đã chụp bằng R."""
        base_xy = (ARM_CONFIG["base_x_cm"], ARM_CONFIG["base_y_cm"])
        self.objects = sorted(objects, key=lambda o: math.hypot(o["x_cm"] - base_xy[0], o["y_cm"] - base_xy[1]))
        servo_now = list(self.link.servo)  # Góc 4 servo Arduino báo về (hoặc góc mô phỏng)
        base = dict(now=servo_now, usb_ok=self.link.connected)
        t = self.target
        if t is None:
            return Plan(found=False, target_cm=None, reachable=True, goal=list(servo_now[:3]), moves=plan_moves(servo_now, servo_now), **base)
        return Plan(found=True, target_cm=t["cm"], reachable=t["reachable"], goal=list(t["goal"]), moves=plan_moves(servo_now, t["goal"]), **base)

    def count_key(self, key):
        """Phím laptop báo qua Wi-Fi: chỉ cộng / trừ góc trên Mac, KHÔNG gửi xuống Arduino (laptop đã gửi qua Bluetooth).
        Có cắm USB thì gói góc Arduino báo về (0,2 giây / lần) vẫn là số đúng và ghi đè số đếm này."""
        self.link.apply_key_locally((key or "")[:1].lower())

    def press(self, key):
        """Gửi một phím điều khiển xuống Arduino (hoặc cập nhật mô phỏng nếu chưa nối USB). Trả về True nếu là phím điều khiển."""
        ch = (key or "")[:1].lower()
        if not ch or ch not in "wasdikjlh":
            return False
        self.link.send_key(ch)
        return True

    def release(self):
        self.link.release()
