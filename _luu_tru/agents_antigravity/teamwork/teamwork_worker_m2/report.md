# BÁO CÁO THỰC HIỆN GIAI ĐOẠN 2 (MILESTONE 2): XÂY DỰNG BỘ SLIDE THUYẾT TRÌNH VÀ ASSET GIAO DIỆN

**Agent thực hiện**: `teamwork_worker_m2`  
**Parent Agent**: `00c906d7-900c-42be-a553-3eacb15019c9`  
**Thời gian hoàn thành**: 2026-11-03T10:55:00Z  
**Phạm vi phụ trách**: Thư mục `slides/` và `.agents/teamwork/teamwork_worker_m2/`

---

## 1. TỔNG QUAN KẾT QUẢ ĐẠT ĐƯỢC

1. **Khởi tạo và sinh Asset giao diện thật không dùng AI**:
   - Viết module `slides/generate_asset.py` sử dụng hàm `fake_assist()` từ `test_ik.py` và `build_guide_screen()` từ `guide_screen.py`.
   - Kết hợp ảnh lưới ArUco thật `aruco_A4_grid.png` có sẵn trong workspace cho góc nhìn trên và khung mô phỏng webcam nhìn ngang có vạch bàn (`SIDE_TABLE_Y_RATIO = 0.54`) và vạch nâng S1 (+20mm, `SIDE_LIFT_RATIO = 0.065`).
   - Xuất thành công tệp ảnh `slides/assets/guide_screen_sample.png` độ phân giải chuẩn $1280 \times 800$ pixel, hiển thị đầy đủ Stepper 5 bước, 4 hàng điều khiển servo có keycap, thanh trượt servo, thẻ kết quả và thông tin tọa độ.
2. **Xây dựng kịch bản tạo slide tự động `slides/build_slides.py`**:
   - Sử dụng thư viện `python-pptx`, thiết lập tỉ lệ 16:9 widescreen ($13.333 \times 7.5$ inches).
   - Áp dụng hệ màu Dark Theme chuẩn theo `guide_screen.py`:
     - Nền tối `#191B1E` (`RGB(25, 27, 30)`)
     - Thẻ khối `#272A2E` (`RGB(39, 42, 46)`)
     - Viền thẻ `#464C52` (`RGB(70, 76, 82)`)
     - Chữ chính `#F5F5F5` (`RGB(245, 245, 245)`)
     - Chữ phụ `#9BA0A5` (`RGB(155, 160, 165)`)
     - Điểm nhấn cam `#FFB928` (`RGB(255, 185, 40)`)
     - Điểm nhấn xanh lá `#5AD76E` (`RGB(90, 215, 110)`)
     - Điểm nhấn đỏ `#F55555` (`RGB(245, 85, 85)`)
   - Định dạng typography:
     - Tiêu đề slide: `Arial Bold`, kích thước 28 pt.
     - Nội dung văn bản: `Arial`, kích thước 15–18 pt.
     - Tên hàm / Code / Tham số: `Courier New`.
     - Chú thích / Footer: `Arial`, kích thước 13–14 pt.
     - Giới hạn mật độ: tối đa 6 gạch đầu dòng/slide, khoảng 12 từ/dòng.
   - Nút phím Keycap: Thiết kế ô bo tròn màu cam `#FFB928` với chữ đen in đậm `#191B1E` đồng bộ với hàm `keycap()` của `guide_screen.py`.
   - Sơ đồ khối bằng hình học nguyên bản (Native PowerPoint Shapes):
     - Slide 4 (Kiến trúc phần mềm): Luồng 2 Camera → ArucoYoloTracker → Homography → GraspAssist4DOF → ArduinoSerialLink → Firmware → Servos cùng 2 nhánh hiển thị HUD & Guide.
     - Slide 7 (Động học & Quy đổi servo): Kích thước ARM_CONFIG → Công thức IK giải tích → Quy đổi servo và khống chế giới hạn.
     - Slide 9 (Quy trình 5 bước): 5 khối Stepper ngang nối bằng mũi tên + Thẻ thứ tự chuyển động an toàn Đế → Kẹp → Vai → Khuỷu với các phím Keycap A/D, J/L, W/S, I/K và phím Auto-Step P.
     - Slide 10 (Tự động xác nhận 2 camera): Cây quyết định S1 (loại trừ ID 6), S2 (bán kính 3cm), cửa sổ 30 khung hình >= 80%, timeout 3s phân loại lỗi kẹp trượt / rơi khi nâng.
     - Slide 11 (Giao thức truyền thông): Sơ đồ Laptop ↔ Arduino USB/BT 9600 baud ↔ PCA9685 I2C 0x40 50Hz, kèm cấu trúc gói JSON 5Hz và cơ chế Watchdog/Fallback.
   - Lời thuyết trình (Speaker Notes): Toàn bộ 15 slide đều có lời thoại tiếng Việt hoàn chỉnh, phong cách thuyết trình thực tế (3–5 câu/slide).
   - Chân trang (Footer): Slide 2 đến 15 có số trang dạng `Trang X / 15` và tiêu đề ngắn `Hệ thống hỗ trợ gắp vật 4-DOF - IoT Robot Arm`.
   - Chèn ảnh giao diện: Slide 12 nhúng tệp ảnh thật `slides/assets/guide_screen_sample.png`.
   - Bảo toàn tính trung thực (Integrity Mandate): Giữ nguyên toàn bộ các placeholder `[...]` đối với các thông tin chưa có trong mã nguồn (Tên sinh viên, GVHD, lớp/môn học, model bo mạch Arduino cụ thể, và các số liệu thực nghiệm gắp vật).
