# Extracted Slides Content

## Slide 1

### Text Elements:
- ĐỒ ÁN TỐT NGHIỆP / BÁO CÁO KỸ THUẬT IoT & ROBOTICS
- HỆ THỐNG HỖ TRỢ GẮP VẬT CHO CÁNH TAY ROBOT 4-DOF
- Thị giác máy tính 2 Camera • Định vị ArUco • Nhận diện YOLO11 • Động học ngược
- DUAL CAMERA
- ARUCO GRID A4
- YOLO11s MODEL
- ANALYTICAL IK
- Sinh viên thực hiện: [...]                      Giảng viên hướng dẫn: [...]
- Lớp / Môn học: [...]                           Thời gian báo cáo: [...]
- Mã nguồn đồ án: GraspAssist4DOF + OpenCV + PyTorch + PCA9685 Firmware

### Speaker Notes:
Kính thưa quý thầy cô và các bạn, hôm nay nhóm chúng em xin được trình bày đề tài: Hệ thống hỗ trợ gắp vật cho cánh tay robot 4 bậc tự do sử dụng 2 camera, ArUco, YOLO11 và động học ngược. Mục tiêu của dự án là xây dựng một hệ thống thị giác thông minh có khả năng quan sát không gian làm việc, tự động tính toán góc quay của từng khớp và hướng dẫn người điều khiển thao tác gắp vật một cách trực quan, chính xác. Sau đây, em xin phép đại diện nhóm đi vào chi tiết cấu trúc phần cứng và giải thuật phần mềm của hệ thống.

## Slide 2

### Text Elements:
- ĐẶT VẤN ĐỀ & MỤC TIÊU
- BÀI TOÁN THỰC TẾ VÀ MỤC TIÊU GIẢI PHÁP
- Hệ thống hỗ trợ gắp vật 4-DOF - IoT Robot Arm
- Trang 2 / 15
- THÁCH THỨC ĐIỀU KHIỂN THỦ CÔNG
- • Khó ước lượng không gian 3D: Người điều khiển khó phán đoán khoảng cách sâu và độ cao chỉ qua một góc nhìn duy nhất.
- • Dò phím mò mẫm: Cánh tay 4 khớp tự do dễ bị va đập mặt bàn hoặc gạt đổ vật khi dịch chuyển các góc không đồng bộ.
- • Thiếu phản hồi vị trí: Servo RC thông thường không có encoder phản hồi, dễ lệch góc khi chịu tải trọng vật nặng.
- • Đánh giá chủ quan: Khó xác định vật đã kẹp chắc chắn hay chưa khi chưa nhấc hẳn lên khỏi vùng làm việc.
- MỤC TIÊU & GIẢI PHÁP ĐỀ XUẤT
- • Thị giác máy tính 2 Camera: Cam trên định vị phẳng (X, Y); Cam ngang kiểm tra cao độ (Z) và vạch nâng.
- • Động học ngược giải tích (IK): Tự động tính toán góc 4 khớp chuẩn xác từng bước 5° và cảnh báo tầm với.
- • Giao diện HUD hướng dẫn trực quan: Chỉ rõ từng phím bấm cần thao tác, số lần bấm và thứ tự di chuyển an toàn.
- • Tự động thẩm định kết quả gắp: Hai camera độc lập tự động đối soát, phân loại lỗi trượt kẹp hoặc rơi vật.

### Speaker Notes:
Trong thực tế, việc điều khiển một cánh tay robot mini 4 bậc tự do gắp vật bằng tay cầm hoặc bàn phím thường gặp rất nhiều khó khăn do người vận hành không thể ước lượng chính xác khoảng cách 3 chiều và góc khớp. Để giải quyết bài toán này, nhóm đã xây dựng giải pháp hỗ trợ thông minh: sử dụng camera góc trên để định vị vật thể và giải động học ngược, kết hợp camera góc ngang để kiểm tra độ cao. Hệ thống đóng vai trò như một người trợ lý ảo, đưa ra hướng dẫn từng bước phím bấm và tự động đánh giá xem vật đã được gắp thành công hay chưa.

## Slide 3

### Text Elements:
- THIẾT BỊ & PHẦN CỨNG
- KIẾN TRÚC VÀ THIẾT BỊ PHẦN CỨNG HỆ THỐNG
- Hệ thống hỗ trợ gắp vật 4-DOF - IoT Robot Arm
- Trang 3 / 15
- CƠ CẤU CHẤP HÀNH
- • 4x Động cơ RC Servo MG996R: Bánh răng kim loại, lực kéo cao.
- • Kênh 0 (Đế): Quay 0° – 180° (Mặc định 90° hướng thẳng).
- • Kênh 1 (Vai): Nâng hạ 25° – 155° (Mặc định 90°).
- • Kênh 2 (Khuỷu): Gập duỗi 25° – 155° (Mặc định 90°).
- • Kênh 3 (Kẹp): Đóng mở 95° – 175° (95° mở rộng, 165° kẹp chặt).
- ĐIỀU KHIỂN & KẾT NỐI
- • Mạch xung PCA9685: Chuẩn I2C địa chỉ 0x40, tần số 50Hz cấp xung servo.
- • Độ rộng xung PWM: 125 (~0°) đến 575 (~180°) xung 12-bit.
- • Vi điều khiển trung tâm: Bo mạch Arduino [...] cấp xung và đọc lệnh 9600 baud.
- • Module Bluetooth HC-05: Chân RX=D2, TX=D3, baud 9600, MAC 98D351F6AF14.
- • Nguồn rời 5V–6V dòng cao: Nuôi riêng 4 servo, chống sụt áp reset Arduino.
- THỊ GIÁC & MÁY TRẠM
- • Cam 1 (Nhìn ngang): Webcam laptop đặt thấp quan sát cao độ gắp.
- • Cam 2 (Nhìn trên xuống): Camera điện thoại gắn giá cao vuông góc mặt bàn.
- • Hỗ trợ kết nối Cam 2: iPhone Continuity, Iriun, DroidCam, Wi-Fi IP Webcam.
- • Máy tính xử lý trung tâm: Laptop [...] chạy mô hình YOLO11s và giải IK.
- • Tăng tốc phần cứng: Tự động nhận diện PyTorch MPS (Apple Silicon), CUDA hoặc CPU.

