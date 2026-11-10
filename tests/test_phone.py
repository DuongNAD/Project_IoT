"""Trang web cho điện thoại: đúng mã mới vào được, trạng thái và ảnh lấy từ main.py, phím bấm đi vào hàng đợi."""

import json
import urllib.error
import urllib.request

import cv2
import numpy as np
import pytest

import phone as P
import success as S
from test_success import make_plan


@pytest.fixture
def server():
    s = P.PhoneServer(port=0, host="127.0.0.1", pin="123456")  # Cổng 0: hệ điều hành chọn cổng trống
    yield s
    s.close()


def call(server, path, method="GET"):
    req = urllib.request.Request(f"http://127.0.0.1:{server.port}{path}", method=method, data=b"" if method == "POST" else None)
    try:
        with urllib.request.urlopen(req, timeout=3) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def test_only_the_link_with_the_right_code_opens_the_page(server):
    status, body = call(server, "/123456/")
    assert status == 200 and "Cánh tay robot" in body.decode("utf-8")
    for path in ("/", "/000000/", "/123456x/", "/favicon.ico"):
        assert call(server, path)[0] == 404, path
    assert call(server, "/000000/key/d", "POST")[0] == 404  # Sai mã thì không bấm được phím
    assert server.pop_keys() == []
    assert server.url("10.0.0.5") == f"http://10.0.0.5:{server.port}/123456/"


def test_state_and_screen_come_from_the_main_loop(server):
    assert call(server, "/123456/screen.jpg")[0] == 503  # main.py chưa dựng khung nào
    plan = make_plan([90, 90, 90, 95], [74, 60, 86, 95])
    screen = np.full((90, 160, 3), 128, np.uint8)
    server.update(P.status_of(plan, S.check(plan)), screen)
    status, body = call(server, "/123456/state")
    st = json.loads(body)
    assert status == 200 and st["state"] == "moving" and st["key"] == "d" and st["steps"] == 8
    assert [s["joint"] for s in st["servo"]] == ["base", "shoulder", "elbow"] and st["grip"] == 95
    status, jpg = call(server, "/123456/screen.jpg")
    assert status == 200 and cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR).shape == (90, 160, 3)


def test_phone_keys_are_queued_in_order_and_only_servo_keys_are_accepted(server):
    for k in "dds":
        assert call(server, f"/123456/key/{k}", "POST")[0] == 204
    for bad in ("q", "dd", "", "%23"):
        assert call(server, f"/123456/key/{bad}", "POST")[0] == 404, bad
    assert server.pop_keys() == ["d", "d", "s"]
    assert server.pop_keys() == []
    assert call(server, "/123456/key/r", "POST")[0] == 204  # R (chốt đích) từ máy Dell, Mac tự xử lý
    assert server.pop_keys() == ["r"]


def test_status_for_done_and_waiting_states():
    done_plan = make_plan([74, 60, 86, 95], [74, 60, 86, 95])
    st = P.status_of(done_plan, S.check(done_plan))
    assert st["done"] and st["key"] is None and all(s["ok"] for s in st["servo"])
    far = make_plan([90, 90, 90, 95], [74, 60, 86, 95], reachable=False, move_closer_mm=42.4)
    st = P.status_of(far, S.check(far))
    assert st["state"] == "unreachable" and st["key"] is None and st["closer_mm"] == 42
    assert "\x1b[40m" in P.qr_text("http://10.0.0.5:8000/123456/")


def test_headless_runs_do_not_open_a_phone_server():
    import main as M

    args = M.parse_args(["--headless", "--no-serial"])
    assert args.phone_port == 8000 and not args.no_phone
    assert M.parse_args(["--no-phone", "--phone-port", "9000"]).phone_port == 9000


def test_the_link_code_stays_the_same_between_runs(tmp_path):
    path = tmp_path / ".phone_pin"
    first = P.stored_pin(str(path))
    assert len(first) == 6 and first.isdigit() and path.read_text().strip() == first
    assert P.stored_pin(str(path)) == first  # Lần chạy sau dùng lại đúng mã, máy Dell khỏi đổi lệnh
    path.write_text("abc\n")  # Tệp hỏng: tạo mã mới
    again = P.stored_pin(str(path))
    assert again.isdigit() and len(again) == 6 and path.read_text().strip() == again
    assert len(P.stored_pin(str(tmp_path / "no_dir" / "pin"))) == 6  # Không ghi được tệp vẫn có mã cho lần chạy này
