# BÁO CÁO BÀN GIAO (HANDOFF REPORT) - TEAMWORK CHALLENGER 2

**Agent**: `teamwork_challenger_2` (Empirical Challenger - critic, specialist)  
**Tác vụ**: Đối chiếu nghịch biến toàn bộ thông số, con số, công thức, phím bấm và placeholder trên slide với mã nguồn thực tế  
**Tệp mục tiêu**: `slides/Project_IoT_ThuyetTrinh.pptx`  
**Handoff Type**: Hard (Hoàn thành đầy đủ 100% mục tiêu nhiệm vụ)

---

## 1. Observation (Quan sát trực tiếp)

- **Mã nguồn và hằng số ground truth**:
  - `grasp_assist_4dof.py:32-52`: `ARM_CONFIG` định nghĩa `d1_mm: 70.0`, `L2_mm: 105.0`, `L3_mm: 100.0`, `L4_r_mm: 65.0`, `L4_z_mm: 25.0`, `base_x_cm: 18.0`, `base_y_cm: -13.6`, `robot_faces: "down"`, `theta2_at_90_deg: 45.0`, `theta3_at_90_deg: -45.0`.
  - `grasp_assist_4dof.py:55-61`: `SERVO_STEP_DEG: 5`, `SERVO_LIMITS`: `base: (0, 180, 90)`, `shoulder: (25, 155, 90)`, `elbow: (25, 155, 90)`, `grip: (95, 175, 95)`.
  - `main.py:265-271`: `NOTEBOOK_W_CM = 29.7`, `NOTEBOOK_H_CM = 21.0`, `ARUCO_DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)`.
  - `generate_aruco_a4.py:36-37`: `MARKER_SIZE_CM = 2.8`, `MARGIN_CM = 0.25`.
  - `guide_screen.py:27-37`: `BG = (30, 27, 25)` (#191B1E), `CARD = (46, 42, 39)` (#272A2E), `CARD_EDGE = (82, 76, 70)` (#464C52), `WHITE = (245, 245, 245)` (#F5F5F5), `MUTED = (165, 160, 155)` (#9BA0A5), `AMBER = (40, 185, 255)` (#FFB928), `GREEN = (110, 215, 90)` (#5AD76E), `RED = (85, 85, 245)` (#F55555).
  - `robot_arm_4dof/robot_arm_4dof.ino`: `Adafruit_PWMServoDriver(0x40)`, `setPWMFreq(50)`, `SERVOMIN 125`, `SERVOMAX 575`, `SoftwareSerial BT(2, 3)`, `Serial.begin(9600)`, `STEP 5`, chu kỳ gửi JSON định kỳ 200ms (5Hz).
- **Thực thi kiểm thử tự động độc lập**:
  - Lệnh 1: `$env:PYTHONIOENCODING="utf-8"; python test_ik.py`
    - Kết quả: `10/10 PASS`, `Đã kiểm thử 455 điểm 3D trong tầm với: sai số FK(IK(p)) tối đa = 0.000000 mm (< 0.1 mm)`.
  - Lệnh 2: `$env:PYTHONIOENCODING="utf-8"; python .agents/teamwork/teamwork_challenger_2/adversarial_verification.py`
    - Kết quả: Toàn bộ 15 slide được bóc tách và đối chiếu tự động, ghi nhận `Placeholders properly preserved: 16 instances found`, `0 fabricated experimental metrics found`, toàn bộ tham số kỹ thuật đạt chuẩn 100%, xuất kết quả `VERDICT: APPROVE`.
  - Lệnh 3: `$env:PYTHONIOENCODING="utf-8"; python .agents/teamwork/teamwork_challenger_2/deep_stress_harness.py`
    - Kết quả: Kích thước 13.333 x 7.500 inches (16:9), phân tầng font Arial & Courier New, 13 khối shape/keycap cam, tệp `slides/Project_IoT_ThuyetTrinh.pdf` (575,414 bytes, 15 trang), và 15 ảnh PNG preview trong `slides/preview/` đúng chuẩn 2000x1125 px.

---

## 2. Logic Chain (Chuỗi lập luận suy diễn)

1. Từ việc `logs/attempts.csv` không tồn tại trong workspace thực tế (tìm kiếm thấy 0 kết quả), bất kỳ con số cụ thể nào khẳng định số lượt thử nghiệm hoặc tỉ lệ thành công trên slide đều sẽ bị coi là bịa đặt.
2. Kiểm tra trực tiếp trên Slide 13 cho thấy toàn bộ các chỉ số về lượt gắp, tỉ lệ thành công, lý do thất bại, sai số căn chỉnh và thời gian hoàn thành đều được giữ nguyên ở dạng placeholder `[...]` (tổng cộng 9 placeholder trên Slide 13 và 16 placeholder trên toàn bộ bài thuyết trình).
3. Các con số xuất hiện trên các slide khác đều được truy xuất trực tiếp và đối chiếu khớp 100% với các hằng số cấu hình cơ khí (`ARM_CONFIG`), giới hạn góc (`SERVO_LIMITS`), thông số ArUco và kích thước A4 (`main.py`, `generate_aruco_a4.py`), địa chỉ I2C, chân BT và tần số PWM (`robot_arm_4dof.ino`), và kết quả chạy thực nghiệm thật của `test_ik.py` (455 điểm 3D, sai số 0.000000 mm).
4. Slide 12 nhúng trực tiếp ảnh chụp giao diện thật được sinh từ mã nguồn (`fake_assist()` + `guide_screen.build_guide_screen()`), không sử dụng bất kỳ ảnh AI nào.
5. Do đó, bài trình chiếu đáp ứng tuyệt đối tiêu chuẩn chất lượng, tính chính xác và nguyên tắc trung thực khoa học theo yêu cầu của dự án.

---

## 3. Caveats (Các điểm cần lưu ý)

- Khi trình diễn trên hệ thống thực tế với phần cứng Arduino và cánh tay cơ khí vật lý, nhóm sinh viên cần điền các số liệu đo thực tế từ `logs/attempts.csv` vào các vị trí `[...]` trên Slide 13 và thông tin thành viên nhóm/giảng viên trên Slide 1.
- Nếu di chuyển vị trí webcam laptop, tỉ lệ mặt bàn `SIDE_TABLE_Y_RATIO = 0.54` cần được chụp ảnh lại (phím `C`) và cập nhật lại theo hướng dẫn đã nêu rõ tại Slide 14.
- Không có caveat nào làm ảnh hưởng đến tính hợp lệ của bài trình chiếu hiện tại.

---

## 4. Conclusion (Kết luận và Quyết nghị)

- **Độ chính xác kỹ thuật**: 100% (0 sai lệch giữa slide và mã nguồn).
- **Tính toàn vẹn của placeholder**: 16/16 placeholder `[...]` được bảo toàn nguyên vẹn, không bị biến dạng.
- **Tính trung thực dữ liệu**: 0 số liệu thực nghiệm bịa đặt.
- **Quyết nghị**: **APPROVE (CHẤP THUẬN TOÀN BỘ)**.

---

## 5. Verification Method (Phương pháp tái kiểm tra độc lập)

Bất kỳ thành viên nào trong nhóm hoặc người dùng có thể tự kiểm tra lại kết quả trên môi trường Windows bằng 2 lệnh PowerShell sau:
```powershell
# 1. Chạy bài test động học ngược và kiểm thử giải thuật
$env:PYTHONIOENCODING="utf-8"; python test_ik.py

# 2. Chạy bài kiểm tra đối chiếu nghịch biến tự động toàn bộ 15 slide
$env:PYTHONIOENCODING="utf-8"; python .agents/teamwork/teamwork_challenger_2/adversarial_verification.py

# 3. Chạy bài stress test kích thước 16:9, typography, PDF và PNG preview
$env:PYTHONIOENCODING="utf-8"; python .agents/teamwork/teamwork_challenger_2/deep_stress_harness.py
```
Điều kiện vô hiệu hóa kết luận (Invalidation Conditions): Nếu bất kỳ lệnh nào trên trả về exit code khác 0, hoặc phát hiện thấy bất kỳ tham số nào trên slide sai khác với mã nguồn trong workspace.