### Speaker Notes:
Về mặt phần cứng, cánh tay robot sử dụng 4 servo MG996R bánh răng kim loại, mang lại lực kẹp và độ ổn định cao. Do dòng khởi động của 4 servo khá lớn, nhóm sử dụng module mở rộng PCA9685 giao tiếp qua chuẩn I2C địa chỉ 0x40 ở tần số 50Hz, được cấp nguồn rời từ 5 đến 6V độc lập với Arduino. Dữ liệu điều khiển được truyền từ máy tính xử lý trung tâm xuống Arduino thông qua cáp USB hoặc module Bluetooth HC-05 gắn ở chân D2 và D3 với tốc độ 9600 baud.

## Slide 4

### Text Elements:
- KIẾN TRÚC PHẦN MỀM
- KIẾN TRÚC PHẦN MỀM VÀ LUỒNG DỮ LIỆU THỜI GIAN THỰC
- Hệ thống hỗ trợ gắp vật 4-DOF - IoT Robot Arm
- Trang 4 / 15
- Cam 1: Ngang (Webcam)CameraStream (Buffer=1)
- Cam 2: Trên (Điện thoại)CameraStream (Buffer=1)
- ArucoYoloTracker• YOLO11s (Luồng nền)• ArUco ID 0-3 góc A4• Homography (px → cm)• Lọc SMA-10 khung hình
- GraspAssist4DOF (Bộ điều phối trung tâm)• Động học ngược giải tích IK (Nghiệm khuỷu lên)• Máy trạng thái 5 bước gắp (Điểm chờ → Kiểm tra)• Phím bấm WASD/IK/JL bước 5° & Auto-Step (P)• Xác nhận 2 camera S1 + S2 (80%, Timeout 3s)
- ArduinoSerialLink & Phần cứng• USB Serial / Bluetooth HC-05 (9600)• Gói tin JSON trạng thái góc 5Hz• PCA9685 I2C 0x40 50Hz• 4x Servo MG996R
- Giao diện kép• Thanh HUD  (1280 × 175)• Cửa sổ Hướng dẫn  (1280 × 800)
- ĐẶC ĐIỂM THIẾT KẾ ĐA LUỒNG & CHỐNG TRỄ
- • Zero-latency buffer: CameraStream duy trì buffersize=1, chống tích tụ trễ khung hình.
- • YOLO Worker nền: Tách biệt luồng nhận diện AI giúp giao diện luôn giữ mượt mà 30+ FPS.
- • Watchdog 4s: Tự động khởi động lại camera nếu mất tín hiệu video.

### Speaker Notes:
Kiến trúc phần mềm của hệ thống được tổ chức hoàn toàn theo hướng đa luồng để triệt tiêu độ trễ hình ảnh. Luồng CameraStream liên tục bắt khung hình mới nhất từ 2 camera, trong khi mô hình YOLO11 chạy trên một worker riêng để không gây sụt giảm FPS hiển thị. Tọa độ vật thể được ánh xạ từ pixel sang centimet thông qua ma trận Homography, sau đó đưa vào module GraspAssist4DOF để tính toán động học ngược. Kết quả góc quay được đồng bộ hai chiều với Arduino qua giao thức JSON ở tần số 5Hz và hiển thị trực quan lên cửa sổ hướng dẫn.

## Slide 5

