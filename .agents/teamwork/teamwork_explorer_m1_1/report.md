# Báo Cáo Kỹ Thuật Chi Tiết: Động Học, Tham Số Cấu Hình, Chuyển Đổi Tọa Độ Và Kiểm Thử Hệ Thống Robot Arm 4-DOF

- **Agent thực hiện**: `teamwork_explorer_m1_1`
- **Mã định danh Parent**: `00c906d7-900c-42be-a553-3eacb15019c9`
- **Thời gian khảo sát**: 2026-11-03T10:32:00Z
- **Phạm vi khảo sát**: `grasp_assist_4dof.py`, `test_ik.py`, `robot_arm_4dof/robot_arm_4dof.ino`, `guide_screen.py`, `main.py`, kiểm tra sự tồn tại của `logs/attempts.csv`.

---

## 1. Cấu Hình Hình Học Cánh Tay Robot 4-DOF (`ARM_CONFIG`)

### 1.1. Bảng Thông Số Hình Học Chi Tiết
*Nguồn trích dẫn: `grasp_assist_4dof.py`, dòng 32–52.*

| Tham số | Giá trị | Đơn vị | Ý nghĩa cơ khí / vật lý | Nguồn code |
|---|---|---|---|---|
| `d1_mm` | `70.0` | mm | Chiều cao từ mặt bàn làm việc đến trục xoay khớp Vai (Shoulder joint) | `grasp_assist_4dof.py:33` |
| `L2_mm` | `105.0` | mm | Chiều dài khâu Vai $\rightarrow$ Khuỷu (Upper arm: Shoulder $\rightarrow$ Elbow) | `grasp_assist_4dof.py:34` |
| `L3_mm` | `100.0` | mm | Chiều dài khâu Khuỷu $\rightarrow$ Cổ tay / Giá kẹp (Forearm: Elbow $\rightarrow$ Wrist) | `grasp_assist_4dof.py:35` |
| `L4_r_mm` | `65.0` | mm | Độ vươn ngang từ khớp giá kẹp tới tâm 2 ngón kẹp (Gripper radial offset) | `grasp_assist_4dof.py:36` |
| `L4_z_mm` | `25.0` | mm | Độ trễ dọc từ khớp giá kẹp xuống tâm 2 ngón kẹp (Gripper vertical drop offset) | `grasp_assist_4dof.py:37` |
| `base_x_cm` | `18.0` | cm | Tọa độ X của trục xoay Đế trên hệ tọa độ tờ giấy A4 (29.7 $\times$ 21.0 cm) | `grasp_assist_4dof.py:43` |
| `base_y_cm` | `-13.6` | cm | Tọa độ Y của trục xoay Đế trên hệ tờ A4 (nằm ngoài mép trên ID 0–1 khoảng 13.6 cm) | `grasp_assist_4dof.py:44` |
| `robot_faces` | `"down"` | - | Hướng vươn của cánh tay robot: `"down"` (đế ở mép trên, vươn xuống mép dưới +Y) | `grasp_assist_4dof.py:48` |
| `theta2_at_90_deg` | `45.0` | độ (deg) | Góc nghiêng hình học của khâu $L_2$ so với phương ngang khi servo Vai ở 90° | `grasp_assist_4dof.py:50` |
| `theta3_at_90_deg` | `-45.0` | độ (deg) | Góc gập hình học của khâu $L_3$ so với khâu $L_2$ khi servo Khuỷu ở 90° | `grasp_assist_4dof.py:51` |

### 1.2. Phân Tích Ghi Chú Cơ Khí và Thực Nghiệm
- **Ước lượng vị trí đế**: Code ghi nhận vị trí đế `base_x_cm = 18.0, base_y_cm = -13.6` được ước lượng từ 1 khung hình cam trên lúc tay ở tư thế 90° bằng `solvePnP` bù thị sai (với giả định tầm với FK là 239 mm). Sai số ước lượng thực tế cỡ $\pm 1 \text{--} 2\text{ cm}$. Nếu tờ A4 bị xê dịch thì cần đo lại hoặc hiệu chỉnh tự động khi nhìn thấy mã ArUco ID 4 dán trên đế robot (`grasp_assist_4dof.py:716-719`).
- **Bố cục gốc dự phòng**: Bố cục ban đầu có `base_y_cm = 22.0` (đế ở mép dưới tờ A4, gần ID 2–3) và `robot_faces = "up"`.

---

## 2. Cấu Hình Giới Hạn Khớp Và Servo (`SERVO_LIMITS`)

### 2.1. Bảng Thông Số Giới Hạn Servo
*Nguồn trích dẫn: `grasp_assist_4dof.py`, dòng 55–61; `robot_arm_4dof/robot_arm_4dof.ino`, dòng 8–20, 73–110.*

