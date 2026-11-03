# 02 · Ảnh thật

Ảnh thật đã được chuẩn bị sẵn trong `assets/real/` (40 ảnh, khoảng 14 MB). Mô tả, alt text và slide dùng của từng ảnh nằm trong
`assets/manifest.json`; ảnh xem nhanh toàn bộ: `assets/real/_preview.jpg`. Tạo lại bằng hai lệnh (chạy theo thứ tự, từ thư mục dự án):

```bash
python3 -I slides/tools/prepare_real_assets.py            # ảnh phần cứng, buổi 02/11, ảnh chụp màn hình bản cũ (làm mờ màn hình laptop)
.venv/bin/python -B slides/tools/make_screen_images.py    # ảnh giao diện MỚI: chạy chương trình trên ảnh camera đã lưu (cần captures/ và .venv)
```

**Nguyên tắc:** ảnh thật là bằng chứng. Dùng đúng file đã chuẩn bị (đã bỏ chú thích dựng sẵn và làm mờ màn hình laptop), không chọn thêm
khung "đẹp hơn" từ nguồn khác, không dùng ảnh AI ở chỗ cần bằng chứng. **Ảnh giao diện mới là chương trình chạy trên ảnh camera thật đã lưu với cánh tay mô phỏng: không phải lần chạy trực tiếp**, và chú thích trên slide phải nói vậy.

## 1. Ảnh có sẵn

### Buổi kẹp bằng bàn phím 02/11/2026 20:27–20:36 (cam NGANG = MacBook | cam TRÊN = OBSBOT), 1920×1080, đã làm mờ màn hình

| File (`_side` = cam NGANG, `_top` = cam TRÊN) | Thời điểm | Nội dung | Dùng ở slide |
|---|---|---|---|
| `demo_06_grip_*` | 20:32:52 | cốc đỏ nằm giữa hai ngón kẹp | **1** (bìa), **10** |
| `demo_07_carry_*` | 20:33:02 | cốc đang được kẹp và chuyển sang trái | **10** |
| `demo_08_place_*` | 20:33:12 | cốc đã đặt xuống bên trái, cánh tay rút về | **10** |
| `demo_05_knocked_*` | 20:32:42 | cốc đổ nằm nghiêng trước hai ngón kẹp | **21** (phụ lục G) |
| `demo_15_tilted_*` | 20:34:22 | lần kẹp thứ hai: cốc nghiêng trong tay kẹp | **21** (phụ lục G) |
| `demo_00_before_*` | 20:27 | trước khi gắp: cốc đứng giữa giấy, cánh tay giơ cao | dự phòng (là khung đầu vào của `ui_screen_before`) |
| `demo_02_approach_*` | 20:32:12 | tiếp cận: kẹp mở, đưa tới sát cốc | dự phòng |
| `demo_16_regrip_*` | 20:34:32 | lần kẹp thứ hai: cốc đứng lại giữa hai ngón kẹp | dự phòng |

Mỗi cặp khung được cắt cách nhau khoảng 10 giây (ba khung 20:32:52, 20:33:02, 20:33:12 cách nhau đúng 10 giây). **Chú thích bắt buộc** khi dùng: giờ của khung và câu "người bấm phím, không tự động". Buổi này dùng màn hình bản trước khi đơn giản hóa; ảnh không chứa giao diện đó.

### Phần cứng (ảnh 18:xx, tư thế gốc 90/90/90/95)

