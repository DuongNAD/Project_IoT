"""Tham số dòng lệnh, chạy toàn chương trình không cửa sổ trên khung giả lập, hiệu chỉnh đế bằng chuột và phím tắt."""

import json
import time

import cv2
import pytest
from synth import draw_disc, render, sheet_texture, side_camera, top_camera

import calibration
import cameras as C
import control
import main as M
import screen


def test_parse_args_defaults_and_options():
    args = M.parse_args([])
    assert (args.top, args.side) == ("auto", "auto")
    assert not (args.no_serial or args.headless or args.yolo) and args.rotate_top is None  # Mặc định chỉ tách vật theo màu, không YOLO
    assert M.parse_args(["--yolo"]).yolo is True
    args = M.parse_args(["--top", "1", "--side", "phone", "--rotate-side", "180", "--no-serial", "--headless", "--seconds", "3"])
    assert (args.top, args.side, args.rotate_side, args.seconds) == ("1", "phone", 180, 3.0)
    with pytest.raises(SystemExit):
        M.parse_args(["--rotate-top", "45"])  # Chỉ nhận 0 / 90 / 180 / 270


def test_slug_and_camera_report(capsys, monkeypatch):
    assert M.slug("Cam TREN: OBSBOT (1)") == "cam_tren_obsbot_1"
    monkeypatch.setattr(C, "list_camera_names", lambda: (["OBSBOT Meet SE", "Camera MacBook Air"], "avfoundation"))
    monkeypatch.setattr(M, "list_camera_names", C.list_camera_names)
    M.report_cameras(C.top_spec(), C.builtin_spec())
    out = capsys.readouterr().out
    assert "[0] OBSBOT Meet SE" in out and "Cam TREN" in out and "OBSBOT (index 0)" in out and "MacBook (index 1)" in out
    monkeypatch.setattr(C, "list_camera_names", lambda: ([], "none"))
    monkeypatch.setattr(M, "list_camera_names", C.list_camera_names)
    M.report_cameras(C.top_spec(), C.builtin_spec())
    assert "KHÔNG THẤY THIẾT BỊ" in capsys.readouterr().out


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
    monkeypatch.setattr("vision.PARALLAX_CAM_HEIGHT_CM", 0.0)  # Cảnh giả lập vẽ vật phẳng trên giấy, không có phối cảnh theo độ cao
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
    assert summary["to_giay"]["cam_tren"]["nguon_luoi"] == "aruco" and summary["to_giay"]["cam_tren"]["so_ma_dang_dung"] == 4
    assert summary["to_giay"]["cam_ngang"]["nguon_luoi"] == "aruco"
    cup = summary["vat_the"][0]
    assert abs(cup["x_cm"] - 20.0) < 0.5 and abs(cup["y_cm"] - 12.0) < 0.5
    one, two = summary["nhom_1_dieu_khien"], summary["nhom_2_success"]
    assert one["trong_tam_voi"] is True and len(one["servo_can_toi"]) == 3 and len(one["lenh"]) == 3
    assert two["trang_thai"] in ("moving", "done") and len(two["servo_dung"]) == 3  # Hai phần nối nhau: kết luận dựa trên lệnh của phần 1


def test_click_on_top_view_calibrates_the_robot_base(scene_files):
    app = make_app(scene_files)
    top_cam = scene_files[2]
    window = screen.SCREEN_WINDOW
    try:
        assert wait_until(app, lambda: app.top_shape is not None and app.tracker.latest_view["topdown"].source == "aruco")
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


def test_keys_swap_calibrate_and_quit(scene_files, monkeypatch):
    requested = []

    class RecordingCapture:
        """Camera giả ghi lại chỉ số được yêu cầu, để phím '1' không mở camera thật."""

        def __init__(self, source, *args):
            requested.append(source)

        def set(self, *args):
            return True

        def isOpened(self):
            return False

        def read(self):
            return False, None

        def release(self):
            pass

    monkeypatch.setattr(cv2, "VideoCapture", RecordingCapture)
    app = make_app(scene_files)
    try:
        assert app.handle_key(ord("b")) and app.calib_base
        assert app.handle_key(27) and not app.calib_base  # ESC hủy hiệu chỉnh
        side, top = app.cam_side, app.cam_top
        assert app.handle_key(ord("t"))  # Tráo vai trò 2 camera
        assert app.cam_side is top and app.cam_top is side
        assert (app.cam_side.role, app.cam_top.role) == ("NGANG", "TREN")
        assert app.handle_key(ord("u"))  # Quên các mã đã nhớ
        assert app.handle_key(ord("x"))  # Phím X thuộc về cánh tay (servo kẹp nghỉ), không bị main nuốt
        assert app.control.link.relaxed
        assert app.handle_key(ord("1")) and app.cam_top.spec.kind == "index"
        end = time.time() + 2
        while time.time() < end and requested != [1]:
            time.sleep(0.02)
        assert requested == [1]  # Luồng camera đã mở lại đúng chỉ số 1 bằng camera giả
        assert app.handle_key(ord("q")) is False
    finally:
        app.close()


def test_servo_keys_move_the_simulated_arm_and_tab_changes_the_target(scene_files):
    app = make_app(scene_files)
    try:
        assert wait_until(app, lambda: app.control.objects)
        for key in "ddw":
            assert app.handle_key(ord(key))
        assert app.control.link.get_state()[0][:3] == [86, 92, 90]  # Mô phỏng: mỗi lần bấm 2°
        assert app.handle_key(9)  # TAB
        assert app.handle_key(255)  # Không có phím nào (waitKey hết giờ) thì bỏ qua
    finally:
        app.close()


def test_snapshots_save_both_raw_frames(scene_files, tmp_path, monkeypatch):
    monkeypatch.setattr(M, "CAPTURE_DIR", str(tmp_path / "captures"))
    app = make_app(scene_files)
    try:
        assert wait_until(app, lambda: app.cam_top.get_raw_frame() is not None and app.cam_side.get_raw_frame() is not None)
        app.handle_key(ord("c"))
    finally:
        app.close()
    saved = sorted(p.name for p in (tmp_path / "captures").iterdir())
    assert len(saved) == 2 and any("ngang" in n for n in saved) and any("tren" in n for n in saved)


def test_swapped_camera_roles_are_detected(scene_files):
    top_path, side_path, _ = scene_files
    ok = make_app(scene_files)
    swapped = M.App(M.parse_args(["--top", str(side_path), "--side", str(top_path), "--no-serial", "--headless"]))
    try:
        assert wait_until(ok, lambda: ok.tracker.latest_view["topdown"].source == "aruco" and ok.tracker.latest_view["side"].source == "aruco")
        assert wait_until(swapped, lambda: swapped.tracker.latest_view["topdown"].source == "aruco" and swapped.tracker.latest_view["side"].source == "aruco")
        assert not ok.roles_look_swapped()
        assert swapped.roles_look_swapped()  # Cam "TREN" đang nhìn xiên, cam "NGANG" đang nhìn thẳng
    finally:
        ok.close()
        swapped.close()
