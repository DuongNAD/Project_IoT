# Project IoT: cánh tay robot 4 servo, 2 camera chỉ cho bạn BẤM PHÍM GÌ

Hệ thống nhìn tờ giấy A4 bằng **2 camera**, tìm vật có màu trên giấy rồi tính xem 3 servo (đế, vai, khuỷu) phải quay tới góc nào để
đầu kẹp tới vật. Màn hình chỉ nói **một việc**: *bấm phím nào, mấy lần, sang trái / phải bao nhiêu độ*, và báo **XONG** khi 3 servo đã tới góc đúng.

```
 camera TREN + NGANG ──► vision.py ──► vật nằm ở (x, y) cm
                                            │
                        ┌───────────────────▼───────────────────┐        ┌────────────────────────────────┐
                        │  KHỐI ĐIỀU KHIỂN       (control.py)   │  Plan  │  KHỐI SUCCESS      (success.py)│
                        │  vật ở đâu -> góc servo cần tới       │ ─────► │  3 servo tới góc đó chưa?      │
                        │  -> bấm phím gì, mấy lần; USB Arduino │        │  -> XONG / còn N lần bấm       │
                        └───────────────────────────────────────┘        └───────────────┬────────────────┘
                                                                                         │ Result
                                              màn hình (screen.py): 2 camera + phần 1 + phần 2 ◄──────────┘
```

Hai khối chỉ nói chuyện với nhau qua **một đối tượng `Plan`**, nên làm riêng được:

| | Khối ĐIỀU KHIỂN (`control.py`) | Khối SUCCESS (`success.py`) |
|---|---|---|
| Việc | tính góc servo cần tới (IK), lập lệnh bấm phím, gửi phím qua USB | kết luận "đã tới chưa", đếm số lần thành công |
| Đầu vào | các vật camera thấy + góc servo đã ra lệnh mà Arduino báo về | `Plan` của khối điều khiển |
| Đầu ra | `Plan`: góc hiện tại, góc cần tới, 3 `Move` (phím, số lần, hướng, độ) | `Result`: `done`, từng servo đúng chưa, còn bao nhiêu lần bấm, `count` |
| Không biết gì về | thế nào là "xong" | cách tính góc, camera, USB |

**Thành công** = cả 3 servo lệch không quá **1 bước bấm (2°)** so với góc gợi ý, giữ đúng liên tục **1 giây** thì đếm thêm 1 lần.
Kẹp không tính (nó chỉ cần đầu kẹp tới đúng chỗ của vật).

## 1. Phần cứng

| Thành phần | Ghi chú |
|---|---|
| Arduino Uno + PCA9685 (I2C 0x40) | kênh 0 = đế, 1 = vai, 2 = khuỷu, 3 = kẹp; HC-05 Bluetooth ở D2 / D3: nhận phím từ máy Dell (điều khiển từ xa, mục 2) |
| 4 servo MG996R | nguồn riêng 5-6 V (nguồn tổ ong) cấp vào cổng xanh của PCA9685, **không** lấy từ cổng USB |
| Cam TREN | OBSBOT Meet SE treo phía trên tờ giấy, nhìn xuống |
| Cam NGANG | camera tích hợp của MacBook đặt thấp trước tờ giấy |
| Tờ giấy | in `aruco_A4_clean.pdf` **đúng 100% kích thước** (đo cạnh 1 mã ArUco phải đúng **2,8 cm**): 4 mã `DICT_4X4_50` (bộ mã có sẵn của OpenCV), ID 0-3, sát 4 góc |

## 2. Cài đặt và chạy

```bash
uv sync                      # cài OpenCV, pyserial
./robot_arm_4dof/flash.sh    # biên dịch + nạp firmware (cần Arduino IDE 2, xem mục 6)
uv run python main.py --port /dev/cu.usbmodem1101    # cổng USB của Arduino (Windows: --port COM3)
```

- **Cổng Arduino** ghi tay: macOS gõ `ls /dev/cu.usbmodem*`; Windows xem Device Manager → Ports (COM & LPT). Không ghi `--port` thì chương trình **mô phỏng**
  (không gửi phím xuống robot, góc servo tự cộng / trừ như firmware).
- **Camera** chọn bằng chỉ số OpenCV: mặc định `--top 0` (cam TREN) và `--side 1` (cam NGANG). Nhìn hai khung hình: thấy đảo thì chạy lại với `--top 1 --side 0`
  (macOS có thể đổi thứ tự camera giữa các lần chạy).
- macOS hỏi quyền **Camera** lần đầu cho ứng dụng đang chạy lệnh (Terminal, PyCharm...): bấm OK.

Một cửa sổ: 2 camera ở trên, bên dưới **phần 1 (điều khiển)** → **phần 2 (success)**. Bấm phím trên cửa sổ video:

