"""Tình huống khắc nghiệt: ảnh nhiễu / mờ, không thấy tờ giấy, thiếu camera, đổi độ phân giải giữa chừng."""

import json
import time

import cv2
import numpy as np
from synth import (
    FRAME_H,
    FRAME_W,
    corner_error_px,
    draw_disc,
    render,
    sheet_texture,
    side_camera,
    top_camera,
)
from test_main import wait_until

import cameras as C
import main as M
import vision as V


def noisy(frame, sigma=6.0, blur=3, seed=1):
    """Thêm nhiễu cảm biến và làm mờ nhẹ như camera thật ở chỗ thiếu sáng."""
    rng = np.random.default_rng(seed)
    out = cv2.GaussianBlur(frame, (0, 0), blur / 2.0)
    return np.clip(out.astype(np.float32) + rng.normal(0, sigma, out.shape), 0, 255).astype(np.uint8)


def test_homography_survives_sensor_noise_and_blur():
    cam = side_camera()
    frame = noisy(render(cam, sheet_texture()))
    tracker = V.SheetTracker(max_rms_px=15.0)
    for _ in range(3):
        view = tracker.update(frame)
    assert view.source == "aruco" and corner_error_px(view, cam) < 4.0


def test_a_scene_without_the_sheet_is_handled_without_errors(ctl):
    empty = np.full((FRAME_H, FRAME_W, 3), 90, np.uint8)
    tracker = V.ArucoYoloTracker(use_yolo=False)
    try:
        for mode in ("topdown", "side"):
            out = tracker.process_frame(empty, mode)
            assert out.shape == empty.shape
            assert tracker.latest_view[mode].H_px2cm is None or tracker.latest_view[mode].source == "fallback"
        plan = ctl.update(tracker.objects)  # Không có vật, không có lưới: vẫn ra kế hoạch trống, không lỗi
        assert not plan.found and len(plan.moves) == 3 and all(m.steps == 0 for m in plan.moves)
        assert tracker.process_frame(None, "side") is None
    finally:
        tracker.stop()


def test_tracker_relearns_when_the_frame_resolution_changes():
    cam = top_camera()
    frame = render(cam, sheet_texture())
    tracker = V.SheetTracker()
    for _ in range(3):
        tracker.update(frame)
    half = cv2.resize(frame, (FRAME_W // 2, FRAME_H // 2), interpolation=cv2.INTER_AREA)
    for _ in range(4):  # Camera đổi sang độ phân giải khác: sau vài khung phải bám theo, không dùng bộ nhớ cũ
        view = tracker.update(half)
    u, v = V.cm_to_px(view.H_cm2px, 0, 0)
    tu, tv = cam.project(0, 0)
    assert abs(u - tu / 2) < 3 and abs(v - tv / 2) < 3


def test_app_runs_with_a_missing_camera(tmp_path, monkeypatch):
    """Thiếu cam TREN (không thấy thiết bị tên đó): chương trình vẫn chạy, hiện khung chờ tín hiệu, summary không lỗi."""
    monkeypatch.setattr(C, "list_camera_names", lambda: (["Camera MacBook Air"], "avfoundation"))
    side_path = tmp_path / "side.png"
    cv2.imwrite(str(side_path), render(side_camera(), sheet_texture()))
    out = tmp_path / "out"
    args = M.parse_args(["--top", "obsbot", "--side", str(side_path), "--no-serial", "--headless", "--seconds", "1.5", "--dump-dir", str(out)])
    app = M.App(args)
    try:
        app.run_headless()
    finally:
        app.close()
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["camera"]["TREN"]["kich_thuoc"] is None and summary["camera"]["TREN"]["nguon"] == "None"
    assert summary["to_giay"]["cam_tren"]["nguon_luoi"] == "none"
    assert summary["to_giay"]["cam_ngang"]["nguon_luoi"] == "aruco"  # Cam NGANG vẫn hoạt động bình thường
    assert summary["hai_camera_co_ve_bi_gan_nguoc"] is False
    assert cv2.imread(str(out / "dual_view.png")) is not None


def test_stream_reconnects_when_the_device_appears_later(monkeypatch):
    """Cắm cáp muộn: camera chưa có lúc mở thì vài giây sau luồng tự tìm lại theo tên và mở được."""
    present = {"value": False}
    monkeypatch.setattr(C, "RETRY_SECONDS", 0.3)

    def fake_names():
        return (["OBSBOT Meet SE", "Camera MacBook Air"] if present["value"] else ["Camera MacBook Air"]), "avfoundation"

    class FakeCapture:
        def __init__(self, source, api=None):  # api: cv2.CAP_DSHOW khi chạy test trên Windows
            self.source = source

        def set(self, *args):
            return True

        def isOpened(self):
            return True

        def read(self):
            time.sleep(0.01)
            return True, np.zeros((90, 160, 3), np.uint8)

        def get(self, *args):
            return 30.0

        def release(self):
            pass

    monkeypatch.setattr(C, "list_camera_names", fake_names)
    monkeypatch.setattr(C.cv2, "VideoCapture", FakeCapture)
    cam = C.CameraStream(C.top_spec(), "TREN")
    try:
        time.sleep(0.5)
        assert cam.get_raw_frame() is None  # Chưa cắm
        present["value"] = True
        end = time.time() + 3
        while time.time() < end and cam.get_raw_frame() is None:
            time.sleep(0.05)
        assert cam.get_raw_frame() is not None and cam.source == 0
    finally:
        cam.release()


def test_dropped_camera_shows_the_waiting_screen_and_forgets_stale_objects(tmp_path, monkeypatch):
    """Camera rớt tín hiệu: không được giữ ảnh đứng hình và danh sách vật cũ; cắm lại thì tự hoạt động trở lại."""
    top_frame = render(top_camera(), sheet_texture(lambda img: draw_disc(img, 20.0, 12.0, 2.2)))
    side_path = tmp_path / "side.png"
    cv2.imwrite(str(side_path), render(side_camera(), sheet_texture()))
    state = {"alive": True}

    class FlakyCapture:
        def __init__(self, source, api=None):  # api: cv2.CAP_DSHOW khi chạy test trên Windows
            pass

        def set(self, *args):
            return True

        def isOpened(self):
            return True

        def read(self):
            time.sleep(0.02)
            return (True, top_frame.copy()) if state["alive"] else (False, None)

        def get(self, *args):
            return 30.0

        def release(self):
            pass

    monkeypatch.setattr(C.cv2, "VideoCapture", FlakyCapture)
    monkeypatch.setattr(C, "RETRY_SECONDS", 0.6)
    args = M.parse_args(["--top", "0", "--side", str(side_path), "--no-serial", "--headless"])
    app = M.App(args)
    try:
        assert wait_until(app, lambda: app.control.objects and app.top_shape is not None)
        state["alive"] = False
        assert wait_until(app, lambda: app.cam_top.get_raw_frame() is None and not app.tracker.objects, timeout=5)
        assert app.top_shape is None and "topdown" not in app.cache
        waiting = app._frame(app.cam_top, "topdown")
        assert waiting.shape == (480, 640, 3)  # Khung "Dang cho tin hieu", không phải ảnh cũ
        state["alive"] = True
        assert wait_until(app, lambda: app.control.objects and app.top_shape is not None, timeout=8)
    finally:
        app.close()
