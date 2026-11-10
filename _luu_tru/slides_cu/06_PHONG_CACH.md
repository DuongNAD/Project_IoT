# 06 · Phong cách slide (rút từ slide Gamota của bạn)

Mục tiêu: slide dự án IoT nhìn **cùng một "nhà"** với slide Gamota: nền trắng sữa ấm, chữ nâu than, một màu nhấn xanh teal,
mỗi slide một ý, số liệu lớn, ảnh thật trong thẻ ngà, lời nói đầy đủ nằm trong ghi chú.

Ảnh tham chiếu (hãy mở xem trước khi dựng): `assets/reference/gamota_contact_1_slides_01-09.png`,
`gamota_contact_2_slides_10-18.png`, `gamota_contact_3_slides_19-25.png`, và các trang lớn `gamota_p01/04/05/06/12/14.png`.
Mã dựng tham chiếu: `assets/reference/gamota_helpers.js` (đã chỉnh cho dự án này: đọc kích thước ảnh từ header, `shot()` tự
vẽ ô "THIẾU ẢNH" nếu thiếu file, `caption()` có nhãn "Minh họa (AI)", công tắc phông `DECK_FONT`).

---

## 1. Token

Khổ **13,333 × 7,5 inch (16:9)**, lề `M = 0,8`, bề rộng nội dung `CW = 11,733`. Mọi tọa độ dưới đây tính bằng inch.

| Token | Giá trị | Dùng cho |
|---|---|---|
| `bg` | `FBF8F1` | nền slide nội dung |
| `bg2` | `F3EDE1` | nền slide xen kẽ, panel trung tính |
| `card` | `FFFDF8` | thẻ, ô số, khung ảnh |
| `ink` | `2B2520` | chữ chính, đường nhấn |
| `text2` | `62594F` | chữ mô tả |
| `muted` | `877D72` | chú thích, nguồn, số trang |
| `line` | `E2D9C8` | đường kẻ mảnh 0,75 pt |
| `teal` / `tealSoft` | `2F6A56` / `E4ECDF` | **phần mềm tất định và bằng chứng đã có** |
| `orange` / `orangeSoft` | `A64B24` / `F5E3D3` | **phần cứng, rủi ro, điều chưa kiểm chứng** |
| `llm` / `llmSoft` | `5C5A8E` / `EAE6EF` | **mô hình học máy (YOLO11, tùy chọn)**; ở Gamota là LLM. Deck mặc định hầu như không dùng màu này (YOLO tắt mặc định) |
| `statement` | `F1E7D3` | nền slide trích dẫn |
| `shadow` | `3A2E22` | bóng thẻ ảnh (độ mờ 10%, blur 12) |

Ý nghĩa màu trong slide IoT (giữ nhất quán từ slide 3 tới hết): **xanh = code tất định hoặc bằng chứng có thật; đất nung = phần cứng,
rủi ro, điều chưa kiểm chứng; chàm = YOLO11 (tùy chọn); xám ấm = trung tính (camera, con người).** Không dùng thêm màu khác.

Phông: mặc định **Arial** (giống hệt trên Windows, macOS, Keynote, LibreOffice; tiêu đề in đậm). `DECK_FONT="Segoe UI"` tái tạo đúng
slide Gamota nhưng chỉ đẹp trên Windows. Arial rộng hơn Segoe UI một chút nên bố cục vừa với Arial thì vừa với Segoe UI.
Mã `Consolas`/`Courier New` cho tên file và hằng số.

| Chữ | Cỡ | Ghi chú |
|---|---|---|
| eyebrow | 11 pt, hoa, giãn chữ 2, màu teal | đặt tại `y = 0,6` (placeholder của master) |
| tiêu đề | 30 pt | `y = 0,92`, tối đa 2 dòng, chữ thường (sentence case), không dấu chấm cuối |
| số lớn | 44–48 pt | teal (có thật) hoặc đất nung (rủi ro) |
| chữ thân | 18 pt mặc định; 12,5–17 pt trong thẻ | **tối thiểu 11 pt**, chân trang 10 pt |
| chú thích, nguồn | 11,5–12 pt, `muted` | `y = 6,78` |
| chip | 11 pt, giãn chữ 1, cao 0,36 | nền soft, chữ màu đậm |

