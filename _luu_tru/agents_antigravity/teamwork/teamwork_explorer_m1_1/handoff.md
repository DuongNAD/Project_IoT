# Báo Cáo Handoff (Handoff Report) — teamwork_explorer_m1_1

- **Người gửi**: `teamwork_explorer_m1_1` (Explorer: Động học, Cấu hình, Tọa độ và Kiểm thử)
- **Người nhận**: `parent` (`00c906d7-900c-42be-a553-3eacb15019c9`)
- **Ngày**: 2026-11-03T10:34:00Z
- **Loại Handoff**: Hard Handoff (Nhiệm vụ điều tra M1 hoàn tất 100%)

---

## 1. Observation (Quan Sát Trực Tiếp)

1. **Thông số cơ khí và tọa độ trong `ARM_CONFIG`** (`grasp_assist_4dof.py:32-52`):
   ```python
   ARM_CONFIG = {
       "d1_mm": 70.0,
       "L2_mm": 105.0,
       "L3_mm": 100.0,
       "L4_r_mm": 65.0,
       "L4_z_mm": 25.0,
       "base_x_cm": 18.0,
       "base_y_cm": -13.6,
       "robot_faces": "down",
       "theta2_at_90_deg": 45.0,
       "theta3_at_90_deg": -45.0,
   }
   ```
2. **Giới hạn servo và bước nhảy trong `SERVO_LIMITS`** (`grasp_assist_4dof.py:55-61`) và `robot_arm_4dof.ino:8-20`:
   - `SERVO_STEP_DEG = 5`
   - `SERVO_LIMITS = {"base": (0, 180, 90), "shoulder": (25, 155, 90), "elbow": (25, 155, 90), "grip": (95, 175, 95)}`
   - Arduino PCA9685: I2C `0x40`, tần số `50Hz`, dải xung `SERVOMIN = 125` (~0°), `SERVOMAX = 575` (~180°).
3. **Công thức giải tích FK / IK** (`grasp_assist_4dof.py:88-155`):
   - FK: $r_w = L_2 \cos(t_2) + L_3 \cos(t_{23})$, $z_w = L_2 \sin(t_2) + L_3 \sin(t_{23})$, $r = r_w + L_{4r}$, $z = d_1 + z_w - L_{4z}$, $x = r \cos(t_1)$, $y = r \sin(t_1)$.
   - IK: $\theta_1 = \text{atan2}(y, x)$, $r_w = \max(5.0, r - L_{4r})$, $z_w = (z + L_{4z}) - d_1$. Nghiệm khuỷu hướng lên ($\sin(\theta_3) \le 0$):
     $$\theta_{3\text{rad}} = \text{atan2}\left(-\sqrt{\max(0.0, 1.0 - D^2)},\; D\right), \quad D = \frac{r_w^2 + z_w^2 - L_2^2 - L_3^2}{2 L_2 L_3}$$
     $$\theta_{2\text{rad}} = \text{atan2}(z_w, r_w) - \text{atan2}\left(L_3 \sin(\theta_{3\text{rad}}),\; L_2 + L_3 \cos(\theta_{3\text{rad}})\right)$$
4. **Quy đổi góc sang servo** (`grasp_assist_4dof.py:157-194`):
   - Đế: $\text{raw} = 90.0 + \theta_1$.
   - Vai: $\text{raw} = 90.0 + (\theta_2 - 45.0)$.
   - Khuỷu: $\text{raw} = 90.0 + (\theta_3 - (-45.0)) = 90.0 + (\theta_3 + 45.0)$.
   - Kẹp: đóng = 165°, mở = $95.0 + \text{ratio} \times 30.0 \in [95^\circ, 125^\circ]$.
   - Lượng tử hóa 5°: `int(round(clamped / 5.0) * 5)`.
5. **Chuyển đổi tờ A4 sang Robot** (`grasp_assist_4dof.py:227-250`):
   - Với `robot_faces == "down"` ($s = -1.0$):
     $x_{\text{robot\_mm}} = (y_{\text{cm}} - \text{base\_y\_cm}) \times 10.0 = (y_{\text{cm}} + 13.6) \times 10.0$
     $y_{\text{robot\_mm}} = (x_{\text{cm}} - \text{base\_x\_cm}) \times 10.0 = (x_{\text{cm}} - 18.0) \times 10.0$
