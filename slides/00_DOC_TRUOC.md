# 00 · Đọc trước

Bộ tài liệu để **Antigravity (Gemini 4 Argon)** dựng slide thuyết trình dự án cánh tay robot, theo phong cách slide Gamota của bạn.
Mình đã chuẩn bị nội dung, lời nói, ảnh thật, prompt ảnh AI, số liệu đã kiểm, và kiểm tra chất lượng tự động. Việc còn lại là bạn **dán prompt**
và **điền các chỗ trống**.

> **Cập nhật 05/11/2026: bộ slide đã dựng xong** là `slides/Project_IoT_ThuyetTrinh.pptx` (+ `.pdf`): **26 slide** theo màu slide Gamota,
> chia 4 phần cho 4 người, mỗi phần mở bằng một slide ngăn: 01 linh kiện (danh sách, giới thiệu, sơ đồ mạch, bảo vệ servo kẹp) →
> 02 computer vision → 03 code điều khiển (lưu đồ, code firmware, động học ngược, giao diện, điều khiển từ xa, hiệu chỉnh) → 04 success.
> Chữ trên slide viết ngắn, từ ngữ trung tính (tiêu đề là cụm danh từ, mỗi ý vài từ); giải thích và hỏi đáp nằm trong ghi chú. Tên ở bảng `TEAM` đầu `build_slides.py`,
> nội dung rút từ `01` và số liệu ở `05`. Dựng lại: `python3 slides/build_slides.py` → `python3 slides/export_pdf.py` → `python3 slides/render_previews.py`;
> kiểm: `python3 slides/verify_slides.py` (số trang, ghi chú, chân trang, chữ "mô phỏng", thiết kế đã bỏ, chỗ `[...]` còn phải điền).
> Kịch bản 25 slide kiểu Gamota trong `01`–`06` dưới đây vẫn giữ làm phương án dựng bằng Antigravity.
>
> **Đã viết lại ngày 02/11/2026 ≈ 23:30** theo mã nguồn **sau khi đơn giản hóa** (`control.py` nhóm 1 → `success.py` nhóm 2; 103 test pass, sau bản gộp 03/11 là 109).
> Bản 21:30 mô tả thiết kế cũ (quy trình 5 bước, S1/S2, Auto-Step, `attempts.csv`, phím `Y`/`E`, 110 test, mô hình lệch 5 cm, chưa có `calibration.json`)
> nên **không còn đúng**: deck dựng từ nó sẽ sai sự thật. Mọi file ở đây đã thay mới; mục 9 liệt kê điều đã đổi.

## 1. Có gì trong thư mục `slides/`

| File | Cho ai | Nội dung |
|---|---|---|
| `00_DOC_TRUOC.md` | bạn | file này |
| `01_KICH_BAN_SLIDE.md` | cả hai | **25 slide** (14 chính + phụ lục A–K): chữ trên slide, hình, mẫu bố cục, **lời nói**, "Nếu được hỏi", "Nguồn" |
| `02_ANH_THAT.md` | cả hai | ảnh thật đã chuẩn bị (kể cả ảnh màn hình mới), ảnh không dùng và lý do, cách cắt video, **danh sách cần chụp thêm** |
| `03_PROMPT_ANH_AI.md` | Antigravity | 2 prompt ảnh AI bắt buộc + 4 tùy chọn, khối phong cách, checklist |
| `04_PROMPT_ANTIGRAVITY.md` | bạn dán | **prompt tổng** và các prompt chia nhỏ A, B, B2, C, D, E, **F (làm mới số liệu khi mã đổi)** |
| `05_SO_LIEU_VA_NGUON.md` | cả hai | mọi con số đã kiểm có nguồn; danh sách **CẤM NÓI**; khối kiểm tự động (mục 17) |
| `06_PHONG_CACH.md` | Antigravity | màu, phông, kích thước, 16 mẫu bố cục có tọa độ |
| `assets/real/` | | ảnh thật (đã cắt, làm mờ màn hình) + `_preview.jpg` |
| `assets/manifest.json` | | mô tả, alt text, slide dùng của từng ảnh |
| `assets/reference/` | | mã dựng tham chiếu của slide Gamota (đã chỉnh) + mã mẫu slide 3, 7, 9, 10, 18 + ảnh các trang mẫu |
| `assets/ai/` | | **trống**: Antigravity lưu ảnh AI vào đây |
| `tools/` | | `check_facts.py` (**tài liệu còn khớp mã không**), `qa_deck.py` (kiểm PPTX), `prepare_real_assets.py` và `make_screen_images.py` (tạo lại ảnh) |
| `build/` | | **trống**: Antigravity dựng `IoT_RobotArm_Presentation.pptx` và `.pdf` vào đây |

