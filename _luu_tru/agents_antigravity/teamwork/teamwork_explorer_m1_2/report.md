# BÁO CÁO ĐIỀU TRA KỸ THUẬT: PIPELINE THỊ GIÁC, ARUCO, YOLO VÀ FIRMWARE ARDUINO

**Đơn vị thực hiện**: `teamwork_explorer_m1_2`  
**Ngày thực hiện**: 2026-11-03  
**Phạm vi điều tra**: `main.py`, `robot_arm_4dof/robot_arm_4dof.ino`, `generate_aruco_a4.py`, `aruco_A4_grid.png`, và các thành phần liên quan trong `grasp_assist_4dof.py`, `guide_screen.py`.

---

## TỔNG QUAN KẾT QUẢ ĐIỀU TRA

Hệ thống thị giác máy tính và điều khiển cánh tay robot 4 bậc tự do (4-DOF) sử dụng kiến trúc phân tầng đa luồng kết hợp giữa:
1. **Quản lý camera kép đa luồng**: Cam 1 (webcam laptop nhìn ngang - "side") và Cam 2 (điện thoại nhìn từ trên xuống - "topdown") chạy trên 2 luồng `CameraStream` độc lập, buffer size = 1, chống trễ khung hình.
2. **Định vị tờ A4 và ArUco**: Bộ từ điển `DICT_4X4_50` với ID 0–3 ở 4 góc tờ A4 (29.7 × 21.0 cm, marker 2.8 cm, lề 0.25 cm), ID 4 ở đế robot, ID 5 ở đầu kẹp (cam trên), ID 6 ở đầu kẹp (cam ngang), ID 10–29 trên các vật thể mục tiêu.
3. **Phép biến đổi Homography (px → cm bàn)**: Tính ma trận $H_{px \to cm}$ từ 4 góc ArUco thật (hoặc fallback phân đoạn màu LAB / ArUco ảo) giúp chuyển đổi chính xác tọa độ pixel sang tọa độ thực tế trên tờ A4.
4. **Nhận diện vật thể & Dung hợp ArUco - YOLO11s (`ArucoYoloTracker`)**: YOLO11s chạy trên luồng nền riêng biệt trong vùng tờ A4, dung hợp với ArUco ID 10–29 qua ngưỡng loại bỏ trùng lặp khoảng cách $< 2.5\text{ cm}$, sắp xếp ưu tiên vật gần đế robot nhất, và làm mượt tọa độ bằng bộ lọc trung bình trượt 10 khung hình (SMA-10).
5. **Firmware Arduino & Giao tiếp USB/Bluetooth**: Board Arduino điều khiển mạch PCA9685 I2C (địa chỉ `0x40`, tần số `50Hz`) cấp xung cho 4 servo MG996R (bước $5^\circ$), giao tiếp hai chiều USB 9600 baud + Bluetooth HC-05 (chân D2/D3), gửi gói tin JSON trạng thái góc servo tần số 5 Hz (chu kỳ 200ms), tự động fallback về USB khi đứt Bluetooth, hỗ trợ chế độ mô phỏng khi không có phần cứng.

---

## 1. QUẢN LÝ CAMERA KÉP VÀ XỬ LÝ KHUNG HÌNH (`main.py`)

### 1.1. Cấu hình hai camera (Dual Camera Management)
- **Cam 1 (Nhìn ngang - "side")**: Webcam laptop đặt thấp nhìn ngang vào vùng làm việc, hiển thị ở nửa trái màn hình kết hợp.
  - Chỉ số mặc định: `DEFAULT_LAPTOP_INDEX = 1` trên Windows (`sys.platform == "win32"`), `0` trên macOS (dòng 36).
  - Tên hiển thị: `"Cam 1: Laptop (Index X)"` (dòng 238).
- **Cam 2 (Nhìn từ trên xuống - "topdown")**: Camera điện thoại đặt trên cao vuông góc với mặt bàn (dùng qua iPhone Continuity Camera, Iriun Webcam, DroidCam, EpocCam, Camo, hoặc IP Webcam qua Wi-Fi).
  - Chỉ số mặc định: `DEFAULT_PHONE_INDEX = 0` trên Windows, `1` trên macOS (dòng 36).
  - Tên nhận diện tự động: `PHONE_NAME_KEYWORDS = ("iphone", "iriun", "droidcam", "epoccam", "camo")` (dòng 33).
  - Lọc bỏ camera không mong muốn: `NOT_LAPTOP_KEYWORDS = ("virtual", "desk view")` (dòng 35).
  - Luồng IP Webcam: Nhận diện qua URL hoặc IP (`http://192.168.1.5:8080/video`), chuẩn hóa bởi hàm `normalize_phone_url()` (dòng 241–250).
  - Xoay hình ảnh: `PHONE_ROTATE = None` (hỗ trợ `cv2.ROTATE_180`, `cv2.ROTATE_90_CLOCKWISE` nếu camera bị ngược) (dòng 44, 96–97).

### 1.2. Kiến trúc đa luồng `CameraStream` (Threading & FPS)
- **Triệt tiêu độ trễ (Zero-latency buffer)**:
  - Mở camera bằng DirectShow trên Windows: `cv2.VideoCapture(source, cv2.CAP_DSHOW)` để khởi động nhanh và cố định chỉ số thiết bị (dòng 60–63).
  - Đặt kích thước hàng đợi đệm: `cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)` (dòng 64) nhằm đảm bảo `cap.read()` luôn trả về khung hình mới nhất của cảm biến, không bị đọc khung cũ bị ứ trong buffer.
