"""Chọn camera theo tên (đúng thứ tự chỉ số OpenCV), phân vai TREN / NGANG và luồng đọc camera."""

import time

import cv2
import numpy as np

import cameras as C

# Thứ tự chỉ số OpenCV đo được trên máy này (sắp theo uniqueID, ổn định) và thứ tự thô của hệ điều hành (đổi theo camera dùng gần nhất)
OPENCV_ORDER = ["OBSBOT Meet SE StreamCamera", "Camera MacBook Air", "OBS Virtual Camera"]
SYSTEM_PROFILER_ORDER = ["Camera MacBook Air", "OBSBOT Meet SE StreamCamera", "OBS Virtual Camera"]
UNIQUE_IDS = {
    "OBSBOT Meet SE StreamCamera": "0x11000003564fefe",
    "Camera MacBook Air": "6C707041-05AC-0011-0003-000000000001",
    "OBS Virtual Camera": "7626645E-4425-469E-9D8B-97E0FA59AC75",
}


def wait_for(predicate, timeout=3.0):
    end = time.time() + timeout
    while time.time() < end:
        if predicate():
            return True
        time.sleep(0.02)
    return False


def test_pick_camera_by_name_follows_the_given_order():
    assert C.pick_camera_index(OPENCV_ORDER, C.TOP_KEYWORDS) == 0
    assert C.pick_camera_index(OPENCV_ORDER, C.BUILTIN_KEYWORDS) == 1
    # Cùng tên nhưng danh sách xếp khác: chỉ số đổi theo, nên bắt buộc tìm theo tên (không cố định chỉ số)
    assert C.pick_camera_index(SYSTEM_PROFILER_ORDER, C.TOP_KEYWORDS) == 1
    assert C.pick_camera_index(SYSTEM_PROFILER_ORDER, C.BUILTIN_KEYWORDS) == 0


def test_virtual_cameras_are_never_picked():
    names = ["OBS Virtual Camera", "Camera MacBook Air"]
    assert C.pick_camera_index(names, ("",)) == 1  # "" khớp mọi tên nhưng camera ảo bị bỏ qua
    assert C.pick_camera_index(names, ("obs",)) is None
    assert C.pick_camera_index(["Desk View Camera"], ("",)) is None


def test_exclude_keeps_roles_apart():
    names = ["Camera MacBook Air", "Logitech C920"]
    assert C.pick_camera_index(names, ("",), exclude=C.BUILTIN_KEYWORDS) == 1
    assert C.pick_camera_index(names, ("",), exclude=C.TOP_KEYWORDS) == 0


def test_specs_resolve_roles_from_current_device_list(monkeypatch):
    monkeypatch.setattr(C, "list_camera_names", lambda: (OPENCV_ORDER, "avfoundation"))
    assert C.top_spec().current_source() == 0
    assert C.builtin_spec().current_source() == 1

    # Rút OBSBOT: cam TREN không được chiếm nhầm camera MacBook, cam NGANG vẫn là MacBook
    monkeypatch.setattr(C, "list_camera_names", lambda: (["Camera MacBook Air", "OBS Virtual Camera"], "avfoundation"))
    assert C.top_spec().current_source() is None
    assert C.builtin_spec().current_source() == 0

    # Không có OBSBOT nhưng có webcam ngoài khác: webcam đó làm cam TREN
    monkeypatch.setattr(C, "list_camera_names", lambda: (["Camera MacBook Air", "Logitech C920"], "avfoundation"))
    assert C.top_spec().current_source() == 1
    assert C.builtin_spec().current_source() == 0


def test_parse_camera_arg_kinds(tmp_path, monkeypatch):
    monkeypatch.setattr(C, "phone_ready", lambda: False)
    assert C.parse_camera_arg("auto", "top").label == "OBSBOT"
    assert C.parse_camera_arg("auto", "side").label == "MacBook"  # Không thấy điện thoại thì dùng camera MacBook
    monkeypatch.setattr(C, "phone_ready", lambda: True)
    assert C.parse_camera_arg("auto", "side").kind == "phone"  # adb thấy điện thoại thì ưu tiên điện thoại
    assert C.parse_camera_arg("auto", "side").rotate == C.PHONE_ROTATE
    assert C.parse_camera_arg("phone", "side", rotate=0).rotate is None

    assert C.parse_camera_arg("mac", "top").label == "MacBook"
    assert C.parse_camera_arg("OBSBOT", "side").label == "OBSBOT"
    spec = C.parse_camera_arg("2", "top")
    assert (spec.kind, spec.value) == ("index", 2)
    assert C.parse_camera_arg("rtsp://10.0.0.5/live", "side").kind == "url"
    assert C.parse_camera_arg("logitech", "top").keywords == ("logitech",)

    image = tmp_path / "frame.png"
    cv2.imwrite(str(image), np.zeros((10, 10, 3), np.uint8))
    assert C.parse_camera_arg(str(image), "top").kind == "image"
    (tmp_path / "clip.mp4").write_bytes(b"")
    assert C.parse_camera_arg(str(tmp_path / "clip.mp4"), "top").kind == "file"
    assert C.parse_camera_arg("90", "top", rotate=90).rotate == cv2.ROTATE_90_CLOCKWISE