### Text Elements:
- HỆ TỌA ĐỘ & ĐỊNH VỊ
- THIẾT LẬP KHÔNG GIAN BÀN VÀ LƯỚI MÃ ARUCO
- Hệ thống hỗ trợ gắp vật 4-DOF - IoT Robot Arm
- Trang 5 / 15
- LƯỚI ARUCO TỜ A4
- • Khổ giấy A4 đặt ngang: Rộng W = 29.7 cm, Dài H = 21.0 cm.
- • Bộ từ điển ArUco: DICT_4X4_50 (50 mã 4x4 bit, nhận diện nhanh).
- • Kích thước mã in: 2.8 x 2.8 cm, đặt cách mép giấy 0.25 cm.
- • ID 0 (Góc Trên-Trái): Gốc O (0.0, 0.0 cm).
- • ID 1 (Góc Trên-Phải): Trục X (29.7, 0.0 cm).
- • ID 2 (Góc Dưới-Phải): Điểm cực (29.7, 21.0 cm).
- • ID 3 (Góc Dưới-Trái): Trục Y (0.0, 21.0 cm).
- PHÂN BỔ MÃ TOÀN HỆ THỐNG
- • ID 4 (Đế Robot): Tự động hiệu chỉnh tọa độ base_x_cm, base_y_cm.
- • ID 5 (Đầu kẹp - Cam trên): Phản hồi vị trí kẹp thực tế (Closed-loop).
- • ID 6 (Đầu kẹp - Cam ngang): Loại trừ khỏi S1 để chống báo gắp giả.
- • ID 10–13: Vật mẫu (Hộp vuông 40mm, Hộp xanh 35x50mm, Hộp đỏ 30x60mm, Trụ 35x50mm).
- • ID 14–29: Dải mã dự phòng cho các vật thể kiểm thử khác (35x35x40 mm).
- HOMOGRAPHY & DỰ PHÒNG
- • Ma trận Homography H: Chuyển đổi chính xác tọa độ pixel sang cm mặt bàn.
- • Ánh xạ 8–16 điểm góc: Khớp 4 điểm góc của các mã ArUco thật với tọa độ cm.
- • Ma trận nghịch đảo H_inv: Chiếu ngược tọa độ centimet lên pixel để vẽ thước đo.
- • Dự phòng phân đoạn màu LAB: Tách nền giấy trắng (L:130-255, A:0-134, B:125-255) khi che mã.
- • Gán ArUco ảo: Dán mã ảo bù trừ viền Quiet Zone nếu chưa in mã thật.

### Speaker Notes:
Để xác định không gian làm việc một cách tuyệt đối, nhóm sử dụng một tờ giấy A4 đặt ngang kích thước 29.7 nhân 21 centimet làm mặt bàn chuẩn. Bốn góc tờ giấy được in 4 mã ArUco thuộc bộ từ điển DICT_4X4_50 từ ID 0 đến ID 3, mỗi mã có kích thước 2.8 centimet và đặt cách mép 2.5 milimet để OpenCV dễ dàng bắt góc. Hệ thống còn quy ước mã ID 4 gắn trên đế robot, mã ID 5 và 6 gắn trên đầu kẹp, cùng dải mã từ 10 đến 29 dành cho các vật thể. Nếu có góc bị che khuất, thuật toán phân đoạn màu LAB sẽ tự động kích hoạt để tìm biên giấy dự phòng.

## Slide 6

### Text Elements:
- THỊ GIÁC MÁY TÍNH & AI
- NHẬN DIỆN VẬT THỂ VÀ HỢP NHẤT DỮ LIỆU THỊ GIÁC
- Hệ thống hỗ trợ gắp vật 4-DOF - IoT Robot Arm
- Trang 6 / 15
- MÔ HÌNH YOLO11s
- • Mô hình học sâu: YOLO11s chạy suy luận trên luồng nền độc lập.
- • Vùng cắt A4: Cắt bao quanh tứ giác A4 (lề an toàn 10px), triệt nhiễu.
- • Tham số Cam trên: conf = 0.12, imgsz = 960 phát hiện vật nhỏ.
- • Lọc diện tích: Bỏ hộp quá lớn (> 40% A4) hoặc quá nhỏ (< 400 px²).
- • Kiểm tra mép: Tâm vật cách mép tờ A4 tối thiểu 15 px.
- DUNG HỢP DỮ LIỆU
- • Ưu tiên ArUco ID 10–29: Cung cấp chính xác kích thước 3 chiều (w, l, h).
- • Khử trùng lặp (Threshold < 2.5 cm): Nếu YOLO cách ArUco < 2.5 cm thì bỏ YOLO.
- • Bổ sung vật YOLO: Nếu cách xa >= 2.5 cm, gán nhãn YOLO:<cls> (35x40 mm).
- • Sắp xếp theo độ gần: Ưu tiên gắp vật thể có khoảng cách gần đế robot nhất.
- • Phím TAB / V: Chuyển đổi mục tiêu gắp cho người vận hành.
- LỌC TỌA ĐỘ & CAM NGANG
- • Lọc trung bình trượt 10 khung hình: deque(maxlen=10) khử rung lắc.
- • Tọa độ cấp cho IK: Tính trung bình cộng của 10 vị trí gần nhất.
- • Nhận diện Cam ngang: conf = 0.20, imgsz = 640 lọc nhiễu bàn ghế, laptop.
- • Điểm chân đế vật: cy_base = y2 - 0.30*(y2 - y1) kiểm tra nằm vùng bàn.
- • Vạch tham chiếu mặt bàn: Tỉ lệ SIDE_TABLE_Y_RATIO = 0.54 xác định cao độ.

### Speaker Notes:
Nhằm tối ưu độ chính xác và khả năng thích ứng linh hoạt, hệ thống kết hợp song song cả mô hình học sâu YOLO11s và mã ArUco. Mô hình YOLO11s được cắt vùng xử lý sát bề mặt tờ A4 để loại bỏ nhiễu từ tay người hay bàn ghế xung quanh, trong khi các vật mẫu dán mã ArUco ID 10 đến 29 sẽ cung cấp ngay kích thước ba chiều thật từ bảng cấu hình. Hai nguồn dữ liệu này được khử trùng lặp với ngưỡng khoảng cách 2.5 centimet, sau đó làm mịn qua bộ lọc trung bình trượt 10 khung hình và ưu tiên gắp vật thể nằm gần đế robot nhất.