- **Luồng nền độc lập**:
  - Mỗi camera chạy trên một luồng riêng: `self.thread = threading.Thread(target=self._update, daemon=True)` (dòng 82).
  - Đồng bộ hóa dữ liệu bằng khóa `self.lock = threading.Lock()` bảo vệ `self.frame` và `self.ret` (dòng 81, 98–103).
  - Khởi tạo camera trong luồng nền: việc mở camera mất 1–3 giây không làm khóa (freeze) giao diện người dùng chính (dòng 76, 87–92).
- **Cơ chế tự động kết nối lại khi mất tín hiệu (Stalled Watchdog)**:
  - Hằng số thời gian chờ: `RETRY_SECONDS = 4` (dòng 26).
  - Nếu sau 4 giây không nhận được khung hình mới (`time.time() - self.last_frame_time > RETRY_SECONDS`), hàm `is_stalled()` kích hoạt giải phóng camera và thử mở lại (`self.cap.release(); self.cap = None`) (dòng 107–110, 112–114).
  - Nghỉ nhịp khi camera chưa sẵn sàng: `time.sleep(0.1)` (dòng 106) giúp tránh tình trạng vòng lặp chiếm dụng 100% CPU.

### 1.3. Độ phân giải hiển thị và ghép khung hình (Resolutions & Layout)
- **Kích thước chuẩn mỗi góc nhìn**:
  - `VIEW_WIDTH = 640`, `VIEW_HEIGHT = 480` (tỉ lệ 4:3) (dòng 19–20).
- **Hàm `letterbox(frame)`** (dòng 47–55):
  - Thu phóng giữ nguyên tỉ lệ gốc của camera (kể cả camera 16:9 như 1920×1080 hay 1280×720), sau đó chèn viền đen đối xứng để vừa khít khung chuẩn 640×480 mà không bị méo biến dạng hình học.
- **Ghép khung hình chính (`combined_screen` & `full_screen`)**:
  - Ghép ngang 2 camera: `combined_screen = cv2.hconcat([frame_left, frame_right])` → kích thước `1280 × 480` pixel (dòng 855).
  - Vẽ vạch ngăn cách trắng dày 2 px tại $x = 640$: `cv2.line(combined_screen, (VIEW_WIDTH, 0), (VIEW_WIDTH, VIEW_HEIGHT), (255, 255, 255), 2)` (dòng 856).
  - Ghép thanh gợi ý gắp HUD ở dưới: `hud_bar = assist.render_hud_bar(width=1280, info=info)` (chiều cao 175 px) → `full_screen = cv2.vconcat([combined_screen, hud_bar])` → kích thước tổng cộng `1280 × 655` pixel (dòng 858–861).
- **Cửa sổ HƯỚNG DẪN GẮP (`GUIDE_WINDOW`)**:
  - Kích thước độc lập: `GUIDE_W = 1280`, `CAM_H = 400`, `PANEL_H = 400` → tổng kích thước `1280 × 800` pixel (`guide_screen.py`, dòng 18–20).

---

## 2. BẢNG PHÂN BỔ MÃ ARUCO VÀ KÍCH THƯỚC VẬT LÝ

### 2.1. Cấu hình bộ từ điển ArUco
- **Bộ từ điển**: `cv2.aruco.DICT_4X4_50` (chứa 50 mã ArUco 4×4 bit) (dòng 269 trong `main.py`, dòng 31 trong `generate_aruco_a4.py`).
- **Bộ giải mã**: `cv2.aruco.ArucoDetector(ARUCO_DICT, ARUCO_PARAMS)` (dòng 270–271).

