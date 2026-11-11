# Học phần 2 · Computer vision & Hỗ trợ gắp

Thư mục này **chỉ chứa hướng dẫn đọc**, không chứa code. Mã nguồn vẫn ở chỗ cũ (thư mục gốc), vì `main.py` và các test import theo đường dẫn hiện tại.

| Người | Phụ trách | Đọc file |
|---|---|---|
| **Nguyễn Anh Dương** | Computer vision: luồng dữ liệu, tìm camera, hệ tọa độ từ tờ A4, nhận diện vật | [DUONG_computer_vision.md](DUONG_computer_vision.md) |
| **Phạm Trương Vũ** | Hỗ trợ gắp: điều kiện hoàn thành (`success.py`), màn hình (`screen.py`), kiểm thử, thử nghiệm, kết quả, hạn chế | [VU_ho_tro_gap.md](VU_ho_tro_gap.md) |

Phân công lấy từ bảng `TEAM` và slide "Thành viên và phân công" trong `slides/build_slides.py:52-57,440-478`.

## Bước 0 · Cả hai cùng đọc trước (phần chung)

Đọc theo thứ tự. Xong bước này thì mỗi người mới đọc file riêng của mình.

| # | Đọc | Để hiểu |
|---|---|---|
| 1 | `README.md` đầu trang + mục 3 "Code chia thế nào" | cả hệ thống làm gì; vì sao chia thành khối điều khiển và khối success |
| 2 | `main.py:110-122` (hàm `render`) | **mỗi khung hình chỉ có ba dòng**: `plan = control.update(...)` → `result = success.update(plan)` → `build_screen(...)` |
| 3 | `control.py:462-477` (lớp `Plan`) và `control.py:214-225` (lớp `Move`) | "hợp đồng" giữa hai khối: vision đưa vật cho control, control đưa `Plan` cho success. Chỉ cần đọc các trường, **không** cần hiểu IK |
| 4 | `slides/05_SO_LIEU_VA_NGUON.md` mục 14 "CẤM NÓI" | những câu không được nói khi thuyết trình (ví dụ "robot tự động gắp", "gắp thành công") |
| 4b | `README.md` mục 2, đoạn "Điều khiển từ xa" | buổi demo: Mac làm hết phần tính và cắm USB Arduino; máy Dell chỉ xem màn hình qua Wi-Fi và gửi phím qua Bluetooth HC-05; `R` bấm trên Mac |
| 5 | Lướt `slides/Phan2_LuongDuLieu_Code.pdf` (9 trang; ảnh từng trang ở `slides/preview_phan2/`) | 9 slide phần 2 đưa lên Canva: trang 1 mở phần, trang 2-7 của Dương, trang 8-9 của Vũ |

Sơ đồ phải nhớ (vẽ lại được bằng tay là hiểu):

```
camera TREN + NGANG ─► cameras.py ─► vision.py ─► danh sách vật (x, y cm)
                                                         │
                                     control.py (điều khiển) ─► Plan
                                                                  │
                                                 success.py (success) ─► Result
                                                                            │
                                                screen.py vẽ 2 camera + Plan + Result
     └──────────── Dương ────────────┘                     └──────── Vũ ────────┘
```

## Thứ tự trình bày phần 2

1. **Dương**: slide mở phần → sơ đồ luồng dữ liệu → vòng lặp `main.py` → tìm camera → hệ tọa độ A4 → nhận diện vật (hình rồi code).
2. **Vũ**: điều kiện hoàn thành (`success.py`) → màn hình (`screen.py`) → thử nghiệm trên cánh tay thật → kết quả → hạn chế và hướng phát triển.

Lời nói của từng slide nằm trong **ghi chú (notes)** của slide: mở `slides/Phan2_LuongDuLieu_Code.pptx` và `slides/Project_IoT_ThuyetTrinh.pptx`, bật chế độ xem Notes.

## Không cần đọc

Hai bạn **không** phải học các phần này (của người khác hoặc đã bỏ):

- `control.py` ngoài `Plan` / `Move` (IK, cổng USB): phần 3, code điều khiển.
- `calibration.py`, `arm_fit.py`, `robot_arm_4dof/`: phần 3.
- `slides/build_slides.py`, `slides/build_part2.py`, `slides/tools/`: chỉ cần khi sửa slide.

## Tự kiểm tra cả phần 2

```bash
uv sync
uv run pytest tests/test_vision.py tests/test_cameras.py tests/test_success.py tests/test_screen.py tests/test_end_to_end.py -v
```

Không test nào cần camera hay Arduino thật (`tests/conftest.py` chặn camera thật; cảnh giả lập trong `tests/synth.py` có đáp án chính xác).