## 2. Bốn master

| Master | Nền | Dùng cho |
|---|---|---|
| `CONTENT` | `bg` | slide nội dung thường (eyebrow + tiêu đề + số trang góc phải dưới `y = 6,9`) |
| `CONTENT_ALT` | `bg2` | slide xen kẽ để tạo nhịp (Gamota xen ở các slide kết quả) và **toàn bộ phụ lục** |
| `PLAIN` | `bg` | bìa và slide kết (không eyebrow/tiêu đề placeholder) |
| `STATEMENT` | `statement` | slide có câu trích lớn |

## 3. Linh kiện (đã có trong `gamota_helpers.js`)

`T` chữ thường · `H` chữ tiêu đề · `mono` tên file · `label` nhãn hoa nhỏ · `box` ô màu · `rule` đường kẻ · `arrow` mũi tên ·
`dot(n)` chấm tròn đánh số 0,46 in, số 14 pt trắng · `chip` nhãn nhỏ · `shot` ảnh trong thẻ ngà (đệm 0,06 + bóng) ·
`caption` chú thích dưới ảnh · `link` liên kết GitHub · `OWN.{CODE,YOLO,HW,NEUTRAL}` màu theo "ai làm việc".

## 4. Mẫu bố cục (pattern)

Mỗi slide trong `01_KICH_BAN_SLIDE.md` ghi tên mẫu. Tọa độ tính từ góc trên trái.

**P1 · BÌA** (`PLAIN`). Nhãn `y 1,0`; tiêu đề 30 pt `x 0,8 · y 1,75 · w 6,0 · h 1,35`; phụ đề 18 pt `text2` `y 3,3`; khối tác giả: tên 17 pt `y 5,7`,
dòng nhỏ 13 pt `muted` `y 6,1`. Panel phải `box(6,9, 0, W−6,9, 7,5, bg2)`; hai thẻ ảnh 16:9 `x 7,35 · w 5,3`: `y 0,6 · h 2,98` và `y 3,9 · h 2,98`.

**P2 · HÀNG ĐÁNH SỐ + THẺ PHỤ** (`CONTENT`, mẫu Gamota slide 2; slide 2 của deck IoT dùng **ba** hàng). Nhãn `y 2,2 · w 6,9`. Các hàng `y = 2,75 + i·0,95`: đường kẻ `w 6,9` ở đầu hàng,
`dot` tại `(0,8; y+0,24)`, câu hỏi 18 pt `x 1,5 · w 4,7`, chip `x 6,4 · w 1,3 · y+0,3`; đường kẻ cuối `y 6,55`. Thẻ phải
`x 8,35 → 12,533 · y 2,2 · h 4,25` nền `orangeSoft`. Chân trang `y 6,78`.

**P3 · HAI THẺ + DẢI DƯỚI** (mẫu Gamota slide 3). Hai thẻ `w = (CW−0,4)/2 = 5,667 · y 1,95 · h 3,85`; dải dưới `y 5,95 · h 0,75` nền `tealSoft` có nhãn và ba mục đánh số.

**P4 · SƠ ĐỒ ỐNG DẪN N Ô** (mẫu Gamota slide 4). Dòng dẫn 14 pt `y 1,98`; N ô `y 2,45 · h 2,4`, khe 0,3; trong ô: số 12 pt, tên 16 pt, tên file `mono` 11 pt, mô tả 12 pt;
nhãn chủ thể dưới ô 10,5 pt giãn chữ 2; mũi tên giữa các ô; ba đường kẻ luật `y 5,55`, tiêu đề 17 pt, mô tả 13,5 pt.