### 2.2. Bảng phân bổ ID ArUco toàn hệ thống
| Mã ArUco ID | Vị trí gắn | Kích thước / Ý nghĩa | Tọa độ chuẩn / Mục đích | Nguồn trích xuất |
|---|---|---|---|---|
| **ID 0** | Góc Trên-Trái (TL) tờ A4 | $2.8 \times 2.8\text{ cm}$, cách mép $0.25\text{ cm}$ | Gốc tọa độ $O (0.0, 0.0)\text{ cm}$ | `main.py:286`, `generate_aruco_a4.py:161` |
| **ID 1** | Góc Trên-Phải (TR) tờ A4 | $2.8 \times 2.8\text{ cm}$, cách mép $0.25\text{ cm}$ | Trục X: $(29.7, 0.0)\text{ cm}$ | `main.py:287`, `generate_aruco_a4.py:162` |
| **ID 2** | Góc Dưới-Phải (BR) tờ A4 | $2.8 \times 2.8\text{ cm}$, cách mép $0.25\text{ cm}$ | Điểm cực $(29.7, 21.0)\text{ cm}$ | `main.py:288`, `generate_aruco_a4.py:163` |
| **ID 3** | Góc Dưới-Trái (BL) tờ A4 | $2.8 \times 2.8\text{ cm}$, cách mép $0.25\text{ cm}$ | Trục Y: $(0.0, 21.0)\text{ cm}$ | `main.py:289`, `generate_aruco_a4.py:164` |
| **ID 4** | Trên thân Đế Robot | $2.8 \times 2.8\text{ cm}$ | Tự động cập nhật `base_x_cm`, `base_y_cm` | `grasp_assist_4dof.py:715-718` |
| **ID 5** | Trên đỉnh Đầu kẹp (Cam trên) | Nhìn từ trên xuống | Vị trí thực tế đầu kẹp (Closed-loop topdown) | `grasp_assist_4dof.py:719-733` |
| **ID 6** | Bên hông Đầu kẹp (Cam ngang) | Nhìn từ góc ngang | **LOẠI TRỪ khỏi S1**: tránh báo nhầm khi kẹp rỗng nâng lên | `grasp_assist_4dof.py:879-880` |
| **ID 10** | Hộp vuông | $40 \times 40 \times 40\text{ mm}$ | `Hop_Vuong_ID10` | `grasp_assist_4dof.py:65` |
| **ID 11** | Hộp xanh chữ nhật | $35 \times 50 \times 35\text{ mm}$ | `Hop_Xanh_ID11` | `grasp_assist_4dof.py:66` |
| **ID 12** | Hộp đỏ | $30 \times 60 \times 40\text{ mm}$ | `Hop_Do_ID12` | `grasp_assist_4dof.py:67` |
| **ID 13** | Khối trụ | $35 \times 35 \times 50\text{ mm}$ | `Khoi_Tru_ID13` | `grasp_assist_4dof.py:68` |
| **ID 14–29** | Vật thể ArUco khác | Mặc định $35 \times 35 \times 40\text{ mm}$ | `Vat_ArUco` (`DEFAULT_OBJ_SPEC`) | `grasp_assist_4dof.py:70` |

---

## 3. HỆ TỌA ĐỘ VÀ GIẢI THUẬT HOMOGRAPHY (PX → CM BÀN)

### 3.1. Kích thước vật lý chuẩn của tờ A4
- Khổ giấy A4 đặt ngang (Landscape):
  - Chiều ngang: `NOTEBOOK_W_CM = 29.7` cm ($297.0\text{ mm}$).
  - Chiều dọc: `NOTEBOOK_H_CM = 21.0` cm ($210.0\text{ mm}$).
- Vị trí vật lý của 4 mã ArUco thật in sát góc:
  - Cạnh mã ArUco: $s = 2.8\text{ cm}$.
  - Lề cách mép giấy: $m = 0.25\text{ cm}$ ($2.5\text{ mm}$).
  - Hộp tọa độ thực của từng mã (dòng 331–337, 603–610 trong `main.py`):
    - ID 0: $[[m, m], [m+s, m], [m+s, m+s], [m, m+s]]$
    - ID 1: $[[W-m-s, m], [W-m, m], [W-m, m+s], [W-m-s, m+s]]$
    - ID 2: $[[W-m-s, H-m-s], [W-m, H-m-s], [W-m, H-m], [W-m-s, H-m]]$
    - ID 3: $[[m, H-m-s], [m+s, H-m-s], [m+s, H-m], [m, H-m]]$

### 3.2. Thuật toán tính ma trận Homography
1. **Khi có mã ArUco thật (`has_real_aruco >= 2` mã)**:
   - Thu thập 4 điểm góc pixel $c[0]$ từ mỗi mã ArUco nhận diện được và 4 điểm tọa độ cm tương ứng từ `marker_cm_boxes` (tối thiểu 8 điểm, tối đa 16 điểm) (dòng 611–616).
   - Gọi hàm OpenCV tính ma trận biến đổi phối cảnh 2D:
     $$H_{px \to cm} = \text{cv2.findHomography}(\text{np.float32}(img\_pts), \text{np.float32}(cm\_pts), 0)$$ (dòng 657).
   - Tính ma trận nghịch đảo để vẽ ngược từ cm lên ảnh pixel:
     $$H_{cm \to px} = H_{px \to cm}^{-1} = \text{np.linalg.inv}(H_{px \to cm})$$ (dòng 658).
2. **Quy đổi tọa độ điểm bất kỳ**:
   - Từ pixel sang tọa độ bàn (cm):
     $$P_{cm} = \text{cv2.perspectiveTransform}([P_{px}], H_{px \to cm})$$ (dòng 716).
   - Từ tọa độ bàn sang pixel để vẽ overlay:
     $$P_{px} = \text{cv2.perspectiveTransform}([P_{cm}], H_{cm \to px})$$ (dòng 728–729).
3. **Vẽ lưới tọa độ và thước đo**:
   - Trục OX (Đỏ Cam: ID 0 $\to$ ID 1, $0 \to 29.7\text{ cm}$) (dòng 699, 706–707).
   - Trục OY (Xanh Cyan: ID 0 $\to$ ID 3, $0 \to 21.0\text{ cm}$) (dòng 700, 708–709).
   - Lưới phụ mỗi $5.0\text{ cm}$ ($50\text{ mm}$): kẻ các vạch dọc tại $x \in \{5, 10, 15, 20, 25\}\text{ cm}$ và ngang tại $y \in \{5, 10, 15\}\text{ cm}$ (dòng 677–694).

---

## 4. CƠ CHẾ DỰ PHÒNG KHI KHÔNG CÓ MÃ ARUCO THẬT (FALLBACK)

