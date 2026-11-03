# 05 · Số liệu và nguồn (nguồn sự thật duy nhất cho slide)

Mọi con số, tên linh kiện và nhận định trên slide **chỉ được lấy từ file này**. Kiểm tra lần cuối: **03/11/2026 khoảng 20:40**, sau khi gộp phần làm
trên máy Windows vào bản hai nhóm nối nhau (`control.py` → `success.py`). Mã đã lên GitHub (`main` = `e3f2d85`); test chạy thật bằng
`.venv/bin/python -m pytest -q` (109 test pass). Bộ slide đã dựng: `Project_IoT_ThuyetTrinh.pptx` (15 slide, `build_slides.py`).

Kiểm lại bằng máy sau mỗi lần sửa mã: `.venv/bin/python -B slides/tools/check_facts.py` (so các hằng số ở mục 17 và mọi dẫn `file:dòng` trong các file `.md` với mã hiện tại).

Nhãn trạng thái:

| Nhãn | Nghĩa |
|---|---|
| **[CODE]** | đọc trực tiếp từ mã nguồn, firmware hoặc `calibration.json` (có dòng dẫn) |
| **[ĐO]** | đo hoặc quan sát trên phần cứng thật (ảnh, hoặc ghi chú của phiên làm việc ngày 02/11 khi không có ảnh) |
| **[MÔ PHỎNG]** | chỉ chạy trong test, hoặc với camera / cánh tay giả lập |
| **[ƯỚC LƯỢNG]** | suy ra từ ảnh, sai số ± đã ghi; phải nói "khoảng" |
| **[CHƯA]** | chưa làm hoặc chưa kiểm chứng; chỉ được nói là "chưa" |

---

## 1. Phần cứng

| Mục | Giá trị | Nhãn | Nguồn |
|---|---|---|---|
| Vi điều khiển | Arduino Uno (board `arduino:avr:uno`) | CODE | `robot_arm_4dof/flash.sh:19`; `README.md` mục 1 |
| Mạch PWM | PCA9685, địa chỉ I²C 0x40, xung 50 Hz | CODE | `robot_arm_4dof.ino:8,90` |
| Servo | 4 × MG996R: kênh 0 đế, 1 vai, 2 khuỷu, 3 kẹp | CODE | `README.md` mục 1; `robot_arm_4dof.ino:26-29`; `control.py:56` |
| Bước mỗi phím | đế, vai, khuỷu **2°**; kẹp **5°** | CODE | `robot_arm_4dof.ino:13-14`; `control.py:63` |
| Giới hạn góc | đế 0–180°, vai 25–155°, khuỷu 25–155°, kẹp 95–**160°** | CODE | `control.py:57-62`; `robot_arm_4dof.ino:19-21,121-152` |
| Góc khởi động / Home | 90 / 90 / 90 / 95° (phím `H` đưa về) | CODE | `robot_arm_4dof.ino:26-29,154-158`; `control.py:64` |
| Nguồn servo | nguồn tổ ong riêng 5–6 V vào cổng xanh PCA9685, **không** lấy từ cổng USB | CODE (tài liệu) | `README.md` mục 1 |
| Bluetooth | HC-05 qua `SoftwareSerial` chân D2/D3, 9600 baud, tùy chọn | CODE | `robot_arm_4dof.ino:6,87` |
| Cổng USB tới laptop | Serial 9600 baud | CODE | `robot_arm_4dof.ino:86`; `control.py:267` |
| Gói trạng thái Arduino → laptop | JSON `{"t":…,"servo":[đế,vai,khuỷu,kẹp],"relax":0\|1,"armrelax":0\|1}`; gửi ngay sau mỗi phím và mỗi 200 ms (5 gói/giây danh định, **đo thực tế 4–5 gói/giây**) | CODE + ĐO | `robot_arm_4dof.ino:70-83,186-188,203-207` |
| **Góc servo báo về là góc LỆNH** | gói JSON in các biến `angleBase`, `angleShoulder`… mà firmware đã gán; MG996R không báo vị trí thật. "Đã tới góc" nghĩa là lệnh đã tới góc, **không** phải đã đo thấy cánh tay ở đó | CODE | `robot_arm_4dof.ino:70-83` |
| Cam TRÊN | OBSBOT Meet SE treo phía trên tờ giấy, nhìn xuống, 1920×1080 | CODE + ĐO | `README.md` mục 1; ghi chú phiên 02/11 (memory `project-iot-camera-setup`) |
| Cam NGANG | camera tích hợp MacBook đặt thấp trước tờ giấy, 1920×1080; có thể thay bằng điện thoại (IP Webcam qua `adb`), tùy chọn | CODE + ĐO | `README.md` mục 1; `cameras.py:117-150,204` |
| Hệ điều hành và thư viện | macOS (PyObjC tìm camera theo tên), Python ≥ 3.12, OpenCV, pyserial, ultralytics (cho YOLO tùy chọn). Từ bản gộp 03/11 mã có thêm phần cho Windows: cổng `COMx` (ưu tiên CH340 / Arduino), tên camera DirectShow qua `pygrabber`, YOLO chạy CUDA nếu có; **mọi ảnh và số đo trong slide đều làm trên macOS** | CODE | `pyproject.toml`; `control.py:251-281`; `cameras.py:82-96,311-314`; `vision.py:369-373` |

## 2. Tờ A4, hệ tọa độ và nhận diện vật