## 2. Quy trình

0. **Kiểm tài liệu còn khớp mã:** `python3 -I slides/tools/check_facts.py` (thêm `--deep` để đếm test và tính lại ví dụ). Dòng cuối phải là `KHỚP`.
   Nếu mã còn đổi (bạn hoặc phiên khác), chạy lại bước này **trước mỗi lần dán prompt**; `LỆCH` thì dùng prompt F hoặc sửa `05` rồi `01` bằng tay.
1. (Tùy chọn, nên làm) chạy **bản mới với cánh tay thật**, bấm theo lệnh trên màn hình tới khi ghi `XONG!`, chụp màn hình và quay video 20–30 giây theo `02_ANH_THAT.md` mục 6.
   **Không bắt buộc**: bộ ảnh hiện có đã đủ để dựng, nhưng đây là bằng chứng mạnh nhất còn thiếu.
2. Mở Antigravity ở thư mục dự án, chọn model `gemini-4-argon-medium`, dán prompt ở `04_PROMPT_ANTIGRAVITY.md` (**A → B → C**, hoặc prompt tổng).
3. Duyệt kết quả theo checklist mục 8; điền chỗ `[…]`; tập nói. (Mã nguồn đã lên GitHub: `main` = `e3f2d85`.)

## 3. Việc bạn cần làm (và Antigravity không làm thay được)

**Điền vào PPTX (tìm dấu `[` trong từng slide; `qa_deck.py` liệt kê hết):**

- [ ] `[TÊN MÔN HỌC]`, `[NGÀY THUYẾT TRÌNH]`, `[TÊN THÀNH VIÊN 2]`, `[TÊN THÀNH VIÊN 3]`, `[TÊN NHÓM]` (slide 1)
- [ ] `[ĐIỀN LIÊN KẾT]` video demo (slide 14); kịch bản demo 2–3 phút (ghi chú slide 14)
- [ ] phân công người nói (cột "Người nói" ở `01_KICH_BAN_SLIDE.md`) và câu trả lời "ai làm gì" (ghi chú slide 1)
- [ ] có video hay không (ghi chú slide 10)
- [ ] **đề bài có bắt buộc dashboard IoT / MQTT hoặc mô hình học máy không** (ghi chú slide 13): kế hoạch 28/10 còn để ngỏ câu này và mã nguồn hiện **không có MQTT**

**Trả lời giúp mình (để sửa chữ trên slide cho đúng):**

- [ ] "**Nhóm 1 · điều khiển**" và "**nhóm 2 · success**" là hai *phần mã* hay hai *nhóm người* trong lớp? Slide gọi chúng là nhóm 1 và nhóm 2; nếu là hai nhóm người thì thêm tên và chia người nói.
- [ ] Đã **chạy bản mới trực tiếp với cánh tay thật** chưa? Nếu rồi: cho mình số `Thanh cong` và ảnh màn hình, mình đổi các dòng "chưa" ở slide 9, 11, 13.
- [ ] Tờ giấy đang dùng là **tờ cũ** (in nhỏ ≈ 4,5%) hay **tờ mới**? Hiệu chỉnh hiện tại chỉ đúng với tờ cũ và chỗ đặt robot lúc đo.

**Trước ngày nói:**

