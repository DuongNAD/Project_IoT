# 01 · Kịch bản slide: Cánh tay robot 4 servo, hai camera chỉ bạn bấm phím gì

Dành cho **Antigravity dựng PPTX** và cho **bạn duyệt lời nói**. Slide kiểu Gamota: một ý mỗi slide, số liệu lớn, ảnh thật trong thẻ ngà,
lời nói đầy đủ nằm trong ghi chú. Bản này viết theo mã nguồn **sau khi đơn giản hóa** (02/11 ≈ 23:00): hai nhóm nối nhau,
`control.py` (nhóm 1 · điều khiển) → `success.py` (nhóm 2 · success). Bản cũ (5 bước, S1/S2, Auto-Step) **không còn** trong deck, trừ phụ lục I.

**Quy ước**

- Khổ 16:9 (13,333 × 7,5 in). **14 slide chính** (nói đủ lời ≈ 15 phút, rút gọn còn ≈ 12 phút: xem bảng) + **11 phụ lục A–K** (để hỏi đáp) = **25 slide**. Slide 10 có thể kèm video.
- `[…]` là chỗ bạn phải điền: **giữ nguyên dấu ngoặc vuông trên slide** để dễ thấy và để `tools/qa_deck.py` liệt kê.
- `real/xxx` là ảnh trong `assets/real/` (đã cắt, làm mờ màn hình laptop). `ai/xxx` là ảnh AI trong `assets/ai/` (tạo theo `03_PROMPT_ANH_AI.md`).
- "Mẫu P…" là mẫu bố cục trong `06_PHONG_CACH.md` (có tọa độ). Màu: xanh = code/bằng chứng có thật, đất nung = phần cứng/rủi ro/chưa kiểm chứng, chàm = YOLO11 (tùy chọn), xám ấm = trung tính.
- Mọi con số lấy từ `05_SO_LIEU_VA_NGUON.md`. **Không thêm số mới, không viết điều ở mục "CẤM NÓI".**
- Mỗi slide có: **Hiển thị** (chữ đặt lên slide, đúng từng chữ) và **Ghi chú diễn giả** (đặt vào notes của PPTX: *lời nói*, đoạn **Nếu được hỏi:**, dòng **Nguồn:**).
- Ảnh `ui_screen_before` / `ui_screen_done` là **màn hình thật của chương trình chạy trên ảnh camera thật đã lưu, cánh tay mô phỏng**: luôn kèm chú thích đó, không bao giờ gọi là "chạy trực tiếp".

## Mạch kể chuyện

| # | Phần | Slide | Ý chính | Phút (nói đủ lời) | Người nói |
|---|---|---|---|---|---|
| 1 | Mở đầu | 1 Bìa | đề tài và lộ trình bài nói | 0:40 | […] |
| 2 | Bài toán | 2 | ba câu hỏi trước mỗi lần gắp | 0:45 | […] |
| 3 | Hệ thống | 3, 4 | hai nhóm nối nhau qua một `Plan`; phần cứng thật | 2:00 | […] |
| 4 | Hệ thống nhìn | 5, 6 | tờ A4 thành thước đo; tìm vật bằng màu | 2:05 | […] |
| 5 | Nhóm 1 · điều khiển | 7, 8 | động học ngược; màn hình chỉ nói bấm phím gì | 2:30 | […] |
| 6 | Nhóm 2 · success | 9 | ba servo tới góc gợi ý, giữ một giây | 1:25 | […] |
| 7 | Thử thật và sự cố | 10, 11, 12 | kẹp bằng phím; mô hình lệch và hiệu chỉnh; servo nóng | 3:55 | […] |
| 8 | Trung thực | 13, 14 | đã có / chưa kiểm chứng; tóm lại | 2:05 | […] |
| | **Tổng** | | | **≈ 15:30** | demo trực tiếp thêm 2–3 phút nếu có |
| 9 | Phụ lục | 15–25 | dự phòng cho câu hỏi | | |

Cách tính: phần **lời nói** (trước đoạn "Nếu được hỏi") của 14 slide dài ≈ 3 100 từ; ở tốc độ ≈ 200 từ/phút (ước lượng, đo lại bằng cách đọc thử) là ≈ 15 phút.
**Muốn còn ≈ 12 phút** (gợi ý, chưa đọc thử): ở slide 4, 6, 12 chỉ nói câu đầu của mỗi đoạn (≈ −1:30); ở slide 11 bỏ đoạn "Nguyên nhân" (≈ −0:30); ở slide 5 bỏ đoạn "Có một chi tiết nhóm phải sửa" (≈ −0:40); slide 13 chỉ đọc hai ô số (≈ −0:40).

---

## Slide 1 · Bìa
**Master** `PLAIN` · **Mẫu** P1 · **Hình** `real/demo_06_grip_side.jpg` (thẻ trên), `real/demo_06_grip_top.jpg` (thẻ dưới)

**Hiển thị**
- Nhãn (teal): `ĐỒ ÁN IOT · [TÊN MÔN HỌC] · [NGÀY THUYẾT TRÌNH]`
- Tiêu đề (2 dòng): `Cánh tay robot 4 servo` / `hai camera chỉ bạn bấm phím gì`
- Phụ đề: `Từ ảnh camera đến phím cần bấm, rồi kiểm tra ba servo đã tới góc chưa`
- Tác giả: `Nguyễn Anh Dương` · dòng nhỏ: `[TÊN THÀNH VIÊN 2] · [TÊN THÀNH VIÊN 3] · [TÊN NHÓM]`
- Chú thích dưới thẻ ảnh dưới (11 pt, nằm trong panel): `Ảnh thật: cam NGANG (trên) và cam TRÊN (dưới), 02/11/2026 20:32:52`

**Ghi chú diễn giả**

Em chào thầy cô và các bạn. Nhóm em làm đề tài cánh tay robot bốn servo, có hai camera nhìn giúp.

Bài nói khoảng mười lăm phút, gồm tám phần. Một là bài toán. Hai là hệ thống. Ba là hệ thống nhìn tờ giấy và tìm vật. Bốn là nhóm một, phần điều khiển: từ vị trí vật tính ra phím cần bấm. Năm là nhóm hai, phần success: ba servo đã tới góc gợi ý chưa. Sáu là thử trên cánh tay thật. Bảy là những sự cố nhóm đã gặp. Tám là những điều nhóm chưa kiểm chứng. Cuối cùng là demo và hỏi đáp.

Hai ảnh bên phải là ảnh thật, chụp từ hai camera của hệ thống lúc cánh tay đang kẹp cốc, không phải ảnh dựng.

**Nếu được hỏi:** ai làm phần nào trong nhóm? […điền phân công; nhóm một là điều khiển, nhóm hai là success].

**Nguồn:** ảnh `demo_06_grip_side`, `demo_06_grip_top`: khung cắt từ video buổi thử 02/11/2026 lúc 20:32:52.

---

## Slide 2 · 01 · Bài toán
**Master** `CONTENT` · **Mẫu** P2 (ba hàng; chip rộng 1,9 tại `x 5,8`, câu hỏi `w 4,0`) · **Hình** `ai/ai_01_problem_depth.png` (vuông 2,0 in trong thẻ phải)

**Hiển thị**
- Eyebrow: `01 · BÀI TOÁN` · Tiêu đề: `Ba câu hỏi trước mỗi lần gắp`
- Nhãn trái: `TRƯỚC MỖI LẦN GẮP`
- Ba hàng (dot 1–3, chip bên phải):
  1. `Vật đang ở đâu trên bàn?` · chip `ARUCO · MÀU`
  2. `Ba servo phải ở góc nào, bấm phím nào mấy lần?` · chip `NHÓM 1 · ĐIỀU KHIỂN`
  3. `Đã tới đúng góc chưa?` · chip `NHÓM 2 · SUCCESS`
- Thẻ phải (`orangeSoft`): nhãn `KHÓ Ở ĐÂU`; ảnh AI vuông 2,0 in; chú thích `Minh họa (AI)`; ba dòng 14 pt: `Mỗi phím chỉ nhích 2°` · `Mắt người khó ước lượng độ sâu` · `Mô hình hình học phải khớp cánh tay thật`
- Chân trang (12 pt, `muted`): `Cánh tay: Arduino Uno + PCA9685 + 4 servo MG996R · Phím: A D / W S / I K / J L, mỗi phím 2° (kẹp 5°)`

**Ghi chú diễn giả**

Bài toán rất cụ thể. Cánh tay của nhóm có bốn servo, điều khiển bằng bàn phím, mỗi lần bấm một phím thì một servo nhích hai độ. Trước mỗi lần gắp, người điều khiển phải tự trả lời ba câu hỏi: vật đang ở đâu trên bàn; ba servo phải ở góc nào và phải bấm phím nào, mấy lần; và đã tới đúng góc chưa.

Khó nhất là mắt người khó ước lượng độ sâu, và nếu mô hình hình học không khớp cánh tay thật thì gợi ý nào cũng lệch. Hệ thống của nhóm trả lời đúng ba câu hỏi này, mỗi câu bằng một thành phần riêng: phần nhìn trả lời câu một, nhóm một trả lời câu hai, nhóm hai trả lời câu ba.

Ảnh minh họa bên phải do AI tạo, chỉ để hình dung cái khó, không phải ảnh thật.

**Nếu được hỏi:** vì sao không làm tự động hoàn toàn? Vì mô hình hình học chỉ khớp cánh tay thật cỡ một vài xăng-ti-mét (slide 11) và kẹp chưa giữ chắc cốc thon (slide 9), nên nhóm chọn hướng hỗ trợ người điều khiển: màn hình chỉ cho biết bấm phím nào, người bấm. Nhóm cũng từng có chế độ tự gửi phím, nhưng đã bỏ để mã giải thích được trong một phút (phụ lục I).

**Nguồn:** `README.md` mục 3; `control.py`; `success.py`.

---

## Slide 3 · 02 · Hệ thống
**Master** `CONTENT` · **Mẫu** P13 (sơ đồ hai hàng, **mẫu mới**: xem `assets/reference/sample_slides_body.js`) · **Hình** không có ảnh; vẽ bằng hình gốc của PPTX

**Hiển thị**
- Eyebrow: `02 · HỆ THỐNG` · Tiêu đề: `Hai camera nhìn, nhóm 1 tính, nhóm 2 kiểm`
- Hàng 1, năm ô (rộng 1,85, khe 0,62, `y 2,55`, cao 1,3), mỗi ô: nhãn nhỏ 10 pt hoa, tiêu đề 14 pt, mô tả 11 pt:
  1. xám ấm `NEUTRAL`: `CẢM BIẾN` / `2 camera + tờ A4` / `OBSBOT TRÊN · MacBook NGANG · 4 mã ArUco`
  2. xanh `CODE`: `NHÌN` / `Tìm vật trên giấy` / `ArUco → homography; tách màu → (X, Y) cm · vision.py`
  3. xanh `CODE`, viền đậm, dot **1** ở góc trên phải: `NHÓM 1` / `Điều khiển` / `vật → góc 3 servo → phím cần bấm · control.py`
  4. xanh `CODE`, viền đậm, dot **2** ở góc trên phải: `NHÓM 2` / `Success` / `3 servo tới góc chưa? đếm số lần · success.py`
  5. xanh `CODE`: `MÀN HÌNH` / `Lệnh + XONG` / `2 camera, lệnh to, kết luận · screen.py`