| Mục | Giá trị | Nhãn | Nguồn |
|---|---|---|---|
| Tờ giấy | A4 đặt ngang 29,7 × 21,0 cm, in đúng 100% (đo cạnh một mã phải đúng 2,8 cm) | CODE | `vision.py:24-25`; `generate_aruco_a4.py:3`; `README.md` mục 1 |
| Mã ArUco của tờ | 4 mã `DICT_4X4_50`, ID 0–3, cạnh 2,8 cm, cách mép 0,25 cm, sát 4 góc | CODE | `vision.py:28-30,40`; `generate_aruco_a4.py:31-36` |
| Hệ tọa độ | gốc ở góc ngoài mã ID 0; X chạy ID 0 → ID 1 (29,7 cm); Y chạy ID 0 → ID 3 (21,0 cm); gắn với **tờ giấy**, không phụ thuộc camera nào nhìn | CODE | `README.md` mục 4; `calibration.py:5-8` |
| Homography | từ 4 mã ArUco thật, cho **cả hai camera**; ảnh phẳng của tờ giấy dựng bằng `warpPerspective` | CODE | `vision.py:152-170,275-290` |
| Che mất mã | che 1–2 mã vẫn chạy nhờ vị trí đã nhớ; camera bị xô thì tự quên; phím `U` quên thủ công | CODE + MÔ PHỎNG | `README.md` mục 4; `main.py:220-223`; `tests/test_vision.py:59,75` |
| Cảnh báo gán nhầm camera | so độ xiên của tờ giấy trong hai ảnh; cam TRÊN xiên hơn cam NGANG thì báo, phím `T` tráo vai trò | CODE | `main.py:119-130,226-231` |
| Mã dán lên vật | ID 10–29; kích thước tra `OBJECT_SPECS` (đã định nghĩa ID 10–13) | CODE | `vision.py:476-482` |
| **Cách tìm vật (mặc định)** | tách màu HSV trên ảnh phẳng của tờ giấy: độ bão hòa ≥ 90, sáng ≥ 60; bỏ viền 1 cm sát mép giấy, khối rộng > 80 mm hoặc dài > 180 mm, khối chạm mép, khối dính phần đen của cánh tay (bàn tay người không bị nhận thành vật) | CODE | `vision.py:271-300` |
| YOLO | **tùy chọn**, bật bằng `--yolo` (mặc định TẮT vì "YOLO hay gọi nhầm bộ phận robot"); YOLO11s trọng số COCO có sẵn (`yolo11s.pt`), **chưa fine-tune**; bỏ 12 lớp (laptop, tv, bed, book, chair, dining table, couch, person, keyboard, mouse, remote, cell phone); vật YOLO phải có màu (bão hòa và sáng ≥ 90) | CODE | `main.py:53`; `vision.py:43-47,365-368,491-492,507-515` |
| YOLO có nhận nhầm | `bottle`, `airplane`, `frisbee` (ảnh), thân servo đen bị gọi là `traffic light` / `motorcycle` (ghi chú trong mã) | ĐO | ảnh `ui_guide_cameras.png` (**bản trước khi đơn giản hóa**); `vision.py:491` |
| Kích thước cốc đỏ số 3 | thân 34 mm, nắp ≈ 40 mm, cao 50 mm | ĐO | `vision.py:483-486` |
| Chọn vật | vật gần đế nhất được chọn trước; `TAB` đổi vật; vật được nhận lại ở khung sau nếu tâm dời ≤ 4 cm; trung bình 10 khung; che mất vật thì nhớ vị trí 120 s | CODE | `control.py:68-69,506-541`; `tests/test_control.py:149-184` |
| **Hiệu chỉnh phối cảnh cam TRÊN** | cam treo cao ≈ 46 cm nhìn xuống; vật cao 5 cm hiện lệch ≈ 1 cm; công thức `p_thật = n + (p_đo − n)·(H − h)/H` (n: tâm ảnh, H: 46 cm, h: độ cao vật). Một phép đo ngày 02/11: cam TRÊN (20,6; 6,8) cm, cam MacBook (20,0; 7,8) cm, lệch **1,2 cm**; sau hiệu chỉnh còn **0,2 cm** | CODE + ĐO (một vị trí cốc) | `vision.py:486-505,557-562`; `tests/test_vision.py:223-243` |
| Độ cao 46 cm của cam TRÊN | ước từ ảnh (≈ 27 px/cm ở mặt bàn); không đo bằng thước | ƯỚC LƯỢNG | `vision.py:490`; ghi chú phiên 02/11 |

## 3. NHÓM 1 · Điều khiển (`control.py`): từ vật tới phím cần bấm

| Mục | Giá trị | Nhãn | Nguồn |
|---|---|---|---|
| Việc của nhóm 1 | vật ở (X, Y) cm → góc ba servo cần tới (IK) → danh sách phím cần bấm; giữ cổng USB tới Arduino. **Không biết** thế nào là "xong" | CODE | `control.py:1-13`; `README.md` (đầu trang, bảng hai nhóm) |
| Số đo cánh tay mặc định (`ARM_CONFIG`) | d₁ = 70 mm (mặt bàn → trục vai), L₂ = 105 mm (vai → khuỷu), L₃ = 100 mm (khuỷu → cổ tay), tâm hai ngón kẹp lệch L₄ᵣ = 65 mm ra trước và L₄z = 25 mm xuống dưới | CODE (số đo thước) | `control.py:36-41` |
| Góc chuẩn khi servo 90° (mặc định) | khâu L₂ nghiêng +45°, khâu L₃ gập −45° so với L₂; **thực tế khác** (xem mục 8) | CODE | `control.py:49-50` |
| Mô hình | đế quay θ₁ = atan2(y, x); vai + khuỷu giải tam giác hai khâu (nghiệm khuỷu hướng lên); **không có servo cổ tay** nên hướng ngón kẹp không chọn được | CODE | `control.py:98-141` |
| Điểm kẹp mục tiêu | cao **25 mm** (nửa thân cốc cao 50 mm) | CODE | `control.py:67` |
| Đổi sang servo | đế = 90 + θ₁; vai = 90 + (θ₂ − θ₂@90); khuỷu = 90 + (θ₃ − θ₃@90); làm tròn về bội số của bước (2°) quanh neo 90°, kẹp trong giới hạn | CODE | `control.py:144-161` |
| Đổi tọa độ | giấy (cm) ↔ hệ robot (mm) theo vị trí và hướng của đế | CODE | `control.py:174-195`; `tests/test_control.py:42` |
| Phím và hướng | `A` / `D` xoay đế **sang phải / sang trái, nhìn theo cam NGANG (MacBook)**; `W` / `S` nâng / hạ vai; `I` / `K` khuỷu lên / xuống; `J` / `L` mở / khép kẹp; `H` Home; `X` kẹp nghỉ; `Z` cả 4 servo nghỉ | CODE | `control.py:211-217`; `README.md` mục 2 |
| Lưu ý chú thích | chú thích trong firmware ghi `a (Trái)` theo hướng nhìn của chính robot; trên màn hình và slide dùng hướng nhìn theo cam NGANG, ngược lại | CODE | `robot_arm_4dof.ino:120`; `screen.py:26` |
| Kế hoạch bấm (`Plan`, `Move`) | mỗi servo một `Move` gồm phím, số lần (= độ lệch ÷ bước, làm tròn xuống), hướng, số độ; **kẹp không bao giờ nằm trong Plan** | CODE | `control.py:221-245,474-490`; `tests/test_control.py:64-90` |
| Kiểm IK ↔ FK | trên lưới > 100 điểm trong tầm với, FK(IK(p)) trùng p với sai số **< 0,1 mm**; mọi góc servo ra đều bấm tới được | MÔ PHỎNG | `tests/test_control.py:16-32` |
| Ngoài tầm với | IK báo `reachable = False` và dời vật thêm bao nhiêu mm; màn hình ghi `VAT NGOAI TAM VOI` | CODE | `control.py:98-141`; `screen.py:175`; `tests/test_control.py:35` |
| **Ví dụ tính được** | với `calibration.json` hiện tại, cốc ở **(20,1; 7,4) cm** → robot x = 240 mm, y = −73 mm → gợi ý **đế 74°, vai 58°, khuỷu 90°**. Từ Home 90/90/90: đế −16° = phím **D × 8**, vai −32° = phím **S × 16**, khuỷu 0 (đã đúng) | CODE (tính lại 02/11 23:07) | mục 16; `main.py` chạy `--headless` 22:46 cho cùng kế hoạch (ghi chú phiên) |
| Ví dụ trên ảnh màn hình (slide 8) | khung camera thật 20:27: cốc ở **(16,5; 13,8) cm** → gợi ý **[đế 88°, vai 60°, khuỷu 84°]**; từ Home: **S × 15** (hạ vai 30°), **K × 3** (khuỷu xuống 6°), đế lệch 2° nên `DA DUNG`; còn **18 lần bấm** | MÔ PHỎNG (chương trình chạy trên ảnh đã lưu; đế đổi sang hệ lúc chụp, xem mục 5) | ảnh `ui_screen_before.png`; `slides/tools/make_screen_images.py` |
| Cổng USB | 9600 baud, đọc nền, **mở tay cầm mới trước khi đóng tay cầm cũ** (để DTR không hạ), không đóng cổng vì một lỗi đọc thoáng qua, tự nhận ra Arduino reset khi thời gian chạy `t` quay về 0 | CODE | `control.py:251-468`; `tests/test_serial_link.py:96-150` |
| Gửi phím | app chỉ gửi phím khi **người bấm**; không còn chế độ tự gửi (Auto-Step đã bỏ) | CODE | `control.py:565-576`; `main.py:204-214` |

