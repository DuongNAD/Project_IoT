"""Cả chuỗi nối nhau trên cảnh giả lập: camera -> vision -> NHÓM 1 điều khiển -> NHÓM 2 success. Làm đúng theo lệnh trên màn hình thì phải ra XONG."""

import time

import cv2
from synth import draw_disc, render, sheet_texture, side_camera, top_camera
from test_main import make_app, wait_until

import main as M
import success as S


def test_following_the_on_screen_commands_ends_with_done_and_one_counted_success(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "HOLD_S", 0.05)  # Giữ đúng góc 50 ms là đủ để đếm 1 lần thành công
    top_path, side_path = tmp_path / "top.png", tmp_path / "side.png"
    cv2.imwrite(str(top_path), render(top_camera(), sheet_texture(lambda img: draw_disc(img, 20.0, 12.0, 2.2))))
    cv2.imwrite(str(side_path), render(side_camera(), sheet_texture()))
    app = make_app((top_path, side_path, None))
    try:
        assert wait_until(app, lambda: app.control.objects)
        _, plan, result = app.render()
        assert plan.found and plan.reachable and result.state == "moving" and not result.done
        total = result.remaining

        pressed = 0
        for _ in range(10):  # Làm đúng như lệnh to trên màn hình: bấm phím `key` `steps` lần, rồi nhìn lại lệnh mới
            _, plan, result = app.render()
            if result.done:
                break
            move = result.next_move
            for _ in range(move.steps):
                assert app.handle_key(ord(move.key))
                pressed += 1
        _, plan, result = app.render()
        assert result.done and result.state == "done" and all(result.joints_ok)
        assert 0 < pressed <= total  # Không bấm thừa: đúng số lần mà lệnh đầu tiên đã đếm

        time.sleep(0.1)
        _, _, result = app.render()
        assert result.done and result.count == 1  # Giữ đúng góc đủ lâu: đếm 1 lần thành công
        time.sleep(0.1)
        assert app.render()[2].count == 1          # Giữ thêm không đếm lần nữa

        app.handle_key(ord("w"))                   # Bấm lệch khỏi góc gợi ý (2 lần = 4°) thì hết XONG
        app.handle_key(ord("w"))
        assert not app.render()[2].done
        assert app.render()[2].count == 1          # Số lần thành công đã đếm không mất
    finally:
        app.close()


def test_the_two_parts_hand_over_the_same_plan(tmp_path):
    """Phần 2 chỉ đọc Plan của phần 1: cùng một Plan cho cùng một kết luận, không cần camera hay cổng USB."""
    import control as C
    plan = C.Control(serial_enabled=False).update([{"name": "Vat mau", "x_cm": 20.0, "y_cm": 12.0, "w_mm": 35.0, "h_mm": 40.0, "px": (0, 0), "source": "color"}])
    assert S.check(plan).state == S.check(plan).state == "moving" and S.check(plan).remaining == sum(m.steps for m in plan.moves if m.degrees > m.step)