- Mũi tên giữa các ô hàng 1 (nhãn 10 pt `muted`): 1→2 `ảnh` / `1920×1080`; 2→3 `(X, Y)` / `cm`; 3→4 **mũi tên dày** nhãn đậm `Plan`; 4→5 `Result`
- Vòng người (3 đoạn thẳng, mũi tên ở cuối): từ đỉnh ô 5 lên `y 2,2`, sang trái tới đỉnh ô 3, xuống ô 3; nhãn 11 pt trên đoạn ngang: `người nhìn màn hình rồi bấm phím`
- Hàng 2, ba ô đất nung `HW` (`y 4,45`, cao 1,1) dưới ô 3, 4, 5: `Arduino Uno` / `nhận phím, gửi JSON` · `PCA9685` / `I²C 0x40 · xung 50 Hz` · `4 servo MG996R` / `đế · vai · khuỷu · kẹp`; mũi tên ngang nối ba ô; hai mũi tên dọc giữa ô 3 và Arduino: xuống `phím · USB 9600 baud`, lên `JSON ~5 gói/giây`
- Thẻ trái hàng 2 (`card`, `x 0,8 · w 4,45 · y 4,45 · h 1,1`): nhãn `CHỈ MỘT ĐỐI TƯỢNG NỐI HAI NHÓM`; `Plan = góc hiện tại · góc cần tới · 3 lệnh bấm. Nhóm 1 sinh ra, nhóm 2 đọc.`
- Dải dưới (`bg2`, `y 5,95 · h 0,65`): nhãn `VÌ VẬY` + ba mục đánh số 12 pt: `Người bấm phím, hệ thống gợi ý` · `Hai nhóm làm riêng được, chỉ chung một Plan` · `Kiểm được từng bước: 109 test`
- Chân trang (chú giải màu, 11 pt, `y 6,75`): ô xanh `Code tất định` · ô đất nung `Phần cứng` · ô xám `Trung tính`; dòng nhỏ bên phải: `Nguồn tổ ong 5–6 V riêng vào PCA9685, không lấy từ USB`

**Ghi chú diễn giả**

Đây là toàn bộ hệ thống trên một trang, đọc từ trái sang phải.

Ô đầu là cảm biến: hai camera cùng quay tờ giấy A4. Camera trên là OBSBOT treo phía trên nhìn xuống, dùng để tính vật nằm ở đâu. Camera ngang là camera MacBook đặt thấp phía trước, để người điều khiển nhìn độ cao và độ sát của hai ngón kẹp; nó cũng có lưới tọa độ trên tờ giấy.

Ô thứ hai là phần nhìn: dò bốn mã ArUco để đổi pixel sang xăng-ti-mét, rồi tìm vật bằng cách tách màu, ra vị trí X, Y của vật.

Hai ô tiếp theo là điểm chính của thiết kế. Nhóm một lo điều khiển: biết vật ở đâu thì tính ra ba servo cần ở góc nào, rồi lập danh sách phím cần bấm. Nhóm hai lo success: chỉ trả lời một câu, ba servo đã tới góc đó chưa. Hai nhóm chỉ nói chuyện với nhau qua một đối tượng duy nhất tên là Plan, nên có thể làm riêng và kiểm riêng.

Ô cuối là màn hình. Người nhìn màn hình rồi bấm phím trên laptop, như vòng mũi tên phía trên cho thấy. Phím đi qua laptop xuống Arduino qua cáp USB, chín nghìn sáu trăm baud; Arduino điều khiển bốn servo qua mạch PCA9685 và gửi ngược lên gói JSON chứa bốn góc servo, khoảng năm gói mỗi giây. Đó là phần IoT của hệ thống.

**Nếu được hỏi:** người nằm ở đâu trong vòng này? Người nhìn lệnh trên màn hình rồi bấm phím; chương trình không tự gửi phím. Có Bluetooth không? Firmware có sẵn đường nhận phím từ module HC-05 ở chân D2, D3, nhưng nhóm điều khiển chủ yếu qua cáp USB.

**Nguồn:** `README.md` (sơ đồ đầu trang, mục 1 và 3); `main.py:171-174`; `robot_arm_4dof.ino:6,8,86,203-207`; `control.py:251-468`.

---

## Slide 4 · 02 · Phần cứng
**Master** `CONTENT` · **Mẫu** P12 · **Hình** `real/hw_overview_top.jpg`, `real/hw_overview_side.jpg`, `real/hw_electronics.jpg`, `real/hw_arm_gripper.jpg`

**Hiển thị**
- Eyebrow: `02 · PHẦN CỨNG` · Tiêu đề: `Phần cứng: Arduino Uno, PCA9685 và bốn servo MG996R`
- Bốn ảnh, chú thích dưới ảnh: `Cam TRÊN (OBSBOT) nhìn xuống` · `Cam NGANG (MacBook) đặt thấp` · `Arduino Uno + PCA9685 + nguồn tổ ong` · `Cánh tay 4 servo, tay kẹp hai ngón`
- Cột phải: nhãn `SERVO · PHÍM · GIỚI HẠN`, bốn hàng (chip + chữ): `KÊNH 0 · ĐẾ · A / D · 0–180°` · `KÊNH 1 · VAI · W / S · 25–155°` · `KÊNH 2 · KHUỶU · I / K · 25–155°` · `KÊNH 3 · KẸP · J / L · 95–160°`
- Dưới bảng, ba dòng 13 pt: `Mỗi phím nhích 2° (kẹp: 5°)` · `Nguồn riêng 5–6 V vào cổng xanh của PCA9685, không lấy từ USB` · `HC-05 Bluetooth (D2/D3): firmware có sẵn, tùy chọn`

**Ghi chú diễn giả**

Phần cứng gồm ba khối. Khối điều khiển là Arduino Uno cộng mạch PCA9685 sinh xung cho servo, trong ảnh cận cảnh bên dưới. Khối chấp hành là cánh tay bốn bậc tự do dùng servo MG996R: kênh không là đế, kênh một là vai, kênh hai là khuỷu, kênh ba là tay kẹp. Khối cảm biến là hai camera.

Mỗi servo có giới hạn cứng trong firmware. Mỗi lần bấm một phím, đế, vai và khuỷu nhích hai độ để căn cho chính xác, còn tay kẹp nhích năm độ. Điểm cần nhớ về nguồn: servo lấy điện từ nguồn tổ ong riêng năm đến sáu vôn cấp vào cổng xanh của PCA9685, không lấy từ cổng USB của laptop.

Bốn ảnh ở đây đều là ảnh thật. Hai ảnh trên là hai camera của hệ thống nhìn cùng một cảnh.

**Nếu được hỏi:** tay kẹp có mấy ngón? Hai ngón, cơ cấu song song, một servo. Vì sao giới hạn kẹp là 160 độ? Xem slide 12 và phụ lục D. Có phản hồi vị trí không? Không: MG996R ở đây chỉ nhận lệnh góc, Arduino báo lại góc đã ra lệnh (xem slide 9).

**Nguồn:** `README.md` mục 1; `robot_arm_4dof.ino:6,8,13-14,19-21,121-152`; `control.py:57-63`.

---

## Slide 5 · 03 · Cách hệ thống nhìn
**Master** `CONTENT_ALT` · **Mẫu** hai ảnh + bốn ý · **Hình** `real/sw_annot_top.jpg` (trái), `real/sw_annot_side.jpg` (phải)

**Hiển thị**
- Eyebrow: `03 · CÁCH HỆ THỐNG NHÌN` · Tiêu đề: `Bốn mã ArUco biến tờ A4 thành hệ tọa độ tính bằng cm`
- Hai ảnh cạnh nhau, mỗi ảnh `w 3,8` (16:9) tại `y 2,0`; chú thích: `Cam TRÊN: lưới 5 cm dựng từ 4 mã; vòng xanh quanh cốc ghi tọa độ (16,5; 13,8) cm` · `Cam NGANG: cùng tờ giấy nhìn nghiêng, cùng lưới`
- Bốn cột ý (dot + tiêu đề 15 pt + mô tả 12,5 pt) tại `y 4,8`, mỗi cột `w 2,7`:
  1. `4 mã ở 4 góc` / `ArUco DICT_4X4_50, ID 0–3, cạnh 2,8 cm; in A4 đúng 100%`
  2. `Homography` / `pixel ↔ cm cho cả hai camera; gốc ở mã ID 0, X dài 29,7 cm, Y rộng 21,0 cm`
  3. `Che mất mã vẫn chạy` / `dùng vị trí đã nhớ; xô camera hoặc giấy thì quên và học lại (phím U)`
  4. `Sửa lệch phối cảnh` / `cam TRÊN treo cao ≈ 46 cm: nắp cốc cao 5 cm hiện lệch ≈ 1 cm; sau sửa hai camera chỉ lệch nhau 0,2 cm`
- Chân trang: `Ảnh thật: chương trình vẽ lưới lên khung hình camera thật đã lưu (không phải dựng)`

**Ghi chú diễn giả**

Điều đầu tiên hệ thống phải biết là vật nằm ở đâu, tính bằng xăng-ti-mét. Nhóm không đo thước cho từng camera, mà in một tờ A4 có bốn mã ArUco ở bốn góc. Mã ArUco là mã vuông đen trắng, mỗi mã có số định danh, và OpenCV tìm được bốn góc của mã.

Biết bốn góc ngoài đời cách nhau hai mươi chín phẩy bảy nhân hai mươi mốt xăng-ti-mét, chương trình tính một phép biến đổi phẳng gọi là homography, đổi từng pixel sang tọa độ trên tờ giấy, cho cả hai camera. Gốc tọa độ ở mã số không, trục X chạy sang mã số một, trục Y chạy sang mã số ba. Che mất một hai mã thì chương trình dùng vị trí đã nhớ.

Có một chi tiết nhóm phải sửa: camera trên treo cao khoảng bốn mươi sáu xăng-ti-mét nhìn xuống, nên nắp cốc cao năm xăng-ti-mét bị đẩy ra xa tâm ảnh khoảng một xăng-ti-mét so với đáy cốc. Nhóm sửa bằng một công thức tỉ lệ theo độ cao vật. Ở một vị trí cốc đã đo, hai camera lệch nhau một phẩy hai xăng-ti-mét trước khi sửa và còn không phẩy hai sau khi sửa.

Hai ảnh là ảnh thật do chương trình vẽ lưới lên khung hình thật đã lưu.

**Nếu được hỏi:** vì sao ArUco? Vì mã có số định danh, cho bốn góc rõ ràng, chịu được nhìn nghiêng, và OpenCV có sẵn. Tờ giấy là hệ quy chiếu chung cho cả hai camera, nên đổi camera hay đổi chỗ đặt không phải đo lại bằng thước. Độ cao bốn mươi sáu xăng-ti-mét đo thế nào? Ước từ ảnh, chưa đo bằng thước; con số hai mươi hai không phẩy hai chỉ là một phép đo.

**Nguồn:** `generate_aruco_a4.py:3,31-36`; `vision.py:24-30,152-170,486-505,557-562`; `tests/test_vision.py:223-243`; `README.md` mục 4.

---

## Slide 6 · 03 · Nhận diện vật
**Master** `CONTENT` · **Mẫu** ba thẻ + ảnh · **Hình** `real/ui_guide_cameras.png`

**Hiển thị**
- Eyebrow: `03 · NHẬN DIỆN VẬT` · Tiêu đề: `Tìm vật bằng màu; YOLO chỉ là tùy chọn`
- Ba thẻ `w 3,7`, `y 1,95`, `h 2,6`:
  1. (xanh `CODE`) nhãn `TÁCH MÀU TRÊN GIẤY TRẮNG` · chip `MẶC ĐỊNH` · `Dựng ảnh phẳng của tờ A4 rồi tách vật có màu đậm (cốc đỏ). Bỏ khối rộng > 8 cm, dài > 18 cm, chạm mép giấy hoặc dính phần đen của cánh tay: bàn tay không bị nhận thành vật.`
  2. (xanh `CODE`) nhãn `MÃ ARUCO ID 10–29` · chip `CHẮC NHẤT` · `Dán lên vật. Cho vị trí; kích thước tra bảng OBJECT_SPECS.`
  3. (chàm `YOLO`) nhãn `YOLO11 (COCO)` · chip `TÙY CHỌN · --yolo` · `Nhận tên vật. Trọng số có sẵn, chưa fine-tune. Bỏ 12 lớp không phải vật cần gắp; vật YOLO tìm ra cũng phải có màu.`