## 4. NHÓM 2 · Success (`success.py`): đã tới chưa?

| Mục | Giá trị | Nhãn | Nguồn |
|---|---|---|---|
| Việc của nhóm 2 | nhận `Plan` của nhóm 1, trả lời một câu: ba servo đế / vai / khuỷu đã tới góc gợi ý chưa. **Không biết** gì về camera, IK hay cổng USB | CODE | `success.py:1-11` |
| Quy tắc "đã tới" | mỗi servo lệch **≤ 1 bước bấm (2°)** so với góc gợi ý (lệch 3° là chưa) | CODE | `success.py:16,32-34`; `tests/test_success.py:23` |
| Quy tắc "một lần thành công" | cả ba servo đã tới và **giữ liên tục ≥ 1,0 giây** thì đếm thêm 1; giữ thêm không đếm nữa; lướt qua chưa đủ 1 s không đếm; rời góc rồi tới lại đủ lâu thì đếm lần hai | CODE | `success.py:17,55-75`; `tests/test_success.py:46-65` |
| Kẹp **không tính** | kẹp lệch 55° vẫn XONG; bản đơn giản chỉ cần đưa đầu kẹp tới đúng chỗ của vật | CODE | `success.py:9-10`; `tests/test_success.py:31` |
| Năm trạng thái | `done` (xong) · `moving` (còn phải bấm) · `no_target` (chưa thấy vật) · `unreachable` (vật ngoài tầm) · `relaxed` (tay đang nghỉ); `relaxed` thắng mọi trạng thái khác, rồi `no_target`, rồi `unreachable`; không thấy vật thì không được báo xong | CODE | `success.py:19,37-52`; `tests/test_success.py:35-43` |
| Kết quả (`Result`) | `state`, `done`, `joints_ok` (3 giá trị), `next_move` (việc đầu tiên chưa xong theo thứ tự đế → vai → khuỷu), `remaining` (tổng số lần bấm còn lại), `count` | CODE | `success.py:22-29` |
| Vì sao dung sai 2° | "mô hình hình học chỉ chính xác cỡ đó"; bắt căn tới 0° chỉ làm người dùng đuổi theo nhiễu | CODE (chú thích) | `success.py:16`; `tests/test_success.py:24` |
| Chuỗi nối nhau | làm đúng lệnh to trên màn hình (bấm phím `key` `steps` lần, nhìn lại lệnh mới) thì ra XONG, đếm đúng 1 lần, không bấm thừa; bấm lệch 4° thì hết XONG và số đã đếm không mất | MÔ PHỎNG | `tests/test_end_to_end.py:11-47` |
| Hai nhóm chỉ nói chuyện qua một đối tượng | `Plan` (nhóm 1 sinh ra, nhóm 2 đọc); cùng một `Plan` cho cùng một kết luận, không cần camera hay cổng USB | CODE | `README.md` (đầu trang); `tests/test_end_to_end.py:50-56` |
| **Giới hạn của "XONG"** | góc servo là **góc lệnh** (mục 1): XONG chứng minh phím đã được bấm đúng số lần, **không** chứng minh hai ngón kẹp thật đang ở sát vật. Độ đúng của gợi ý phụ thuộc mô hình hình học (mục 8) | CODE | `robot_arm_4dof.ino:70-83`; `success.py:42-43` |
| **Trạng thái thật** | **chưa có lần đếm thành công nào trên cánh tay thật**: bản này mới chạy bằng test, bằng camera giả lập và bằng ảnh đã lưu (`--no-serial --headless`); Arduino được rút ra lúc ≈ 22:40 | MÔ PHỎNG / CHƯA | ghi chú phiên 02/11; `ls logs` (không có thư mục) |

## 5. Màn hình (`screen.py`, `main.py`)

