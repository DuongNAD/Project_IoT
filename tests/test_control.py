"""KHỐI ĐIỀU KHIỂN: hình học cánh tay (FK / IK), góc servo bấm tới được, lệnh bấm phím, phím R chụp đích, phím và cổng USB giả lập."""

import math

import pytest

import control as C


def obj(x, y, name="Vat mau"):
    return {"name": name, "x_cm": x, "y_cm": y, "w_mm": 35.0, "h_mm": 40.0, "px": (0, 0), "source": "color"}


# ----------------------------------------------------------------------------- hình học
def test_fk_of_ik_returns_the_same_point_over_a_grid_and_servo_angles_are_reachable_by_keys():
    tested, worst = 0, 0.0
    for x in range(110, 215, 15):
        for y in range(-90, 95, 15):
            for z in (15, 30, 50, 80, 100):
                res = C.ik_4dof_joint(x, y, z)
                if not res["reachable"]:
                    continue
                fx, fy, fz = C.fk_4dof_joint(res["theta1_deg"], res["theta2_deg"], res["theta3_deg"])
                worst = max(worst, math.sqrt((fx - x) ** 2 + (fy - y) ** 2 + (fz - z) ** 2))
                servo = C.joint_to_servo(res["theta1_deg"], res["theta2_deg"], res["theta3_deg"])
                for ch, joint in enumerate(C.ARM_JOINTS):
                    lo, hi, _ = C.SERVO_LIMITS[joint]
                    assert lo <= servo[ch] <= hi
                    assert (servo[ch] - C.SERVO_ANCHORS[joint]) % C.SERVO_STEPS[joint] == 0 or servo[ch] in (lo, hi), (joint, servo)
                tested += 1
    assert tested > 100 and worst < 0.1, (tested, worst)


def test_ik_says_when_a_point_is_out_of_reach():
    far = C.ik_4dof_joint(400.0, 0.0, 25.0)
    assert not far["reachable"] and far["move_closer_mm"] > 50
    assert C.ik_4dof_joint(220.0, 0.0, 25.0)["reachable"]


@pytest.mark.parametrize("heading", [-90.0, 0.0, 37.0, 90.0, 180.0])
def test_table_robot_transform_round_trip_for_any_heading(heading):
    cfg = dict(C.ARM_CONFIG, base_x_cm=12.0, base_y_cm=-5.0, base_heading_deg=heading)
    for x, y in ((14.85, 10.5), (3.0, 18.0), (28.0, 2.0)):
        rx, ry = C.table_cm_to_robot_mm(x, y, cfg)
        assert C.robot_mm_to_table_cm(rx, ry, cfg) == pytest.approx((x, y), abs=1e-6)


def test_default_robot_stands_outside_the_y0_edge_looking_into_the_sheet():
    cfg = C.ARM_CONFIG
    assert (cfg["base_x_cm"], cfg["base_y_cm"], cfg["base_heading_deg"]) == (14.85, -7.5, 90.0)
    x_mm, y_mm = C.table_cm_to_robot_mm(14.85, 10.5)
    assert x_mm == pytest.approx((10.5 + 7.5) * 10) and abs(y_mm) < 1e-6  # Tâm giấy nằm thẳng phía trước, cách 18 cm
    assert C.table_cm_to_robot_mm(24.85, 10.5)[1] == pytest.approx(100.0)  # Lệch +10 cm theo X = 10 cm sang TRÁI robot


def test_predict_tip_at_home_matches_forward_kinematics():
    x_cm, y_cm, z_mm = C.predict_tip([90, 90, 90, 95])
    fx, fy, fz = C.fk_4dof_joint(*C.arduino_servo_to_joint([90, 90, 90, 95]))
    assert (x_cm, y_cm) == pytest.approx(C.robot_mm_to_table_cm(fx, fy)) and z_mm == pytest.approx(fz)


