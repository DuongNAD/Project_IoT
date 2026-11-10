# Project IoT: cánh tay robot 4 servo, 2 camera chỉ cho bạn BẤM PHÍM GÌ

Hệ thống nhìn tờ giấy A4 bằng **2 camera**, tìm vật có màu trên giấy rồi tính xem 3 servo (đế, vai, khuỷu) phải quay tới góc nào để
đầu kẹp tới vật. Màn hình chỉ nói **một việc**: *bấm phím nào, mấy lần, sang trái / phải bao nhiêu độ*, và báo **XONG** khi 3 servo đã tới góc đúng.

```
 camera TREN + NGANG ──► vision.py ──► vật nằm ở (x, y) cm
                                            │
                        ┌───────────────────▼───────────────────┐        ┌────────────────────────────────┐
                        │  NHÓM 1 - ĐIỀU KHIỂN   (control.py)   │  Plan  │  NHÓM 2 - SUCCESS  (success.py)│
                        │  vật ở đâu -> góc servo cần tới       │ ─────► │  3 servo tới góc đó chưa?      │
                        │  -> bấm phím gì, mấy lần; USB Arduino │        │  -> XONG / còn N lần bấm       │
                        └───────────────────────────────────────┘        └───────────────┬────────────────┘
                                                                                         │ Result
                                              màn hình (screen.py): 2 camera + phần 1 + phần 2 ◄──────────┘
```

Hai nhóm chỉ nói chuyện với nhau qua **một đối tượng `Plan`**, nên làm riêng được:

| | Nhóm 1 - ĐIỀU KHIỂN (`control.py`) | Nhóm 2 - SUCCESS (`success.py`) |
|---|---|---|
| Việc | tính góc servo cần tới (IK), lập lệnh bấm phím, gửi phím qua USB | kết luận "đã tới chưa", đếm số lần thành công |
| Đầu vào | các vật camera thấy + góc servo thật Arduino báo về | `Plan` của nhóm 1 |
| Đầu ra | `Plan`: góc hiện tại, góc cần tới, 3 `Move` (phím, số lần, hướng, độ) | `Result`: `done`, từng servo đúng chưa, còn bao nhiêu lần bấm, `count` |
| Không biết gì về | thế nào là "xong" | cách tính góc, camera, USB |

**Thành công** = cả 3 servo lệch không quá **1 bước bấm (2°)** so với góc gợi ý, giữ đúng liên tục **1 giây** thì đếm thêm 1 lần.
Kẹp không tính (nó chỉ cần đầu kẹp tới đúng chỗ của vật).

## 1. Phần cứng

| Thành phần | Ghi chú |
|---|---|
| Arduino Uno + PCA9685 (I2C 0x40) | kênh 0 = đế, 1 = vai, 2 = khuỷu, 3 = kẹp; HC-05 Bluetooth ở D2 / D3: nhận phím từ máy Dell (mục 2, điều khiển từ xa) |
| 4 servo MG996R | nguồn riêng 5-6 V (nguồn tổ ong) cấp vào cổng xanh của PCA9685, **không** lấy từ cổng USB |
| Cam TREN | OBSBOT Meet SE treo phía trên tờ giấy, nhìn xuống |
| Cam NGANG | camera tích hợp của MacBook đặt thấp trước tờ giấy |
| Tờ giấy | in `aruco_A4_clean.pdf` **đúng 100% kích thước** (đo cạnh 1 mã ArUco phải đúng **2,8 cm**), 4 mã (ID 0-3) sát 4 góc; tạo lại bằng `generate_aruco_a4.py` |

## 2. Cài đặt và chạy

```bash
uv sync                      # cài OpenCV, pyserial, pytest (Windows thêm pygrabber)
./robot_arm_4dof/flash.sh    # biên dịch + nạp firmware (cần Arduino IDE 2, xem mục 6)
uv run python main.py
```

macOS hỏi quyền **Camera** lần đầu cho ứng dụng đang chạy lệnh (Terminal, PyCharm...): bấm OK.

**Windows** (máy Dell): `pygrabber` đọc tên camera theo đúng thứ tự DirectShow; `Integrated Webcam` được nhận là cam NGANG. Cam TREN khác OBSBOT thì
truyền một phần tên (`--top iriun`) hoặc chỉ số (`--top 0`). Cổng Arduino là `COMx`, tự tìm theo tên CH340 / Arduino.

