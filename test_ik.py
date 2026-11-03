#!/usr/bin/env python3
"""
Kiểm thử bắt buộc theo Kế hoạch (trang 11 & 15):
1. Sinh lưới điểm (x, y, z) trong tầm với của cánh tay 4 Servo, kiểm tra FK(IK(p)) trùng p với sai số < 0.1 mm.
2. Kiểm tra ánh xạ góc khớp -> 4 góc servo Arduino [angleBase, angleShoulder, angleElbow, angleGrip]
   nằm trong giới hạn an toàn (Đế 0..180, Vai 25..155, Khuỷu 25..155, Kẹp 95..175) và chia hết cho STEP = 5°.
3. Kiểm tra hàm sinh gợi ý bấm phím (WASD + IK + JL).
4. Kiểm tra quy trình gắp: tín hiệu S1, khóa vật lúc đóng kẹp và log CSV (không mở cổng serial / camera thật).
"""

import contextlib
import csv
import math
import os
import tempfile
import time
import numpy as np
import grasp_assist_4dof as ga
from grasp_assist_4dof import (
    ARM_CONFIG,
    ArduinoSerialLink,
    find_bluetooth_port,
    SERVO_LIMITS,
    SERVO_STEP_DEG,
    fk_4dof_joint,
    format_key_hint,
    ik_4dof_joint,
    joint_to_arduino_servo,
    robot_mm_to_table_cm,
    table_cm_to_robot_mm,
)


def test_fk_ik_grid():
    max_err_mm = 0.0
    tested = 0
    for x in range(110, 215, 15):
        for y in range(-90, 95, 15):
            for z in (15, 30, 50, 80, 100):
                res = ik_4dof_joint(x, y, z)
                if not res["reachable"]:
                    continue
                fx, fy, fz = fk_4dof_joint(
                    res["theta1_deg"], res["theta2_deg"], res["theta3_deg"]
                )
                err = math.sqrt((fx - x) ** 2 + (fy - y) ** 2 + (fz - z) ** 2)
                max_err_mm = max(max_err_mm, err)
                assert err < 0.1, f"Sai số FK(IK({x},{y},{z})) = {err:.4f} mm >= 0.1 mm!"

                servos = joint_to_arduino_servo(
                    res["theta1_deg"], res["theta2_deg"], res["theta3_deg"], close_grip=False
                )
                for idx, key in enumerate(("base", "shoulder", "elbow", "grip")):
                    lo, hi, _ = SERVO_LIMITS[key]
                    assert lo <= servos[idx] <= hi, f"Servo {key}={servos[idx]} vượt giới hạn [{lo},{hi}]"
                    assert servos[idx] % SERVO_STEP_DEG == 0, f"Servo {key}={servos[idx]} không chia hết cho STEP=5"
                tested += 1

    print(f"✅ [PASS] Đã kiểm thử {tested} điểm 3D trong tầm với: sai số FK(IK(p)) tối đa = {max_err_mm:.6f} mm (< 0.1 mm)")


def test_key_hints():
    # Đế đang ở 90°, mục tiêu 115° (+25°) -> Bấm 'A' x5 lần (Trái)
    delta, steps, key, txt, ok = format_key_hint(0, 90, 115)
    assert (delta, steps, key, ok) == (25, 5, "a", False), f"Sai gợi ý Đế: {txt}"
    # Vai đang ở 90°, mục tiêu 70° (-20°) -> Bấm 'S' x4 lần (Xuống)
    delta, steps, key, txt, ok = format_key_hint(1, 90, 70)
    assert (delta, steps, key, ok) == (-20, 4, "s", False), f"Sai gợi ý Vai: {txt}"
    # Khuỷu đang ở 90°, mục tiêu 105° (+15°) -> Bấm 'I' x3 lần (Gập lên)
    delta, steps, key, txt, ok = format_key_hint(2, 90, 105)
    assert (delta, steps, key, ok) == (15, 3, "i", False), f"Sai gợi ý Khuỷu: {txt}"
    # Kẹp đang ở 95°, mục tiêu 165° (+70°) -> Bấm 'L' x14 lần (Kẹp vào)
    delta, steps, key, txt, ok = format_key_hint(3, 95, 165)
    assert (delta, steps, key, ok) == (70, 14, "l", False), f"Sai gợi ý Kẹp: {txt}"
    print("✅ [PASS] Kiểm thử gợi ý bấm phím (WASD + IK + JL) với STEP = 5° chính xác tuyệt đối!")


