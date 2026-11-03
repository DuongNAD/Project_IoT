"""arm_fit.py (công cụ khớp offline): khớp vị trí đế, hướng robot và hai góc chuẩn vai / khuỷu từ vài lần "ôm" thật (servo + vị trí vật)."""

import itertools
import math
import random

import numpy as np
import pytest

import arm_fit
import control as g

# Cánh tay "thật" trong mô phỏng: khác mặc định về vị trí đế, hướng và hai góc chuẩn (cùng cỡ với sai lệch đo được trên cánh tay thật)
SHIFTED = dict(base_x_cm=18.7, base_y_cm=-5.0, base_heading_deg=79.0, theta2_at_90_deg=55.0, theta3_at_90_deg=-55.0)
CUP_Z_MM = g.GRASP_Z_MM  # Độ cao điểm kẹp = nửa chiều cao cốc
SAMPLE_CUPS = [(12.0, 9.0), (23.0, 14.0), (17.0, 18.0)]


def real_cfg(**over):
    cfg = dict(g.ARM_CONFIG)
    cfg.update(over)
    return cfg


def servo_for(cfg, x_cm, y_cm, z_mm=CUP_Z_MM):
    xr, yr = g.table_cm_to_robot_mm(x_cm, y_cm, cfg)
    ik = g.ik_4dof_joint(xr, yr, z_mm, cfg)
    servo = g.joint_to_servo(ik["theta1_deg"], ik["theta2_deg"], ik["theta3_deg"], cfg=cfg)
    return tuple(servo), ik["reachable"]


def human_aligns(true_cfg, x_cm, y_cm, z_mm=CUP_Z_MM):
    """Người dùng nhích từng bước 2° tới khi kẹp bao quanh vật: lấy tổ hợp (±1 bước mỗi khớp) có điểm kẹp THẬT gần vật nhất."""
    base, reachable = servo_for(true_cfg, x_cm, y_cm, z_mm)
    assert reachable, (x_cm, y_cm)
    best, best_d = None, float("inf")
    for db, ds, de in itertools.product((-2, 0, 2), repeat=3):
        cand = (base[0] + db, base[1] + ds, base[2] + de)
        if not (0 <= cand[0] <= 180 and 25 <= cand[1] <= 155 and 25 <= cand[2] <= 155):
            continue
        x, y, z = g.predict_tip(cand, true_cfg)
        d = math.hypot(x - x_cm, y - y_cm) * 10.0 + 0.3 * abs(z - z_mm)
        if d < best_d:
            best, best_d = cand, d
    return best


def make_samples(true_cfg, cups, seed=3, xy_noise_mm=3.0):
    rng = random.Random(seed)
    samples = []
    for x, y in cups:
        servo = human_aligns(true_cfg, x, y)
        samples.append({
            "servo": servo,
            "x_cm": x + rng.gauss(0, xy_noise_mm) / 10.0,  # Vị trí vật do camera đo có nhiễu vài mm
            "y_cm": y + rng.gauss(0, xy_noise_mm) / 10.0,
            "z_mm": CUP_Z_MM + rng.gauss(0, 8.0),
        })
    return samples


def workspace_error_mm(cfg, true_cfg):
    """RMS (mm) khi dùng cấu hình cfg để gợi ý servo tới các điểm khắp vùng làm việc, rồi đo bằng cánh tay thật."""
    errors = []
    for x, y in itertools.product(np.arange(9, 26, 2.5), np.arange(6, 20, 2.5)):
        if not servo_for(true_cfg, x, y)[1]:
            continue
        servo, _ = servo_for(cfg, x, y)
        tx, ty, _ = g.predict_tip(servo, true_cfg)
        errors.append(math.hypot(tx - x, ty - y) * 10.0)
    return float(np.sqrt(np.mean(np.square(errors))))


def fitted_cfg(fit):
    cfg = dict(g.ARM_CONFIG)
    cfg.update(fit["params"])
    return cfg