```bash
uv run python main.py --list-cameras    # in danh sách camera theo chỉ số OpenCV
uv run python main.py --no-serial       # chạy mô phỏng, không mở cổng USB Arduino (không gửi phím xuống robot)
uv run python main.py --top 0 --side 1  # chỉ rõ chỉ số camera (mặc định: --top obsbot --side mac, tìm theo tên)
```

Một cửa sổ: 2 camera ở trên, bên dưới **phần 1 (điều khiển)** → **phần 2 (success)**. Bấm phím trên cửa sổ video:

| Phím | Tác dụng |
|---|---|
| `A` / `D` | xoay đế sang **phải** / **trái** (nhìn theo cam NGANG = MacBook), mỗi lần **2°** |
| `W` / `S` | nâng / hạ vai, mỗi lần 2° |
| `I` / `K` | khuỷu lên / xuống, mỗi lần 2° |
| `J` / `L` | mở / khép kẹp, mỗi lần 5° (không tính vào thành công) |
| `H` | đưa cả 4 servo về Home (90/90/90/95) |
| `X` / `Z` | cho servo kẹp / cả 4 servo nghỉ (ngắt xung PWM để nguội); `Z` cần firmware có phím Z, hạ đầu kẹp tựa xuống chỗ trống trước |
| `TAB` | đổi vật mục tiêu |
| `B` | hiệu chỉnh đế robot (mục 4), `ESC` để hủy |
| `U` | quên vị trí 4 mã ArUco đã nhớ (sau khi dời camera hoặc tờ giấy) |
| `C` | chụp ảnh gốc cả 2 camera vào `captures/` |
| `Q` | thoát |

### Điều khiển từ xa: máy Dell cách ~2 m (xem qua Wi-Fi, bấm phím qua Bluetooth)

```
                 USB: góc servo + nguồn
   MAC (main.py) ─────────────────────── UNO ── HC-05
   2 camera, vision, control, success              ▲
     │                                             │ Bluetooth: phím a d w s i k j l h x z
     └── Wi-Fi: ảnh màn hình (2 cam + lệnh + XONG) ──►  DELL (remote.py)
```

- **Mac** đặt cạnh cánh tay (camera MacBook là cam NGANG), **cắm USB vào Arduino**: Arduino báo góc servo về Mac sau mỗi phím, Mac tính lại lệnh và success.
  `main.py` chia sẻ ảnh màn hình qua Wi-Fi (`phone.py`) và in ra lệnh cho máy Dell kèm đường dẫn có mã 6 số. Mã lưu trong `.phone_pin`, giữ nguyên giữa các lần chạy (đổi mạng thì chỉ IP đổi); xóa tệp này để đổi mã.
- **Dell** chạy `remote.py`: một cửa sổ hiện màn hình của Mac, gõ `A D W S I K J L H X Z` trên bàn phím Dell thì phím đi qua Bluetooth tới HC-05.
  `H` (Home) và `Z` (nghỉ hết) phải bấm 2 lần trong 2 giây. Thanh trên cùng báo Mac (Wi-Fi) và Bluetooth đã nối chưa; `Q` thoát.
- **Firmware không đổi**: firmware đang nạp đã nhận phím từ HC-05 và báo góc qua USB.

Chuẩn bị:
1. Dell: ghép đôi HC-05 trong cài đặt Bluetooth (PIN thường là `1234` hoặc `0000`). Windows tạo 2 cổng COM: dùng cổng **Outgoing**
   (`uv run python remote.py --list-ports` cho biết cổng sẽ dùng). **Chỉ ghép đôi HC-05 với Dell**: HC-05 nhận một kết nối mỗi lúc.
2. Mac và Dell vào **cùng một Wi-Fi**. Mạng trường chặn hai máy thấy nhau thì cả hai bắt điểm phát Wi-Fi của điện thoại.
3. Mac: cắm USB Arduino, `uv run python main.py`, chép dòng `Chạy trên máy Dell (không chạy trên Mac): python remote.py --mac http://<ip Mac>:8000/<mã>/` nó in ra.
4. Dell: chạy đúng dòng đó (thêm `--port COM5` nếu tự tìm sai cổng).