def test_table_robot_mapping():
    # Đổi qua lại tờ A4 <-> hệ robot phải trả đúng điểm cũ ở cả hai hướng đặt robot
    for faces in ("up", "down"):
        cfg = dict(ARM_CONFIG, robot_faces=faces)
        for x_cm, y_cm in ((3.0, 4.0), (14.85, 10.5), (25.0, 18.0)):
            back = robot_mm_to_table_cm(*table_cm_to_robot_mm(x_cm, y_cm, cfg), cfg)
            assert abs(back[0] - x_cm) < 1e-9 and abs(back[1] - y_cm) < 1e-9, f"{faces}: ({x_cm},{y_cm}) -> {back}"

    # "up": đế ở mép dưới (Y=22), điểm cách 10 cm về phía mép trên nằm thẳng phía trước (+x_robot); X_A4 nhỏ hơn = bên trái (+y_robot)
    up = dict(ARM_CONFIG, robot_faces="up", base_x_cm=15.0, base_y_cm=22.0)
    assert table_cm_to_robot_mm(15.0, 12.0, up) == (100.0, 0.0)
    assert table_cm_to_robot_mm(10.0, 12.0, up)[1] > 0
    # "down": đế ở mép trên (Y=-18), điểm cách 10 cm về phía mép dưới nằm thẳng phía trước; X_A4 lớn hơn = bên trái
    down = dict(ARM_CONFIG, robot_faces="down", base_x_cm=15.0, base_y_cm=-18.0)
    assert table_cm_to_robot_mm(15.0, -8.0, down) == (100.0, 0.0)
    assert table_cm_to_robot_mm(20.0, -8.0, down)[1] > 0
    print("✅ [PASS] Ánh xạ tờ A4 <-> hệ robot đúng cho cả hai hướng đặt robot (up / down)")


def test_board_silence_detection():
    # Không tạo luồng/mở cổng serial thật (mở cổng sẽ reset Arduino): chỉ thử logic phát hiện board không trả lời lệnh USB
    link = ArduinoSerialLink.__new__(ArduinoSerialLink)
    link.heard_board, link.unanswered_since = False, None
    assert not link.board_ignores_usb()          # chưa gửi phím nào
    link.unanswered_since = time.time() - 0.5
    assert not link.board_ignores_usb()          # mới gửi, chưa quá 2 giây
    link.unanswered_since = time.time() - 3.0
    assert link.board_ignores_usb()              # gửi hơn 2 giây mà board im lặng (firmware cũ)
    link.heard_board = True
    assert not link.board_ignores_usb()          # board đã trả lời (JSON hoặc "Phím bấm")
    print("✅ [PASS] Phát hiện board không nhận lệnh USB (firmware cũ)")


def test_find_bluetooth_port():
    from serial.tools import list_ports

    class FakePort:
        def __init__(self, device, hwid):
            self.device, self.hwid = device, hwid

    spp = r"BTHENUM\{00001101-0000-1000-8000-00805F9B34FB}_LOCALMFG&0000\7&172BD935&1&"
    fake = [
        FakePort("COM8", spp + "4142F51A7E10_C00000000"),
        FakePort("COM5", spp + "000000000000_00000000"),     # cổng incoming không gắn với thiết bị nào
        FakePort("COM10", spp + "98D351F6AF14_C00000000"),   # HC-05 đã ghép đôi
        FakePort("COM9", r"USB\VID_0843&PID_5740\FX2348N"),  # cáp USB Arduino: không phải cổng Bluetooth
    ]
    real = list_ports.comports
    list_ports.comports = lambda: fake
    try:
        assert find_bluetooth_port("98:d3:51:f6:af:14") == "COM10"
        assert find_bluetooth_port("98-D3-51-F6-AF-14") == "COM10"
        assert find_bluetooth_port("4142F51A7E10") == "COM8"
        assert find_bluetooth_port("AABBCCDDEEFF") is None   # chưa ghép đôi
        assert find_bluetooth_port("COM7") == "COM7"          # chỉ định thẳng tên cổng
        # macOS: cổng Bluetooth không có địa chỉ MAC trong hwid, HC-05 đã ghép đôi hiện ra theo tên thiết bị
        mac_ports = [
            FakePort("/dev/cu.Bluetooth-Incoming-Port", "n/a"),
            FakePort("/dev/cu.usbmodemFX2348N1", "USB VID:PID=2341:0069 SER=FX2348N"),
            FakePort("/dev/cu.HC-05", "n/a"),
        ]
        list_ports.comports = lambda: mac_ports
        assert find_bluetooth_port("98D351F6AF14") == "/dev/cu.HC-05"
        assert find_bluetooth_port("/dev/cu.HC-05-DevB") == "/dev/cu.HC-05-DevB"
    finally:
        list_ports.comports = real
    print("✅ [PASS] Tìm cổng Bluetooth của HC-05 (Windows theo địa chỉ MAC, macOS theo tên cổng)")


