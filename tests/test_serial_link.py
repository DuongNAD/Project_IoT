"""Luồng đọc Serial: lỗi đọc thoáng qua không đóng cổng, mở lại thì mở tay cầm mới trước (DTR không hạ), nhận ra Arduino bị reset."""

import threading
import time

import pytest

import control as g


class FakeSerialError(Exception):
    pass


class FakePort:
    """Một tay cầm Serial giả. Kịch bản: bytes = một dòng đọc được, Exception = ném lỗi, hàm = gọi rồi đọc tiếp; hết kịch bản trả b''."""

    def __init__(self, module, n, script):
        self.module, self.n, self.script, self.closed = module, n, list(script), False

    def readline(self):
        while True:
            if self.closed:
                raise FakeSerialError("port closed")
            if not self.script:
                time.sleep(0.002)
                return b""
            item = self.script.pop(0)
            if isinstance(item, Exception):
                raise item
            if callable(item):
                item()
                continue
            return item

    def write(self, data):
        pass

    def flush(self):
        pass

    def close(self):
        if not self.closed:
            self.closed = True
            self.module.events.append(("close", self.n))


class FakeSerialModule:
    """Thay module pyserial: mỗi lần mở cổng lấy một kịch bản, ghi lại thứ tự mở / đóng. Không bao giờ chạm cổng thật."""

    def __init__(self, *scripts):
        self.scripts = list(scripts)
        self.events = []
        self.opened = 0

    def Serial(self, port, baud, timeout=None):
        n, self.opened = self.opened, self.opened + 1
        self.events.append(("open", n))
        return FakePort(self, n, self.scripts[n] if n < len(self.scripts) else [])


def packet(t, servo=(90, 90, 90, 95), relax=0):
    return f'{{"t":{t},"servo":{list(servo)},"relax":{relax}}}\n'.encode()


def wait_for(predicate, timeout=3.0):
    end = time.time() + timeout
    while time.time() < end:
        if predicate():
            return True
        time.sleep(0.005)
    return False


@pytest.fixture
def run_link(monkeypatch):
    started = []

    def run(fake, port_exists=lambda: True, find_port=lambda: "FAKE-PORT"):
        monkeypatch.setattr(g, "serial", fake)
        link = g.ArduinoSerialLink(enabled=False)  # enabled=False: không tự chạy luồng, nên chưa mở gì
        link.READ_RETRY_S, link.PORT_WAIT_S = 0.003, 0.01
        link._find_port, link._port_exists = find_port, port_exists
        thread = threading.Thread(target=link._loop, daemon=True)
        thread.start()
        started.append((link, thread))
        return link

    yield run
    for link, thread in started:
        link.running = False
        thread.join(timeout=2)
        link.release()


def test_a_transient_read_error_does_not_close_the_port(run_link):
    fake = FakeSerialModule([packet(1000), FakeSerialError("multiple access on port?"), FakeSerialError("again"), packet(1200, (95, 90, 90, 95))])
    link = run_link(fake)
    assert wait_for(lambda: link.get_state()[0] == [95, 90, 90, 95])
    assert fake.events == [("open", 0)]  # Không đóng, không mở lại: đường DTR không đổi nên Arduino không reset
    assert link.get_state()[1] and link.get_reset_count() == 0


def test_reopening_after_persistent_errors_opens_the_new_handle_before_closing_the_old(run_link):
    broken = [packet(5000)] + [FakeSerialError("device reports readiness to read but returned no data")] * g.ArduinoSerialLink.READ_ERRORS_BEFORE_REOPEN
    fake = FakeSerialModule(broken, [packet(5200, (100, 90, 90, 95))])
    link = run_link(fake)
    assert wait_for(lambda: link.get_state()[0] == [100, 90, 90, 95])
    # Tay cầm mới được mở khi tay cầm cũ còn mở: DTR không bao giờ hạ xuống nên Arduino không bị reset (đóng trước rồi mở lại thì reset)
    assert fake.events == [("open", 0), ("open", 1), ("close", 0)]
    assert link.get_reset_count() == 0


def test_unplugged_arduino_is_reconnected_when_it_comes_back(run_link):
    plugged = [True]
    fake = FakeSerialModule([packet(8000), lambda: plugged.__setitem__(0, False), FakeSerialError("device disconnected")], [packet(300)])
    link = run_link(fake, port_exists=lambda: plugged[0], find_port=lambda: "FAKE-PORT" if plugged[0] else None)
    assert wait_for(lambda: not link.get_state()[1])  # Rút cáp: báo mất kết nối ngay, không thử đọc lại 5 lần
    assert fake.events == [("open", 0), ("close", 0)]
    plugged[0] = True  # Cắm lại: Arduino khởi động lại nên thời gian chạy bắt đầu từ đầu
    assert wait_for(lambda: link.get_state()[1] and link.get_reset_count() == 1)
    assert fake.events == [("open", 0), ("close", 0), ("open", 1)]