Dự phòng: Dell mở đường dẫn đó bằng trình duyệt để xem, và gửi phím bằng PuTTY (Serial, cổng COM của HC-05, 9600). Điện thoại mở đường dẫn
(hoặc quét mã QR in trong Terminal) cũng xem được và có nút bấm phím; nút trên trang đi qua Wi-Fi tới Mac rồi USB, không qua Bluetooth.
Khác mạng: `ngrok http 8000` rồi dùng đường dẫn ngrok + `/<mã>/`. `--no-phone` tắt chia sẻ màn hình, `--phone-port` đổi cổng.

## 3. Code chia thế nào

| Tệp | Vai trò |
|---|---|
| `main.py` | nối các phần: camera → vision → control → success → màn hình; phím, chuột, tham số dòng lệnh |
| `control.py` | **NHÓM 1**: hình học cánh tay (FK / IK), cổng USB Arduino, chọn vật, `Plan` + `Move` |
| `success.py` | **NHÓM 2**: `check(plan)` → `Result`; `Success` đếm số lần thành công |
| `screen.py` | vẽ màn hình: 2 camera + phần 1 + phần 2 nối nhau |
| `vision.py` | dò tờ A4 qua ArUco (Homography pixel ↔ cm), tìm vật có màu, bù thị sai theo độ cao vật |
| `cameras.py` | tìm camera theo tên, mỗi camera đọc trên một luồng riêng, mất tín hiệu thì tự mở lại |
| `phone.py` | chia sẻ màn hình qua Wi-Fi (máy chủ web nhỏ, thư viện chuẩn) cho máy Dell; trang web dự phòng cho điện thoại |
| `remote.py` | app máy Dell: xem màn hình Mac qua Wi-Fi, gửi phím qua Bluetooth HC-05 (chép riêng tệp này sang Dell cũng chạy) |
| `calibration.py` | lưu / nạp hiệu chỉnh vào `calibration.json` |
| `arm_fit.py` | công cụ khớp hình học cánh tay từ các lần "ôm" thật (Levenberg-Marquardt, chỉ dùng numpy) |
| `generate_aruco_a4.py` | tạo tờ A4 4 mã ArUco để in (`aruco_A4_clean.pdf`) |
| `robot_arm_4dof/` | firmware Arduino và `flash.sh` |
| `tests/` | bộ test, mỗi nhóm một tệp (`test_control.py`, `test_success.py`, `test_screen.py`, ...) |
| `_luu_tru/` | file không còn dùng (kịch bản slide cũ, tờ A4 có lưới, script thử servo bằng tay), giữ lại để tra cứu |

Mỗi khung hình trong `main.py` chỉ là ba dòng: `plan = control.update(vision.objects)` → `result = success.update(plan)` → `build_screen(..., plan, result)`.

## 4. Tờ giấy, đế robot và hiệu chỉnh

Hệ tọa độ gắn với **tờ giấy** (không phụ thuộc camera nào nhìn): gốc ở góc ngoài mã **ID 0**, trục **X** chạy ID 0 → ID 1 (29.7 cm), trục **Y**
chạy ID 0 → ID 3 (21.0 cm). Lưới tự dò từ các mã ArUco thật; cánh tay che mất 1-2 mã thì dùng vị trí đã nhớ.

- **Đế robot**: mặc định (14.85, -7.5) cm, nhìn vào +Y. Đặt khác thì bấm `B` rồi click vào **trục xoay của đế** trên hình cam TREN (đúng điểm ở
  mặt bàn). **Chỉ bấm `B` khi cam TREN đã thấy đủ 4 mã** (góc dưới trái ghi `Luoi A4: thay 4/4 ma ArUco`), nếu không vị trí đế lưu sai.
