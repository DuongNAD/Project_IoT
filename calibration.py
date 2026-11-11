#!/usr/bin/env python3
"""
Hiệu chỉnh lưu lại giữa các lần chạy (calibration.json cạnh main.py, không đưa lên git).

Hiện lưu vị trí trục xoay Đế robot trên tờ A4 (cm) và HƯỚNG robot nhìn (độ) trong hệ tọa độ tờ giấy:
  - Gốc (0, 0) = góc ngoài mã ArUco ID 0, trục X chạy từ ID 0 sang ID 1 (cạnh dài 29.7 cm),
    trục Y chạy từ ID 0 sang ID 3 (cạnh ngắn 21.0 cm). Hệ này gắn với TỜ GIẤY nên không phụ thuộc camera nào nhìn.
  - base_heading_deg = góc của hướng "tiến thẳng" của robot, đo từ +X quay về +Y: atan2(dY, dX).
    Robot nhìn về +Y (vào trong tờ giấy từ mép Y = 0) là 90°; robot đứng mép Y = 21 nhìn về -Y là -90°.
Bấm phím B trong main.py rồi click vào trục xoay đế để hiệu chỉnh lại khi dời robot hoặc dời tờ giấy.

Hiệu chỉnh bằng các lần ôm thật (công cụ ngoài arm_fit.py) khớp thêm hướng robot và hai góc chuẩn vai / khuỷu khi servo ở 90°
(mục "arm"), nên vị trí / hướng đế và hai góc này cùng được lưu lại.

Mục "claw" (tùy chọn) lưu hình học càng kẹp đo từ các lần ôm thật: càng kẹp gắn cứng vào khâu khuỷu nên độ lệch của điểm kẹp quay theo
khâu đó. Mô hình FK của app (L3 + độ lệch L4 cố định theo phương ngang) tái hiện được điều này bằng cách dồn độ lệch vào chiều dài khâu 3:
L3_mm = |(L3 + a, b)|, L4_r_mm = L4_z_mm = 0, và cộng atan2(b, L3 + a) vào theta3_at_90_deg (a, b: tọa độ điểm kẹp trong hệ khâu khuỷu).
"""

import json
import math
import os

CALIBRATION_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calibration.json")

# Tờ A4 đặt ngang (cm), dùng để hướng robot nhìn vào tâm tờ giấy
SHEET_W_CM = 29.7
SHEET_H_CM = 21.0

# Hai góc chuẩn của vai / khuỷu (ARM_CONFIG) mà hiệu chỉnh bằng các lần ôm thật (arm_fit.py) lưu vào mục "arm"
ARM_OFFSET_KEYS = ("theta2_at_90_deg", "theta3_at_90_deg")
# Hình học càng kẹp (mm) lưu ở mục "claw": chiều dài khâu khuỷu -> điểm kẹp và độ lệch phụ cố định của kẹp. Mỗi giá trị nằm trong [0, 400] mm
CLAW_KEYS = ("L3_mm", "L4_r_mm", "L4_z_mm")
CLAW_MAX_MM = 400.0


