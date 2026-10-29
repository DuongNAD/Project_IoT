#!/usr/bin/env python3
"""
Kiểm thử bắt buộc theo Kế hoạch (trang 11 & 15):
1. Sinh lưới điểm (x, y, z) trong tầm với của cánh tay 4 Servo, kiểm tra FK(IK(p)) trùng p với sai số < 0.1 mm.
2. Kiểm tra ánh xạ góc khớp -> 4 góc servo Arduino [angleBase, angleShoulder, angleElbow, angleGrip]
   nằm trong giới hạn an toàn (Đế 0..180, Vai 25..155, Khuỷu 25..155, Kẹp 95..175) và chia hết cho STEP = 5°.
3. Kiểm tra hàm sinh gợi ý bấm phím (WASD + IK + JL).
"""

import math
from grasp_assist_4dof import (
    SERVO_LIMITS,
    SERVO_STEP_DEG,
    fk_4dof_joint,
    format_key_hint,
    ik_4dof_joint,
    joint_to_arduino_servo,
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


if __name__ == "__main__":
    test_fk_ik_grid()
    test_key_hints()
