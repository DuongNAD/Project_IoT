# BÁO CÁO GIÁM ĐỊNH TÍNH TOÀN VẸN (FORENSIC INTEGRITY AUDIT REPORT)

**Work Product**: Toàn bộ workspace `Project_IoT` và thư mục sản phẩm `slides/`  
**Auditor**: `teamwork_auditor` (Forensic Integrity Auditor)  
**Integrity Mode**: `development` (theo `ORIGINAL_REQUEST.md`)  
**Timestamp**: 2026-11-03T11:28:45Z  
**Final Binary Verdict**: **CLEAN**

---

## 1. TỔNG QUAN KẾT QUẢ GIÁM ĐỊNH (EXECUTIVE SUMMARY)

| STT | Hạng mục kiểm tra | Yêu cầu kiểm tra | Kết quả thực tế | Trạng thái |
|:---:|:---|:---|:---|:---:|
| **1** | **Scope Boundaries** | Không file nào ngoài `slides/` và `.agents/teamwork/` bị sửa đổi hoặc tạo mới bởi team | 100% file ngoài `slides/` giữ nguyên timestamp trước giờ phê duyệt tác vụ | **PASS** |
| **2** | **Source Code Preservation** | Source code (`main.py`, `grasp_assist_4dof.py`, `guide_screen.py`, `generate_aruco_a4.py`, `test_ik.py`, `test_base_servo.py`, `robot_arm_4dof/*`), `pyproject.toml`, `uv.lock` 100% UNMODIFIED | Không có bất kỳ thay đổi nào từ phía team | **PASS** |
| **3** | **Git Integrity** | Không có lệnh `git commit` hoặc `git push` nào được thực thi | Git log chỉ có duy nhất 1 commit gốc `21b07ae` ngày 29/10/2026 | **PASS** |
| **4** | **Media Integrity** | `guide_screen_sample.png` tạo bằng mã nguồn từ `fake_assist()`, `build_guide_screen()`, `aruco_A4_grid.png`; không có ảnh AI | Sinh tự động 100% bằng code OpenCV, không sử dụng công cụ AI sinh ảnh | **PASS** |
| **5** | **Metric & Fabrication Check** | Không bịa đặt số liệu; các thông tin chưa có trong workspace giữ nguyên dạng `[...]` | Toàn bộ thông số thực nghiệm, tên thành viên, GVHD, lớp, loại board giữ nguyên `[...]` | **PASS** |
| **6** | **Technical Constants Match** | 100% hằng số kỹ thuật trên slide khớp với mã nguồn | Khớp tuyệt đối với `ARM_CONFIG`, `SERVO_LIMITS`, `ROBOT_BT_DEFAULT`, PCA9685, ArUco IDs | **PASS** |
| **7** | **Slide Generation & Presentation** | File `Project_IoT_ThuyetTrinh.pptx` tạo thành công, 15 slide, 16:9 widescreen, notes tiếng Việt, footer | 15 slide đầy đủ, kích thước ~326 KB, đầy đủ speaker notes và footer | **PASS** |

---

## 2. BẰNG CHỨNG THỰC NGHIỆM CHI TIẾT (EMPIRICAL EVIDENCE)

### 2.1. Kiểm tra ranh giới phạm vi (Scope Boundaries & Git Porcelain)

#### Lệnh thực thi:
```powershell
git status --porcelain
```
#### Kết quả trích xuất:
```text
 M grasp_assist_4dof.py
 M guide_screen.py
 M main.py
 M pyproject.toml
 M test_base_servo.py
 M test_ik.py
?? .agents/
?? prompt_slide_antigravity.md
?? slides/
```

#### Phân tích thời gian sửa đổi (Modification Timestamps Analysis):
- Thời điểm phê duyệt yêu cầu tác vụ (`ORIGINAL_REQUEST.md`): `2026-11-03T10:21:13Z`
- Khởi tạo thư mục quản lý agent `.agents/`: `2026-11-03T09:58:13Z`
- Bảng thời gian sửa đổi file gốc trong workspace:
  - `grasp_assist_4dof.py`: `2026-11-03 09:00:58 UTC` (Trước thời điểm phê duyệt)
  - `guide_screen.py`: `2026-10-30 05:37:21 UTC` (Trước thời điểm phê duyệt)
  - `main.py`: `2026-11-03 09:00:42 UTC` (Trước thời điểm phê duyệt)
  - `pyproject.toml`: `2026-11-03 08:45:31 UTC` (Trước thời điểm phê duyệt)
  - `test_base_servo.py`: `2026-10-29 08:52:04 UTC` (Trước thời điểm phê duyệt)
  - `test_ik.py`: `2026-11-03 09:01:49 UTC` (Trước thời điểm phê duyệt)
  - `prompt_slide_antigravity.md`: `2026-11-03 09:52:46 UTC` (Trước thời điểm phê duyệt)
  - `uv.lock`: `2026-10-29 08:26:39 UTC` (Trước thời điểm phê duyệt)
  - `robot_arm_4dof/robot_arm_4dof.ino`: `2026-10-29 08:26:39 UTC` (Trước thời điểm phê duyệt)