### 4.1. Phân đoạn màu LAB tìm 4 góc tờ A4 (`detect_notebook_corners_topdown`)
Khi người dùng chưa in tờ giấy ArUco thật hoặc mã bị che khuất:
- **Chuyển không gian màu**: `cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)` (dòng 309).
- **Ngưỡng nhị phân hóa (inRange)**:
  - Kênh L: $130 \to 255$
  - Kênh A: $0 \to 134$
  - Kênh B: $125 \to 255$
  - Lọc dải màu của nền giấy trắng/vở học sinh dưới ánh sáng phòng (dòng 310).
- **Phép toán hình thái học (Morphology)**:
  - Closing với kernel chữ nhật $25 \times 25$ để lấp kín các khoảng thủng bên trong (dòng 311).
  - Opening với kernel chữ nhật $11 \times 11$ để triệt tiêu nhiễu hạt nhỏ xung quanh (dòng 312).
- **Lọc đường biên (Contour filtering)**:
  - Tìm contour có diện tích lớn nhất thỏa mãn $S_{contour} > 0.12 \times (W_{frame} \times H_{frame})$ (dòng 314–315).
  - Tìm hình chữ nhật nghiêng nhỏ nhất: `cv2.minAreaRect(c)`.
  - Sắp xếp 4 đỉnh theo thứ tự chuẩn TL (ID 0), TR (ID 1), BR (ID 2), BL (ID 3) qua hàm `order_quad_points()` (dòng 293–303, 317).
- **Tọa độ tĩnh mặc định (Static fallback)**:
  - Nếu phân đoạn màu thất bại (phòng quá tối/quá sáng), tự áp dụng tọa độ góc đo sẵn trên khung hình $1920 \times 1080$:
    `[[505*sx, 118*sy], [1380*sx, 70*sy], [1405*sx, 678*sy], [535*sx, 718*sy]]` (dòng 319–320).

### 4.2. Gán mã ArUco ảo (Virtual ArUco Overlay)
- **Topdown (`overlay_virtual_aruco_topdown`)**:
  - Tính ma trận phối cảnh $H$ từ hình chữ nhật chuẩn $29.7 \times 21.0\text{ cm}$ sang 4 góc tứ giác `quad_pts` (dòng 375–378).
  - Dán 4 ảnh mã ArUco ảo kích thước tile $120\text{ px}$ + viền Quiet Zone $16\text{ px}$ (tổng $152 \times 152\text{ px}$) vào 4 góc giấy bằng `cv2.warpPerspective` và mặt nạ `cv2.fillConvexPoly` (dòng 390–399).
  - Khi tính Homography từ mã ảo, thuật toán bù trừ vùng đệm Quiet Zone:
    `pad = 2.8 * (16.0 / 152.0)`, `s = 2.8 * (120.0 / 152.0)` để 16 điểm góc của mã ảo ánh xạ chính xác tuyệt đối với tọa độ thực (dòng 620–635).
- **Side view (`overlay_virtual_aruco_side`)**:
  - Gán 4 mã ảo tại 4 góc mặt vở đo sẵn trên khung $1440 \times 1080$: ID 0 `[1330*sx, 595*sy]`, ID 1 `[95*sx, 600*sy]`, ID 2 `[265*sx, 485*sy]`, ID 3 `[1065*sx, 475*sy]` (dòng 364–369, 402–414).

---

## 5. BỘ THEO DÕI VẬT THỂ VÀ DUNG HỢP YOLO11s (`ArucoYoloTracker`)

### 5.1. Khởi tạo và thiết bị phần cứng
- **Khởi tạo luồng nền**: `self.worker = threading.Thread(target=self._yolo_loop, daemon=True)` (dòng 449).
- **Tải mô hình**: `YOLO("yolo11s.pt")` (dòng 457–459).
- **Tự động nhận diện thiết bị phần cứng**:
  - `cuda:0` nếu có GPU NVIDIA và thư viện PyTorch CUDA (dòng 461–462).
  - `mps` nếu chạy trên Apple Silicon (MacBook Air / Pro chip M-series) (dòng 463–464).
  - `cpu` nếu không có bộ tăng tốc phần cứng (dòng 443).
- **Tần số chạy luồng nền**: Chu kỳ nghỉ `time.sleep(0.03)` (~33 Hz) khi có khung hình mới (dòng 500).

### 5.2. Nhận diện vật thể trên Cam trên xuống (`_detect_objects_topdown`)
- **Vùng cắt (Bounding Crop)**: Cắt ảnh bao quanh tứ giác tờ A4 cộng thêm lề an toàn 10 px ($x_1 - 10, y_1 - 10, x_2 + 10, y_2 + 10$) (dòng 506–510).
- **Tham số chạy YOLO**:
  - Ngưỡng tin cậy: `conf = 0.12` (dòng 516).
  - Kích thước ảnh đầu vào: `imgsz = 960` (dòng 516).
- **Lọc vật thể**:
  - Loại bỏ hộp quá lớn ($S_{box} > 0.40 \times S_{A4}$) hoặc quá nhỏ ($S_{box} < 400\text{ px}^2$) (dòng 522–523).
  - Kiểm tra tâm vật thể nằm trọn trong tờ A4: `cv2.pointPolygonTest(poly, (cx, cy), True) >= 15` (cách mép giấy tối thiểu 15 px) (dòng 526).