## Slide 7

### Text Elements:
- ĐỘNG HỌC ROBOT 4-DOF
- ĐỘNG HỌC CÁNH TAY ROBOT VÀ QUY ĐỔI SERVO ARDUINO
- Hệ thống hỗ trợ gắp vật 4-DOF - IoT Robot Arm
- Trang 7 / 15
- THÔNG SỐ CƠ KHÍ
- • Chiều cao trục vai d1: 70.0 mm (mặt bàn tới trục servo Vai).
- • Khâu vai L2: 105.0 mm (Upper arm: Trục Vai → Trục Khuỷu).
- • Khâu khuỷu L3: 100.0 mm (Forearm: Trục Khuỷu → Khớp kẹp).
- • Độ vươn kẹp L4_r: 65.0 mm (khoảng cách ngang tới tâm ngón).
- • Độ trễ kẹp L4_z: 25.0 mm (khoảng cách dọc hạ thấp đầu kẹp).
- • Tầm với: Tối đa L2 + L3 = 205.0 mm, tối thiểu |L2 - L3| = 5.0 mm.
- ĐỘNG HỌC NGƯỢC (IK)
- • Tâm cổ tay rw, zw: rw = max(5, r - L4_r), zw = (z + L4_z) - d1.
- • Định lý cosin: D = (rw² + zw² - L2² - L3²) / (2*L2*L3).
- • Điều kiện với tới: |D| <= 1.0 và r >= L4_r + 2.5 mm.
- • Nghiệm khuỷu lên (Elbow-up): sin(θ3) <= 0 tránh chạm bàn:
- θ3 = atan2(-sqrt(1 - D²), D)
- θ2 = atan2(zw, rw) - atan2(L3*sin(θ3), L2 + L3*cos(θ3))
- • Góc xoay đế: θ1 = atan2(y, x) tính theo tọa độ robot.
- QUY ĐỔI SERVO ARDUINO
- • Quy ước chuẩn 90°: θ2 = 45.0°, θ3 = -45.0° (vị trí cân bằng).
- • Servo Đế: raw_base = 90.0 + θ1 (Dải [0°, 180°]).
- • Servo Vai: raw_shoulder = 90.0 + (θ2 - 45.0°) (Dải [25°, 155°]).
- • Servo Khuỷu: raw_elbow = 90.0 + (θ3 + 45.0°) (Dải [25°, 155°]).
- • Servo Kẹp: Mở 95° – 125°, Kẹp chặt 165° (Dải [95°, 175°]).
- • Lượng tử hóa: SERVO_STEP_DEG = 5° (snap_and_clamp).
- • Cảnh báo đỏ: Khi góc yêu cầu chạm giới hạn cứng.

### Speaker Notes:
Cấu trúc cơ học của cánh tay được xác định bởi các thông số thực tế đo bằng thước: chiều cao khớp vai d1 bằng 70mm, khâu vai L2 dài 105mm, khâu khuỷu L3 dài 100mm, cùng độ vươn đầu kẹp L4r bằng 65mm. Thuật toán IK giải tích chọn nghiệm khuỷu hướng lên để tối ưu không gian vận động và tránh va quẹt với mặt bàn. Các góc khớp sau khi giải sẽ được ánh xạ sang góc xung servo với quy ước chuẩn 90 độ tương ứng theta2 bằng 45 độ và theta3 bằng âm 45 độ, sau đó làm tròn theo bước nhảy 5 độ nằm trong dải giới hạn an toàn tuyệt đối.

## Slide 8

### Text Elements:
- KHÔNG GIAN BÀN & AN TOÀN
- CHUYỂN ĐỔI HỆ TỌA ĐỘ VÀ VÙNG LÀM VIỆC AN TOÀN
- Hệ thống hỗ trợ gắp vật 4-DOF - IoT Robot Arm
- Trang 8 / 15
- CHUYỂN ĐỔI TỌA ĐỘ A4 → ROBOT
- • Vị trí Đế Robot trên tờ A4: base_x_cm = 18.0, base_y_cm = -13.6 cm.
- • Hướng đặt: robot_faces = 'down' (đế mép trên, vươn xuống bàn, hệ số s = -1.0).
- • Công thức tọa độ Robot (mm):
- x_robot_mm = (y_cm - base_y_cm) * 10 = (y_cm + 13.6) * 10
- y_robot_mm = (x_cm - base_x_cm) * 10 = (x_cm - 18.0) * 10
- • Chiều trục: +X_robot vươn sâu vào giấy, +Y_robot hướng sang bên trái.
- • Thuận nghịch: robot_mm_to_table_cm() ánh xạ ngược chính xác sai số < 1e-9 cm.
- KIỂM SOÁT VÙNG AN TOÀN & CẢNH BÁO
- • Tầm với tối đa: max_reach = 205.0 mm (khoảng cách cổ tay rw² + zw²).
- • Tầm với tối thiểu: min_reach = 5.0 mm (tránh điểm kỳ dị khâu gập sát đế).
- • Cảnh báo NGOÀI TẦM VỚI: Hiển thị chữ đỏ rực rỡ khi khoảng cách dist > 205.0 mm.
- • Khoảng cách dời vật: move_closer_mm = dist - (max_reach - 2.0 mm) báo số mm cần đẩy lại gần.
- • Cảnh báo kẹp servo: Phát hiện khi góc yêu cầu vượt ngưỡng [lo - 2.5°, hi + 2.5°].
- • Cập nhật vị trí đế qua ID 4: Tự động hiệu chỉnh lại base_x, base_y nếu tờ A4 bị xê dịch.