- [x] Mã nguồn mới đã lên GitHub (`main` = `e3f2d85`, 03/11/2026), gồm cả phần gộp từ máy Windows. Ảnh trong `assets/real/` và `captures/` vẫn ngoài repo; **lưu ý**: `Project_IoT_ThuyetTrinh.pptx`, `.pdf` và `preview/` có nhúng ảnh thật và đang được git theo dõi, nên quyết định trước khi commit chúng lên repo công khai.
- [ ] đọc lại lời nói từng slide, sửa thành giọng của bạn; tập nói thử và bấm giờ: lời nói đủ ≈ 15 phút, bản rút gọn ≈ 12 phút (bảng giờ và gợi ý cắt ở `01_KICH_BAN_SLIDE.md`)
- [ ] thử mở PPTX và PDF trên **máy sẽ trình chiếu** (phông mặc định Arial; bản Segoe UI cho Windows ở prompt E)
- [ ] chuẩn bị demo: thử nguyên chuỗi trước giờ nói; tắt chương trình khác giữ cổng USB; nhớ rằng mở cổng thứ hai làm Arduino reset (slide 22); khi hạ đầu kẹp tựa xuống rồi bấm `Z` thì cả cánh tay sụp
- [ ] sao lưu PDF và video vào USB / Drive

**Nếu muốn slide mạnh hơn (đổi cả chữ trên slide, nên sửa `05_SO_LIEU_VA_NGUON.md` trước):**

- [ ] chạy bản mới với cánh tay thật, bấm theo gợi ý đã hiệu chỉnh và xem hai ngón có bao quanh cốc không; đếm `Thanh cong` → slide 9, 11, 13
- [ ] nếu đổi tờ giấy hoặc dời robot: ôm cốc ≥ 3 lần ở các chỗ khác nhau và khớp lại bằng `arm_fit.fit_geometry` (phụ lục F) → slide 11
- [ ] dán ma sát (băng keo hai mặt / xốp mỏng) lên mặt trong hai ngón hoặc dùng vật thân thẳng, thử kẹp lại → slide 9, 21
- [ ] đo nhiệt độ servo kẹp (nhiệt kế hồng ngoại) → slide 12

## 4. Giả định mình đã đặt (sai thì nói, mình sửa)

| Giả định | Căn cứ |
|---|---|
| Người nghe là **giảng viên và các bạn trong nhóm** | kế hoạch 28/10: "dùng để thuyết trình với giảng viên và các bạn trong nhóm" |
| Lời nói đủ **≈ 15 phút** (rút gọn được còn ≈ 12 phút) + demo 2–3 phút + hỏi đáp | đếm từ: ≈ 3 100 từ lời nói ở 14 slide chính, ≈ 200 từ/phút (ước lượng, hãy đọc thử); Gamota là 9 phút / 14 slide |
| Tiếng Việt, xưng "nhóm em" (bạn nói "chúng tôi") | thuyết trình nhóm cho thầy cô |
| 14 slide chính + 11 phụ lục A–K = 25 slide | Gamota: 14 + 11 |
| PPTX 16:9 + PDF; phông **Arial** | Mac không có Segoe UI nên PDF xuất ra sẽ vỡ chữ; Segoe UI chỉ đẹp trên Windows |
| Câu chuyện **trung thực**: màn hình chỉ cho biết bấm phím nào; "thành công" = ba servo tới góc gợi ý; số lần XONG trên cánh tay thật, bấm theo gợi ý mới và nhiệt độ servo ghi rõ "chưa kiểm chứng" | khớp phong cách Gamota (hiện "CHƯA ĐẠT" trên slide) và đúng dữ liệu |
| Ảnh buổi 02/11 20:32 là bằng chứng cánh tay thật ôm cốc; ảnh buổi 18:10 (tiếp cận "thiếu 1,5–2 cm") **không dùng** | báo cáo đã đính chính 20:25 |
| Ảnh màn hình mới (`ui_screen_*`) là **chương trình chạy trên ảnh camera thật đã lưu, cánh tay mô phỏng** | chưa có lần chạy trực tiếp với cánh tay (Arduino rút ra lúc ≈ 22:40) |

## 5. Sáu điều không được nói quá (tóm tắt `05_SO_LIEU_VA_NGUON.md` mục 14)

