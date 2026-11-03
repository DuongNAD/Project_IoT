# Original User Request

## Approved Task Prompt — 2026-11-03T10:21:13Z

Tạo bộ slide thuyết trình kỹ thuật 15 slide bằng tiếng Việt có dấu đầy đủ giới thiệu dự án hệ thống hỗ trợ gắp vật cho cánh tay robot 4 bậc tự do (4 servo) dùng 2 camera, ArUco, YOLO11 và động học ngược, thực hiện toàn bộ 4 giai đoạn trực tiếp trong workspace.

Integrity mode: development
The team must NOT: modify files outside slides/, modify project source code, pyproject.toml, or uv.lock, execute git commit or git push, fabricate or guess any metrics/numbers/parameters not present in workspace code, or use AI-generated images for hardware, UI, or experimental results.

## Requirements

### R1. Đọc mã nguồn, chạy kiểm thử và lập Implementation Plan (Giai đoạn 1)
- Đọc kỹ toàn bộ mã nguồn liên quan trong workspace để trích xuất các con số, mã ArUco, phím bấm, thông số cơ khí và ngưỡng giải thuật thực tế:
  - `main.py`: luồng camera, ArUco 4 góc tờ A4, homography px→cm, `ArucoYoloTracker`, vòng lặp chính, phím tắt
  - `grasp_assist_4dof.py`: `ARM_CONFIG`, `SERVO_LIMITS`, FK/IK (`fk_4dof_joint`, `ik_4dof_joint`), `joint_to_arduino_servo`, `table_cm_to_robot_mm`, `ArduinoSerialLink`, `STAGE_NAMES`, `GraspAssist4DOF`
  - `guide_screen.py`: cửa sổ "HƯỚNG DẪN GẮP", hàm `build_guide_screen`, bảng màu giao diện
  - `robot_arm_4dof/robot_arm_4dof.ino`: firmware (PCA9685, HC-05, lệnh phím, JSON trạng thái)
  - `generate_aruco_a4.py`, `aruco_A4_grid.png`: lưới ArUco tờ A4
  - `test_ik.py`: script kiểm thử động học ngược và hàm `fake_assist()`
- Chạy script kiểm thử `test_ik.py` (sử dụng `uv run python test_ik.py` hoặc `python test_ik.py`) và ghi lại kết quả thực tế. Nếu có file `logs/attempts.csv`, tính toán số lần gắp, tỉ lệ thành công và lý do thất bại thực tế; nếu không có, giữ nguyên dạng placeholder `[...]`.
- Lập Implementation Plan chi tiết cho 15 slide theo dàn ý định hướng:
  1. Tiêu đề (tên đề tài, nhóm, GVHD, môn, ngày)
  2. Bài toán và mục tiêu (hỗ trợ điều khiển gắp vật bằng thị giác, tính góc khớp, hướng dẫn phím bấm, tự động xác nhận)
  3. Phần cứng (Arduino, PCA9685 I2C 0x40 50Hz, 4 servo MG996R, HC-05 D2/D3 9600, nguồn 5–6V, MacBook Air M5 PyTorch MPS, webcam ngang và camera điện thoại nhìn trên xuống)
  4. Kiến trúc phần mềm (sơ đồ khối: 2 camera → ArucoYoloTracker → homography → GraspAssist4DOF → ArduinoSerialLink → firmware → servo; HUD & cửa sổ hướng dẫn)
  5. Hệ tọa độ và ArUco (tờ A4 ngang 29.7 × 21 cm, DICT_4X4_50: ID 0–3 ở 4 góc, ID 4 trên đế, ID 5–6 trên đầu kẹp, ID 10–29 trên vật; homography px→cm, dự phòng phân đoạn màu LAB / ArUco ảo)
  6. Nhận diện vật (YOLO11s chạy luồng nền trong vùng A4, kết hợp ArUco ID 10–29 bỏ trùng khoảng cách < 2.5 cm, ưu tiên vật gần đế, lọc trung bình trượt 10 khung hình)
  7. Động học thuận / ngược (thông số d1, L2, L3, L4_r, L4_z từ ARM_CONFIG, công thức IK giải tích nghiệm khuỷu hướng lên, quy đổi góc khớp sang servo với 90° ứng với θ2 = 45°, θ3 = −45°, bước nhảy 5°, giới hạn servo)
  8. Chuyển đổi hệ tọa độ tờ A4 sang hệ robot (base_x_cm, base_y_cm, robot_faces, đổi dấu trục, cảnh báo ngoài tầm với)
  9. Quy trình gắp 5 bước (điểm chờ +60 mm → hạ xuống điểm kẹp → đóng kẹp → nâng +80 mm → kiểm tra; bảng phím A/D, W/S, I/K, J/L, H; thứ tự an toàn Đế → Kẹp → Vai → Khuỷu; Auto-Step phím P)
  10. Tự xác nhận gắp 2 camera (S1 cam ngang thấy mã/YOLO > +20 mm không tính ID 6; S2 cam trên thấy trống bán kính 3 cm; cửa sổ 30 khung ≥ 80%; hết 3s phân loại kẹp trượt / rơi khi nâng / không xác định; log attempts.csv kèm sai số)
  11. Giao tiếp Arduino (USB 9600 baud, JSON {"servo":[...]} 5 Hz, HC-05 tự fallback về USB khi đứt kết nối, timeout 2s, chế độ mô phỏng khi không có board)
  12. Giao diện người dùng (ảnh cửa sổ "HƯỚNG DẪN GẮP" và bảng phím tắt)
  13. Kết quả kiểm thử (kết quả chạy test_ik.py thật, kết quả thực nghiệm nếu có)
  14. Hạn chế và hướng phát triển (hiệu chỉnh cam ngang thủ công SIDE_TABLE_Y_RATIO, ước lượng đế ±1–2 cm, bước nhảy 5° chưa vòng kín, phát hiện camera macOS; hướng phát triển: solvePnP, vòng kín ID 5, tự động toàn phần)
  15. Demo và kết luận (tóm tắt 3 ý chính, Q&A)
