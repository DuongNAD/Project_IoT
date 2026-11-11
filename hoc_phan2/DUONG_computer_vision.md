# Dương · Computer vision

**Việc của bạn:** từ ảnh hai camera ra **vị trí vật trên tờ A4, tính bằng cm**. Bạn không cần biết servo quay bao nhiêu độ: đó là việc của `control.py`.

Đọc [README.md](README.md) bước 0 (phần chung) trước.

## Slide bạn nói

| Bộ slide | Slide | Nội dung |
|---|---|---|
| `slides/Phan2_LuongDuLieu_Code.pptx` (Canva) | 1 | mở phần 2, giới thiệu hai người |
| | 2 | sơ đồ luồng dữ liệu |
| | 3 | vòng lặp mỗi khung hình · `main.py` |
| | 4 | tìm camera theo tên · `cameras.py` |
| | 5 | hệ tọa độ từ tờ A4 · `vision.py` |
| | 6-7 | nhận diện vật: hình 3 bước, rồi code `vision.py` |
| `slides/Project_IoT_ThuyetTrinh.pptx` (bản đầy đủ 25 slide) | 11, 12, 13 | mở phần 02, hệ tọa độ A4, nhận diện vật |

## Lộ trình đọc (theo thứ tự)

Mỗi bước: mở đúng dòng, đọc, rồi tự trả lời câu hỏi ở cột cuối **không nhìn code**.

### Bước 1 · Vòng lặp chính: dữ liệu đi đâu

| Đọc | Ý chính | Tự hỏi |
|---|---|---|
| `main.py:65-83` (`App.__init__`) | tạo 2 `Camera`, 1 `Vision`, `Control`, `Success` | Cam TRÊN và cam NGANG được tạo ở dòng nào? |
| `main.py:86-99` (`_frame`) | chỉ xử lý lại khi `frame_id` đổi (có khung mới); mất tín hiệu thì hiện "Dang cho tin hieu" và **xóa danh sách vật cũ** | Vì sao cần `self.cache`? (vòng lặp chạy nhanh hơn camera; không cache thì một ảnh bị dò ArUco nhiều lần) |
| `main.py:110-122` (`render`) | `vision.objects` → `control.update` → `success.update` → `build_screen` | Kể lại 5 bước được đánh số trên slide 3 |

### Bước 2 · Tìm camera: cam nào là cam nào

| Đọc | Ý chính | Tự hỏi |
|---|---|---|
| `cameras.py:1-7`, `19-23` | cam TRÊN = OBSBOT, cam NGANG = camera laptop; tìm theo **tên** chứ không theo chỉ số | Từ khóa nào nhận ra webcam laptop Windows? (`integrated`) |
| `cameras.py:26-37` (`list_camera_names`) | Windows: thứ tự DirectShow qua `pygrabber`. macOS: `system_profiler` rồi **sắp theo uniqueID** như OpenCV | Vì sao không dùng chỉ số cố định 0 và 1? |
| `cameras.py:40-46` (`find_camera`) | trả về chỉ số camera đầu tiên có tên khớp, bỏ camera ảo (`virtual`, `desk view`) | Không thấy camera thì trả về gì? (`None`) |
| `cameras.py:49-100` (`Camera`, `_open`, `_read`, `_loop`) | mỗi camera đọc trên **một luồng riêng**; mỗi khung mới tăng `frame_id`; quá 4 giây không có khung thì mở lại; nguồn là ảnh `.png/.jpg` thì lặp mãi một ảnh (dùng để chạy thử) | Vì sao đọc trên luồng riêng? (vòng lặp chính luôn lấy được khung mới nhất, không chờ camera) |
| `cameras.py:102-109` (`stalled`, `get_raw_frame`) | khung cũ hơn 4 giây coi như không có | Rút cáp thì màn hình hiện gì? |

### Bước 3 · Hệ tọa độ từ tờ A4 (phần quan trọng nhất)

| Đọc | Ý chính | Tự hỏi |
|---|---|---|
| `vision.py:1-23` | tờ A4 ngang 29,7 × 21 cm; mã ArUco `DICT_4X4_50` cạnh 2,8 cm cách mép 0,25 cm; gốc tọa độ ở góc ngoài mã ID 0, X chạy ID 0 → 1, Y chạy ID 0 → 3 | Vẽ tờ giấy, đánh dấu 4 mã và hai trục |
| `vision.py:26-31` (`marker_corners_cm`) | tọa độ **thật** (cm) bốn góc của mỗi mã | Mã ID 1 nằm ở góc nào? Tính `x` của nó |
| `vision.py:45-62` (`Sheet.update`) | dò mã → **nhớ vị trí mã** (`self.markers.update`) → có ≥ 2 mã thì `findHomography` (pixel → cm) và ma trận nghịch đảo (cm → pixel) | Vì sao 2 mã là đủ? (homography cần ≥ 4 cặp điểm; mỗi mã 4 góc, 2 mã = 8). Cánh tay che mã thì sao? |
| `vision.py:34-39` (`px_to_cm`, `cm_to_px`) | đổi một điểm qua lại bằng homography | |
| `generate_aruco_a4.py` (29 dòng) | tạo tờ in 300 DPI từ **cùng hằng số** của `vision.py` | Vì sao phải in đúng 100%? (đo cạnh mã phải đúng 2,8 cm) |

Kiến thức nền cần nắm (ngoài code): **homography** là ma trận 3 × 3 đổi điểm trên một mặt phẳng nhìn từ góc này sang mặt phẳng khác. Ở đây: mặt phẳng ảnh camera (pixel) ↔ mặt phẳng tờ giấy (cm).