| File | Kích thước | Nội dung | Slide |
|---|---|---|---|
| `hw_overview_top.jpg` | 1920×1080 | toàn cảnh cam TRÊN: mạch bên trái, cánh tay, tờ A4 4 mã ArUco, cốc đỏ | 4 |
| `hw_overview_side.jpg` | 1920×1080 | toàn cảnh cam NGANG, bốn mã ArUco rõ nét, cốc số 3, bóng cánh tay | 4 |
| `hw_electronics.jpg` | 800×678 | cận cảnh Arduino Uno, PCA9685, nguồn tổ ong, dây servo | 4 (ảnh nhỏ) |
| `hw_arm_gripper.jpg` | 960×578 | cánh tay 4 bậc tự do và tay kẹp, nhìn từ trên xuống | 4 (ảnh nhỏ) |
| `hw_gripper_95_vs_125.jpg` | 1235×734 | tay kẹp 95° (mở hết) và 125°, cạnh nhau | 21 (phụ lục G) |
| `hw_gripper_95.jpg`, `hw_gripper_125.jpg` | ≈ 615×734 | hai nửa của ảnh trên, tách rời | dự phòng |

### Ảnh giao diện MỚI (chạy chương trình trên ảnh camera thật đã lưu, cánh tay mô phỏng): `tools/make_screen_images.py`

| File | Nội dung | Slide | Chú thích bắt buộc |
|---|---|---|---|
| `ui_screen_before.png` (1280×728) | màn hình hai phần lúc còn phải bấm: khung camera thật 20:27 (cánh tay chưa tới cốc), servo mô phỏng ở Home 90/90/90/95. Cốc đo được ở **(16,5; 13,8) cm**; phần 1: `BAM S x 15 · HA XUONG 30 DO`, `Con 18 lan bam` (đế 90 → 88° đã `DA DUNG`, khuỷu `K x3`); phần 2: `CHUA XONG` | **8** | "chạy trên ảnh camera thật đã lưu; cánh tay mô phỏng (chân trang: `USB Arduino: MO PHONG`)" |
| `ui_screen_done.png` | cùng chương trình sau khi **mô phỏng** bấm 21 phím theo lệnh và giữ góc > 1 s: `KHONG CAN BAM THEM`, `XONG!`, ba dấu tích, `Thanh cong: 1 lan` (khung camera thật 20:32:52, hai ngón kẹp ôm cốc). Hai ngón kẹp che cốc nên cốc đo lệch 1,5 cm so với ảnh trước (16,7; 15,3): **không ghép số của hai ảnh thành một câu chuyện** | **9** | "Mô phỏng: bấm đủ phím theo lệnh thì phần 2 báo XONG! và đếm 1 lần (ảnh camera thật đã lưu)" |
| `sw_annot_top.jpg`, `sw_annot_side.jpg` (1920×1080) | khung camera do chương trình vẽ (ảnh 20:27): viền tờ giấy, lưới 5 cm, bốn mã ArUco, vòng xanh quanh cốc ghi `Vat mau X=16.5 Y=13.8cm`. Cố ý **không** vẽ vòng `DICH` và dấu `KEP` (dấu `KEP` ở Home nằm cạnh cốc, dễ hiểu nhầm) | **5** | "chương trình vẽ lưới lên khung hình camera thật đã lưu" |
| `calib_before_after_side.jpg` (1400×788) | khung cam NGANG lúc ôm cốc 21:03:35 (servo 75/85/50, kẹp 150): dấu cam `MAC DINH` (mô hình mặc định) cách cốc ≈ **5,3 cm**, dấu xanh `SAU HIEU CHINH` ≈ **0,95 cm** (cốc đo từ cam ngang, ± 1 cm); hai ngón kẹp thấy rõ | **11** | "khung ôm cốc 21:03; lần ôm này nằm trong 10 mẫu khớp nên đây là minh họa, không phải kiểm độc lập" |
| `calib_before_after_top.jpg` (1200×675) | cùng khung 21:03:35 nhìn từ cam TRÊN; yếu hơn vì thân kẹp che cốc | dự phòng | như trên |

Vì sao hai màn hình dùng khung 20:xx chứ không phải 21:xx: chín cặp ảnh 21:03–21:16 trong `captures/` đều là khung **đang ôm cốc**, nên chương trình không thấy cốc (`CHUA THAY VAT`) và cam TRÊN chỉ thấy 3 mã. Khung 21:03:35 chỉ dùng cho ảnh hiệu chỉnh vì là khung duy nhất có góc servo được ghi lại.