#### Kiểm tra tìm kiếm file bị sửa đổi sau thời điểm 10:21:13Z ngoài `slides/` và `.agents/`:
```powershell
Get-ChildItem -Path . -Recurse -Force | Where-Object { 
    $_.LastWriteTimeUtc -gt [DateTime]::Parse("2026-11-03T10:21:13Z") -and 
    $_.FullName -notmatch '\\slides\\' -and 
    $_.FullName -notmatch '\\.agents\\' -and 
    $_.FullName -notmatch '\\.git\\' 
} | Select-Object FullName, LastWriteTimeUtc
```
**Kết quả**: `No output` (Không có bất kỳ file mã nguồn, cấu hình hay dữ liệu nào bị thay đổi).  
*(Lưu ý: Chỉ có các file bytecode `.pyc` tạm trong `__pycache__` được sinh ra tự động bởi trình thông dịch Python khi chạy test kiểm thử)*.

---

### 2.2. Kiểm tra tính toàn vẹn Git (Git Commit & Push Integrity)

#### Lệnh thực thi:
```powershell
git log --oneline
```
#### Kết quả trích xuất:
```text
21b07ae feat: import 4-DOF robot arm grasp assistant (Python + Arduino)
```
- Tổng số commit trong lịch sử: Đúng 1 commit duy nhất của tác giả gốc từ ngày 29/10/2026.
- Không có bất kỳ lệnh `git commit` nào được gọi bởi team.
- Không có bất kỳ lệnh `git push` nào được gọi bởi team.

---

### 2.3. Kiểm tra tính toàn vẹn hình ảnh (Media & Asset Integrity)

#### Phân tích tạo ảnh `slides/assets/guide_screen_sample.png`:
- File script sinh ảnh: `slides/generate_asset.py`
- Cơ chế sinh ảnh:
  - Khởi tạo môi trường ảo với hàm `fake_assist()` từ `test_ik.py`.
  - Cấu hình vật thể mẫu: `Hop_Xanh_ID11` tại tọa độ `(15.0, 8.0)` cm.
  - Sử dụng ảnh lưới ArUco thật có sẵn trong workspace: `aruco_A4_grid.png`.
  - Vẽ khung nhìn camera ngang dựa trên tỷ lệ thực tế `SIDE_TABLE_Y_RATIO = 0.54` và `SIDE_LIFT_RATIO = 0.065`.
  - Gọi trực tiếp hàm hiển thị giao diện gốc `guide_screen.build_guide_screen()`.
  - Xuất ảnh bằng `cv2.imwrite` sang định dạng PNG (kích thước chuẩn 1280x800).
- Kiểm tra sự hiện diện của công cụ AI sinh ảnh:
  - Lệnh tìm kiếm gọi tool `generate_image` trong toàn bộ lịch sử agent: `No results found`.
  - Không có bất kỳ ảnh giả lập phần cứng hay kết quả thực nghiệm nào do AI tạo.
- Các ảnh preview trong `slides/preview/` (`slide_01.png` đến `slide_15.png`): Được trích xuất trực tiếp từ file PDF render thực tế thông qua thư viện `PyMuPDF` (`fitz`).

---

### 2.4. Kiểm tra việc bảo tồn thông số và không bịa đặt số liệu (Metric & Fabrication Check)

#### Đối chiếu các placeholder `[...]` trong `slides/build_slides.py`:
1. **Slide 1 (Tiêu đề)**:
   - `Sinh viên thực hiện: [...]`
   - `Giảng viên hướng dẫn: [...]`
   - `Lớp / Môn học: [...]`
   - `Thời gian báo cáo: [...]`
2. **Slide 3 (Phần cứng)**:
   - `Vi điều khiển trung tâm: Bo mạch Arduino [...]`
   - `Máy tính xử lý trung tâm: Laptop [...]`
3. **Slide 13 (Kiểm thử & Thực nghiệm)**:
   - `Tổng số lượt thử nghiệm gắp: [...] lượt.`
   - `Tỉ lệ gắp thành công: [...]% (Thành công [...] lượt, Thất bại [...] lượt).`
   - `Phân bố nguyên nhân thất bại thực nghiệm:`
     - `Lỗi kẹp trượt (vật vẫn ở chỗ cũ): [...]%`
     - `Lỗi rơi khi nâng (vật rơi lúc nhấc cao): [...]%`
     - `Lỗi bị che khuất tầm nhìn: [...]%`
   - `Sai số căn chỉnh đầu kẹp thực tế: align_error_mm = [...] mm.`
   - `Thời gian trung bình hoàn thành 5 bước: [...] giây/lượt.`