### Speaker Notes:
Do camera đo đạc vật thể trên hệ tọa độ centimet của tờ giấy A4, hệ thống cần chuyển đổi sang hệ quy chiếu milimet lấy gốc tại đế robot. Trong bố cục hiện tại, robot đặt ở mép trên tại tọa độ X bằng 18 và Y bằng âm 13.6 centimet, vươn xuống với cấu hình robot_faces bằng 'down'. Nếu mục tiêu nằm ngoài tầm với tối đa 205 milimet, hệ thống sẽ phát cảnh báo đỏ và tính toán chính xác số milimet cần dịch chuyển vật lại gần, đồng thời phát hiện kịp thời các trường hợp góc khớp bị chạm giới hạn cơ khí.

## Slide 9

### Text Elements:
- QUY TRÌNH GẮP VẬT
- QUY TRÌNH GẮP 5 BƯỚC VÀ THỨ TỰ THAO TÁC AN TOÀN
- Hệ thống hỗ trợ gắp vật 4-DOF - IoT Robot Arm
- Trang 9 / 15
- 1. ĐIỂM CHỜCao +60mmMở kẹp (J)Đưa kẹp trên cao
- 2. HẠ XUỐNGSát thân vậtKẹp mởCăn tâm đầu kẹp
- 3. ĐÓNG KẸPKhóa vậtPhím L (165°)Khóa mục tiêu
- 4. NÂNG LÊNCao +80mmGiữ kẹp chặtNhấc khỏi mặt bàn
- 5. KIỂM TRACửa sổ 30f2 Camera S1+S2Thẩm định kết quả
- THỨ TỰ ĐIỀU KHIỂN KHỚP AN TOÀN & BẢNG PHÍM TẮT KEYCAP
- ƯU TIÊN 1
- ĐẾ XOAY (Kênh 0)
- Quay trái (+5°) / Quay phải (-5°)
- A
- D
- ƯU TIÊN 2
- KẸP GẮP (Kênh 3)
- Mở kẹp (-5°) / Kẹp chặt (+5°)
- J
- L
- ƯU TIÊN 3
- KHỚP VAI (Kênh 1)
- Nâng vai lên (+5°) / Hạ vai (-5°)
- W
- S
- ƯU TIÊN 4
- KHỚP KHUỶU (Kênh 2)
- Gập khuỷu lên (+5°) / Duỗi hạ (-5°)
- I
- K
- TỰ ĐỘNG BƯỚCAuto-Step (Phím P)Phát 1 phím / 0.28stheo đúng thứ tự an toàn.
- P

### Speaker Notes:
Quy trình gắp vật được chia thành 5 bước tuần tự chặt chẽ: bắt đầu bằng việc đưa tay tới điểm chờ cao hơn vật 60mm với kẹp mở, hạ xuống sát tâm vật, bấm phím L để kẹp chặt ở góc 165 độ, nâng bổng vật lên 80mm và cuối cùng là giữ yên để kiểm tra. Để đảm bảo an toàn tuyệt đối, hệ thống quy định thứ tự dịch chuyển các khớp là Đế trước, rồi tới Kẹp, sau đó mới tới Vai và Khuỷu nhằm tránh va chạm ngang vào các vật lân cận. Người dùng có thể nhấn phím P để hệ thống tự động phát xung phím sau mỗi 0.28 giây theo đúng trình tự này.

## Slide 10