- **Hình học cánh tay thật khác mô hình mặc định**: đo từ 10 lần "ôm" cốc bằng tay (2026-11-02), sai số RMS còn ~0,85 cm (kiểm tra bỏ-một-mẫu ~1,2 cm). Kết quả nằm trong
  `calibration.json` (không đưa lên git): `base` (vị trí, hướng đế), `arm` (hai góc chuẩn vai / khuỷu khi servo ở 90°), `claw` (càng kẹp gắn cứng vào khâu
  khuỷu nên độ lệch của điểm kẹp quay theo khâu đó; app gộp nó vào chiều dài khâu 3, xem docstring `calibration.py`). **Hiệu chỉnh này gắn với đúng tờ
  giấy và cách đặt robot hiện tại**: đổi tờ giấy (kích thước in khác) hoặc dời robot thì phải đo lại. Tờ A4 cũ in nhỏ hơn ~4,5% so với đúng cỡ.
- **Vị trí vật** đo từ cam TREN được **bù thị sai** (`vision.find_objects`): cam treo cao ~46 cm nên nắp cốc cao 5 cm hiện lệch ~1 cm so với đáy.
- Công cụ khớp lại: `arm_fit.fit_geometry(samples, ARM_CONFIG, control.predict_tip)` với mỗi mẫu `{"servo": (đế, vai, khuỷu), "x_cm", "y_cm", "z_mm"}` (servo
  khi hai ngón bao quanh vật + vị trí vật đo bằng camera). Cần ≥ 2 mẫu cách nhau ≥ 5 cm, 3 mẫu là đủ.

## 5. Camera: cách nhận đúng OBSBOT và MacBook

