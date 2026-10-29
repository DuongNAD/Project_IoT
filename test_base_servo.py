#!/usr/bin/env python3
"""
Script kiểm tra & điều khiển Servo Đế (Base Servo - Channel 0) của cánh tay robot.
Tự động nhận diện baud rate (9600 của firmware hiện tại hoặc 115200 của Robot_Arm_4DOF_Controller).
"""

import sys
import time
import glob
import serial

DEFAULT_PORT = "/dev/cu.usbmodemFX2348N1"

def find_port():
    ports = glob.glob("/dev/cu.usbmodem*") + glob.glob("/dev/cu.usbserial*")
    if DEFAULT_PORT in ports:
        return DEFAULT_PORT
    if ports:
        return ports[0]
    return DEFAULT_PORT

def detect_firmware(port):
    """Thử kết nối ở 9600 và 115200 để xác định giao thức firmware đang nạp."""
    for baud in [9600, 115200]:
        try:
            ser = serial.Serial(port, baud, timeout=1.0)
            ser.dtr = False
            time.sleep(0.1)
            ser.dtr = True
            time.sleep(2.2)
            banner = ser.read_all().decode("utf-8", errors="ignore").strip()
            
            # Kiểm tra xem có phản hồi text không
            if "Robot Arm Ready" in banner:
                return ser, baud, "legacy_wasd"
            if "PCA9685" in banner or "STAT:" in banner:
                return ser, baud, "new_protocol"
            
            # Thử gửi PING để kiểm tra new protocol
            ser.write(b"PING\n")
            ser.flush()
            time.sleep(0.3)
            resp = ser.read_all().decode("utf-8", errors="ignore").strip()
            if "PONG" in resp or "STAT:" in resp:
                return ser, baud, "new_protocol"
            
            ser.close()
        except Exception:
            pass

    # Mặc định kết nối 9600 baud
    ser = serial.Serial(port, 9600, timeout=1.0)
    ser.dtr = False
    time.sleep(0.1)
    ser.dtr = True
    time.sleep(2.0)
    return ser, 9600, "legacy_wasd"

def test_sweep_base(ser, mode):
    print("\n" + "=" * 50)
    print("🤖 BẮT ĐẦU QUY TRÌNH TEST SERVO ĐẾ (BASE SERVO)")
    print("=" * 50)

    if mode == "legacy_wasd":
        print("📌 Chế độ: Firmware WASD (9600 baud)")
        print("1. Quay Đế sang TRÁI (+15°)...")
        for _ in range(3):
            ser.write(b"a")
            ser.flush()
            time.sleep(0.25)
        time.sleep(1.0)

        print("2. Quay Đế sang PHẢI (-30°)...")
        for _ in range(6):
            ser.write(b"d")
            ser.flush()
            time.sleep(0.25)
        time.sleep(1.0)

        print("3. Đưa Đế về vị trí TRUNG TÂM ban đầu 90° (+15°)...")
        for _ in range(3):
            ser.write(b"a")
            ser.flush()
            time.sleep(0.25)
        time.sleep(0.5)

    else:
        print("📌 Chế độ: Firmware New Protocol (115200 baud)")
        print("1. Đặt Đế về 90°...")
        ser.write(b"B:90\n")
        ser.flush()
        time.sleep(1.0)

        print("2. Quay Đế sang 115°...")
        ser.write(b"B:115\n")
        ser.flush()
        time.sleep(1.0)

        print("3. Quay Đế sang 65°...")
        ser.write(b"B:65\n")
        ser.flush()
        time.sleep(1.0)

        print("4. Trả về vị trí trung tâm 90°...")
        ser.write(b"B:90\n")
        ser.flush()
        time.sleep(1.0)

    print("=" * 50)
    print("✅ ĐÃ GỬI LỆNH TEST THÀNH CÔNG!")
    print("LƯU Ý: Nếu servo chưa nhúc nhích, hãy kiểm tra công tắc nguồn tổ ong (5V-6V)")
    print("cấp vào cổng Terminal màu xanh của mạch PCA9685.")
    print("=" * 50 + "\n")

if __name__ == "__main__":
    port = find_port()
    print(f"🔌 Đang mở cổng {port}...")
    try:
        ser, baud, mode = detect_firmware(port)
        print(f"✅ Đã kết nối thành công: {port} @ {baud} baud ({mode})")
        test_sweep_base(ser, mode)
        ser.close()
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        sys.exit(1)