### Text Elements:
- TỰ ĐỘNG XÁC NHẬN GẮP
- CƠ CHẾ TỰ ĐỘNG XÁC NHẬN GẮP 2 CAMERA ĐỘC LẬP
- Hệ thống hỗ trợ gắp vật 4-DOF - IoT Robot Arm
- Trang 10 / 15
- HAI KÊNH CẢM BIẾN ĐỘC LẬP
- • Kênh S1 (Cam B - Ngang): Phát hiện vật thể nhấc cao hơn mặt bàn > +20 mm.
- • Vạch bàn: SIDE_TABLE_Y_RATIO = 0.54, ngưỡng nâng: SIDE_LIFT_RATIO = 0.065.
- • LOẠI TRỪ MÃ ID 6: Tuyệt đối không tính mã đầu kẹp (chỉ tính ID 10–29 / YOLO).
- • Kênh S2 (Cam A - Trên xuống): Kiểm tra vị trí cũ (locked_grasp_cm) có trống không.
- • Bán kính r = 3.0 cm: Quét dọn chỗ cũ hoàn toàn sạch bóng vật thể.
- CỬA SỔ ĐỒNG THUẬN 80%
- • Cửa sổ trượt: deque(maxlen=30) lưu kết quả từng khung hình của S1 và S2.
- • Tỉ lệ đồng thuận: s1_ratio = sum(s1)/30, s2_ratio = sum(s2)/30.
- • Điều kiện THÀNH CÔNG: Số khung >= 15 và đồng thời s1_ratio >= 0.80 VÀ s2_ratio >= 0.80.
- • Thời gian Timeout: Giới hạn tối đa 3.0 giây ở Bước 5.
- • Biểu ngữ: 'GAP THANH CONG: Cam A + Cam B deu thay vat da roi ban!'
- PHÂN LOẠI LỖI & NHẬT KÝ
- • Phân loại lỗi khi hết 3.0s Timeout:
- • 1. Kẹp trượt (s2 < 0.40): Vật vẫn ở vị trí cũ (kep_truot_vat_van_o_cho_cu).
- • 2. Rơi khi nâng (s1 < 0.40): Cam B không thấy vật (roi_khi_nang_hoac_chua_nhac_len).
- • 3. Không xác định: Bị che khuất tầm nhìn (khong_xac_dinh_bi_che).
- • Ghi nhật ký attempts.csv: Timestamp, tên vật, tọa độ, sai số align_error_mm, S1/S2.

### Speaker Notes:
Điểm sáng tạo cốt lõi của đề tài là cơ chế tự động xác nhận kết quả gắp độc lập bằng 2 camera mà không cần gắn thêm cảm biến áp lực phức tạp. Camera ngang kiểm tra tín hiệu S1 xem vật đã nâng cao hơn mặt bàn 20mm hay chưa, trong đó thuật toán đặc biệt loại trừ mã ID 6 của đầu kẹp để tránh trường hợp kẹp rỗng nâng lên bị báo nhầm là thành công. Cùng lúc đó, camera trên kiểm tra tín hiệu S2 xem vị trí cũ trong bán kính 3 centimet đã hoàn toàn trống hay chưa. Nếu cả hai camera đồng thuận đạt từ 80% trên tổng số 30 khung hình, hệ thống sẽ công nhận thành công và tự động ghi log sai số vào CSV.

## Slide 11

### Text Elements:
- TRUYỀN THÔNG & ĐỒNG BỘ
- GIAO THỨC TRUYỀN THÔNG VÀ ĐỒNG BỘ ARDUINO
- Hệ thống hỗ trợ gắp vật 4-DOF - IoT Robot Arm
- Trang 11 / 15
- MÁY TÍNH (PYTHON)ArduinoSerialLinkGửi ký tự phím 'a','w','s'...Đọc gói JSON trạng thái
- ARDUINO [...]Firmware robot_arm_4dof.inoUSB 9600 & Bluetooth HC-05Phát JSON mỗi 200ms (5Hz)
- MẠCH PCA9685 & SERVOI2C Địa chỉ 0x40, Tần số 50HzXung 12-bit (125 - 575)4x Servo MG996R
- GÓI TIN JSON ĐỒNG BỘ
- • Định dạng JSON gửi từ Arduino:
- {"t":12450,"servo":[90,85,110,165]}
- • Tần số gửi:
- • 1. Gửi tức thời sau mỗi lệnh phím.
- • 2. Gửi định kỳ mỗi 200 ms (5 Hz) qua ngắt timer millis().
- • Đồng bộ góc thực tế với giao diện laptop không bị giật.
- WATCHDOG & FALLBACK
- • Tự động tìm Bluetooth HC-05: Tìm MAC 98D351F6AF14 trên Windows hoặc /dev/cu.HC-05 trên macOS.
- • Tự động Fallback: Đang gửi Bluetooth nếu đứt kết nối sẽ lập tức chuyển sang cáp USB.
- • Phát hiện mất phản hồi (Timeout 2s): Cảnh báo 'BOARD KHONG PHAN HOI' nếu vi điều khiển im lặng > 2.0s.
- MÔ PHỎNG & KHẨN CẤP
- • Chế độ Mô phỏng (Simulation Mode): Tự động kích hoạt khi không cắm board thật, cập nhật góc ảo bằng phím.
- • Kiểm thử độc lập: Cho phép kiểm tra toàn bộ thị giác và giải thuật IK mà không sợ reset board.
- • Phím khẩn cấp [H] (Home): Đưa lập tức 4 servo về tư thế an toàn: [90°, 90°, 90°, 95°].

### Speaker Notes:
Giao thức truyền thông giữa máy tính và vi điều khiển được thiết kế vô cùng tin cậy với tốc độ 9600 baud. Bo mạch Arduino định kỳ phát gói JSON chứa mảng 4 góc servo với tần số 5Hz để đồng bộ thời gian thực với mô hình 3D trên máy tính. Hệ thống hỗ trợ truyền nhận song song qua cả USB và Bluetooth HC-05, có khả năng tự động fallback về cáp USB nếu đường truyền Bluetooth bị gián đoạn. Đặc biệt, nếu không có phần cứng kết nối, phần mềm sẽ tự động chuyển sang chế độ mô phỏng giúp nhóm có thể kiểm thử toàn bộ thuật toán mọi lúc mọi nơi.

## Slide 12