def load_calibration(path=None):
    """Đọc file hiệu chỉnh; thiếu file hoặc file hỏng thì trả về {} (dùng giá trị mặc định trong code)."""
    try:
        with open(path or CALIBRATION_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_calibration(data, path=None):
    with open(path or CALIBRATION_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def heading_toward(base_x_cm, base_y_cm, target_x_cm=SHEET_W_CM / 2.0, target_y_cm=SHEET_H_CM / 2.0, snap_deg=20.0):
    """
    Hướng (độ, đo từ +X quay về +Y) robot nhìn vào tờ giấy.
    - Đế nằm NGOÀI một mép giấy: robot nhìn vuông góc vào mép đó (song song các trục tờ giấy), kể cả khi đế không nằm đúng giữa
      mép (đế ở X = 5 cm cạnh mép Y = 0 vẫn nhìn +Y chứ không ngả về tâm giấy). Nằm ngoài ở góc chéo thì lấy mép xa nhất.
    - Đế nằm TRONG tờ giấy: nhìn về điểm đích (mặc định tâm tờ giấy), lấy tròn về 0 / 90 / 180 / -90 nếu lệch không quá snap_deg.
    Robot đặt chéo với mép giấy thì sửa tay base.heading_deg trong calibration.json.
    """
    outside = (
        (-base_y_cm, 90.0),                  # Ngoài mép Y = 0: nhìn vào +Y
        (base_y_cm - SHEET_H_CM, -90.0),     # Ngoài mép Y = 21: nhìn vào -Y
        (-base_x_cm, 0.0),                   # Ngoài mép X = 0: nhìn vào +X
        (base_x_cm - SHEET_W_CM, 180.0),     # Ngoài mép X = 29.7: nhìn vào -X
    )
    distance, axis_heading = max(outside, key=lambda item: item[0])
    if distance > 0:
        return axis_heading
    heading = math.degrees(math.atan2(target_y_cm - base_y_cm, target_x_cm - base_x_cm))
    for axis in (-180.0, -90.0, 0.0, 90.0, 180.0):
        if abs(heading - axis) <= snap_deg:
            return -180.0 if axis == 180.0 else axis
    return heading


def apply_calibration(arm_config, data=None):
    """
    Ghi vị trí / hướng đế robot ("base") và hai góc chuẩn vai / khuỷu ("arm") đã hiệu chỉnh vào ARM_CONFIG
    (bỏ qua mục thiếu hoặc sai kiểu). Trả về True nếu có áp dụng.
    """
    data = load_calibration() if data is None else data
    applied = False
    base = data.get("base")
    if isinstance(base, dict):
        for key in ("x_cm", "y_cm", "heading_deg"):
            value = base.get(key)
            if isinstance(value, (int, float)) and math.isfinite(value):
                arm_config[f"base_{key}"] = float(value)
                applied = True
    arm = data.get("arm")
    if isinstance(arm, dict):
        for key in ARM_OFFSET_KEYS:
            value = arm.get(key)
            if isinstance(value, (int, float)) and math.isfinite(value) and abs(value) <= 180.0:
                arm_config[key] = float(value)
                applied = True
    claw = data.get("claw")
    if isinstance(claw, dict):
        for key in CLAW_KEYS:
            value = claw.get(key)
            if isinstance(value, (int, float)) and math.isfinite(value) and 0.0 <= value <= CLAW_MAX_MM:
                arm_config[key] = float(value)
                applied = True
    return applied


def store_base_pose(x_cm, y_cm, heading_deg, path=None):
    """Lưu vị trí / hướng đế robot vào file hiệu chỉnh, giữ nguyên các mục khác."""
    data = load_calibration(path)
    data["base"] = {"x_cm": round(float(x_cm), 2), "y_cm": round(float(y_cm), 2), "heading_deg": round(float(heading_deg), 1)}
    save_calibration(data, path)
    return data


def store_claw_geometry(L3_mm, L4_r_mm, L4_z_mm, path=None):
    """Lưu hình học càng kẹp (mm) vào mục "claw", giữ nguyên các mục khác."""
    data = load_calibration(path)
    data["claw"] = {"L3_mm": round(float(L3_mm), 1), "L4_r_mm": round(float(L4_r_mm), 1), "L4_z_mm": round(float(L4_z_mm), 1)}
    save_calibration(data, path)
    return data


def store_arm_offsets(theta2_deg, theta3_deg, path=None, defaults=None, info=None):
    """
    Lưu hai góc chuẩn của vai và khuỷu (độ, khi servo ở 90°) vào mục "arm", giữ nguyên các mục khác.
    defaults = (theta2, theta3) mặc định trong code: nếu hai góc đã trở về đúng mặc định thì xóa mục "arm" thay vì ghi đè.
    info: ghi chú để người dùng biết hiệu chỉnh lấy từ đâu (số mẫu, sai số), lưu ở mục "arm_fit".
    """
    data = load_calibration(path)
    at_defaults = defaults is not None and abs(theta2_deg - defaults[0]) < 0.05 and abs(theta3_deg - defaults[1]) < 0.05
    if at_defaults:
        data.pop("arm", None)
        data.pop("arm_fit", None)
    else:
        data["arm"] = {"theta2_at_90_deg": round(float(theta2_deg), 1), "theta3_at_90_deg": round(float(theta3_deg), 1)}
        if info is not None:
            data["arm_fit"] = info
    save_calibration(data, path)
    return data