def test_send_key_over_bluetooth():
    class FakeSer:
        def __init__(self, fail=False):
            self.sent, self.fail = [], fail

        def write(self, b):
            if self.fail:
                raise OSError("link lost")
            self.sent.append(b)

        def flush(self):
            pass

        def close(self):
            pass

    def make(bt, usb):
        link = ArduinoSerialLink.__new__(ArduinoSerialLink)  # không mở cổng thật
        link.lock = __import__("threading").Lock()
        link.servo, link.last_cmd = [90, 90, 90, 95], ""
        link.heard_board, link.unanswered_since = False, None
        link.bt_ser, link.bt_port, link.ser, link.connected = bt, "COM10" if bt else None, usb, usb is not None
        return link

    # Chỉ có Bluetooth (không cáp USB): gửi qua BT và cập nhật góc servo giả định theo lệnh
    bt = FakeSer()
    link = make(bt, None)
    link.send_key("a")
    assert bt.sent == [b"a"] and link.servo[0] == 95 and link.unanswered_since is not None
    # Có cả BT lẫn USB: lệnh đi qua BT, USB chỉ để đọc trạng thái (không ghi), góc servo chờ board báo lại
    bt, usb = FakeSer(), FakeSer()
    link = make(bt, usb)
    link.send_key("w")
    assert bt.sent == [b"w"] and usb.sent == [] and link.servo == [90, 90, 90, 95]
    # BT đứt giữa chừng: tự bỏ BT và gửi lại qua USB
    bt, usb = FakeSer(fail=True), FakeSer()
    link = make(bt, usb)
    link.send_key("s")
    assert link.bt_ser is None and usb.sent == [b"s"]
    print("✅ [PASS] Gửi lệnh qua Bluetooth HC-05, tự quay về USB khi BT đứt")


@contextlib.contextmanager
def fake_assist():
    """GraspAssist4DOF không mở cổng serial thật (mở cổng sẽ reset Arduino), log CSV ghi vào thư mục tạm."""

    class FakeLink:
        bt_port, bt_ser = None, None

        def __init__(self, baud=9600):
            self.servo = [90, 90, 90, 95]

        def get_state(self):
            return list(self.servo), False, None, ""

        def board_ignores_usb(self):
            return False

        def send_key(self, cmd):
            pass

        def release(self):
            pass

    real_link, real_log = ga.ArduinoSerialLink, ga.LOG_CSV_PATH
    with tempfile.TemporaryDirectory() as tmp:
        ga.ArduinoSerialLink, ga.LOG_CSV_PATH = FakeLink, os.path.join(tmp, "logs", "attempts.csv")
        try:
            yield ga.GraspAssist4DOF()
        finally:
            ga.ArduinoSerialLink, ga.LOG_CSV_PATH = real_link, real_log


def test_s1_ignores_gripper_marker():
    with fake_assist() as assist:
        img = np.zeros((480, 640, 3), np.uint8)
        y = 480 * (ga.SIDE_TABLE_Y_RATIO - ga.SIDE_LIFT_RATIO) - 60  # cao hơn ngưỡng nâng S1
        box = np.float32([[[300, y - 10], [320, y - 10], [320, y + 10], [300, y + 10]]])
        assist.stage, assist.verify_start_ts = 4, time.time()  # bước 5, vừa bắt đầu kiểm tra
        assist.update_side_observations(img, [box], np.array([[6]]), [])
        assert list(assist.s1_window) == [0], "Mã ID 6 (đầu kẹp) nâng lên không được tính là vật đã nhấc"
        assist.update_side_observations(img, [box], np.array([[12]]), [])
        assert list(assist.s1_window) == [0, 1], "Mã vật ID 12 trên ngưỡng phải tính là vật đã nhấc"
    print("✅ [PASS] S1 chỉ tính mã của vật (ID 10-29), kẹp rỗng nâng lên không bị báo là đã gắp")