| Mục | Giá trị | Nhãn | Nguồn |
|---|---|---|---|
| Bố cục | cửa sổ rộng 1280 px: hai camera ở trên (mỗi ô 640 × 360), bên dưới **phần 1 · ĐIỀU KHIỂN** → mũi tên → **phần 2 · SUCCESS**, chân trang | CODE | `screen.py:1-26,262-271` |
| Phần 1 | lệnh to: phím to màu hổ phách + `BAM D x8` + `SANG TRAI 16 DO` + `Con 24 lan bam`; ba hàng servo (góc hiện tại → góc đích, thanh vị trí, `DA DUNG` khi xong) | CODE | `screen.py:157-203` |
| Phần 2 | `CHUA XONG` + `con N lan bam`, hoặc **`XONG!`** (nền xanh) khi cả ba servo tới góc; ba dấu tích đế / vai / khuỷu; `Thanh cong: N lan`; dòng chú giải "ca 3 servo toi goc goi y (lech khong qua 2 do, kep khong tinh)" | CODE | `screen.py:206-239` |
| Trạng thái khác | `CHUA THAY VAT`, `VAT NGOAI TAM VOI`, `CANH TAY DANG NGHI`, `KHONG CAN BAM THEM` | CODE | `screen.py:172-177` |
| Trên hai camera | vòng **DICH** (chỗ vật) và dấu **KEP** (đầu kẹp theo mô hình) vẽ trên mặt giấy; lưới 5 cm; viền tờ giấy | CODE | `main.py:155-162`; `vision.py:585-616` |
| Chân trang | trạng thái USB (`DA KET NOI` hoặc `MO PHONG`), `Vat n/N`, hàng phím tắt; banner `ARDUINO VUA RESET` hoặc `FIRMWARE CU KHONG CO PHIM Z` | CODE | `screen.py:249-259`; `control.py:550-552,572` |
| Chữ **không dấu** | OpenCV `putText` không vẽ được dấu tiếng Việt: giữ nguyên, nói rõ khi thuyết trình | CODE | `screen.py:10` |
| Ảnh màn hình trên slide | `ui_screen_before.png` (khung camera 20:27) và `ui_screen_done.png` (khung 20:32:52, sau khi **mô phỏng** bấm 21 phím theo lệnh) là màn hình **thật của chương trình, chạy trên ảnh camera thật đã lưu, cánh tay MÔ PHỎNG** (chân trang ghi `USB Arduino: MO PHONG`, tiêu đề camera ghi `anh da luu`): không phải lần chạy trực tiếp. Ảnh chụp lúc tờ giấy còn hướng ban đầu còn `calibration.json` ghi theo tờ đã xoay 180°, nên script đổi đế về hệ lúc chụp rồi tự kiểm (dấu `KEP` đã hiệu chỉnh cách cốc ≤ 2 cm, không thì dừng). Hai ảnh cho cốc lệch 1,5 cm vì hai ngón kẹp che cốc ở khung 20:32:52 | MÔ PHỎNG | `slides/tools/make_screen_images.py` |

## 6. Firmware bảo vệ servo (tránh nóng)

| Mục | Giá trị | Nhãn | Nguồn |
|---|---|---|---|
| Nguyên nhân nóng | firmware cũ không ngắt xung PWM: kẹp giữ vật hoặc chạm chốt chặn thì servo bị ép liên tục; lệnh đóng cũ 175° ứng xung ≈ 2,74 ms, vượt dải 0,5–2,5 ms của MG996R | CODE (chú thích) | `robot_arm_4dof.ino:16-18,21`; `README.md` mục 6 |
| Giới hạn kẹp hiện tại | **160°** (xung ≈ 2,56 ms, **hơi vượt** dải danh định 2,5 ms); nâng từ 150° lên 160° theo chủ máy vì ở 150° khe giữa hai ngón bằng bề rộng nắp cốc nên không siết được; vẫn có tự nhả xung | CODE + ĐO | `robot_arm_4dof.ino:21`; ghi chú phiên 02/11 21:4x |
| Ngắt xung tự động | kẹp **mở hết cỡ (đúng 95°)** 5 giây không có lệnh kẹp → ngắt xung; kẹp **đã khép (> 95°)** quá 60 giây → ngắt xung (vật có thể tuột) | CODE | `robot_arm_4dof.ino:22-23,191-201` |
| Phím nghỉ | `X` nghỉ servo kẹp ngay; **`Z` nghỉ cả 4 servo** (cánh tay tự sụp theo trọng lực: hạ đầu kẹp tựa xuống chỗ trống trước); chỉ phím di chuyển mới cấp xung lại | CODE | `robot_arm_4dof.ino:160-176`; `README.md` mục 6 |
| Cờ trong JSON | `relax` (kẹp nghỉ), `armrelax` (ba servo còn lại nghỉ) | CODE | `robot_arm_4dof.ino:78-82` |
| Chương trình biết tay đang nghỉ | trạng thái `relaxed` (`CANH TAY DANG NGHI`); bấm `Z` khi firmware cũ chưa có phím Z thì cảnh báo `FIRMWARE CU KHONG CO PHIM Z` | CODE | `control.py:278,482,570-574`; `tests/test_control.py:210` |
| **Đã nạp và kiểm** | firmware cuối (phím Z, bước 2°/5°, giới hạn 160°) nạp lúc 21:42:45 và 21:54:48 ngày 02/11, kiểm trên mạch thật: banner kết thúc `+ Z (nghi het)`, JSON có `armrelax`. Trước đó (17:35) bản chống nóng kênh kẹp: `relax` chuyển 0 → 1 sau 5 giây ở 95° | ĐO (ghi chú phiên) | memory `project-iot-arduino-firmware`; `robot_arm_4dof.ino:99` |
| Kẹp đã ngắt xung thì tự khép | khi PWM kênh kẹp bị cắt, hai hàm rơi thành hình chữ V hẹp (khe ≈ 1–2 cm), trong khi kẹp có xung ở 95° thì mở rộng ≈ 7 cm. Hệ quả: ngắt xung sau 5 s ở 95° làm hàm sập nếu không bấm `J` lại | ƯỚC LƯỢNG (ảnh zoom ±30%) | ghi chú phiên 02/11 20:18 |
| Nhiệt độ servo | **chưa đo**; chưa có số "nguội đi bao nhiêu độ" | CHƯA | — |
| Màn hình cảnh báo "GIU 31s" | **không còn** (thuộc giao diện cũ đã bỏ) | — | `screen.py` không có |

## 7. Buổi thử trên cánh tay thật, 02/11/2026