1. **Không tự động**: màn hình chỉ cho biết bấm phím nào; người bấm. Chế độ tự gửi phím đã bỏ.
2. **"XONG" không phải "đã gắp"**: nó nghĩa là ba góc *lệnh* (Arduino báo lại góc đã ra lệnh, MG996R không báo vị trí thật) tới góc gợi ý, kẹp không tính.
3. **Không có tỉ lệ thành công**: bản mới chưa có lần đếm nào trên cánh tay thật.
4. **Hiệu chỉnh**: sai số khớp 8,5 mm là trên chính 10 mẫu (bỏ-một-mẫu 11,6 mm), chỉ đúng với tờ giấy và chỗ đặt robot lúc đo, và **chưa thử bấm theo gợi ý mới trên cánh tay thật**.
5. **Servo kẹp**: đã thêm ngắt xung, giới hạn 160°, phím `X`/`Z` (đã nạp, đã kiểm); **chưa đo nhiệt độ**. Kẹp chưa giữ chắc cốc thon.
6. **Kế hoạch 28/10 ≠ sản phẩm**: ESP32, 6 servo, MQTT, dashboard, cảm biến lực, YOLO26 **không có** trong mã nguồn.

## 6. Điều mình phát hiện khi kiểm lại (đáng biết)

- **Mã đã đổi lớn trong tối 02/11** (đơn giản hóa để giải thích trong một phút): bỏ 5 bước, S1/S2, Auto-Step, nhật ký CSV, cửa sổ HƯỚNG DẪN, phím `Y`/`E`; thêm `calibration.json` thật. Có sao lưu 14 MB ngoài repo.
- **Số đo mạnh nhất hiện nay** là hiệu chỉnh: mô hình mặc định đặt đầu kẹp cách cốc **5,4 · 3,5 · 5,9 cm** trong ba lần ôm đầu; khớp **10 lần ôm** cho sai số **8,5 mm** (bỏ-một-mẫu 11,6 mm). Mình tính lại các số này từ mã và `calibration.json` (`check_facts.py --deep`).
- **Camera NGANG không dùng để tính vị trí vật** (chỉ cam TRÊN tìm vật); cam NGANG để người nhìn độ cao và độ sát của hai ngón. Slide viết đúng như vậy.
- **Phím `Z` đã nạp và kiểm** (21:42 và 21:54): bản 21:30 còn ghi "chưa nạp".
- **Hướng trái / phải**: `A` = sang **phải**, `D` = sang **trái**, nhìn theo cam NGANG (MacBook). Chú thích trong firmware ghi ngược (theo hướng nhìn của robot); slide theo màn hình.
- `calibration.json` có `arm_fit.to_giay`: *tờ cũ in nhỏ ≈ 4,5%, đổi tờ thì phải khớp lại*. Tờ mới lớn hơn ≈ 4,5%.
- **Repo công khai còn bản cũ**; slide 14 trỏ tới nó.
- Mình **không dùng** ảnh thử 18:10 và các kết luận "cốc ở mép tầm với", "cần 155–165°" vì chúng đã bị rút lại hoặc chưa xác nhận.

## 7. Giữ nguyên và đổi so với slide Gamota

| Giữ nguyên | Đổi |
|---|---|
| bảng màu ấm, 4 master, eyebrow đánh số, tiêu đề là kết luận | màu chàm là **YOLO11 (tùy chọn)** (ở Gamota là LLM); đất nung là phần cứng, rủi ro, chưa kiểm chứng |
| số liệu lớn, thẻ ngà, chip, mũi tên, dot đánh số | thêm **ảnh thật**, **ảnh màn hình mô phỏng**, **sơ đồ vẽ bằng hình gốc** (slide 3, 7, 18), **2 ảnh AI** có nhãn "Minh họa (AI)" |
| ghi chú ba phần: lời nói, "Nếu được hỏi", "Nguồn" | phông mặc định Arial (có công tắc Segoe UI) |
| phụ lục dự phòng cho hỏi đáp; nói thẳng điều "chưa đạt" | 14 + 11 slide; slide kết có "việc tiếp theo" thay cho liên kết demo trực tuyến |