**P5 · BA SỐ LỚN + BỐN THẺ** (`CONTENT_ALT`, mẫu Gamota slide 5). Nhãn `y 1,8`; ba ô `card` `y 2,15 · h 1,75` (số 44 pt teal `y 2,3`, mô tả 14,5 pt `y 3,15`);
nhãn `y 4,1`; bốn thẻ `y 4,45 · h 2,25`.

**P6 · TRÍCH DẪN LỚN** (`STATEMENT`, mẫu Gamota slide 6). Nhãn `y 1,0`; câu trích 26 pt `y 1,45 · w 11,2 · h 1,95`; nhãn `y 3,5`; ba thẻ `y 3,9 · h 2,85`.

**P7 · BA SỐ + HAI Ô** (mẫu Gamota slide 7). Ba số 48 pt đất nung `y 2,4` dưới đường kẻ `y 2,2`; mô tả 17 pt `y 3,45`; hai ô `bg2` phía dưới.

**P8 · LÀM / CHƯA LÀM** (mẫu Gamota slide 8). Panel trái `tealSoft` (các hàng đánh số, gạch teal) và danh sách phải gạch ngang "—" màu đất nung.

**P9 · BỐN Ô SỐ** (`CONTENT_ALT`, mẫu Gamota slide 12). Lưới 2×2 ô `card`, số 30–36 pt teal, mô tả 14,5 pt, ghi chú nhỏ 11,5 pt `muted`.

**P10 · LƯỚI THẺ NHỎ** (phụ lục, mẫu Gamota slide 15–18). Tên lớp ở cột trái, thẻ `card` nhỏ chứa tên file `mono` 11 pt và mô tả 11 pt.

Các mẫu mới cho slide IoT:

**P11 · HÀNG ẢNH KỂ CHUYỆN** (slide 10). Nhãn hàng ở cột trái `x 0,8 · w 0,95` (chip "CAM NGANG" `y 2,75`, "CAM TRÊN" `y 4,94`). Ba cột ảnh `x = 1,8 + i·3,63 · w 3,45` (16:9, cao 1,94);
hàng 1 `y 2,0`, hàng 2 `y 4,19`. Dưới hàng 2 (`y 6,22`) nhãn thời điểm 11 pt teal. Chân trang `y 6,62`: chip đất nung `x 0,8 · w 5,0` + dòng 11 pt `muted` `x 5,95 · w 6,58`.

**P12 · LƯỚI ẢNH 2×2 + CỘT THÔNG SỐ** (slide 4). Bốn ô ảnh `w 2,9 · h 2,0` tại `(0,8; 1,95)`, `(3,9; 1,95)`, `(0,8; 4,35)`, `(3,9; 4,35)`, chú thích 11,5 pt `+2,1` dưới mỗi ô; cột phải `x 7,2 · w 5,33`.

**P13 · SƠ ĐỒ KHỐI HAI HÀNG** (slide 3). Hàng 1: năm ô rộng 1,85, khe 0,62, tại `x = 0,8 + i·2,47`, `y 2,55 · h 1,3`; mỗi ô có nhãn nhỏ 10 pt hoa (màu theo `OWN`), tiêu đề 14 pt, mô tả 11 pt. Ô nhóm 1 và nhóm 2 viền dày 2,25 pt, dot số 1 và 2 ở **góc trên phải** (để không đè nhãn). Mũi tên giữa các ô, nhãn 10 pt trên mũi tên; mũi tên `Plan` dày 3,5 pt màu teal, nhãn đậm 12 pt. Vòng người: ba đoạn thẳng màu đất nung từ đỉnh ô 5 lên `y 2,18`, sang trái, xuống đỉnh ô 3 (đầu mũi tên), nhãn 11 pt màu đất nung trên đoạn ngang. Hàng 2: ba ô đất nung `y 4,45 · h 1,1` dưới ô 3, 4, 5 nối bằng mũi tên ngang; hai mũi tên dọc giữa ô 3 và Arduino (phím xuống, JSON lên) có nhãn 10 pt ở `y 3,97`; thẻ `card` bên trái `x 0,8 · w 4,45 · y 4,45 · h 1,1` nói về `Plan`. Dải `Vì vậy` `y 5,95 · h 0,65`; chú giải màu `y 6,82`. Tiêu đề mỗi ô ≤ 16 ký tự (`Lệnh + XONG`, không phải `Lệnh bấm + XONG`: sẽ xuống dòng và đè mô tả). Mã chạy được: `assets/reference/sample_slides_body.js`.