| Kênh PCA9685 | Tên khớp / Servo | Góc Min (deg) | Góc Max (deg) | Góc Mặc Định / Safe Home (deg) | Phím điều khiển (+5° / -5°) | Giới hạn xung PWM (50Hz) |
|---|---|---|---|---|---|---|
| Kênh 0 (`ch=0`) | Đế xoay (`base`) | `0` | `180` | `90` | `A` (+5° Trái) / `D` (-5° Phải) | `SERVOMIN=125`, `SERVOMAX=575` |
| Kênh 1 (`ch=1`) | Khớp Vai (`shoulder`) | `25` | `155` | `90` | `W` (+5° Lên) / `S` (-5° Xuống) | `SERVOMIN=125`, `SERVOMAX=575` |
| Kênh 2 (`ch=2`) | Khớp Khuỷu (`elbow`) | `25` | `155` | `90` | `I` (+5° Gập lên) / `K` (-5° Hạ xuống) | `SERVOMIN=125`, `SERVOMAX=575` |
| Kênh 3 (`ch=3`) | Kẹp gắp (`grip`) | `95` | `175` | `95` (mở rộng nhất) | `L` (+5° Kẹp vào) / `J` (-5° Mở ra) | `SERVOMIN=125`, `SERVOMAX=575` |

### 2.2. Lượng Tử Hóa Góc Khớp Và Khống Chế Giới Hạn Cứng
- **Bước nhảy góc rời rạc**: `SERVO_STEP_DEG = 5` (độ). Mọi góc lệnh servo đều được làm tròn (snap) về bội số của 5° (`snap_and_clamp`, `grasp_assist_4dof.py:181-186`).
- **Phần cứng điều khiển**: Module PCA9685 giao tiếp I2C địa chỉ `0x40`, tần số xung `50Hz`.
- **Ánh xạ xung**: Trong firmware Arduino:
  $$\text{pulse} = \text{map}(\text{angle}, 0, 180, 125, 575)$$
- **Phát hiện vượt giới hạn cứng (`servo_limit_overshoot`)**: `grasp_assist_4dof.py:196-214`. Nếu góc yêu cầu từ IK vượt ngưỡng $[lo - 2.5^\circ, hi + 2.5^\circ]$, hàm trả về từ điển chỉ rõ khớp và độ lệch vượt giới hạn cứng.

---

## 3. Công Thức Toán Học Động Học Thuận (FK) Và Động Học Ngược (IK)

### 3.1. Hệ Tọa Độ Chuẩn Của Robot (Robot Base Coordinate System)
*Nguồn trích dẫn: `grasp_assist_4dof.py`, dòng 88–95.*
- Gốc tọa độ $(0, 0, 0)$: Tâm đáy đế robot trên mặt bàn.
- Trục $+X_{\text{robot}}$: Hướng thẳng về phía trước mặt đế robot.
- Trục $+Y_{\text{robot}}$: Hướng sang bên trái của đế robot.
- Trục $+Z_{\text{robot}}$: Hướng thẳng đứng vuông góc lên trên từ mặt bàn.

### 3.2. Động Học Thuận (`fk_4dof_joint`)
*Nguồn trích dẫn: `grasp_assist_4dof.py`, dòng 88–109.*
- **Đầu vào**: Bộ 3 góc khớp hình học $\theta_1, \theta_2, \theta_3$ (đơn vị: độ).
- **Quy đổi radian**:
  $$t_1 = \text{radians}(\theta_1), \quad t_2 = \text{radians}(\theta_2), \quad t_{23} = \text{radians}(\theta_2 + \theta_3)$$
- **Tọa độ tâm khớp giá kẹp / cổ tay (Wrist position)**:
  $$r_w = L_2 \cos(t_2) + L_3 \cos(t_{23})$$
  $$z_w = L_2 \sin(t_2) + L_3 \sin(t_{23})$$
- **Tọa độ tâm ngón kẹp (Fingertip center)**:
  $$r = r_w + L_{4r}$$
  $$z = d_1 + z_w - L_{4z}$$
  $$x = r \cos(t_1)$$
  $$y = r \sin(t_1)$$
- **Đầu ra**: Tọa độ $(x, y, z)$ tính bằng milimét (mm).

### 3.3. Động Học Ngược Giải Tích Nghiệm Khuỷu Hướng Lên (`ik_4dof_joint`)
*Nguồn trích dẫn: `grasp_assist_4dof.py`, dòng 111–155.*
- **Đầu vào**: Tọa độ mục tiêu $(x_{\text{mm}}, y_{\text{mm}}, z_{\text{mm}})$.
- **Bước 1: Tính góc xoay đế $\theta_1$ và khoảng cách ngang $r$**:
  $$r = \sqrt{x_{\text{mm}}^2 + y_{\text{mm}}^2}$$
  $$\theta_1 = \begin{cases} \text{degrees}(\text{atan2}(y_{\text{mm}}, x_{\text{mm}})) & \text{khi } r > 10^{-6} \\ 0.0 & \text{khi } r \le 10^{-6} \end{cases}$$
