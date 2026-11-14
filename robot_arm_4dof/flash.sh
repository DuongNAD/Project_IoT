#!/bin/bash
# Biên dịch rồi nạp firmware robot_arm_4dof.ino cho Arduino Uno bằng arduino-cli (có sẵn trong Arduino IDE 2).
#   ./robot_arm_4dof/flash.sh            tự tìm cổng /dev/cu.usbmodem* hoặc /dev/cu.usbserial*
#   ./robot_arm_4dof/flash.sh /dev/cu.usbmodemXXXX
# Nạp xong Arduino sẽ reset: servo giật về góc mặc định (90, 90, 90, 95). Hãy cắt nguồn servo (nguồn tổ ong)
# hoặc đưa cánh tay ra chỗ trống trước khi nạp. Tắt chương trình main.py (đang giữ cổng USB) trước khi nạp.
set -euo pipefail
cd "$(dirname "$0")"

CLI="$(command -v arduino-cli || true)"
if [ -z "$CLI" ]; then
  CLI="/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli"
fi
if [ ! -x "$CLI" ]; then
  echo "Không tìm thấy arduino-cli (cài Arduino IDE 2 hoặc: brew install arduino-cli)" >&2
  exit 1
fi

FQBN="arduino:avr:uno"
echo "Biên dịch firmware cho $FQBN ..."
"$CLI" compile --fqbn "$FQBN" .

PORT="${1:-$(ls /dev/cu.usbmodem* /dev/cu.usbserial* 2>/dev/null | head -n 1 || true)}"
if [ -z "$PORT" ]; then
  echo "Đã biên dịch xong nhưng chưa thấy cổng USB của Arduino. Cắm cáp rồi chạy lại để nạp." >&2
  exit 0
fi

echo "Nạp vào $PORT ..."
"$CLI" upload -p "$PORT" --fqbn "$FQBN" .
echo "Xong. Arduino khởi động lại: đế quay hết sang trái (Home 0°) là firmware mới đã chạy."