3. **Kiểm tra và xác thực file xuất ra**:
   - Chạy `python slides/build_slides.py` tạo ra tệp `slides/Project_IoT_ThuyetTrinh.pptx` dung lượng `326,968 bytes` (0.31 MB).
   - Viết kịch bản kiểm thử `slides/verify_slides.py` xác minh tự động:
     - 15/15 slide đầy đủ.
     - Tỉ lệ đúng 16:9 ($13.333 \times 7.500$ in).
     - Đầy đủ footer `Trang X / 15` trên các slide 2–15.
     - Đầy đủ speaker notes độ dài > 50 ký tự trên toàn bộ 15 slide.
     - Slide 12 có nhúng ảnh giao diện thật.
     - 100% assertions passed thành công tuyệt đối.

---

## 2. DANH MỤC TỆP TIN ĐÃ TẠO

| Tệp tin | Vị trí | Mô tả chi tiết |
|---|---|---|
| `guide_screen_sample.png` | `slides/assets/` | Ảnh chụp giao diện thật $1280 \times 800$ sinh từ `fake_assist()`, `aruco_A4_grid.png` và `build_guide_screen()`. |
| `generate_asset.py` | `slides/` | Script sinh ảnh giao diện mẫu từ mã nguồn không dùng AI. |
| `build_slides.py` | `slides/` | Script chính sử dụng `python-pptx` tự động tạo toàn bộ 15 slide. |
| `Project_IoT_ThuyetTrinh.pptx` | `slides/` | Bộ slide thuyết trình kỹ thuật 15 slide tỉ lệ 16:9 widescreen, dark theme. |
| `verify_slides.py` | `slides/` | Kịch bản kiểm thử tự động cấu trúc và nội dung của tệp PPTX. |

---

## 3. CHI TIẾT 15 SLIDE THUYẾT TRÌNH