- **Bước 2: Thu hồi về tọa độ cổ tay $(r_w, z_w)$**:
  $$r_w = \max(5.0, r - L_{4r})$$
  $$z_w = (z_{\text{mm}} + L_{4z}) - d_1$$
- **Bước 3: Định lý hàm số cosin cho tam giác khâu $L_2, L_3$**:
  $$\text{dist\_sq} = r_w^2 + z_w^2, \quad \text{dist} = \sqrt{\text{dist\_sq}}$$
  $$\text{max\_reach} = L_2 + L_3 = 105.0 + 100.0 = 205.0\text{ mm}$$
  $$\text{min\_reach} = |L_2 - L_3| = |105.0 - 100.0| = 5.0\text{ mm}$$
  $$D = \frac{\text{dist\_sq} - L_2^2 - L_3^2}{2 L_2 L_3}$$
  $$\text{reachable} = (|D| \le 1.0) \land \left(r \ge L_{4r} + 0.5 \times \text{min\_reach}\right) \quad (\text{với } 65.0 + 2.5 = 67.5\text{ mm})$$
  $$\text{move\_closer\_mm} = \begin{cases} \max(0.0, \text{dist} - (\text{max\_reach} - 2.0)) & \text{khi } \text{dist} > \text{max\_reach} \\ 0.0 & \text{ngược lại} \end{cases}$$
- **Bước 4: Nghiệm khuỷu hướng lên (Elbow-up analytical solution)**:
  Để tránh điểm kỳ dị khi ra ngoài biên, kẹp $D_{\text{clamped}} = \max(-1.0, \min(1.0, D))$.
  Nghiệm khuỷu hướng lên tương ứng với $\sin(\theta_3) \le 0$:
  $$\theta_{3\text{rad}} = \text{atan2}\left(-\sqrt{\max(0.0, 1.0 - D_{\text{clamped}}^2)},\; D_{\text{clamped}}\right)$$
  $$\theta_{2\text{rad}} = \text{atan2}(z_w, r_w) - \text{atan2}\left(L_3 \sin(\theta_{3\text{rad}}),\; L_2 + L_3 \cos(\theta_{3\text{rad}})\right)$$
  $$\theta_{2\text{deg}} = \text{degrees}(\theta_{2\text{rad}}), \quad \theta_{3\text{deg}} = \text{degrees}(\theta_{3\text{rad}})$$

---

## 4. Ánh Xạ Góc Khớp Sang Servo Arduino (`joint_to_arduino_servo`)

### 4.1. Công Thức Quy Đổi Tuyệt Đối
*Nguồn trích dẫn: `grasp_assist_4dof.py`, dòng 157–194.*

1. **Servo Đế (Kênh 0)**:
   $$\text{raw\_base} = 90.0 + \theta_1$$
   *Góc 90° tương ứng hướng thẳng phía trước ($\theta_1 = 0^\circ$). Phím `A` tăng góc (quay trái), phím `D` giảm góc (quay phải).*
2. **Servo Vai (Kênh 1)**:
   $$\text{raw\_shoulder} = 90.0 + (\theta_2 - 45.0^\circ)$$
   *Góc 90° ứng với vị trí chuẩn $\theta_2 = 45.0^\circ$ so với phương ngang. Phím `W` tăng góc (nâng lên), phím `S` giảm góc (hạ xuống).*
3. **Servo Khuỷu (Kênh 2)**:
   $$\text{raw\_elbow} = 90.0 + (\theta_3 - (-45.0^\circ)) = 90.0 + (\theta_3 + 45.0^\circ)$$
   *Góc 90° ứng với góc gập chuẩn $\theta_3 = -45.0^\circ$ so với khâu $L_2$. Phím `I` tăng góc (gập lên), phím `K` giảm góc (gập xuống).*
4. **Servo Kẹp (Kênh 3)**:
   - Khi đóng kẹp (`close_grip = True`): $\text{raw\_grip} = 165.0^\circ$ (kẹp chặt).
   - Khi mở kẹp (`close_grip = False`):
     $$\text{ratio} = \max\left(0.0, \min\left(1.0, \frac{60.0 - \text{grip\_open\_mm}}{40.0}\right)\right)$$
     $$\text{raw\_grip} = 95.0 + \text{ratio} \times 30.0 \quad (\in [95^\circ, 125^\circ] \subset [95^\circ, 175^\circ])$$
     *Mở tối đa 60mm ứng với 95°; mở 20mm ứng với 125°.*