#### Xác minh sự tồn tại của file `logs/attempts.csv`:
```powershell
Test-Path logs\attempts.csv
```
**Kết quả**: `False` (File không tồn tại trong workspace).  
Nhóm đã tuân thủ 100% nguyên tắc: do chưa có dữ liệu thực nghiệm thật trên cánh tay vật lý, toàn bộ chỉ số thực nghiệm được bảo lưu trung thực dưới dạng `[...]`, tuyệt đối không tự ý đưa ra các tỷ lệ phần trăm bịa đặt.

---

### 2.5. Kiểm tra tính chính xác của 100% hằng số kỹ thuật (Technical Constants Match)

Toàn bộ các hằng số kỹ thuật xuất hiện trong `slides/build_slides.py` đã được đối chiếu đối sánh 1:1 với mã nguồn dự án:

1. **Thông số cơ học cánh tay (`ARM_CONFIG` trong `grasp_assist_4dof.py`)**:
   - `d1_mm = 70.0` (Chiều cao khớp vai: 70.0 mm)
   - `L2_mm = 105.0` (Khâu vai: 105.0 mm)
   - `L3_mm = 100.0` (Khâu khuỷu: 100.0 mm)
   - `L4_r_mm = 65.0` (Độ vươn kẹp: 65.0 mm)
   - `L4_z_mm = 25.0` (Độ trễ kẹp: 25.0 mm)
   - `theta2_at_90_deg = 45.0°`, `theta3_at_90_deg = -45.0°`
   - `base_x_cm = 18.0`, `base_y_cm = -13.6`, `robot_faces = "down"`
   - Tầm với: Tối đa 205.0 mm, tối thiểu 5.0 mm.

2. **Giới hạn Servo và bước lượng tử hóa (`SERVO_LIMITS` & `SERVO_STEP_DEG`)**:
   - Kênh 0 (Đế): `[0°, 180°]`, mặc định 90°
   - Kênh 1 (Vai): `[25°, 155°]`, mặc định 90°
   - Kênh 2 (Khuỷu): `[25°, 155°]`, mặc định 90°
   - Kênh 3 (Kẹp): `[95°, 175°]`, mở 95°–125°, kẹp chặt 165°
   - `SERVO_STEP_DEG = 5°`

3. **Mạch xung PCA9685 & Vi điều khiển**:
   - Địa chỉ I2C: `0x40`, tần số xung: `50 Hz`
   - Độ rộng xung PWM: 125 (~0°) đến 575 (~180°) xung 12-bit
   - Bluetooth HC-05: Chân SoftwareSerial RX=D2, TX=D3, tốc độ 9600 baud, MAC mặc định `98D351F6AF14` (`ROBOT_BT_DEFAULT`)

4. **Hệ ArUco và xử lý ảnh**:
   - Bộ từ điển: `cv2.aruco.DICT_4X4_50`
   - Tờ A4: 29.7 x 21.0 cm; 4 góc ID 0, 1, 2, 3 kích thước 2.8 x 2.8 cm (cách mép 0.25 cm)
   - Mã ID 4: Đế robot; ID 5, 6: Đầu kẹp; ID 10–29: Vật thể mẫu
   - Ngưỡng lọc trùng ArUco-YOLO: khoảng cách `< 2.5 cm`
   - Bộ lọc làm mịn: Trung bình trượt 10 khung hình (`deque(maxlen=10)`)
   - Cam ngang: `SIDE_TABLE_Y_RATIO = 0.54`, `SIDE_LIFT_RATIO = 0.065`

5. **Quy trình gắp và xác nhận 2 camera**:
   - 5 bước: Điểm chờ (+60 mm) → Hạ xuống điểm kẹp → Đóng kẹp (165°) → Nâng lên (+80 mm) → Kiểm tra
   - S1 (cam ngang): Vật vượt ngưỡng nâng +20 mm (loại trừ mã ID 6 của đầu kẹp)
   - S2 (cam trên): Vị trí cũ sạch vật trong bán kính 3.0 cm
   - Cửa sổ đồng thuận: 30 khung hình, tỷ lệ đạt đồng thời `>= 80%` (24/30 khung)
   - Giới hạn thời gian xác nhận: Timeout 3.0 giây

---

### 2.6. Thực thi kiểm thử động học độc lập (`test_ik.py`)

