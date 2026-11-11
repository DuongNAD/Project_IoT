# Dương · Computer vision

**Việc của bạn:** từ ảnh hai camera ra **vị trí vật trên tờ A4, tính bằng cm**. Học khoảng **95 dòng** dưới đây (đúng code chiếu trên slide);
phần còn lại chỉ cần một câu. Đọc [README.md](README.md) phần "Cả hai phải thuộc" trước.

## Slide bạn nói

| Bộ slide | Slide | Nội dung |
|---|---|---|
| `slides/Phan2_LuongDuLieu_Code.pptx` (Canva) | 1 | mở phần 2, giới thiệu hai người |
| | 2 | sơ đồ luồng dữ liệu |
| | 3 | vòng lặp mỗi khung hình · `main.py` |
| | 4 | đọc camera trên luồng riêng · `cameras.py` |
| | 5 | hệ tọa độ từ tờ A4 · `vision.py` |
| | 6-7 | nhận diện vật: hình 3 bước, rồi code `vision.py` |
| `slides/Project_IoT_ThuyetTrinh.pptx` (bản đầy đủ 25 slide) | 11, 12, 13 | mở phần 02, hệ tọa độ A4, nhận diện vật (ô "Chọn mục tiêu": phím R) |

## Dòng code chính (học kỹ)

| Dòng | Ý chính | Tự hỏi |
|---|---|---|
| `main.py:60-71` (`_frame`) | chỉ xử lý lại khi camera có khung mới (`frame_id` đổi); mất tín hiệu thì hiện "Dang cho tin hieu" và xóa vật cũ | Vì sao cần `self.cache`? (vòng lặp chạy nhanh hơn camera) |
| `main.py:82-89` (`render`) | `vision.objects` → `control.update` → `success.update` → `build_screen` | Kể lại 5 số trên slide 3 |
| `cameras.py:35-44` (`_open`) | mở camera theo **chỉ số** (`--top`, `--side`); nguồn là ảnh `.png` thì lặp lại một ảnh để chạy thử | Camera nào là cam TRÊN? (số ghi ở `--top`) |
| `cameras.py:54-66` (`_loop`) | luồng riêng đọc liên tục, lưu khung mới nhất kèm `frame_id`; quá 4 giây không có khung thì mở lại | Vì sao đọc trên luồng riêng? |
| `vision.py:26-31` (`marker_corners_cm`) | tọa độ **thật** (cm) bốn góc mỗi mã: cạnh 2,8 cm, cách mép 0,25 cm | Mã ID 1 nằm ở góc nào? |
| `vision.py:45-62` (`Sheet`) | OpenCV dò mã → **nhớ mã bị che** → có ≥ 2 mã thì `findHomography` (pixel → cm) | Vì sao 2 mã là đủ? (8 góc, homography cần ≥ 4 cặp điểm) |
| `vision.py:68-95` (`find_objects`) | 4 bước: ảnh phẳng (`70-71`) → tách màu HSV (`72-75`) → lọc khối (`81-89`) → bù thị sai (`79, 92-93`) | Vật màu trắng thì sao? (chưa nhận được) |

## Phần còn lại: chỉ cần một câu

| Phần | Câu cần nói |
|---|---|
| Dò mã ArUco | Dùng hàm có sẵn của OpenCV (`cv2.aruco`), bộ mã có sẵn `DICT_4X4_50`; tờ in là `aruco_A4_clean.pdf`. |
| `vision.py:141-163` (`process_frame`) | Ghép hai bước trên cho từng camera, vẽ mã, lưới 5 cm, vòng xanh quanh vật. |
| `control.py:429-440` (`lock_target`, phím R) | Bấm R: vật gần đế nhất trong ảnh lúc đó thành đích, góc cần tới tính một lần. |
| `calibration.py` | Nạp `calibration.json`: vị trí đế (đo bằng thước), hai góc chuẩn vai / khuỷu, càng kẹp. |
| `share.py` | Mac chia sẻ ảnh màn hình qua Wi-Fi cho máy Dell, chỉ cho xem. |
| `main.py:99-113` (`handle_key`) | Phím di chuyển gửi xuống Arduino, `R` chụp đích, `U` dò lại mã, `Q` thoát. |

Kiến thức nền (ngoài code): **homography** là ma trận 3 × 3 đổi điểm trên một mặt phẳng nhìn từ góc này sang mặt phẳng khác. Ở đây: ảnh camera (pixel) ↔ tờ giấy (cm).

## Bài tập

Bài tập bù thị sai (làm bằng tay trước, rồi mới xem đáp án): cam nhìn thẳng xuống điểm n = (14,85; 10,5) cm, nắp cốc đo được ở
(24,85; 10,5) cm. Vị trí thật của cốc? Cốc bị kéo vào phía tâm ảnh bao nhiêu cm?

<details><summary>Đáp án</summary>

x = 14,85 + (24,85 − 14,85) × 41 / 46 ≈ 23,76 cm, y giữ 10,5 cm: kéo vào ≈ 1,1 cm (khớp câu "lệch ~1 cm" ở `vision.py:23`).
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