def test_fit_recovers_a_shifted_arm_from_three_samples():
    true_cfg = real_cfg(**SHIFTED)
    fit = arm_fit.fit_geometry(make_samples(true_cfg, SAMPLE_CUPS), dict(g.ARM_CONFIG), g.predict_tip)
    p = fit["params"]
    assert fit["n"] == 3 and fit["converged"]
    assert fit["before_rms_xy_mm"] > 40 and fit["rms_xy_mm"] < 15
    assert abs(p["base_x_cm"] - SHIFTED["base_x_cm"]) < 3.0 and abs(p["base_y_cm"] - SHIFTED["base_y_cm"]) < 3.0
    assert abs(p["base_heading_deg"] - SHIFTED["base_heading_deg"]) < 8.0
    # Điều quan trọng: gợi ý servo ở chỗ KHÔNG ghi mẫu trúng hơn hẳn (sàn còn lại là bước nhích 2° của servo)
    before, after = workspace_error_mm(dict(g.ARM_CONFIG), true_cfg), workspace_error_mm(fitted_cfg(fit), true_cfg)
    assert before > 60 and after < 35 and after < before / 2, (before, after)


def test_fit_leaves_an_already_correct_model_nearly_unchanged():
    true_cfg = real_cfg()  # Cánh tay thật đúng như mặc định
    fit = arm_fit.fit_geometry(make_samples(true_cfg, SAMPLE_CUPS), dict(g.ARM_CONFIG), g.predict_tip)
    p = fit["params"]
    assert abs(p["base_x_cm"] - g.ARM_CONFIG["base_x_cm"]) < 2.0 and abs(p["base_y_cm"] - g.ARM_CONFIG["base_y_cm"]) < 2.0
    assert abs(p["base_heading_deg"] - g.ARM_CONFIG["base_heading_deg"]) < 6.0
    before, after = workspace_error_mm(dict(g.ARM_CONFIG), true_cfg), workspace_error_mm(fitted_cfg(fit), true_cfg)
    assert after < before + 8.0, (before, after)  # Mẫu có nhiễu cũng không làm mô hình đúng tệ đi đáng kể


def test_inconsistent_samples_leave_a_high_residual():
    true_cfg = real_cfg(**SHIFTED)
    samples = make_samples(true_cfg, SAMPLE_CUPS)
    good = arm_fit.fit_geometry(samples, dict(g.ARM_CONFIG), g.predict_tip)
    assert good["rms_xy_mm"] <= arm_fit.MAX_ACCEPT_RMS_MM
    samples[1]["x_cm"] += 12.0  # Bấm Y khi kẹp còn cách vật 12 cm
    bad = arm_fit.fit_geometry(samples, dict(g.ARM_CONFIG), g.predict_tip)
    assert bad["rms_xy_mm"] > arm_fit.MAX_ACCEPT_RMS_MM


def test_fit_never_moves_a_parameter_beyond_its_allowed_shift():
    far = real_cfg(base_heading_deg=g.ARM_CONFIG["base_heading_deg"] - 70.0, base_x_cm=g.ARM_CONFIG["base_x_cm"] + 15.0)
    cups = [(12.0, 9.0), (23.0, 14.0), (17.0, 18.0)]
    samples = [{"servo": (80, 70, 70), "x_cm": x, "y_cm": y, "z_mm": CUP_Z_MM} for x, y in cups]
    fit = arm_fit.fit_geometry(samples, far, g.predict_tip)
    for key in arm_fit.FIT_KEYS:
        assert abs(fit["params"][key] - far[key]) <= arm_fit.MAX_SHIFT[key] + 1e-6, key


def test_spread_is_the_largest_distance_between_samples():
    assert arm_fit.samples_spread_cm([]) == 0.0
    assert arm_fit.samples_spread_cm([{"x_cm": 1.0, "y_cm": 1.0}]) == 0.0
    samples = [{"x_cm": 0.0, "y_cm": 0.0}, {"x_cm": 3.0, "y_cm": 4.0}, {"x_cm": 1.0, "y_cm": 1.0}]
    assert arm_fit.samples_spread_cm(samples) == pytest.approx(5.0)