### Text Elements:
- GIAO DIỆN NGƯỜI DÙNG
- THIẾT KẾ GIAO DIỆN NGƯỜI DÙNG VÀ BẢNG PHÍM TẮT
- Hệ thống hỗ trợ gắp vật 4-DOF - IoT Robot Arm
- Trang 12 / 15
- CÁC VÙNG CHỨC NĂNG CHÍNH
- 1. Khung 2 Camera (1280x400): Cam ngang kiểm tra vạch nâng; Cam trên quan sát bàn.
- 2. Thanh Stepper 5 bước: Viên thuốc bo tròn thể hiện tiến độ quy trình gắp.
- 3. Chỉ dẫn phím Keycap: Nút cam chỉ rõ phím cần bấm và số lần lặp xN.
- 4. Thanh trượt servo: Vạch trắng góc hiện tại, vòng tròn mục tiêu cần đạt.
- 5. Thẻ kết quả & Đồng hồ 80%: Hiển thị trạng thái thành công hoặc lý do lỗi.
- DANH MỤC PHÍM TẮT HỆ THỐNG
- • SPACE / N: Sang bước tiếp   • TAB / V: Đổi mục tiêu
- • P: Bật/Tắt Auto-Step        • H: Về vị trí Home
- • R: Reset về Bước 1         • G: Ẩn/Hiện Guide HUD
- • Q: Thoát an toàn khỏi chương trình.

### Speaker Notes:
Đây là hình ảnh thực tế của cửa sổ 'HƯỚNG DẪN GẮP' với độ phân giải 1280 nhân 800 do nhóm tự động sinh từ mã nguồn. Nửa trên hiển thị song song hai góc camera giúp người quan sát nắm bắt trọn vẹn hiện trường, trong khi nửa dưới là bảng hướng dẫn thao tác được thiết kế tương phản cao trên nền tối. Mỗi khớp servo đều có ô keycap màu cam chỉ rõ phím cần bấm, số lần lặp và thanh trượt trực quan hóa góc xoay. Người vận hành chỉ cần làm theo hướng dẫn từng bước mà không cần phải ghi nhớ bất kỳ thông số kỹ thuật phức tạp nào.

## Slide 13

### Text Elements:
- KIỂM THỬ & THỰC NGHIỆM
- KẾT QUẢ KIỂM THỬ GIẢI THUẬT VÀ THỰC NGHIỆM
- Hệ thống hỗ trợ gắp vật 4-DOF - IoT Robot Arm
- Trang 13 / 15
- KIỂM THỬ ĐỘNG HỌC (test_ik.py)
- ✅ 10/10 Bài kiểm thử PASS 100% (Exit code 0).
- ✅ Kiểm thử lưới 455 điểm 3D trong tầm với: Sai số cực đại FK(IK(p)) = 0.000000 mm (< 0.1 mm).
- ✅ Toàn bộ góc servo tuân thủ SERVO_LIMITS và chia hết cho SERVO_STEP_DEG = 5°.
- ✅ Gợi ý phím WASD + IK + JL: Tính toán số xung phím chính xác tuyệt đối.
- ✅ Ánh xạ tờ A4 ↔ Robot: Đúng 100% cho cả 2 hướng up và down.
- ✅ Xử lý ngắt kết nối: Tự động fallback từ Bluetooth về cáp USB khi đứt kết nối.
- ✅ Loại trừ mã ID 6: Kẹp rỗng nâng lên không bị báo nhầm là đã gắp vật.
- THỰC NGHIỆM TRÊN PHẦN CỨNG THẬT
- • Tổng số lượt thử nghiệm gắp: [...] lượt.
- • Tỉ lệ gắp thành công: [...]% (Thành công [...] lượt, Thất bại [...] lượt).
- • Phân bố nguyên nhân thất bại thực nghiệm:
- • Lỗi kẹp trượt (vật vẫn ở chỗ cũ): [...]%
- • Lỗi rơi khi nâng (vật rơi lúc nhấc cao): [...]%
- • Lỗi bị che khuất tầm nhìn: [...]%
- • Sai số căn chỉnh đầu kẹp thực tế: align_error_mm = [...] mm.
- • Thời gian trung bình hoàn thành 5 bước: [...] giây/lượt.
- • Ghi chú: Số liệu thực nghiệm do nhóm cập nhật sau khi chạy chuỗi đo trên cánh tay vật lý.

### Speaker Notes:
Về mặt kiểm thử giải thuật, bộ test tự động test_ik.py đã thực thi thành công toàn bộ 10 bài kiểm tra nghiêm ngặt. Trong đó, giải thuật động học ngược được thử nghiệm trên lưới 455 điểm không gian 3 chiều trong tầm với, cho sai số giữa động học thuận và ngược đạt 0.000000 milimet, chứng minh công thức giải tích hoàn toàn chính xác. Đối với phần thực nghiệm trên mô hình thực tế, do hệ thống nhật ký đang tiếp tục ghi nhận, nhóm xin phép thể hiện các chỉ số về số lượt gắp và tỉ lệ thành công dưới dạng số liệu đang hoàn thiện và sẽ cập nhật chi tiết trong buổi báo cáo trực tiếp.

## Slide 14