| Phím | Tác dụng |
|---|---|
| `A` / `D` | xoay đế sang **trái** / **phải**, mỗi lần **2°** |
| `W` / `S` | nâng / hạ vai, mỗi lần 2° |
| `I` / `K` | khuỷu lên / xuống, mỗi lần 2° |
| `J` / `L` | mở / khép kẹp, mỗi lần 5° (không tính vào thành công) |
| `H` | đưa cả 4 servo về Home (0/90/90/95): đế quay hết sang **phải** để cánh tay không che vật ở cam TREN |
| `R` | **chụp đích**: lấy vật gần đế nhất trong ảnh lúc bấm, tính góc cần tới **một lần** (không theo camera nữa, tay kẹp che hay đẩy lệch vật cũng không đổi đích); vật bị dời thì bấm `R` lại. Chưa bấm `R` thì chưa có lệnh |
| `U` | quên vị trí 4 mã ArUco đã nhớ (sau khi dời camera hoặc tờ giấy) |
| `Q` | thoát |

### Điều khiển từ xa: máy Dell cách ~2 m (xem qua Wi-Fi, bấm phím qua Bluetooth)

```
                 USB: góc servo + nguồn
   MAC (main.py) ─────────────────────── UNO ── HC-05
   2 camera, vision, control, success              ▲
     │                                             │ Bluetooth: phím a d w s i k j l h
     └── Wi-Fi: ảnh màn hình (2 cam + lệnh + XONG) ──►  DELL (remote.py)
```

- **Mac** đặt cạnh cánh tay, **cắm USB vào Arduino** và làm toàn bộ phần tính: camera, vision, control, success. Sau mỗi phím Arduino báo góc servo
  về Mac qua USB. Khi mở cửa sổ, `main.py` tự chia sẻ ảnh màn hình qua Wi-Fi (`share.py`, chỉ cho xem, không nhận lệnh) và in ra lệnh cho máy Dell.
  Phím `R` (chụp đích) bấm trên bàn phím Mac.
- **Dell** chạy `remote.py`: cửa sổ hiện màn hình của Mac; gõ `A D W S I K J L H` thì phím đi qua Bluetooth tới HC-05 rồi Arduino.
  `H` (Home) phải bấm 2 lần trong 2 giây. Dòng trên cùng nhắc phím vừa gửi; không mở được cổng Bluetooth thì `remote.py` dừng và báo lỗi; `Q` thoát.

Chuẩn bị:
1. Dell: ghép đôi HC-05 trong cài đặt Bluetooth (PIN thường là `1234` hoặc `0000`). Số cổng: Settings > Bluetooth & devices > Devices >
   More Bluetooth settings > tab COM Ports, dòng **Outgoing** tên HC-05. Chỉ ghép đôi HC-05 với Dell: HC-05 nhận một kết nối mỗi lúc.
2. Mac và Dell vào **cùng một Wi-Fi** (mạng trường chặn hai máy thấy nhau thì cả hai bắt điểm phát Wi-Fi của điện thoại).
3. Mac: cắm USB Arduino, `uv run python main.py --port /dev/cu.usbmodem…` (macOS hỏi cho Python nhận kết nối mạng thì bấm Cho phép), chép dòng
   `python remote.py --mac http://<ip Mac>:8000/ --port COMx` nó in ra.
4. Dell: chạy dòng đó, thay `COMx` bằng cổng HC-05 ở bước 1.

## 3. Code chia thế nào

| Tệp | Vai trò |
|---|---|
| `main.py` | nối các phần: camera → vision → control → success → màn hình; phím, tham số dòng lệnh |
| `control.py` | **Khối điều khiển**: hình học cánh tay (FK / IK), cổng USB Arduino, phím R chụp đích, `Plan` + `Move` |
| `success.py` | **Khối success**: `check(plan)` → `Result`; `Success` đếm số lần thành công |
| `screen.py` | vẽ màn hình: 2 camera + phần 1 + phần 2 nối nhau |
| `vision.py` | dò tờ A4 qua ArUco (hàm có sẵn của OpenCV, homography pixel ↔ cm), tìm vật có màu, bù thị sai theo độ cao vật |
| `cameras.py` | mở camera theo chỉ số (hoặc ảnh để chạy thử), vòng lặp chính đọc thẳng từng khung; rút cáp camera thì chạy lại chương trình |
| `calibration.py` | nạp hiệu chỉnh từ `calibration.json` |
| `share.py` | chia sẻ ảnh màn hình của Mac qua Wi-Fi cho máy Dell (`/screen.jpg`, chỉ cho xem) |
| `remote.py` | app máy Dell: xem màn hình Mac qua Wi-Fi, gửi phím qua Bluetooth HC-05 (chép riêng tệp này sang Dell cũng chạy) |
| `robot_arm_4dof/` | firmware Arduino và `flash.sh` |
| `hoc_phan2/` | hướng dẫn đọc code và slide cho hai người trình bày phần 2 (computer vision, hỗ trợ gắp) |