**P14 · SƠ ĐỒ CÁNH TAY NHÌN NGANG** (slide 7), vẽ bằng hình gốc của PPTX, tỉ lệ 0,02 in/mm, mặt bàn `y 6,0`:
đế (1,3; 6,0) → vai (1,3; 4,6) → khuỷu (2,785; 3,115) → cổ tay (4,785; 3,115) → tâm hai ngón kẹp (6,085; 3,615).
Khâu L₂ và L₃ là thanh dày 6 pt màu `ink`; đoạn cổ tay → tâm kẹp nét đứt; khớp là vòng tròn 0,16 in; đích là chấm đất nung. Ghi kích thước
`d₁ = 70`, `L₂ = 105`, `L₃ = 100`, `65`, `25` (mm) và góc `θ₂ = 45°`, `θ₃ = −45°` (tư thế servo 90°/90°). Chú thích "Mô hình mặc định: số đo thước theo `ARM_CONFIG`" (số đã hiệu chỉnh nằm ở phụ lục B). Vị trí nhãn (11,5 pt, tránh đè lên thanh): `d₁` `(1,85; 5,15)`; `L₂` `(0,8; 3,55) w 1,15 căn phải`; `L₃` `(3,05; 2,75) w 1,5 căn giữa`; `65 mm` `(5,1; 2,82)`; `25 mm` `(6,2; 3,28)`; `Vai` `(0,8; 4,5) w 0,34 căn phải`; `Khuỷu` `(1,95; 2,82) căn phải`; `Cổ tay` `(4,45; 3,28)`; `Tâm hai ngón kẹp` `(4,4; 3,82) w 1,7 căn phải` màu đất nung; `θ₂` `(1,95; 4,25)`; `θ₃` `(2,95; 3,3)`.

**P15 · DÒNG THỜI GIAN HAI LÀN** (slide 18). Trục 0–70 s ánh xạ `x 2,6 → 12,2` (0,137 in/giây). Làn A `y 2,35` (thanh cao 0,5): teal 0–5 s rồi xám; làn B `y 3,25`: teal 0–60 s rồi xám. Trục `y 3,95`, mốc 0, 5, 60 s. Bốn thẻ nhỏ `y 4,6 · h 0,95 · w 2,78` (khe 0,2); chú thích 11 pt `y 5,8`. (Cảnh báo "GIU 31s" ở giây 30 thuộc giao diện cũ đã bỏ, **không** vẽ.)

**P17 · BA SỐ LỚN + ẢNH MÀN HÌNH + HAI THẺ RỦI RO** (slide 9). Trái: ba hàng `y = 1,95 + i·1,2`, mỗi hàng một đường kẻ `w 6,3`, số lớn 34 pt teal `x 0,8 · w 1,95`, mô tả 14 pt `x 2,9 · w 4,2`. Phải: ảnh màn hình `x 7,4 · y 1,95 · w 5,13 · h ≤ 3,0`, chú thích 11 pt ngay dưới (2 dòng). Dưới: hai thẻ `orangeSoft` `y 5,6 · h 1,0` (nhãn đất nung + chữ 12 pt). Chân: chip teal `w 6,2` và chip đất nung `w 4,6` tại `y 6,68`, **không** vượt `x 11,8` (số trang nằm ở `x 12,0 · y 6,9`). Mã chạy được: `sample_slides_body.js`.