### Slide 1: Tiêu đề đề tài
- **Tiêu đề**: HỆ THỐNG HỖ TRỢ GẮP VẬT CHO CÁNH TAY ROBOT 4-DOF
- **Phụ đề**: Thị giác máy tính 2 Camera • Định vị ArUco • Nhận diện YOLO11 • Động học ngược
- **Nội dung**: Thẻ lớn trung tâm viền cam, 4 huy hiệu công nghệ (Dual Camera, ArUco Grid A4, YOLO11s Model, Analytical IK), metadata sinh viên `[...]`, GVHD `[...]`, lớp/môn `[...]`, ngày báo cáo `[...]`.
- **Speaker Notes**: Lời chào mừng, giới thiệu đề tài, mục tiêu hỗ trợ thông minh và cấu trúc bài thuyết trình.

### Slide 2: Bài toán thực tế và mục tiêu giải pháp
- **Tag**: ĐẶT VẤN ĐỀ & MỤC TIÊU
- **Bố cục**: 2 thẻ so sánh đối chiếu: Thách thức điều khiển thủ công (viền đỏ) vs Mục tiêu & Giải pháp đề xuất (viền xanh).
- **Speaker Notes**: Trình bày khó khăn khi điều khiển tay 4-DOF bằng mắt thường và giải pháp trợ lý ảo 2 camera.

### Slide 3: Kiến trúc và thiết bị phần cứng
- **Tag**: THIẾT BỊ & PHẦN CỨNG
- **Bố cục**: 3 cột: Cơ cấu chấp hành (4 servo MG996R) | Điều khiển & Kết nối (PCA9685 0x40 50Hz, Arduino `[...]`, HC-05 9600, nguồn rời 5-6V) | Thị giác & Máy trạm (Webcam laptop, Cam điện thoại, Laptop `[...]` PyTorch MPS/CUDA).
- **Speaker Notes**: Giải thích cấu trúc cơ khí, phân bố tải nguồn tránh sụt áp và cấu hình phần cứng.

### Slide 4: Kiến trúc phần mềm và luồng dữ liệu thời gian thực
- **Tag**: KIẾN TRÚC PHẦN MỀM
- **Bố cục**: Sơ đồ khối 24 hình học PowerPoint native kết nối bằng mũi tên: 2 Cam Stream (buffer=1) → ArucoYoloTracker → Homography → GraspAssist4DOF → ArduinoSerialLink / Giao diện kép (HUD & Guide) → Firmware & 4 Servo.
- **Speaker Notes**: Nhấn mạnh kiến trúc đa luồng, triệt tiêu độ trễ hình ảnh và cơ chế điều phối trung tâm.

### Slide 5: Thiết lập không gian bàn và lưới mã ArUco
- **Tag**: HỆ TỌA ĐỘ & ĐỊNH VỊ
- **Bố cục**: 3 cột: Lưới ArUco tờ A4 ($29.7 \times 21.0$ cm, DICT_4X4_50 ID 0–3, mã $2.8$ cm, lề $0.25$ cm) | Phân bổ mã toàn hệ thống (ID 4 đế robot, ID 5–6 đầu kẹp, ID 10–29 vật thể) | Homography $H_{px \to cm}$, phân đoạn màu LAB dự phòng và mã ArUco ảo.
- **Speaker Notes**: Thuyết minh cách thiết lập gốc tọa độ chuẩn tuyệt đối trên mặt bàn và cơ chế dự phòng khi bị che khuất.

### Slide 6: Nhận diện vật thể và hợp nhất dữ liệu thị giác
- **Tag**: THIẾT KẾ THỊ GIÁC & AI
- **Bố cục**: 3 cột: Mô hình YOLO11s luồng nền (crop A4, conf=0.12, imgsz=960) | Dung hợp dữ liệu (khử trùng lặp $< 2.5$ cm, ưu tiên ArUco ID 10–29, sắp xếp vật gần đế nhất) | Lọc tọa độ SMA-10 khung hình & Xử lý cam ngang (vạch bàn 0.54, lọc nhiễu bàn ghế).
- **Speaker Notes**: Trình bày giải thuật kết hợp giữa học sâu hiện đại và mã định vị chính xác cao, triệt tiêu jitter rung lắc.