- Dưới trái: ảnh `ui_guide_cameras.png` (`w 6,5 · h 1,94` tại `x 0,8 · y 4,75`), chú thích: `Ảnh chụp màn hình bản TRƯỚC khi đơn giản hóa (02/11, 20:32): YOLO gọi chi tiết robot là bottle, airplane, frisbee`
- Dưới phải: ô đất nung (`x 7,6 · w 4,93 · y 4,75 · h 1,94`): nhãn `VÌ SAO YOLO TẮT MẶC ĐỊNH` + `YOLO bản COCO hay gọi nhầm bộ phận robot (xem ảnh). Bản hiện tại tắt YOLO, chỉ nhận vật có màu và chọn vật bằng phím TAB.`

**Ghi chú diễn giả**

Biết tờ giấy rồi thì phải tìm vật. Nhóm có ba cách, từ mặc định tới tùy chọn.

Cách mặc định là tách màu trên nền giấy trắng: chương trình dựng ảnh phẳng của tờ A4 rồi tách vật có màu đậm, như cốc đỏ, không cần mã. Có một việc nhỏ nhưng quan trọng: bàn tay người đưa vào tờ giấy không được bị nhận thành vật. Bộ tách màu bỏ qua khối rộng hơn tám xăng-ti-mét, dài hơn mười tám, chạm mép giấy, hoặc dính vào phần đen của cánh tay.

Cách chắc nhất là dán mã ArUco số mười tới hai mươi chín lên vật; mã cho vị trí, kích thước tra trong một bảng.

Cách thứ ba là YOLO11, bản đã huấn luyện sẵn trên bộ COCO, nhóm chưa huấn luyện lại, và nó là tùy chọn, phải bật bằng tham số riêng. Lý do: như trong ảnh chụp màn hình của bản trước, YOLO đôi lúc gọi chi tiết của robot là chai hay máy bay, và gọi nắp cốc là đĩa ném. Vì vậy bản hiện tại tắt YOLO mặc định, chỉ nhận vật có màu, và người điều khiển chọn vật bằng phím TAB.

**Nếu được hỏi:** có huấn luyện YOLO không? Chưa; fine-tune cho vật thật là việc có thể làm sau. Vì sao còn giữ YOLO? Để nhận tên vật khi cần; còn vị trí xăng-ti-mét luôn tính từ homography của tờ giấy. Ảnh chụp màn hình lấy ở đâu? Từ giao diện cũ trước khi đơn giản hóa; hiện tượng nhận nhầm là có thật và là lý do YOLO bị tắt.

**Nguồn:** `main.py:53`; `vision.py:43-47,271-300,365-368,476-486,491-492,507-515`; ảnh `ui_guide_cameras` (bản trước khi đơn giản hóa).

---

## Slide 7 · 04 · Nhóm 1 · Điều khiển
**Master** `CONTENT` · **Mẫu** P14 (sơ đồ) + bốn bước · **Hình** vẽ bằng hình gốc, không dùng ảnh

**Hiển thị**
- Eyebrow: `04 · NHÓM 1 · ĐIỀU KHIỂN` · Tiêu đề: `Từ vị trí (X, Y) của vật tính ra góc ba servo`
- Sơ đồ trái (P14), chú thích dưới sơ đồ: `Mô hình mặc định: tư thế servo 90° / 90°, số đo thước theo ARM_CONFIG (mm)`
- Cột phải (`x 7,3 · w 5,23`), bốn bước có dot:
  1. `Đổi (X, Y) cm trên giấy sang tọa độ robot (mm) theo vị trí và hướng của đế`
  2. `Đế: θ₁ = atan2(y, x)`
  3. `Vai và khuỷu: giải tam giác hai khâu; chọn nghiệm khuỷu hướng lên`
  4. `Đổi ra góc servo, làm tròn bội số 2°; trừ góc hiện tại: số lần bấm = độ lệch ÷ 2°`
- Thẻ ví dụ (`card`, `y 5,45 · h 1,2`, dưới cột phải): nhãn `VÍ DỤ: CỐC Ở (20,1; 7,4) CM`; số lớn 22 pt teal `đế 74° · vai 58° · khuỷu 90°`; dòng nhỏ 11 pt `từ Home 90/90/90: phím D × 8, phím S × 16, khuỷu đã đúng · mô hình đã hiệu chỉnh (slide 11)`

**Ghi chú diễn giả**

Biết vật ở (X, Y), nhóm một phải tính ba servo cần ở góc nào. Đây là bài toán động học ngược.

Cánh tay nhìn ngang như hình: trục vai cao bảy mươi mi-li-mét so với mặt bàn, khâu vai dài một trăm linh năm, khâu khuỷu dài một trăm, và tâm hai ngón kẹp lệch sáu mươi lăm ra trước, hai mươi lăm xuống dưới. Đó là số nhóm đo bằng thước, cho mô hình mặc định. Sau khi thử trên cánh tay thật, các số này được hiệu chỉnh, ở slide mười một.

Bước một, đổi tọa độ trên giấy sang tọa độ robot theo vị trí và hướng của đế. Bước hai, góc đế bằng a-tan-hai của y trên x. Bước ba, vai và khuỷu giải tam giác hai khâu, chọn nghiệm khuỷu hướng lên. Bước bốn, đổi sang góc servo, làm tròn về bội số của hai độ cho khớp với phím bấm, rồi trừ góc hiện tại: độ lệch chia hai là số lần phải bấm.

Ví dụ với cốc ở hai mươi phẩy một và bảy phẩy bốn xăng-ti-mét, mô hình đã hiệu chỉnh gợi ý đế bảy mươi bốn, vai năm mươi tám, khuỷu chín mươi độ. Xuất phát từ Home, khi ba servo đều ở chín mươi độ, đế cần giảm mười sáu độ, tức bấm D tám lần; vai giảm ba mươi hai độ, tức bấm S mười sáu lần; khuỷu đã đúng. Cánh tay chỉ có bốn servo, không có cổ tay, nên hướng ngón kẹp không chọn được.

**Nếu được hỏi:** công thức có được kiểm lại không? Có: trong bộ test, chương trình đưa kết quả động học ngược vào động học thuận trên hơn một trăm điểm trong tầm với và thấy sai số dưới không phẩy một mi-li-mét. Vì sao nghiệm khuỷu hướng lên? Tam giác hai khâu có hai nghiệm; code luôn chọn khuỷu hướng lên để mỗi điểm chỉ có một bộ góc. Vì sao trái phải ngược với hướng nhìn của robot? Màn hình dùng hướng nhìn theo camera MacBook đặt đối diện robot: A sang phải, D sang trái.

**Nguồn:** `control.py:36-67,98-161,174-195,221-245`; `tests/test_control.py:16-32`; `05_SO_LIEU_VA_NGUON.md` mục 3 và 16.

---

## Slide 8 · 04 · Màn hình hai phần
**Master** `CONTENT` · **Mẫu** ảnh trái + danh sách phải · **Hình** `real/ui_screen_before.png` (`w 7,4`, tỉ lệ gốc, `x 0,8 · y 1,95`)

**Hiển thị**
- Eyebrow: `04 · MÀN HÌNH HAI PHẦN` · Tiêu đề: `Màn hình chỉ nói một việc: bấm phím nào, mấy lần`
- Chú thích dưới ảnh (11 pt): `Màn hình thật của chương trình, chạy trên ảnh camera thật đã lưu; cánh tay mô phỏng (chân trang: USB Arduino: MO PHONG). Chữ không dấu do OpenCV.`
- Cột phải (`x 8,5 · w 4,03`): nhãn `HAI PHẦN NỐI NHAU`, ba hàng có dot:
  1. `Phần 1 · điều khiển: phím to, số lần, sang trái hay phải bao nhiêu độ`
  2. `Phần 2 · success: CHƯA XONG còn N lần bấm, hoặc XONG!`
  3. `Trái / phải nhìn theo cam NGANG (MacBook): A sang phải, D sang trái`
- Dưới đường kẻ: `A D đế · W S vai · I K khuỷu · mỗi lần 2°` · chip đất nung `CHẠY TRÊN ẢNH ĐÃ LƯU · CÁNH TAY MÔ PHỎNG`

**Ghi chú diễn giả**

Đây là màn hình của chương trình. Nhóm chụp nó khi chạy trên ảnh camera thật đã lưu và cánh tay ở chế độ mô phỏng, nên chân trang ghi USB Arduino: mô phỏng. Hai khung camera ở trên cho thấy lưới tọa độ, vòng DICH quanh cốc và dấu KEP là chỗ đầu kẹp theo mô hình.

Bên dưới là hai phần nối nhau bằng một mũi tên, giống hai nhóm làm hai việc. Phần một là điều khiển, vẽ từ Plan của nhóm một: một dòng chữ to; ví dụ trong ảnh, cốc ở mười sáu phẩy năm và mười ba phẩy tám xăng-ti-mét, lệnh là bấm S mười lăm lần, hạ vai ba mươi độ, còn mười tám lần bấm. Ba hàng bên dưới là ba servo: góc hiện tại đi tới góc đích; hàng nào đã đúng thì ghi ĐÃ ĐÚNG, như hàng đế: lệch hai độ là đủ. Phần hai là success, vẽ từ kết quả của nhóm hai: chưa xong, còn bao nhiêu lần bấm; hoặc XONG.

Chữ trên giao diện không có dấu vì thư viện vẽ chữ của OpenCV không vẽ được dấu tiếng Việt. Về hướng: trái và phải nhìn theo camera MacBook, đặt phía trước robot; vì thế phím A quay đế sang phải, phím D sang trái, ngược với hướng nhìn của chính robot. Màn hình chỉ cho biết phải bấm gì; người điều khiển là người bấm.

**Nếu được hỏi:** có tự gửi phím không? Không; chương trình chỉ gửi phím khi người bấm. Vì sao chỉ một lệnh to? Để người điều khiển làm theo được ngay, không phải đọc bảng số. Vì sao thứ tự đế, rồi vai, rồi khuỷu? Là thứ tự code lập lệnh; hàng nào đã đúng thì được bỏ qua. Ảnh camera là ảnh cũ mà vẫn có gợi ý? Ảnh là khung camera thật lúc hai mươi giờ hai mươi bảy, chương trình đọc nó như camera đang chạy, còn cánh tay mô phỏng đặt ở Home. Ảnh chụp lúc tờ giấy còn hướng ban đầu, còn file hiệu chỉnh ghi theo tờ đã xoay một trăm tám mươi độ, nên khi tạo ảnh nhóm đổi đế về hệ lúc chụp rồi tự kiểm. Gợi ý trên ảnh này là đế 88, vai 60, khuỷu 84, gần tư thế người thật sự ôm cốc lúc hai mươi giờ ba mươi hai, khoảng 85, 60, 90 (đọc từ màn hình bản cũ); nhưng chưa rõ lần ôm đó có nằm trong mười mẫu khớp hay không, nên chỉ nói là gần.

**Nguồn:** `screen.py:157-239,249-259`; `main.py:155-180`; `control.py:211-217`; ảnh `ui_screen_before` (tạo bằng `tools/make_screen_images.py`).

---

## Slide 9 · 05 · Nhóm 2 · Success
**Master** `CONTENT` · **Mẫu** ba số lớn + ảnh phải + hai thẻ rủi ro · **Hình** `real/ui_screen_done.png` (`w 5,13`, `x 7,4 · y 1,95`)

**Hiển thị**
- Eyebrow: `05 · NHÓM 2 · SUCCESS` · Tiêu đề: `Xong khi cả ba servo tới góc gợi ý và giữ yên một giây`
- Trái (`x 0,8 · w 6,3`), ba hàng cao 1,1 tại `y 1,95 / 3,15 / 4,35`: số lớn 36 pt teal + mô tả 14 pt:
  - `± 2°` · `mỗi servo lệch không quá một bước bấm so với góc gợi ý (lệch 3° là chưa)`
  - `3 servo` · `đế, vai, khuỷu; kẹp không tính`
  - `1 s` · `giữ đúng liên tục đủ một giây mới đếm thêm một lần thành công`
