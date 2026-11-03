"""Màn hình 2 phần nối nhau: phần 1 ĐIỀU KHIỂN (từ Plan) và phần 2 SUCCESS (từ Result), cùng 2 camera ở trên."""

import numpy as np

import control as C
import screen as SC
import success as S
from test_success import make_plan


def draw(now, goal, **kw):
    plan = make_plan(now, goal, **kw)
    cam = np.full((480, 640, 3), 70, np.uint8)
    return SC.build_screen(cam, cam, plan, S.check(plan)), plan


def test_screen_has_two_parts_that_change_with_the_state():
    moving, _ = draw([90, 90, 90, 95], [74, 60, 86, 95])
    done, _ = draw([74, 60, 86, 95], [74, 60, 86, 95])
    nothing, _ = draw([90, 90, 90, 95], [74, 60, 86, 95], found=False)
    assert moving.shape == (SC.SCREEN_H, SC.SCREEN_W, 3)
    cams = slice(0, SC.CAM_H)
    assert (moving[cams] == done[cams]).all()  # Hai camera ở trên không đổi theo trạng thái
    control = (slice(SC.PANEL_Y, SC.PANEL_Y + SC.PANEL_H), slice(SC.CTRL_X0, SC.CTRL_X1))
    success = (slice(SC.PANEL_Y, SC.PANEL_Y + SC.PANEL_H), slice(SC.SUCC_X0, SC.SUCC_X1))
    for part in (control, success):  # Cả hai phần đổi theo trạng thái: đang chạy / xong / chưa thấy vật
        assert (moving[part] != done[part]).any() and (done[part] != nothing[part]).any() and (moving[part] != nothing[part]).any()
    # Phần SUCCESS: viền thẻ xanh lá khi XONG, cam khi chưa xong (kiểm tra màu viền để chắc không đổi nhầm trạng thái)
    edge_y, edge_x = SC.PANEL_Y + 46 + 75, SC.SUCC_X0 + 1
    assert tuple(done[edge_y, edge_x]) == SC.GREEN and tuple(moving[edge_y, edge_x]) == SC.AMBER
    # Hai phần tách riêng nhau và có mũi tên nối ở giữa
    gap_mid = moving[SC.PANEL_Y + SC.PANEL_H // 2, SC.CTRL_X1 + 8:SC.SUCC_X0 - 8]
    assert (gap_mid == SC.AMBER).all(axis=1).any()


def test_unreachable_and_relaxed_states_draw_without_errors():
    for kw in ({"reachable": False, "move_closer_mm": 40.0}, {"relaxed": True}):
        img, _ = draw([90, 90, 90, 95], [74, 60, 86, 95], **kw)
        assert img.shape[:2] == (SC.SCREEN_H, SC.SCREEN_W)


def test_a_success_count_and_a_warning_banner_reach_the_screen():
    plan = make_plan([74, 60, 86, 95], [74, 60, 86, 95])
    cam = np.full((480, 640, 3), 70, np.uint8)
    base = S.check(plan)
    counted = S.check(plan)
    counted.count = 3
    assert (SC.build_screen(cam, cam, plan, base) != SC.build_screen(cam, cam, plan, counted)).any()
    plan.banner = "ARDUINO VUA RESET: kiem tra truoc khi bam tiep"
    assert (SC.build_screen(cam, cam, plan, base) != SC.build_screen(cam, cam, make_plan([74, 60, 86, 95], [74, 60, 86, 95]), base)).any()


def test_the_headline_command_matches_the_first_move():
    plan = make_plan([90, 90, 90, 95], [74, 60, 86, 95])
    result = S.check(plan)
    assert result.next_move.key == "d" and result.next_move.steps == 8  # Lệnh to trên màn hình vẽ đúng Move này
    assert all(SC.SERVO_LIMITS[m.joint][0] <= m.now <= SC.SERVO_LIMITS[m.joint][1] for m in plan.moves)
    assert C.SERVO_LIMITS is SC.SERVO_LIMITS