**P18 · ẢNH LỚN + DANH SÁCH** (slide 8). Ảnh màn hình `x 0,8 · y 1,95 · w 7,4` (tỉ lệ gốc ≈ 1,76:1 nên cao ≈ 4,2), chú thích 11 pt dưới ảnh (2 dòng, `w 7,4`); cột phải `x 8,5 · w 4,03`: nhãn, ba hàng có dot, đường kẻ, dòng phím tắt và chip đất nung.

**P16 · HỎI–ĐÁP HAI CỘT** (slide 25). Hai cột `w 5,6`, mỗi cột sáu hàng cao 0,78: câu hỏi 13 pt đậm + câu trả lời 11,5 pt `text2`, đường kẻ mảnh giữa các hàng.

## 5. Quy tắc ảnh

1. Ảnh thật dùng đúng file trong `assets/real/` (đã cắt và làm mờ), qua `shot()`; **không kéo méo**, không phóng quá 2 lần kích thước gốc.
2. Mọi ảnh có `altText` (lấy từ `assets/manifest.json`, trường `alt_vi`).
3. Ảnh AI luôn kèm nhãn **"Minh họa (AI)"** (đất nung, cạnh chú thích) và **không bao giờ** đặt ở slide kết quả hoặc bằng chứng (slide 5, 6, 8, 9, 10, 11, 12, 13); mặc định ảnh AI chỉ ở slide 2 và 14.
4. Không chữ đè lên ảnh. Nhãn nằm ngoài ảnh (chip hoặc chú thích). Ảnh chụp màn hình giữ chữ không dấu của phần mềm, không "sửa".
5. Ảnh nhỏ (≤ 960 px: `hw_electronics`, `hw_arm_gripper`, `ui_fk_vs_real`) đặt ở thẻ ≤ 3,2 in rộng.
6. Ảnh màn hình `ui_screen_before` / `ui_screen_done` và các ảnh `sw_annot_*`, `calib_before_after_side` là **chương trình chạy trên ảnh camera thật đã lưu, cánh tay mô phỏng**: chú thích bắt buộc ghi "mô phỏng" hoặc "ảnh đã lưu", không bao giờ ghi là chạy trực tiếp.

## 6. Giọng văn

- Tiêu đề là mệnh đề ngắn, chữ thường, nêu **kết luận** ("Thành công chỉ khi hai camera cùng đồng ý"), không phải nhãn trống.
- Eyebrow đánh số và đặt tên phần: `03 · CÁCH HỆ THỐNG NHÌN`.
- Số thập phân dùng dấu phẩy (2,8 cm; 29,7 cm); độ `85°`; đơn vị cách số một khoảng trắng (`20 mm`).
- Nói thẳng điều chưa làm (nhãn đất nung "CHƯA KIỂM CHỨNG"), như slide Gamota ghi "CHƯA ĐẠT".
- Ghi chú diễn giả có đúng ba phần: lời nói (văn nói, "nhóm em"); đoạn **"Nếu được hỏi:"**; dòng **"Nguồn:"** dẫn file và dòng.
- Không emoji, không clip art, không icon kho, không gradient, không quá ba màu nhấn trên một slide.

## 7. Mã mẫu chạy được

`assets/reference/sample_slides_body.js` là bản cài đặt **đã dựng và đã xem trên PDF** của năm slide khó nhất: slide 3 (P13), slide 7 (P14), slide 9 (P17), slide 10 (P11), slide 18 (P15).
Nối sau `gamota_helpers.js` rồi chạy `node` để xem; sao chép và chỉnh các khối vào `build/build_deck.js`. Văn bản trong mẫu là văn bản trên slide ở `01_KICH_BAN_SLIDE.md`.