- Phải: ảnh `ui_screen_done.png`; chú thích 11 pt: `Mô phỏng: bấm đủ phím theo lệnh thì phần 2 báo XONG! và đếm 1 lần (ảnh camera thật đã lưu)`
- Dưới (`y 5,4`, hai thẻ `orangeSoft` cao 1,1, `w 5,7` mỗi thẻ):
  - nhãn `VÌ SAO KẸP KHÔNG TÍNH` + `Cốc thon dần xuống đáy nên hai ngón đẩy cốc ra ở 150–160°; cốc đổ khoảng 3 lần trong buổi thử. Đề tài chỉ cần ba góc servo.`
  - nhãn `GIỚI HẠN CỦA CHỮ XONG` + `Góc servo là góc lệnh Arduino báo lại; MG996R không báo vị trí thật. XONG = phím đã bấm đủ, chưa phải đã đo thấy kẹp sát cốc.`
- Chân trang (`y 6,7`): chip teal `ĐÃ KIỂM BẰNG TEST: 7 TEST SUCCESS + CHUỖI ĐẦU–CUỐI` · chip đất nung `CHƯA CÓ LẦN ĐẾM NÀO TRÊN CÁNH TAY THẬT`

**Ghi chú diễn giả**

Nhóm hai chỉ trả lời một câu hỏi: ba servo đế, vai, khuỷu đã tới góc mà nhóm một gợi ý chưa. Nhóm hai không biết gì về camera, về động học ngược hay cổng USB; nó chỉ đọc Plan do nhóm một đưa sang.

Quy tắc có ba điều. Một, mỗi servo lệch không quá một bước bấm, tức hai độ, là đã tới; lệch ba độ là chưa. Nhóm chọn hai độ vì mô hình hình học vốn chỉ chính xác cỡ đó, bắt căn đúng không độ chỉ làm người điều khiển đuổi theo nhiễu. Hai, chỉ tính ba servo của cánh tay, không tính tay kẹp. Ba, cả ba phải tới và giữ liên tục một giây thì mới đếm thêm một lần thành công; lướt qua rồi đi thì không đếm.

Vì sao không tính tay kẹp? Cốc nhóm dùng thon dần xuống đáy, nên khi khép hai ngón tới một trăm năm mươi đến một trăm sáu mươi độ, cốc bị đẩy ra như hạt dưa, và trong buổi thử cốc đổ khoảng ba lần. Nhóm quyết định đề tài chỉ xét ba góc servo.

Hai điều nhóm nói thẳng. Một, chữ XONG nghĩa là ba góc lệnh đã tới, vì MG996R không báo vị trí thật, Arduino chỉ báo lại góc mà nó đã ra lệnh; nó chưa phải bằng chứng đo được rằng hai ngón kẹp đang sát cốc. Hai, ảnh bên phải là mô phỏng: nhóm cho chương trình chạy trên ảnh thật đã lưu, bấm phím giả đủ số lần thì màn hình chuyển XONG. Trên cánh tay thật nhóm chưa có lần đếm nào cho bản này.

**Nếu được hỏi:** vì sao giữ một giây? Để lướt qua mục tiêu không bị tính là thành công. Có thể kiểm bằng camera không? Bản trước có làm, bằng hai tín hiệu từ hai camera; nhóm đã bỏ để mã đơn giản (phụ lục I). Đếm ở đâu? Ở dòng Thành công N lần trên phần hai; chưa ghi ra file.

**Nguồn:** `success.py:16-17,19,22-75`; `tests/test_success.py`; `tests/test_end_to_end.py:11-47`; `robot_arm_4dof.ino:70-83`; `README.md` mục 6; ảnh `ui_screen_done` (tạo bằng `tools/make_screen_images.py`).

---

## Slide 10 · 06 · Thử trên cánh tay thật
**Master** `CONTENT` · **Mẫu** P11 (hàng ảnh kể chuyện) · **Hình** hàng 1 (cam NGANG): `real/demo_06_grip_side.jpg`, `real/demo_07_carry_side.jpg`, `real/demo_08_place_side.jpg`; hàng 2 (cam TRÊN): `real/demo_06_grip_top.jpg`, `real/demo_07_carry_top.jpg`, `real/demo_08_place_top.jpg`. **Tùy chọn:** nếu có `assets/real/video/demo_gap.mp4` thì thêm video (khung đầu `demo_06_grip_side`) cạnh hàng ảnh, thu nhỏ hàng ảnh.

**Hiển thị**
- Eyebrow: `06 · THỬ TRÊN CÁNH TAY THẬT` · Tiêu đề: `Cốc đỏ được kẹp, chuyển sang trái và đặt xuống`
- Chip nhãn hàng: `CAM NGANG`, `CAM TRÊN`
- Nhãn dưới ba cột: `20:32:52 · KẸP` · `20:33:02 · CHUYỂN SANG TRÁI` · `20:33:12 · ĐẶT XUỐNG`
- Chân trang (`y 6,62`): chip đất nung `NGƯỜI BẤM PHÍM · KHÔNG TỰ ĐỘNG` (`x 0,8 · w 5,0`) + dòng 11 pt `muted` (`x 5,95 · w 6,58`): `02/11/2026 · khung cắt từ video, mỗi khung cách nhau 10 giây · cốc đổ khoảng 3 lần và được dựng lại bằng tay (phụ lục G)`

**Ghi chú diễn giả**

Đây là bằng chứng cánh tay thật làm được việc, và cũng là chỗ nhóm cần nói rõ nhất.

Ba cột là ba thời điểm cách nhau mười giây trong buổi thử ngày hai tháng mười một, hàng trên là camera ngang, hàng dưới là camera trên. Hai mươi giờ ba mươi hai phút năm mươi hai giây: cốc đỏ nằm giữa hai ngón kẹp. Mười giây sau: cốc đang được kẹp và chuyển sang bên trái tờ giấy. Mười giây nữa: cốc đã đặt xuống bên trái và cánh tay rút về. Nhóm làm vòng này nhiều lần.

Ba điều nhóm xin nói thẳng. Một, đây là người bấm phím nhìn hình hai camera, trên màn hình của bản trước khi đơn giản hóa; chưa phải tự động. Hai, trong buổi thử cốc bị đổ khoảng ba lần và nhóm dựng lại bằng tay; những khung đó ở phụ lục G. Ba, đây chưa phải số liệu về tỉ lệ thành công: nhóm chưa có tỉ lệ nào.

Góc servo lúc kẹp, đọc từ màn hình bản cũ: đế khoảng tám mươi lăm độ, vai sáu mươi đến sáu mươi lăm, khuỷu tám mươi lăm đến chín mươi, kẹp một trăm bốn mươi lăm đến một trăm năm mươi. Chính những lần cánh tay ôm cốc kiểu này là dữ liệu để nhóm hiệu chỉnh mô hình, ở slide kế tiếp.

**Nếu được hỏi:** có video không? […điền: có / không; nếu có thì chiếu đoạn 20–30 giây]. Kẹp có giữ chắc không? Không hẳn: cốc đổ khoảng ba lần, và các thử sau cho thấy cốc thon bị đẩy ra ở 150–160 độ (phụ lục G).

**Nguồn:** ảnh `demo_06`, `demo_07`, `demo_08` (khung cắt từ video 02/11/2026, 20:32:52 đến 20:33:12); ghi chú phiên thử 20:32–20:35; `05_SO_LIEU_VA_NGUON.md` mục 7.

---

## Slide 11 · 07 · Sự cố 1: mô hình lệch cánh tay thật
**Master** `CONTENT_ALT` · **Mẫu** hai cột (bằng chứng | cách sửa) · **Hình** `real/calib_before_after_side.jpg` (1400×788, cột phải, `w 5,63`). **Nếu file này thiếu**, dùng `real/ui_fk_vs_real.png` (ảnh nhỏ, bản trước khi đơn giản hóa) và ghi vào chú thích `Ảnh chụp màn hình bản trước`.

**Hiển thị**
- Eyebrow: `07 · SỰ CỐ 1` · Tiêu đề: `Mô hình mặc định lệch 3,5–5,9 cm; khớp 10 lần ôm còn 8,5 mm`
- Cột trái (`x 0,8 · w 5,6`): nhãn `ĐẦU KẸP THEO MÔ HÌNH MẶC ĐỊNH CÁCH CỐC THẬT`; ba hàng số lớn (36 pt đất nung) + mô tả 13 pt:
  - `5,4 cm` · `ôm lúc 20:32, servo [85, 60, 90]`
  - `3,5 cm` · `ôm lúc 20:46, servo [80, 70, 75]`
  - `5,9 cm` · `ôm lúc 21:03, servo [75, 85, 50]`
  - dòng nhỏ 12 pt: `Cùng chiều, cùng cỡ: lệch có hệ thống, nên sửa được bằng cách khớp lại mô hình`
- Cột phải (`x 6,9 · w 5,63`): nhãn `CÁCH SỬA: HIỆU CHỈNH BẰNG CÁC LẦN ÔM CỐC`; ảnh (`y 2,2`), chú thích (2 dòng, 11 pt): `Khung cam NGANG lúc ôm cốc 21:03: dấu MAC DINH (mô hình mặc định) cách cốc khoảng 5 cm, dấu SAU HIEU CHINH sát cốc, khoảng 1 cm (cốc đo từ cam ngang, ± 1 cm). Lần ôm này nằm trong 10 mẫu khớp.`; ba bước 13,5 pt có dot:
  1. `Người bấm phím cho hai ngón bao quanh cốc; ghi ba góc servo và vị trí cốc`
  2. `10 lần ở các chỗ khác nhau; khớp 5 thông số của đế và hai góc chuẩn, cộng càng kẹp quay theo khâu khuỷu (Levenberg–Marquardt, numpy)`
  3. `Lưu vào calibration.json`
- Hai ô số cạnh nhau (`bg2`): `8,5 mm` (teal) `sai số khớp, RMS trên 10 mẫu` · `11,6 mm` (teal) `bỏ-một-mẫu (leave-one-out)`
- Hai chip cuối: teal `ĐÃ KHỚP TRÊN 10 LẦN ÔM THẬT` · đất nung `CHƯA THỬ BẤM THEO GỢI Ý MỚI TRÊN CÁNH TAY THẬT · CHỈ ĐÚNG VỚI TỜ GIẤY VÀ VỊ TRÍ ROBOT LÚC ĐO`

**Ghi chú diễn giả**

Sự cố này là chỗ nhóm học được nhiều nhất. Gợi ý trên màn hình được tính từ mô hình cánh tay chứ không đo bằng camera, nên mô hình lệch thì gợi ý nào cũng lệch.

Bằng chứng ở cột trái. Trong buổi thử, người điều khiển bấm phím cho hai ngón kẹp bao quanh chiếc cốc, rồi nhóm ghi ba góc servo và vị trí cốc đo bằng camera. Đưa ba tư thế đầu vào mô hình mặc định, đầu kẹp theo mô hình cách cốc thật năm phẩy bốn, ba phẩy năm và năm phẩy chín xăng-ti-mét: lệch cùng chiều, cùng cỡ, nên là lỗi có hệ thống chứ không phải nhiễu. Ảnh bên phải là một trong các lần ôm: dấu cam là chỗ mô hình mặc định tưởng đầu kẹp đang ở, dấu xanh là sau hiệu chỉnh, sát cốc. Lần ôm này nằm trong số mười mẫu dùng để khớp, nên đây là minh họa chứ không phải kiểm tra độc lập.

Nguyên nhân có ba. Một, vị trí và hướng của đế khác mặc định. Hai, hai góc chuẩn của vai và khuỷu khi servo ở chín mươi độ khác bốn mươi lăm độ, vì chúng phụ thuộc cách lắp cần servo mà thước không đo được. Ba, càng kẹp gắn cứng vào khâu khuỷu nên độ lệch của điểm kẹp quay theo khâu đó, trong khi mô hình cũ giữ nó cố định theo phương ngang.