| Mục | Giá trị | Nhãn | Nguồn |
|---|---|---|---|
| Thử 18:10–18:28 | một hướng tiếp cận, dừng trước khi kẹp. Kết luận "cốc ở mép tầm với, dời cốc 3 cm" **đã bị rút lại**; ảnh buổi này không dùng | — | ghi chú phiên (đính chính 20:25) |
| **Kẹp bằng bàn phím 20:32–20:36** | người bấm phím theo hình hai camera (và màn hình bản cũ): cốc đỏ ở giữa giấy được kẹp, chuyển sang trái, đặt xuống, lặp lại nhiều lần; cốc đổ khoảng 3 lần và được dựng lại bằng tay | ĐO | ảnh `demo_*` (khung cắt từ video, mỗi cặp cách 10 giây: 20:32:52, 20:33:02, 20:33:12) |
| Góc servo lúc kẹp | đế ≈ 85°, vai ≈ 60–65°, khuỷu ≈ 85–90°, kẹp ≈ 145–150°; đế ≈ 60° khi mang cốc sang trái (đọc từ màn hình bản cũ) | ĐO | ghi chú phiên 02/11 20:32–20:35 |
| Tay kẹp không giữ chắc cốc thon | ở 150° khe giữa hai ngón bằng bề rộng nắp cốc (≈ 3,9 cm) nên cốc bị đẩy ra; cốc thon dần xuống đáy nên hai mặt kẹp đẩy nó ra "như hạt dưa"; **nâng giới hạn lên 160° cũng chưa giữ chắc**. Cách chữa đề xuất: dán ma sát (băng keo hai mặt / xốp mỏng) lên mặt trong hai ngón, hoặc dùng vật thân thẳng | ĐO + CODE (tài liệu) | `README.md` mục 6; `robot_arm_4dof.ino:21`; ghi chú phiên 21:42–21:58 |
| **Quyết định của đề tài** | vì vậy "thành công" chỉ xét **ba góc servo đế / vai / khuỷu** tới góc gợi ý, kẹp không tính | QUYẾT ĐỊNH | `success.py:9-10`; ghi chú phiên 22:00 |
| Tự động | **không**: app chỉ gửi phím khi người bấm | CODE | mục 3 |
| Tỉ lệ thành công | **chưa đo**; kế hoạch 28/10 đặt mục tiêu ≥ 80% trên 30 lần, chưa chạy | CHƯA | kế hoạch PDF; không có thư mục `logs/` |

## 8. Mô hình lệch cánh tay thật và hiệu chỉnh bằng các lần "ôm" cốc

| Mục | Giá trị | Nhãn | Nguồn |
|---|---|---|---|
| **Mô hình mặc định lệch** | ba lần ôm đầu (người bấm phím cho hai ngón bao quanh cốc): servo [85, 60, 90] lúc 20:32:50, [80, 70, 75] lúc 20:46, [75, 85, 50] lúc 21:03:35. Mô hình mặc định đặt đầu kẹp ở (12,6; 17,7), (10,6; 16,3), (9,3; 13,4) cm, còn cốc thật ở (16,9; 14,4), (13,3; 14,0), (10,8; 7,7) cm → lệch **5,4 · 3,5 · 5,9 cm**, luôn về một phía (hệ thống) | CODE (tính lại 02/11 23:07) + ĐO (vị trí cốc đo bằng camera) | mục 16; ghi chú phiên 02/11 |
| Cùng ý với màn hình cũ | màn hình bản cũ lúc 20:32:05 báo `Sai so dau kep: 56 mm` khi cốc đã nằm giữa hai ngón kẹp thật | ĐO | ảnh `ui_status_bar.png` (không dùng trên slide) |
| Nguyên nhân (đã tìm ra) | (1) vị trí và hướng đế lệch so với mặc định; (2) hai góc chuẩn vai / khuỷu khi servo ở 90° khác 45° / −45° (phụ thuộc cách lắp cần servo, thước không đo được); (3) **càng kẹp gắn cứng vào khâu khuỷu** nên độ lệch của điểm kẹp quay theo khâu đó, trong khi mô hình cũ giữ độ lệch cố định theo phương ngang | CODE (tài liệu) | `calibration.py:16-20`; `README.md` mục 4 |
| Cách sửa | **hiệu chỉnh bằng trình diễn**: người đưa hai ngón kẹp bao quanh cốc, ghi góc ba servo + vị trí cốc; từ ≥ 2 mẫu cách nhau ≥ 5 cm, khớp 5 thông số (x, y, hướng của đế; hai góc chuẩn vai, khuỷu) bằng Levenberg–Marquardt thuần numpy; kèm mô hình càng kẹp quay theo khâu khuỷu (gộp vào chiều dài khâu 3); từ chối nếu sai số sau khớp > 30 mm | CODE | `arm_fit.py:1-45`; `calibration.py:16-20` |
| **Kết quả** | **10 mẫu**, sai số khớp (RMS trong mặt phẳng) **8,5 mm**, bỏ-một-mẫu (leave-one-out) **11,6 mm** | CODE (file) | `calibration.json` mục `arm_fit` |
| Giá trị đã lưu | đế (13,83; 31,67) cm, hướng −92,4°; θ₂@90 = 60,2° (mặc định 45°), θ₃@90 = −58,6° (mặc định −45°); càng kẹp gộp vào khâu 3: L₃ = 183,7 mm, L₄ᵣ = L₄z = 0 (mặc định 100 / 65 / 25 mm) | CODE (file) | `calibration.json`; `calibration.py:77-105` |
| **Hiệu lực hạn chế** | chỉ đúng với tờ giấy dùng lúc đo (tờ cũ in nhỏ hơn đúng cỡ ≈ 4,5%, nên mọi số cm đo trên đó lớn hơn thật ≈ 4,7%) và với vị trí robot lúc đo; **đổi tờ giấy hoặc dời robot thì phải đo lại** | CODE + ĐO | `README.md` mục 4; `calibration.json` mục `arm_fit.to_giay` |
| Ví dụ sau hiệu chỉnh | cốc (20,1; 7,4) → gợi ý [74°, 58°, 90°]. Hai tư thế người căn tay quanh cốc ở chỗ đó, [72, 54, 92] và [74, 60, 86], cho đầu kẹp theo mô hình ở (20,6; 7,5) và (19,6; 7,8) cm, cách cốc **0,5 và 0,6 cm**; gợi ý lệch chúng 0–4° mỗi servo. Chưa rõ hai tư thế này có nằm trong 10 mẫu khớp không: **chỉ nói "gần", không nói "kiểm độc lập"** | CODE (tính lại) + ĐO (tư thế, ghi chú phiên) | mục 16 |
| Ảnh minh họa (slide 11) | khung cam NGANG lúc ôm cốc 21:03:35, servo [75, 85, 50]: dấu mô hình mặc định cách cốc ≈ **5,3 cm**, dấu mô hình đã hiệu chỉnh ≈ **0,95 cm** (cốc đo từ cam ngang, ± 1 cm). Lần ôm này nằm trong bộ mẫu khớp: **không phải kiểm độc lập**; số 5,9 cm ở hàng trên dùng vị trí cốc ghi lúc ôm (cùng cỡ) | ĐO (ảnh) | ảnh `calib_before_after_side.jpg`; `slides/tools/make_screen_images.py` |
| Gợi ý trên ảnh 20:27 so với tư thế thật | gợi ý [88°, 60°, 84°] cho cốc ở (16,5; 13,8) cm, so với tư thế người thật sự ôm cốc lúc 20:32:50: [85°, 60°, 90°] (đọc từ màn hình bản cũ): lệch 3° / 0° / 6°. **Chưa rõ lần ôm 20:32 có trong 10 mẫu khớp không**: chỉ nói "gần", không nói "kiểm độc lập" | MÔ PHỎNG + ĐO | ảnh `ui_screen_before.png`; mục 7 |
| Mô phỏng | cánh tay giả lập có độ lệch biết trước: sai số trên vùng làm việc **> 60 mm trước, < 35 mm sau** khi có 3 mẫu (ngưỡng trong test) | MÔ PHỎNG | `tests/test_arm_fit.py:80-91` |
| Công cụ khớp lại | chạy **ngoài** ứng dụng: `arm_fit.fit_geometry(samples, ARM_CONFIG, control.predict_tip)`, mỗi mẫu `{"servo": (đế, vai, khuỷu), "x_cm", "y_cm", "z_mm"}`; phím `Y` / `E` trong ứng dụng **đã bỏ** | CODE | `README.md` mục 4; `arm_fit.py` |
| **Chưa làm** | chưa thử chuỗi đầy đủ trên cánh tay thật: bấm đúng theo gợi ý của bản mới rồi xem hai ngón có bao quanh cốc không; chưa hiệu chỉnh lại cho tờ giấy mới | CHƯA | — |