Mỗi khung hình trong `main.py` chỉ là ba dòng: `plan = control.update(vision.objects)` → `result = success.update(plan)` → `build_screen(..., plan, result)`.

## 4. Tờ giấy, đế robot và hiệu chỉnh

Hệ tọa độ gắn với **tờ giấy** (không phụ thuộc camera nào nhìn): gốc ở góc ngoài mã **ID 0**, trục **X** chạy ID 0 → ID 1 (29.7 cm), trục **Y**
chạy ID 0 → ID 3 (21.0 cm). Lưới tự dò từ các mã ArUco thật; cánh tay che mất 1-2 mã thì dùng vị trí đã nhớ.

- **Hiệu chỉnh** nằm trong `calibration.json` (không đưa lên git), sửa tay được:
  `base` (vị trí trục xoay đế trên tờ giấy, cm, và hướng robot nhìn), `arm` (hai góc chuẩn vai / khuỷu khi servo ở 90°), `claw` (càng kẹp gắn cứng vào khâu
  khuỷu nên độ lệch của điểm kẹp được dồn vào chiều dài khâu 3). Ví dụ ở docstring `calibration.py`.
- **Đế robot**: dời robot thì **đo bằng thước** vị trí trục xoay đế theo hệ tọa độ tờ giấy rồi sửa mục `base`. Không có `calibration.json` thì dùng mặc định
  (14.85, -7.5) cm, nhìn vào +Y.
- **Hình học cánh tay thật khác mô hình mặc định**: từ 10 lần "ôm" cốc bằng tay (2026-11-02), khớp 5 thông số bằng bình phương tối thiểu, sai số RMS còn
  ~0,85 cm (kiểm tra bỏ-một-mẫu ~1,2 cm). **Hiệu chỉnh này gắn với đúng tờ giấy và cách đặt robot lúc đo**. Tờ A4 cũ in nhỏ hơn ~4,5% so với đúng cỡ.
- **Vị trí vật** đo từ cam TREN được **bù thị sai** (`vision.find_objects`): cam treo cao ~46 cm nên nắp vật cao 4 cm hiện lệch ra xa tâm ảnh so với đáy.

## 5. Camera: nhận đúng OBSBOT và MacBook

Camera mở bằng **chỉ số** OpenCV (`--top`, `--side`). Trên macOS thứ tự này có thể đổi giữa các lần chạy (đã thấy lúc `[OBSBOT, MacBook]`, lúc ngược lại),
nên mỗi lần chạy nhìn hai khung hình: khung có tiêu đề `CAM TREN` phải là hình nhìn từ trên xuống; sai thì đổi hai số.

## 6. Firmware và bảo vệ servo

`robot_arm_4dof/robot_arm_4dof.ino` nhận phím từ USB lẫn Bluetooth và gửi gói JSON góc 4 servo (`{"servo":[...]}`) 5 lần/giây.

- Mỗi phím quay **2°** (đế / vai / khuỷu, `STEP_ARM`) hoặc **5°** (kẹp, `STEP_GRIP`). Giới hạn kẹp **160°** (`GRIP_CLOSE_LIMIT`).
- Servo kẹp từng bị nóng vì firmware không nhả xung PWM khi bị ép. Giờ: kẹp mở hết cỡ 5 giây không có lệnh thì **ngắt xung**; đã khép quá 60 giây cũng ngắt; chỉ khi có lệnh kẹp (`J` / `L` / `H`) mới cấp xung lại.
- Kẹp là cơ cấu song song **phi tuyến**: từ 95° lên 125° hàm chỉ khép thêm ~0,5 cm; vật rộng ~4 cm (như cốc đỏ) bị đẩy ra khi khép tới 150-160°. Cốc thon dần xuống
  đáy nên hai mặt kẹp đẩy nó ra như hạt dưa: nên dán ma sát (băng keo hai mặt / xốp mỏng) lên mặt trong hai ngón hoặc dùng vật có thân thẳng.
- Nạp firmware: `./robot_arm_4dof/flash.sh` (dùng `arduino-cli` có sẵn trong Arduino IDE 2, board `arduino:avr:uno`). Arduino reset khi nạp nên servo giật về
  Home: cắt nguồn servo hoặc đưa cánh tay ra chỗ trống trước. Nạp xong, đế quay hết sang phải (Home 0°) là firmware mới đã chạy.
