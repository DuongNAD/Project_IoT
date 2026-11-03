"""Cấu hình chung cho test: không bao giờ chạm vào camera, cổng Serial hay calibration.json thật của người dùng."""

import copy

import cv2
import pytest

import calibration
import control


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    """File hiệu chỉnh trỏ vào thư mục tạm; ARM_CONFIG được khôi phục sau mỗi test."""
    monkeypatch.setattr(calibration, "CALIBRATION_PATH", str(tmp_path / "calibration.json"))
    saved = copy.deepcopy(control.ARM_CONFIG)
    yield
    control.ARM_CONFIG.clear()
    control.ARM_CONFIG.update(saved)


@pytest.fixture
def ctl():
    """Nhóm điều khiển ở chế độ mô phỏng (serial_enabled=False nên không bao giờ mở cổng Arduino thật)."""
    c = control.Control(serial_enabled=False)
    yield c
    c.release()


@pytest.fixture(autouse=True)
def no_real_cameras(monkeypatch):
    """Không test nào được mở camera thật: cv2.VideoCapture bị thay bằng bẫy (test cần camera giả thì tự patch lại)."""
    opened = []

    class TrapCapture:
        def __init__(self, source, *args):
            opened.append(source)

        def set(self, *args):
            return True

        def isOpened(self):
            return False

        def read(self):
            return False, None

        def get(self, *args):
            return 0.0

        def release(self):
            pass

    monkeypatch.setattr(cv2, "VideoCapture", TrapCapture)
    yield
    assert not opened, f"Test đã mở camera thật qua cv2.VideoCapture: {opened}"