6. **Máy trạng thái gắp 5 bước** (`STAGE_NAMES`, `grasp_assist_4dof.py:546-552, 658-678, 1010-1054`):
   - Bước 1: Điểm chờ ($Z_{\text{grasp}} + 60\text{ mm}$, mở kẹp).
   - Bước 2: Hạ xuống ($Z_{\text{grasp}}$, mở kẹp).
   - Bước 3: Đóng kẹp ($Z_{\text{grasp}}$, đóng kẹp 165°, khóa `locked_grasp_cm`, `locked_obj`, `locked_align_err_mm`).
   - Bước 4: Nâng vật ($Z_{\text{grasp}} + 80\text{ mm}$, giữ kẹp).
   - Bước 5: Xác nhận 2 cam (giữ nâng, kích hoạt cửa sổ 30 khung).
   - Thứ tự an toàn: Đế (0) $\rightarrow$ Kẹp (3) $\rightarrow$ Vai (1) $\rightarrow$ Khuỷu (2).
   - Auto-Step phím `P`: chu kỳ 0.28s / 1 bước.
7. **Thuật toán tự động xác nhận** (`grasp_assist_4dof.py:772-797, 852-952`):
   - S1 (Cam B - nhìn ngang): $y_{\text{table}} = 0.54h$, $y_{\text{lift}} = y_{\text{table}} - 0.065h$ (+20mm); ArUco ID 10–29 hoặc đáy YOLO; **bỏ qua mã ID 6 của đầu kẹp**.
   - S2 (Cam A - nhìn trên): vòng tròn bán kính $3.0\text{ cm}$ quanh vị trí cũ không còn vật thể.
   - Cửa sổ 30 frames: thành công khi cả hai đạt $\ge 80\%$.
   - Timeout 3.0s: phân loại $s2 < 0.40 \rightarrow$ kẹp trượt; $s1 < 0.40 \rightarrow$ rơi khi nâng; còn lại $\rightarrow$ không xác định.
   - Nhật ký: `logs/attempts.csv` gồm 9 cột.
8. **Chạy kiểm thử `test_ik.py`**:
   - Chạy lệnh `python -X utf8 test_ik.py` thành công: Exit code `0`.
   - Kết quả: `Đã kiểm thử 455 điểm 3D trong tầm với: sai số FK(IK(p)) tối đa = 0.000000 mm (< 0.1 mm)`. Vượt qua 10/10 bài kiểm thử.
9. **Tình trạng file `logs/attempts.csv`**:
   - Kiểm tra `find_by_name`: Không tìm thấy `attempts.csv` hay thư mục `logs/` trong workspace.

---

## 2. Logic Chain (Chuỗi Lập Luận)

1. Từ **Observation 1, 2, 3, 4**: Mô hình động học 4-DOF bao gồm 3 khâu chuyển động phẳng trong mặt phẳng thẳng đứng ($L_2, L_3$ cùng phần bù đầu kẹp $L_{4r}, L_{4z}$) và 1 khớp xoay đế quanh trục thẳng đứng $\theta_1$. Việc lựa chọn nghiệm giải tích khuỷu hướng lên ($\sin(\theta_3) \le 0$) là bắt buộc do kết cấu cơ khí của tay gắp (tránh va đập vào mặt bàn hoặc thân robot).
2. Từ **Observation 4**: Khớp vai và khuỷu của servo MG996R được căn chỉnh góc 90° ứng với $\theta_2 = 45^\circ$ và $\theta_3 = -45^\circ$. Vì vậy, công thức ánh xạ cộng trừ góc lệch tương ứng là chuẩn xác tuyệt đối và ăn khớp với hàm `snap_and_clamp` bước 5°.
3. Từ **Observation 5**: Hướng đặt robot `robot_faces = "down"` tại tọa độ $(18.0, -13.6)\text{ cm}$ quy định trục $+X_{\text{robot}}$ đi sâu vào tờ A4 ($+Y_{\text{A4}}$) và $+Y_{\text{robot}}$ đi sang trái của robot ($+X_{\text{A4}}$). Hệ số $s = -1.0$ thực hiện phép đổi trục và bù tịnh tiến chính xác.
4. Từ **Observation 6, 7**: Để tránh trường hợp vật mẫu sau khi nâng lên bị biến mất khỏi danh sách quan sát của camera trên làm hệ thống mất mục tiêu hoặc tính toán sai vị trí, việc khóa vị trí (`locked_grasp_cm`) và thông số kích thước (`locked_obj`) tại thời điểm chuyển sang Bước 3 là mắt xích then chốt giúp Bước 4 và Bước 5 hoạt động tin cậy. Đồng thời, việc loại trừ mã ID 6 của đầu kẹp khỏi điều kiện S1 ngăn chặn hoàn toàn lỗi báo thành công giả khi kẹp rỗng nâng lên.
5. Từ **Observation 8, 9**: Toàn bộ 455 điểm kiểm thử 3D trong không gian làm việc đạt sai số bằng 0.000000 mm khẳng định tính đúng đắn toán học của thuật toán IK/FK. Tệp `logs/attempts.csv` chưa tồn tại trong workspace chứng minh hệ thống chưa từng chạy thu thập dữ liệu thực tế tại workspace hiện tại; do đó theo đúng nguyên tắc R1.13 và Integrity constraints, các slide thuyết trình bắt buộc phải giữ nguyên placeholder `[...]`, không được bịa đặt bất kỳ con số thực nghiệm nào.

