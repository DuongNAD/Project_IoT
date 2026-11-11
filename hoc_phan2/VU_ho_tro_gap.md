# Vũ · Hỗ trợ gắp

**Việc của bạn:** nhận `Plan` của khối điều khiển rồi trả lời **một câu**: ba servo đế, vai, khuỷu đã tới góc gợi ý chưa (`success.py`); vẽ kết quả lên
màn hình (`screen.py`); trình bày thử nghiệm, kết quả, hạn chế. Học khoảng **85 dòng** dưới đây; phần còn lại chỉ cần một câu.
Đọc [README.md](README.md) phần "Cả hai phải thuộc" trước.

## Slide bạn nói

| Bộ slide | Slide | Nội dung |
|---|---|---|
| `slides/Phan2_LuongDuLieu_Code.pptx` (Canva) | 8 | điều kiện hoàn thành · `success.py` |
| | 9 | màn hình · `screen.py` |
| `slides/Project_IoT_ThuyetTrinh.pptx` (bản đầy đủ 25 slide) | 14 | điều kiện hoàn thành |
| | 15 | thử nghiệm trên cánh tay thật (02/11) |
| | 16 | kết quả: đã làm / chưa làm, cách kiểm tra bằng mắt |
| | 17 | hạn chế và hướng phát triển (cuối slide giới thiệu người nói phần 3) |

## Dòng code chính (học kỹ)

| Dòng | Ý chính | Tự hỏi |
|---|---|---|
| `success.py:11-12` | lệch **≤ 1 bước (2°)** là tới; giữ **1 giây** mới đếm | Vì sao 2° mà không 0°? (mô hình chỉ chính xác cỡ đó) |
| `success.py:25-37` (`check`) | so từng servo với góc gợi ý; trạng thái theo ưu tiên `relaxed` → `no_target` → `unreachable` → `moving` / `done` | Chưa bấm R mà góc "khớp" thì có XONG không? (không) |
| `success.py:48-58` (`Success.update`) | vừa `done` thì bắt đầu tính giờ; đủ 1 giây cộng 1; rời góc thì tính lại | Lướt qua đích có được đếm không? (không) |
| `screen.py:46-71` (`build_screen`) | 2 camera; ô 1 lệnh to `BAM D x8`; 3 dòng servo (`DA DUNG` màu xanh); ô 2 `XONG!` / `CHUA XONG`, `Thanh cong: N lan` | Vì sao chữ không dấu? (font OpenCV không vẽ được dấu) |
| `control.py:227-235` (`plan_moves`) | góc hiện tại → góc đích: phím gì, mấy lần (`độ lệch // 2`) | Từ 90° tới 74° bấm mấy lần? (8) |
| `control.py:429-440` (`lock_target`) | bấm R: vật gần đế nhất thành đích, góc cần tới tính **một lần** | Cốc bị dời thì sao? (bấm R lại) |
| `control.py:443-454` (`update`) | mỗi khung chỉ so góc servo hiện tại với góc đích, ra `Plan` | Arduino báo góc về bằng gì? (gói JSON qua USB) |

## Phần còn lại: chỉ cần một câu

| Phần | Câu cần nói |
|---|---|
| IK `control.py:91-134` | Đế quay theo `atan2(y, x)`; vai và khuỷu giải tam giác hai khâu bằng định lý cos, chọn nghiệm khuỷu hướng lên. |
| `control.py:137-154` (`joint_to_servo`) | Đổi góc khớp sang góc servo, làm tròn về bước 2°. |
| `control.py:289-301`, `303-318` | Mỗi phím gửi 1 ký tự qua USB; đọc gói JSON góc servo Arduino gửi về; không ghi `--port` thì mô phỏng. |
| `remote.py` | Dell hiện màn hình Mac, gửi phím qua Bluetooth HC-05; `H` và `Z` phải bấm 2 lần (`KeyGate`, `remote.py:120-139`). |
| `screen.py:21-26` (`MESSAGES`) | Câu nhắc ở ô 1 cho các trạng thái không phải `moving`. |
| Cách kiểm tra | Bằng mắt khi chạy chương trình: lưới bám giấy, vòng xanh trên cốc, bấm theo lệnh thì cánh tay đi đúng hướng. |

## Bài tập

Bài tập (làm bằng tay trước): góc hiện tại `[90, 90, 90]`, góc gợi ý `[74, 60, 86]`. Trạng thái? Servo nào làm trước, bấm phím gì, mấy lần? Còn tổng bao nhiêu lần bấm?

<details><summary>Đáp án và cách tự kiểm</summary>

`moving`; đế trước, phím `D` × 8 (16°); vai `S` × 15 (30°); khuỷu `K` × 2 (4°); còn 8 + 15 + 2 = **25** lần bấm. Chạy thử:

```bash
uv run python -c "import control as C, success as S; p = C.Plan(found=True, target_name='Vat mau', target_cm=(20.0, 12.0), reachable=True, move_closer_mm=0.0, relaxed=False, now=[90, 90, 90, 95], goal=[74, 60, 86], moves=C.plan_moves([90, 90, 90, 95], [74, 60, 86])); r = S.check(p); print(r.state, r.joints_ok, r.next_move.key, r.next_move.steps, r.remaining)"
```

In ra `moving [False, False, False] d 8 25`.
</details>

## Thử nghiệm, kết quả, hạn chế (slide 15-17)

Phần này không có code, chỉ có số liệu. Đọc trong `slides/05_SO_LIEU_VA_NGUON.md`:

| Mục | Để nói slide |
|---|---|
| mục 7 · buổi thử 02/11 | slide 15: kẹp bằng bàn phím 20:32-20:36, cốc đỏ được kẹp, chuyển sang trái, đặt xuống; cốc đổ khoảng 3 lần; kẹp chưa giữ chắc cốc thon |
| mục 11 · cách kiểm tra | slide 16: kiểm tra **bằng mắt** khi chạy chương trình (lưới bám giấy, vòng xanh trên cốc, cánh tay đi đúng hướng); bộ test tự động đã bỏ |
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
| 0,2 cm | slide 16: hai camera đo cùng một cốc lệch nhau 0,2 cm sau bù thị sai (đo ở **một** vị trí, 02/11) |
| 02/11/2026, 20:32-20:36 | buổi kẹp cốc bằng bàn phím trên cánh tay thật |
| 8,5 mm | sai số hiệu chỉnh trên **chính 10 mẫu** dùng để khớp (chi tiết ở phần 3) |

## Không nói quá (quan trọng nhất với phần của bạn)

- **XONG ≠ gắp được.** XONG nghĩa là ba góc **đã ra lệnh** tới góc gợi ý; MG996R không báo vị trí thật, kẹp không tính.
- **Không có tỉ lệ thành công nào.** Chưa có lần đếm XONG nào trên cánh tay thật với bản mới: nói "chưa đo".
- Không nói "robot tự động gắp": người bấm phím, màn hình chỉ cho biết bấm gì.
- Không nói "kẹp giữ chắc cốc": cốc thon bị đẩy ra khi khép tới 150-160°.
- Ảnh màn hình trên slide là chương trình thật **chạy trên ảnh đã lưu, cánh tay mô phỏng**, không phải lần chạy trực tiếp.
- Còn hai chỗ `[...điền]` trong ghi chú slide 15 (có video không) và slide 16 (đề có bắt buộc dashboard IoT không): hỏi nhóm trước khi tập nói.