### Slide 7: Động học cánh tay robot và quy đổi servo Arduino
- **Tag**: ĐỘNG HỌC ROBOT 4-DOF
- **Bố cục**: 3 cột: Thông số cơ khí ARM_CONFIG ($d_1=70, L_2=105, L_3=100, L_{4r}=65, L_{4z}=25$ mm) | Động học ngược giải tích IK (nghiệm khuỷu lên $\sin(\theta_3) \le 0$, định lý cosin) | Quy đổi servo (90° chuẩn ứng với $\theta_2=45^\circ, \theta_3=-45^\circ$, bước lượng tử hóa 5°, SERVO_LIMITS).
- **Speaker Notes**: Phân tích công thức giải tích hình học và quy tắc ánh xạ góc lệnh servo chuẩn xác.

### Slide 8: Chuyển đổi hệ tọa độ và vùng làm việc an toàn
- **Tag**: KHÔNG GIAN BÀN & AN TOÀN
- **Bố cục**: 2 cột: Chuyển đổi tọa độ A4 sang Robot ($base_x=18.0, base_y=-13.6$ cm, $robot\_faces = "down"$, công thức $x_{rob}, y_{rob}$) | Kiểm soát vùng an toàn (tầm với tối đa 205 mm, cảnh báo đỏ ngoài tầm với kèm khoảng cách dời vật $move\_closer\_mm$, cảnh báo kẹp servo).
- **Speaker Notes**: Thuyết minh cách quy đổi gốc tọa độ giữa tờ giấy và đế robot, cùng các cơ chế bảo vệ chống va chạm.

### Slide 9: Quy trình gắp 5 bước và thứ tự thao tác an toàn
- **Tag**: QUY TRÌNH GẮP VẬT
- **Bố cục**: 5 khối Stepper ngang có mũi tên (1. Điểm chờ +60mm → 2. Hạ xuống sát vật → 3. Đóng kẹp L:165° → 4. Nâng lên +80mm → 5. Kiểm tra 3s) + Thẻ thứ tự an toàn 4 khớp Đế (0) → Kẹp (3) → Vai (1) → Khuỷu (2) kèm nút phím Keycap A/D, J/L, W/S, I/K và phím Auto-Step P.
- **Speaker Notes**: Trình bày chi tiết từng giai đoạn trong máy trạng thái gắp vật và giải thích lý do cơ học của thứ tự dịch chuyển an toàn.

### Slide 10: Cơ chế tự động xác nhận gắp 2 camera độc lập
- **Tag**: TỰ ĐỘNG XÁC NHẬN GẮP
- **Bố cục**: 3 cột: Hai kênh cảm biến độc lập (S1 cam ngang nhấc $> +20$ mm loại trừ ID 6; S2 cam trên chỗ cũ sạch vật bán kính 3 cm) | Cửa sổ trượt 30 khung hình, đồng thuận cả hai kênh $\ge 80\%$ | Phân loại lỗi tự động khi hết 3s timeout (Kẹp trượt $S_2 < 40\%$, Rơi khi nâng $S_1 < 40\%$, Bị che) và ghi log CSV.
- **Speaker Notes**: Nhấn mạnh giải thuật tự động đánh giá kết quả bằng thị giác kép mà không cần cảm biến lực vật lý.

### Slide 11: Giao thức truyền thông và đồng bộ Arduino
- **Tag**: TRUYỀN THÔNG & ĐỒNG BỘ
- **Bố cục**: Sơ đồ 3 khối ngang: Máy tính Python ↔ Arduino `[...]` ↔ PCA9685 & Servo; 3 thẻ chi tiết: Gói JSON đồng bộ 5Hz (`{"t":...,"servo":[...]}`) | Watchdog 2s & Tự động Fallback từ Bluetooth về USB | Chế độ mô phỏng Simulation và phím khẩn cấp Home H.
- **Speaker Notes**: Giải thích giao thức truyền gói tin JSON hai chiều và các cơ chế dự phòng an toàn khi mất tín hiệu.