- Với từng slide, ghi rõ: tiêu đề, 3–6 ý chính, hình/sơ đồ dự kiến, tóm tắt lời thuyết trình, và nguồn trích xuất của từng con số (tên file + tên hàm hoặc hằng số).

### R2. Dựng slide bằng Python (Giai đoạn 2)
- Tạo thư mục `slides/` và viết script `slides/build_slides.py` sử dụng thư viện `python-pptx` để tự động tạo file `slides/Project_IoT_ThuyetTrinh.pptx` (tỉ lệ 16:9, tương thích cả Keynote và PowerPoint).
- Chuẩn phong cách hiển thị theo `guide_screen.py` (chuyển BGR sang hex RGB):
  - Tỉ lệ: 16:9 (13.333 × 7.5 inch)
  - Nền tối `#191B1E`, thẻ/khối `#272A2E`, viền `#464C52`
  - Chữ chính `#F5F5F5`, chữ phụ `#9BA0A5`, nhấn cam `#FFB928`, xanh lá `#5AD76E`, đỏ `#F55555`
  - Font: Arial (tiêu đề Arial Bold), code và tên hàm dùng Courier New (tiêu đề ≥ 28 pt, nội dung ≥ 18 pt, chú thích ≥ 14 pt; tối đa 6 gạch đầu dòng/slide, mỗi dòng ~12 chữ)
  - Phím bấm vẽ bằng ô "keycap" màu cam chữ tối tương tự `keycap()` trong `guide_screen.py`
  - Sơ đồ khối vẽ bằng Shape của PowerPoint để có thể chỉnh sửa trực tiếp
  - Mỗi slide có speaker notes tiếng Việt (3–5 câu viết theo phong cách thuyết trình thực tế)
  - Chân slide có số trang và tên đề tài ngắn (trừ slide tiêu đề)
- Sinh ảnh giao diện ứng dụng mẫu bằng code vào `slides/assets/`: dùng `fake_assist()` trong `test_ik.py` để lấy `info = assist.compute_current_suggestion()` (thêm vật mẫu vào `assist.objects` và `assist.target_history_cm`), kết hợp `aruco_A4_grid.png` cho view trên và khung đen cho view ngang, gọi `guide_screen.build_guide_screen()` và lưu bằng `cv2.imwrite`. Không sử dụng ảnh AI.