Chỉ số `cv2.VideoCapture(i)` trên macOS **không** theo thứ tự của `system_profiler` hay danh sách AVFoundation (hai danh sách đó xếp camera "dùng gần
nhất" lên đầu nên đổi giữa các lần chạy); OpenCV sắp theo `uniqueID` nên ổn định. `cameras.py` tìm camera theo **tên**, rồi đổi sang chỉ số bằng đúng
quy tắc sắp theo `uniqueID` của OpenCV, ngay trước mỗi lần mở. Bỏ qua camera ảo (`OBSBOT Virtual Camera`, Desk View).

## 6. Firmware và bảo vệ servo

`robot_arm_4dof/robot_arm_4dof.ino` nhận phím từ USB lẫn Bluetooth và gửi trạng thái JSON 5 lần/giây (`servo`, `relax`, `armrelax`).

- Mỗi phím quay **2°** (đế / vai / khuỷu, `STEP_ARM`) hoặc **5°** (kẹp, `STEP_GRIP`). Giới hạn kẹp **160°** (`GRIP_CLOSE_LIMIT`).
- Servo kẹp từng bị nóng vì firmware không nhả xung PWM khi bị ép. Giờ: kẹp mở hết cỡ 5 giây không có lệnh thì **ngắt xung**; đã khép quá 60 giây cũng ngắt;
  phím `X` cho kẹp nghỉ ngay, phím `Z` ngắt xung **cả 4 servo** (cánh tay tự sụp theo trọng lực, hạ đầu kẹp tựa xuống trước). Chỉ phím di chuyển mới cấp xung lại.
- Kẹp là cơ cấu song song **phi tuyến**: từ 95° lên 125° hàm chỉ khép thêm ~0,5 cm; vật rộng ~4 cm (như cốc đỏ) bị đẩy ra khi khép tới 150-160°. Cốc thon dần xuống
  đáy nên hai mặt kẹp đẩy nó ra như hạt dưa: nên dán ma sát (băng keo hai mặt / xốp mỏng) lên mặt trong hai ngón hoặc dùng vật có thân thẳng.
- Nạp firmware: `./robot_arm_4dof/flash.sh` (dùng `arduino-cli` có sẵn trong Arduino IDE 2, board `arduino:avr:uno`). Arduino reset khi nạp nên servo giật về
  Home: cắt nguồn servo hoặc đưa cánh tay ra chỗ trống trước. Banner `Robot Arm Ready! ... + Z (nghi het)` là firmware mới đã chạy.
- Arduino Uno **tự reset mỗi khi đường DTR của cổng USB hạ xuống rồi nâng lên**, cả 4 servo giật về 90/90/90/95. Thường do một chương trình khác mở rồi đóng
  cổng `/dev/cu.usbmodem*` lúc `main.py` đang chạy. **Đừng mở cổng bằng chương trình khác khi `main.py` đang chạy.** `main.py` nhận ra reset qua thời gian
  chạy của firmware quay về 0 và báo `ARDUINO VUA RESET` ở chân màn hình.

## 7. Kiểm thử và chạy không cần phần cứng

```bash
uv run pytest        # FK / IK, lệnh bấm phím, chọn vật, success, màn hình, nhận diện camera, hiệu chỉnh, chạy thử cả chương trình
```

Không test nào chạm vào camera, cổng Serial hay `calibration.json` thật (cảnh dựng bằng camera giả lập có đáp án chính xác). `_luu_tru/test_base_servo.py` là script
điều khiển robot thật nên không nằm trong bộ test tự động. Chạy cả chương trình không cửa sổ, không camera, không robot (dùng ảnh chụp bằng phím `C`):

```bash
uv run python main.py --top captures/tren.jpg --side captures/ngang.jpg --no-serial --headless --seconds 10 --dump-dir out/
# out/ có dual_view.png (màn hình), ảnh đã chú thích của 2 camera và summary.json (nhom_1_dieu_khien, nhom_2_success)
```

## 8. Xử lý sự cố

| Hiện tượng | Cách xử lý |
|---|---|
| `KHONG THAY TO A4` | in đúng kích thước, đủ sáng, 4 mã không bị che / chói; trong khung có ít nhất 2 mã |
| Mã ArUco không nhận | thêm **viền trắng** quanh mã (ít nhất ~0,5 cm); kiểm tra cạnh mã đúng 2,8 cm |
| Lưới lệch sau khi dời camera / giấy | bấm `U` |
| Hai khung hiện cùng một góc nhìn / sai camera | `--list-cameras` rồi chạy lại với `--top N --side M` |
| Camera đen, log `not authorized to capture video` | cấp quyền Camera trong Cài đặt hệ thống → Quyền riêng tư; mở lại ứng dụng |
| `USB Arduino: MO PHONG` | cắm cáp USB, tắt chương trình khác đang giữ cổng |
| Chữ `CHUA THAY VAT` | đặt vật **có màu** (cốc đỏ) lên giấy, không sát mép (dưới ~1 cm); bấm `TAB` đổi vật |
| Cánh tay tự giật về Home | xem mục 6 (Arduino reset) |
| Gợi ý đưa kẹp lệch vài cm | đo lại hiệu chỉnh (mục 4); kiểm tra tờ giấy không bị xê dịch |
| Dell: `khong thay Mac` | hai máy cùng Wi-Fi chưa, `main.py` đang chạy chưa, macOS có hỏi cho Python nhận kết nối mạng (bấm Cho phép); mạng trường chặn thì dùng điểm phát điện thoại |
| Dell: `sai ma trong duong dan` | mã trong đường dẫn không khớp `.phone_pin` (gõ nhầm, hoặc tệp bị xóa nên `main.py` tạo mã mới): chép lại dòng `python remote.py --mac ...` mới nhất `main.py` in ra |
| Dell: `chua thay cong Bluetooth` / `khong noi duoc COMx` | ghép đôi HC-05; HC-05 có điện (đèn nháy); Mac / điện thoại khác đang nối HC-05 thì ngắt ra; thử `--port` cổng Outgoing |

## 9. Đã bỏ khi đơn giản hóa (2026-11-02)

Quy trình gắp 5 bước, kiểm tra thành công bằng S1 / S2 (cam NGANG thấy vật nhấc lên, cam TREN thấy chỗ cũ trống), ghi `logs/attempts.csv`, tự động gửi phím
(Auto-Step), cửa sổ HƯỚNG DẪN GẮP và thanh gợi ý 4 servo, tư thế cam NGANG, YOLO làm mặc định, hiệu chỉnh trong chương trình bằng phím `Y` / `E`. Bản đầy đủ
trước khi đơn giản hóa được sao lưu ở `~/Documents/project/Project_IoT_backup_truoc_don_gian_hoa_2026-11-02.tgz` (không nằm trong repo).

Lần rút gọn phần 2 (2026-11-10): bỏ YOLO (`--yolo`), điện thoại qua `adb` / IP Webcam, xoay hình (`--rotate-*`), ước lượng tờ giấy khi không thấy mã,
vật dán mã ArUco, cảnh báo và phím tráo camera (`T`, `0`-`3`). Vẫn giữ: nhớ mã bị che, bù thị sai, lọc tay người / thân robot, tìm camera theo tên.
