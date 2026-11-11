"""App máy Dell: H / Z phải bấm 2 lần, gửi phím qua Bluetooth HC-05, lấy ảnh màn hình Mac qua Wi-Fi, R chỉ nhắc bấm trên Mac."""

import types

import numpy as np
import pytest

import remote as R
import share as SH


def test_home_and_relax_all_need_a_second_press_within_two_seconds():
    gate = R.KeyGate()
    assert gate.press("D", now=0.0) == ("d", "")
    assert gate.press("q", now=0.0) == (None, "")  # Không phải phím servo
    assert gate.press("r", now=0.0) == (None, "")  # R bấm trên Mac, không gửi qua Bluetooth
    send, msg = gate.press("z", now=1.0)
    assert send is None and "Z LAN NUA" in msg
    assert gate.press("z", now=2.5) == ("z", "")
    gate.press("h", now=10.0)
    assert gate.press("h", now=12.5)[0] is None  # Quá 2 giây: lần này lại thành lần bấm thứ nhất
    assert gate.press("h", now=13.0) == ("h", "")
    gate.press("h", now=20.0)
    gate.press("a", now=20.5)  # Bấm phím khác thì hủy lời hỏi
    assert gate.press("h", now=21.0)[0] is None


class FakeSerial:
    def __init__(self, fail_write=False):
        self.written, self.fail_write, self.closed = [], fail_write, False

    def write(self, data):
        if self.fail_write:
            raise OSError("link lost")
        self.written.append(data)

    def flush(self):
        pass

    def close(self):
        self.closed = True


def fake_module(handle=None, error=None):
    opened = []

    def Serial(port, baud, timeout=None, write_timeout=None):
        if error:
            raise error
        opened.append((port, baud))
        return handle

    return types.SimpleNamespace(Serial=Serial, opened=opened)


def test_keys_go_out_over_bluetooth_and_a_lost_link_is_reported():
    handle = FakeSerial()
    module = fake_module(handle)
    bt = R.BluetoothLink("COM5", serial_module=module, start=False)
    assert not bt.send("d")  # Chưa nối: không gửi được, app báo CHUA GUI
    assert bt.open_once() and bt.connected and module.opened == [("COM5", 9600)] and "COM5 da noi" in bt.state
    assert bt.send("d") and handle.written == [b"d"]
    handle.fail_write = True
    assert not bt.send("w") and not bt.connected and "rot ket noi" in bt.state and handle.closed
    bt.close()


def test_an_unreachable_hc05_is_explained():
    bt = R.BluetoothLink("COM5", serial_module=fake_module(error=OSError("timeout")), start=False)
    assert not bt.open_once() and "khong noi duoc COM5" in bt.state


@pytest.fixture
def mac():
    server = SH.ScreenServer(port=0, host="127.0.0.1")
    yield server
    server.close()


def test_the_mac_screen_comes_over_wifi(mac):
    view = R.MacView(f"http://127.0.0.1:{mac.port}", start=False)
    assert not view.fetch_once() and view.error == "Mac chua co anh" and not view.ok
    mac.update(np.full((72, 128, 3), 200, np.uint8))
    assert view.fetch_once() and view.ok and view.frame.shape == (72, 128, 3)
    gone = R.MacView("http://127.0.0.1:9/", start=False)
    assert not gone.fetch_once(timeout=0.5) and "khong thay Mac" in gone.error


def test_window_shows_a_status_bar_above_the_mac_screen():
    screen = np.full((650, 1280, 3), 90, np.uint8)
    img = R.compose(screen, "MAC (Wi-Fi): da noi", True, "BLUETOOTH: COM5 da noi", True, "DA GUI D", R.GREEN)
    assert img.shape == (R.BAR_H + 650, 1280, 3)
    assert (img[R.BAR_H:] == screen).all()  # Ảnh của Mac giữ nguyên
    stale = R.compose(screen, "MAC (Wi-Fi): mat ket noi", False, "BLUETOOTH: ...", False)
    assert tuple(stale[R.BAR_H + 2, 2]) == R.RED  # Ảnh cũ: viền đỏ
    waiting = R.compose(None, "MAC (Wi-Fi): dang noi...", False, "BLUETOOTH: dang noi COM5...", False)
    assert waiting.shape == (R.BAR_H + 650, 1280, 3)


def test_the_mac_link_and_the_com_port_are_required():
    with pytest.raises(SystemExit):
        R.parse_args([])
    with pytest.raises(SystemExit):
        R.parse_args(["--mac", "http://192.168.1.5:8000/"])  # Thiếu --port: không còn tự tìm cổng
    args = R.parse_args(["--mac", "http://192.168.1.5:8000/", "--port", "COM5"])
    assert (args.mac, args.port, args.baud) == ("http://192.168.1.5:8000/", "COM5", 9600)
