# HANDOFF REPORT — UI & 15-SLIDE IMPLEMENTATION PLAN (M1)

**Agent:** `teamwork_explorer_m1_3`  
**Date:** 2026-11-03  
**Status:** COMPLETE (Hard Handoff)  
**Target Recipient:** Orchestrator (`00c906d7-900c-42be-a553-3eacb15019c9`) & Milestone 2 Generator (`teamwork_generator_m2`)

---

## 1. OBSERVATION

1. **Giao diện người dùng trong `guide_screen.py`:**
   - Kích thước cửa sổ: `GUIDE_W = 1280` px (dòng 18), `CAM_H = 400` px (dòng 19), `PANEL_H = 400` px (dòng 20), tổng kích thước: $1280 \times 800$ px.
   - Hàm chính: `build_guide_screen(view_left, view_right, info, titles=...)` (dòng 403–410).
   - Bảng màu BGR sang RGB Hex (dòng 27–37):
     - `BG = (30, 27, 25)` $\to$ `#191B1E`
     - `CARD = (46, 42, 39)` $\to$ `#272A2E`
     - `CARD_EDGE = (82, 76, 70)` $\to$ `#464C52`
     - `WHITE = (245, 245, 245)` $\to$ `#F5F5F5`
     - `MUTED = (165, 160, 155)` $\to$ `#9BA0A5`
     - `AMBER = (40, 185, 255)` $\to$ `#FFB928`
     - `AMBER_DK = (28, 62, 98)` $\to$ `#623E1C`
     - `GREEN = (110, 215, 90)` $\to$ `#5AD76E`
     - `GREEN_DK = (50, 88, 42)` $\to$ `#2A5832`
     - `RED = (85, 85, 245)` $\to$ `#F55555`
     - `DARK_TXT = (30, 27, 25)` $\to$ `#191B1E`
   - Kiểu dáng `keycap()`: ô vuông bo góc $44 \times 44$ px, bán kính $R = 9$, đổ bóng màu tối dời xuống 3 px, nền cam `AMBER` `#FFB928`, chữ in hoa `DARK_TXT` `#191B1E` (dòng 155–159).
   - Thứ tự an toàn 4 khớp: `ROW_ORDER = (0, 3, 1, 2)` tương ứng Đế → Kẹp → Vai → Khuỷu (dòng 63).

2. **Kiểm thử thực thi trong `test_ik.py`:**
   - Lệnh chạy: `$env:PYTHONUTF8="1"; python test_ik.py`
   - Kết quả: `exit code 0`, 10/10 bài test PASS thành công:
     - `test_fk_ik_grid`: `✅ [PASS] Đã kiểm thử 455 điểm 3D trong tầm với: sai số FK(IK(p)) tối đa = 0.000000 mm (< 0.1 mm)`
     - `test_key_hints`: `✅ [PASS] Kiểm thử gợi ý bấm phím (WASD + IK + JL) với STEP = 5° chính xác tuyệt đối!`
     - `test_table_robot_mapping`: `✅ [PASS] Ánh xạ tờ A4 <-> hệ robot đúng cho cả hai hướng đặt robot (up / down)`
     - `test_board_silence_detection`: `✅ [PASS] Phát hiện board không nhận lệnh USB (firmware cũ)`
     - `test_find_bluetooth_port`: `✅ [PASS] Tìm cổng Bluetooth của HC-05`
     - `test_send_key_over_bluetooth`: `✅ [PASS] Gửi lệnh qua Bluetooth HC-05, tự quay về USB khi BT đứt`
     - `test_s1_ignores_gripper_marker`: `✅ [PASS] S1 chỉ tính mã của vật (ID 10-29), kẹp rỗng nâng lên không bị báo là đã gắp`
     - `test_grasp_locks_target_and_logs_align_error`: `✅ [PASS] Khóa vật lúc đóng kẹp cho bước nâng + kiểm tra, log CSV ghi đúng sai số căn đầu kẹp`
     - `test_normalize_phone_url`: `✅ [PASS] Chuẩn hóa địa chỉ IP Webcam của điện thoại`
     - `test_find_cameras_macos`: `✅ [PASS] Nhận camera MacBook và iPhone theo tên trên macOS`
   - Hàm `fake_assist()` (dòng 190–218): Cho phép khởi tạo `GraspAssist4DOF` với link giả lập `FakeLink` không mở cổng Serial thật, kết hợp ảnh `aruco_A4_grid.png` để sinh frame giao diện chuẩn `slides/assets/guide_screen_sample.png` trong Milestone 2 mà không cần AI image.

3. **Hiện trạng tệp nhật ký thực nghiệm `logs/attempts.csv`:**
   - Đã dùng lệnh `find_by_name` tìm kiếm toàn bộ workspace: Tệp `logs/attempts.csv` và thư mục `logs/` chưa tồn tại trong workspace.
   - Do đó, số liệu gắp thực tế trên các slide liên quan được giữ nguyên ở dạng placeholder `[...]` đúng yêu cầu bảo toàn tính toàn vẹn của R1 và R4.

---

## 2. LOGIC CHAIN

