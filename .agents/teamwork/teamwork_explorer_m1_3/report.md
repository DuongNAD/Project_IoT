# BÁO CÁO ĐIỀU TRA GIAO DIỆN & KẾ HOẠCH TRIỂN KHAI 15 SLIDE KỸ THUẬT
**Dự án:** Hệ thống Hỗ trợ Gắp vật Cánh tay Robot 4-DOF (Dual Camera, ArUco, YOLO11 & Động học ngược)  
**Agent thực hiện:** `teamwork_explorer_m1_3`  
**Ngày thực hiện:** 2026-11-03  
**Chế độ tuân thủ:** Integrity Mode (Không sửa mã nguồn, không bịa số liệu, giữ nguyên placeholder `[...]`)

---

## MỤC LỤC
1. [TỔNG QUAN ĐIỀU TRA & KẾT QUẢ CỐT LÕI](#1-tổng-quan-điều-tra--kết-quả-cốt-lõi)
2. [ĐIỀU TRA CHI TIẾT GIAO DIỆN VÀ HỆ MÀU (guide_screen.py)](#2-điều-tra-chi-tiết-giao-diện-và-hệ-màu-guide_screenpy)
   - 2.1 Bố cục cửa sổ "HƯỚNG DẪN GẮP" (1280 × 800)
   - 2.2 Hàm `build_guide_screen()` và cây hàm dựng giao diện
   - 2.3 Bảng quy đổi hệ màu (OpenCV BGR → RGB Hex)
   - 2.4 Thiết kế nút phím "Keycap" và Bảng phím tắt toàn diện
3. [ĐIỀU TRA BỘ KIỂM THỬ VÀ SINH ẢNH GIAO DIỆN MẪU (test_ik.py)](#3-điều-tra-bộ-kiểm-thử-và-sinh-ảnh-giao-diện-mẫu-test_ikpy)
   - 3.1 Kết quả chạy thực tế 10 bài kiểm thử của `test_ik.py`
   - 3.2 Cơ chế `fake_assist()` và phương pháp sinh ảnh `guide_screen_sample.png` cho M2
   - 3.3 Trạng thái nhật ký thực nghiệm (`logs/attempts.csv`)
4. [KẾ HOẠCH TRIỂN KHAI CHI TIẾT 15 SLIDE THUYẾT TRÌNH (Slide 1 → 15)](#4-kế-hoạch-triển-khai-chi-tiết-15-slide-thuyết-trình-slide-1--15)
   - Slide 1: Trang tiêu đề dự án
   - Slide 2: Đặt vấn đề và Mục tiêu giải pháp
   - Slide 3: Kiến trúc Phần cứng & Cấu hình thiết bị
   - Slide 4: Kiến trúc Phần mềm & Luồng dữ liệu thời gian thực
   - Slide 5: Hệ tọa độ bàn làm việc & Lưới ArUco tờ A4
   - Slide 6: Nhận diện vật thể kết hợp YOLO11s và ArUco
   - Slide 7: Động học thuận và Động học ngược giải tích 4-DOF
   - Slide 8: Chuyển đổi tọa độ A4 sang Hệ gốc Robot & Cảnh báo an toàn
   - Slide 9: Quy trình gắp 5 bước & Hướng dẫn phím bấm an toàn
   - Slide 10: Tự động xác nhận kết quả gắp 2 Camera độc lập
   - Slide 11: Giao thức giao tiếp Arduino & Đồng bộ thời gian thực
   - Slide 12: Thiết kế Giao diện Người dùng (HUD & Cửa sổ Hướng dẫn)
   - Slide 13: Kết quả kiểm thử động học & Thực nghiệm hệ thống
   - Slide 14: Đánh giá hạn chế & Hướng phát triển mở rộng
   - Slide 15: Tổng kết đề tài & Phiên hỏi đáp (Q&A)
5. [TỔNG HỢP CÁC PLACEHOLDER `[...]` VÀ VIỆC CẦN LÀM CỦA NHÓM SINH VIÊN](#5-tổng-hợp-các-placeholder--và-việc-cần-làm-của-nhóm-sinh-viên)

---

## 1. TỔNG QUAN ĐIỀU TRA & KẾT QUẢ CỐT LÕI

Quá trình điều tra trực tiếp toàn bộ mã nguồn trong workspace (`guide_screen.py`, `test_ik.py`, `grasp_assist_4dof.py`, `main.py`, `generate_aruco_a4.py`, `robot_arm_4dof.ino`) đã xác định được:
1. **Giao diện người dùng:** Toàn bộ hệ thống giao diện được định nghĩa theo phong cách Dark Theme hiện đại với độ tương phản cao, kích thước chuẩn 1280 × 800 px gồm 2 vùng độc lập: nửa trên (1280 × 400) hiển thị 2 camera song song, nửa dưới (1280 × 400) là bảng điều khiển và kết quả gắp.
2. **Hệ màu nhận diện:** Chuyển đổi chính xác 100% từ tuple BGR của OpenCV sang mã RGB Hex theo chuẩn công nghiệp: nền `#191B1E`, thẻ khối `#272A2E`, viền `#464C52`, chữ chính `#F5F5F5`, chữ phụ `#9BA0A5`, nhấn cam `#FFB928`, xanh lá `#5AD76E`, đỏ `#F55555`.
3. **Kết quả kiểm thử thực tế:** Chạy `test_ik.py` đạt 10/10 bài test thành công tuyệt đối (`exit code 0`), kiểm thử 455 điểm 3D trong tầm với có sai số động học $0.000000\text{ mm}$ ($< 0.1\text{ mm}$).
4. **Nhật ký thực nghiệm:** File `logs/attempts.csv` hiện chưa tồn tại trong workspace. Do đó, toàn bộ số liệu thống kê thực nghiệm về số lần gắp thật và tỉ lệ thành công được giữ nguyên ở dạng placeholder `[...]` theo đúng nguyên tắc bảo toàn tính trung thực của R1 và R4.
5. **Kế hoạch 15 slide:** Đã hoàn thiện cấu trúc 15 slide chi tiết theo đúng dàn ý R1, kèm speaker notes tiếng Việt tự nhiên (3–5 câu/slide), đặc tả hình vẽ/sơ đồ khối chuẩn PowerPoint shape, và dẫn chứng chính xác từng hằng số, công thức, phím bấm từ mã nguồn.

---

## 2. ĐIỀU TRA CHI TIẾT GIAO DIỆN VÀ HỆ MÀU (`guide_screen.py`)

### 2.1 Bố cục cửa sổ "HƯỚNG DẪN GẮP" (1280 × 800)
Tệp `guide_screen.py` định nghĩa cửa sổ độc lập mang tên `GUIDE_WINDOW = "HUONG DAN GAP: 2 Cam + Thao tac (bam G de an/hien)"`.
- **Kích thước toàn khung:** Chiều rộng `GUIDE_W = 1280` px, tổng chiều cao `800` px gồm:
  - Khung 2 Camera phía trên: Chiều cao `CAM_H = 400` px.
  - Bảng thao tác phía dưới: Chiều cao `PANEL_H = 400` px.
- **Nửa trên (2 Camera 1280 × 400):**
  - Ghép ngang (`cv2.hconcat`) 2 ô hình camera, mỗi ô rộng $1280 / 2 = 640$ px, cao 400 px.
  - Camera bên trái (`view_left`): `CAM 1: LAPTOP (nhin ngang)` — góc nhìn ngang kiểm tra độ cao nâng vật.
  - Camera bên phải (`view_right`): `CAM 2: DIEN THOAI (nhin tu tren)` — góc nhìn thẳng đứng nhận diện vị trí vật và lưới A4.
  - Đường phân cách giữa 2 camera: Đường kẻ dọc màu trắng dày 2 px tại $X = 640$ (`cv2.line(cams, (half, 0), (half, CAM_H), (255, 255, 255), 2)`).
  - Khung tiêu đề camera: Ô chữ nhật nền đen góc trên bên trái, chữ xanh lá nhạt `(120, 255, 120)`.
- **Nửa dưới (Bảng thao tác 1280 × 400):** Được dựng bởi `render_guide_panel(info)` với 6 phân khu chức năng:
  1. *Thanh 5 bước gắp (`draw_stepper`, $Y=8, H=40$):* Chia đều 5 viên thuốc (pill) bo góc tròn ứng với 5 bước (`DIEM CHO`, `HA XUONG`, `DONG KEP`, `NANG LEN`, `KIEM TRA`).
  2. *Dòng lệnh thao tác chính (`draw_instruction`, $Y=54$):* Chữ cỡ lớn (`FONT_BIG`, tỉ lệ 0.95), hiển thị hành động trọng tâm hiện tại và số lần bấm phím còn lại (`Con X lan bam`).
  3. *Dòng thông tin mục tiêu (`draw_target_line`, $Y=94$):* Tên vật, tọa độ robot $(X, Y, Z)$ mm bên trái; cảnh báo tầm với (`TRONG TAM VOI` / `NGOAI TAM VOI!` / `CANH BAO:... cham gioi han servo`) bên phải.
  4. *Khối gợi ý hành động 4 servo (`draw_action_rows`, $X=12, Y=118, W=800$):* Gồm 4 hàng tương ứng với 4 khớp theo thứ tự an toàn `ROW_ORDER = (0, 3, 1, 2)` (Đế → Kẹp → Vai → Khuỷu).
  5. *Thẻ kết quả gắp (`draw_result_card`, $X=824, Y=118, W=444, H=228$):* Hiển thị tiến độ kiểm tra 2 camera thời gian thực (ở bước 5) hoặc kết quả gắp mới nhất (`GAP THANH CONG` / `GAP THAT BAI`) cùng thống kê tổng số lần.
  6. *Thanh chân trang (`draw_footer`, $Y=352$):* Trạng thái cổng kết nối Arduino USB/Bluetooth, chế độ tự động (Auto-Step P), số thứ tự vật, sai số đầu kẹp và dải phím tắt hướng dẫn.

### 2.2 Hàm `build_guide_screen()` và cây hàm dựng giao diện
Hàm điều phối trung tâm:
```python
def build_guide_screen(view_left, view_right, info,
                       titles=("CAM 1: LAPTOP (nhin ngang)", "CAM 2: DIEN THOAI (nhin tu tren)"))
```
**Tham số đầu vào:**
- `view_left`: Khung hình từ webcam laptop (numpy array BGR).
- `view_right`: Khung hình từ camera điện thoại nhìn trên xuống (numpy array BGR).
- `info`: Dict dữ liệu trạng thái thu được từ `GraspAssist4DOF.compute_current_suggestion()`.
- `titles`: Tuple 2 chuỗi tiêu đề hiển thị trên từng camera.

**Cây gọi hàm (Call Tree):**
- `build_guide_screen()`
  - `_cam_cell(view_left, titles[0], 640, 400)` → gọi `fit_cell()` (letterbox giữ tỉ lệ)
  - `_cam_cell(view_right, titles[1], 640, 400)` → gọi `fit_cell()`
  - `render_guide_panel(info, 1280, 400)`
    - `draw_stepper(img, stage)` → vẽ 5 viên thuốc trạng thái bước bằng `rrect()`, `check_icon()`
    - `draw_instruction(img, info)` → thông báo việc cần làm ngay và đếm số lần bấm
    - `draw_target_line(img, info)` → tọa độ mm và kiểm tra tầm với
    - `draw_action_rows(img, info)` → 4 hàng điều khiển: `keycap()`, `direction_glyph()`, `servo_track()`
    - `draw_result_card(img, info)` → tiến độ S1/S2 qua `meter()` hoặc thẻ kết quả
    - `draw_footer(img, info)` → trạng thái kết nối, phím tắt

### 2.3 Bảng quy đổi hệ màu (OpenCV BGR → RGB Hex)
Trong OpenCV, thứ tự màu của pixel là Blue-Green-Red (BGR). Để đưa lên tài liệu thuyết trình PowerPoint hoặc CSS giao diện, toàn bộ hằng số màu trong `guide_screen.py` được trích xuất và chuyển đổi sang RGB Hex chính xác:

| Tên biến trong code | Giá trị BGR (OpenCV) | Giá trị RGB (R, G, B) | Mã RGB Hex | Vai trò hiển thị trên giao diện |
|----------------------|----------------------|-----------------------|------------|---------------------------------|
| `BG`                 | `(30, 27, 25)`       | `(25, 27, 30)`        | `#191B1E`  | Màu nền chính toàn màn hình (Dark Background) |
| `CARD`               | `(46, 42, 39)`       | `(39, 42, 46)`        | `#272A2E`  | Màu nền thẻ khối chức năng (Card Surface) |
| `CARD_EDGE`          | `(82, 76, 70)`       | `(70, 76, 82)`        | `#464C52`  | Màu viền đường phân cách, khung thẻ (Border) |
| `WHITE`              | `(245, 245, 245)`    | `(245, 245, 245)`     | `#F5F5F5`  | Màu chữ chính, tiêu đề nổi bật (Primary Text) |
| `MUTED`              | `(165, 160, 155)`    | `(155, 160, 165)`     | `#9BA0A5`  | Màu chữ phụ, chú thích, nhãn mờ (Muted Text) |
| `AMBER`              | `(40, 185, 255)`     | `(255, 185, 40)`      | `#FFB928`  | Màu cam nhấn, bước hiện tại, ô phím bấm (Accent) |
| `AMBER_DK`           | `(28, 62, 98)`       | `(98, 62, 28)`        | `#623E1C`  | Nền cam tối cho hàng servo đang cần tác động |
| `GREEN`              | `(110, 215, 90)`     | `(90, 215, 110)`      | `#5AD76E`  | Màu xanh lá thành công, bước hoàn thành, trong tầm với |
| `GREEN_DK`           | `(50, 88, 42)`       | `(42, 88, 50)`        | `#2A5832`  | Nền xanh lá sẫm cho viên thuốc bước đã xong |
| `RED`                | `(85, 85, 245)`      | `(245, 85, 85)`       | `#F55555`  | Màu đỏ cảnh báo ngoài tầm với, lỗi, thất bại |
| `DARK_TXT`           | `(30, 27, 25)`       | `(25, 27, 30)`        | `#191B1E`  | Màu chữ đen tương phản trên nền cam / xanh |

### 2.4 Thiết kế nút phím "Keycap" và Bảng phím tắt toàn diện
**Đặc tả hình học của hàm `keycap()` (dòng 155–159):**
- Hàm: `keycap(img, x, y, letter, size=44, bg=AMBER, fg=DARK_TXT)`
- Kích thước: Hình vuông bo góc $44 \times 44$ px, bán kính bo góc $R = 9$ px.
- Hiệu ứng đổ bóng 3D: Một hình chữ nhật bo góc màu tối `(20, 18, 16)` dời xuống 3 px tại `(x, y + 3)`.
- Mặt phím: Đặt tại `(x, y)` với màu nền `AMBER` (`#FFB928`) khi phím đang cần bấm, hoặc xám `(120, 116, 112)` khi ở hàng khác.
- Ký tự phím: Viết hoa, in đậm (`FONT_BIG`, font scale 1.1, thickness 2), căn giữa phím với màu `DARK_TXT` (`#191B1E`).

**Bảng ánh xạ phím tắt toàn diện trong toàn bộ hệ thống:**

| Phím bấm | Kênh servo / Chức năng | Hành vi vật lý & Chiều chuyển động | Ngưỡng giới hạn góc | File định nghĩa & Hàm nguồn |
|:---:|:---|:---|:---:|:---|
| <kbd>A</kbd> | Kênh 0: Đế (Base) | Quay sang **TRÁI** $+5^\circ$ ($+\theta_1$) | $[0^\circ, 180^\circ]$ | `grasp_assist_4dof.py`: `SERVO_LIMITS`, `format_key_hint` |
| <kbd>D</kbd> | Kênh 0: Đế (Base) | Quay sang **PHẢI** $-5^\circ$ ($-\theta_1$) | $[0^\circ, 180^\circ]$ | `grasp_assist_4dof.py`: `SERVO_LIMITS`, `format_key_hint` |
| <kbd>W</kbd> | Kênh 1: Vai (Shoulder) | Nâng cánh tay **LÊN** $+5^\circ$ ($+\theta_2$) | $[25^\circ, 155^\circ]$ | `grasp_assist_4dof.py`: `SERVO_LIMITS`, `format_key_hint` |
| <kbd>S</kbd> | Kênh 1: Vai (Shoulder) | Hạ cánh tay **XUỐNG** $-5^\circ$ ($-\theta_2$) | $[25^\circ, 155^\circ]$ | `grasp_assist_4dof.py`: `SERVO_LIMITS`, `format_key_hint` |
| <kbd>I</kbd> | Kênh 2: Khuỷu (Elbow) | Gập khuỷu **LÊN** $+5^\circ$ ($+\theta_3$) | $[25^\circ, 155^\circ]$ | `grasp_assist_4dof.py`: `SERVO_LIMITS`, `format_key_hint` |
| <kbd>K</kbd> | Kênh 2: Khuỷu (Elbow) | Duỗi khuỷu **XUỐNG** $-5^\circ$ ($-\theta_3$) | $[25^\circ, 155^\circ]$ | `grasp_assist_4dof.py`: `SERVO_LIMITS`, `format_key_hint` |
| <kbd>L</kbd> | Kênh 3: Kẹp (Grip) | **KẸP VÀO** $+5^\circ$ (tăng lực kẹp) | $[95^\circ, 175^\circ]$ | `grasp_assist_4dof.py`: `SERVO_LIMITS`, `format_key_hint` |
| <kbd>J</kbd> | Kênh 3: Kẹp (Grip) | **MỞ RA** $-5^\circ$ (nhả kẹp rộng hơn) | $[95^\circ, 175^\circ]$ | `grasp_assist_4dof.py`: `SERVO_LIMITS`, `format_key_hint` |
| <kbd>H</kbd> | Toàn bộ 4 khớp (Home) | Đưa cánh tay về vị trí an toàn ban đầu $[90^\circ, 90^\circ, 90^\circ, 95^\circ]$ | Vị trí chuẩn | `robot_arm_4dof.ino`: `case 'h'`, `apply_key_locally` |
| <kbd>SPACE</kbd> / <kbd>N</kbd> | Điều phối quy trình | Chuyển sang bước tiếp theo trong quy trình 5 bước gắp | Bước 0 → 4 | `grasp_assist_4dof.py`: `next_stage()`, `main.py` |
| <kbd>TAB</kbd> / <kbd>V</kbd> | Chọn mục tiêu | Chuyển đổi vật mục tiêu tiếp theo trên bàn A4 | Vòng lặp vật | `grasp_assist_4dof.py`: `cycle_target()` |
| <kbd>P</kbd> | Tự động hóa | Bật / Tắt chế độ tự động gửi từng bước góc (Auto-Step) | Chu kỳ 0.28s | `grasp_assist_4dof.py`: `auto_step_enabled` |
| <kbd>R</kbd> | Khôi phục hệ thống | Reset toàn bộ quy trình gắp về Bước 1 (Điểm chờ) | Về bước 0 | `grasp_assist_4dof.py`: `reset_workflow()` |
| <kbd>G</kbd> | Cửa sổ hiển thị | Ẩn hoặc Hiện cửa sổ "HƯỚNG DẪN GẮP" (1280 × 800) | Toggle UI | `main.py`: `guide_enabled` |
| <kbd>M</kbd> | Thị giác máy tính | Bật / Tắt lớp phủ tọa độ ArUco 4 góc và bounding box YOLO | Toggle Vision | `main.py`: `aruco_enabled` |
| <kbd>C</kbd> | Thu thập dữ liệu | Chụp ảnh frame gốc 2 camera lưu vào thư mục `captures/` | Ghi file JPEG | `main.py`: `save_snapshots()` |
| <kbd>X</kbd> | Cấu hình camera | Đổi vị trí hiển thị giữa 2 camera (Laptop ↔ Điện thoại) | Hoán đổi vị trí | `main.py`: phím 'X' |
| <kbd>0</kbd>–<kbd>3</kbd> | Chỉ số camera | Chuyển đổi chỉ số thiết bị phần cứng của camera | Index OpenCV | `main.py`: phím số '0'–'3' |
| <kbd>Q</kbd> | Thoát chương trình | Đóng luồng camera, ngắt kết nối serial và đóng cửa sổ | Dừng an toàn | `main.py`: vòng lặp chính |

---

## 3. ĐIỀU TRA BỘ KIỂM THỬ VÀ SINH ẢNH GIAO DIỆN MẪU (`test_ik.py`)

### 3.1 Kết quả chạy thực tế 10 bài kiểm thử của `test_ik.py`
Lệnh thực thi trong môi trường Windows PowerShell (thiết lập chuẩn UTF-8 để hiển thị ký tự tiếng Việt):
```powershell
$env:PYTHONUTF8="1"; python test_ik.py
```
**Kết quả thực tế ghi nhận:**
- Mã thoát (Exit code): `0` (Toàn bộ bài test đều PASS).
- **Chi tiết 10 bài kiểm thử được ghi nhận từng dòng:**
  1. `test_fk_ik_grid`: `✅ [PASS] Đã kiểm thử 455 điểm 3D trong tầm với: sai số FK(IK(p)) tối đa = 0.000000 mm (< 0.1 mm)`
     - Quét lưới điểm: $X \in [110, 200]\text{ mm}$ (bước 15), $Y \in [-90, 90]\text{ mm}$ (bước 15), $Z \in \{15, 30, 50, 80, 100\}\text{ mm}$.
     - Tổng số điểm nằm trong tầm với hợp lệ: **455 điểm**.
     - Sai số Euclid giữa tọa độ ban đầu $p$ và tọa độ tính ngược qua thuận $FK(IK(p))$ đạt độ chính xác số học lý tưởng: $0.000000\text{ mm}$ (ngưỡng yêu cầu $< 0.1\text{ mm}$).
     - Toàn bộ 4 góc servo đều tuân thủ giới hạn an toàn trong `SERVO_LIMITS` và chia hết cho `SERVO_STEP_DEG = 5`.
  2. `test_key_hints`: `✅ [PASS] Kiểm thử gợi ý bấm phím (WASD + IK + JL) với STEP = 5° chính xác tuyệt đối!`
     - Đế: $90^\circ \to 115^\circ$ ($+25^\circ$) $\implies$ Phím 'a' $\times 5$ lần (Trái).
     - Vai: $90^\circ \to 70^\circ$ ($-20^\circ$) $\implies$ Phím 's' $\times 4$ lần (Xuống).
     - Khuỷu: $90^\circ \to 105^\circ$ ($+15^\circ$) $\implies$ Phím 'i' $\times 3$ lần (Gập lên).
     - Kẹp: $95^\circ \to 165^\circ$ ($+70^\circ$) $\implies$ Phím 'l' $\times 14$ lần (Kẹp vào).
  3. `test_table_robot_mapping`: `✅ [PASS] Ánh xạ tờ A4 <-> hệ robot đúng cho cả hai hướng đặt robot (up / down)`
     - Kiểm tra tính thuận nghịch hai chiều: $p = \text{robot\_mm\_to\_table\_cm}(\text{table\_cm\_to\_robot\_mm}(p))$. Sai số tuyệt đối $< 10^{-9}$.
  4. `test_board_silence_detection`: `✅ [PASS] Phát hiện board không nhận lệnh USB (firmware cũ)`
     - Phát hiện cờ `board_ignores_usb()` khi lệnh gửi quá $2.0\text{ giây}$ mà vi điều khiển không có phản hồi.
  5. `test_find_bluetooth_port`: `✅ [PASS] Tìm cổng Bluetooth của HC-05 (Windows theo địa chỉ MAC, macOS theo tên cổng)`
     - Windows: Tự động trích xuất chuỗi MAC `98D351F6AF14` trong Hardware ID (`BTHENUM`).
     - macOS: Nhận diện cổng `/dev/cu.HC-05` theo tên thiết bị.
  6. `test_send_key_over_bluetooth`: `✅ [PASS] Gửi lệnh qua Bluetooth HC-05, tự quay về USB khi BT đứt`
     - Khi kết nối Bluetooth bị ngắt (`OSError`), hệ thống tự động fallback truyền lệnh qua cổng USB Serial.
  7. `test_s1_ignores_gripper_marker`: `✅ [PASS] S1 chỉ tính mã của vật (ID 10-29), kẹp rỗng nâng lên không bị báo là đã gắp`
     - Mã ArUco ID 6 gắn trên đầu kẹp khi nâng lên cao không kích hoạt cờ S1; chỉ mã vật ID 10–29 vượt ngưỡng mới được tính.
  8. `test_grasp_locks_target_and_logs_align_error`: `✅ [PASS] Khóa vật lúc đóng kẹp cho bước nâng + kiểm tra, log CSV ghi đúng sai số căn đầu kẹp`
     - Khi chuyển từ bước 2 sang bước 3, tọa độ và tên vật được khóa cố định (`locked_grasp_cm`, `locked_obj`). Sai số đầu kẹp được ghi nhận vào cột `align_error_mm`.
  9. `test_normalize_phone_url`: `✅ [PASS] Chuẩn hóa địa chỉ IP Webcam của điện thoại`
     - `192.168.1.5` $\to$ `http://192.168.1.5:8080/video`.
  10. `test_find_cameras_macos`: `✅ [PASS] Nhận camera MacBook và iPhone (Continuity Camera) theo tên trên macOS`
      - Nhận diện đúng camera iPhone rời, tự động loại trừ camera ảo và "Desk View".

### 3.2 Cơ chế `fake_assist()` và phương pháp sinh ảnh `guide_screen_sample.png` cho M2
Trong `test_ik.py` (dòng 190–218), context manager `fake_assist()` được thiết kế để kiểm thử toàn bộ logic điều phối và giao diện mà không cần cắm phần cứng thật:
- Lớp `FakeLink` mô phỏng `ArduinoSerialLink` với góc ban đầu `[90, 90, 90, 95]`, `usb_ok = False`, không mở cổng COM vật lý (tránh gây reset vi điều khiển).
- Thư mục tạm thời `tempfile.TemporaryDirectory()` chứa file log giả định, bảo đảm không làm bẩn workspace.

**Đoạn mã mẫu sẵn sàng cho Milestone 2 để sinh ảnh giao diện thật:**
```python
import cv2
import numpy as np
from test_ik import fake_assist
from guide_screen import build_guide_screen

with fake_assist() as assist:
    # 1. Thêm vật thể mẫu trên tờ A4 (tọa độ cm)
    assist.objects = [{
        "name": "Hop_Xanh_ID11", "x_cm": 15.0, "y_cm": 8.0,
        "w_mm": 35.0, "h_mm": 35.0, "px": (640, 480), "source": "aruco"
    }]
    assist.target_history_cm.append((15.0, 8.0))
    assist.stage = 1  # Bước 2: Hạ xuống điểm kẹp
    info = assist.compute_current_suggestion()
    
    # 2. Tạo hình ảnh 2 camera
    # Cam phải (Top-down): Dùng ảnh lưới ArUco A4 thật có sẵn trong workspace
    grid_img = cv2.imread("aruco_A4_grid.png")
    if grid_img is None:
        grid_img = np.full((400, 640, 3), (240, 240, 240), dtype=np.uint8)
    # Cam trái (Side): Khung nền tối mô phỏng góc nhìn ngang
    side_img = np.zeros((400, 640, 3), dtype=np.uint8)
    cv2.putText(side_img, "SIDE VIEW (WEBCAM)", (160, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 180, 255), 2)
    
    # 3. Tạo màn hình hướng dẫn và lưu vào slides/assets/
    screen = build_guide_screen(side_img, grid_img, info)
    cv2.imwrite("slides/assets/guide_screen_sample.png", screen)
```
*Ghi chú quan trọng:* Phương pháp này sử dụng 100% mã nguồn thực tế và tệp lưới `aruco_A4_grid.png` có sẵn trong workspace, hoàn toàn đáp ứng tiêu chí Không sử dụng ảnh do AI tạo (No AI-generated images).

### 3.3 Trạng thái nhật ký thực nghiệm (`logs/attempts.csv`)
- **Điều tra hệ thống:** Đã quét toàn bộ cây thư mục workspace, thư mục `logs/` và tệp `logs/attempts.csv` hiện chưa tồn tại.
- **Xử lý theo quy định R1 & R4:** Không tự ý tính toán hay bịa đặt tỉ lệ thành công thực tế. Toàn bộ các chỉ số về số lượt thử nghiệm, tỉ lệ gắp thành công (%) và phân bố lỗi (kẹp trượt vs rơi khi nâng) trên các slide liên quan (Slide 13) được thể hiện dưới dạng placeholder `[...]` để nhóm sinh viên tự đo lường và điền sau khi vận hành phần cứng thật.

---

## 4. KẾ HOẠCH TRIỂN KHAI CHI TIẾT 15 SLIDE THUYẾT TRÌNH (SLIDE 1 → 15)

Dưới đây là đặc tả kỹ thuật chi tiết cho từng slide từ 1 đến 15. Mỗi slide bao gồm: Tiêu đề, 3–6 ý chính (≤ 12 từ/ý), Quy cách hình ảnh / Khối Shape PowerPoint native, Lời thuyết trình bằng tiếng Việt hoàn chỉnh (3–5 câu), Nguồn dẫn chứng mã nguồn chính xác, và Danh mục placeholder `[...]`.

---

### SLIDE 1: TIÊU ĐỀ ĐỀ TÀI
- **Tiêu đề slide:** HỆ THỐNG HỖ TRỢ GẮP VẬT CHO CÁNH TAY ROBOT 4-DOF
- **Phụ đề:** Ứng dụng Thị giác máy tính 2 Camera, Định vị ArUco, Nhận diện YOLO11 và Động học ngược
- **Ý chính:**
  1. Đề tài: Hệ thống thị giác máy tính hỗ trợ gắp vật cho Robot Arm 4-DOF.
  2. Cơ cấu chấp hành: Cánh tay 4 bậc tự do điều khiển qua 4 động cơ servo.
  3. Cảm biến thị giác: Kết hợp Camera nhìn trên xuống và Webcam nhìn ngang.
  4. Thuật toán: Định vị không gian ArUco, phát hiện vật thể YOLO11s và giải tích IK.
  5. Thông tin nhóm: Sinh viên thực hiện `[...]` — Lớp/Môn: `[...]`.
  6. Giảng viên hướng dẫn: `[...]` — Thời gian báo cáo: `[...]`.
- **Đặc tả Shape / Visual:**
  - Layout trung tâm đối xứng trên nền tối `#191B1E`.
  - Khung thẻ chính `#272A2E`, viền `#464C52` bo góc nhẹ, dải viền trang trí màu cam `#FFB928` ở cạnh trên.
  - Phù hiệu/Icon công nghệ: 4 khối tượng trưng: [Dual Camera] ↔ [ArUco Grid] ↔ [YOLO11s] ↔ [Inverse Kinematics].
- **Lời thuyết trình (Speaker Notes):**
  > "Kính thưa quý thầy cô và các bạn, hôm nay nhóm chúng em xin được trình bày đề tài: Hệ thống hỗ trợ gắp vật cho cánh tay robot 4 bậc tự do sử dụng 2 camera, ArUco, YOLO11 và động học ngược. Mục tiêu của dự án là xây dựng một hệ thống thị giác thông minh có khả năng quan sát không gian làm việc, tự động tính toán góc quay của từng khớp và hướng dẫn người điều khiển thao tác gắp vật một cách trực quan, chính xác. Sau đây, em xin phép đại diện nhóm đi vào chi tiết cấu trúc phần cứng và giải thuật phần mềm của hệ thống."
- **Nguồn dẫn chứng:** `ORIGINAL_REQUEST.md` (R1.1), `orchestrator/PROJECT.md` (Feature 1).
- **Placeholder cần điền `[...]`:**
  - Tên thành viên nhóm và MSSV: `[...]`
  - Giảng viên hướng dẫn: `[...]`
  - Tên môn học / Mã lớp học phần: `[...]`
  - Ngày báo cáo: `[...]`

---

### SLIDE 2: BÀI TOÁN VÀ MỤC TIÊU GIẢI PHÁP
- **Tiêu đề slide:** BÀI TOÁN THỰC TẾ VÀ MỤC TIÊU HỆ THỐNG
- **Ý chính:**
  1. Thách thức: Điều khiển cánh tay 4-DOF thủ công khó ước lượng không gian 3D.
  2. Giải pháp thị giác: Dùng 2 camera độc lập quan sát toàn diện vùng gắp.
  3. Tính toán tự động: Giải động học ngược (IK) ra góc servo chính xác từng 5°.
  4. Hướng dẫn trực quan: Bảng điều khiển chỉ rõ phím bấm và số lần thao tác.
  5. Tự động xác nhận: Kiểm tra kết quả 2 góc nhìn, loại bỏ phán đoán chủ quan.
- **Đặc tả Shape / Visual:**
  - Bố cục so sánh 2 cột (Side-by-side Cards):
    - Cột trái (Thách thức - Viền đỏ `#F55555`): Khó canh tọa độ, dễ va chạm bàn, thao tác mò mẫm.
    - Cột phải (Giải pháp - Viền xanh lá `#5AD76E`): Tự tính toán IK, hướng dẫn phím bấm trực quan, camera kép tự xác nhận.
- **Lời thuyết trình (Speaker Notes):**
  > "Trong thực tế, việc điều khiển một cánh tay robot mini 4 bậc tự do gắp vật bằng tay cầm hoặc bàn phím thường gặp rất nhiều khó khăn do người vận hành không thể ước lượng chính xác khoảng cách 3 chiều và góc khớp. Để giải quyết bài toán này, nhóm đã xây dựng giải pháp hỗ trợ thông minh: sử dụng camera góc trên để định vị vật thể và giải động học ngược, kết hợp camera góc ngang để kiểm tra độ cao. Hệ thống đóng vai trò như một người trợ lý ảo, đưa ra hướng dẫn từng bước phím bấm và tự động đánh giá xem vật đã được gắp thành công hay chưa."
- **Nguồn dẫn chứng:** `ORIGINAL_REQUEST.md` (R1.2), `guide_screen.py` (Mục đích thiết kế dòng 3–10).
- **Placeholder cần điền `[...]`:** Không có.

---

### SLIDE 3: KIẾN TRÚC PHẦN CỨNG & CẤU HÌNH THIẾT BỊ
- **Tiêu đề slide:** KIẾN TRÚC VÀ THIẾT BỊ PHẦN CỨNG
- **Ý chính:**
  1. Cơ cấu chấp hành: 4 động cơ RC Servo MG996R (Bánh răng kim loại, lực kéo lớn).
  2. Mạch điều khiển xung: Mạch PCA9685 giao tiếp I2C địa chỉ `0x40`, tần số `50Hz`.
  3. Vi điều khiển trung tâm: Bo mạch Arduino `[...]` cấp xung và nhận lệnh 9600 baud.
  4. Kết nối không dây: Module Bluetooth HC-05 (Chân RX=D2, TX=D3, tốc độ 9600 baud).
  5. Nguồn điện: Bộ nguồn rời 5V–6V dòng cao cung cấp riêng cho 4 động cơ servo.
  6. Máy tính xử lý & Camera: Máy tính `[...]` chạy YOLO11s, Webcam laptop + Camera điện thoại.
- **Đặc tả Shape / Visual:**
  - Sơ đồ khối phần cứng (PowerPoint native shapes):
    - Khối Máy tính (MacBook/PC) kết nối USB Serial (9600) & Bluetooth tới Arduino.
    - Arduino kết nối I2C (SDA/SCL) tới PCA9685.
    - Mạch PCA9685 nối 4 kênh Servo (Kênh 0: Đế, 1: Vai, 2: Khuỷu, 3: Kẹp).
    - Khối nguồn rời 5–6V độc lập nuôi PCA9685 (chống sụt áp vi điều khiển).
- **Lời thuyết trình (Speaker Notes):**
  > "Về mặt phần cứng, cánh tay robot sử dụng 4 servo MG996R bánh răng kim loại, mang lại lực kẹp và độ ổn định cao. Do dòng khởi động của 4 servo khá lớn, nhóm sử dụng module mở rộng PCA9685 giao tiếp qua chuẩn I2C địa chỉ 0x40 ở tần số 50Hz, được cấp nguồn rời từ 5 đến 6V độc lập với Arduino. Dữ liệu điều khiển được truyền từ máy tính xử lý trung tâm xuống Arduino thông qua cáp USB hoặc module Bluetooth HC-05 gắn ở chân D2 và D3 với tốc độ 9600 baud."
- **Nguồn dẫn chứng:** `robot_arm_4dof/robot_arm_4dof.ino` (dòng 5–8, 11–13, 43–47), `grasp_assist_4dof.py` (dòng 29–37).
- **Placeholder cần điền `[...]`:**
  - Loại bo mạch Arduino chính xác (Uno R3 / Nano / Mega 2560): `[...]`
  - Model máy tính xử lý (MacBook Air M5 / PC Laptop Windows): `[...]`

---

### SLIDE 4: KIẾN TRÚC PHẦN MỀM & LUỒNG DỮ LIỆU THỜI GIAN THỰC
- **Tiêu đề slide:** KIẾN TRÚC PHẦN MỀM VÀ LUỒNG XỬ LÝ
- **Ý chính:**
  1. Đa luồng song song: Đọc 2 camera (`CameraStream`) và suy luận YOLO trên luồng nền riêng.
  2. Chuẩn hóa hình học: Biến đổi Homography chuyển đổi tọa độ từ pixel sang centimet.
  3. Xử lý logic trung tâm: `GraspAssist4DOF` điều phối 5 bước gắp và giải thuật IK.
  4. Giao tiếp vi điều khiển: `ArduinoSerialLink` gửi gói JSON trạng thái servo ở tần số 5Hz.
  5. Hiển thị kép: Thanh HUD gắn chân màn hình video và Cửa sổ hướng dẫn 1280 × 800.
- **Đặc tả Shape / Visual:**
  - Sơ đồ Pipeline dữ liệu dạng khối (Dataflow Pipeline):
    `[2 Camera Feeds]` → `[ArucoYoloTracker]` → `[Homography Px→Cm]` → `[GraspAssist4DOF (IK)]` → `[ArduinoSerialLink]` → `[Firmware Arduino]` → `[4x Servos]`
    Nhánh song song hiển thị: `[GraspAssist4DOF]` → `[Thanh HUD 1280x175]` + `[Cửa sổ Hướng dẫn 1280x800]`.
- **Lời thuyết trình (Speaker Notes):**
  > "Kiến trúc phần mềm của hệ thống được tổ chức hoàn toàn theo hướng đa luồng để triệt tiêu độ trễ hình ảnh. Luồng CameraStream liên tục bắt khung hình mới nhất từ 2 camera, trong khi mô hình YOLO11 chạy trên một worker riêng để không gây sụt giảm FPS hiển thị. Tọa độ vật thể được ánh xạ từ pixel sang centimet thông qua ma trận Homography, sau đó đưa vào module GraspAssist4DOF để tính toán động học ngược. Kết quả góc quay được đồng bộ hai chiều với Arduino qua giao thức JSON ở tần số 5Hz và hiển thị trực quan lên cửa sổ hướng dẫn."
- **Nguồn dẫn chứng:** `main.py` (`CameraStream` dòng 68–84, `ArucoYoloTracker` dòng 432–451, luồng hiển thị dòng 845–870), `grasp_assist_4dof.py` (dòng 346–376).
- **Placeholder cần điền `[...]`:** Không có.

---

### SLIDE 5: HỆ TỌA ĐỘ BÀN LÀM VIỆC & LƯỚI ARUCO TỜ A4
- **Tiêu đề slide:** THIẾT LẬP KHÔNG GIAN BÀN VÀ LƯỚI MÃ ARUCO
- **Ý chính:**
  1. Mặt bàn chuẩn: Tờ giấy A4 đặt ngang kích thước chuẩn $29.7 \times 21.0\text{ cm}$.
  2. Bộ từ điển: `DICT_4X4_50` gồm 50 mã kích thước 4×4 bit, tối ưu tốc độ nhận diện.
  3. Định vị 4 góc: Mã ID 0 (Gốc $0,0$), ID 1 ($29.7, 0$), ID 2 ($29.7, 21$), ID 3 ($0, 21\text{ cm}$).
  4. Kích thước mã in: Kích thước $2.8\text{ cm}$, đặt cách mép giấy $0.25\text{ cm}$ (viền Quiet Zone).
  5. Hệ thống mã mở rộng: Mã ID 4 gắn trên đế robot, ID 5–6 trên đầu kẹp, ID 10–29 trên vật thể.
  6. Cơ chế dự phòng: Tự động phân đoạn màu không gian LAB khi che khuất mã góc.
- **Đặc tả Shape / Visual:**
  - Hình minh họa mặt phẳng tờ giấy A4 đặt ngang (tỉ lệ 29.7 : 21.0):
    - 4 góc có 4 ô ArUco ID 0 (TL), ID 1 (TR), ID 2 (BR), ID 3 (BL).
    - Trục $X$ chạy dọc cạnh trên ($0 \to 29.7\text{ cm}$), Trục $Y$ chạy dọc cạnh trái ($0 \to 21.0\text{ cm}$).
    - Vị trí Đế robot gắn mã ID 4 ở mép giấy và các vật thể dán mã ID 10–29.
- **Lời thuyết trình (Speaker Notes):**
  > "Để xác định không gian làm việc một cách tuyệt đối, nhóm sử dụng một tờ giấy A4 đặt ngang kích thước 29.7 nhân 21 centimet làm mặt bàn chuẩn. Bốn góc tờ giấy được in 4 mã ArUco thuộc bộ từ điển DICT_4X4_50 từ ID 0 đến ID 3, mỗi mã có kích thước 2.8 centimet và đặt cách mép 2.5 milimet để OpenCV dễ dàng bắt góc. Hệ thống còn quy ước mã ID 4 gắn trên đế robot, mã ID 5 và 6 gắn trên đầu kẹp, cùng dải mã từ 10 đến 29 dành cho các vật thể. Nếu có góc bị che khuất, thuật toán phân đoạn màu LAB sẽ tự động kích hoạt để tìm biên giấy dự phòng."
- **Nguồn dẫn chứng:** `generate_aruco_a4.py` (dòng 17–20, 31–38, 160–165), `main.py` (dòng 264–291, 306–321), `grasp_assist_4dof.py` (dòng 38–48, 704–744).
- **Placeholder cần điền `[...]`:** Không có.

---

### SLIDE 6: NHẬN DIỆN VẬT THỂ KẾT HỢP YOLO11s VÀ ARUCO
- **Tiêu đề slide:** NHẬN DIỆN VẬT THỂ VÀ HỢP NHẤT DỮ LIỆU THỊ GIÁC
- **Ý chính:**
  1. Mô hình AI: YOLO11s chạy với vùng cắt (crop) A4, ngưỡng tin cậy `conf=0.12`, `imgsz=960`.
  2. Nhận diện ArUco: Phát hiện mã ID 10–29 gắn trên vật thể, truy xuất kích thước từ `OBJECT_SPECS`.
  3. Khử trùng lặp thông minh: Bỏ qua kết quả YOLO nếu cách mã ArUco dưới khoảng cách $2.5\text{ cm}$.
  4. Lọc mịn tọa độ: Sử dụng bộ lọc trung bình trượt 10 khung hình (`deque(maxlen=10)`).
  5. Thứ tự ưu tiên gắp: Tự động sắp xếp vật thể theo khoảng cách Euclid gần đế robot nhất.
- **Đặc tả Shape / Visual:**
  - Sơ đồ hợp nhất dữ liệu (Sensor Fusion Flow):
    - Nhánh 1: `[Ảnh Cam Trên]` → `[YOLO11s (conf=0.12)]` → `[Tọa độ Bounding Box]`
    - Nhánh 2: `[Ảnh Cam Trên]` → `[ArucoDetector]` → `[Mã ID 10–29 & Kích thước thật]`
    - Khối hợp nhất: `[Khoảng cách < 2.5cm?]` → `Có: Giữ ArUco, bỏ YOLO` / `Không: Nhận cả hai`
    - Bộ lọc: `[Moving Average 10 frames]` → `[Sort by Proximity to Base]`.
- **Lời thuyết trình (Speaker Notes):**
  > "Nhằm tối ưu độ chính xác và khả năng thích ứng linh hoạt, hệ thống kết hợp song song cả mô hình học sâu YOLO11s và mã ArUco. Mô hình YOLO11s được cắt vùng xử lý sát bề mặt tờ A4 để loại bỏ nhiễu từ tay người hay bàn ghế xung quanh, trong khi các vật mẫu dán mã ArUco ID 10 đến 29 sẽ cung cấp ngay kích thước ba chiều thật từ bảng cấu hình. Hai nguồn dữ liệu này được khử trùng lặp với ngưỡng khoảng cách 2.5 centimet, sau đó làm mịn qua bộ lọc trung bình trượt 10 khung hình và ưu tiên gắp vật thể nằm gần đế robot nhất."
- **Nguồn dẫn chứng:** `main.py` (`_detect_objects_topdown` dòng 502–536), `grasp_assist_4dof.py` (`update_topdown_observations` dòng 746–770, `OBJECT_SPECS` dòng 63–70).
- **Placeholder cần điền `[...]`:** Không có.

---

### SLIDE 7: ĐỘNG HỌC THUẬN VÀ ĐỘNG HỌC NGƯỢC GIẢI TÍCH 4-DOF
- **Tiêu đề slide:** ĐỘNG HỌC CÁNH TAY ROBOT VÀ QUY ĐỔI SERVO
- **Ý chính:**
  1. Thông số hình học (`ARM_CONFIG`): $d_1 = 70$, $L_2 = 105$, $L_3 = 100$, $L_{4r} = 65$, $L_{4z} = 25\text{ mm}$.
  2. Động học thuận (FK): Xác định vị trí điểm kẹp $(x, y, z)$ trong không gian từ bộ 3 góc $(\theta_1, \theta_2, \theta_3)$.
  3. Động học ngược (IK): Giải tích nghiệm khuỷu hướng lên (Elbow-up) với điều kiện $\sin(\theta_3) \le 0$.
  4. Ánh xạ góc servo: $90^\circ$ tương ứng góc nghiêng $\theta_2 = 45^\circ$ và góc gập $\theta_3 = -45^\circ$.
  5. Làm tròn bước nhảy: Quy đổi về bước `SERVO_STEP_DEG = 5°` khớp 100% lệnh phím vi điều khiển.
  6. Giới hạn cơ khí: Đế $[0^\circ, 180^\circ]$, Vai $[25^\circ, 155^\circ]$, Khuỷu $[25^\circ, 155^\circ]$, Kẹp $[95^\circ, 175^\circ]$.
- **Đặc tả Shape / Visual:**
  - Sơ đồ động học mặt phẳng 2D (Kinematic Diagram):
    - Trục đứng từ bàn lên vai: $d_1 = 70\text{ mm}$.
    - Khâu vai $L_2 = 105\text{ mm}$ nghiêng góc $\theta_2$.
    - Khâu khuỷu $L_3 = 100\text{ mm}$ gập góc $\theta_3$ (tư thế khuỷu hướng lên).
    - Đầu kẹp: vươn ngang $L_{4r} = 65\text{ mm}$, hạ thấp $L_{4z} = 25\text{ mm}$.
    - Thẻ công thức toán IK: $D = \frac{r_w^2 + z_w^2 - L_2^2 - L_3^2}{2 L_2 L_3}$, $\theta_3 = \text{atan2}(-\sqrt{1-D^2}, D)$.
- **Lời thuyết trình (Speaker Notes):**
  > "Cấu trúc cơ học của cánh tay được xác định bởi các thông số thực tế đo bằng thước: chiều cao khớp vai d1 bằng 70mm, khâu vai L2 dài 105mm, khâu khuỷu L3 dài 100mm, cùng độ vươn đầu kẹp L4r bằng 65mm. Thuật toán IK giải tích chọn nghiệm khuỷu hướng lên để tối ưu không gian vận động và tránh va quẹt với mặt bàn. Các góc khớp sau khi giải sẽ được ánh xạ sang góc xung servo với quy ước chuẩn 90 độ tương ứng theta2 bằng 45 độ và theta3 bằng âm 45 độ, sau đó làm tròn theo bước nhảy 5 độ nằm trong dải giới hạn an toàn tuyệt đối."
- **Nguồn dẫn chứng:** `grasp_assist_4dof.py` (`ARM_CONFIG` dòng 32–52, `fk_4dof_joint` dòng 88–108, `ik_4dof_joint` dòng 111–154, `joint_to_arduino_servo` dòng 157–193, `SERVO_LIMITS` dòng 56–61).
- **Placeholder cần điền `[...]`:** Không có.

---

### SLIDE 8: CHUYỂN ĐỔI TỌA ĐỘ A4 SANG HỆ GỐC ROBOT & CẢNH BÁO AN TOÀN
- **Tiêu đề slide:** CHUYỂN ĐỔI HỆ TỌA ĐỘ VÀ VÙNG LÀM VIỆC AN TOÀN
- **Ý chính:**
  1. Vị trí đế trên A4: Tọa độ tâm xoay `base_x_cm = 18.0`, `base_y_cm = -13.6` (đặt mép trên tờ A4).
  2. Hướng vươn cánh tay: Cấu hình `robot_faces = "down"` (tay hướng từ mép trên vươn xuống).
  3. Công thức chuyển đổi: $x_{rob} = -(base\_y - y_{cm}) \times 10$, $y_{rob} = -(base\_x - x_{cm}) \times 10\text{ mm}$.
  4. Cảnh báo ngoài tầm với: Báo động đỏ khi $D > 1$, chỉ rõ số milimet cần đẩy vật lại gần (`move_closer_mm`).
  5. Cảnh báo kẹp servo (`clamped`): Phát hiện sớm góc khớp chạm giới hạn cứng của servo để tránh lệch đầu kẹp.
- **Đặc tả Shape / Visual:**
  - Hình minh họa mặt bằng tờ giấy A4 và vị trí gốc tọa độ Robot:
    - Điểm đặt Đế $(18.0\text{ cm}, -13.6\text{ cm})$ ở phía ngoài mép trên.
    - Cung tròn bán kính vươn tối đa ($L_2 + L_3 = 205\text{ mm}$) và bán kính tối thiểu.
    - Thẻ trạng thái UI màu: Xanh lá `TRONG TAM VOI`, Cam `CANH BAO: cham gioi han servo`, Đỏ `NGOAI TAM VOI! Doi vat gan them X mm`.
- **Lời thuyết trình (Speaker Notes):**
  > "Do camera đo đạc vật thể trên hệ tọa độ centimet của tờ giấy A4, hệ thống cần chuyển đổi sang hệ quy chiếu milimet lấy gốc tại đế robot. Trong bố cục hiện tại, robot đặt ở mép trên tại tọa độ X bằng 18 và Y bằng âm 13.6 centimet, vươn xuống với cấu hình robot_faces bằng 'down'. Nếu mục tiêu nằm ngoài tầm với tối đa 205 milimet, hệ thống sẽ phát cảnh báo đỏ và tính toán chính xác số milimet cần dịch chuyển vật lại gần, đồng thời phát hiện kịp thời các trường hợp góc khớp bị chạm giới hạn cơ khí."
- **Nguồn dẫn chứng:** `grasp_assist_4dof.py` (`ARM_CONFIG` dòng 43–48, `table_cm_to_robot_mm` dòng 227–240, `servo_limit_overshoot` dòng 196–214, `ik_4dof_joint` dòng 131–138).
- **Placeholder cần điền `[...]`:** Không có.

---

### SLIDE 9: QUY TRÌNH GẮP 5 BƯỚC & HƯỚNG DẪN PHÍM BẤM AN TOÀN
- **Tiêu đề slide:** QUY TRÌNH GẮP 5 BƯỚC VÀ THỨ TỰ THAO TÁC AN TOÀN
- **Ý chính:**
  1. Bước 1 — Điểm chờ: Đưa đầu kẹp lên trên cao $+60\text{ mm}$ so với vật, mở kẹp sẵn ($95^\circ$).
  2. Bước 2 — Hạ xuống: Hạ đầu kẹp xuống sát vật ($Z = \max(12, h/2)\text{ mm}$), giữ kẹp mở.
  3. Bước 3 — Đóng kẹp: Khóa chặt vật với góc kẹp $165^\circ$ (bấm phím <kbd>L</kbd>), khóa tọa độ mục tiêu.
  4. Bước 4 — Nâng lên: Nhấc vật lên khỏi mặt bàn $+80\text{ mm}$, duy trì trạng thái kẹp đóng.
  5. Bước 5 — Kiểm tra: Giữ yên toàn bộ cánh tay trong $3.0\text{ giây}$ để 2 camera tự động đánh giá.
  6. Thứ tự chuyển động an toàn: **Đế (0) → Kẹp (3) → Vai (1) → Khuỷu (2)** (tránh gạt đổ vật xung quanh).
  7. Chế độ Auto-Step (<kbd>P</kbd>): Tự động phát từng xung phím cách nhau $0.28\text{ giây}$ theo đúng thứ tự an toàn.
- **Đặc tả Shape / Visual:**
  - Sơ đồ tiến trình 5 bước gắp (Stepper UI flow):
    `[1. ĐIỂM CHỜ (+60mm)]` → `[2. HẠ XUỐNG (Sát vật)]` → `[3. ĐÓNG KẸP (L: 165°)]` → `[4. NÂNG LÊN (+80mm)]` → `[5. KIỂM TRA (3s)]`
  - Bảng thứ tự an toàn 4 khớp: Số 1: Đế <kbd>A</kbd>/<kbd>D</kbd> | Số 2: Kẹp <kbd>J</kbd>/<kbd>L</kbd> | Số 3: Vai <kbd>W</kbd>/<kbd>S</kbd> | Số 4: Khuỷu <kbd>I</kbd>/<kbd>K</kbd>.
- **Lời thuyết trình (Speaker Notes):**
  > "Quy trình gắp vật được chia thành 5 bước tuần tự chặt chẽ: bắt đầu bằng việc đưa tay tới điểm chờ cao hơn vật 60mm với kẹp mở, hạ xuống sát tâm vật, bấm phím L để kẹp chặt ở góc 165 độ, nâng bổng vật lên 80mm và cuối cùng là giữ yên để kiểm tra. Để đảm bảo an toàn tuyệt đối, hệ thống quy định thứ tự dịch chuyển các khớp là Đế trước, rồi tới Kẹp, sau đó mới tới Vai và Khuỷu nhằm tránh va chạm ngang vào các vật lân cận. Người dùng có thể nhấn phím P để hệ thống tự động phát xung phím sau mỗi 0.28 giây theo đúng trình tự này."
- **Nguồn dẫn chứng:** `grasp_assist_4dof.py` (`STAGE_NAMES` dòng 546–552, `ROW_ORDER` trong `guide_screen.py` dòng 63, `compute_current_suggestion` dòng 1011–1054).
- **Placeholder cần điền `[...]`:** Không có.

---

### SLIDE 10: TỰ ĐỘNG XÁC NHẬN KẾT QUẢ GẮP 2 CAMERA ĐỘC LẬP
- **Tiêu đề slide:** CƠ CHẾ TỰ ĐỘNG XÁC NHẬN GẮP 2 CAMERA ĐỘC LẬP
- **Ý chính:**
  1. Tín hiệu S1 (Cam ngang): Phát hiện vật thể nhấc cao $> +20\text{ mm}$ so với mặt bàn (`SIDE_LIFT_RATIO = 0.065`).
  2. Chống báo giả S1: Tuyệt đối không tính mã ArUco ID 6 gắn trên đầu kẹp (chỉ tính ID 10–29 / YOLO).
  3. Tín hiệu S2 (Cam trên): Vị trí ban đầu của vật trên bàn phải trống trong bán kính $3.0\text{ cm}$ ($30\text{ mm}$).
  4. Cửa sổ thống kê: Thu thập trong 30 khung hình, kết luận thành công khi cả S1 và S2 cùng đạt $\ge 80\%$.
  5. Phân loại lỗi tự động: Hết timeout $3.0\text{ giây}$:
     - $S_2 < 40\%$: Lỗi kẹp trượt (vật vẫn nằm ở vị trí cũ).
     - $S_1 < 40\%$: Lỗi rơi khi nâng hoặc chưa nhấc được vật lên.
     - Khác: Không xác định (bị che khuất tầm nhìn).
  6. Ghi nhật ký tự động: Lưu kết quả kèm sai số căn đầu kẹp vào tệp `logs/attempts.csv`.
- **Đặc tả Shape / Visual:**
  - Sơ đồ Logic 2 Camera (Verification Decision Matrix):
    - Khung Cam B (Ngang): Vạch mặt bàn (Cam) và Vạch ngưỡng nhấc $+20\text{ mm}$ (Xanh lá). Tín hiệu $S_1$.
    - Khung Cam A (Trên): Vòng tròn bán kính $3\text{ cm}$ tại chỗ cũ. Tín hiệu $S_2$ (`TRỐNG` / `CÒN VẬT`).
    - Bảng quyết định logic:
      - $S_1 \ge 80\% \text{ AND } S_2 \ge 80\% \implies$ **GẮP THÀNH CÔNG** (Banner xanh lá `#5AD76E`).
      - Timeout $3\text{s} \implies$ Phân loại: Kẹp trượt ($S_2 < 40\%$) / Rơi khi nâng ($S_1 < 40\%$) / Bị che (Banner đỏ `#F55555`).
- **Lời thuyết trình (Speaker Notes):**
  > "Điểm sáng tạo cốt lõi của đề tài là cơ chế tự động xác nhận kết quả gắp độc lập bằng 2 camera mà không cần gắn thêm cảm biến áp lực phức tạp. Camera ngang kiểm tra tín hiệu S1 xem vật đã nâng cao hơn mặt bàn 20mm hay chưa, trong đó thuật toán đặc biệt loại trừ mã ID 6 của đầu kẹp để tránh trường hợp kẹp rỗng nâng lên bị báo nhầm là thành công. Cùng lúc đó, camera trên kiểm tra tín hiệu S2 xem vị trí cũ trong bán kính 3 centimet đã hoàn toàn trống hay chưa. Nếu cả hai camera đồng thuận đạt từ 80% trên tổng số 30 khung hình, hệ thống sẽ công nhận thành công và tự động ghi log sai số vào CSV."
- **Nguồn dẫn chứng:** `grasp_assist_4dof.py` (`update_side_observations` dòng 852–899, `_evaluate_verification_locked` dòng 900–952, `test_ik.py` bài test S1 dòng 220–232).
- **Placeholder cần điền `[...]`:** Không có.

---

### SLIDE 11: GIAO THỨC GIAO TIẾP ARDUINO & ĐỒNG BỘ THỜI GIAN THỰC
- **Tiêu đề slide:** GIAO THỨC TRUYỀN THÔNG VÀ ĐỒNG BỘ ARDUINO
- **Ý chính:**
  1. Cấu hình cổng nối tiếp: Tốc độ truyền chuẩn 9600 baud qua cáp USB Serial hoặc Bluetooth HC-05.
  2. Gói tin JSON đồng bộ: Định kỳ mỗi $200\text{ ms}$ (tần số 5Hz), Arduino gửi `{"t":...,"servo":[B,S,E,G]}`.
  3. Cơ chế tự động Fallback: Đang gửi lệnh qua Bluetooth nếu mất kết nối sẽ tự động chuyển sang USB.
  4. Phát hiện mất phản hồi: Cảnh báo `BOARD KHONG PHAN HOI` nếu gửi lệnh quá $2.0\text{ giây}$ mà không nhận phản hồi.
  5. Chế độ mô phỏng (Simulation): Khi không cắm mạch, hệ thống tự kích hoạt mô phỏng góc servo trên bàn phím.
  6. Phím khẩn cấp <kbd>H</kbd> (Home): Đưa toàn bộ 4 servo lập tức về trạng thái ban đầu $[90^\circ, 90^\circ, 90^\circ, 95^\circ]$.
- **Đặc tả Shape / Visual:**
  - Sơ đồ kiến trúc truyền thông (Communication Topology):
    - [Laptop / Python] $\underset{\text{USB Serial 9600 / Bluetooth HC-05}}{\overset{\text{Lệnh phím 'w','a','s','d'...}}{\rightleftharpoons}}$ [Arduino UNO `[...]`] $\xrightarrow{\text{I2C 0x40 50Hz}}$ [PCA9685]
    - Cấu trúc chuỗi JSON: `{"t": 12450, "servo": [90, 85, 110, 165]}`.
    - Hộp cơ chế bảo vệ: Timeout 2s + Tự động chuyển cổng + Chế độ Simulation.
- **Lời thuyết trình (Speaker Notes):**
  > "Giao thức truyền thông giữa máy tính và vi điều khiển được thiết kế vô cùng tin cậy với tốc độ 9600 baud. Bo mạch Arduino định kỳ phát gói JSON chứa mảng 4 góc servo với tần số 5Hz để đồng bộ thời gian thực với mô hình 3D trên máy tính. Hệ thống hỗ trợ truyền nhận song song qua cả USB và Bluetooth HC-05, có khả năng tự động fallback về cáp USB nếu đường truyền Bluetooth bị gián đoạn. Đặc biệt, nếu không có phần cứng kết nối, phần mềm sẽ tự động chuyển sang chế độ mô phỏng giúp nhóm có thể kiểm thử toàn bộ thuật toán mọi lúc mọi nơi."
- **Nguồn dẫn chứng:** `robot_arm_4dof/robot_arm_4dof.ino` (dòng 30–40, 60–73, 123–128), `grasp_assist_4dof.py` (`ArduinoSerialLink` dòng 346–495).
- **Placeholder cần điền `[...]`:**
  - Model cụ thể của Arduino: `[...]`

---

### SLIDE 12: THIẾT KẾ GIAO DIỆN NGƯỜI DÙNG (HUD & CỬA SỔ HƯỚNG DẪN)
- **Tiêu đề slide:** GIAO DIỆN NGƯỜI DÙNG TRỰC QUAN (HUD & GUIDE SCREEN)
- **Ý chính:**
  1. Cửa sổ hướng dẫn 1280 × 800: Nửa trên tích hợp 2 camera song song, nửa dưới là bảng chỉ dẫn thao tác lớn.
  2. Nút phím Keycap nổi bật: Thiết kế ô phím màu cam `#FFB928` chữ tối `#191B1E` kèm chỉ dẫn số lần bấm (`xN`).
  3. Thanh theo dõi góc servo (`servo_track`): Chấm trắng thể hiện góc hiện tại, vòng tròn màu chỉ góc mục tiêu cần đạt.
  4. Thanh tiến trình kiểm tra: Trực quan hóa tỉ lệ đồng thuận S1/S2 kèm vạch ngưỡng chuẩn $80\%$.
  5. Bảng thẻ kết quả gắp: Thông báo rõ ràng `GAP THANH CONG` hoặc lý do thất bại cụ thể và tỉ lệ tích lũy.
- **Đặc tả Shape / Visual:**
  - Chèn ảnh chụp giao diện thật kích thước lớn: `slides/assets/guide_screen_sample.png` (được sinh từ `fake_assist()` và `build_guide_screen()`).
  - Chú thích 4 vùng nổi bật trên ảnh bằng Callout Shape màu cam:
    1. Vùng 2 Camera quan sát.
    2. Thanh Stepper 5 bước gắp.
    3. Hàng phím Keycap hướng dẫn thao tác theo thứ tự an toàn.
    4. Thẻ kết quả và thanh tiến độ $80\%$.
- **Lời thuyết trình (Speaker Notes):**
  > "Đây là hình ảnh thực tế của cửa sổ 'HƯỚNG DẪN GẮP' với độ phân giải 1280 nhân 800 do nhóm tự động sinh từ mã nguồn. Nửa trên hiển thị song song hai góc camera giúp người quan sát nắm bắt trọn vẹn hiện trường, trong khi nửa dưới là bảng hướng dẫn thao tác được thiết kế tương phản cao trên nền tối. Mỗi khớp servo đều có ô keycap màu cam chỉ rõ phím cần bấm, số lần lặp và thanh trượt trực quan hóa góc xoay. Người vận hành chỉ cần làm theo hướng dẫn từng bước mà không cần phải ghi nhớ bất kỳ thông số kỹ thuật phức tạp nào."
- **Nguồn dẫn chứng:** `guide_screen.py` (`build_guide_screen` dòng 403–410, `render_guide_panel` dòng 384–394, `keycap` dòng 155–159, `meter` dòng 173–181).
- **Placeholder cần điền `[...]`:** Không có.

---

### SLIDE 13: KẾT QUẢ KIỂM THỬ ĐỘNG HỌC & THỰC NGHIỆM HỆ THỐNG
- **Tiêu đề slide:** KẾT QUẢ KIỂM THỬ GIẢI THUẬT VÀ THỰC NGHIỆM
- **Ý chính:**
  1. Kiểm thử giải thuật IK/FK (`test_ik.py`): Đạt 10/10 bài test, $100\%$ vượt qua toàn bộ assertions.
  2. Độ chính xác động học: Thử nghiệm 455 điểm không gian 3D, sai số tuyệt đối $0.000000\text{ mm}$ ($< 0.1\text{ mm}$).
  3. Kiểm tra gợi ý phím: Phím bấm WASD/IK/JL với bước $5^\circ$ chuẩn xác tuyệt đối trên cả 4 khớp.
  4. Số lượt thực nghiệm gắp thực tế: Tổng số `[...]` lượt gắp với các khối hình học khác nhau.
  5. Tỉ lệ gắp thành công: Đạt `[...]%` (Thành công `[...]` lần, Thất bại `[...]` lần).
  6. Phân tích nguyên nhân lỗi thực nghiệm: Kẹp trượt do bề mặt nhẵn `[...]%`, Rơi khi nhấc `[...]%`.
- **Đặc tả Shape / Visual:**
  - Bố cục 2 phần:
    - Bảng kiểm thử mã nguồn (Bên trái - Dữ liệu thật từ `test_ik.py`):
      - 455 điểm 3D kiểm thử: Sai số tối đa $0.000000\text{ mm}$ (PASS ✅).
      - Ánh xạ tọa độ tờ A4 ↔ Robot (up/down): PASS ✅.
      - Phát hiện ngắt kết nối USB/Bluetooth: PASS ✅.
      - Chống báo giả mã đầu kẹp ID 6: PASS ✅.
    - Khung thống kê thực nghiệm phần cứng (Bên phải - Giữ nguyên dạng placeholder `[...]`):
      - Tổng số lần thử nghiệm: `[...]` lượt.
      - Tỉ lệ thành công: `[...]%`.
      - Phân bố lỗi: Kẹp trượt `[...]%` | Rơi khi nâng `[...]%`.
- **Lời thuyết trình (Speaker Notes):**
  > "Về mặt kiểm thử giải thuật, bộ test tự động test_ik.py đã thực thi thành công toàn bộ 10 bài kiểm tra nghiêm ngặt. Trong đó, giải thuật động học ngược được thử nghiệm trên lưới 455 điểm không gian 3 chiều trong tầm với, cho sai số giữa động học thuận và ngược đạt 0.000000 milimet, chứng minh công thức giải tích hoàn toàn chính xác. Đối với phần thực nghiệm trên mô hình thực tế, do hệ thống nhật ký đang tiếp tục ghi nhận, nhóm xin phép thể hiện các chỉ số về số lượt gắp và tỉ lệ thành công dưới dạng số liệu đang hoàn thiện và sẽ cập nhật chi tiết trong buổi báo cáo trực tiếp."
- **Nguồn dẫn chứng:** `test_ik.py` (kết quả chạy thực tế dòng 305–315), `grasp_assist_4dof.py` (`_evaluate_verification_locked` dòng 900–952).
- **Placeholder cần điền `[...]`:**
  - Tổng số lần gắp thực tế: `[...]`
  - Tỉ lệ thành công (%): `[...]`
  - Số lần thành công / thất bại: `[...]`
  - Tỉ lệ lỗi kẹp trượt và rơi vật: `[...]`

---

### SLIDE 14: ĐÁNH GIÁ HẠN CHẾ & HƯỚNG PHÁT TRIỂN MỞ RỘNG
- **Tiêu đề slide:** ĐÁNH GIÁ HẠN CHẾ VÀ HƯỚNG PHÁT TRIỂN
- **Ý chính:**
  1. Hiệu chuẩn góc ngang thủ công: Tỉ lệ `SIDE_TABLE_Y_RATIO = 0.54` cần đo lại khi di chuyển vị trí webcam.
  2. Sai số vị trí đế robot: Ước lượng vị trí đế từ ảnh còn sai số khoảng $\pm 1 \text{–} 2\text{ cm}$ nếu tờ A4 bị xê dịch.
  3. Cơ chế điều khiển hở: Bước nhảy cố định $5^\circ$ chưa có phản hồi encoder góc xoay thực tế của servo.
  4. Hướng nâng cấp 1: Áp dụng thuật toán `solvePnP` kết hợp ma trận camera $3\times3$ để tự động định chuẩn 3D.
  5. Hướng nâng cấp 2: Vòng lặp đóng (Closed-loop) bám vết mã ArUco ID 5 trên đầu kẹp để triệt tiêu sai số.
  6. Hướng nâng cấp 3: Tự động hóa toàn phần (Full-Autonomous) tích hợp quỹ đạo mượt (Trajectory Planning).
- **Đặc tả Shape / Visual:**
  - Bố cục 2 khối đối chiếu (Current Limitations vs Future Roadmap):
    - Khối Hạn chế hiện tại (Viền cam `#FFB928`): Vạch bàn cam ngang thủ công, sai số đế $\pm 1\text{–}2\text{cm}$, servo bước $5^\circ$ vòng hở.
    - Khối Lộ trình nâng cấp (Viền xanh lá `#5AD76E`): Tự định chuẩn qua solvePnP, vòng kín với mã ID 5, tự động gắp hoàn toàn không cần can thiệp tay.
- **Lời thuyết trình (Speaker Notes):**
  > "Nhìn nhận một cách khách quan, hệ thống vẫn tồn tại một số hạn chế nhất định: vị trí vạch mặt bàn của webcam ngang hiện vẫn phụ thuộc vào tỉ lệ đặt trước là 0.54 nên cần canh chỉnh lại nếu dời vị trí laptop, và góc servo bước 5 độ vẫn là điều khiển vòng hở chưa có encoder phản hồi. Trong giai đoạn phát triển tiếp theo, nhóm định hướng tích hợp thuật toán solvePnP để tự động hiệu chuẩn không gian camera 3 chiều, kích hoạt vòng điều khiển kín dựa trên mã ArUco ID 5 gắn ở đầu kẹp, và tiến tới tự động hóa toàn phần quỹ đạo chuyển động của robot."
- **Nguồn dẫn chứng:** `grasp_assist_4dof.py` (dòng 38–42, 81–83, 577–580), `main.py` (dòng 352–361).
- **Placeholder cần điền `[...]`:** Không có.

---

### SLIDE 15: TỔNG KẾT ĐỀ TÀI & PHIÊN HỎI ĐÁP (Q&A)
- **Tiêu đề slide:** TỔNG KẾT DỰ ÁN VÀ HỎI ĐÁP (Q&A)
- **Ý chính:**
  1. Làm chủ giải thuật: Xây dựng thành công động học ngược 4-DOF giải tích chính xác tuyệt đối.
  2. Ứng dụng thị giác kép: Kết hợp hài hòa ArUco định vị không gian và YOLO11s nhận diện linh hoạt.
  3. Trải nghiệm người dùng: Bảng điều khiển "HƯỚNG DẪN GẮP" trực quan, dễ thao tác, tự động đánh giá.
  4. Khả năng nhân rộng: Dễ dàng mở rộng cho các hệ thống robot phân loại sản phẩm trong công nghiệp IoT.
  5. Lời cảm ơn & Q&A: Lắng nghe ý kiến đóng góp và trả lời câu hỏi từ Hội đồng chấm điểm.
- **Đặc tả Shape / Visual:**
  - Khung tóm tắt 3 trụ cột thành công (3 Key Takeaways Pillars):
    1. [Động học chính xác 100%]
    2. [Thị giác kết hợp ArUco + YOLO11s]
    3. [Giao diện hỗ trợ người dùng thời gian thực]
  - Khối biểu tượng "Q&A" lớn ở trung tâm, viền cam `#FFB928`, chữ nổi bật mời đặt câu hỏi.
- **Lời thuyết trình (Speaker Notes):**
  > "Tóm lại, đề tài đã xây dựng thành công một hệ thống hỗ trợ gắp vật hoàn chỉnh cho cánh tay robot 4-DOF, làm chủ từ bài toán giải tích động học ngược, xử lý ảnh thị giác máy tính với ArUco và YOLO11s, cho đến thiết kế giao diện hướng dẫn người dùng trực quan. Hệ thống chứng minh tính khả thi cao và mở ra tiềm năng ứng dụng lớn trong các dây chuyền phân loại sản phẩm mini. Nhóm chúng em xin chân thành cảm ơn quý thầy cô và các bạn đã chú ý lắng nghe, và chúng em rất mong nhận được những câu hỏi và ý kiến đóng góp quý báu."
- **Nguồn dẫn chứng:** `ORIGINAL_REQUEST.md` (R1.15), `orchestrator/PROJECT.md` (Feature 15).
- **Placeholder cần điền `[...]`:** Không có.

---

## 5. TỔNG HỢP CÁC PLACEHOLDER `[...]` VÀ VIỆC CẦN LÀM CỦA NHÓM SINH VIÊN

Để đảm bảo tính toàn vẹn tuyệt đối theo yêu cầu R1 và R4, toàn bộ các thông tin nhóm sinh viên cần điền bổ sung được tổng hợp trong bảng dưới đây:

| Vị trí Slide | Trường thông tin placeholder `[...]` | Trạng thái hiện tại | Hướng dẫn nhóm sinh viên tự cập nhật |
|:---:|:---|:---:|:---|
| **Slide 1** | Tên các thành viên trong nhóm, MSSV, vai trò | `[...]` | Điền danh sách họ tên, mã số sinh viên và phân công nhiệm vụ vào slide tiêu đề. |
| **Slide 1** | Giảng viên hướng dẫn (GVHD) | `[...]` | Điền học hàm, học vị và họ tên thầy/cô hướng dẫn đề tài. |
| **Slide 1** | Tên môn học / Mã lớp học phần / Ngày báo cáo | `[...]` | Điền tên học phần thực tập/đồ án và ngày tổ chức buổi bảo vệ. |
| **Slide 3, 11**| Model bo mạch Arduino cụ thể | `[...]` | Ghi rõ loại bo mạch nhóm đang sử dụng (ví dụ: `Arduino Uno R3` hoặc `Arduino Nano V3`). |
| **Slide 3** | Cấu hình máy tính trạm xử lý | `[...]` | Ghi thông số laptop nhóm dùng chạy demo (ví dụ: `MacBook Air M5 (MPS)` hoặc `Dell XPS 15 (CUDA)`). |
| **Slide 13** | Tổng số lượt gắp thực nghiệm | `[...]` | Vận hành robot thực tế, ghi lại tổng số lần thử nghiệm gắp vật trên bàn. |
| **Slide 13** | Số lần thành công / thất bại & Tỉ lệ (%) | `[...]` | Đọc file `logs/attempts.csv` sau khi chạy thực tế để lấy tỉ lệ % thành công chính xác. |
| **Slide 13** | Phân bố nguyên nhân lỗi thực tế (%) | `[...]` | Thống kê số lần bị lỗi kẹp trượt (`s2 < 0.4`) và rơi vật khi nâng (`s1 < 0.4`). |

### Danh mục công việc nhóm cần thực hiện thêm trước khi thuyết trình:
1. **Chụp ảnh phần cứng thật:** Chụp ảnh cánh tay robot 4-DOF thực tế kèm mạch PCA9685, module HC-05 và dán mã ArUco ID 4, ID 5–6 để chèn thêm vào Slide 3 nếu cần minh họa trực quan.
2. **Quay video demo vận hành:** Quay video ngắn (1–2 phút) ghi lại quá trình robot gắp vật theo hướng dẫn trên màn hình để trình chiếu trong Slide 15.
3. **Chạy thực nghiệm lấy log:** Thực hiện ít nhất 20–30 lần gắp với các khối hộp khác nhau để file `logs/attempts.csv` được sinh ra tự động, từ đó lấy số liệu điền vào các placeholder của Slide 13.

---
*Báo cáo được hoàn thành bởi `teamwork_explorer_m1_3` theo đúng quy chuẩn Teamwork Protocol.*