# ----------------------------------------------------------------------------- lệnh bấm phím
def test_moves_tell_which_key_how_many_times_and_which_way():
    base, shoulder, elbow = C.plan_moves([90, 90, 90, 95], [74, 60, 86, 95])
    # Đế 90 -> 74 = giảm 16° = 8 lần D (bước 2°), sang TRÁI theo cam NGANG
    assert (base.key, base.steps, base.degrees, base.words, base.step) == ("d", 8, 16, "SANG TRAI", 2)
    assert (shoulder.key, shoulder.steps, shoulder.degrees, shoulder.words) == ("s", 15, 30, "HA XUONG")
    assert (elbow.key, elbow.steps, elbow.degrees, elbow.words) == ("k", 2, 4, "KHUYU XUONG")


def test_moves_to_the_right_and_up_use_the_other_keys():
    base, shoulder, elbow = C.plan_moves([70, 60, 80, 95], [76, 70, 90, 95])
    assert (base.key, base.steps, base.words) == ("a", 3, "SANG PHAI")
    assert (shoulder.key, shoulder.steps, shoulder.words) == ("w", 5, "NANG LEN")
    assert (elbow.key, elbow.steps, elbow.words) == ("i", 5, "KHUYU LEN")


def test_a_servo_already_on_target_needs_no_key():
    moves = C.plan_moves([74, 60, 86, 95], [74, 60, 86, 95])
    assert all(m.key is None and m.steps == 0 and m.degrees == 0 and m.words == "" for m in moves)


def test_the_gripper_is_never_part_of_the_plan():
    moves = C.plan_moves([74, 60, 86, 95], [74, 60, 86, 150])
    assert [m.joint for m in moves] == ["base", "shoulder", "elbow"] and all(m.steps == 0 for m in moves)


# ----------------------------------------------------------------------------- phím mô phỏng
def test_simulated_keys_move_arm_servos_2_degrees_and_the_gripper_5():
    link = C.ArduinoSerialLink(enabled=False)
    for key in "ddwwwik":
        link.apply_key_locally(key)
    assert link.get_state()[0][:3] == [180 - 4, 90 + 6, 90 + 2 - 2]  # Đế khởi động ở 180° (hết bên phải)
    link.apply_key_locally("l")
    link.apply_key_locally("l")
    assert link.get_state()[0][3] == 95 + 10
    for _ in range(30):
        link.apply_key_locally("l")
    assert link.get_state()[0][3] == 160  # Giới hạn kẹp của firmware
    for _ in range(120):
        link.apply_key_locally("w")
    assert link.get_state()[0][1] == 155  # Vai bị chặn ở giới hạn
    link.apply_key_locally("h")
    assert link.get_state()[0] == [180, 90, 90, 95]  # Home: đế quay hết sang phải để không che vật ở cam TRÊN


def test_x_and_z_keys_relax_the_gripper_and_the_whole_arm_in_simulation():
    link = C.ArduinoSerialLink(enabled=False)
    link.apply_key_locally("x")
    assert link.relaxed and not link.get_arm_relaxed()
    link.apply_key_locally("z")
    assert link.get_arm_relaxed()
    link.apply_key_locally("w")  # Phím di chuyển cấp xung lại
    assert not link.get_arm_relaxed()


# ----------------------------------------------------------------------------- phím R chụp đích + lập kế hoạch
def aim(ctl, *objects):
    """Camera thấy các vật rồi người bấm R: đích là vật gần đế nhất lúc bấm."""
    ctl.update(list(objects))
    assert ctl.lock_target() == "locked"
    return ctl.update(list(objects))


def test_no_target_and_no_moves_until_r_is_pressed(ctl):
    for objects in ([], [obj(20.0, 12.0)]):  # Thấy vật mà chưa bấm R thì cũng chưa có lệnh
        plan = ctl.update(objects)
        assert not plan.found and plan.target_cm is None and plan.goal == plan.now[:3]
        assert all(m.steps == 0 for m in plan.moves)


def test_r_without_any_object_in_view_gives_no_target(ctl):
    ctl.update([])
    assert ctl.lock_target() == "no_target" and not ctl.update([]).found