### 5.3. Nhận diện vật thể trên Cam nhìn ngang (`_detect_objects_side`)
- **Tham số YOLO**: `conf = 0.20`, `imgsz = 640` (dòng 539).
- **Loại trừ các lớp không liên quan**: `cls_name in ("laptop", "tv", "bed", "book", "chair", "dining table")` (dòng 548–549).
- **Điểm tiếp xúc chân đế vật thể**: `cy_base = fy2 - 0.30 * (fy2 - fy1)` (dòng 553).
- **Kiểm tra vùng bàn**: `cv2.pointPolygonTest(poly, (cx, cy_base), True) >= -25` (dòng 554).

### 5.4. Giải thuật Dung hợp ArUco - YOLO (`grasp_assist_4dof.py:701-770`)
1. **Ưu tiên ArUco ID 10–29**: Quét tất cả các mã ArUco dán trên vật thể. Tọa độ $(x_{cm}, y_{cm})$ được chuyển đổi qua $H_{px \to cm}$. Kích thước $(w, l, h)$ lấy từ từ điển `OBJECT_SPECS` hoặc `DEFAULT_OBJ_SPEC`.
2. **Khử trùng lặp (Deduplication threshold $< 2.5\text{ cm}$)**:
   - Với mỗi vật thể do YOLO phát hiện tại $(ox_{cm}, oy_{cm})$, tính khoảng cách Euclid tới các vật ArUco đã có:
     $$\text{dist} = \sqrt{(ox_{cm} - x_{cm})^2 + (oy_{cm} - y_{cm})^2}$$
   - Nếu $\text{dist} < 2.5\text{ cm}$: Bỏ qua kết quả YOLO (coi như trùng với vật thể ArUco đã được định danh chính xác hơn) (dòng 752–753).
   - Nếu $\text{dist} \ge 2.5\text{ cm}$: Thêm vào danh sách với nhãn `YOLO:<cls>`, kích thước quy ước $35.0 \times 40.0\text{ mm}$ (dòng 754–762).
3. **Sắp xếp thứ tự ưu tiên gắp (Proximity Sorting)**:
   - Danh sách vật thể được sắp xếp theo khoảng cách tăng dần tới Đế Robot (`ARM_CONFIG["base_x_cm"]`, `ARM_CONFIG["base_y_cm"]`):
     $$\text{key} = \sqrt{(x - x_{base})^2 + (y - y_{base})^2}$$
   - Vật nằm gần đế nhất luôn được chọn làm mục tiêu gắp đầu tiên (`selected_idx = 0`) (dòng 765–770).
4. **Bộ lọc trung bình trượt 10 khung hình (10-frame SMA)**:
   - Khởi tạo hàng đợi: `self.target_history_cm = deque(maxlen=10)` (dòng 583).
   - Mỗi khung hình, tọa độ mục tiêu được đẩy vào hàng đợi: `self.target_history_cm.append((sel["x_cm"], sel["y_cm"]))` (dòng 807).
   - Tọa độ mục tiêu cấp cho động học ngược IK là trung bình cộng của 10 khung hình gần nhất:
     $$\bar{X}_{cm} = \frac{1}{N} \sum_{i=1}^N X_i, \quad \bar{Y}_{cm} = \frac{1}{N} \sum_{i=1}^N Y_i \quad (N \le 10)$$
     (dòng 665, 924, 973). Giải pháp này triệt tiêu hoàn toàn hiện tượng rung lắc (jitter) do nhiễu camera.

---

## 6. VÒNG LẶP CHÍNH VÀ DANH MỤC PHÍM TẮT ĐIỀU KHIỂN

### 6.1. Cấu trúc vòng lặp chính (`main()` trong `main.py`)
```
[Khởi tạo Camera + Serial Link + ArucoYoloTracker + GraspAssist4DOF]
                        │
                        ▼
┌───────────────── Vòng lặp while True ─────────────────┐
│ 1. Lấy khung hình mới nhất từ cam_laptop & cam_phone   │
│ 2. tracker.process_frame() (ArUco + Homography + YOLO) │
│ 3. letterbox() đưa về 640x480 & hconcat() (1280x480)   │
│ 4. assist.compute_current_suggestion() (IK + 5 bước)   │
│ 5. assist.render_hud_bar() (1280x175) & vconcat()     │
│ 6. cv2.imshow() hiển thị màn hình chính (1280x655)    │
│ 7. cv2.imshow() hiển thị GUIDE_WINDOW (1280x800)       │
│ 8. Đọc phím cv2.waitKey(1):                            │
│    - Thoát 'Q' / Phím hệ thống / assist.handle_key()   │
└────────────────────────────────────────────────────────┘
                        │
                        ▼
[Giải phóng tài nguyên (release camera, serial, destroyAllWindows)]
```