def test_reset_is_detected_when_the_firmware_uptime_goes_backwards():
    link = g.ArduinoSerialLink(enabled=False)
    link._parse_line(packet(60000).decode())  # Gói đầu tiên chưa có mốc so sánh nên không tính là reset dù t lớn
    link._parse_line(packet(61000).decode())
    assert link.get_reset_count() == 0
    link._parse_line(packet(800).decode())  # Thời gian chạy tụt về gần 0
    assert link.get_reset_count() == 1
    link._parse_line(packet(1000).decode())
    link._parse_line('{"servo":[90,90,90,95]}')  # Firmware không gửi "t": bỏ qua
    assert link.get_reset_count() == 1
    link._parse_line(packet(70000).decode())
    link._parse_line(packet(69000).decode())  # Tụt dưới ngưỡng 1.5 giây: không phải reset
    assert link.get_reset_count() == 1


def test_firmware_banner_is_echoed_so_the_log_shows_which_sketch_is_running(capsys):
    link = g.ArduinoSerialLink(enabled=False)
    link.servo = [100, 80, 70, 120]
    link._parse_line("Robot Arm Ready! WASD + IK + JL + X (nghi kep) + Z (nghi het)\r\n")
    assert "Z (nghi het)" in capsys.readouterr().out
    assert link.get_state()[0] == [90, 90, 90, 95]  # Arduino vừa khởi động nên về góc mặc định
    link._parse_line("Phím bấm: w")  # Dòng khác không được in lại
    assert capsys.readouterr().out == ""


def test_arm_relaxed_flag_follows_the_firmware_json_and_the_simulated_keys():
    link = g.ArduinoSerialLink(enabled=False)
    assert not link.get_arm_relaxed() and not link.firmware_has_arm_relax
    link._parse_line('{"t":1,"servo":[90,90,90,95],"relax":0}')  # Firmware chưa có phím z: JSON không có "armrelax"
    assert not link.get_arm_relaxed() and not link.firmware_has_arm_relax
    link._parse_line('{"t":2,"servo":[90,90,90,95],"relax":1,"armrelax":1}')
    assert link.get_arm_relaxed() and link.firmware_has_arm_relax
    link._parse_line('{"t":3,"servo":[95,90,90,95],"relax":0,"armrelax":0}')
    assert not link.get_arm_relaxed() and link.firmware_has_arm_relax

    sim = g.ArduinoSerialLink(enabled=False)  # Chế độ mô phỏng đúng như firmware có phím z
    sim.apply_key_locally("z")
    assert sim.get_arm_relaxed() and sim.relaxed
    for key in "lxjz":  # Phím kẹp, x và z không cấp lại xung cho cánh tay đang nghỉ
        sim.apply_key_locally(key)
        assert sim.get_arm_relaxed(), key
    for key in "adwsikh":  # Phím di chuyển đế / vai / khuỷu (và h) cấp xung lại
        sim.apply_key_locally("z")
        sim.apply_key_locally(key)
        assert not sim.get_arm_relaxed(), key


def fake_port_info(device, description, manufacturer=None, vid=0x2341):
    import types

    return types.SimpleNamespace(device=device, description=description, manufacturer=manufacturer, vid=vid)


def test_windows_arduino_port_is_found_among_com_ports(monkeypatch):
    import serial.tools.list_ports as list_ports

    ports = [
        fake_port_info("COM3", "Standard Serial over Bluetooth link (COM3)", "Microsoft"),  # Cổng Bluetooth ảo: bỏ
        fake_port_info("COM4", "Samsung Mobile USB Modem", "SAMSUNG"),  # Điện thoại cắm USB: bỏ
        fake_port_info("COM1", "Communications Port (COM1)", vid=None),  # Không phải USB: bỏ
        fake_port_info("COM9", "USB Composite Device"),
        fake_port_info("COM7", "USB-SERIAL CH340 (COM7)", "wch.cn"),
    ]
    monkeypatch.setattr(g.glob, "glob", lambda pattern: [])  # Không có /dev/cu.usbmodem* như trên macOS
    monkeypatch.setattr(list_ports, "comports", lambda: ports)
    assert g.find_arduino_port() == "COM7"  # Cổng có tên CH340 được ưu tiên
    monkeypatch.setattr(list_ports, "comports", lambda: ports[:4])
    assert g.find_arduino_port() == "COM9"  # Không có tên quen thì lấy cổng USB còn lại
    monkeypatch.setattr(list_ports, "comports", lambda: ports[:3])
    assert g.find_arduino_port() is None


def test_macos_port_still_comes_from_dev_cu(monkeypatch):
    monkeypatch.setattr(g.glob, "glob", lambda pattern: ["/dev/cu.usbmodem1101"] if "usbmodem" in pattern else [])
    assert g.find_arduino_port() == "/dev/cu.usbmodem1101"


def test_com_port_existence_is_checked_against_the_port_list(monkeypatch):
    """COMx không phải đường dẫn tệp: nếu hỏi os.path.exists thì lỗi đọc thoáng qua nào cũng mở lại cổng và Arduino bị reset."""
    import serial.tools.list_ports as list_ports

    link = g.ArduinoSerialLink(enabled=False)
    link.port = "COM7"
    monkeypatch.setattr(list_ports, "comports", lambda: [fake_port_info("COM7", "USB-SERIAL CH340")])
    assert link._port_exists()
    monkeypatch.setattr(list_ports, "comports", lambda: [])
    assert not link._port_exists()  # Rút cáp
