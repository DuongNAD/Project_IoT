# Vũ · Hỗ trợ gắp

**Việc của bạn:** nhận `Plan` của khối điều khiển rồi trả lời **một câu**: ba servo đế, vai, khuỷu đã tới góc gợi ý chưa (`success.py`).
Sau đó vẽ kết quả lên màn hình (`screen.py`), giữ bộ test, và trình bày thử nghiệm, kết quả, hạn chế. Bạn **không** cần biết camera, IK hay cổng USB hoạt động thế nào.

Đọc [README.md](README.md) bước 0 (phần chung) trước, nhất là lớp `Plan` và `Move`: đó là toàn bộ đầu vào của bạn.

## Slide bạn nói

| Bộ slide | Slide | Nội dung |
|---|---|---|
| `slides/Phan2_LuongDuLieu_Code.pptx` (Canva) | 8 | điều kiện hoàn thành · `success.py` |
| | 9 | màn hình · `screen.py` |
| `slides/Project_IoT_ThuyetTrinh.pptx` (bản đầy đủ 25 slide) | 14 | điều kiện hoàn thành |
| | 15 | thử nghiệm trên cánh tay thật (02/11) |
| | 16 | kết quả: đã làm / chưa làm, 102 test |
| | 17 | hạn chế và hướng phát triển (cuối slide giới thiệu người nói phần 3) |

## Lộ trình đọc (theo thứ tự)

Mỗi bước: mở đúng dòng, đọc, rồi tự trả lời câu hỏi ở cột cuối **không nhìn code**.

### Bước 1 · Đầu vào: `Plan` và `Move`