### Bước 4 · Nhận diện vật

`vision.py:68-95` (`find_objects`), đọc theo 4 số trên slide 7:

| Số | Dòng | Làm gì |
|---|---|---|
| 1 | `vision.py:70-71` | `warpPerspective` dựng **ảnh phẳng** của tờ A4, 1 cm = 8 pixel, nên mọi phép đo sau đó tính thẳng bằng cm |
| 2 | `vision.py:72-75` | HSV, giữ điểm **độ bão hòa ≥ 90, độ sáng ≥ 60** (bỏ giấy trắng, bóng xám); mở ảnh để bỏ nhiễu và dây mảnh; đánh dấu phần đen của cánh tay (nới ~1 cm) |
| 3 | `vision.py:81-89` | lọc từng khối: < 1,5 cm² là nhiễu; > 50 cm² là bàn tay; cách mép giấy < 1 cm là vật thò từ ngoài vào; > 30% dính phần đen là bộ phận robot |
| 4 | `vision.py:77-79`, `90-93` | **bù thị sai**: vị trí thật = n + (vị trí đo − n) × (46 − 5) / 46, với n là điểm cam nhìn thẳng xuống (tâm ảnh) |

Tự hỏi: vì sao nắp cốc nhìn từ trên bị lệch ra xa tâm ảnh? Vật màu trắng thì sao? (chưa nhận được: hạn chế) Vì sao bỏ YOLO? (bản trước hay nhận nhầm bộ phận robot; nhóm bỏ cho mã đơn giản)

### Bước 5 · Vẽ lên ảnh (đọc lướt)

| Đọc | Ý chính |
|---|---|
| `vision.py:130-163` (`Vision.process_frame`) | ghép bước 3 + 4 cho từng camera; chỉ cam TRÊN mới tìm vật; vẽ mã, lưới 5 cm, vòng xanh quanh vật, dòng `Luoi A4: thay n/4 ma ArUco` hoặc `KHONG THAY TO A4` |
| `vision.py:112-127` | lưới 5 cm (nhìn là biết lưới có bám tờ giấy không), dấu `DICH` và `KEP` |
| `control.py:491-502` (`lock_target`, phím `R`) | ô "Chọn mục tiêu" trên slide 13: bấm `R` thì vật gần đế nhất trong ảnh lúc đó thành đích, góc cần tới tính **một lần**, không theo camera nữa; vật bị dời thì bấm `R` lại |

## Test của phần bạn

| Test | Kiểm gì |
|---|---|
| `tests/test_vision.py` (8 test) | góc mã đúng tờ in; homography cho cả 2 camera; nhớ mã bị che; tìm đúng vị trí đĩa màu; bù thị sai kéo vật về tâm ảnh; bỏ dây điện, bộ phận robot, bàn tay |
| `tests/test_cameras.py` (5 test) | tìm theo tên, bỏ camera ảo; sắp theo uniqueID trên macOS; thứ tự DirectShow trên Windows; ảnh tĩnh lặp lại; mất camera thì hiện ảnh chờ |
| `tests/synth.py` (đọc lướt) | camera **giả lập** chiếu tờ A4 vào khung hình với thông số biết trước, nên có đáp án chính xác |

```bash
uv run pytest tests/test_vision.py tests/test_cameras.py -v
```

Bài tập bù thị sai (làm bằng tay trước, rồi mới xem đáp án): cam nhìn thẳng xuống điểm n = (14,85; 10,5) cm, nắp cốc đo được ở
(24,85; 10,5) cm. Vị trí thật của cốc? Cốc bị kéo vào phía tâm ảnh bao nhiêu cm?

<details><summary>Đáp án</summary>

x = 14,85 + (24,85 − 14,85) × 41 / 46 ≈ 23,76 cm, y giữ 10,5 cm: kéo vào ≈ 1,1 cm (khớp câu "lệch ~1 cm" ở `vision.py:23`).
Test kiểm đúng công thức này: `tests/test_vision.py:64-71`.
</details>

## Số liệu phải nhớ

Nguồn: `slides/05_SO_LIEU_VA_NGUON.md` mục 2 và 10.

| Số | Ý nghĩa |
|---|---|
| 29,7 × 21,0 cm | tờ A4 ngang |
| 2,8 cm · 0,25 cm | cạnh mã ArUco · khoảng cách tới mép giấy |
| ≥ 2 mã | đủ tính homography (8 cặp điểm) |
| 8 pixel / cm | độ phân giải ảnh phẳng của tờ giấy |
| 90 · 60 | ngưỡng độ bão hòa · độ sáng để coi là "có màu" |
| 1,5 cm² · 50 cm² · 1 cm · 30% | bốn ngưỡng lọc vật |
| 46 cm · 5 cm | cam TRÊN treo cao (ước lượng từ ảnh, không đo bằng thước) · cốc cao |
| 1,2 cm → 0,2 cm | lệch giữa hai camera trước / sau bù thị sai, **ở một vị trí cốc** đo ngày 02/11 |
| 4 giây | mất khung quá lâu thì mở lại camera |

## Không nói quá

- Không nói "tìm vật bằng YOLO": đã bỏ ngày 10/11, giờ chỉ tách màu.
- 1,2 → 0,2 cm là **một phép đo ở một vị trí**, không phải sai số trung bình.
- 46 cm là **ước lượng** từ ảnh, nói "khoảng 46 cm".
- Mọi ảnh và số đo trong slide làm trên **macOS**.