Hai điều cần biết khi đọc các ảnh này (script đã kiểm và dừng nếu sai): ảnh camera chụp lúc tờ giấy còn **hướng ban đầu**, còn `calibration.json` ghi đế theo tờ giấy đã xoay 180°. Dùng nguyên file thì dấu `KEP` lệch 8,6 cm; script xoay đế về (15,87; −10,67; 87,6°)
(`photo_frame_config`) rồi tự kiểm: dấu `KEP` đã hiệu chỉnh phải cách cốc đo từ chính ảnh không quá 2 cm, không thì dừng thay vì vẽ ảnh sai. Script cũng kiểm `calibration.json` không bị ghi (băm trước và sau khi chạy); chạy hai lần cho ảnh giống hệt nhau.

### Ảnh chụp màn hình BẢN CŨ (trước khi đơn giản hóa), chỉ dùng làm bằng chứng lịch sử

| File | Kích thước | Nội dung | Slide |
|---|---|---|---|
| `ui_guide_cameras.png` | 2560×765 | hai khung camera của cửa sổ cũ (02/11 20:32): cốc ở (16,5; 13,9) cm, khung nhận diện **kể cả nhãn YOLO nhận nhầm** (`bottle`, `airplane`, `frisbee`) | **6** |
| `ui_fk_vs_real.png` | 940×390 | khung cam TRÊN: dấu đầu kẹp theo mô hình (`Dau kep FK`) lệch so với hai ngón kẹp thật | dự phòng của slide 11 (chỉ dùng nếu `calib_before_after_side.jpg` thiếu; ghi "ảnh chụp màn hình bản trước") |
| `repo_aruco_a4_clean.png`, `repo_aruco_a4_grid.png` | 3508×2480 | tờ A4 in 4 mã ArUco (bản sạch và bản có lưới) | tùy chọn |

`ui_guide_cameras.png` có nhãn YOLO nhận nhầm: đó là bằng chứng trung thực cho lý do YOLO bị tắt mặc định (slide 6), **không** cắt bỏ. Chữ trên mọi ảnh chụp màn hình **không dấu** vì OpenCV `putText` không vẽ được dấu: giữ nguyên, nói rõ khi thuyết trình.

### Còn trong thư mục nhưng KHÔNG dùng (giao diện cũ đã bỏ hoặc nhãn đã lỗi thời)

| File | Vì sao không dùng |
|---|---|
| `ui_guide_live.png`, `ui_guide_steps.png`, `ui_guide_relaxed.png` | cửa sổ HƯỚNG DẪN GẮP (thanh 5 bước, thẻ servo, `Thanh cong: 0 / That bai: 0`): giao diện đã bỏ |
| `ui_status_bar.png` | `Tu dong (P): TAT`, `Sai so dau kep: 56 mm`, hàng phím cũ: giao diện đã bỏ (số 56 mm vẫn đúng, chỉ dùng được bằng lời) |
| `ui_hud_grip_warning.png` | cảnh báo `GIU 31s` của giao diện cũ: màn hình mới không có |
| `sw_grid_top.jpg`, `sw_grid_side.jpg` | lưới của giao diện cũ; ảnh cam NGANG còn vạch `S1 (+20mm)` đã bỏ. Thay bằng `sw_annot_*` |

## 2. Ảnh KHÔNG dùng (và lý do)