### 6.2. Danh mục đầy đủ tất cả các phím tắt điều khiển
| Phím | Nơi xử lý | Chức năng chi tiết | Khối / Giới hạn tác động |
|---|---|---|---|
| **`W` / `w`** | `handle_key` (`grasp_assist_4dof.py:1204`) | Nâng cánh tay (Vai quay lên $+5^\circ$) | Kênh 1: Servo Vai ($25^\circ \to 155^\circ$) |
| **`S` / `s`** | `handle_key` (`grasp_assist_4dof.py:1204`) | Hạ cánh tay (Vai quay xuống $-5^\circ$) | Kênh 1: Servo Vai ($25^\circ \to 155^\circ$) |
| **`A` / `a`** | `handle_key` (`grasp_assist_4dof.py:1204`) | Xoay đế sang Trái ($+5^\circ$) | Kênh 0: Servo Đế ($0^\circ \to 180^\circ$) |
| **`D` / `d`** | `handle_key` (`grasp_assist_4dof.py:1204`) | Xoay đế sang Phải ($-5^\circ$) | Kênh 0: Servo Đế ($0^\circ \to 180^\circ$) |
| **`I` / `i`** | `handle_key` (`grasp_assist_4dof.py:1204`) | Gập khuỷu lên ($+5^\circ$) | Kênh 2: Servo Khuỷu ($25^\circ \to 155^\circ$) |
| **`K` / `k`** | `handle_key` (`grasp_assist_4dof.py:1204`) | Duỗi khuỷu xuống ($-5^\circ$) | Kênh 2: Servo Khuỷu ($25^\circ \to 155^\circ$) |
| **`J` / `j`** | `handle_key` (`grasp_assist_4dof.py:1204`) | Mở kẹp ra ($-5^\circ$) | Kênh 3: Servo Kẹp ($95^\circ \to 175^\circ$) |
| **`L` / `l`** | `handle_key` (`grasp_assist_4dof.py:1204`) | Kẹp chặt vào ($+5^\circ$) | Kênh 3: Servo Kẹp ($95^\circ \to 175^\circ$) |
| **`H` / `h`** | `handle_key` (`grasp_assist_4dof.py:1204`) | Đưa 4 servo về vị trí an toàn Home | Đế: $90^\circ$, Vai: $90^\circ$, Khuỷu: $90^\circ$, Kẹp: $95^\circ$ |
| **`SPACE` / `N`** | `handle_key` (`grasp_assist_4dof.py:1207`) | Chuyển sang bước tiếp theo trong quy trình 5 bước | Bước $1 \to 2 \to 3 \to 4 \to 5$ |
| **`TAB` / `V`** | `handle_key` (`grasp_assist_4dof.py:1210`) | Chuyển đổi mục tiêu sang vật thể tiếp theo | Duyệt vòng tròn danh sách `self.objects` |
| **`P` / `p`** | `handle_key` (`grasp_assist_4dof.py:1213`) | Bật / Tắt chế độ tự động gửi phím (Auto-Step) | Tự gửi 1 phím/khung hình theo thứ tự an toàn |
| **`R` / `r`** | `handle_key` (`grasp_assist_4dof.py:1217`) | Reset quy trình gắp về Bước 1 | Hủy khóa vật, xóa cửa sổ S1/S2 |
| **`M` / `m`** | `main()` (`main.py:887`) | Bật / Tắt lớp phủ ArUco + Homography + YOLO | Đổi giữa chế độ trực quan và camera mộc |
| **`G` / `g`** | `main()` (`main.py:890`) | Ẩn / Hiện cửa sổ HƯỚNG DẪN GẮP (`GUIDE_WINDOW`) | Bật / tắt cửa sổ hướng dẫn thao tác to |
| **`C` / `c`** | `main()` (`main.py:900`) | Chụp ảnh gốc 2 camera lưu vào `captures/` | Đặt tên theo thời gian `YYYYMMDD_HHMMSS` |
| **`X` / `x`** | `main()` (`main.py:902`) | Đổi chỗ 2 camera Trái $\leftrightarrow$ Phải | Áp dụng khi điện thoại nhận nhầm vị trí |
| **`0` .. `3`** | `main()` (`main.py:911`) | Đổi chỉ số camera điện thoại / webcam laptop | Đổi thiết bị video trực tiếp không cần restart |
| **`Q` / `q`** | `main()` (`main.py:883`) | Thoát chương trình | Giải phóng an toàn tất cả camera và cổng COM |

---

## 7. FIRMWARE ARDUINO VÀ PHẦN CỨNG (`robot_arm_4dof.ino`)

### 7.1. Giao diện phần cứng (Hardware Interfaces)
- **Bộ vi điều khiển**: Arduino (Uno / Nano) kết nối máy tính qua cáp USB và module Bluetooth HC-05.
- **Mạch điều khiển xung PCA9685**:
  - Giao tiếp: I2C (chân SDA / SCL của Arduino).
  - Địa chỉ phần cứng I2C: `0x40` (`Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);`, dòng 8).
  - Tần số PWM: `50Hz` (`pwm.setPWMFreq(50);`, dòng 47) chuẩn cho servo RC.
- **Động cơ Servo**: 4 động cơ MG996R bánh răng kim loại, lực kéo cao.
  - Kênh 0: Đế xoay (Base) (`angleBase = 90`, phạm vi $0^\circ \dots 180^\circ$)
  - Kênh 1: Cánh tay nâng hạ (Shoulder) (`angleShoulder = 90`, phạm vi $25^\circ \dots 155^\circ$)
  - Kênh 2: Khuỷu tay (Elbow) (`angleElbow = 90`, phạm vi $25^\circ \dots 155^\circ$)
  - Kênh 3: Kẹp gắp (Gripper) (`angleGrip = 95`, phạm vi $95^\circ \dots 175^\circ$)