## 9. Tay kẹp phi tuyến

| Mục | Giá trị | Nhãn | Nguồn |
|---|---|---|---|
| Cơ cấu | kẹp song song hai ngón, **phi tuyến** theo góc servo | ĐO | ảnh `hw_gripper_95_vs_125.jpg` |
| Số đo | mở hết cỡ (95°): hai hàm cách ≈ 7,5 cm; từ 95° lên 125°: ngón vươn ra trước ≈ 1,7 cm nhưng khe chỉ hẹp ≈ 0,5 cm | ĐO (3 điểm 95 / 110 / 125°) | `README.md` mục 6; ghi chú phiên 02/11 18:2x |
| Ảnh zoom từ trên | khe giữa hai đầu ngón ≈ 7 cm ở 95°, ≈ 5–6 cm ở 125°, ≈ 3,3–4 cm ở 150° (độ lớn biểu kiến, ± 30% do phối cảnh) | ƯỚC LƯỢNG | ghi chú phiên 02/11 20:20 |
| Vật rộng ≈ 4 cm | (như cốc đỏ) bị đẩy ra khi khép tới 150–160° | ĐO | `README.md` mục 6 |
| Không nói | "cần 155–165° để kẹp" là ngoại suy từ 3 điểm, **chưa được xác nhận**; giới hạn 160° là quyết định của chủ máy, không phải góc kẹp "đúng" | — | mục 14 |

## 10. Lỗi tích hợp khó thấy

| Mục | Giá trị | Nhãn | Nguồn |
|---|---|---|---|
| Chỉ số camera trên macOS | `cv2.VideoCapture(i)` sắp camera theo `uniqueID`; danh sách của AVFoundation / `system_profiler` xếp camera "dùng gần nhất" lên đầu nên đổi thứ tự giữa các lần chạy (đã thấy: lúc `[OBSBOT, MacBook]`, lúc `[MacBook, OBSBOT]`; có lúc hai khung cùng là OBSBOT). Cách xử lý: tìm camera theo **tên**, đổi sang chỉ số theo đúng quy tắc sắp `uniqueID` ngay trước mỗi lần mở | ĐO + CODE | `cameras.py:4-12,75-115`; `README.md` mục 5; `tests/test_cameras.py:135` |
| Arduino Uno tự reset | mở rồi đóng cổng USB làm đường DTR hạ xuống rồi nâng lên → Uno reset → 4 servo giật về 90/90/90/95. Thường do **một chương trình thứ hai** mở cổng khi `main.py` đang chạy. Cách xử lý: không đóng cổng khi đọc lỗi thoáng qua; mở tay cầm mới **trước** khi đóng tay cầm cũ; nhận ra reset khi thời gian chạy `t` quay về 0 và báo `ARDUINO VUA RESET` | ĐO + CODE | `control.py:345-352,396-446`; `README.md` mục 6; `tests/test_serial_link.py:96-140` |

## 11. Mã nguồn và kiểm thử

| Mục | Giá trị | Nhãn | Nguồn |
|---|---|---|---|
| Kiểm thử | **109 test** pass trong 8,7 giây: `test_control` 29, `test_vision` 15, `test_cameras` 13, `test_calibration` 11, `test_serial_link` 9, `test_main` 8, `test_success` 7, `test_robustness` 6, `test_arm_fit` 5, `test_screen` 4, `test_end_to_end` 2 (11 tệp test) | ĐO | `.venv/bin/python -m pytest -q`, 03/11 20:15 |
| Không chạm phần cứng | không test nào đụng camera, cổng Serial hay `calibration.json` thật; cảnh dựng bằng camera giả lập có đáp án chính xác | CODE | `README.md` mục 7 |
| Quy mô | 8 module Python ≈ **2 690 dòng** (`main.py` 334 · `control.py` 620 · `success.py` 75 · `screen.py` 271 · `vision.py` 691 · `cameras.py` 415 · `calibration.py` 140 · `arm_fit.py` 141) + firmware 208 dòng + `generate_aruco_a4.py` 225 dòng + 11 file test ≈ 1 890 dòng | CODE | `wc -l` (03/11) |
| Chạy không cần phần cứng | `main.py --top a.jpg --side b.jpg --no-serial --headless --seconds 10 --dump-dir out/` → `dual_view.png`, ảnh chú thích của 2 camera, `summary.json` (có `nhom_1_dieu_khien` và `nhom_2_success`) | CODE | `README.md` mục 7; `main.py:280-304` |
| Mỗi khung hình là ba dòng | `plan = control.update(tracker.objects)` → `result = success.update(plan)` → `build_screen(…, plan, result)` | CODE | `README.md` mục 3; `main.py:171-174` |
| Repo | `github.com/DuongNAD/Project_IoT`: nhánh `main` (`e3f2d85`, 03/11/2026) đã có bản hai nhóm (`control.py`, `success.py`, `screen.py`, `vision.py`, `cameras.py`, `calibration.py`, `arm_fit.py`, `tests/`, `README.md`) và phần gộp từ máy Windows. `captures/`, `calibration.json` và `slides/assets/real/` nằm trong `.gitignore`; riêng `slides/Project_IoT_ThuyetTrinh.pptx`, `.pdf` và `slides/preview/` **đang được git theo dõi và có nhúng ảnh thật** | CODE | `git log`; `.gitignore`; `slides/.gitignore` |
| Sao lưu bản trước khi đơn giản hóa | `~/Documents/project/Project_IoT_backup_truoc_don_gian_hoa_2026-11-02.tgz` (14 MB, ngoài repo) | CODE | `README.md` mục 9 |