def test_plan_for_a_cup_gives_angles_that_point_at_it(ctl):
    plan = aim(ctl, obj(20.0, 12.0))
    assert plan.found and plan.reachable and plan.target_cm == pytest.approx((20.0, 12.0))
    # FK của góc cần tới phải trùng vật (sai số do làm tròn về bước 2° còn dưới 2 cm)
    x_cm, y_cm, z_mm = C.predict_tip(plan.goal)
    assert math.hypot(x_cm - 20.0, y_cm - 12.0) < 2.0 and abs(z_mm - C.GRASP_Z_MM) < 20
    assert plan.moves[0].key in ("a", "d") and plan.n_objects == 1 and plan.target_name == "Vat mau"


def test_an_object_too_far_is_reported_as_out_of_reach(ctl):
    plan = aim(ctl, obj(14.85, 28.0))  # Cách đế ~35 cm
    assert plan.found and not plan.reachable and plan.move_closer_mm > 30


def test_following_the_moves_with_the_keys_reaches_the_goal(ctl):
    plan = aim(ctl, obj(20.0, 12.0))
    assert sum(m.steps for m in plan.moves) > 0
    for m in plan.moves:
        for _ in range(m.steps):
            assert ctl.press(m.key)
    after = ctl.update([obj(20.0, 12.0)])
    assert after.now[:3] == plan.goal  # Bấm đúng số lần thì servo đứng đúng góc cần tới
    assert all(m.degrees == 0 for m in after.moves)


def test_r_takes_the_object_nearest_to_the_base(ctl):
    near, far = obj(15.0, 5.0, "gan"), obj(25.0, 15.0, "xa")
    plan = aim(ctl, far, near)
    assert plan.target_name == "gan" and plan.n_objects == 2


def test_the_target_stays_where_r_was_pressed_until_r_is_pressed_again(ctl):
    first = aim(ctl, obj(20.0, 12.0))
    moved = ctl.update([obj(10.0, 6.0)])  # Vật bị dời: đích vẫn là chỗ lúc bấm R
    hidden = ctl.update([])               # Càng kẹp che mất vật: đích vẫn còn
    for plan in (moved, hidden):
        assert plan.found and plan.target_cm == pytest.approx((20.0, 12.0)) and plan.goal == first.goal
    again = aim(ctl, obj(10.0, 6.0))      # Bấm R lại: chụp vị trí mới
    assert again.target_cm == pytest.approx((10.0, 6.0)) and again.goal != first.goal


def test_the_goal_is_computed_once_when_r_is_pressed(ctl, monkeypatch):
    calls = []
    real_ik = C.ik_4dof_joint
    monkeypatch.setattr(C, "ik_4dof_joint", lambda *a, **k: calls.append(1) or real_ik(*a, **k))
    aim(ctl, obj(20.0, 12.0))
    for _ in range(5):
        ctl.update([obj(20.0, 12.0)])
    assert len(calls) == 1  # Mỗi khung chỉ so góc servo với góc đích, không tính lại IK


def test_moving_the_base_drops_the_old_target(ctl):
    before = aim(ctl, obj(20.0, 12.0))
    ctl.set_base_pose(20.0, -7.5, 90.0)  # Đế dịch sang phải 5 cm: góc đích cũ không còn đúng
    assert not ctl.update([obj(20.0, 12.0)]).found  # Phải bấm R lại
    after = aim(ctl, obj(20.0, 12.0))
    assert after.goal[0] != before.goal[0]


# ----------------------------------------------------------------------------- phím và cổng USB
def test_press_sends_only_control_keys(ctl):
    assert all(ctl.press(k) for k in "wasdikjlhxzWASD")
    assert not any(ctl.press(k) for k in ("q", "b", "u", "1", " ", "", None))


def test_the_gripper_keys_do_not_change_the_arm_plan(ctl):
    base = aim(ctl, obj(20.0, 12.0))
    ctl.press("l")
    after = ctl.update([obj(20.0, 12.0)])
    assert after.now[3] == 100 and [m.steps for m in after.moves] == [m.steps for m in base.moves]


def test_control_warns_once_when_the_arduino_resets(ctl):
    assert ctl.update([]).banner == ""
    ctl.link.reset_count += 1  # Gói JSON báo thời gian chạy tụt về 0
    assert "ARDUINO VUA RESET" in ctl.update([]).banner
