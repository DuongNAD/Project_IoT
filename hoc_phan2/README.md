# Học phần 2 · Computer vision & Hỗ trợ gắp

Thư mục này **chỉ chứa hướng dẫn đọc**, không chứa code. Cách học: mỗi người chỉ học **dòng code chính** (đúng đoạn chiếu trên slide và vài hàm cốt lõi,
khoảng 100 dòng); mọi phần khác chỉ cần nói được **một câu** "nó làm gì". Thầy hỏi sâu vào phần một câu thì mở file ra chỉ đúng hàm.

| Người | Phụ trách | Đọc file |
|---|---|---|
| **Nguyễn Anh Dương** | Computer vision: camera, hệ tọa độ từ tờ A4, nhận diện vật, vòng lặp `main.py` | [DUONG_computer_vision.md](DUONG_computer_vision.md) |
| **Phạm Trương Vũ** | Hỗ trợ gắp: điều kiện hoàn thành (`success.py`), màn hình (`screen.py`), lệnh bấm phím, thử nghiệm, kết quả, hạn chế | [VU_ho_tro_gap.md](VU_ho_tro_gap.md) |

## Cả hai phải thuộc

| Dòng | Ý chính |
|---|---|
| `main.py:85-88` | mỗi khung hình chỉ có ba bước: `plan = control.update(...)` → `result = success.update(plan)` → `screen = build_screen(...)` |
| `success.py:11-12` | hai con số: lệch **≤ 2°** là tới, giữ **1 giây** thì đếm 1 lần |
| `control.py:403-417` | lớp `Plan`, "hợp đồng" giữa hai khối: chỉ cần biết tên các trường (`found`, `goal`, `moves`, `now`...) |

```
camera TREN + NGANG ─► cameras.py ─► vision.py ─► danh sách vật (x, y cm)
                                                         │  bấm R: chụp đích, tính góc một lần
                                     control.py (điều khiển) ─► Plan
                                                                  │
                                                 success.py (success) ─► Result
                                                                            │
                                                screen.py vẽ 2 camera + Plan + Result
     └──────────── Dương ────────────┘                     └──────── Vũ ────────┘
```

## Thứ tự trình bày phần 2

1. **Dương**: slide mở phần → sơ đồ luồng dữ liệu → vòng lặp `main.py` → đọc camera → hệ tọa độ A4 → nhận diện vật (hình rồi code).
2. **Vũ**: điều kiện hoàn thành (`success.py`) → màn hình (`screen.py`) → thử nghiệm trên cánh tay thật → kết quả → hạn chế và hướng phát triển.

Lời nói của từng slide nằm trong **ghi chú (notes)**: mở `slides/Phan2_LuongDuLieu_Code.pptx` và `slides/Project_IoT_ThuyetTrinh.pptx`, bật chế độ xem Notes.

## Chạy và kiểm tra bằng mắt

```bash
uv run python main.py --port /dev/cu.usbmodem1101    # Windows: --port COM3; không ghi --port thì cánh tay mô phỏng
```

1. Lưới 5 cm bám đúng tờ giấy, góc dưới ghi `Luoi A4: thay 4/4 ma ArUco` (hai khung đảo nhau thì chạy lại với `--top 1 --side 0`).
2. Đặt cốc: vòng xanh nằm trên cốc, kèm X, Y (cm).
3. Bấm `R`: ô 1 hiện lệnh to, ví dụ `BAM D x8`.
4. Bấm đúng phím đó: số lần bấm giảm dần, tới `XONG!`; giữ 1 giây thì `Thanh cong` cộng 1.

## Không cần đọc

- `robot_arm_4dof/`: firmware (phần 3).
- `slides/build_slides.py`, `slides/build_part2.py`, `slides/tools/`: chỉ cần khi sửa slide.
