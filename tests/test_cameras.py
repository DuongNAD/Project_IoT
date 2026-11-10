"""Tìm camera theo tên (đúng thứ tự chỉ số của OpenCV), đọc ảnh tĩnh để chạy thử, chờ khi chưa có camera."""

import json
import sys
import time
import types

import cv2
import numpy as np

import cameras as C


def test_find_camera_by_name_and_skip_virtual_cameras(monkeypatch):
    monkeypatch.setattr(C, "list_camera_names", lambda: ["OBSBOT Virtual Camera", "Camera MacBook Air", "OBSBOT Meet SE"])
    assert C.find_camera(C.CAMERAS["obsbot"][1]) == 2  # Bỏ camera ảo của phần mềm OBSBOT
    assert C.find_camera(C.CAMERAS["mac"][1]) == 1
    assert C.find_camera(("logitech",)) is None


def test_mac_camera_list_is_sorted_by_unique_id_like_opencv(monkeypatch):
    """macOS đưa camera dùng gần nhất lên đầu, còn OpenCV đánh số theo uniqueID: danh sách phải theo thứ tự của OpenCV."""
    data = {"SPCameraDataType": [{"_name": "Camera MacBook Air", "spcamera_unique-id": "B"}, {"_name": "OBSBOT Meet SE", "spcamera_unique-id": "A"}]}
    monkeypatch.setattr(C.sys, "platform", "darwin")
    monkeypatch.setattr(C.subprocess, "run", lambda *a, **k: types.SimpleNamespace(stdout=json.dumps(data)))
    assert C.list_camera_names() == ["OBSBOT Meet SE", "Camera MacBook Air"]
    monkeypatch.setattr(C.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(OSError("không có system_profiler")))
    assert C.list_camera_names() == []


def test_windows_camera_list_follows_directshow_and_the_laptop_webcam_is_the_side_camera(monkeypatch):
    fake = types.SimpleNamespace(FilterGraph=lambda: types.SimpleNamespace(get_input_devices=lambda: ["Iriun Webcam", "Integrated Webcam"]))
    monkeypatch.setattr(C.sys, "platform", "win32")
    monkeypatch.setitem(sys.modules, "pygrabber", types.SimpleNamespace(dshow_graph=fake))
    monkeypatch.setitem(sys.modules, "pygrabber.dshow_graph", fake)
    assert C.list_camera_names() == ["Iriun Webcam", "Integrated Webcam"]
    assert C.find_camera(C.CAMERAS["mac"][1]) == 1


def test_a_still_image_is_read_again_and_again(tmp_path):
    path = tmp_path / "anh.png"
    cv2.imwrite(str(path), np.full((90, 160, 3), 7, np.uint8))
    cam = C.Camera(str(path), "TREN")
    try:
        end = time.time() + 2
        while time.time() < end and cam.frame_id < 3:
            time.sleep(0.02)
        assert cam.frame_id >= 3 and cam.get_raw_frame().shape == (90, 160, 3)
        assert (cam.label, cam.source) == ("anh.png", str(path))
    finally:
        cam.release()


def test_a_missing_camera_shows_the_waiting_image(monkeypatch):
    monkeypatch.setattr(C, "list_camera_names", lambda: ["Camera MacBook Air"])
    cam = C.Camera("obsbot", "TREN")
    try:
        time.sleep(0.2)
        assert cam.get_raw_frame() is None and cam.source is None
        waiting = cam.waiting_image()
        assert waiting.shape == (360, 640, 3) and waiting.any()
    finally:
        cam.release()