5. **Làm tròn theo bước 5° và khống chế giới hạn**:
   $$\text{snapped} = \text{int}\left(\text{round}\left(\frac{\text{clamp}(\text{raw}, lo, hi)}{5}\right) \times 5\right)$$
   $$\text{servo\_angle} = \text{clamp}(\text{snapped}, lo, hi)$$

### 4.2. Chuyển Đổi Ngược Từ Servo Sang Góc Khớp (`arduino_servo_to_joint`)
*Nguồn trích dẫn: `grasp_assist_4dof.py`, dòng 217–225.*
$$\theta_1 = \text{base} - 90.0$$
$$\theta_2 = 45.0 + (\text{shoulder} - 90.0)$$
$$\theta_3 = -45.0 + (\text{elbow} - 90.0)$$

---

## 5. Chuyển Đổi Hệ Tọa Độ Giấy A4 Sang Hệ Robot (`table_cm_to_robot_mm`)

### 5.1. Mô Hình Hình Học Và Đảo Trục
*Nguồn trích dẫn: `grasp_assist_4dof.py`, dòng 227–250.*
- Kích thước tờ giấy A4 đặt ngang: Rộng $W = 29.7\text{ cm}$ (trục X giấy), Dài $H = 21.0\text{ cm}$ (trục Y giấy).
- Vị trí đế: $(\text{base\_x\_cm}, \text{base\_y\_cm}) = (18.0, -13.6)$.
- Biến hướng cánh tay `robot_faces = "down"`: Hệ số hướng $s = -1.0$.

### 5.2. Công Thức Chuyển Đổi Thuận (`table_cm_to_robot_mm`)
$$x_{\text{robot\_mm}} = s \cdot (\text{base\_y\_cm} - y_{\text{cm}}) \times 10.0$$
$$y_{\text{robot\_mm}} = s \cdot (\text{base\_x\_cm} - x_{\text{cm}}) \times 10.0$$

Khi `robot_faces = "down"` ($s = -1.0$):
$$x_{\text{robot\_mm}} = (y_{\text{cm}} - \text{base\_y\_cm}) \times 10.0 = (y_{\text{cm}} + 13.6) \times 10.0$$
$$y_{\text{robot\_mm}} = (x_{\text{cm}} - \text{base\_x\_cm}) \times 10.0 = (x_{\text{cm}} - 18.0) \times 10.0$$

*Giải thích quy ước chiều*:
- Chiều tiến $+X_{\text{robot}}$ đi từ đế vươn sâu vào tờ giấy A4 (theo chiều tăng dần của $Y_{\text{A4}}$).
- Chiều sang trái $+Y_{\text{robot}}$ tương ứng với chiều tăng dần của $X_{\text{A4}}$ (từ trái sang phải của tờ giấy).

### 5.3. Công Thức Chuyển Đổi Ngược (`robot_mm_to_table_cm`)
$$x_{\text{cm}} = \text{base\_x\_cm} - s \cdot \frac{y_{\text{robot\_mm}}}{10.0}$$
$$y_{\text{cm}} = \text{base\_y\_cm} - s \cdot \frac{x_{\text{robot\_mm}}}{10.0}$$

---

## 6. Máy Trạng Thái Quy Trình Gắp 5 Bước (`STAGE_NAMES`)

### 6.1. Chi Tiết 5 Bước Trong Quy Trình Gắp
*Nguồn trích dẫn: `grasp_assist_4dof.py`, dòng 546–552, 658–678, 1010–1044.*

| Bước (Stage) | Tên bước trong code (`STAGE_NAMES`) | Độ cao mục tiêu ($Z_{\text{target}}$) | Trạng thái kẹp | Mô tả hành động & Điều kiện chuyển bước |
|---|---|---|---|---|
| Bước 1 (`stage=0`) | `"1. DIEM CHO (Cao +60mm, Mo kep J)"` | $Z_{\text{grasp}} + 60.0\text{ mm}$ | Mở (`close_grip=False`) | Đưa đầu kẹp lơ lửng ngay phía trên vật mẫu; mở kẹp độ rộng $w_{\text{obj}} + 18\text{ mm}$. |
| Bước 2 (`stage=1`) | `"2. HA XUONG DIEM KEP (Cao +20mm)"` | $Z_{\text{grasp}} = \max(12.0, h_{\text{obj}} \times 0.5)$ | Mở (`close_grip=False`) | Hạ đầu kẹp xuống sát thân vật; căn chỉnh sai số tâm kẹp. |
| Bước 3 (`stage=2`) | `"3. DONG KEP (Bam L kep chat vat)"` | $Z_{\text{grasp}}$ | Đóng (`close_grip=True`, 165°) | **Khóa mục tiêu**: Trước khi sang bước 3, lưu `locked_grasp_cm`, `locked_obj`, `locked_align_err_mm`. Đóng kẹp chặt vật. |
| Bước 4 (`stage=3`) | `"4. NANG VAT LEN (Cao +80mm)"` | $Z_{\text{grasp}} + 80.0\text{ mm}$ | Đóng (`close_grip=True`) | Nhấc vật lên khỏi mặt bàn +80mm theo tọa độ vật đã khóa. |
| Bước 5 (`stage=4`) | `"5. XAC NHAN GAP (Cam A + Cam B)"` | $Z_{\text{grasp}} + 80.0\text{ mm}$ | Đóng (`close_grip=True`) | Kích hoạt cửa sổ đánh giá S1 & S2 (30 frames); sau khi có kết luận tự reset về Bước 1. |