#### Lệnh thực thi:
```powershell
$env:PYTHONIOENCODING="utf-8"; python test_ik.py
```
#### Kết quả trích xuất:
```text
✅ [PASS] Đã kiểm thử 455 điểm 3D trong tầm với: sai số FK(IK(p)) tối đa = 0.000000 mm (< 0.1 mm)
✅ [PASS] Kiểm thử gợi ý bấm phím (WASD + IK + JL) với STEP = 5° chính xác tuyệt đối!
✅ [PASS] Ánh xạ tờ A4 <-> hệ robot đúng cho cả hai hướng đặt robot (up / down)
✅ [PASS] Phát hiện board không nhận lệnh USB (firmware cũ)
✅ [PASS] Tìm cổng Bluetooth của HC-05 (Windows theo địa chỉ MAC, macOS theo tên cổng)
✅ [PASS] Gửi lệnh qua Bluetooth HC-05, tự quay về USB khi BT đứt
✅ [PASS] S1 chỉ tính mã của vật (ID 10-29), kẹp rỗng nâng lên không bị báo là đã gắp
📝 Đã ghi kết quả gắp vào ...\logs\attempts.csv: SUCCESS (ok)
✅ [PASS] Khóa vật lúc đóng kẹp cho bước nâng + kiểm tra, log CSV ghi đúng sai số căn đầu kẹp
✅ [PASS] Chuẩn hóa địa chỉ IP Webcam của điện thoại
📷 Camera: 0=Duong's iPhone Desk View Camera, 1=Duong's iPhone Camera, 2=MacBook Air Camera
📷 Camera: 0=OBS Virtual Camera, 1=MacBook Air Camera
✅ [PASS] Nhận camera MacBook và iPhone (Continuity Camera) theo tên trên macOS
```
- Toàn bộ 10/10 bài kiểm thử đơn vị và tích hợp trong `test_ik.py` đạt kết quả PASS 100% với exit code 0.
- Kết quả kiểm thử thực tế này hoàn toàn trùng khớp với nội dung trình bày trên Slide 13.

---

### 2.7. Tái tạo độc lập và xác minh tệp thuyết trình (`slides/verify_slides.py`)

#### Lệnh thực thi:
```powershell
$env:PYTHONIOENCODING="utf-8"; python slides/verify_slides.py
```
#### Kết quả trích xuất:
```text
VERIFYING: E:\03_Development_Projects\project\Project_IoT\slides\Project_IoT_ThuyetTrinh.pptx
File size: 326,587 bytes
Slide width: 13.333 in (expected ~13.333)
Slide height: 7.500 in (expected ~7.500)
Total slides: 15 (expected 15)
Slide 01: shapes=16, img=False, footer=YES, notes_len=520
Slide 02: shapes=12, img=False, footer=YES, notes_len=542
Slide 03: shapes=12, img=False, footer=YES, notes_len=451
Slide 04: shapes=24, img=False, footer=YES, notes_len=533
Slide 05: shapes=12, img=False, footer=YES, notes_len=540
Slide 06: shapes=12, img=False, footer=YES, notes_len=520
Slide 07: shapes=12, img=False, footer=YES, notes_len=527
Slide 08: shapes=12, img=False, footer=YES, notes_len=499
Slide 09: shapes=44, img=False, footer=YES, notes_len=528
Slide 10: shapes=12, img=False, footer=YES, notes_len=596
Slide 11: shapes=20, img=False, footer=YES, notes_len=538
Slide 12: shapes=09, img=True, footer=YES, notes_len=524
Slide 13: shapes=12, img=False, footer=YES, notes_len=581
Slide 14: shapes=12, img=False, footer=YES, notes_len=547
Slide 15: shapes=14, img=False, footer=YES, notes_len=525
ALL PRESENTATION VERIFICATION CHECKS PASSED SUCCESSFULLY!
```

---

## 3. KẾT LUẬN VÀ PHÁN QUYẾT GIÁM ĐỊNH (FINAL AUDIT VERDICT)

Căn cứ trên toàn bộ bằng chứng pháp y thu thập độc lập từ file hệ thống, nhật ký git, mã nguồn và quá trình chạy kiểm thử:
- Workspace hoàn toàn tuân thủ các ràng buộc phạm vi nghiêm ngặt đã đề ra trong `ORIGINAL_REQUEST.md`.
- Không có bất kỳ vi phạm tính toàn vẹn (Integrity Violation), bịa đặt số liệu hay chỉnh sửa mã nguồn trái phép nào.

**PHÁN QUYẾT CUỐI CÙNG**: **CLEAN** (HỢP LỆ VÀ TOÀN VẸN 100%)