Cách sửa là hiệu chỉnh bằng trình diễn: mười lần ôm cốc ở các chỗ khác nhau, khớp lại năm thông số cộng hình học càng kẹp bằng thuật toán Levenberg–Marquardt viết thuần numpy. Kết quả: sai số khớp tám phẩy năm mi-li-mét trên mười mẫu, và mười một phẩy sáu khi bỏ lần lượt từng mẫu.

Giới hạn nhóm nói thẳng. Tám phẩy năm là sai số trên chính mười mẫu dùng để khớp. Nhóm chưa thử bấm đúng theo gợi ý mới rồi xem hai ngón có bao quanh cốc không. Và hiệu chỉnh chỉ đúng với tờ giấy và vị trí robot lúc đo; đổi một trong hai thì phải đo lại.

**Nếu được hỏi:** con số năm phẩy bốn có độc lập không? Màn hình bản cũ lúc hai mươi giờ ba mươi hai báo sai số đầu kẹp năm mươi sáu mi-li-mét, cùng cỡ. Vì sao không đo lại bằng thước? Thước đo được chiều dài các khâu, không đo được góc lắp cần servo; hiệu chỉnh bằng trình diễn làm được cả hai việc mà không cần thước. Ví dụ sau hiệu chỉnh? Cốc ở hai mươi phẩy một và bảy phẩy bốn cho gợi ý bảy mươi bốn, năm mươi tám, chín mươi; hai tư thế người căn tay quanh cốc ở chỗ đó cho đầu kẹp theo mô hình cách cốc chỉ khoảng năm đến sáu mi-li-mét. Nhóm chưa rõ hai tư thế đó có nằm trong mười mẫu khớp hay không, nên chỉ nói là gần. Vì sao ảnh ghi khoảng năm xăng-ti-mét mà cột trái ghi năm phẩy chín? Cột trái dùng vị trí cốc ghi lúc ôm; ảnh đo lại từ camera ngang với độ chính xác khoảng một xăng-ti-mét; hai số cùng cỡ. Mô phỏng thế nào? Một cánh tay giả lập có độ lệch biết trước, trong bộ test: sai số trên vùng làm việc từ trên sáu mươi xuống dưới ba mươi lăm mi-li-mét với ba mẫu; đó chưa phải bằng chứng trên cánh tay thật.

**Nguồn:** `calibration.json` (mục `arm`, `claw`, `arm_fit`); `calibration.py:16-20,77-105`; `arm_fit.py:1-45`; `tests/test_arm_fit.py:80-91`; `05_SO_LIEU_VA_NGUON.md` mục 8 và 16; ảnh `calib_before_after_side`.

---

## Slide 12 · 07 · Sự cố 2: servo kẹp nóng
**Master** `CONTENT` · **Mẫu** hai thẻ nguyên nhân / cách xử lý + dải chip · **Hình** không có ảnh (giao diện cảnh báo cũ đã bỏ)

**Hiển thị**
- Eyebrow: `07 · SỰ CỐ 2` · Tiêu đề: `Servo kẹp nóng vì xung PWM không bao giờ nghỉ`
- Thẻ trái (`orangeSoft`, `x 0,8 · w 4,6 · y 1,95 · h 3,7`): nhãn `NGUYÊN NHÂN` (đất nung), hai mục:
  1. `Firmware cũ không bao giờ ngắt xung: kẹp giữ vật hay chạm chốt chặn thì servo bị ép liên tục, đứng yên cũng vậy`
  2. `Lệnh đóng cũ 175° (xung ≈ 2,74 ms), vượt dải 0,5–2,5 ms của MG996R`
- Thẻ phải (`tealSoft`, `x 5,7 · w 6,83 · y 1,95 · h 3,7`): nhãn `CÁCH XỬ LÝ` (teal), bốn mục:
  1. `Firmware: giới hạn cứng góc kẹp 160°; kẹp chỉ nhích 5° mỗi phím`
  2. `Kẹp mở hết cỡ 5 giây không có lệnh → ngắt xung. Kẹp đã khép quá 60 giây → ngắt xung`
  3. `Phím X: servo kẹp nghỉ ngay. Phím Z: nghỉ cả 4 servo`
  4. `Màn hình biết tay đang nghỉ: CANH TAY DANG NGHI; Arduino reset thì báo ARDUINO VUA RESET`
- Dải chip (`y 5,95`): teal `ĐÃ NẠP VÀ KIỂM TRÊN MẠCH: BANNER + Z (nghi het), JSON CÓ armrelax` · đất nung `CHƯA ĐO NHIỆT ĐỘ SERVO`
- Chân trang (`y 6,75`, 11 pt `muted`): `Phụ lục D: dòng thời gian ngắt xung`

**Ghi chú diễn giả**

Đây là sự cố phần cứng. Servo tay kẹp bị nóng.

Nhóm tìm ra hai nguyên nhân. Một, firmware cũ không bao giờ ngắt xung PWM: khi kẹp đang giữ vật hoặc chạm chốt chặn thì servo bị ép liên tục, đứng yên cũng vậy. Hai, lệnh đóng kẹp cũ là một trăm bảy mươi lăm độ, ứng với xung khoảng hai phẩy bảy bốn mi-li-giây, vượt dải không phẩy năm đến hai phẩy năm của MG996R.

Cách xử lý có bốn lớp. Firmware giới hạn cứng góc kẹp một trăm sáu mươi độ. Kẹp mở hết cỡ năm giây không có lệnh thì firmware ngắt xung; kẹp đã khép quá sáu mươi giây cũng ngắt. Phím X cho servo kẹp nghỉ ngay, phím Z cho cả bốn servo nghỉ, cánh tay tự sụp theo trọng lực nên phải hạ đầu kẹp tựa xuống chỗ trống trước. Và chương trình biết khi tay đang nghỉ, nên màn hình ghi cánh tay đang nghỉ thay vì tin các góc cũ.

Nhóm nói rõ trạng thái: firmware cuối cùng, gồm phím Z, bước hai độ và giới hạn một trăm sáu mươi độ, đã được nạp lúc chín giờ bốn mươi hai và chín giờ năm mươi tư tối ngày hai tháng mười một, và kiểm trên mạch thật: dòng chào của Arduino có chữ Z, gói JSON có cờ armrelax. Nhưng nhóm chưa đo nhiệt độ servo nên chưa có số nguội đi bao nhiêu.

**Nếu được hỏi:** vì sao không dùng cảm biến nhiệt? Chưa có trong phần cứng; đây là việc có thể thêm. Giới hạn một trăm sáu mươi có vượt dải xung không? Có, hơi vượt: xung khoảng hai phẩy năm sáu mi-li-giây so với dải danh định hai phẩy năm; chủ máy chấp nhận để kẹp chặt hơn và vẫn có tự nhả xung sau sáu mươi giây. Tại sao khép quá 60 giây lại ngắt, vật có rơi không? Có thể tuột; đó là đánh đổi để servo không bị ép vô hạn. Vì sao ngắt xung khi mở hết cỡ thì hàm khép lại? Khi mất xung, hai hàm rơi thành hình chữ V hẹp; nhóm ước khe còn khoảng một đến hai xăng-ti-mét, nên khi tiếp cận phải bấm J lại trong vòng bốn giây (ước lượng từ ảnh, chưa đo kỹ).

**Nguồn:** `robot_arm_4dof.ino:16-23,160-176,191-201`; `control.py:278,482,550-552,570-574`; `README.md` mục 6; `05_SO_LIEU_VA_NGUON.md` mục 6.

---

## Slide 13 · 08 · Trung thực về kết quả
**Master** `CONTENT` · **Mẫu** P8 (làm / chưa làm) + hai ô số · **Hình** không có

**Hiển thị**
- Eyebrow: `08 · TRUNG THỰC VỀ KẾT QUẢ` · Tiêu đề: `Đã có bằng chứng, và những điều chưa kiểm chứng`
- Panel trái (`tealSoft`), nhãn `ĐÃ CÓ BẰNG CHỨNG`, năm hàng đánh số:
  1. `Hệ tọa độ từ tờ A4 chạy trên cả hai camera (ảnh thật)`
  2. `Cánh tay thật ôm được cốc và chuyển sang trái khi người bấm phím (02/11)`
  3. `Mô hình khớp 10 lần ôm thật: sai số 8,5 mm, bỏ-một-mẫu 11,6 mm`
  4. `Firmware chống nóng và phím Z đã nạp, kiểm trên mạch thật`
  5. `109 test tự động pass: động học, success, màn hình, camera, hiệu chỉnh, Serial`
- Danh sách phải (gạch "—", đất nung), nhãn `CHƯA KIỂM CHỨNG`:
  - `Số lần XONG trên cánh tay thật: bản mới mới chạy bằng test và ảnh đã lưu`
  - `Bấm đúng theo gợi ý mới rồi hai ngón có bao quanh cốc không`
  - `Kẹp giữ chắc cốc thon: chưa; cần ma sát hoặc vật thân thẳng`
  - `Nhiệt độ servo kẹp sau khi thêm ngắt xung`
  - `Hiệu chỉnh cho tờ giấy mới hoặc robot đặt chỗ khác`
  - `Dashboard IoT / MQTT, cảm biến lực: có trong kế hoạch 28/10, chưa làm`
- Hai ô số dưới (`bg2`): `109 / 109` (teal) `test tự động pass` · `0` (đất nung) `lần đếm thành công trên cánh tay thật`

**Ghi chú diễn giả**

Slide này nói thật những gì nhóm có và chưa có.

Cột trái là những gì có bằng chứng. Hệ tọa độ từ tờ A4 chạy trên cả hai camera, có ảnh thật. Cánh tay thật ôm được cốc và chuyển sang trái khi người bấm phím, có ảnh ngày hai tháng mười một. Mô hình cánh tay khớp mười lần ôm thật với sai số tám phẩy năm mi-li-mét. Firmware chống nóng và phím Z đã nạp và kiểm trên mạch. Và một trăm linh chín test tự động đều pass.

Cột phải là những gì chưa kiểm chứng. Một, số lần XONG trên cánh tay thật: bản đơn giản hóa mới chạy bằng test, camera giả lập và ảnh đã lưu. Hai, chưa thử bấm đúng theo gợi ý đã hiệu chỉnh rồi xem hai ngón có bao quanh cốc không. Ba, kẹp chưa giữ chắc cốc thon, nên success không tính kẹp. Bốn, chưa đo nhiệt độ servo. Năm, hiệu chỉnh chỉ đúng với tờ giấy và chỗ đặt robot lúc đo. Sáu, bảng điều khiển IoT với MQTT và cảm biến lực có trong kế hoạch ngày hai mươi tám tháng mười nhưng chưa làm.

Hai ô số bên dưới tóm lại: một trăm linh chín trên một trăm linh chín test pass, và chưa có lần đếm thành công nào trên cánh tay thật.

**Nếu được hỏi:** vì sao chưa chạy bản mới trên cánh tay thật? Nhóm đơn giản hóa mã ngay trong ngày để giải thích được trong một phút, và rút dây Arduino sau đó; chạy bản mới với cánh tay là bước đầu của việc tiếp theo. Có bắt buộc dashboard IoT không? […điền theo yêu cầu đề bài]; nếu có, nhóm sẽ thêm MQTT từ gói JSON hiện có.

**Nguồn:** `05_SO_LIEU_VA_NGUON.md` mục 4, 6, 7, 8, 11, 13; lệnh `pytest -q` (109 passed, 03/11); `ls logs` (không có thư mục).

---

## Slide 14 · Tóm lại
**Master** `PLAIN` · **Mẫu** như slide 14 Gamota + panel ảnh · **Hình** `ai/ai_03_future_autonomous.png` (4:5, panel phải `x 8,4 → 13,333`, ảnh `w 4,2`)

