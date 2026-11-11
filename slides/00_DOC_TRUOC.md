# 00 · Đọc trước

Bộ slide thuyết trình đề tài: `Project_IoT_ThuyetTrinh.pptx` (+ `.pdf`), **24 slide**, 3 phần cho 4 người:
01 linh kiện → 02 computer vision & hỗ trợ gắp (Nguyễn Anh Dương, Phạm Trương Vũ) → 03 code điều khiển. Chữ trên slide ngắn; lời nói,
"Nếu được hỏi" và "Nguồn" nằm trong ghi chú của từng slide.

| File | Nội dung |
|---|---|
| `build_slides.py` | dựng cả bộ slide; tên người ở bảng `TEAM` đầu tệp, thứ tự slide ở `ORDER` cuối tệp |
| `05_SO_LIEU_VA_NGUON.md` | mọi con số trên slide và nguồn của nó; danh sách **CẤM NÓI** (mục 14) |
| `verify_slides.py` | kiểm bộ slide: số trang, ghi chú, chữ "mô phỏng", chỗ `[...]` còn phải điền |
| `tools/check_facts.py` | kiểm `05_SO_LIEU_VA_NGUON.md` còn khớp mã nguồn không (hằng số, dẫn `tệp:dòng`) |
| `tools/make_screen_images.py` | chụp lại ảnh màn hình và lưới camera cho slide 12, 13, 14, 22 (cần `captures/` và `calibration.json`, chỉ có trên MacBook) |
| `tools/prepare_real_assets.py` | cắt và làm mờ ảnh thật vào `assets/real/` |
| `preview/` | ảnh xem trước từng slide |

## Dựng lại

```bash
python slides/build_slides.py      # -> Project_IoT_ThuyetTrinh.pptx
python slides/export_pdf.py        # -> .pdf (LibreOffice, hoặc PowerPoint trên Windows)
python slides/render_previews.py   # -> preview/slide_XX.png
python slides/verify_slides.py     # phải ra "KẾT QUẢ: ĐẠT"
python slides/tools/check_facts.py # sau mỗi lần sửa mã
```

Ảnh thật (`assets/real/`) không nằm trong git. Thiếu ảnh nào thì slide hiện khung `[Ảnh: ...]`.

## Còn phải làm

- [ ] Điền `[Tên A]` (linh kiện), `[Tên C]` (code điều khiển) ở bảng `TEAM`; `[Môn học]`, `[Ngày báo cáo]`, giảng viên, lớp ở bìa.
- [ ] Ảnh ở slide 12, 13, 14, 22 chụp bằng **giao diện trước khi rút gọn mã ngày 10/11** (chú thích trên slide ghi "giao diện bản trước").
  Trên MacBook chạy `python slides/tools/make_screen_images.py`, đặt `UI_OLD = False` trong `build_slides.py`, dựng lại; kiểm lại các số trong ghi chú slide 22
  (vị trí cốc, `S × 15`, còn 18 lần bấm) theo ảnh mới. Ảnh cũ mô phỏng cánh tay ở 90/90/90; Home giờ là **180/90/90/95** (đế hết bên phải)
  nên ảnh mới sẽ bắt đầu bằng lệnh `D` nhiều lần.
- [ ] Nạp lại firmware (`./robot_arm_4dof/flash.sh`) trên máy cắm Arduino: Home và góc khởi động của đế đổi từ 90° sang **180°** ngày 11/11.
- [ ] Chạy `pytest` trên MacBook: 92 test mới chỉ chạy trên máy Windows (xem `05_SO_LIEU_VA_NGUON.md` mục 11).
- [ ] Tập nói, bấm giờ; thử mở PPTX và PDF trên máy sẽ trình chiếu.

## Không nói quá (tóm tắt mục 14 của `05`)

1. Không tự động: màn hình chỉ cho biết bấm phím nào; người bấm.
2. "XONG" là ba góc lệnh tới góc gợi ý (MG996R không báo vị trí thật), kẹp không tính; không phải "đã gắp".
3. Chưa có tỉ lệ thành công trên cánh tay thật.
4. Sai số hiệu chỉnh 8,5 mm là trên chính 10 mẫu dùng để khớp; đổi tờ giấy hoặc dời robot thì phải đo lại.
5. Servo kẹp: có ngắt xung, giới hạn 160°, phím `X` / `Z`; chưa đo nhiệt độ.