---

## 3. Caveats (Khu Vực Chưa Khảo Sát / Giả Định)

1. **Hiệu chỉnh góc nhìn thực tế**: Tỉ lệ vạch bàn `SIDE_TABLE_Y_RATIO = 0.54` và vị trí đế `(18.0, -13.6) cm` được ghi nhận trong mã nguồn là số liệu đo từ cấu hình camera cũ bằng laptop/điện thoại cụ thể. Khi dịch chuyển vị trí camera hoặc tờ giấy A4, người dùng cần căn chỉnh lại hoặc dán chặt tờ A4.
2. **Môi trường chạy `test_ik.py`**: Lệnh mặc định `python test_ik.py` trên Windows có thể gặp lỗi mã hóa `cp1252` với ký tự emoji Unicode (`\u2705`). Khi chạy cần sử dụng cờ `python -X utf8 test_ik.py` hoặc thiết lập biến môi trường `PYTHONIOENCODING=utf-8`.
3. **Dữ liệu thực nghiệm**: Không có file `logs/attempts.csv` có sẵn trong workspace.

---

## 4. Conclusion (Kết Luận)

1. Toàn bộ tham số cấu hình, giới hạn góc, công thức động học thuận/ngược, chuyển đổi tọa độ tờ A4 và quy trình gắp 5 bước đã được khảo sát toàn diện và chứng minh toán học với độ chính xác cao.
2. Kết quả chạy kiểm thử thực tế `test_ik.py` đạt **455/455 điểm 3D hợp lệ**, sai số tối đa $0.000000\text{ mm}$, vượt qua 10/10 bài kiểm tra.
3. Vì `logs/attempts.csv` chưa có, toàn bộ thông số thực nghiệm (tổng số lần gắp, tỉ lệ thành công, số lần trượt/rơi) trên slide 13 sẽ được giữ dưới dạng placeholder `[...]`.
4. Báo cáo chi tiết `report.md` đã sẵn sàng cung cấp nguồn dẫn chứng chính xác (tên file, số dòng) cho Milestone M2 (Dựng slide tự động bằng `python-pptx`).

---

## 5. Verification Method (Phương Pháp Xác Minh Độc Lập)

1. **Kiểm tra chạy test suite**:
   Chạy lệnh sau tại thư mục gốc workspace:
   ```powershell
   python -X utf8 test_ik.py
   ```
   *Điều kiện hợp lệ*: Exit code 0, 10 dòng `[PASS]`, thông báo `Đã kiểm thử 455 điểm 3D trong tầm với: sai số FK(IK(p)) tối đa = 0.000000 mm (< 0.1 mm)`.
2. **Kiểm tra file báo cáo**:
   Xem file `e:\03_Development_Projects\project\Project_IoT\.agents\teamwork\teamwork_explorer_m1_1\report.md`.
3. **Kiểm tra sự vắng mặt của file log**:
   Chạy lệnh kiểm tra `Test-Path logs/attempts.csv` (phải trả về `False`).