*Lưu ý về độ cao*: Với vật mẫu tiêu chuẩn cao $h = 40.0\text{ mm}$, độ cao kẹp $Z_{\text{grasp}} = 20.0\text{ mm}$, điểm chờ là $+80.0\text{ mm}$ tính từ mặt bàn, điểm nâng lên là $+100.0\text{ mm}$ tính từ mặt bàn.

### 6.2. Thứ Tự Điều Khiển Khớp An Toàn
*Nguồn trích dẫn: `grasp_assist_4dof.py`, dòng 1048–1053; `guide_screen.py`, dòng 62–64.*
- **Thứ tự ưu tiên**: `Đế (0) -> Kẹp (3) -> Vai (1) -> Khuỷu (2)`.
- **Lý do cơ học**:
  1. Xoay Đế trước để định hướng phương ngang, tránh va chạm ngang vào vật cản ở các phía.
  2. Định hình độ mở ngón Kẹp để sẵn sàng đón hoặc giữ vật.
  3. Di chuyển liên kết Vai và Khuỷu để đưa đầu kẹp lên/xuống theo trục thẳng đứng một cách ổn định nhất.

### 6.3. Chế Độ Tự Động Bước (Auto-Step, Phím `P`)
*Nguồn trích dẫn: `grasp_assist_4dof.py`, dòng 1045–1054, 1213–1216.*
- Khi bật chế độ `auto_step_enabled` (phím `P` trên bàn phím), bộ điều khiển tự động duyệt qua các gợi ý theo thứ tự `(0, 3, 1, 2)`.
- Cứ mỗi chu kỳ $\ge 0.28\text{ s}$ (`last_auto_step_ts`), nếu phát hiện khớp chưa đạt (`not ok and steps > 0`), nó tự động gửi 1 xung ký tự lệnh tương ứng qua `serial_link.send_key(cmd_key)`.

---

## 7. Giải Thuật Tự Động Xác Nhận Gắp Hai Camera (S1 + S2)

### 7.1. Kênh Cảm Biến S1 (Cam B - Nhìn Ngang Webcam Laptop)
*Nguồn trích dẫn: `grasp_assist_4dof.py`, dòng 78–82, 852–898.*
- **Vạch tham chiếu mặt bàn**: $y_{\text{table\_px}} = \text{round}(h \times \text{SIDE\_TABLE\_Y\_RATIO}) = \text{round}(h \times 0.54)$.
- **Ngưỡng nhấc vật (+20mm)**: $y_{\text{lift\_thresh\_px}} = \text{round}(y_{\text{table\_px}} - h \times \text{SIDE\_LIFT\_RATIO}) = \text{round}(y_{\text{table\_px}} - h \times 0.065)$.
- **Điều kiện phát hiện**:
  - Mã ArUco dán cạnh hông vật thể (ID 10–29) có tọa độ tâm $c_y < y_{\text{lift\_thresh\_px}}$.
  - Hoặc đáy hộp bao YOLO (`dets_side`, `bottom_y = fy2 < y_lift_thresh_px`).
- **ĐẶC BIỆT LOẠI TRỪ MÃ ID 6**: Mã ArUco ID 6 được dán trên đầu kẹp robot. Khi kẹp rỗng không gắp được vật nâng lên, ID 6 cũng vượt qua ngưỡng độ cao. Do đó thuật toán **tuyệt đối không tính ID 6** vào tín hiệu S1 để tránh báo nhầm "GẮP THÀNH CÔNG" khi vật rơi hoặc kẹp trượt (`grasp_assist_4dof.py:879-886`).

### 7.2. Kênh Cảm Biến S2 (Cam A - Nhìn Trên Xuống Điện Thoại)
*Nguồn trích dẫn: `grasp_assist_4dof.py`, dòng 772–797.*
- **Vị trí gốc được khóa**: $(lx_{\text{cm}}, ly_{\text{cm}}) = \text{locked\_grasp\_cm}$.
- **Bán kính quét dọn sạch (Clearing radius)**: $r_{\text{clear}} = 3.0\text{ cm}$ (30 mm).
- **Điều kiện xác nhận chỗ cũ trống**: Không còn bất kỳ vật thể nào (ArUco ID 10–29 hoặc YOLO) có khoảng cách $\le 3.0\text{ cm}$ tính từ tâm vị trí gắp cũ.