**Hiển thị**
- Nhãn: `TÓM LẠI`
- Ba câu lớn (26 pt, `y 1,3`):
  `Hai camera biến tờ A4 thành thước đo bằng cm.`
  `Nhóm 1 biến vị trí vật thành phím cần bấm.`
  `Nhóm 2 báo ba servo đã tới góc gợi ý chưa.`
- Nhãn `VIỆC TIẾP THEO` (`y 4,2`), ba mục có dot 15 pt:
  1. `Bấm theo gợi ý đã hiệu chỉnh trên cánh tay thật và đếm số lần XONG`
  2. `Dán ma sát lên hai ngón hoặc dùng vật thân thẳng, rồi mới tính kẹp vào success`
  3. `Hiệu chỉnh lại cho tờ giấy mới; thêm dashboard IoT nếu đề bài yêu cầu`
- Bảng nhỏ (nhãn `muted` + giá trị): `Mã nguồn` `github.com/DuongNAD/Project_IoT` · `Video demo` `[ĐIỀN LIÊN KẾT]`
- Câu kết: `Nhóm em cảm ơn thầy cô và các bạn.`
- Panel phải (`bg2`): ảnh AI, chú thích `Hướng phát triển (minh họa AI), không phải kết quả đã đạt`

**Ghi chú diễn giả**

Tóm lại trong ba câu. Hai camera biến tờ giấy A4 thành thước đo bằng xăng-ti-mét. Nhóm một biến vị trí vật thành phím cần bấm. Và nhóm hai báo ba servo đã tới góc gợi ý chưa.

Nhóm không cho rằng hệ thống đã hoàn hảo: những điều ở slide mười ba là thật. Nhưng nhóm hiểu từng phần, mã đủ ngắn để giải thích trong một phút, và có thể sửa bất kỳ phần nào ngay tại đây. Việc tiếp theo có ba bước: bấm theo gợi ý đã hiệu chỉnh trên cánh tay thật và đếm số lần XONG; dán ma sát lên hai ngón hoặc dùng vật thân thẳng để kẹp giữ chắc rồi mới tính kẹp vào success; hiệu chỉnh lại khi đổi tờ giấy. Nếu đề bài cần dashboard IoT thì thêm MQTT.

Ảnh bên phải do AI tạo, minh họa hướng phát triển, không phải kết quả đã đạt.

Nếu thầy cô muốn, nhóm demo trực tiếp: […điền kịch bản demo 2–3 phút].

Nhóm em cảm ơn thầy cô và các bạn.

**Nếu được hỏi:** việc nào làm trước? Chạy bản mới trên cánh tay thật để có số lần XONG đầu tiên, vì đó là chỗ còn thiếu bằng chứng nhất. Có làm được tự động không? Về mặt kỹ thuật là gửi phím theo Plan; nhóm đã bỏ chế độ đó để giữ mã đơn giản, và chỉ nên làm lại khi đo được độ lệch còn lại.

**Nguồn:** `README.md`; `05_SO_LIEU_VA_NGUON.md` mục 4 đến 8. Mã nguồn mới đã lên GitHub (`main` = `e3f2d85`, 03/11).

---
---

# PHỤ LỤC (CONTENT_ALT, chân trang có nhãn `PHỤ LỤC X`)

## Slide 15 · Phụ lục A · Bản đồ module và luồng dữ liệu
**Mẫu** P10 · **Hình** không có

**Hiển thị** · Eyebrow `PHỤ LỤC A` · Tiêu đề `Bản đồ module và luồng dữ liệu`. Các hàng (nhãn lớp bên trái, thẻ nhỏ bên phải; tên file `mono` + mô tả):
- `Nối các phần`: `main.py` vòng lặp: camera → vision → control → success → màn hình; phím, chuột, tham số
- `Màn hình`: `screen.py` hai camera + phần 1 + phần 2
- `Camera`: `cameras.py` tìm camera theo tên, luồng nền tự mở lại
- `Thị giác`: `vision.py` ArUco, homography, tìm vật (tách màu, YOLO tùy chọn), sửa phối cảnh
- `NHÓM 1`: `control.py` FK / IK, cổng USB Arduino, chọn vật, `Plan` và `Move`
- `NHÓM 2`: `success.py` `check(plan)` → `Result`; `Success` đếm số lần
- `Hiệu chỉnh`: `calibration.py` lưu đế, góc chuẩn, càng kẹp · `arm_fit.py` khớp hình học cánh tay (ngoài ứng dụng)
- `Công cụ`: `generate_aruco_a4.py` sinh tờ A4 4 mã
- `Firmware`: `robot_arm_4dof/robot_arm_4dof.ino` · `flash.sh`
- `Kiểm thử`: `tests/`: 109 test
- Dòng cuối: `≈ 2 690 dòng Python (8 module) · 208 dòng firmware · ≈ 1 890 dòng test`

**Ghi chú diễn giả.** Slide dự phòng cho câu hỏi "code nằm ở đâu". Tám module Python, gần hai nghìn bảy trăm dòng, chia theo việc. Mỗi khung hình trong main chỉ là ba dòng: nhóm một lập Plan từ các vật camera thấy, nhóm hai kết luận từ Plan, rồi vẽ màn hình. Firmware Arduino hai trăm linh tám dòng. Một trăm linh chín test chạy trong khoảng chín giây và không đụng vào camera hay cổng USB thật vì cảnh được dựng bằng camera giả lập có đáp án. **Nếu được hỏi:** chạy không cần phần cứng thế nào? `main.py --top a.jpg --side b.jpg --no-serial --headless`. **Nguồn:** `README.md` mục 3 và 7; `main.py:171-174`; `wc -l`.

## Slide 16 · Phụ lục B · Công thức động học ngược và số đo cánh tay
**Mẫu** hai cột · **Hình** không có

**Hiển thị** · Eyebrow `PHỤ LỤC B` · Tiêu đề `Công thức động học ngược và số đo cánh tay`.
- Khối `mono` (trái):
  ```
  r   = √(x² + y²)             θ₁ = atan2(y, x)
  r_w = r − L₄ᵣ                z_w = z + L₄z − d₁
  D   = (r_w² + z_w² − L₂² − L₃²) / (2·L₂·L₃)        |D| ≤ 1: với tới được
  θ₃  = atan2(−√(1 − D²), D)                          khuỷu hướng lên
  θ₂  = atan2(z_w, r_w) − atan2(L₃·sin θ₃, L₂ + L₃·cos θ₃)
  servo: đế = 90 + θ₁ · vai = 90 + (θ₂ − θ₂@90) · khuỷu = 90 + (θ₃ − θ₃@90), làm tròn 2°
  ```
- Bảng số đo (phải), ba cột `Tham số · Mặc định (thước) · Đã hiệu chỉnh`: `d₁` `70 mm` `70 mm` · `L₂` `105 mm` `105 mm` · `L₃` `100 mm` `183,7 mm` · `L₄ᵣ` `65 mm` `0` · `L₄z` `25 mm` `0` · `θ₂@90` `45°` `60,2°` · `θ₃@90` `−45°` `−58,6°` · `đế` `(14,85; −7,5) cm, 90°` `(13,83; 31,67) cm, −92,4°`
- Dòng ghi chú: `Đã hiệu chỉnh: càng kẹp gắn cứng vào khâu khuỷu nên độ lệch của điểm kẹp được gộp vào L₃ (L₄ = 0)`
- Ví dụ (thẻ dưới): `cốc (20,1; 7,4) cm → robot x = 240 mm, y = −73 mm → [đế 74°, vai 58°, khuỷu 90°]`

**Ghi chú diễn giả.** Slide dự phòng cho câu hỏi về công thức. Góc đế là a-tan-hai của y trên x. Phần còn lại là bài toán phẳng hai khâu: đặt D bằng hiệu bình phương khoảng cách trừ tổng bình phương hai khâu, chia hai lần tích hai khâu; nếu giá trị tuyệt đối của D lớn hơn một thì ngoài tầm với. Chọn nghiệm khuỷu hướng lên. Bảng bên phải so mô hình mặc định, đo bằng thước, với mô hình đã hiệu chỉnh: hai góc chuẩn đổi từ bốn mươi lăm lên sáu mươi phẩy hai, và từ âm bốn mươi lăm xuống âm năm mươi tám phẩy sáu; càng kẹp được gộp vào chiều dài khâu ba nên L ba thành một trăm tám mươi ba phẩy bảy. **Nếu được hỏi:** tính ví dụ thế nào? Cốc ở (20,1; 7,4) cm → robot x = 240 mm, y = −73 mm → gợi ý bảy mươi bốn, năm mươi tám, chín mươi. Chạy lại ở đâu? `05_SO_LIEU_VA_NGUON.md` mục 16. **Nguồn:** `control.py:36-67,98-161`; `calibration.json`; `calibration.py:16-20,77-105`; `05_SO_LIEU_VA_NGUON.md` mục 3, 8 và 16.

## Slide 17 · Phụ lục C · Phím điều khiển và gói JSON của Arduino
**Mẫu** hai cột · **Hình** không có

**Hiển thị** · Eyebrow `PHỤ LỤC C` · Tiêu đề `Phím điều khiển và gói JSON của Arduino`.
- Bảng servo (trái): `A` +2° đế sang phải (nhìn theo cam NGANG) · `D` −2° sang trái · `W` +2° vai nâng · `S` −2° vai hạ · `I` +2° khuỷu lên · `K` −2° khuỷu xuống · `J` −5° mở kẹp · `L` +5° đóng kẹp · `H` về Home 90/90/90/95 · `X` nghỉ servo kẹp · `Z` nghỉ cả 4 servo
- Bảng phần mềm (giữa): `TAB` đổi vật · `B` hiệu chỉnh đế (rồi click vào trục xoay đế trên hình cam TRÊN) · `U` quên 4 mã ArUco đã nhớ · `T` tráo vai trò 2 camera · `0`–`3` đổi chỉ số camera TRÊN · `C` chụp ảnh gốc 2 camera · `Q` thoát
- Khối `mono` (phải): `{"t":123456,"servo":[90,90,90,95],"relax":0,"armrelax":0}`; chú giải: `t` thời gian chạy (ms), `t` quay về 0 = Arduino vừa reset · `servo` 4 góc lệnh · `relax` servo kẹp đang nghỉ · `armrelax` ba servo còn lại nghỉ
- Dòng: `Danh định 200 ms (5 gói/giây, đo thực tế 4–5) · USB 9600 baud · HC-05 cũng 9600`
- Chip đất nung: `GÓC SERVO LÀ GÓC LỆNH, KHÔNG PHẢI GÓC ĐO`

**Ghi chú diễn giả.** Slide dự phòng cho câu hỏi về giao thức. Phím điều khiển giống nhau trên bàn phím USB và Bluetooth. Đế, vai, khuỷu nhích hai độ mỗi phím, kẹp năm độ. Mỗi lần Arduino nhận một phím thì gửi ngay gói JSON mới, và cứ hai trăm mi-li-giây gửi một gói. Gói gồm thời gian chạy, bốn góc servo và hai cờ nghỉ. Bốn góc này là góc mà firmware đã ra lệnh, không phải góc đo được. Thời gian chạy quay về không nghĩa là Arduino vừa tự reset; phần mềm bắt dấu hiệu này và báo lên màn hình. **Nếu được hỏi:** có mã hóa hay kiểm lỗi không? Không; đường USB ngắn, mỗi dòng một gói, phần mềm bỏ dòng không đọc được. **Nguồn:** `robot_arm_4dof.ino:70-83,119-170,203-207`; `control.py:211-217,354-392`; `README.md` mục 2.

## Slide 18 · Phụ lục D · Firmware tự ngắt xung để servo kẹp nguội
**Mẫu** P15 (vẽ bằng hình gốc; xem `assets/reference/sample_slides_body.js`) · **Hình** không có ảnh

