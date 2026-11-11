#!/usr/bin/env python3
"""
ĐỘNG HỌC THUẬN cho công cụ slide (check_facts.py --deep, make_screen_images.py): từ góc 3 servo ra chỗ đầu kẹp theo mô hình.
App không dùng nữa (đã bỏ dấu KEP khỏi màn hình); chuyển từ control.py sang đây để công cụ slide vẫn chạy.
"""

import math

from control import ARM_CONFIG


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


def arduino_servo_to_joint(servo_angles, cfg=None):
    """Đổi ngược từ 4 góc servo Arduino [base, shoulder, elbow, grip] sang góc khớp (theta1, theta2, theta3)."""
    c = cfg or ARM_CONFIG
    b, s, e, _ = servo_angles
    theta1 = float(b) - 90.0
    theta2 = c["theta2_at_90_deg"] + (float(s) - 90.0)
    theta3 = c["theta3_at_90_deg"] + (float(e) - 90.0)
    return theta1, theta2, theta3


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
    theta1, theta2, theta3 = arduino_servo_to_joint((servo_angles[0], servo_angles[1], servo_angles[2], 0), c)
    x_mm, y_mm, z_mm = fk_4dof_joint(theta1, theta2, theta3, c)
    x_cm, y_cm = robot_mm_to_table_cm(x_mm, y_mm, c)
    return x_cm, y_cm, z_mm
