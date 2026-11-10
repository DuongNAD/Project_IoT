# Prompt cho Antigravity (Gemini 4 Argon): làm slide thuyết trình Project_IoT

**Cách dùng (trên MacBook Air M5):**
1. Mở thư mục `Project_IoT` trong Antigravity. Chọn model **Gemini 4 Argon**, chế độ **Planning**.
2. Cho phép Agent chạy lệnh terminal: nó cần chạy `python`, cài `python-pptx` / `pymupdf` và xuất PDF.
3. Điền các chỗ `[...]` ở mục "Thông tin nhóm". Chỗ nào chưa biết thì cứ để nguyên.
4. Dán toàn bộ phần **PROMPT** bên dưới vào khung chat. Nếu có file *Kế hoạch dự án* (code có nhắc "tài liệu Kế hoạch
   trang 6, 9, 10, 11, 15"), kéo file đó vào cùng.
5. Agent sẽ dừng lại sau khi gửi dàn ý (Implementation Plan). Đọc và sửa nếu cần, rồi trả lời **"Duyệt"** để nó dựng slide.

---

## PROMPT

Bạn là trợ lý làm slide thuyết trình kỹ thuật, làm việc trực tiếp trong workspace này. Hãy tạo bộ slide **tiếng Việt có dấu
đầy đủ** giới thiệu dự án: hệ thống hỗ trợ gắp vật cho cánh tay robot 4 servo, dùng 2 camera + ArUco + YOLO11 + động học ngược.

### Quy tắc bắt buộc
1. Mọi con số, mã ArUco, phím bấm, ngưỡng, thông số trên slide phải lấy từ code trong workspace. Không đoán, không bịa.
2. Không có số liệu thực nghiệm thật thì để placeholder `[...]`. Tuyệt đối không tự đặt ra tỉ lệ thành công.
3. Chỉ tạo và sửa file trong thư mục `slides/`. Không sửa mã nguồn dự án, `pyproject.toml`, `uv.lock`; không chạy `git commit` / `git push`.
4. Không dùng ảnh do AI tạo để mô tả phần cứng, giao diện hay kết quả thật. Chưa có ảnh thật thì chừa khung ghi `[Ảnh: ...]`.
5. Làm đúng 4 giai đoạn dưới đây. **Dừng ở cuối Giai đoạn 1 để chờ tôi duyệt.**

### Thông tin nhóm (giữ nguyên dạng `[...]` nếu chưa điền)
- Tên đề tài: [Hệ thống hỗ trợ gắp vật cho cánh tay robot 4 bậc tự do bằng thị giác máy tính]
- Môn học / lớp: [...]
- Giảng viên hướng dẫn: [...]
- Thành viên và vai trò: [...]
- Thời lượng thuyết trình: [10–15 phút]
- Loại board Arduino: [...]
- Máy tính chạy hệ thống: MacBook Air M5 (macOS, chip Apple Silicon)
- Điện thoại làm camera trên: [iPhone qua Continuity Camera / Android qua Iriun hoặc IP Webcam]

### Giai đoạn 1: Đọc code và lập dàn ý (xong thì DỪNG chờ duyệt)
Đọc kỹ các file sau:
- `main.py`: luồng camera, ArUco 4 góc tờ A4, homography px→cm, `ArucoYoloTracker` (YOLO chạy luồng nền), vòng lặp chính, phím tắt
- `grasp_assist_4dof.py`: `ARM_CONFIG`, `SERVO_LIMITS`, FK/IK (`fk_4dof_joint`, `ik_4dof_joint`), `joint_to_arduino_servo`,
  `table_cm_to_robot_mm`, `ArduinoSerialLink` (USB + Bluetooth HC-05), `STAGE_NAMES`, `GraspAssist4DOF` (5 bước, S1/S2, log CSV)
- `guide_screen.py`: cửa sổ "HƯỚNG DẪN GẮP" và bảng màu giao diện
- `robot_arm_4dof/robot_arm_4dof.ino`: firmware (PCA9685, HC-05, lệnh phím, gói JSON trạng thái)
- `generate_aruco_a4.py`, `aruco_A4_grid.png`: tờ A4 in mã ArUco
- `test_ik.py`: các bài kiểm thử. Chạy `uv run python test_ik.py` (chưa có uv thì `python3 test_ik.py`) và ghi lại kết quả thật

Nếu có `logs/attempts.csv` thì tính số lần gắp, tỉ lệ thành công, lý do thất bại từ file đó. Không có thì dùng placeholder.

Sau đó tạo **Implementation Plan**. Với từng slide ghi: tiêu đề, 3–6 ý chính, hình hoặc sơ đồ dự kiến, tóm tắt lời thuyết trình,
và **nguồn của từng con số** (tên file + tên hàm hoặc hằng số) để tôi đối chiếu. Dàn ý gợi ý (khoảng 15 slide, mỗi slide nói khoảng 1 phút):

1. **Tiêu đề**: tên đề tài, nhóm, GVHD, môn, ngày
2. **Bài toán và mục tiêu**: điều khiển tay robot bằng phím rất khó căn đúng vị trí. Hệ thống "nhìn" vật, tính góc khớp,
   chỉ cho người dùng bấm phím nào và bấm mấy lần, rồi tự xác nhận gắp thành công hay chưa
3. **Phần cứng**: Arduino + PCA9685 (I2C 0x40, 50 Hz) + 4 servo MG996R (Đế, Vai, Khuỷu, Kẹp) + HC-05 (SoftwareSerial D2/D3, 9600)
   + nguồn 5–6V. Máy tính là MacBook Air M5: YOLO chạy trên GPU Apple qua PyTorch MPS. Camera 1 là webcam MacBook nhìn ngang;
   Camera 2 là điện thoại nhìn từ trên xuống
4. **Kiến trúc phần mềm** (sơ đồ khối): 2 luồng camera → `ArucoYoloTracker` (ArUco + YOLO luồng nền) → homography px→cm
   → `GraspAssist4DOF` (IK, 5 bước, S1/S2) → `ArduinoSerialLink` (USB/Bluetooth, có chế độ mô phỏng) → firmware → servo.
   Giao diện gồm cửa sổ ghép 2 cam + HUD và cửa sổ hướng dẫn
5. **Hệ tọa độ và ArUco**: tờ A4 ngang 29.7 × 21 cm. Mã DICT_4X4_50: ID 0–3 ở 4 góc (2.8 cm, cách mép 0.25 cm), ID 4 trên đế,
   ID 5–6 trên đầu kẹp, ID 10–29 trên vật. Có ảnh `aruco_A4_grid.png`. Giải thích homography và phương án dự phòng
   (phân đoạn màu LAB, mã ArUco ảo) khi chưa thấy mã thật
6. **Nhận diện vật**: YOLO11s chạy luồng nền, chỉ giữ vật nằm trong vùng tờ A4. Gộp với mã ArUco ID 10–29 (bỏ trùng nếu cách nhau
   dưới 2.5 cm), ưu tiên vật gần đế, lọc trung bình trượt 10 khung hình
7. **Động học thuận / ngược**: thông số d1, L2, L3, L4_r, L4_z từ `ARM_CONFIG`, hình minh họa cánh tay, công thức IK giải tích
   (nghiệm khuỷu hướng lên). Cách đổi góc khớp sang góc servo (90° ứng với θ2 = 45°, θ3 = −45°), làm tròn bước 5°, giới hạn servo
8. **Từ tờ A4 sang hệ robot**: vị trí đế (`base_x_cm`, `base_y_cm`, `robot_faces`), đổi dấu trục, kiểm tra tầm với
   ("Ngoài tầm, dời vật gần thêm … mm")
9. **Quy trình gắp 5 bước** (độ cao lấy từ `compute_current_suggestion`): điểm chờ +60 mm → hạ xuống điểm kẹp → đóng kẹp
   → nâng +80 mm → kiểm tra. Bảng phím A/D, W/S, I/K, J/L, H; thứ tự an toàn Đế → Kẹp → Vai → Khuỷu; Auto-Step (phím P)
10. **Tự xác nhận gắp bằng 2 camera**: S1 (cam ngang thấy mã của vật hoặc khung YOLO vượt ngưỡng +20 mm; mã ID 6 trên kẹp không tính)
    và S2 (cam trên thấy chỗ cũ đã trống, bán kính 3 cm). Cửa sổ 30 khung, thành công khi cả hai đạt ≥ 80%; hết 3 giây thì phân
    loại lỗi (kẹp trượt / rơi khi nâng / không xác định). Mỗi lần gắp ghi vào `logs/attempts.csv`, có cả sai số căn đầu kẹp
11. **Giao tiếp Arduino**: USB 9600 baud, board gửi JSON `{"servo":[...]}` 5 lần/giây. Lệnh có thể đi qua HC-05; tự quay về USB khi
    Bluetooth đứt; báo "board không phản hồi" sau 2 giây; không có board thì chạy mô phỏng
12. **Giao diện người dùng**: ảnh cửa sổ "HƯỚNG DẪN GẮP" (cách tạo ảnh ở Giai đoạn 2) và bảng phím tắt
13. **Kiểm thử**: kết quả thật khi chạy `test_ik.py`, kèm kết quả thực nghiệm nếu có
14. **Hạn chế và hướng phát triển** (lấy từ comment trong code): cam ngang còn hiệu chỉnh tay (`SIDE_TABLE_Y_RATIO`, 4 góc đo tay),
    vị trí đế là ước lượng (±1–2 cm), điều khiển theo bước 5° chưa phải vòng kín, thứ tự camera trên macOS đoán theo tên.
    Hướng phát triển: hiệu chỉnh camera (solvePnP), vòng kín bằng mã ID 5, tự động điều khiển toàn bộ
15. **Demo và kết luận**: tóm tắt 3 ý chính, mời đặt câu hỏi

### Giai đoạn 2: Dựng slide (sau khi tôi trả lời "Duyệt")
**Phong cách** (theo bảng màu giao diện app trong `guide_screen.py`, đã đổi từ BGR sang hex RGB):
- Tỉ lệ 16:9 (13.333 × 7.5 inch), nền tối `#191B1E`, thẻ/khối `#272A2E`, viền `#464C52`
- Chữ chính `#F5F5F5`, chữ phụ `#9BA0A5`; nhấn chính (cam) `#FFB928`, thành công (xanh) `#5AD76E`, lỗi (đỏ) `#F55555`
- Font **Arial** (tiêu đề Arial Bold), code và tên hàm **Courier New**: có sẵn trên cả macOS lẫn Windows, đủ dấu tiếng Việt,
  vì file .pptx không nhúng font và có thể phải chiếu trên máy Windows của lớp
- Cỡ chữ: tiêu đề từ 28 pt, nội dung từ 18 pt, chú thích từ 14 pt. Mỗi slide tối đa 6 gạch đầu dòng, mỗi dòng khoảng 12 chữ
- Ưu tiên sơ đồ, bảng và hình hơn chữ. Phím bấm vẽ thành ô "keycap" màu cam chữ tối, giống `keycap()` trong `guide_screen.py`
- Mỗi slide có **speaker notes** tiếng Việt 3–5 câu, viết như lời nói khi trình bày
- Chân slide có số trang và tên đề tài ngắn (trừ slide tiêu đề)

**Cách làm:**
- Viết `slides/build_slides.py` dùng **python-pptx** để sinh `slides/Project_IoT_ThuyetTrinh.pptx`.
  Cài bằng `uv pip install python-pptx` (hoặc `pip install python-pptx`). Sơ đồ vẽ bằng shape của PowerPoint để sửa được.
  File phải mở được bằng cả Keynote lẫn PowerPoint
- Ảnh đặt trong `slides/assets/`. **Ảnh giao diện app** tạo bằng code thật, không cần camera: dùng `fake_assist()` trong `test_ik.py`
  để lấy `info = assist.compute_current_suggestion()` (thêm 1 vật mẫu vào `assist.objects` và `assist.target_history_cm`), rồi gọi
  `guide_screen.build_guide_screen(view_left, view_right, info)`. Hình cam trên dùng `aruco_A4_grid.png`, hình cam ngang dùng khung đen,
  sau đó lưu ảnh bằng `cv2.imwrite`

### Giai đoạn 3: Tự kiểm tra bằng mắt
- Xuất PDF:
  `/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to pdf --outdir slides slides/Project_IoT_ThuyetTrinh.pptx`
- Đổi từng trang PDF sang PNG bằng PyMuPDF (`uv pip install pymupdf`), lưu vào `slides/preview/`
- Xem từng ảnh và sửa `build_slides.py` cho tới khi sạch các lỗi:
  - chữ tràn khỏi khung hoặc đè lên nhau
  - dấu tiếng Việt bị lỗi
  - chữ nhỏ hơn mức quy định
  - màu chữ khó đọc trên nền tối
- Đối chiếu lại mọi con số trên slide với code
- Máy không có LibreOffice thì nói rõ là chưa kiểm tra bằng mắt được, không được báo là đã kiểm tra

### Giai đoạn 4: Báo cáo (Walkthrough)
Báo lại:
- Đường dẫn file .pptx (và .pdf nếu có), danh sách tiêu đề từng slide
- Ảnh preview của 3–4 slide tiêu biểu
- Các placeholder `[...]` còn lại
- Việc nhóm cần tự làm thêm: chụp ảnh phần cứng thật, quay video demo, chạy thực nghiệm để có số liệu