**Hiển thị** · Eyebrow `PHỤ LỤC D` · Tiêu đề `Firmware tự ngắt xung để servo kẹp nguội`.
- Làn A: `Kẹp mở hết cỡ (đúng 95°)`: có xung 0–5 s (teal) → `NGẮT XUNG sau 5 s` (xám)
- Làn B: `Kẹp đã khép (> 95°)`: có xung 0–60 s (teal) → `NGẮT XUNG sau 60 s` (xám)
- Mốc trục: `0 s` · `5 s` · `60 s`
- Bốn thẻ nhỏ (`y 4,6 · h 0,95 · w 2,78`, khe 0,2): `Giới hạn cứng 160°` · `Phím X: nghỉ servo kẹp ngay` · `Phím Z: nghỉ cả 4 servo (đã nạp)` · `JSON: relax, armrelax`
- Chú thích 11 pt `muted` dưới thẻ: `Mỗi lệnh kẹp cấp xung và đặt lại đồng hồ. Ngắt xung = đặt kênh PWM của PCA9685 về luôn tắt.`

**Ghi chú diễn giả.** Slide dự phòng cho câu hỏi "firmware bảo vệ servo thế nào". Mỗi lệnh kẹp cấp xung và đặt lại đồng hồ. Nếu kẹp đang mở hết cỡ mà năm giây không có lệnh thì ngắt xung; nếu kẹp đã khép, tức góc lớn hơn chín mươi lăm, mà sáu mươi giây không có lệnh cũng ngắt, vì khi đó vật có thể tuột. Ngắt xung là đặt kênh PWM của PCA9685 về luôn tắt. Phím X ngắt ngay kênh kẹp, phím Z ngắt cả bốn kênh, khi đó cánh tay tự sụp theo trọng lực nên phải hạ đầu kẹp tựa xuống chỗ trống trước; chỉ phím di chuyển mới cấp xung lại. **Nếu được hỏi:** giới hạn kẹp là bao nhiêu? Một trăm sáu mươi độ, nâng từ một trăm năm mươi vì ở một trăm năm mươi khe giữa hai ngón chỉ bằng bề rộng nắp cốc. **Nguồn:** `robot_arm_4dof.ino:19-23,47-67,160-176,191-201`; `README.md` mục 6.

## Slide 19 · Phụ lục E · Success chi tiết
**Mẫu** hai cột · **Hình** không có

**Hiển thị** · Eyebrow `PHỤ LỤC E` · Tiêu đề `Success chi tiết: năm trạng thái và một bộ đếm`.
- Khối `mono` (trái):
  ```
  joint_ok(move) = move.degrees <= 1 × bước          (bước 2° với đế, vai, khuỷu)
  check(plan)    -> Result(state, done, joints_ok, next_move, remaining)
  Success.update -> giữ 'done' liên tục >= 1,0 s thì count += 1
  ```
- Bảng trạng thái (phải, theo thứ tự ưu tiên): `relaxed` tay đang nghỉ · `no_target` chưa thấy vật · `unreachable` vật ngoài tầm với · `done` cả ba servo đã tới · `moving` còn phải bấm
- `Result` gồm: `state`, `done`, `joints_ok` (3 giá trị đế / vai / khuỷu), `next_move` (việc đầu tiên chưa xong, thứ tự đế → vai → khuỷu), `remaining` (tổng số lần bấm còn lại), `count`
- Bảy test của nhóm 2 (chip nhỏ): `đang đi tới` · `bỏ qua servo đã đúng` · `lệch 2° vẫn tới, 3° thì chưa` · `kẹp không tính` · `thứ tự ưu tiên các trạng thái` · `giữ đủ lâu mới đếm` · `lướt qua không đếm`
- Chip đất nung: `ĐÃ CHẠY BẰNG TEST VÀ CAMERA GIẢ LẬP · CHƯA CÓ LẦN ĐẾM TRÊN CÁNH TAY THẬT`

**Ghi chú diễn giả.** Slide dự phòng cho câu hỏi "nhóm hai làm chính xác điều gì". Nhóm hai không nhớ gì giữa hai lần gọi, trừ bộ đếm. Mỗi khung hình nó đọc Plan: với mỗi servo, đủ gần nếu độ lệch không quá một bước bấm. Rồi xếp trạng thái theo ưu tiên: tay đang nghỉ thắng mọi thứ, vì khi đã ngắt xung thì góc báo về chỉ là góc lệnh cuối cùng, không tin được; sau đó là chưa thấy vật, rồi vật ngoài tầm; còn lại là xong hoặc còn phải bấm. Việc đầu tiên chưa xong được chọn theo thứ tự đế, vai, khuỷu để màn hình chỉ cho người dùng một lệnh to mỗi lúc. Bộ đếm chỉ tăng khi trạng thái xong được giữ liên tục một giây. **Nếu được hỏi:** vì sao không báo xong khi không thấy vật? Vì khi đó không có đích, góc khớp chỉ là trùng hợp. **Nguồn:** `success.py:16-75`; `tests/test_success.py:12-65`; `tests/test_end_to_end.py`.

## Slide 20 · Phụ lục F · Hiệu chỉnh bằng các lần ôm cốc: chi tiết
**Mẫu** hai cột · **Hình** không có

**Hiển thị** · Eyebrow `PHỤ LỤC F` · Tiêu đề `Hiệu chỉnh bằng các lần ôm cốc: chi tiết và giới hạn`.
- Trái, bốn bước có dot: `Người đưa hai ngón kẹp bao quanh cốc: lúc đó đầu kẹp trùng vị trí cốc, không phụ thuộc camera nhìn nghiêng hay thẳng` · `Ghi ba góc servo (đế, vai, khuỷu), vị trí cốc (cm) và độ cao điểm kẹp (mm)` · `Khớp 5 thông số (x, y, hướng của đế; hai góc chuẩn vai, khuỷu) + hình học càng kẹp, bằng Levenberg–Marquardt thuần numpy; từ chối nếu sai số sau khớp > 30 mm` · `Lưu calibration.json; ứng dụng nạp khi khởi động`
- Phải, ba số lớn teal: `10` mẫu · `8,5 mm` RMS · `11,6 mm` bỏ-một-mẫu
- Khối `mono`: `arm_fit.fit_geometry(samples, ARM_CONFIG, control.predict_tip)`, mỗi mẫu `{"servo": (đế, vai, khuỷu), "x_cm", "y_cm", "z_mm"}`; cần ≥ 2 mẫu cách nhau ≥ 5 cm
- Chip đất nung (ba chip xếp dọc): `CHỈ ĐÚNG VỚI TỜ GIẤY VÀ VỊ TRÍ ROBOT LÚC ĐO` · `TỜ CŨ IN NHỎ HƠN ĐÚNG CỠ ≈ 4,5%: ĐỔI TỜ THÌ ĐO LẠI` · `PHÍM Y / E TRONG ỨNG DỤNG ĐÃ BỎ; KHỚP LẠI BẰNG CÔNG CỤ NGOÀI`

**Ghi chú diễn giả.** Slide dự phòng cho câu hỏi về hiệu chỉnh. Ý tưởng: khi hai ngón kẹp bao quanh cốc thì đầu kẹp của cánh tay đang trùng vị trí cốc, nên mỗi lần ôm cho một phương trình giữa ba góc servo và vị trí cốc. Với mười lần ở các chỗ cách nhau, chương trình khớp năm thông số mà thước không đo được: vị trí và hướng của đế, và hai góc chuẩn của vai và khuỷu. Nhóm còn phát hiện càng kẹp gắn cứng vào khâu khuỷu, nên độ lệch của điểm kẹp quay theo khâu đó; mô hình cũ giữ nó cố định theo phương ngang là sai về cấu trúc. Mô hình mới gộp độ lệch vào chiều dài khâu ba. Chương trình từ chối kết quả nếu sai số sau khớp quá ba mươi mi-li-mét. Giới hạn quan trọng: tờ A4 cũ in nhỏ hơn đúng cỡ khoảng bốn phẩy năm phần trăm, nên mọi số xăng-ti-mét đo trên tờ đó lớn hơn thật khoảng bốn phẩy bảy phần trăm, và hiệu chỉnh gắn với đúng tờ giấy và chỗ đặt robot; đổi một trong hai thì đo lại. **Nếu được hỏi:** vì sao bỏ phím Y trong ứng dụng? Để mã gọn và giải thích được; công cụ khớp vẫn có, chạy ngoài ứng dụng. **Nguồn:** `arm_fit.py:1-45`; `calibration.py:16-20,77-105`; `calibration.json`; `README.md` mục 4; `tests/test_arm_fit.py`.

## Slide 21 · Phụ lục G · Tay kẹp: phi tuyến, cốc thon và cốc đổ
**Mẫu** ảnh trái + facts phải, hàng ảnh dưới · **Hình** `real/hw_gripper_95_vs_125.jpg` (`w 4,4 · h 2,6` tại `x 0,8 · y 1,95`); hàng dưới (`y 4,75`, mỗi ảnh `w 2,8`, 16:9): `real/demo_05_knocked_side.jpg`, `real/demo_05_knocked_top.jpg`, `real/demo_15_tilted_side.jpg`, `real/demo_15_tilted_top.jpg`

**Hiển thị** · Eyebrow `PHỤ LỤC G` · Tiêu đề `Tay kẹp: phi tuyến, cốc thon và cốc đổ`.
- Ảnh trái với nhãn chip phía trên hai nửa: `95° (MỞ HẾT)` và `125°`; chú thích `Ảnh thật, cùng góc nhìn từ trên xuống`
- Phải (`x 5,5 · w 7,0`), ba ý có số: `≈ 7,5 cm` khe kẹp khi mở hết cỡ · `95° → 125°`: ngón vươn ra ≈ 1,7 cm nhưng khe chỉ hẹp ≈ 0,5 cm · `150–160°`: vật rộng ≈ 4 cm (như cốc đỏ) bị đẩy ra
- Chip đất nung: `CỐC THON DẦN XUỐNG ĐÁY → HAI NGÓN ĐẨY CỐC RA` · chip teal nhạt: `CÁCH CHỮA ĐỀ XUẤT, CHƯA THỬ: DÁN MA SÁT LÊN HAI NGÓN HOẶC DÙNG VẬT THÂN THẲNG`
- Hàng ảnh dưới, nhãn 11 pt: `20:32:42 · cốc đổ nằm nghiêng (cam NGANG, cam TRÊN)` và `20:34:22 · kẹp lần hai, cốc nghiêng (cam NGANG, cam TRÊN)`
- Dòng chữ: `Cốc đổ khoảng 3 lần trong buổi 20:32–20:36; người dựng lại bằng tay. Ảnh thật, không chọn khung đẹp.`

**Ghi chú diễn giả.** Slide dự phòng cho câu hỏi về tay kẹp, và để nhóm không chỉ cho thầy cô xem khung đẹp. Tay kẹp là cơ cấu song song nên không tuyến tính theo góc servo. Đo trên không, mở hết cỡ hai hàm cách nhau khoảng bảy phẩy năm xăng-ti-mét; từ chín mươi lăm lên một trăm hai mươi lăm độ, ngón kẹp vươn ra trước khoảng một phẩy bảy xăng-ti-mét nhưng khe chỉ hẹp khoảng nửa xăng-ti-mét. Với cốc đỏ rộng khoảng bốn xăng-ti-mét, khi khép tới một trăm năm mươi đến một trăm sáu mươi độ, cốc bị đẩy ra: cốc thon dần xuống đáy nên hai mặt kẹp đẩy nó ra như hạt dưa. Trong buổi thử cốc bị đổ khoảng ba lần; hai ảnh dưới là một lần cốc đổ nằm nghiêng ngay trước hai ngón kẹp, và một lần kẹp lại nhưng cốc nghiêng trong tay kẹp. Mỗi lần như vậy người điều khiển dựng cốc lại bằng tay rồi thử tiếp. Đây là lý do success không tính tay kẹp. **Nếu được hỏi:** vì sao cốc dễ đổ? Nguyên nhân chính nhóm cho là hình dạng cốc thon; chưa phân tích kỹ hơn. Cách chữa nào? Dán ma sát lên mặt trong hai ngón hoặc dùng vật có thân thẳng; nhóm chưa thử. **Nguồn:** ảnh `hw_gripper_95_vs_125`, `demo_05`, `demo_15`; `README.md` mục 6; `05_SO_LIEU_VA_NGUON.md` mục 7 và 9.