### 7.3. Cửa Sổ Trượt Và Phân Loại Lỗi Thực Nghiệm
*Nguồn trích dẫn: `grasp_assist_4dof.py`, dòng 900–952.*
- **Cửa sổ đánh giá**: `deque(maxlen=30)` khung hình cho cả $S_1$ và $S_2$.
- **Tỉ lệ khung hình thỏa mãn**:
  $$s1\_ratio = \frac{\sum s1\_window}{\text{len}(s1\_window)}, \quad s2\_ratio = \frac{\sum s2\_window}{\text{len}(s2\_window)}$$
- **Điều kiện THÀNH CÔNG (SUCCESS)**:
  Khi số khung hình $\ge 15$ và đồng thời:
  $$s1\_ratio \ge 0.80 \quad \text{VÀ} \quad s2\_ratio \ge 0.80$$
  *(Cả hai camera đồng thuận $\ge 80\%$ cửa sổ, tức khoảng 24–25/30 khung hình).*
- **Điều kiện THẤT BẠI (FAIL) Và Phân Loại**:
  Khi thời gian kiểm tra vượt quá Timeout 3.0 giây (`time.time() - verify_start_ts >= 3.0`), hệ thống phân loại theo cây quyết định:
  1. **Nếu $s2\_ratio < 0.40$**: `reason = "kep_truot_vat_van_o_cho_cu"`
     Biểu ngữ: `"THAT BAI: KEP TRUOT (Vat van nam o cho cu tren Cam A)"` (vật vẫn nằm nguyên tại chỗ cũ).
  2. **Nếu $s1\_ratio < 0.40$**: `reason = "roi_khi_nang_hoac_chua_nhac_len"`
     Biểu ngữ: `"THAT BAI: ROI KHI NANG (Cam B khong thay vat o tren cao)"` (vật bị rơi hoặc chưa nhấc lên được).
  3. **Ngược lại**: `reason = "khong_xac_dinh_bi_che"`
     Biểu ngữ: `"KHONG XAC DINH -> Thu lai voi tu the vat moi"`.

### 7.4. Định Dạng Ghi Nhật Ký (`logs/attempts.csv`)
*Nguồn trích dẫn: `grasp_assist_4dof.py`, dòng 606–634.*
- Đường dẫn file log: `os.path.join(os.path.dirname(__file__), "logs", "attempts.csv")`.
- Cấu trúc tiêu đề 9 cột:
  `timestamp, object_name, target_x_mm, target_y_mm, align_error_mm, s1_ratio, s2_ratio, result, reason`
- Định dạng giá trị:
  - `timestamp`: `%Y-%m-%d %H:%M:%S`
  - `target_x_mm`, `target_y_mm`: số thực 1 chữ số thập phân (`.1f`)
  - `align_error_mm`: sai số căn chỉnh tâm kẹp lúc đóng kẹp tính bằng mm (`.1f`)
  - `s1_ratio`, `s2_ratio`: tỉ lệ 2 chữ số thập phân (`.2f`)
  - `result`: `"SUCCESS"` hoặc `"FAIL"`
  - `reason`: `"ok"`, `"kep_truot_vat_van_o_cho_cu"`, `"roi_khi_nang_hoac_chua_nhac_len"`, `"khong_xac_dinh_bi_che"`

---

## 8. Kết Quả Chạy Kiểm Thử Thực Tế (`test_ik.py`)

### 8.1. Lệnh Thực Thi
- **Môi trường**: Windows PowerShell, Python 3.13.
- **Lệnh thực thi**: `python -X utf8 test_ik.py` *(sử dụng cờ `-X utf8` để xử lý chuẩn mã hóa UTF-8 cho các ký tự emoji tiếng Việt trên terminal Windows cp1252)*.
- **Exit Code**: `0` (Toàn bộ 10 bài test đều vượt qua 100%).