- Arduino Uno **tự reset mỗi khi đường DTR của cổng USB hạ xuống rồi nâng lên**, cả 4 servo giật về Home 0/90/90/95. Thường do một chương trình khác mở rồi đóng
  cổng USB lúc `main.py` đang chạy. **Đừng mở cổng bằng chương trình khác khi `main.py` đang chạy.** `main.py` chỉ mở cổng một lần lúc chạy và không mở lại; rút cáp USB thì cắm lại rồi chạy lại chương trình.

## 7. Kiểm tra bằng mắt

Chạy chương trình (không ghi `--port` cũng được, khi đó cánh tay mô phỏng) rồi nhìn màn hình:

1. Lưới 5 cm bám đúng tờ giấy, góc dưới ghi `Luoi A4: thay 4/4 ma ArUco`.
2. Đặt vật có màu: vòng xanh nằm trên vật, kèm X, Y (cm).
3. Bấm `R`: ô 1 hiện lệnh to, ví dụ `BAM A x55`.
4. Bấm đúng phím đó: số lần bấm giảm dần, tới `XONG!`; giữ 1 giây thì `Thanh cong` cộng 1.

Không có camera thì dùng 2 ảnh đã lưu thay camera: `uv run python main.py --top tren.jpg --side ngang.jpg`.

## 8. Xử lý sự cố

| Hiện tượng | Cách xử lý |
|---|---|
| `KHONG THAY TO A4` | in đúng kích thước, đủ sáng, 4 mã không bị che / chói; trong khung có ít nhất 2 mã |
| Mã ArUco không nhận | thêm **viền trắng** quanh mã (ít nhất ~0,5 cm); kiểm tra cạnh mã đúng 2,8 cm |
| Lưới lệch sau khi dời camera / giấy | bấm `U` |
| Hai khung đảo nhau / sai camera | chạy lại với `--top` / `--side` đổi số (mục 5) |
| Camera đen, log `not authorized to capture video` | cấp quyền Camera trong Cài đặt hệ thống → Quyền riêng tư; mở lại ứng dụng |
| `USB Arduino: MO PHONG` | chưa ghi `--port` hoặc ghi sai cổng; cắm cáp USB, tắt chương trình khác đang giữ cổng |
| `Chua co dich: ... roi bam R` | đặt vật **có màu** (cốc đỏ) lên giấy, không sát mép (dưới ~1 cm), rồi bấm `R` |
| Cánh tay tự giật về Home | Arduino vừa reset (mục 6) |
| Dell: `khong thay Mac` | hai máy cùng Wi-Fi chưa, `main.py` đang chạy trên Mac chưa, macOS có hỏi cho Python nhận kết nối mạng (bấm Cho phép) |
| Dell: `khong noi duoc COMx` | HC-05 có điện (đèn nháy), đã ghép đôi với Dell, đúng cổng **Outgoing**; máy khác đang nối HC-05 thì ngắt ra |
| Gợi ý đưa kẹp lệch vài cm | đo lại vị trí đế (mục 4); kiểm tra tờ giấy không bị xê dịch |

## 9. Đã bỏ khi đơn giản hóa (2026-11-02)

Quy trình gắp 5 bước, kiểm tra thành công bằng S1 / S2 (cam NGANG thấy vật nhấc lên, cam TREN thấy chỗ cũ trống), ghi `logs/attempts.csv`, tự động gửi phím
(Auto-Step), cửa sổ HƯỚNG DẪN GẮP và thanh gợi ý 4 servo, tư thế cam NGANG, YOLO làm mặc định, hiệu chỉnh trong chương trình bằng phím `Y` / `E`. Bản đầy đủ
trước khi đơn giản hóa được sao lưu ở `~/Documents/project/Project_IoT_backup_truoc_don_gian_hoa_2026-11-02.tgz` (không nằm trong repo).

Lần rút gọn phần 2 (2026-11-10): bỏ YOLO (`--yolo`), điện thoại qua `adb` / IP Webcam, xoay hình (`--rotate-*`), ước lượng tờ giấy khi không thấy mã,
vật dán mã ArUco, cảnh báo và phím tráo camera (`T`, `0`-`3`). Vẫn giữ: nhớ mã bị che, bù thị sai, lọc tay người.
Điều khiển từ xa bằng máy Dell được đưa lại ngày 11/11 ở dạng gọn (`share.py`, `remote.py`): chỉ xem màn hình và gửi phím, `R` bấm trên Mac.

Ngày 11/11, những việc làm tay được thì bỏ code (còn trong lịch sử git): bộ test tự động (kiểm tra bằng mắt, mục 7), tạo tờ ArUco (`generate_aruco_a4.py`),
công cụ khớp hiệu chỉnh (`arm_fit.py`), hiệu chỉnh đế bằng chuột (phím `B`), chạy không cửa sổ (`--headless`), tự tìm cổng Arduino (giờ ghi `--port`),
cảnh báo Arduino reset, tìm camera theo tên (giờ chọn chỉ số).