### R3. Kiểm tra trực quan và báo cáo tổng kết (Giai đoạn 3 & 4)
- Kiểm tra trực quan:
  - Nếu máy tính có cài LibreOffice (lệnh `soffice`), chạy chuyển đổi headless sang PDF: `soffice --headless --convert-to pdf --outdir slides slides/Project_IoT_ThuyetTrinh.pptx`.
  - Dùng PyMuPDF (`fitz`) chuyển các trang PDF thành ảnh PNG lưu vào `slides/preview/`.
  - Kiểm tra các lỗi trực quan: tràn khung, đè chữ, lỗi dấu tiếng Việt, cỡ chữ nhỏ hơn quy định, độ tương phản màu trên nền tối, đối chiếu lại số liệu với code và sửa `build_slides.py` nếu phát hiện lỗi.
  - Nếu hệ thống không có sẵn LibreOffice, ghi rõ trong báo cáo là chưa kiểm tra trực quan bằng mắt được.
- Báo cáo tổng kết (Walkthrough):
  - Đường dẫn file `.pptx` (và `.pdf` nếu có), danh sách tiêu đề từng slide.
  - Ảnh preview của các slide tiêu biểu (nếu xuất được PNG).
  - Danh sách các placeholder `[...]` còn lại cần nhóm điền thông tin thực tế.
  - Các công việc nhóm cần thực hiện thêm (chụp ảnh phần cứng thật, quay video demo, thực nghiệm đo tỉ lệ thành công).

### R4. Ràng buộc về phạm vi và tính toàn vẹn
- Chỉ tạo và chỉnh sửa file bên trong thư mục `slides/`. Tuyệt đối không thay đổi mã nguồn dự án, `pyproject.toml`, `uv.lock`. Không chạy các lệnh `git commit` hoặc `git push`.
- Giữ nguyên các thông tin chưa có dạng `[...]` (Môn học/lớp, Giảng viên hướng dẫn, Thành viên và vai trò, Loại board Arduino).
- Tuyệt đối không tự bịa đặt bất kỳ thông số, số liệu thực nghiệm hay tỉ lệ thành công nào.

## Acceptance Criteria

### Tính chính xác và nguồn dẫn chứng
- [ ] 100% các thông số kỹ thuật, kích thước cơ khí, góc servo, mã ArUco, phím bấm và ngưỡng thuật toán trên slide đều có nguồn dẫn chứng rõ ràng từ code trong workspace.
- [ ] Không có số liệu thực nghiệm bịa đặt; các thông tin chưa có đều giữ nguyên placeholder `[...]`.
- [ ] Không có bất kỳ file nào ngoài thư mục `slides/` bị tạo mới hoặc sửa đổi; không có commit git nào được tạo.
- [ ] Không sử dụng bất kỳ hình ảnh nào do AI tạo.

### Chất lượng tệp slide (.pptx)
- [ ] File `slides/Project_IoT_ThuyetTrinh.pptx` được sinh tự động bởi `slides/build_slides.py`, mở được và hiển thị đúng tỉ lệ 16:9.
- [ ] Áp dụng đúng bảng màu dark theme: nền `#191B1E`, thẻ `#272A2E`, viền `#464C52`, nhấn `#FFB928`, `#5AD76E`, `#F55555`.
- [ ] Font chữ chuẩn Arial / Courier New, đúng ngưỡng kích thước: tiêu đề ≥ 28pt, nội dung ≥ 18pt, chú thích ≥ 14pt.
- [ ] Các phím bấm được định dạng theo kiểu ô keycap màu cam chữ tối.
- [ ] Mỗi slide (trừ slide tiêu đề) đều có đầy đủ speaker notes tiếng Việt (3–5 câu) và footer (số trang + tên đề tài ngắn).
- [ ] Ảnh giao diện thật được sinh từ code vào `slides/assets/` và chèn vào slide tương ứng.

### Thực thi kiểm thử và báo cáo
- [ ] Script `test_ik.py` được thực thi và ghi nhận kết quả thực tế vào slide kiểm thử.
- [ ] Nếu có LibreOffice trên hệ thống, tệp PDF và các ảnh PNG preview trong `slides/preview/` được tạo đầy đủ; nếu không có, báo cáo nêu rõ chưa kiểm tra trực quan.
- [ ] Báo cáo tổng kết đầy đủ đường dẫn file, danh mục slide, các placeholder còn lại và hướng dẫn các bước nhóm cần tự làm thêm.