- **Ánh xạ độ sang xung PWM (Servo Pulse Mapping)**:
  - Hằng số xung: `#define SERVOMIN 125` (~0 độ), `#define SERVOMAX 575` (~180 độ) (dòng 11–12).
  - Công thức quy đổi: `int pulse = map(angle, 0, 180, SERVOMIN, SERVOMAX);` (dòng 26).
  - Độ phân giải bước góc: `#define STEP 5` (mỗi phím bấm di chuyển đúng $5^\circ$) (dòng 13).
- **Module Bluetooth HC-05**:
  - Giao tiếp qua `SoftwareSerial BT(2, 3);` (chân RX gắn vào D2 Arduino, TX gắn vào D3 Arduino) (dòng 6).
  - Tốc độ truyền (baud rate): `9600 baud` (`BT.begin(9600);`, dòng 44).
  - Mã PIN ghép đôi: `1234`.
  - Địa chỉ MAC mặc định trên robot: `ROBOT_BT_DEFAULT = "98D351F6AF14"` (`grasp_assist_4dof.py:313`).
- **Nguồn cấp (Power Supply Specifications)**:
  - Nguồn ngoài riêng biệt: $5\text{V} - 6\text{V}$ DC cấp trực tiếp vào cọc nguồn xanh của PCA9685.
  - Tuyệt đối không dùng chân 5V của Arduino để nuôi 4 servo MG996R vì dòng khởi động/kẹt của 4 servo có thể lên tới 6–10A, gây sụt áp làm reset Arduino ngay lập tức.

### 7.2. Giao thức truyền thông và phản hồi trạng thái
- **Giao thức nhận lệnh hai chiều (Bidirectional Command Handling)**:
  - Vòng lặp `loop()` ưu tiên đọc từ Bluetooth trước, sau đó tới USB Serial:
    `if (BT.available()) cmd = BT.read(); else if (Serial.available()) cmd = Serial.read();` (dòng 63–67).
  - Phản hồi xác nhận: Sau khi nhận phím, Arduino in lại dòng `Serial.print("Phím bấm: "); Serial.println(cmd);` (dòng 70–71).
- **Gói tin JSON báo trạng thái 4 Servo (`sendServoState`)**:
  - Định dạng: `{"t":<millis>,"servo":[angleBase,angleShoulder,angleElbow,angleGrip]}` (dòng 31–40).
  - Tần số gửi:
    1. Gửi ngay lập tức sau mỗi lần nhận lệnh thay đổi góc (dòng 119–120).
    2. Gửi định kỳ mỗi 200 ms ($5\text{ Hz}$): `if (millis() - lastReportMs >= 200)` (dòng 124–127) để giữ đồng bộ góc thực tế với giao diện laptop.
- **Cơ chế Fallback và Chế độ Mô phỏng (`ArduinoSerialLink`)**:
  - **Fallback Bluetooth $\to$ USB**: Trên máy tính, `ArduinoSerialLink` ưu tiên gửi qua cổng COM Bluetooth HC-05 (`self.bt_ser`). Nếu Bluetooth đứt kết nối hoặc lỗi ghi, tự động đóng cổng và quay về gửi qua cáp USB (`self.ser`) (dòng 434–457 trong `grasp_assist_4dof.py`).
  - **Phát hiện board treo / mất kết nối (2s Timeout)**:
    - Nếu đã gửi lệnh qua USB/Bluetooth quá 2.0 giây mà không hề nhận được phản hồi (`heard_board == False` và `time.time() - unanswered_since > 2.0s`), hàm `board_ignores_usb()` sẽ trả về `True` (dòng 394–398 trong `grasp_assist_4dof.py`) để cảnh báo người dùng trên thanh HUD.
  - **Chế độ Mô phỏng (Simulation Mode)**:
    - Nếu không cắm cáp USB Arduino hoặc không có module Bluetooth, `ArduinoSerialLink` tự động chuyển sang chế độ mô phỏng cục bộ: hàm `apply_key_locally(ch)` tự cập nhật mảng góc `self.servo` theo đúng logic của firmware Arduino, cho phép kiểm thử toàn bộ hệ thống thị giác, động học ngược IK và giao diện mà không cần board thật (dòng 402–427, 459).

---

## 8. LƯỚI ARUCO TỜ A4 VÀ FILE TẠO LƯỚI (`generate_aruco_a4.py`)

### 8.1. Thông số thiết kế và kích thước tệp
- **File kịch bản**: `generate_aruco_a4.py` (226 dòng code).
- **File xuất ra**:
  - `aruco_A4_grid.png` & `aruco_A4_grid.pdf`: Bản in có lưới milimet/centimet và thước đo tọa độ.
  - `aruco_A4_clean.png` & `aruco_A4_clean.pdf`: Bản in nền trắng tinh, chỉ có 4 mã ArUco sát góc.
