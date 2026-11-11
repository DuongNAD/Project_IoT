"""Tham số dòng lệnh, chạy toàn chương trình không cửa sổ trên khung giả lập, hiệu chỉnh đế bằng chuột và phím tắt."""

import json
import time

import cv2
import pytest
from synth import draw_disc, render, sheet_texture, side_camera, top_camera

import calibration
import control
import main as M
import screen


def test_parse_args_defaults_and_options():
    args = M.parse_args([])
    assert (args.top, args.side) == ("obsbot", "mac") and not (args.no_serial or args.headless)
    args = M.parse_args(["--top", "1", "--side", "anh.png", "--no-serial", "--headless", "--seconds", "3"])
    assert (args.top, args.side, args.no_serial, args.seconds) == ("1", "anh.png", True, 3.0)


def test_camera_report(capsys, monkeypatch):
    monkeypatch.setattr(M, "list_camera_names", lambda: ["OBSBOT Meet SE", "Camera MacBook Air"])
    M.report_cameras()
    assert "[0] OBSBOT Meet SE, [1] Camera MacBook Air" in capsys.readouterr().out
    monkeypatch.setattr(M, "list_camera_names", lambda: [])
    M.report_cameras()
    assert "không thấy camera nào" in capsys.readouterr().out


@pytest.fixture
def scene_files(tmp_path):
    top, side = top_camera(), side_camera()
    texture = sheet_texture(lambda img: draw_disc(img, 20.0, 12.0, 2.2))
    top_path, side_path = tmp_path / "top.png", tmp_path / "side.png"
    cv2.imwrite(str(top_path), render(top, texture))
    cv2.imwrite(str(side_path), render(side, texture))
    return top_path, side_path, top


def make_app(scene_files, *extra):
    top_path, side_path, _ = scene_files
    args = M.parse_args(["--top", str(top_path), "--side", str(side_path), "--no-serial", "--headless", *extra])
    return M.App(args)


def wait_until(app, predicate, timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        app.render()
        if predicate():
            return True
        time.sleep(0.03)
    return False


def test_headless_run_writes_the_screen_and_a_summary_with_both_parts(scene_files, tmp_path, monkeypatch):
    monkeypatch.setattr("vision.CAM_HEIGHT_CM", 0.0)  # Cảnh giả lập vẽ vật phẳng trên giấy, không có phối cảnh theo độ cao
    out = tmp_path / "out"
    app = make_app(scene_files, "--seconds", "2", "--dump-dir", str(out))
    try:
        app.run_headless()
    finally:
        app.close()
    for name in ("dual_view.png", "cam_tren_annotated.jpg", "cam_ngang_annotated.jpg", "summary.json"):
        assert (out / name).exists(), name
    assert not (out / "guide.png").exists()  # Chỉ còn một cửa sổ
    assert cv2.imread(str(out / "dual_view.png")).shape[:2] == (screen.SCREEN_H, screen.SCREEN_W)
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["to_giay"]["cam_tren"] == {"co_luoi": True, "so_ma_thay": 4, "so_ma_da_nho": 4}
    assert summary["to_giay"]["cam_ngang"]["co_luoi"] is True
    cup = summary["vat_the"][0]
    assert abs(cup["x_cm"] - 20.0) < 0.5 and abs(cup["y_cm"] - 12.0) < 0.5
    one, two = summary["dieu_khien"], summary["success"]
    assert one["trong_tam_voi"] is True and len(one["servo_can_toi"]) == 3 and len(one["lenh"]) == 3
    assert two["trang_thai"] in ("moving", "done") and len(two["servo_dung"]) == 3  # Hai phần nối nhau: kết luận dựa trên lệnh của phần 1


def test_click_on_top_view_calibrates_the_robot_base(scene_files):
    app = make_app(scene_files)
    top_cam = scene_files[2]
    window = screen.SCREEN_WINDOW
    try:
        assert wait_until(app, lambda: app.top_shape is not None and app.vision.sheets["topdown"].H_px2cm is not None)
        u, v = top_cam.project(13.0, -6.0)  # Điểm trục xoay đế ngoài mép giấy
        x, y = screen.CAM_W + u * (screen.CAM_W / 1920), v * (screen.CAM_W / 1920)  # Khung 1920x1080 thu vào ô 640x360 bên phải
        # Chưa bật chế độ hiệu chỉnh thì click không có tác dụng
        app.on_mouse(cv2.EVENT_LBUTTONDOWN, int(x), int(y), 0, window)
        assert control.ARM_CONFIG["base_y_cm"] == pytest.approx(-7.5)
        # Click vào nửa hình cam NGANG (bên trái) bị từ chối, vẫn chờ click đúng
        app.calib_base = True
        app.on_mouse(cv2.EVENT_LBUTTONDOWN, 100, 100, 0, window)
        assert app.calib_base
        app.on_mouse(cv2.EVENT_LBUTTONDOWN, int(x), int(y), 0, window)
        assert not app.calib_base
        assert control.ARM_CONFIG["base_x_cm"] == pytest.approx(13.0, abs=0.7)
        assert control.ARM_CONFIG["base_y_cm"] == pytest.approx(-6.0, abs=0.7)
        assert control.ARM_CONFIG["base_heading_deg"] == 90.0
        saved = calibration.load_calibration()
        assert saved["base"]["heading_deg"] == 90.0 and abs(saved["base"]["x_cm"] - 13.0) < 0.7
    finally:
        app.close()


def test_keys_calibrate_reset_and_quit(scene_files):
    app = make_app(scene_files)
    try:
        assert app.handle_key(ord("b")) and app.calib_base
        assert app.handle_key(27) and not app.calib_base  # ESC hủy hiệu chỉnh
        assert app.handle_key(ord("u"))  # Quên các mã đã nhớ
        assert app.handle_key(ord("x"))  # Phím X thuộc về cánh tay (servo kẹp nghỉ), không bị main nuốt
        assert app.control.link.relaxed
        assert app.handle_key(ord("q")) is False
    finally:
        app.close()


def test_servo_keys_move_the_simulated_arm(scene_files):
    app = make_app(scene_files)
    try:
        assert wait_until(app, lambda: app.control.objects)
        for key in "ddw":
            assert app.handle_key(ord(key))
        assert app.control.link.get_state()[0][:3] == [176, 92, 90]  # Mô phỏng: mỗi lần bấm 2°, đế bắt đầu ở 180°
        assert app.handle_key(255)  # Không có phím nào (waitKey hết giờ) thì bỏ qua
    finally:
        app.close()