### Slide 12: Thiết kế giao diện người dùng (HUD & Cửa sổ Hướng dẫn)
- **Tag**: GIAO DIỆN NGƯỜI DÙNG
- **Bố cục**: Nhúng ảnh thật `guide_screen_sample.png` ($1280 \times 800$) ở bên trái; Cột phải phân tích 5 vùng chức năng (Khung 2 Cam, Stepper 5 bước, Hàng keycap, Thanh trượt servo, Thẻ kết quả 80%) và danh mục phím tắt hệ thống.
- **Speaker Notes**: Thuyết minh giao diện thực tế do nhóm tự động sinh từ code, nhấn mạnh trải nghiệm trực quan cho người vận hành.

### Slide 13: Kết quả kiểm thử giải thuật và thực nghiệm hệ thống
- **Tag**: KIỂM THỬ & THỰC NGHIỆM
- **Bố cục**: Cột trái: Kết quả thật 10/10 PASS từ `test_ik.py` (455 điểm 3D sai số $0.000000$ mm, phím WASD/IK/JL bước 5° chính xác, fallback Bluetooth/USB, loại trừ ID 6) | Cột phải: Thực nghiệm trên phần cứng thật (Giữ nguyên toàn bộ placeholder `[...]` cho số lượt gắp, tỉ lệ thành công, phân bố lỗi).
- **Speaker Notes**: Báo cáo kết quả kiểm thử động học đạt độ chính xác số học lý tưởng và giải thích việc hoàn thiện số liệu thực nghiệm sau chuỗi đo thực tế.

### Slide 14: Đánh giá hạn chế và hướng phát triển mở rộng
- **Tag**: ĐÁNH GIÁ & ĐỊNH HƯỚNG
- **Bố cục**: 2 cột đối chiếu: Hạn chế kỹ thuật hiện tại (vạch bàn cam ngang cố định 0.54, sai số vị trí đế $\pm 1\text{–}2$ cm, servo vòng hở bước 5°) vs Hướng phát triển nâng cấp (solvePnP tự định chuẩn 3D, vòng kín mã ID 5, tự động hóa toàn phần với hoạch định quỹ đạo mượt).
- **Speaker Notes**: Đánh giá khách quan các điểm nghẽn kỹ thuật và đề xuất lộ trình nâng cấp mang tính khả thi cao.

### Slide 15: Tổng kết dự án và phiên hỏi đáp (Q&A)
- **Tag**: TỔNG KẾT & HỎI ĐÁP
- **Bố cục**: 3 khối trụ cột thành công (Động học chính xác 100% • Thị giác kép thông minh • Trải nghiệm trực quan) + Khung biểu ngữ lớn trung tâm mời Hội đồng đặt câu hỏi Q&A.
- **Speaker Notes**: Tóm tắt 3 đóng góp cốt lõi của đề tài, gửi lời cảm ơn tới Hội đồng chấm điểm và sẵn sàng trả lời câu hỏi.

---

## 4. BẰNG CHỨNG XÁC MINH VÀ KIỂM THỬ

```text
============================================================
VERIFYING: E:\03_Development_Projects\project\Project_IoT\slides\Project_IoT_ThuyetTrinh.pptx
File size: 326,968 bytes
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
============================================================
ALL PRESENTATION VERIFICATION CHECKS PASSED SUCCESSFULLY!
============================================================
```

- **Tính toàn vẹn mã nguồn**: Không sửa đổi mã nguồn dự án, không sửa `pyproject.toml`, `uv.lock`. Không tạo commit git.
- **Tính toàn vẹn dữ liệu**: Không tạo số liệu giả, các thông tin thực nghiệm đều giữ nguyên placeholder `[...]`.
- **Không dùng ảnh AI**: 100% hình ảnh sinh trực tiếp từ pipeline code.

---
*Báo cáo hoàn thành bởi `teamwork_worker_m2`.*