### 8.2. Toàn Văn Console Output Ghi Nhận Được
```text
✅ [PASS] Đã kiểm thử 455 điểm 3D trong tầm với: sai số FK(IK(p)) tối đa = 0.000000 mm (< 0.1 mm)
✅ [PASS] Kiểm thử gợi ý bấm phím (WASD + IK + JL) với STEP = 5° chính xác tuyệt đối!
✅ [PASS] Ánh xạ tờ A4 <-> hệ robot đúng cho cả hai hướng đặt robot (up / down)
✅ [PASS] Phát hiện board không nhận lệnh USB (firmware cũ)
✅ [PASS] Tìm cổng Bluetooth của HC-05 (Windows theo địa chỉ MAC, macOS theo tên cổng)
✅ [PASS] Gửi lệnh qua Bluetooth HC-05, tự quay về USB khi BT đứt
✅ [PASS] S1 chỉ tính mã của vật (ID 10-29), kẹp rỗng nâng lên không bị báo là đã gắp
📝 Đã ghi kết quả gắp vào C:\Users\DELL\AppData\Local\Temp\tmppc2y11q4\logs\attempts.csv: SUCCESS (ok)
✅ [PASS] Khóa vật lúc đóng kẹp cho bước nâng + kiểm tra, log CSV ghi đúng sai số căn đầu kẹp
✅ [PASS] Chuẩn hóa địa chỉ IP Webcam của điện thoại
📷 Camera: 0=Duong's iPhone Desk View Camera, 1=Duong's iPhone Camera, 2=MacBook Air Camera
📷 Camera: 0=OBS Virtual Camera, 1=MacBook Air Camera
✅ [PASS] Nhận camera MacBook và iPhone (Continuity Camera) theo tên trên macOS
```

### 8.3. Phân Tích Kết Quả Kiểm Thử
1. **Kiểm thử lưới 3D (`test_fk_ik_grid`)**:
   - Duyệt qua dải tọa độ: $X \in [110, 215)$ bước 15, $Y \in [-90, 95)$ bước 15, $Z \in \{15, 30, 50, 80, 100\}$.
   - Tổng cộng **455 điểm 3D** nằm trong tầm với hình học đã được kiểm tra.
   - Sai số cực đại giữa tọa độ gốc và tọa độ phục hồi qua $FK(IK(p))$:
     $$\max \|FK(IK(p)) - p\| = 0.000000\text{ mm} \ll 0.1\text{ mm}$$
   - Mọi góc servo sinh ra đều nằm chính xác trong `SERVO_LIMITS` và chia hết cho `SERVO_STEP_DEG = 5°`.
2. **Kiểm thử phím bấm gợi ý (`test_key_hints`)**:
   - Đế: 90° $\rightarrow$ 115°: $\Delta = +25^\circ \rightarrow$ Bấm `A` $\times 5$ (Trái).
   - Vai: 90° $\rightarrow$ 70°: $\Delta = -20^\circ \rightarrow$ Bấm `S` $\times 4$ (Xuống).
   - Khuỷu: 90° $\rightarrow$ 105°: $\Delta = +15^\circ \rightarrow$ Bấm `I` $\times 3$ (Gập lên).
   - Kẹp: 95° $\rightarrow$ 165°: $\Delta = +70^\circ \rightarrow$ Bấm `L` $\times 14$ (Kẹp vào).
3. **Kiểm thử chuyển đổi tờ A4 <-> Robot (`test_table_robot_mapping`)**:
   - Khớp 100% tọa độ cho cả hai hướng `robot_faces = "up"` và `robot_faces = "down"`.
4. **Kiểm thử xử lý giao tiếp phần cứng và ngoại vi**:
   - Tự động nhận diện firmware cũ không phản hồi lệnh USB sau 2 giây.
   - Tìm kiếm cổng Bluetooth HC-05 (Windows theo MAC ID `98D351F6AF14`, macOS theo tên thiết bị).
   - Cơ chế tự fallback về cáp USB khi đường truyền Bluetooth bị ngắt.
5. **Kiểm thử logic xác nhận hai camera và ghi log**:
   - Kiểm tra loại trừ mã ID 6 của đầu kẹp trong $S_1$.
   - Kiểm tra cơ chế khóa thông số vật mục tiêu khi chuyển sang Bước 3 (Đóng kẹp).
   - Ghi nhận chính xác sai số căn chỉnh đầu kẹp `align_error_mm` vào file CSV.

---

## 9. Kiểm Tra Tình Trạng Tệp Dữ Liệu Thực Nghiệm `logs/attempts.csv`

### 9.1. Kết Quả Kiểm Tra Hệ Thống Tập Tin
- Đã thực hiện tìm kiếm toàn diện tệp `logs/attempts.csv` và thư mục `logs/` trong toàn bộ workspace `e:\03_Development_Projects\project\Project_IoT`.
- **Kết quả xác minh**: Tệp `logs/attempts.csv` và thư mục `logs/` **CHƯA TỒN TẠI** trong không gian làm việc.

### 9.2. Kết Luận Và Ràng Buộc Triển Khai
- Theo đúng quy tắc ràng buộc Integrity Mode và yêu cầu R1.13 của `ORIGINAL_REQUEST.md`:
  > *"Nếu có file `logs/attempts.csv`, tính toán số lần gắp, tỉ lệ thành công và lý do thất bại thực tế; nếu không có, giữ nguyên dạng placeholder `[...]`."*
  > *"Tuyệt đối không tự bịa đặt bất kỳ thông số, số liệu thực nghiệm hay tỉ lệ thành công nào."*