def test_grasp_locks_target_and_logs_align_error():
    obj_a = {"name": "Vat_A", "x_cm": 12.0, "y_cm": 8.0, "w_mm": 30.0, "h_mm": 60.0, "px": (0, 0), "source": "aruco"}
    obj_b = {"name": "Vat_B", "x_cm": 22.0, "y_cm": 15.0, "w_mm": 35.0, "h_mm": 40.0, "px": (0, 0), "source": "yolo"}
    with fake_assist() as assist:
        assist.objects = [obj_a]
        assist.target_history_cm.append((obj_a["x_cm"], obj_a["y_cm"]))
        assist.stage = 1  # bước 2: hạ xuống điểm kẹp
        err_at_grip = assist.compute_current_suggestion()["align_err_mm"]
        assist.next_stage()  # sang bước 3 (đóng kẹp): khóa vật A
        # Vật A đã nằm trong kẹp, cam trên giờ chỉ còn thấy vật B
        assist.objects = [obj_b]
        assist.target_history_cm.clear()
        assist.target_history_cm.append((obj_b["x_cm"], obj_b["y_cm"]))
        for stage in (2, 3):  # bước 3 đóng kẹp, bước 4 nâng lên: gợi ý vẫn theo vật A
            info = assist.compute_current_suggestion()
            assert info["stage"] == stage and info["obj_name"] == "Vat_A" and info["obj_cm"] == (12.0, 8.0), info["obj_name"]
            assist.next_stage()
        # Bước 5: S1 và S2 cùng đạt -> GẮP THÀNH CÔNG, log ghi sai số căn lúc đóng kẹp (trước đây luôn ghi 0)
        assist.s1_window.extend([1] * 15)
        assist.s2_window.extend([1] * 15)
        with assist.lock:
            assist._evaluate_verification_locked()
        with open(ga.LOG_CSV_PATH, encoding="utf-8") as f:
            row = list(csv.DictReader(f))[-1]
        assert row["result"] == "SUCCESS" and row["object_name"] == "Vat_A", row
        assert err_at_grip > 0 and row["align_error_mm"] == f"{err_at_grip:.1f}", row
    print("✅ [PASS] Khóa vật lúc đóng kẹp cho bước nâng + kiểm tra, log CSV ghi đúng sai số căn đầu kẹp")


def test_normalize_phone_url():
    from main import normalize_phone_url  # main.py có `if __name__ == "__main__"` nên import không mở camera

    assert normalize_phone_url("") == ""
    assert normalize_phone_url(" 192.168.1.5 ") == "http://192.168.1.5:8080/video"
    assert normalize_phone_url("192.168.1.5:4747") == "http://192.168.1.5:4747/video"
    assert normalize_phone_url("http://192.168.1.5/") == "http://192.168.1.5:8080/video"
    assert normalize_phone_url("http://192.168.1.5:8080/shot.jpg") == "http://192.168.1.5:8080/shot.jpg"
    print("✅ [PASS] Chuẩn hóa địa chỉ IP Webcam của điện thoại")


def test_find_cameras_macos():
    import json
    import subprocess
    import sys
    import main

    names = ["Duong's iPhone Desk View Camera", "Duong's iPhone Camera", "MacBook Air Camera"]
    real_platform, real_run = sys.platform, subprocess.run
    sys.platform = "darwin"
    subprocess.run = lambda *a, **k: subprocess.CompletedProcess(
        a, 0, stdout=json.dumps({"SPCameraDataType": [{"_name": n} for n in names]})
    )
    try:
        assert main.list_camera_names() == names
        # Desk View (cảnh bàn cắt ra từ iPhone) không được chọn: điện thoại = iPhone Camera, laptop = MacBook Air Camera
        assert main.find_camera_indices() == (2, 1)
        subprocess.run = lambda *a, **k: subprocess.CompletedProcess(a, 1, stdout="")  # system_profiler lỗi
        assert main.list_camera_names() == []
    finally:
        sys.platform, subprocess.run = real_platform, real_run

    real_list = main.list_camera_names
    main.list_camera_names = lambda: ["OBS Virtual Camera", "MacBook Air Camera"]
    try:
        # Điện thoại dùng IP Webcam (URL): bỏ camera ảo, chỉ số điện thoại là chỉ số chưa có thiết bị
        assert main.find_camera_indices(want_phone=False) == (1, 2)
    finally:
        main.list_camera_names = real_list
    print("✅ [PASS] Nhận camera MacBook và iPhone (Continuity Camera) theo tên trên macOS")


if __name__ == "__main__":
    test_fk_ik_grid()
    test_key_hints()
    test_table_robot_mapping()
    test_board_silence_detection()
    test_find_bluetooth_port()
    test_send_key_over_bluetooth()
    test_s1_ignores_gripper_marker()
    test_grasp_locks_target_and_logs_align_error()
    test_normalize_phone_url()
    test_find_cameras_macos()