| Nguồn | Lý do |
|---|---|
| Drive `anh_slide/05_tiep_can_*`, `06_diem_gan_nhat_*`, `09_cac_buoc_thu_gap.jpg` | lần thử 18:10–18:28 dừng **trước khi kẹp**, chú thích dựng sẵn ghi "thiếu ~1,5–2 cm"; kết luận đó đã bị đính chính lúc 20:25. Thay bằng khung `demo_*` |
| Drive `anh_slide/08_giao_dien_2_camera.png`, `08_giao_dien_huong_dan.png` | giao diện cũ (trước 20:00), đang ở chế độ MÔ PHỎNG |
| Drive `anh_slide/10_trang_thai_luc_18h41_cam_tren.jpg` | ảnh trạng thái an toàn, không phục vụ slide nào |
| Drive `video/1…4_*.mp4` (3 clip 104 giây và bản 21 phút) | thuộc buổi 18:10–18:28, **chưa kẹp được**; không dùng làm bằng chứng kết quả |
| Khung `t25`–`t60` của buổi 20:27–20:45 | cánh tay đứng yên; từ khoảng 20:40 camera TRÊN bị xoay nên lưới ArUco không còn đúng |
| Khung có tay người (`t12`, `t17`–`t21`, `t44`–`t48`) | tay người và điện thoại trong khung, không cần |
| `captures/*.jpg` (18 ảnh gốc 21:03–21:16, chưa làm mờ) | chỉ là đầu vào của `make_screen_images.py`; chứa màn hình laptop ở mép khung, **không** đưa thẳng lên slide |

## 3. Riêng tư đã xử lý

- Màn hình laptop lọt vào mép khung (trái ở cam NGANG, dưới đáy ở cam TRÊN) và điện thoại đặt góc trên: **làm mờ** trong bản chuẩn bị, kể cả trong các ảnh giao diện mới (khung ảnh gốc `captures/` còn chữ đọc được). Ảnh gốc không bị sửa.
- Nhãn do phần mềm vẽ đè lên vùng mờ (VD `DICH`, `KEP`, tiêu đề `CAM NGANG: anh da luu …`) được giữ rõ.
- Khi tạo ảnh giao diện mới, phát hiện và **sửa thêm** ba chỗ lộ trong ảnh cũ: điện thoại còn sáng chữ trong khung NGANG 20:27, mép màn hình điện thoại lộ chữ nghiêng ở khung TRÊN, và màn hình laptop trong `ui_guide_cameras.png` (slide 6). Các ảnh `demo_*` và `ui_guide_cameras.png` đã được dựng lại.
- Không có khuôn mặt trong ảnh nào. Ảnh chụp màn hình bản cũ giữ nguyên tên cổng `/dev/cu.usbmodemFX2348N1` (tên thiết bị, không nhạy cảm).
- `slides/.gitignore` loại `assets/real/` khỏi git: repo GitHub của bạn công khai và `.gitignore` gốc đã nhắc tránh đẩy ảnh cá nhân (`captures/`).

## 4. Nguồn gốc và chỗ lưu bền

| Nhóm | Nguồn gốc | Lưu ý |
|---|---|---|
| Phần cứng, lưới ArUco cũ | Google Drive: `Project_IoT_Thu_gap_2026-11-02/anh_slide/` | bền (đồng bộ Drive) |
| Buổi kẹp 20:27–20:45 | thư mục tạm của phiên Claude: `/private/tmp/claude-501/…/2b984ba7-…/scratchpad/run4/` (192 file: 60 cặp khung cam NGANG/TRÊN mỗi 10 giây, 60 thanh HUD, 3 video) | **tạm thời, có thể bị dọn**; các khung cần dùng đã chép vào `assets/real/`. Muốn giữ cả thư mục: chép sang Drive |
| Giao diện bản cũ | `…/2b984ba7-…/scratchpad/guide_win.png` (20:32:05) | đã chép vào `assets/real/` |
| Ảnh giao diện mới | tạo từ `demo_00_before_*`, `demo_06_grip_*` (trong `assets/real/`) và ảnh gốc `captures/20261102_210335_*` | `captures/` nằm trong `.gitignore`; **giữ thư mục này** nếu muốn tạo lại ảnh |

## 5. Video