### Text Elements:
- ĐÁNH GIÁ & ĐỊNH HƯỚNG
- ĐÁNH GIÁ HẠN CHẾ VÀ HƯỚNG PHÁT TRIỂN MỞ RỘNG
- Hệ thống hỗ trợ gắp vật 4-DOF - IoT Robot Arm
- Trang 14 / 15
- HẠN CHẾ KỸ THUẬT HIỆN TẠI
- • Vạch bàn Cam ngang cố định: Tỉ lệ SIDE_TABLE_Y_RATIO = 0.54 cần đo đạc lại bằng tay nếu di chuyển vị trí webcam laptop.
- • Ước lượng vị trí đế: Tọa độ base_x, base_y ước lượng từ ảnh vẫn còn sai số ±1–2 cm nếu tờ A4 bị xê dịch.
- • Điều khiển servo vòng hở: Servo RC MG996R bước 5° chưa có encoder đọc phản hồi góc thực tế nên có thể bị trễ dưới tải nặng.
- • Phụ thuộc ánh sáng môi trường: Phân đoạn màu LAB tìm 4 góc giấy dễ bị ảnh hưởng khi phòng quá tối hoặc bị bóng sẫm che khuất.
- • Tốc độ khung hình: Mô hình YOLO11s trên CPU thông thường chỉ đạt 10–15 FPS nếu không có bộ tăng tốc GPU/NPU.
- HƯỚNG PHÁT TRIỂN & NÂNG CẤP
- • Tự động định chuẩn 3D với solvePnP: Sử dụng ma trận camera nội quy (Intrinsic Matrix) để tự động tính tư thế 6-DOF không cần vạch bàn thủ công.
- • Điều khiển vòng lặp kín (Closed-loop): Bám vết trực tiếp mã ArUco ID 5 trên đầu kẹp để bù sai số cơ khí thời gian thực.
- • Tự động hóa toàn phần (Full-Autonomous): Tích hợp thuật toán quy hoạch quỹ đạo mượt (Trajectory Planning) gắp vật hoàn toàn tự động.
- • Cảm biến áp lực đầu kẹp: Gắn thêm cảm biến FSR ở ngón kẹp để điều khiển lực kẹp thích ứng với các vật mềm dễ vỡ.
- • Tích hợp ROS2 & IoT Cloud: Đưa trạng thái gắp lên MQTT Dashboard quản lý từ xa qua Internet.

### Speaker Notes:
Nhìn nhận một cách khách quan, hệ thống vẫn tồn tại một số hạn chế nhất định: vị trí vạch mặt bàn của webcam ngang hiện vẫn phụ thuộc vào tỉ lệ đặt trước là 0.54 nên cần canh chỉnh lại nếu dời vị trí laptop, và góc servo bước 5 độ vẫn là điều khiển vòng hở chưa có encoder phản hồi. Trong giai đoạn phát triển tiếp theo, nhóm định hướng tích hợp thuật toán solvePnP để tự động hiệu chuẩn không gian camera 3 chiều, kích hoạt vòng điều khiển kín dựa trên mã ArUco ID 5 gắn ở đầu kẹp, và tiến tới tự động hóa toàn phần quỹ đạo chuyển động của robot.

## Slide 15

### Text Elements:
- TỔNG KẾT & HỎI ĐÁP
- TỔNG KẾT DỰ ÁN VÀ PHIÊN HỎI ĐÁP (Q&A)
- Hệ thống hỗ trợ gắp vật 4-DOF - IoT Robot Arm
- Trang 15 / 15
- ĐỘNG HỌC CHÍNH XÁC
- Làm chủ trọn vẹn giải thuật giải tích Động học thuận và Động học ngược 4-DOF nghiệm khuỷu lên. Sai số 0.000000 mm trên 455 điểm kiểm thử không gian.
- THỊ GIÁC KÉP THÔNG MINH
- Hợp nhất ArUco định vị không gian và YOLO11s nhận diện linh hoạt. Tự động xác nhận gắp bằng 2 camera độc lập với ngưỡng đồng thuận 80%.
- TRẢI NGHIỆM TRỰC QUAN
- Giao diện HƯỚNG DẪN GẮP chuẩn Dark Theme hiện đại, nút Keycap cam trực quan hóa từng phím bấm. Hỗ trợ tự động bước Auto-Step và chế độ mô phỏng.
- XIN CHÂN THÀNH CẢM ƠN QUÝ THẦY CÔ VÀ CÁC BẠN ĐÃ LẮNG NGHE!
- PHIÊN HỎI ĐÁP & ĐÓNG GÓP Ý KIẾN (Q&A)

### Speaker Notes:
Tóm lại, đề tài đã xây dựng thành công một hệ thống hỗ trợ gắp vật hoàn chỉnh cho cánh tay robot 4-DOF, làm chủ từ bài toán giải tích động học ngược, xử lý ảnh thị giác máy tính với ArUco và YOLO11s, cho đến thiết kế giao diện hướng dẫn người dùng trực quan. Hệ thống chứng minh tính khả thi cao và mở ra tiềm năng ứng dụng lớn trong các dây chuyền phân loại sản phẩm mini. Nhóm chúng em xin chân thành cảm ơn quý thầy cô và các bạn đã chú ý lắng nghe, và chúng em rất mong nhận được những câu hỏi và ý kiến đóng góp quý báu.

