#!/usr/bin/env python3
"""
Hiệu chỉnh: đo một lần, nạp mỗi lần chạy (calibration.json cạnh main.py, không đưa lên git).

Hệ tọa độ gắn với tờ giấy: gốc ở góc ngoài mã ArUco ID 0, X chạy ID 0 -> ID 1 (29,7 cm), Y chạy ID 0 -> ID 3 (21 cm).
  "base": vị trí trục xoay đế robot trên tờ giấy (cm, đo bằng thước) và hướng robot nhìn (độ, từ +X quay về +Y; 90 = nhìn vào +Y).
  "arm":  góc thật của khâu vai / khuỷu khi servo ở 90° (khớp từ 10 lần ôm cốc bằng bình phương tối thiểu).
  "claw": hình học càng kẹp (mm). Càng kẹp gắn cứng vào khâu khuỷu nên độ lệch của điểm kẹp được dồn vào chiều dài khâu 3.
Ví dụ: {"base": {"x_cm": 13.83, "y_cm": 31.67, "heading_deg": -92.4},
        "arm": {"theta2_at_90_deg": 60.2, "theta3_at_90_deg": -58.6}, "claw": {"L3_mm": 183.7, "L4_r_mm": 0, "L4_z_mm": 0}}
Dời robot hoặc đổi tờ giấy thì đo lại mục "base" bằng thước và sửa tay file này.
"""

import json
import math
import os

CALIBRATION_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calibration.json")

ARM_OFFSET_KEYS = ("theta2_at_90_deg", "theta3_at_90_deg")  # Mục "arm": hai góc chuẩn vai / khuỷu (độ)
CLAW_KEYS = ("L3_mm", "L4_r_mm", "L4_z_mm")                  # Mục "claw": hình học càng kẹp (mm), mỗi giá trị trong [0, 400]
CLAW_MAX_MM = 400.0


def load_calibration(path=None):
    """Đọc file hiệu chỉnh; thiếu file hoặc file hỏng thì trả về {} (dùng giá trị mặc định trong code)."""
    try:
        with open(path or CALIBRATION_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def apply_calibration(arm_config, data=None):
    """Ghi các mục "base", "arm", "claw" vào ARM_CONFIG (bỏ qua mục thiếu hoặc sai kiểu). Trả về True nếu có áp dụng."""
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
