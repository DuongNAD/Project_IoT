"""Lưu / nạp vị trí và hướng đế robot, chọn hướng nhìn vào tờ giấy."""

import json
import math

import pytest

import calibration as cal
import control as g


def test_heading_looks_perpendicular_into_the_sheet_from_the_edge_the_base_is_outside_of():
    # Đế ngoài mép Y = 0 nhìn vuông góc vào +Y, dù đế nằm giữa mép hay lệch về một bên (trước đây lệch bị ngả về tâm giấy)
    for base_x in (14.85, 11.0, 8.0, 5.0, 25.0):
        assert cal.heading_toward(base_x, -7.5) == 90.0, base_x
    assert cal.heading_toward(14.85, 28.5) == -90.0  # Ngoài mép Y = 21 nhìn lên: thiết kế ban đầu
    assert cal.heading_toward(-8.0, 10.5) == 0.0  # Ngoài mép X = 0 nhìn sang phải
    assert cal.heading_toward(-8.0, 4.0) == 0.0
    assert cal.heading_toward(40.0, 10.5) == 180.0  # Ngoài mép X = 29.7 nhìn sang trái
    # Nằm ngoài ở góc chéo thì theo mép xa nhất
    assert cal.heading_toward(-6.0, -12.0) == 90.0
    assert cal.heading_toward(-12.0, -6.0) == 0.0


def test_heading_for_a_base_inside_the_sheet_aims_at_the_centre():
    assert cal.heading_toward(14.85, 8.0) == 90.0  # Gần như thẳng hàng với tâm: lấy tròn về trục
    inside = cal.heading_toward(5.0, 5.0)  # Chéo rõ rệt: giữ nguyên hướng tới tâm giấy
    assert inside == pytest.approx(math.degrees(math.atan2(5.5, 9.85)))
    assert inside not in (0.0, 90.0)


def test_store_load_and_apply_round_trip(tmp_path):
    path = tmp_path / "cal.json"
    assert cal.load_calibration(str(path)) == {}  # Chưa có file: dùng mặc định
    cal.store_base_pose(13.456, -6.789, 90.0, path=str(path))
    data = cal.load_calibration(str(path))
    assert data["base"] == {"x_cm": 13.46, "y_cm": -6.79, "heading_deg": 90.0}

    cfg = {"base_x_cm": 1.0, "base_y_cm": 2.0, "base_heading_deg": 3.0, "other": 7}
    assert cal.apply_calibration(cfg, data)
    assert (cfg["base_x_cm"], cfg["base_y_cm"], cfg["base_heading_deg"], cfg["other"]) == (13.46, -6.79, 90.0, 7)


def test_store_keeps_other_sections(tmp_path):
    path = tmp_path / "cal.json"
    path.write_text(json.dumps({"ghi_chu": {"a": 1}}), encoding="utf-8")
    cal.store_base_pose(1, 2, 0, path=str(path))
    data = cal.load_calibration(str(path))
    assert data["ghi_chu"] == {"a": 1} and data["base"]["x_cm"] == 1.0


def test_bad_calibration_files_are_ignored(tmp_path):
    path = tmp_path / "cal.json"
    path.write_text("không phải JSON", encoding="utf-8")
    assert cal.load_calibration(str(path)) == {}
    path.write_text("[1, 2, 3]", encoding="utf-8")
    assert cal.load_calibration(str(path)) == {}
    cfg = {"base_x_cm": 5.0}
    assert not cal.apply_calibration(cfg, {"base": "sai"})
    assert not cal.apply_calibration(cfg, {"base": {"x_cm": "abc", "y_cm": None}})
    assert cfg == {"base_x_cm": 5.0}  # Mục sai kiểu bị bỏ qua, giá trị cũ giữ nguyên


def test_default_robot_pose_matches_the_current_setup():
    """Mặc định: robot ngoài mép Y = 0, giữa mép, nhìn vào +Y. Tâm tờ giấy nằm ngay phía trước, +X là bên TRÁI robot."""
    cfg = g.ARM_CONFIG
    assert (cfg["base_x_cm"], cfg["base_heading_deg"]) == (14.85, 90.0) and cfg["base_y_cm"] < 0
    x_mm, y_mm = g.table_cm_to_robot_mm(14.85, 10.5)
    assert x_mm == pytest.approx((10.5 - cfg["base_y_cm"]) * 10) and abs(y_mm) < 1e-6
    assert g.table_cm_to_robot_mm(24.85, 10.5)[1] == pytest.approx(100.0)  # Lệch +10 cm theo X = 10 cm sang trái