## Slide 22 · Phụ lục H · Hai lỗi tích hợp khó thấy: camera macOS và Arduino tự reset
**Mẫu** hai thẻ ba dòng · **Hình** không có

**Hiển thị** · Eyebrow `PHỤ LỤC H` · Tiêu đề `Hai lỗi tích hợp khó thấy: camera macOS và Arduino tự reset`.
- Thẻ trái `CAMERA TRÊN macOS`: `Hiện tượng: hai khung hình cùng một góc nhìn (OBSBOT bị mở hai lần).` · `Nguyên nhân: OpenCV sắp camera theo uniqueID; danh sách của hệ thống xếp camera dùng gần nhất lên đầu nên đổi thứ tự giữa các lần chạy.` · `Xử lý: tìm camera theo tên, đổi sang chỉ số theo đúng quy tắc sắp uniqueID ngay trước mỗi lần mở; so độ xiên của tờ giấy để cảnh báo; phím T để tráo.`
- Thẻ phải `ARDUINO TỰ RESET`: `Hiện tượng: cả 4 servo giật về 90/90/90/95 khi không ai bấm phím.` · `Nguyên nhân: mở rồi đóng cổng USB làm đường DTR hạ xuống rồi nâng lên, Uno reset (xảy ra khi chương trình thứ hai mở cổng).` · `Xử lý: không đóng cổng khi lỗi đọc thoáng qua; mở tay cầm mới trước khi đóng tay cầm cũ; nhận ra reset khi thời gian chạy t quay về 0, báo ARDUINO VUA RESET.`

**Ghi chú diễn giả.** Slide dự phòng, hai bài học tích hợp. Một, trên macOS chỉ số camera của OpenCV không theo danh sách của hệ thống: hai danh sách đó xếp camera dùng gần nhất lên đầu, nên đổi từ lần chạy này sang lần khác, còn OpenCV thì sắp theo mã định danh. Nhóm đã thấy lúc OBSBOT đứng trước, lúc MacBook đứng trước, và có lúc cả hai khung hình cùng là camera trên. Hai, Arduino Uno tự reset mỗi khi đường DTR của cổng USB hạ xuống rồi nâng lên; nhóm gặp điều này khi một chương trình khác mở cổng song song, làm cả bốn servo giật về vị trí gốc. Vì vậy khi đang chạy chương trình chính, không mở cổng bằng chương trình khác. **Nếu được hỏi:** có nguy hiểm không? Cánh tay có thể giật khi vật hay tay người ở trong tầm; vì vậy màn hình báo ngay `ARDUINO VUA RESET` và nhóm dặn kiểm tra trước khi bấm tiếp. **Nguồn:** `cameras.py:4-12,75-115`; `control.py:345-352,396-446`; `README.md` mục 5 và 6; `tests/test_serial_link.py:96-140`.

## Slide 23 · Phụ lục I · Đã bỏ khi đơn giản hóa
**Mẫu** bảng hai cột · **Hình** không có

**Hiển thị** · Eyebrow `PHỤ LỤC I` · Tiêu đề `Đã bỏ khi đơn giản hóa, có sao lưu`. Bảng (đã bỏ · thay bằng):
- `Quy trình gắp 5 bước` · `một đích duy nhất: ba servo tới góc gợi ý`
- `Kiểm tra S1 và S2 bằng hai camera` · `success.py: ba góc servo trong ±2°, giữ 1 s`
- `Nhật ký logs/attempts.csv` · `số lần thành công đếm trên màn hình`
- `Tự gửi phím (Auto-Step)` · `chương trình chỉ gửi phím người bấm`
- `Cửa sổ HƯỚNG DẪN GẮP và thanh gợi ý 4 servo` · `màn hình hai phần: điều khiển → success`
- `Ước lượng tư thế cam NGANG` · `không cần: vị trí vật chỉ lấy từ homography`
- `YOLO là mặc định` · `tách màu là mặc định; YOLO tùy chọn`
- `Hiệu chỉnh trong chương trình (phím Y / E)` · `công cụ ngoài arm_fit.py, kết quả lưu calibration.json`
- Chú thích: `Mục đích: mã và màn hình giải thích được trong một phút. Bản đầy đủ trước khi đơn giản hóa còn sao lưu (14 MB, ngoài repo).`

**Ghi chú diễn giả.** Slide dự phòng cho câu hỏi "sao không dùng camera để xác nhận gắp" hay "tự động đâu". Sáng ngày hai tháng mười một nhóm có một bản đầy đủ hơn: quy trình gắp năm bước, hai tín hiệu từ hai camera để xác nhận vật được nhấc lên, nhật ký CSV, chế độ tự gửi phím. Tối cùng ngày, nhóm quyết định đơn giản hóa để mã và màn hình giải thích được trong một phút, và để đề tài tập trung vào hai việc lõi: tính phím cần bấm, và kiểm ba servo đã tới góc. Bản đầy đủ không bị mất, đã sao lưu ngoài repo. Vì thế, mọi nhận xét "chưa kiểm chứng" ở slide mười ba tính theo bản mới. **Nếu được hỏi:** có định khôi phục không? Chỉ khi đo được độ lệch còn lại của mô hình và kẹp giữ chắc cốc; khi đó xác nhận bằng camera mới có ý nghĩa. **Nguồn:** `README.md` mục 9; `05_SO_LIEU_VA_NGUON.md` mục 12.

## Slide 24 · Phụ lục J · Điều chỉnh so với kế hoạch ngày 28/10
**Mẫu** bảng ba cột · **Hình** không có

**Hiển thị** · Eyebrow `PHỤ LỤC J` · Tiêu đề `Điều chỉnh so với kế hoạch ngày 28/10`. Bảng (hàng · kế hoạch 28/10 · thực tế 02/11):
- `Vi điều khiển` · `ESP32` · `Arduino Uno`
- `Servo` · `6 (có cổ tay gập và xoay)` · `4 (đế, vai, khuỷu, kẹp)`
- `Camera` · `2 webcam USB 1280×720` · `OBSBOT + MacBook, 1920×1080`
- `Giao tiếp` · `USB Serial 115200 + MQTT` · `USB Serial 9600 (+ HC-05 tùy chọn), không MQTT`
- `Nhận diện` · `ArUco; mở rộng YOLO26n-seg` · `ArUco 4 góc + tách màu; YOLO11s tùy chọn`
- `Giám sát` · `dashboard Node-RED / web` · `màn hình OpenCV hai phần`
- `Xác nhận` · `S1 + S2 (+ cảm biến lực)` · `ba góc servo tới góc gợi ý; không cảm biến lực`
- `Mục tiêu đo` · `≥ 80% / 30 lần; ≤ 3 mm; ≤ 2 s; ≥ 20 fps` · `chưa đo`
- Chú thích: `Kế hoạch 28/10 giả định phần cứng chưa biết; bản thực tế bám phần cứng nhóm có.`

**Ghi chú diễn giả.** Slide dự phòng cho câu hỏi "kế hoạch có ESP32, MQTT, sáu servo, sao làm khác". Kế hoạch ngày hai mươi tám tháng mười đặt giả định về phần cứng vì lúc đó nhóm chưa chốt; khi đối chiếu với phần cứng thật thì cánh tay có bốn servo, dùng Arduino Uno, không có cổ tay, nên nhóm điều chỉnh: bỏ cổ tay khỏi động học, giữ giao tiếp USB, và chưa làm MQTT hay cảm biến lực. Việc xác nhận cũng đổi: từ hai tín hiệu camera sang ba góc servo, theo phụ lục I. Các mục tiêu đo trong kế hoạch vẫn là mục tiêu, nhóm chưa đo. **Nếu được hỏi:** có làm MQTT không? Chưa; gói JSON hiện có sẵn sàng để đẩy lên MQTT nếu cần. **Nguồn:** kế hoạch PDF 28/10/2026; `05_SO_LIEU_VA_NGUON.md` mục 13; `grep` MQTT trong mã nguồn: không có.

## Slide 25 · Phụ lục K · Hỏi đáp dự kiến
**Mẫu** P16 (hai cột, sáu hàng mỗi cột) · **Hình** không có

**Hiển thị** · Eyebrow `PHỤ LỤC K` · Tiêu đề `Hỏi đáp dự kiến`. Mười hai cặp (câu hỏi đậm 13 pt, câu trả lời 11,5 pt):
1. `Vì sao hai camera, không phải một?` · `Cam trên cho vị trí X, Y của vật. Cam ngang cho người nhìn độ cao và độ sát của hai ngón kẹp, thứ mà camera trên đầu không thấy. Code chỉ dùng cam trên để tính vị trí vật.`
2. `Vì sao không gắn camera lên tay?` · `Servo rung làm ảnh nhòe, dây đi qua khớp xoay, phải hiệu chuẩn hand-eye; hai camera cố định đơn giản hơn.`
3. `Vì sao tách màu, không phải YOLO?` · `YOLO bản COCO hay gọi nhầm bộ phận robot; tách màu chắc hơn với vật có màu. YOLO còn lại như tùy chọn (--yolo).`
4. `Độ chính xác định vị?` · `Chưa đo bằng thước trên nhiều mẫu. Đã có: hai camera lệch nhau 0,2 cm sau khi sửa phối cảnh (một vị trí); mô hình cánh tay khớp 8,5 mm trên 10 mẫu.`
5. `Vì sao Arduino Uno, không ESP32?` · `Phần cứng của nhóm là Arduino Uno + PCA9685; kế hoạch ban đầu giả định ESP32 và đã được điều chỉnh (phụ lục J).`
6. `Servo kẹp còn nóng không?` · `Chưa đo nhiệt độ. Đã thêm ngắt xung, giới hạn 160°, phím X và Z (slide 12).`
7. `Tỉ lệ thành công bao nhiêu?` · `Chưa đo. Bản mới đếm số lần XONG trên màn hình nhưng chưa chạy trên cánh tay thật.`
8. `Có tự động hoàn toàn không?` · `Không. Màn hình chỉ cho bấm phím nào, người bấm. Chế độ tự gửi phím đã bỏ để mã đơn giản.`
9. `Vì sao kẹp không tính vào success?` · `Cốc thon bị đẩy ra ở 150–160°. Đề tài chỉ cần ba góc servo tới góc gợi ý.`
10. `XONG nghĩa là vật đã được gắp?` · `Không. Nghĩa là ba góc lệnh đã tới góc gợi ý; MG996R không báo vị trí thật.`
11. `Phần IoT ở đâu?` · `Arduino ↔ laptop qua USB 9600 baud, gói JSON ~5 gói/giây, Bluetooth HC-05 tùy chọn; chưa có MQTT hay đám mây.`
12. `Đổi tờ giấy hoặc dời robot thì sao?` · `Phải hiệu chỉnh lại: khoảng 10 lần ôm cốc rồi khớp bằng arm_fit (phụ lục F).`

**Ghi chú diễn giả.** Slide dự phòng, chỉ mở khi được hỏi; mỗi câu trả lời trên slide là câu trả lời ngắn nhất, nói thêm theo phần **Nếu được hỏi** của slide tương ứng. Với bất kỳ câu nào đòi một con số mà bảng số liệu không có (tỉ lệ thành công, nhiệt độ, sai số trên vật thật), câu trả lời là "chưa đo" cộng cách sẽ đo. **Nguồn:** `05_SO_LIEU_VA_NGUON.md`; kế hoạch PDF 28/10/2026 (các lý do chọn hai camera và không gắn camera lên tay).
