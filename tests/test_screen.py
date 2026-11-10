"""Màn hình: 2 camera ở trên, ô 1 ĐIỀU KHIỂN (từ Plan) và ô 2 SUCCESS (từ Result) đổi theo trạng thái."""

import numpy as np
from test_success import make_plan

import screen as SC
import success as S

CAM = np.full((480, 640, 3), 70, np.uint8)
BOXES = slice(SC.CAM_H, SC.SCREEN_H - 56)
CONTROL, SUCCESS = (BOXES, slice(0, 820)), (BOXES, slice(830, SC.SCREEN_W))


def draw(plan, result=None):
    return SC.build_screen(CAM, CAM, plan, result or S.check(plan))


def test_both_boxes_change_with_the_state_and_the_cameras_do_not():
    moving = draw(make_plan([90, 90, 90, 95], [74, 60, 86, 95]))
    done = draw(make_plan([74, 60, 86, 95], [74, 60, 86, 95]))
    nothing = draw(make_plan([90, 90, 90, 95], [74, 60, 86, 95], found=False))
    assert moving.shape == (SC.SCREEN_H, SC.SCREEN_W, 3)
    assert (moving[:SC.CAM_H] == done[:SC.CAM_H]).all()
    for box in (CONTROL, SUCCESS):
        assert (moving[box] != done[box]).any() and (done[box] != nothing[box]).any() and (moving[box] != nothing[box]).any()

    def green(img):
        return (img[SUCCESS] == SC.GREEN).all(axis=2).any()

    assert green(done) and not green(moving)  # XONG! màu xanh lá, CHUA XONG màu cam


def test_unreachable_and_relaxed_states_draw():
    for kw in ({"reachable": False, "move_closer_mm": 40.0}, {"relaxed": True}):
        assert draw(make_plan([90, 90, 90, 95], [74, 60, 86, 95], **kw)).shape == (SC.SCREEN_H, SC.SCREEN_W, 3)


def test_the_success_count_and_a_warning_banner_reach_the_screen():
    plan = make_plan([74, 60, 86, 95], [74, 60, 86, 95])
    base, counted = S.check(plan), S.check(plan)
    counted.count = 3
    assert (draw(plan, base) != draw(plan, counted)).any()
    warned = make_plan([74, 60, 86, 95], [74, 60, 86, 95])
    warned.banner = "ARDUINO VUA RESET: kiem tra truoc khi bam tiep"
    assert (draw(plan, base) != draw(warned, base)).any()