- Ba video lớn trong `run4/` (`video_ghep_raw.mp4` 301 MB, `video_tren_raw.mp4` 226 MB, `video_ngang_raw.mp4` 266 MB lúc 20:45:58) lúc kiểm tra **đang được ghi dở**:
  `ffprobe` báo `moov atom not found`. Mình không đụng tới. Khi `ffprobe` đọc được, cắt đoạn kẹp bằng lệnh sau
  (giả định video bắt đầu khoảng 20:27:38 theo khung `anh_00_batdau`; **xem thử và chỉnh ±10 giây**):

```bash
mkdir -p slides/assets/real/video
R=/private/tmp/claude-501/-Users-duongnad-Documents-project-Project-IoT/2b984ba7-f079-5e9a-b65f-9a90f8099ed3/scratchpad/run4
ffprobe -v error -show_entries format=duration -of csv=p=0 "$R/video_ghep_raw.mp4"      # phải in ra số giây, không báo lỗi
# kẹp, chuyển trái, đặt xuống: 20:32:45 → 20:33:20 (bắt đầu +5:07, dài 35 giây), không tiếng, nén nhẹ
ffmpeg -ss 00:05:07 -i "$R/video_ghep_raw.mp4" -t 00:00:35 -vf "scale=1280:-2" -c:v libx264 -crf 24 -preset medium -an -movflags +faststart slides/assets/real/video/demo_gap.mp4
```

- Cách tốt hơn: **quay mới bằng điện thoại** (mục 6 A), tốt nhất khi chạy **bản mới với cánh tay thật**. Có `assets/real/video/demo_gap.mp4` thì Antigravity thêm video vào slide 10 (pptxgenjs `addMedia`, khung đầu là `demo_06_grip_side`); PDF xuất từ LibreOffice không phát video nên vẫn giữ hàng ảnh tĩnh.

## 6. Danh sách cần chụp / quay thêm (không bắt buộc, nâng chất lượng)

Chụp ngang, giữ máy chắc, ánh sáng đều, **tắt hoặc xoay màn hình laptop ra khỏi khung**.

| # | Cần | Chi tiết | Để dùng ở |
|---|---|---|---|
| **F** | **Màn hình bản mới lúc chạy TRỰC TIẾP với cánh tay thật** | chụp khoảnh khắc phần 2 ghi `XONG!` và `Thanh cong: 1 lan`; chân trang phải ghi `USB Arduino: DA KET NOI`. Đây là bằng chứng quan trọng nhất còn thiếu; có nó thì đổi các dòng "chưa" ở slide 9, 11, 13 (sửa `05` trước) | slide 8, 9, 13 |
| A | **Video 20–30 giây** bấm theo lệnh tới khi `XONG!` | 1080p, máy cố định, thấy cả cánh tay, cốc và màn hình chương trình ở một góc khung | slide 10 |
| B | Toàn cảnh bàn thí nghiệm | góc 3/4 từ trên cao, thấy cánh tay, tờ A4, hai camera, laptop | slide 4 (thay hoặc thêm) |
| C | Cận cảnh mạch | Arduino Uno + PCA9685 + dây gọn; **cắt nguồn** trước khi lại gần | slide 4 |
| D | Servo MG996R và tay kẹp mở / đóng | hai ảnh cùng góc | slide 4, 21 |
| E | Vị trí hai camera | OBSBOT treo phía trên và MacBook đặt thấp trước giấy | slide 3, 4 |
| G | Tay người đang bấm phím + màn hình | thể hiện "người trong vòng điều khiển" | slide 3 hoặc 8 |
| H | Tay kẹp có dán ma sát, kẹp cốc | nếu thử cách chữa ở slide 21 | slide 9, 21 |
| I | Ảnh nhóm (tùy chọn) | cho bìa hoặc slide kết | slide 1, 14 |

Chép ảnh mới vào `slides/assets/real_new/` (đặt tên tùy ý, ghi chú trong tên nếu cần), rồi dùng **Prompt B2** trong `04_PROMPT_ANTIGRAVITY.md`:
Antigravity chép vào `assets/real/`, làm mờ màn hình, thêm vào manifest và đề xuất vị trí, **không** ghi đè ảnh đang dùng.