def test_arm_offsets_round_trip_and_defaults_remove_the_section(tmp_path):
    path = tmp_path / "cal.json"
    cal.store_base_pose(18.7, -5.0, 79.0, path=str(path))
    cal.store_arm_offsets(52.34, -48.66, path=str(path), defaults=(45.0, -45.0), info={"n": 3, "rms_xy_mm": 5.1})
    data = cal.load_calibration(str(path))
    assert data["arm"] == {"theta2_at_90_deg": 52.3, "theta3_at_90_deg": -48.7}
    assert data["arm_fit"]["n"] == 3 and data["base"]["heading_deg"] == 79.0  # Giữ nguyên mục base

    cfg = {"theta2_at_90_deg": 45.0, "theta3_at_90_deg": -45.0, "base_x_cm": 1.0}
    assert cal.apply_calibration(cfg, data)
    assert (cfg["theta2_at_90_deg"], cfg["theta3_at_90_deg"], cfg["base_x_cm"]) == (52.3, -48.7, 18.7)

    # Hai góc trở về đúng mặc định (VD: hủy hết mẫu): xóa mục arm thay vì ghi đè giá trị mặc định vào file
    cal.store_arm_offsets(45.0, -45.0, path=str(path), defaults=(45.0, -45.0))
    data = cal.load_calibration(str(path))
    assert "arm" not in data and "arm_fit" not in data and data["base"]["x_cm"] == 18.7


def test_arm_section_only_without_a_base_section_still_applies():
    cfg = {"theta2_at_90_deg": 45.0, "theta3_at_90_deg": -45.0, "base_x_cm": 14.85}
    assert cal.apply_calibration(cfg, {"arm": {"theta2_at_90_deg": 60.0}})
    assert (cfg["theta2_at_90_deg"], cfg["theta3_at_90_deg"], cfg["base_x_cm"]) == (60.0, -45.0, 14.85)


def test_bad_arm_section_is_ignored():
    cfg = {"theta2_at_90_deg": 45.0, "theta3_at_90_deg": -45.0}
    assert not cal.apply_calibration(cfg, {"arm": "sai"})
    assert not cal.apply_calibration(cfg, {"arm": {"theta2_at_90_deg": "abc", "theta3_at_90_deg": 400}})  # Sai kiểu / ngoài ±180°
    assert not cal.apply_calibration(cfg, {"arm": {"theta2_at_90_deg": float("nan")}})
    assert cfg == {"theta2_at_90_deg": 45.0, "theta3_at_90_deg": -45.0}


def test_claw_geometry_round_trip_and_bad_values_are_ignored(tmp_path):
    path = tmp_path / "cal.json"
    cal.store_base_pose(15.0, -10.0, 87.0, path=str(path))
    cal.store_arm_offsets(59.9, -58.0, path=str(path), defaults=(45.0, -45.0))
    cal.store_claw_geometry(186.93, 0, 0, path=str(path))
    data = cal.load_calibration(str(path))
    assert data["claw"] == {"L3_mm": 186.9, "L4_r_mm": 0.0, "L4_z_mm": 0.0}
    assert data["base"]["x_cm"] == 15.0 and data["arm"]["theta2_at_90_deg"] == 59.9  # Các mục khác còn nguyên

    cfg = {"L3_mm": 100.0, "L4_r_mm": 65.0, "L4_z_mm": 25.0, "theta2_at_90_deg": 45.0, "theta3_at_90_deg": -45.0}
    assert cal.apply_calibration(cfg, data)
    assert (cfg["L3_mm"], cfg["L4_r_mm"], cfg["L4_z_mm"]) == (186.9, 0.0, 0.0)

    # Mô hình càng kẹp lưu trong file cho điểm kẹp trùng điểm kẹp của mô hình "độ lệch quay theo khâu khuỷu" (a, b) = (86.3, 14.7)
    import math
    a, b = 86.3, 14.7
    assert 186.9 == pytest.approx(math.hypot(100.0 + a, b), abs=0.05)

    # Giá trị âm / quá lớn / sai kiểu / NaN bị bỏ qua, giá trị cũ giữ nguyên
    keep = {"L3_mm": 100.0, "L4_r_mm": 65.0, "L4_z_mm": 25.0}
    for bad in ({"L3_mm": -5}, {"L3_mm": 4000}, {"L3_mm": "abc"}, {"L4_r_mm": float("nan")}, "sai"):
        cfg2 = dict(keep)
        assert not cal.apply_calibration(cfg2, {"claw": bad})
        assert cfg2 == keep


def test_claw_section_survives_arm_offset_updates(tmp_path):
    """Phím Y / E (store_arm_offsets) ghi lại mục arm nhưng không được làm mất mục claw đã lưu."""
    path = tmp_path / "cal.json"
    cal.store_claw_geometry(186.9, 0, 0, path=str(path))
    cal.store_arm_offsets(52.0, -48.0, path=str(path), defaults=(45.0, -45.0))
    cal.store_arm_offsets(45.0, -45.0, path=str(path), defaults=(45.0, -45.0))  # Về mặc định: xóa mục arm, claw còn
    assert cal.load_calibration(str(path))["claw"]["L3_mm"] == 186.9