## 12. Đã bỏ khi đơn giản hóa (02/11, khoảng 22:00–22:50)

Mục đích: mã và màn hình giải thích được trong một phút. Chỉ nhắc ở phụ lục I như lịch sử, **không** như tính năng hiện có.

| Đã bỏ | Thay bằng |
|---|---|
| quy trình gắp 5 bước (điểm chờ +60 mm, hạ, đóng kẹp, nâng +80 mm, kiểm 3 giây) | một đích duy nhất: ba servo tới góc gợi ý |
| kiểm tra thành công S1 (cam NGANG thấy vật nhấc ≥ 20 mm) và S2 (cam TRÊN thấy chỗ cũ không còn nguyên) | `success.py`: ba góc servo trong ±2°, giữ 1 s |
| `logs/attempts.csv` | số lần thành công đếm trên màn hình (`Thanh cong: N lan`) |
| Auto-Step (phím `P`, tự gửi phím) | app chỉ gửi phím người bấm |
| cửa sổ HƯỚNG DẪN GẮP và thanh gợi ý 4 servo | màn hình hai phần (điều khiển → success) |
| ước lượng tư thế cam NGANG (tiêu cự, độ cao, góc ngẩng) | không cần: vị trí vật chỉ lấy từ homography của tờ giấy |
| YOLO là mặc định | tách màu là mặc định; YOLO tùy chọn `--yolo` |
| hiệu chỉnh trong chương trình bằng phím `Y` / `E` | công cụ ngoài `arm_fit.py`, kết quả lưu `calibration.json` |

Nguồn: `README.md` mục 9; các tệp bị xóa khỏi thư mục làm việc: `grasp_assist_4dof.py`, `guide_screen.py`, `test_ik.py` (`git status`).

## 13. Kế hoạch ngày 28/10 so với thực tế

Kế hoạch (`Kế hoạch Camera & Gợi ý gắp — Cánh tay robot IoT.pdf`, 28/10/2026) đặt giả định phần cứng chưa biết; phần cứng thật khác:

| | Kế hoạch 28/10 | Thực tế 02/11 |
|---|---|---|
| Vi điều khiển | ESP32 | Arduino Uno |
| Servo | 6 (có cổ tay gập, cổ tay xoay) | 4 (đế, vai, khuỷu, kẹp) |
| Camera | 2 webcam USB 1280×720 | OBSBOT Meet SE + MacBook, 1920×1080 |
| Giao tiếp | USB Serial 115200 baud + MQTT | USB Serial 9600 baud (+ HC-05 tùy chọn); **không có MQTT** |
| Nhận diện | ArUco chính; mở rộng YOLO26n-seg | ArUco 4 góc tờ giấy + tách màu (mặc định) + YOLO11s tùy chọn |
| Giám sát | dashboard Node-RED / web trên điện thoại | màn hình OpenCV hai phần (lệnh bấm → đã tới chưa) |
| Xác nhận | S1 + S2 (+ S3 cảm biến lực FSR) | **ba góc servo tới góc gợi ý**; không dùng camera để xác nhận gắp, **không có FSR** |
| Mục tiêu đo | ≥ 80% thành công / 30 lần; sai số định vị ≤ 3 mm; kết luận ≤ 2 s; ≥ 20 fps | **chưa đo** (sai số khớp mô hình 8,5 mm là số khác, xem mục 8) |

Kết quả `grep` MQTT, paho, ESP32, FSR, dashboard trong mã nguồn (`*.py`, `*.ino`, `*.toml`, `*.sh`): **không có kết quả**.

---

## 14. CẤM NÓI (và lý do)

| Không được viết hoặc nói | Vì sao | Được nói thay bằng |
|---|---|---|
| "Robot tự động gắp", "tự động hoàn toàn" | app chỉ cho biết bấm phím nào; người bấm; chế độ tự gửi phím đã bỏ | "Hệ thống chỉ cho bạn bấm phím nào, mấy lần; người bấm" |
| "Gắp thành công" cho một lần XONG | XONG = ba góc servo tới góc gợi ý (kẹp không tính, góc là góc lệnh); không có camera xác nhận vật được nhấc | "Thành công = ba servo tới góc gợi ý" |
| Bất kỳ **tỉ lệ thành công** nào (VD "9/10", "90%") | chưa có lần đếm nào trên cánh tay thật | "Chưa đo" |
| "Mô hình đã chính xác dưới 1 cm" | 8,5 mm là sai số khớp trên **chính 10 mẫu** (bỏ-một-mẫu 11,6 mm), chỉ cho tờ giấy cũ và vị trí robot lúc đo; chưa kiểm bằng cách bấm theo gợi ý trên cánh tay thật | "Sai số khớp 8,5 mm trên 10 lần ôm (bỏ-một-mẫu 11,6 mm); chưa thử bấm theo gợi ý trên cánh tay thật" |
| "Hiệu chỉnh dùng cho mọi tờ giấy / mọi vị trí robot" | `calibration.json` gắn với tờ giấy và chỗ đặt robot lúc đo | "Đổi tờ giấy hoặc dời robot thì phải đo lại" |
| "Servo hết nóng", "nhiệt độ giảm N°C" | chưa đo nhiệt độ | "Đã thêm ngắt xung, giới hạn góc và phím nghỉ; chưa đo nhiệt độ" |
| "Kẹp giữ cốc chắc", "nhấc cốc ổn định" | cốc thon bị đẩy ra ở 150–160°; cốc đổ khoảng 3 lần trong buổi 20:32–20:36 | "Kẹp chưa giữ chắc cốc thon nên đề tài chỉ xét ba góc servo" |
| S1/S2, "5 bước", Auto-Step, `attempts.csv`, phím `Y`/`E`, cửa sổ HƯỚNG DẪN GẮP như tính năng đang có | đã bỏ khi đơn giản hóa | chỉ nhắc ở phụ lục I như lịch sử, có sao lưu |
| "Phím `A` quay đế sang trái" | trên màn hình và slide, trái / phải **nhìn theo cam NGANG (MacBook)**: `A` = sang phải, `D` = sang trái | "A sang phải, D sang trái, nhìn theo cam ngang" |
| MQTT, dashboard, ESP32, 6 servo, FSR, YOLO26 là "đã làm" | chỉ có trong kế hoạch | chỉ nhắc ở phụ lục J như "điều chỉnh so với kế hoạch" |
| "YOLO nhận diện chính xác" / "tìm vật bằng YOLO" như cách mặc định | YOLO tùy chọn, mặc định tắt; bản COCO chưa fine-tune, có nhận nhầm | "Mặc định tách màu; YOLO11 tùy chọn, có nhận nhầm nên chọn vật bằng TAB" |
| "Cốc nằm ở mép tầm với", "dời cốc gần đế 3 cm" | đã bị đính chính 20:25 | không nhắc |
| "Cần 155–165° để kẹp cốc" | ngoại suy từ 3 điểm, chưa xác nhận | "Giới hạn kẹp 160°; cốc thon vẫn bị đẩy ra" |
| "Phím Z chưa nạp" | **đã nạp và kiểm** lúc 21:42 và 21:54 | "Phím Z (nghỉ cả 4 servo) đã nạp và kiểm trên mạch" |
| Ảnh AI ở slide kết quả hay bằng chứng | gây hiểu nhầm | ảnh AI chỉ ở slide 2 và 14 và luôn ghi "Minh họa (AI)" |
| Gọi ảnh `ui_screen_*` là "lần chạy trực tiếp" | đó là màn hình thật chạy trên ảnh đã lưu, cánh tay mô phỏng | "Chạy trên ảnh thật đã lưu, cánh tay mô phỏng" |

