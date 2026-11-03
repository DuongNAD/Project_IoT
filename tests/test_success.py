"""NHÓM 2 - SUCCESS: đã tới chưa? Nhận Plan của nhóm điều khiển, trả lời xong / chưa xong, còn bao nhiêu lần bấm, đếm số lần thành công."""

import control as C
import success as S


def make_plan(now, goal, found=True, reachable=True, relaxed=False, move_closer_mm=0.0):
    return C.Plan(found=found, target_name="Vat mau", target_cm=(20.0, 12.0) if found else None, reachable=reachable,
                  move_closer_mm=move_closer_mm, relaxed=relaxed, now=list(now), goal=list(goal), moves=C.plan_moves(now, goal))


def test_moving_until_all_three_servos_are_on_target():
    r = S.check(make_plan([90, 90, 90, 95], [74, 60, 86, 95]))
    assert r.state == "moving" and not r.done and r.joints_ok == [False, False, False]
    assert r.next_move.joint == "base" and r.remaining == 8 + 15 + 2  # Việc đầu tiên: đế, rồi vai, rồi khuỷu


def test_next_move_skips_servos_that_are_already_right():
    r = S.check(make_plan([74, 70, 86, 95], [74, 60, 86, 95]))
    assert r.joints_ok == [True, False, True] and r.next_move.joint == "shoulder" and r.next_move.key == "s" and r.remaining == 5


def test_one_step_off_still_counts_as_arrived_but_three_degrees_does_not():
    # Mô hình hình học chỉ chính xác cỡ 1 bước (2°): bắt căn tới 0° chỉ làm người dùng đuổi theo nhiễu
    done = S.check(make_plan([72, 62, 88, 95], [74, 60, 86, 95]))
    assert done.state == "done" and done.done and done.next_move is None and done.remaining == 0
    not_yet = S.check(make_plan([71, 60, 86, 95], [74, 60, 86, 95]))
    assert not_yet.state == "moving" and not_yet.next_move.steps == 1 and not_yet.remaining == 1


def test_gripper_does_not_matter():
    assert S.check(make_plan([74, 60, 86, 95], [74, 60, 86, 150])).done  # Kẹp lệch 55° mà vẫn XONG


def test_other_states_and_their_priority():
    wrong = ([90, 90, 90, 95], [74, 60, 86, 95])
    assert S.check(make_plan(*wrong, found=False)).state == "no_target"
    assert S.check(make_plan(*wrong, reachable=False, move_closer_mm=35)).state == "unreachable"
    # Cánh tay đang nghỉ (ngắt xung) thắng mọi thứ khác: góc servo báo về chỉ là góc lệnh cuối, không tin được
    assert S.check(make_plan([74, 60, 86, 95], [74, 60, 86, 95], relaxed=True)).state == "relaxed"
    assert not S.check(make_plan([74, 60, 86, 95], [74, 60, 86, 95], relaxed=True)).done
    # Không thấy vật thì dù góc "khớp" vẫn không được báo xong
    assert not S.check(make_plan([74, 60, 86, 95], [74, 60, 86, 95], found=False)).done


def test_a_success_is_counted_only_after_holding_the_angles_long_enough():
    s = S.Success()
    on_target = make_plan([74, 60, 86, 95], [74, 60, 86, 95])
    off = make_plan([90, 90, 90, 95], [74, 60, 86, 95])
    assert s.update(on_target, now=0.0).count == 0                 # Mới tới: chưa đếm
    assert s.update(on_target, now=S.HOLD_S - 0.1).count == 0
    assert s.update(on_target, now=S.HOLD_S + 0.1).count == 1      # Giữ đủ lâu: đếm 1 lần
    assert s.update(on_target, now=S.HOLD_S + 5.0).count == 1      # Giữ thêm không đếm lần nữa
    assert s.update(off, now=10.0).count == 1                      # Rời khỏi góc: giữ nguyên số đã đếm
    assert s.update(on_target, now=11.0).count == 1
    assert s.update(on_target, now=11.0 + S.HOLD_S + 0.1).count == 2  # Tới lại và giữ đủ lâu: lần thứ hai


def test_passing_through_the_target_does_not_count():
    s = S.Success()
    on_target = make_plan([74, 60, 86, 95], [74, 60, 86, 95])
    off = make_plan([90, 90, 90, 95], [74, 60, 86, 95])
    s.update(on_target, now=0.0)
    s.update(off, now=0.4)  # Lướt qua chưa tới HOLD_S đã rời đi
    assert s.update(on_target, now=0.6).count == 0 and s.update(off, now=0.9).count == 0