def test_letterbox_and_inverse_round_trip():
    frame = np.full((1080, 1920, 3), 200, np.uint8)
    box = C.letterbox(frame)
    assert box.shape == (C.VIEW_HEIGHT, C.VIEW_WIDTH, 3)
    assert box[0].max() == 0 and box[240].min() == 200  # Viền đen trên / dưới, hình ở giữa
    # Điểm giữa ảnh gốc rơi vào giữa khung, và đổi ngược lại đúng
    fx, fy = C.letterbox_inverse(320, 240, frame.shape)
    assert abs(fx - 960) < 2 and abs(fy - 540) < 2
    assert C.letterbox_inverse(320, 5, frame.shape) is None  # Viền đen không phải ảnh
    x, y = C.letterbox_inverse(100, 150, frame.shape, 640, 400)
    assert 0 <= x < 1920 and 0 <= y < 1080


def test_camera_stream_reads_a_still_image_with_rotation(tmp_path):
    image = np.zeros((90, 160, 3), np.uint8)
    image[:, :80] = 255
    path = tmp_path / "still.png"
    cv2.imwrite(str(path), image)
    cam = C.CameraStream(C.parse_camera_arg(str(path), "top", rotate=90), "TREN")
    try:
        assert wait_for(lambda: cam.get_raw_frame() is not None)
        assert cam.get_raw_frame().shape[:2] == (160, 90)  # Đã xoay 90 độ
        first = cam.frame_id
        assert wait_for(lambda: cam.frame_id > first)  # Ảnh tĩnh vẫn phát khung mới liên tục
        panel = cam.get_frame()
        assert panel.shape == (C.VIEW_HEIGHT, C.VIEW_WIDTH, 3) and panel.max() > 0
        assert cam.name == "Cam TREN: still.png"
    finally:
        cam.release()


def test_camera_stream_waits_without_crashing_when_device_is_missing(monkeypatch):
    monkeypatch.setattr(C, "list_camera_names", lambda: (["Camera MacBook Air"], "avfoundation"))
    cam = C.CameraStream(C.top_spec(), "TREN")  # Không có OBSBOT
    try:
        time.sleep(0.4)
        assert cam.get_raw_frame() is None and cam.source is None
        waiting = cam.get_frame()  # Khung đen kèm lời nhắc kiểm tra cáp, không phải lỗi
        assert waiting.shape == (C.VIEW_HEIGHT, C.VIEW_WIDTH, 3) and waiting.max() > 0
    finally:
        start = time.time()
        cam.release()
        assert time.time() - start < 2.0  # Tắt nhanh, không treo


def test_camera_list_is_sorted_like_opencv_whatever_order_the_os_reports(monkeypatch):
    """OpenCV đánh chỉ số theo uniqueID nên danh sách phải sắp theo uniqueID dù hệ điều hành xếp camera dùng gần nhất lên đầu."""
    import sys
    import types

    class FakeDevice:
        def __init__(self, name):
            self.name = name

        def localizedName(self):
            return self.name

        def uniqueID(self):
            return UNIQUE_IDS[self.name]

    for os_order in (OPENCV_ORDER, SYSTEM_PROFILER_ORDER, list(reversed(OPENCV_ORDER))):
        fake = types.SimpleNamespace(
            AVMediaTypeVideo="vide",
            AVCaptureDevice=types.SimpleNamespace(devicesWithMediaType_=lambda _t, o=os_order: [FakeDevice(n) for n in o]),
        )
        monkeypatch.setitem(sys.modules, "AVFoundation", fake)
        assert C.list_camera_names() == (OPENCV_ORDER, "avfoundation")


def test_camera_list_falls_back_to_system_profiler_with_the_same_order(monkeypatch):
    import json
    import subprocess
    import sys

    monkeypatch.setitem(sys.modules, "AVFoundation", None)  # Chưa cài PyObjC: import báo lỗi
    cams = [{"_name": n, "spcamera_unique-id": UNIQUE_IDS[n]} for n in SYSTEM_PROFILER_ORDER]
    result = subprocess.CompletedProcess([], 0, stdout=json.dumps({"SPCameraDataType": cams}))
    monkeypatch.setattr(C.subprocess, "run", lambda *a, **k: result)
    assert C.list_camera_names() == (OPENCV_ORDER, "system_profiler")
    monkeypatch.setattr(C.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(OSError("không có system_profiler")))
    assert C.list_camera_names() == ([], "none")