- **Quy tắc bắt buộc cho các slide thuyết trình**:
  - Không tự ý bịa đặt số lần thử nghiệm, tỉ lệ thành công hay thống kê phân loại lỗi.
  - Toàn bộ các mục kết quả thực nghiệm gắp vật trên phần cứng thật phải được trình bày dưới dạng placeholder rõ ràng: `[...]` (Ví dụ: `Tổng số lần gắp: [...]`, `Tỉ lệ thành công: [...]%`, `Số lần kẹp trượt: [...]`, `Số lần rơi khi nâng: [...]`).

---

## 10. Bảng Tổng Hợp Dẫn Chứng Mã Nguồn Phục Vụ Dựng Slide (Evidence Summary Table)

| Hạng mục / Thông số kỹ thuật | Giá trị thực tế trích xuất từ code | File nguồn | Dòng code |
|---|---|---|---|
| Chiều cao vai `d1_mm` | `70.0 mm` | `grasp_assist_4dof.py` | Line 33 |
| Chiều dài khâu `L2_mm` | `105.0 mm` | `grasp_assist_4dof.py` | Line 34 |
| Chiều dài khâu `L3_mm` | `100.0 mm` | `grasp_assist_4dof.py` | Line 35 |
| Độ vươn kẹp `L4_r_mm` | `65.0 mm` | `grasp_assist_4dof.py` | Line 36 |
| Độ trễ kẹp `L4_z_mm` | `25.0 mm` | `grasp_assist_4dof.py` | Line 37 |
| Tọa độ trục đế `base_x_cm`, `base_y_cm` | `18.0 cm`, `-13.6 cm` | `grasp_assist_4dof.py` | Line 43–44 |
| Hướng robot `robot_faces` | `"down"` | `grasp_assist_4dof.py` | Line 48 |
| Góc chuẩn servo 90° | $\theta_2 = 45^\circ$, $\theta_3 = -45^\circ$ | `grasp_assist_4dof.py` | Line 50–51 |
| Bước góc `SERVO_STEP_DEG` | `5°` | `grasp_assist_4dof.py` | Line 55 |
| Giới hạn góc servo | Base `[0, 180]`, Shoulder `[25, 155]`, Elbow `[25, 155]`, Grip `[95, 175]` | `grasp_assist_4dof.py` | Line 56–61 |
| Địa chỉ & Tần số PCA9685 | I2C `0x40`, `50 Hz` | `robot_arm_4dof.ino` | Line 8, 47 |
| Dải xung PWM servo | `125` (~0°) $\rightarrow$ `575` (~180°) | `robot_arm_4dof.ino` | Line 11–12 |
| Chân kết nối Bluetooth HC-05 | `RX = D2, TX = D3`, Baud `9600` | `robot_arm_4dof.ino` | Line 6, 44 |
| MAC mặc định HC-05 | `"98D351F6AF14"` | `grasp_assist_4dof.py` | Line 313 |
| Chu kỳ báo trạng thái servo | `200 ms` (5 Hz) qua JSON `{"servo":[...]}` | `robot_arm_4dof.ino` | Line 30–40, 123–127 |
| Tỉ lệ vạch bàn cam ngang | `SIDE_TABLE_Y_RATIO = 0.54` | `grasp_assist_4dof.py` | Line 81 |
| Tỉ lệ nâng +20mm cam ngang | `SIDE_LIFT_RATIO = 0.065` | `grasp_assist_4dof.py` | Line 82 |
| Bán kính trống chỗ cũ Cam A (S2) | `3.0 cm` (30 mm) | `grasp_assist_4dof.py` | Line 776–779 |
| Ngưỡng cửa sổ xác nhận gắp | `30 frames`, tỉ lệ đồng thuận $\ge 80\%$ | `grasp_assist_4dof.py` | Line 587–588, 928 |
| Thời gian Timeout xác nhận | `3.0 giây` | `grasp_assist_4dof.py` | Line 935 |
| Thứ tự an toàn khi dịch chuyển | Đế (0) $\rightarrow$ Kẹp (3) $\rightarrow$ Vai (1) $\rightarrow$ Khuỷu (2) | `grasp_assist_4dof.py` / `guide_screen.py` | Line 1048–1053 / Line 63 |
| Tốc độ tự động bước Auto-Step | `0.28 giây` / 1 bước 5° (phím `P`) | `grasp_assist_4dof.py` | Line 1046 |
| Kết quả chạy `test_ik.py` | `455 điểm 3D`, sai số cực đại `0.000000 mm`, 10/10 PASS | `test_ik.py` console output | Test run 2026-11-03 |
| Tình trạng `logs/attempts.csv` | Chưa có trong workspace (giữ `[...]`) | Filesystem check | Test run 2026-11-03 |