## 15. Cần bạn xác nhận (không suy ra được từ máy)

1. Tên môn học hoặc sự kiện, ngày giờ, địa điểm, thời lượng được phép.
2. Tên và vai trò các thành viên; ai nói slide nào; **"nhóm 1 · điều khiển" và "nhóm 2 · success" là hai phần mã hay hai nhóm người?** (slide gọi chúng là nhóm 1 và nhóm 2).
3. ~~Đã commit và push mã nguồn mới lên GitHub chưa?~~ Đã xong: `main` = `e3f2d85` (03/11/2026) có bản hai nhóm; slide 15 trỏ tới repo.
4. Giảng viên có **bắt buộc dashboard IoT / MQTT** hoặc **mô hình học máy** không (kế hoạch 28/10 còn hỏi điều này).
5. **Đã chạy bản mới trực tiếp với cánh tay thật chưa?** Nếu rồi, cho mình số `Thanh cong` và ảnh màn hình để đổi các dòng "chưa" ở slide 9, 11, 13.
6. Tờ giấy đang dùng là tờ cũ (in nhỏ) hay tờ mới? Hiệu chỉnh hiện tại chỉ đúng cho tờ cũ.
7. Có quay được video 20–30 giây không (slide 10).

## 16. Tái tạo các số tính được

Chạy từ thư mục dự án; chỉ đọc mã và `calibration.json`, **không** đụng camera hay cổng USB:

```bash
.venv/bin/python -B - <<'EOF'
import math, control as c
from calibration import apply_calibration

# 1. Mô hình MẶC ĐỊNH (chưa nạp calibration.json) trên ba lần ôm đầu: servo -> đầu kẹp theo mô hình, so với cốc đo bằng camera
hugs = {"20:32": ((85, 60, 90), (16.9, 14.4)), "20:46": ((80, 70, 75), (13.3, 14.0)), "21:03": ((75, 85, 50), (10.8, 7.7))}
for name, (servo, cup) in hugs.items():
    x, y, z = c.predict_tip(servo)
    print(name, servo, "-> (%.1f, %.1f) cm; cốc %s; lệch %.1f cm" % (x, y, cup, math.hypot(x - cup[0], y - cup[1])))   # 5.4, 3.5, 5.9

# 2. Nạp calibration.json rồi tính gợi ý cho cốc ở (20,1; 7,4) cm
apply_calibration(c.ARM_CONFIG)
rx, ry = c.table_cm_to_robot_mm(20.1, 7.4)                                  # -> 240, -73 (mm)
ik = c.ik_4dof_joint(rx, ry, c.GRASP_Z_MM)
goal = c.joint_to_servo(ik["theta1_deg"], ik["theta2_deg"], ik["theta3_deg"])
print("gợi ý", goal)                                                        # [74, 58, 90]
for m in c.plan_moves([90, 90, 90, 95], goal):
    print(m.label, m.key, m.steps, m.words, m.degrees)                      # D x8 (16°), S x16 (32°), khuỷu không phím
for pose in ((72, 54, 92), (74, 60, 86)):
    print(pose, "-> (%.1f, %.1f) cm" % c.predict_tip(pose)[:2])             # (20.6, 7.5) và (19.6, 7.8)
EOF
```

## 17. Khối kiểm tự động (đọc bởi `tools/check_facts.py`)

Mỗi dòng `tên = giá trị` được so với mã hiện tại. Sửa mã thì chạy `check_facts.py`; dòng nào báo `LỆCH` thì sửa ở **đây trước**, rồi sửa `01_KICH_BAN_SLIDE.md`.

```facts
STEP_ARM = 2
STEP_GRIP = 5
GRIP_CLOSE_LIMIT = 160
GRIP_IDLE_RELAX_MS = 5000
GRIP_HOLD_MAX_MS = 60000
JSON_PERIOD_MS = 200
TOLERANCE_STEPS = 1
HOLD_S = 1.0
SERVO_STEPS = base:2 shoulder:2 elbow:2 grip:5
SERVO_LIMITS_GRIP = 95 160
GRASP_Z_MM = 25.0
ARM_DEFAULT = d1:70 L2:105 L3:100 L4_r:65 L4_z:25 theta2_90:45 theta3_90:-45
PARALLAX_CAM_HEIGHT_CM = 46.0
CALIB_BASE = 13.83 31.67 -92.4
CALIB_THETA = 60.2 -58.6
CALIB_CLAW = 183.7 0.0 0.0
CALIB_FIT = n:10 rms:8.5 loo:11.6
PY_LINES = 2687
FIRMWARE_LINES = 208
TESTS = 109
HUG_ERR_CM = 5.4 3.5 5.9
GOAL_CUP_20_1_7_4 = 74 58 90
KEYS_FROM_HOME = d:8 s:16
```

Ba dòng cuối (và `TESTS`) chỉ được kiểm khi chạy `check_facts.py --deep`.