1. *Từ Quan sát 1 (Bố cục giao diện & bảng màu BGR $\to$ RGB Hex):*
   - Cửa sổ "HƯỚNG DẪN GẮP" có tỉ lệ $1280 \times 800$, rất tương thích với thiết kế slide 16:9 ($13.333 \times 7.5$ inch) trong PowerPoint.
   - Toàn bộ slide trong Milestone 2 sẽ áp dụng chuẩn màu tối của `guide_screen.py`: Nền `#191B1E`, thẻ `#272A2E`, viền `#464C52`, chữ chính `#F5F5F5`, nhấn cam `#FFB928`.
   - Các phím bấm được trực quan hóa bằng ô "Keycap" màu cam chữ đen, mô phỏng chính xác hàm `keycap()`.

2. *Từ Quan sát 2 (Kết quả `test_ik.py` & cơ chế `fake_assist()`):*
   - Độ chính xác động học ngược đạt mức lý tưởng ($0.000000\text{ mm}$ sai số trên 455 điểm), là bằng chứng vững chắc nhất để đưa vào Slide 13 (Kiểm thử).
   - Cơ chế `fake_assist()` kết hợp `aruco_A4_grid.png` có sẵn trong workspace cung cấp giải pháp sinh ảnh giao diện thực tế 100% bằng code Python thuần túy, hoàn toàn không vi phạm lệnh cấm ảnh AI.

3. *Từ Quan sát 3 (Trạng thái file `logs/attempts.csv`):*
   - Vì chưa có file log thực nghiệm trên phần cứng thật trong workspace, việc tự ước lượng số liệu là vi phạm điều kiện nghiêm ngặt "Không bịa đặt số liệu".
   - Do đó, việc duy trì placeholder `[...]` cho tỉ lệ thành công thực tế, số lần gắp, thông tin thành viên, giáo viên hướng dẫn, loại bo mạch Arduino là logic duy nhất bảo đảm đạt Acceptance Criteria.

---

## 3. CAVEATS

- **Môi trường hiển thị tiếng Việt trên terminal Windows:** Khi chạy script kiểm thử Python có chứa emoji hoặc ký tự Unicode trên Windows PowerShell, cần thiết lập `$env:PYTHONUTF8="1"` hoặc `PYTHONIOENCODING=utf-8` để tránh lỗi `UnicodeEncodeError: 'charmap'`.
- **Mã nguồn không bị chỉnh sửa:** Không có bất kỳ tệp mã nguồn nào ngoài thư mục `.agents/teamwork/` bị thay đổi.
- **Thực nghiệm phần cứng:** Nhóm sinh viên cần tự chạy thực tế với cánh tay robot thật để có file `logs/attempts.csv` hoàn chỉnh trước khi điền số liệu vào các vị trí `[...]`.

---

## 4. CONCLUSION

1. Đã hoàn thành toàn diện điều tra giao diện `guide_screen.py`, hệ màu 11 hằng số chuẩn RGB Hex, phong cách ô phím keycap, và bảng ánh xạ phím tắt toàn hệ thống.
2. Đã kiểm thử thành công bộ test `test_ik.py` với 10/10 bài test đạt, xác nhận công thức động học ngược giải tích đạt sai số $0.000000\text{ mm}$ trên 455 điểm.
3. Đã tổng hợp Kế hoạch triển khai 15 slide hoàn chỉnh, chi tiết từng slide từ 1 đến 15 trong `report.md`, đáp ứng trọn vẹn:
   - Tiêu đề & 3–6 ý chính súc tích.
   - Đặc tả hình khối sơ đồ PowerPoint native & tài sản ảnh thật từ code.
   - Speaker notes tiếng Việt phong cách thuyết trình thực tế (3–5 câu/slide).
   - Trích dẫn chính xác 100% nguồn hằng số, công thức, file code.
   - Thống kê toàn bộ placeholder `[...]` và hướng dẫn nhóm sinh viên cập nhật.
4. Sẵn sàng bàn giao tài liệu cho Milestone 2 để viết mã `slides/build_slides.py`.

---

## 5. VERIFICATION METHOD

1. **Xác minh kết quả kiểm thử:**
   Chạy lệnh sau trong PowerShell để kiểm tra 10 bài test tự động:
   ```powershell
   $env:PYTHONUTF8="1"; python test_ik.py
   ```
   *Điều kiện hợp lệ:* Toàn bộ 10 test đều in `✅ [PASS]` và kết thúc với `exit code 0`.

2. **Xác minh bảng màu và quy chuẩn UI:**
   Mở tệp `guide_screen.py` và đối chiếu các hằng số từ dòng 27 đến 37 với Bảng quy đổi màu trong `report.md`.

3. **Xác minh nội dung kế hoạch 15 slide:**
   Xem xét tệp `e:\03_Development_Projects\project\Project_IoT\.agents\teamwork\teamwork_explorer_m1_3\report.md` tại Mục 4, kiểm tra đủ 15 slide không thiếu bất kỳ slide nào, mỗi slide có đủ speaker notes và nguồn dẫn chứng code.

---
*Báo cáo Handoff được lập bởi teamwork_explorer_m1_3.*
