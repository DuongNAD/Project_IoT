"""Chia sẻ màn hình Mac qua Wi-Fi: chỉ có /screen.jpg, ảnh lấy từ vòng lặp main.py, không nhận lệnh nào."""

import urllib.error
import urllib.request

import cv2
import numpy as np
import pytest

import share as SH
from test_main import scene_files  # noqa: F401 (fixture: cảnh giả lập 2 camera)


@pytest.fixture
def server():
    s = SH.ScreenServer(port=0, host="127.0.0.1")  # Cổng 0: hệ điều hành chọn cổng trống
    yield s
    s.close()


def call(server, path, method="GET"):
    req = urllib.request.Request(f"http://127.0.0.1:{server.port}{path}", method=method, data=b"" if method == "POST" else None)
    try:
        with urllib.request.urlopen(req, timeout=3) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def test_the_screen_comes_from_the_main_loop(server):
    assert call(server, "/screen.jpg")[0] == 503  # main.py chưa dựng khung nào
    server.update(np.full((90, 160, 3), 128, np.uint8))
    status, jpg = call(server, "/screen.jpg")
    assert status == 200 and cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR).shape == (90, 160, 3)
    assert server.url("10.0.0.5") == f"http://10.0.0.5:{server.port}/"


def test_only_the_screen_is_served_and_no_command_is_accepted(server):
    server.update(np.zeros((90, 160, 3), np.uint8))
    for path in ("/", "/state", "/key/d", "/favicon.ico"):
        assert call(server, path)[0] == 404, path
    assert call(server, "/key/d", "POST")[0] == 501  # Không có POST: Dell gửi phím qua Bluetooth, không qua Mac


def test_a_busy_port_does_not_stop_the_program(monkeypatch, capsys):
    def busy(*args, **kwargs):
        raise OSError("Address already in use")

    monkeypatch.setattr(SH, "ScreenServer", busy)
    assert SH.start(8000) is None  # main.py vẫn chạy, chỉ máy Dell không xem được
    assert "Không chia sẻ được" in capsys.readouterr().out


def test_the_window_loop_shares_its_screen_and_stops_sharing_on_exit(scene_files, monkeypatch):
    from test_main import make_app

    monkeypatch.setattr(SH, "lan_ip", lambda: "127.0.0.1")
    started, real_start = [], SH.start
    monkeypatch.setattr(SH, "start", lambda: started.append(real_start(0)) or started[-1])
    for name in ("namedWindow", "setMouseCallback", "imshow"):
        monkeypatch.setattr(cv2, name, lambda *args, **kwargs: None)
    fetched = []

    def wait_key(ms):  # Lần đầu: Dell lấy ảnh màn hình; lần sau: bấm Q để thoát
        if not fetched:
            fetched.append(call(started[0], "/screen.jpg"))
            return 255
        return ord("q")

    monkeypatch.setattr(cv2, "waitKey", wait_key)
    app = make_app(scene_files)
    try:
        app.run()
    finally:
        app.close()
    status, jpg = fetched[0]
    assert status == 200 and cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR).shape[:2] == (650, 1280)
    with pytest.raises(OSError):  # Thoát chương trình thì máy chủ cũng tắt
        urllib.request.urlopen(f"http://127.0.0.1:{started[0].port}/screen.jpg", timeout=1)


def test_start_prints_the_command_for_the_dell(monkeypatch, capsys):
    monkeypatch.setattr(SH, "lan_ip", lambda: "192.168.1.5")
    server = SH.start(0)
    try:
        assert f"python remote.py --mac http://192.168.1.5:{server.port}/ --port COMx" in capsys.readouterr().out
    finally:
        server.close()