## 8. Checklist duyệt bản PPTX Antigravity trả về

- [ ] `build/REPORT.md` đọc được, nêu rõ ảnh AI nào thiếu, chỗ `[…]` còn lại và mục "Contradictions" (nếu có)
- [ ] `python3 -I slides/tools/check_facts.py` vẫn `KHỚP` (mã không đổi giữa chừng)
- [ ] `python3 -I slides/tools/qa_deck.py slides/build/IoT_RobotArm_Presentation.pptx` in `QA OK`
- [ ] mở PDF, lướt 25 trang: không chữ tràn hay đè, ảnh không méo, chữ không nhỏ hơn 11 pt
- [ ] chỉ slide 2 và 14 có ảnh AI, kèm "Minh họa (AI)"; **không** slide nào khác có ảnh AI
- [ ] slide 8 và 9: ảnh màn hình có chú thích "mô phỏng / ảnh đã lưu", **không** ghi là chạy trực tiếp; `A` sang phải, `D` sang trái
- [ ] slide 10: ba cột ảnh thật có giờ `20:32:52`, `20:33:02`, `20:33:12` và dòng "KHÔNG TỰ ĐỘNG"
- [ ] slide 9, 11, 12, 13 giữ nguyên các nhãn "chưa kiểm chứng / chưa đo / chưa thử"
- [ ] không có chữ "tự động hoàn toàn", tỉ lệ thành công, "servo hết nóng", S1/S2 / 5 bước / Auto-Step như tính năng đang có (chỉ phụ lục I được nhắc), MQTT/dashboard như điều đã làm
- [ ] ghi chú diễn giả có đủ lời nói, "Nếu được hỏi", "Nguồn" ở mọi slide

## 9. Đã đổi so với bản 21:30

| Mục | Bản 21:30 (không còn đúng) | Bản này |
|---|---|---|
| Số slide | 24 (14 + 10) | **25 (14 + 11)** |
| Nhân vật chính của kịch bản | quy trình 5 bước + S1/S2 hai camera cùng đồng ý | **hai nhóm nối nhau qua `Plan`**: điều khiển (phím cần bấm) → success (ba servo tới góc, giữ 1 s) |
| Màn hình | cửa sổ HƯỚNG DẪN GẮP, HUD | màn hình hai phần (ảnh `ui_screen_*` mới, mô phỏng) |
| Mô hình cánh tay | lệch ≈ 5 cm, chưa hiệu chỉnh | lệch 3,5–5,9 cm, **đã khớp 10 lần ôm: 8,5 mm** |
| Bước phím | 5° | **2°** (kẹp 5°); giới hạn kẹp 160° |
| Phím `Z` | "chưa nạp" | đã nạp và kiểm |
| Kiểm thử | 110 test | **103 test** (sau bản gộp 03/11: **109**) |
| Ảnh AI | 3 bắt buộc (slide 2, 9, 14) | **2 bắt buộc (slide 2, 14)** |
| Phụ lục | S1/S2 chi tiết, ngoại suy 155–165° | success chi tiết, hiệu chỉnh chi tiết, **đã bỏ khi đơn giản hóa** |
| Công cụ | `qa_deck.py` | thêm **`check_facts.py`** (chống lỗi thời), `make_screen_images.py`; `qa_deck.py` biết thiết kế đã bỏ |
| Prompt | A, B, B2, C, D, E | thêm bước kiểm trước khi dựng, quy tắc hướng A/D, **prompt F làm mới số liệu** |

## 10. Thư mục và git

`slides/.gitignore` loại khỏi git: `assets/real/` (ảnh bàn làm việc riêng tư; repo GitHub công khai), `assets/ai/`, `assets/reference/` (có ảnh từ slide Gamota),
`assets/manifest.json` (có đường dẫn cá nhân), và mọi thứ sinh ra trong `build/`. **Các file `.md` và `tools/` không bị loại**, bạn tự quyết có commit hay không.
Mình **không commit gì**.