- **Thông số hình học & độ phân giải**:
  - Khổ giấy: $297.0 \times 210.0\text{ mm}$ ($29.7 \times 21.0\text{ cm}$).
  - Độ phân giải in ấn chuẩn: `DPI = 300`.
  - Tỉ lệ quy đổi: `PX_PER_MM = 300 / 25.4` (~$11.811\text{ px/mm}$), `PX_PER_CM = 300 / 2.54` (~$118.11\text{ px/cm}$) (dòng 24–25).
  - Kích thước ảnh xuất: `IMG_W = 3508` px, `IMG_H = 2480` px (dòng 27–28).

### 8.2. Bố cục chi tiết trên tờ giấy
- **Kích thước mã ArUco**: `MARKER_SIZE_CM = 2.8` cm ($28.0\text{ mm}$, tương ứng $331\text{ px}$).
- **Khoảng cách mép giấy**: `MARGIN_CM = 0.25` cm ($2.5\text{ mm}$, tương ứng $30\text{ px}$).
- **Vùng bảo vệ trắng (Quiet Zone)**: `quiet_px = 30` px ($2.5\text{ mm}$) trắng 100% quanh mỗi mã để OpenCV nhận diện đường biên đen ngoài cùng không bị nhiễu bởi lưới thước (dòng 50, 169–174).
- **Vị trí 4 góc ArUco (DICT_4X4_50)**:
  - **ID 0**: Góc Trên-Trái ($x = 30\text{ px}, y = 30\text{ px}$) $\to$ Nhãn: `"ID:0 (0, 0 cm) - GOC O"`
  - **ID 1**: Góc Trên-Phải ($x = 3147\text{ px}, y = 30\text{ px}$) $\to$ Nhãn: `"ID:1 (29.7, 0 cm) - TRUC X"`
  - **ID 2**: Góc Dưới-Phải ($x = 3147\text{ px}, y = 2119\text{ px}$) $\to$ Nhãn: `"ID:2 (29.7, 21.0 cm)"`
  - **ID 3**: Góc Dưới-Trái ($x = 30\text{ px}, y = 2119\text{ px}$) $\to$ Nhãn: `"ID:3 (0, 21.0 cm) - TRUC Y"`
- **Lưới tọa độ và vạch chia độ**:
  - Lưới $1\text{ cm}$: Nét xám nhạt `#F0F0F0` (dòng 55–60).
  - Lưới $5\text{ cm}$: Nét xám đậm `#DCDCDC` tại các mốc 5, 10, 15, 20, 25 cm (dòng 63–68).
  - Vạch chia milimet: Dọc theo cạnh trên từ $35\text{ mm} \to 263\text{ mm}$ và cạnh trái từ $35\text{ mm} \to 176\text{ mm}$ (dòng 71–110).
  - Dấu chữ thập tâm A4: Tọa độ chính giữa $(14.85\text{ cm}, 10.50\text{ cm})$ (dòng 138–153).

---

## 9. KẾT QUẢ CHẠY KIỂM THỬ THỰC TẾ (`test_ik.py`)

Kịch bản kiểm thử toàn diện `test_ik.py` được thực thi với môi trường biến UTF-8 (`$env:PYTHONUTF8=1; python test_ik.py`). Kết quả xác thực 100% đạt chuẩn:

```
✅ [PASS] Đã kiểm thử 455 điểm 3D trong tầm với: sai số FK(IK(p)) tối đa = 0.000000 mm (< 0.1 mm)
✅ [PASS] Kiểm thử gợi ý bấm phím (WASD + IK + JL) với STEP = 5° chính xác tuyệt đối!
✅ [PASS] Ánh xạ tờ A4 <-> hệ robot đúng cho cả hai hướng đặt robot (up / down)
✅ [PASS] Phát hiện board không nhận lệnh USB (firmware cũ)
✅ [PASS] Tìm cổng Bluetooth của HC-05 (Windows theo địa chỉ MAC, macOS theo tên cổng)
✅ [PASS] Gửi lệnh qua Bluetooth HC-05, tự quay về USB khi BT đứt
✅ [PASS] S1 chỉ tính mã của vật (ID 10-29), kẹp rỗng nâng lên không bị báo là đã gắp
📝 Đã ghi kết quả gắp vào C:\Users\DELL\AppData\Local\Temp\...\logs\attempts.csv: SUCCESS (ok)
✅ [PASS] Khóa vật lúc đóng kẹp cho bước nâng + kiểm tra, log CSV ghi đúng sai số căn đầu kẹp
✅ [PASS] Chuẩn hóa địa chỉ IP Webcam của điện thoại
📷 Camera: 0=Duong's iPhone Desk View Camera, 1=Duong's iPhone Camera, 2=MacBook Air Camera
📷 Camera: 0=OBS Virtual Camera, 1=MacBook Air Camera
✅ [PASS] Nhận camera MacBook và iPhone (Continuity Camera) theo tên trên macOS
```

- **Thống kê thực nghiệm từ file log (`logs/attempts.csv`)**:
  - Trong thư mục làm việc hiện tại, file `logs/attempts.csv` chưa tồn tại trong repo gốc.
  - Do đó, tuân thủ đúng yêu cầu R1 & Acceptance Criteria, số liệu thực nghiệm về số lần gắp, tỉ lệ thành công và nguyên nhân thất bại sẽ được giữ ở định dạng placeholder `[...]` để nhóm điền số liệu thực tế sau khi chạy thí nghiệm thực tế trên cánh tay vật lý.