| Đọc | Ý chính | Tự hỏi |
|---|---|---|
| `control.py:510-525` (`Plan`) | các trường bạn dùng: `found` (đã có đích chưa, tức đã bấm `R`), `reachable` (trong tầm với), `relaxed` (tay đang nghỉ), `moves` (3 `Move`), `usb_ok`, `banner` | Trường nào cho biết tay đang ngắt xung? |
| `control.py:216-228` (`Move`) | mỗi servo một `Move`: `key` (phím), `steps` (số lần bấm), `step` (2° mỗi lần), `degrees` (độ lệch thật), `words` (lời chỉ), `now`, `goal` | `steps` và `degrees` khác nhau thế nào? |
| `control.py:231-240` (`plan_moves`) | `steps = độ lệch // bước` (làm tròn xuống) | Từ 90° tới 74° thì bấm mấy lần? (16 // 2 = 8) |

### Bước 2 · `success.py` (58 dòng, đọc hết)

Đọc theo 4 số trên slide 8:

| Số | Dòng | Làm gì |
|---|---|---|
| 1 | `success.py:11-12` | `TOLERANCE_STEPS = 1`: lệch **≤ 1 bước (2°)** là đã tới. `HOLD_S = 1.0`: giữ **liên tục 1 giây** mới đếm |
| 2 | `success.py:27-28` | so từng servo với góc gợi ý; `pending` = các servo chưa tới |
| 3 | `success.py:29-37` | trạng thái theo **ưu tiên**: `relaxed` → `no_target` → `unreachable` → `moving` / `done`. Hàm `check` **không nhớ gì** giữa hai lần gọi |
| 4 | `success.py:48-58` (`Success.update`) | bắt đầu tính giờ khi vừa `done`; đủ 1 giây thì `count + 1`; giữ thêm không cộng; rời góc thì tính lại |

Đọc thêm `success.py:15-22` (lớp `Result`): `state`, `done`, `joints_ok`, `next_move` (việc đầu tiên, theo thứ tự đế → vai → khuỷu), `remaining` (tổng số lần bấm còn lại), `count`.

Tự hỏi:

- Vì sao dung sai là 2° chứ không phải 0°? (mô hình hình học chỉ chính xác cỡ đó; bắt căn 0° chỉ làm người dùng đuổi theo nhiễu)
- Vì sao `relaxed` thắng mọi trạng thái khác? (đã ngắt xung thì góc báo về chỉ là góc lệnh cuối, không tin được)
- Vì sao phải giữ 1 giây? (để lần lướt qua mục tiêu không bị đếm)
- Chưa bấm `R` (chưa có đích) mà góc "khớp" thì có XONG không? (không)

### Bước 3 · `screen.py` (79 dòng)

`screen.py` **chỉ vẽ, không tính gì**: mọi chữ lấy từ `Plan` và `Result`. Đọc theo 4 số trên slide 9:

| Số | Dòng | Làm gì |
|---|---|---|
| 1 | `screen.py:33-48` | thu mỗi camera vào ô 640 × 360, ghép thành hàng trên |
| 2 | `screen.py:51-57` | ô 1 · điều khiển: trạng thái `moving` thì hiện lệnh lớn (ví dụ `BAM S x15: HA XUONG 30 do`); trạng thái khác hiện câu nhắc trong `MESSAGES` (`screen.py:21-26`) |
| 3 | `screen.py:58-60` | 3 dòng servo: góc hiện tại → góc đích, phím cần bấm; dòng đã tới ghi `DA DUNG` màu xanh |
| 4 | `screen.py:62-71` | ô 2 · success: `XONG!` xanh, hoặc `CHUA XONG` + `con N lan bam`; `Thanh cong: N lan` |

Đọc lướt `screen.py:73-76` (chân trang: trạng thái USB, phím tắt, banner `ARDUINO VUA RESET`).

Tự hỏi: vì sao chữ không dấu? (font của OpenCV không vẽ được dấu tiếng Việt) Phím `A` quay đế sang đâu? (sang **phải**, nhìn theo cam NGANG)

### Bước 4 · Bộ test (bạn phụ trách kiểm thử)

| Đọc | Kiểm gì |
|---|---|
| `tests/test_success.py` (7 test) | đọc từng test như một **ví dụ có đáp án**: đang đi, bỏ qua servo đã đúng, lệch 2° vẫn tới còn 3° thì chưa, kẹp không tính, ưu tiên trạng thái, đếm sau 1 giây, lướt qua không đếm |
| `tests/test_screen.py` (3 test) | hai ô đổi theo trạng thái còn ô camera không đổi; trạng thái ngoài tầm, đang nghỉ vẫn vẽ được; số lần thành công và banner hiện lên màn hình |
| `tests/test_end_to_end.py` (2 test) | cả chuỗi trên cảnh giả lập: bấm đúng theo lệnh trên màn hình thì ra XONG, đếm đúng 1 lần; cùng một `Plan` cho cùng một kết luận |
| `tests/conftest.py` | vì sao không test nào mở camera thật, cổng Serial hay `calibration.json` thật |

```bash
uv run pytest tests/test_success.py tests/test_screen.py tests/test_end_to_end.py -v
```

Bài tập (làm bằng tay trước): góc hiện tại `[90, 90, 90]`, góc gợi ý `[74, 60, 86]`. Trạng thái? Servo nào làm trước, bấm phím gì, mấy lần? Còn tổng bao nhiêu lần bấm?

<details><summary>Đáp án và cách tự kiểm</summary>

`moving`; đế trước, phím `D` × 8 (16°); vai `S` × 15 (30°); khuỷu `K` × 2 (4°); còn 8 + 15 + 2 = **25** lần bấm (`tests/test_success.py:12-15`). Chạy thử:

```bash
uv run python -c "import control as C, success as S; p = C.Plan(found=True, target_name='Vat mau', target_cm=(20.0, 12.0), reachable=True, move_closer_mm=0.0, relaxed=False, now=[90, 90, 90, 95], goal=[74, 60, 86], moves=C.plan_moves([90, 90, 90, 95], [74, 60, 86])); r = S.check(p); print(r.state, r.joints_ok, r.next_move.key, r.next_move.steps, r.remaining)"
```

In ra `moving [False, False, False] d 8 25`.
</details>

### Bước 5 · Thử nghiệm, kết quả, hạn chế (slide 15-17)

Phần này không có code, chỉ có số liệu. Đọc trong `slides/05_SO_LIEU_VA_NGUON.md`:

| Mục | Để nói slide |
|---|---|
| mục 7 · buổi thử 02/11 | slide 15: kẹp bằng bàn phím 20:32-20:36, cốc đỏ được kẹp, chuyển sang trái, đặt xuống; cốc đổ khoảng 3 lần; kẹp chưa giữ chắc cốc thon |
| mục 11 · kiểm thử | slide 16: **102 test**, 13 tệp; chạy ngày 11/11 trên máy Windows |
| mục 13 · kế hoạch 28/10 so với thực tế | slide 16: việc chưa làm (MQTT, dashboard, cảm biến lực FSR) |
| mục 4, 8, 9, 10 | slide 17: điều khiển vòng hở, hiệu chỉnh phụ thuộc tờ giấy và vị trí robot, tay kẹp phi tuyến, hai lỗi tích hợp đã xử lý (thứ tự camera macOS, Arduino tự reset) |

## Số liệu phải nhớ

Nguồn: `slides/05_SO_LIEU_VA_NGUON.md` mục 4, 5, 7, 11.

| Số | Ý nghĩa |
|---|---|
| 2° | mỗi lần bấm đế / vai / khuỷu, và cũng là dung sai "đã tới" |
| 1 giây | phải giữ đúng liên tục mới đếm 1 lần thành công |
| 5 trạng thái | `done`, `moving`, `no_target`, `unreachable`, `relaxed` |
| 640 × 360 | mỗi ô camera trên màn hình (cửa sổ rộng 1280 px) |
| 102 test · 13 tệp | success 7, màn hình 3, đầu-cuối 2, điều khiển từ xa 11 (trong tổng 102) |
| 02/11/2026, 20:32-20:36 | buổi kẹp cốc bằng bàn phím trên cánh tay thật |
| 8,5 mm | sai số hiệu chỉnh trên **chính 10 mẫu** dùng để khớp (chi tiết ở phần 3) |

## Không nói quá (quan trọng nhất với phần của bạn)

- **XONG ≠ gắp được.** XONG nghĩa là ba góc **đã ra lệnh** tới góc gợi ý; MG996R không báo vị trí thật, kẹp không tính.
- **Không có tỉ lệ thành công nào.** Chưa có lần đếm XONG nào trên cánh tay thật với bản mới: nói "chưa đo".
- Không nói "robot tự động gắp": người bấm phím, màn hình chỉ cho biết bấm gì.
- Không nói "kẹp giữ chắc cốc": cốc thon bị đẩy ra khi khép tới 150-160°.
- Ảnh màn hình trên slide là chương trình thật **chạy trên ảnh đã lưu, cánh tay mô phỏng**, không phải lần chạy trực tiếp.
- Còn hai chỗ `[...điền]` trong ghi chú slide 15 (có video không) và slide 16 (đề có bắt buộc dashboard IoT không): hỏi nhóm trước khi tập nói.
