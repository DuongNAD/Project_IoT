# 04 · Prompt cho Antigravity (model Gemini 4 Argon)

Antigravity **không nhìn thấy cuộc trò chuyện này**, nên mỗi prompt dưới đây tự đứng một mình: tiếng Anh, theo khung GOAL / FILES / RULES / DONE WHEN.
Nội dung slide bằng tiếng Việt nằm trong các file tài liệu để Antigravity đọc; prompt chỉ ra lệnh và ràng buộc.

**Bản này viết lại ngày 02/11/2026 ≈ 23:30** cho mã nguồn **sau khi đơn giản hóa** (hai nhóm: `control.py` → `success.py`; không còn 5 bước, S1/S2, Auto-Step, `attempts.csv`, phím `Y`/`E`).
Bản prompt cũ (24 slide, S1/S2) sẽ dựng ra deck sai sự thật; đừng dùng lại.

## Cách dùng

1. **Kiểm tài liệu còn khớp mã:** `python3 -I slides/tools/check_facts.py` phải in `KHỚP` ở dòng cuối. In `LỆCH` nghĩa là mã đã đổi sau lần viết tài liệu: sửa `05_SO_LIEU_VA_NGUON.md` (mục 17 và dòng liên quan) rồi `01_KICH_BAN_SLIDE.md` **trước khi** dán prompt.
2. Mở Antigravity với workspace là **thư mục dự án** `/Users/duongnad/Documents/project/Project_IoT` (các prompt dùng đường dẫn `slides/...` từ `slides/`).
3. Chọn model **`gemini-4-argon-medium`** cho việc dài (dựng slide, tạo ảnh); **`gemini-3.8-flash-high`** cho sửa nhanh (prompt D).
4. Chọn **một** trong hai cách:
   - **Một lần:** dán *PROMPT TỔNG* (mục 1). Nhanh, nhưng nếu tác nhân dừng giữa chừng thì phải nhắc tiếp.
   - **Từng bước (khuyến nghị):** dán lần lượt **A → B → C**, đợi mỗi bước xong rồi mới sang bước sau. Chỉ chạy **một** prompt ghi vào `slides/` tại một thời điểm.
5. Khi xong: mở `slides/build/IoT_RobotArm_Presentation.pdf`, đọc `slides/build/REPORT.md`, chạy
   `python3 -I slides/tools/qa_deck.py slides/build/IoT_RobotArm_Presentation.pptx` và đi qua checklist ở `00_DOC_TRUOC.md`.
6. Muốn **mình (Claude) bấm chạy Antigravity thay bạn** qua công cụ `mcp-agy`: nói "chạy Antigravity". Mình sẽ dùng `agy_start_task` (model `gemini-4-argon-medium`),
   `agy_wait`, rồi kiểm bằng `check_facts.py`, `qa_deck.py` và đọc `REPORT.md`. `agy_get_diff` có thể không liệt kê file mới chưa theo dõi trong git (thư mục `slides/` đang untracked).
   Mình **không tự chạy** khi bạn chưa bảo.

---

## 1 · PROMPT TỔNG (dựng cả bộ slide trong một lần)

```text
GOAL
Build the final presentation deck for a student IoT project ("a 4-servo robot arm; two cameras tell the operator which keys to press"): a 25-slide
Vietnamese PowerPoint (.pptx; 14 main slides + 11 backup slides A-K), a PDF export and a QA report, in the same visual language as the reference deck,
using the prepared real photos and the two AI illustrations you generate.

WORKSPACE
/Users/duongnad/Documents/project/Project_IoT/slides/   (every path below is relative to it; WRITE only inside this folder)

WHAT THE PRODUCT IS (so you can sanity-check the documents; the code was simplified on 2026-11-02 and the old design is gone)
Two cameras see an A4 sheet with 4 ArUco markers. vision.py finds a coloured object; control.py ("group 1") turns its position into target angles for three servos
(base, shoulder, elbow) and a list of key presses; success.py ("group 2") says whether those three servos are within 2 degrees of the target and counts a success after 1 s.
The screen shows only: which key, how many times, left/right how many degrees; then DONE or not. A HUMAN presses the keys; nothing is automatic.
There is NO five-step grasp, NO S1/S2 camera check, NO Auto-Step, NO attempts.csv, NO in-app Y/E calibration: they were removed and appear only in backup slide I as history.

READ FIRST, IN THIS ORDER
1. 00_DOC_TRUOC.md       (skim: context, assumptions, open placeholders)
2. 06_PHONG_CACH.md      (design system: colour tokens, fonts, masters, layout patterns with coordinates)
3. 01_KICH_BAN_SLIDE.md  (the content of every slide: exact Vietnamese on-slide text, pictures, layout pattern, speaker notes)
4. 05_SO_LIEU_VA_NGUON.md (the ONLY allowed facts and numbers; its section 14 "CẤM NÓI" lists claims you must never write)
5. 02_ANH_THAT.md and assets/manifest.json (prepared real photos with Vietnamese alt text; assets/real/_preview.jpg shows all of them)
6. 03_PROMPT_ANH_AI.md   (prompts for the AI illustrations)
7. assets/reference/gamota_helpers.js (helper code to start from), assets/reference/sample_slides_body.js (WORKING, already-rendered code for slides 3, 7, 9, 10 and 18:
   reuse it) and the images assets/reference/gamota_contact_*.png and gamota_p*.png (LOOK at them: this is the target look)
You may READ ../README.md, ../control.py, ../success.py, ../screen.py to verify a fact, never modify them. If a statement in 01 or 05 contradicts them, do NOT pick one silently:
build that slide with the text of 01, and list the contradiction under "Contradictions" in build/REPORT.md.

STEPS
0. Preflight. Run: python3 -I tools/check_facts.py . If its last line is not "KHỚP", build nothing: copy its output to build/REPORT.md and stop.
1. AI images. For prompts 1 and 3 of 03_PROMPT_ANH_AI.md (prompts 2, 4, 5, 6 are optional: skip them) generate, with your image tool, 3 variations each, pick the best,
   and save PNG at the stated size to assets/ai/<name>.png plus assets/ai/<name>.prompt.txt. Open every image and check it against the checklist at the end of
   03_PROMPT_ANH_AI.md (no letters, black 4-axis arm, palette only). Regenerate up to 3 times; if still bad, leave it missing (the build draws a dashed
   "THIẾU ẢNH" box) and report it. If you cannot generate images at all, say so in the report and continue.
2. Build. Create build/build_deck.js starting from assets/reference/gamota_helpers.js (keep the helpers, the masters and the DECK_FONT switch; default font Arial).
   Implement all 25 slides of 01_KICH_BAN_SLIDE.md in order: exact Vietnamese text, pictures, layout patterns, speaker notes (notes = the "Ghi chú diễn giả" block:
   the spoken text, then "Nếu được hỏi:", then "Nguồn:"). Diagrams (slides 3, 7 and 18) are drawn with native PPTX shapes using the coordinates in
   06_PHONG_CACH.md and assets/reference/sample_slides_body.js, not with pictures (slides 21 and 23 are pictures/tables only). Then: cd build && npm init -y && npm i pptxgenjs && node build_deck.js  ->  build/IoT_RobotArm_Presentation.pptx
3. Render and LOOK. Convert to PDF: soffice --headless --convert-to pdf --outdir build/pdf build/IoT_RobotArm_Presentation.pptx
   (add -env:UserInstallation=file:///tmp/lo_profile_agy if soffice is busy). Render every page to PNG (python3 + PyMuPDF: page.get_pixmap(matrix=fitz.Matrix(1, 1)))
   into build/pages/ and OPEN EVERY PAGE IMAGE. Fix any text overflow or overlap, body text under 11 pt (footers under 10 pt), cramped or clipped text,
   distorted or badly cropped pictures, unreadable chips, wrong colours. Repeat until all 25 pages are clean.
4. QA. python3 -I tools/qa_deck.py build/IoT_RobotArm_Presentation.pptx   (pip install python-pptx if missing). Fix every ERROR. Read every WARN and INFO and
   either fix it or consciously accept it (say why in the report).
5. Finish. Copy the final PDF to build/IoT_RobotArm_Presentation.pdf and write build/REPORT.md.

RULES
- Facts: use ONLY 05_SO_LIEU_VA_NGUON.md. Never invent a number, date, name or result. Never turn "chưa kiểm chứng / chưa đo / chưa làm" into a success claim.
  Never write anything listed under section 14 "CẤM NÓI". In particular never present as a feature or a result: automatic grasping, any success rate, S1/S2, a five-step grasp,
  Auto-Step, attempts.csv, keys Y/E, "servo hết nóng", MQTT / dashboard / ESP32 / FSR. Say "XONG" means three servo angles reached the suggestion, not that an object was grasped.
- Direction: on slides and notes, left/right follow the SIDE camera (MacBook, facing the robot): key A = right, key D = left. Do not "fix" this to the robot's own point of view.
- Language: all slide text and notes are Vietnamese WITH diacritics, copied exactly from 01_KICH_BAN_SLIDE.md, without Markdown markup (no ** and no backticks on slides or in notes;
  file names use the monospace font instead). Screenshots keep their own ASCII text; never retype it.
- Placeholders in [SQUARE BRACKETS] (e.g. [TÊN MÔN HỌC], [ĐIỀN LIÊN KẾT]) stay visible on the slide exactly as written; never invent values for them. List them in the report.
- Pictures: real photos only from assets/real/ exactly as given (already cropped, laptop screens already blurred). Never stretch a picture, never enlarge it beyond
  2x its natural size, give every picture the alt text from assets/manifest.json (alt_vi). The screen images ui_screen_before / ui_screen_done / sw_annot_* / calib_before_after_side
  are simulations or stored-photo runs: use exactly the captions written in 01 and never call them live. AI pictures only on slides 2 and 14, always with the caption tag
  "Minh họa (AI)", never on slides 5, 6, 8, 9, 10, 11, 12, 13. Use no picture that 01_KICH_BAN_SLIDE.md does not list.
- Style: follow 06_PHONG_CACH.md (palette tokens, 16:9 at 13.333 x 7.5 in, masters CONTENT / CONTENT_ALT / PLAIN / STATEMENT, one idea per slide, no emoji,
  no clip art, no gradients, at most three accent colours per slide). Body text at least 11 pt.
- Safety: do NOT modify anything outside slides/ (no Python code, README, firmware, git). Do NOT commit or push. Do NOT run main.py, open serial ports, access cameras
  or touch the Arduino. Treat assets/real/ and assets/reference/ as read-only. Network use only for npm / pip install.
- The whole deck must be reproducible with: node build/build_deck.js

DONE WHEN (all checkable)
- python3 -I tools/check_facts.py ended with "KHỚP" before you started building.
- build/IoT_RobotArm_Presentation.pptx exists with 25 slides, every slide has speaker notes containing a "Nguồn:" line; build/IoT_RobotArm_Presentation.pdf exists.
- python3 -I tools/qa_deck.py build/IoT_RobotArm_Presentation.pptx prints "QA OK" (no ERROR).
- You opened all 25 rendered page images and none shows overflowing, overlapping or clipped text, or a distorted picture.
- build/REPORT.md lists: files produced; AI images generated or missing; remaining [placeholders]; every deviation from 01_KICH_BAN_SLIDE.md and why; Contradictions (if any);
  remaining WARN / INFO lines from the QA script; anything you could not verify.
```

---

## 2 · Chia nhỏ (khuyến nghị)

### A · Tạo ảnh AI

```text
GOAL
Generate two AI illustrations for a presentation and save them to disk.

FILES
Work in /Users/duongnad/Documents/project/Project_IoT/slides/. Read 03_PROMPT_ANH_AI.md completely (style block, rules, prompts 1 and 3, checklist).
Reference photos (shape reference only, never copy their background): assets/real/hw_arm_gripper.jpg, assets/real/demo_06_grip_top.jpg.
Output: assets/ai/ai_01_problem_depth.png (1536x1536), assets/ai/ai_03_future_autonomous.png (1200x1500),
each with a matching <name>.prompt.txt (the exact prompt used and which of the 3 variations you chose).

RULES
- Prepend the STYLE / ARM / CUP / SHEET blocks to every prompt exactly as written. No text, letters, numbers, logos, watermarks or faces in any image.
- The arm must be a small black DESKTOP 4-axis arm with a two-finger parallel gripper and no wrist; never an industrial orange or humanoid robot.
- Generate 3 variations per prompt, choose the best, regenerate up to 3 times per prompt if the checklist fails. Skip prompts 2, 4, 5, 6 (optional, not used in the deck).
- Create only files inside assets/ai/. Modify nothing else.

DONE WHEN
- The two PNG files exist with the stated pixel sizes (verify with Pillow) and you have opened each one and ticked the checklist of 03_PROMPT_ANH_AI.md.
- Final message lists, for each image, the chosen variation and any remaining defect. If an image could not be made acceptable, say so and do not save it.
```

### B · Dựng bộ slide

```text
GOAL
Build the 25-slide Vietnamese PPTX of the Project IoT robot-arm presentation and its PDF.

FILES
Work in /Users/duongnad/Documents/project/Project_IoT/slides/. Run first: python3 -I tools/check_facts.py  (if its last line is not "KHỚP", stop and report its output).
Read, in order: 06_PHONG_CACH.md, 01_KICH_BAN_SLIDE.md, 05_SO_LIEU_VA_NGUON.md, 02_ANH_THAT.md, assets/manifest.json. Start from the code in assets/reference/gamota_helpers.js,
reuse the working code in assets/reference/sample_slides_body.js (slides 3, 7, 9, 10, 18), and LOOK at assets/reference/gamota_contact_*.png and gamota_p*.png.
Pictures: assets/real/* (given, read-only) and assets/ai/* (may be partly missing: the helper draws a dashed placeholder).
Output: build/build_deck.js, build/IoT_RobotArm_Presentation.pptx, build/IoT_RobotArm_Presentation.pdf, build/pages/*.png.

RULES
- Implement every slide of 01_KICH_BAN_SLIDE.md with its exact Vietnamese on-slide text, pictures, pattern and speaker notes (spoken text, then "Nếu được hỏi:", then "Nguồn:").
  Diagrams on slides 3, 7 and 18 are native PPTX shapes using the coordinates in 06_PHONG_CACH.md and assets/reference/sample_slides_body.js.
- Facts only from 05_SO_LIEU_VA_NGUON.md; never write anything under its section 14 "CẤM NÓI"; keep every [SQUARE BRACKET] placeholder visible and unchanged.
  A = right and D = left as seen from the side camera. "XONG" means three servo angles reached the suggestion, nothing more.
- Copy text without Markdown markup (no ** and no backticks on slides or in notes).
- Never stretch pictures; alt text from manifest.json (alt_vi); AI pictures only on slides 2 and 14 with the tag "Minh họa (AI)". Screen images use the captions of 01 (they are stored-photo runs with a simulated arm, never "live").
- Default font Arial (the DECK_FONT switch in the helper); body text at least 11 pt; slide size 13.333 x 7.5 in.
- Install with: cd build && npm init -y && npm i pptxgenjs. Convert to PDF with soffice --headless --convert-to pdf. Render each page to PNG with PyMuPDF and OPEN EVERY PAGE IMAGE;
  fix overflow, overlap, clipped or tiny text and rebuild until all 25 pages are clean.
- Do not modify anything outside slides/build/. Do not commit. Do not run main.py or touch cameras or serial ports.

DONE WHEN
- build/IoT_RobotArm_Presentation.pptx has 25 slides, each with notes containing a "Nguồn:" line, and the PDF exists.
- You opened all 25 page images and none has overflowing, overlapping or clipped text or a distorted picture.
- Final message lists any slide you could not complete and why.
```

### B2 · Thêm ảnh thật mới (khi bạn chụp thêm, xem `02_ANH_THAT.md` mục 6)

```text
GOAL
Integrate newly taken real photos into the asset set without changing anything that is already used.

FILES
Work in /Users/duongnad/Documents/project/Project_IoT/slides/. New photos are in assets/real_new/ (any file names). Read 01_KICH_BAN_SLIDE.md and assets/manifest.json.
Read tools/prepare_real_assets.py for the blur method (Pillow: polygon mask, feathered, Gaussian blur radius about 26). Output goes to assets/real/ and assets/manifest.json.

RULES
- For each new photo: open it; if any laptop or phone screen, readable text or face is visible, blur those regions; save as JPEG quality 90 with the long side at most 1920 px
  to assets/real/new_<nn>_<short_ascii_name>.jpg; append an entry to assets/manifest.json (file, size_px, group "new", desc_vi, alt_vi, slides [], note_vi) in Vietnamese.
- Write assets/NEW_PHOTOS.md proposing, per photo, which slide it could replace or complement (use 01_KICH_BAN_SLIDE.md) and why. Do NOT edit 01_KICH_BAN_SLIDE.md or build/build_deck.js.
- Never overwrite or delete existing files in assets/real/. Never use a photo showing a face without telling me.
- A photo of the program's screen taken during a LIVE run with the arm connected is the most valuable one (slides 8, 9, 13): say so in NEW_PHOTOS.md and note what its footer says (USB Arduino: DA KET NOI or MO PHONG).

DONE WHEN
- Every new photo has a processed copy in assets/real/ and a manifest entry; NEW_PHOTOS.md exists; the final message lists photos that needed blurring and any you rejected.
```

### C · Kiểm tra và sửa

```text
GOAL
Review the built deck against its specification and fix every defect.

FILES
Work in /Users/duongnad/Documents/project/Project_IoT/slides/. Deck: build/IoT_RobotArm_Presentation.pptx, source build/build_deck.js. Spec: 01_KICH_BAN_SLIDE.md, 05_SO_LIEU_VA_NGUON.md,
06_PHONG_CACH.md. Tools: tools/qa_deck.py, tools/check_facts.py.

STEPS
1. Render all pages to build/pages/*.png and OPEN EVERY ONE. Write build/REVIEW.md: per slide, list defects (text overflow or overlap, text under 11 pt, clipped or cramped text,
   distorted or badly placed picture, on-slide text that differs from 01_KICH_BAN_SLIDE.md, missing or short speaker notes, any claim listed under section 14 "CẤM NÓI", any trace of the
   removed design: S1/S2, five steps, Auto-Step, attempts.csv, keys Y/E, "tự động" used as a feature, a screen image described as live).
2. Fix them in build/build_deck.js, rebuild, re-render, run: python3 -I tools/qa_deck.py build/IoT_RobotArm_Presentation.pptx. Repeat until there is no ERROR and REVIEW.md has no open defect.
3. Rewrite build/REPORT.md.

RULES
- Change only what a defect requires. Do not redesign slides, do not add content, do not touch anything outside slides/build/.
- Never remove a [SQUARE BRACKET] placeholder or soften a "chưa kiểm chứng" statement.

DONE WHEN
- qa_deck.py prints "QA OK"; REVIEW.md lists defects found and how each was fixed; the final PDF is rebuilt from the final PPTX.
```

### D · Sửa theo nhận xét của bạn (mẫu, điền danh sách rồi dán; model nhanh là đủ)

```text
GOAL
Apply exactly the fixes below to the deck and nothing else.

FIXES
- Slide <N>: <what is wrong and what you want, quoting the on-slide text>
- Slide <M>: <...>

FILES
/Users/duongnad/Documents/project/Project_IoT/slides/build/build_deck.js (edit), 01_KICH_BAN_SLIDE.md and 05_SO_LIEU_VA_NGUON.md (read only).

RULES
- Change only the listed slides. Keep all other slides' content identical. Keep facts within 05_SO_LIEU_VA_NGUON.md. Rebuild with node build_deck.js, convert to PDF,
  render only the touched slides and open them, then run python3 -I tools/qa_deck.py build/IoT_RobotArm_Presentation.pptx.
- Do not edit 01_KICH_BAN_SLIDE.md unless a fix says so; if a fix contradicts 05_SO_LIEU_VA_NGUON.md, stop and say so instead of applying it.

DONE WHEN
- The listed slides match the fixes, QA prints "QA OK", and the final message states for each fix what you changed.
```

### E · Bản Windows (phông Segoe UI) và video

```text
GOAL
(1) Produce a second PPTX that uses the Gamota font, for Windows PowerPoint. (2) If assets/real/video/demo_gap.mp4 exists, add that video to slide 10.

FILES
/Users/duongnad/Documents/project/Project_IoT/slides/build/build_deck.js and assets/reference/gamota_helpers.js (the DECK_FONT switch). 01_KICH_BAN_SLIDE.md slide 10.

STEPS
1. Make sure build_deck.js still honours the environment variable DECK_OUT (output path; the helper in assets/reference/gamota_helpers.js already does). Run, from slides/:
   DECK_FONT="Segoe UI" DECK_OUT=build/IoT_RobotArm_Presentation_SegoeUI.pptx node build/build_deck.js
   Do NOT overwrite the Arial deck. (Segoe UI is narrower than Arial, so no layout change is needed; skip the PDF for this version.)
2. If the video file exists: on slide 10 add it with pptxgenjs addMedia({type: "video", path, x, y, w, h, cover: assets/real/demo_06_grip_side.jpg}) at the right of the photo grid,
   shrink the six photos to make room (keep their order and captions), and add the caption "Video thật 02/11/2026". If the file does not exist, do nothing for step 2 and say so.

RULES
- Touch only build/. Keep every other slide identical. Run python3 -I tools/qa_deck.py on both PPTX files.

DONE WHEN
- build/IoT_RobotArm_Presentation_SegoeUI.pptx exists and passes QA; the Arial deck is unchanged except possibly slide 10; the final message says whether the video was added.
```

### F · Làm mới số liệu khi mã đã đổi (chạy khi `check_facts.py` báo `LỆCH`)

```text
GOAL
Bring the fact documents back in line with the current code after the code changed, touching as little as possible.

FILES
Work in /Users/duongnad/Documents/project/Project_IoT/slides/. Read-only sources of truth: ../README.md, ../control.py, ../success.py, ../screen.py, ../vision.py, ../calibration.json,
../robot_arm_4dof/robot_arm_4dof.ino. Edit only: 05_SO_LIEU_VA_NGUON.md (section 17 "facts" block and the rows it affects), then the sentences in 01_KICH_BAN_SLIDE.md that quote the changed values.

STEPS
1. Run python3 -I tools/check_facts.py and copy its LỆCH / THIẾU lines into slides/build/REFRESH_REPORT.md.
2. For each LỆCH line: open the cited code, update the value in 05 section 17 and in the table row of 05 that states it (keep the label [CODE] / [ĐO] / [MÔ PHỎNG] / [CHƯA] honest:
   a value you cannot verify in code stays with its old label and a note "chưa kiểm lại"), then update every sentence in 01 that quotes it (on-slide text AND speaker notes AND "Nguồn:" lines).
3. For each dead citation (a `file:line` whose file or line no longer exists), re-find the code and fix the citation; if the code was deleted, delete the claim and say so in the report.
4. Run check_facts.py again; it must end with "KHỚP".

RULES
- Never write a new fact that the code does not show. Never upgrade a "chưa" to a result. If the code gained or lost a FEATURE (not just a number), do not rewrite slides yourself:
  list the change in REFRESH_REPORT.md under "Needs a human decision" and stop.
- Touch nothing outside the two files above and build/REFRESH_REPORT.md. No commits.

DONE WHEN
- check_facts.py ends with "KHỚP", or REFRESH_REPORT.md says exactly which lines still disagree and why.
```

---

## 3 · Việc Antigravity không làm được (bạn làm)

- Điền các chỗ `[…]` (tên môn, ngày, thành viên, liên kết video, kịch bản demo, phân công người nói). Danh sách đầy đủ: `00_DOC_TRUOC.md` mục 3.
- Quay video gắp, chụp ảnh mới (`02_ANH_THAT.md` mục 6). **Quý nhất:** một ảnh màn hình chương trình lúc **chạy trực tiếp với cánh tay thật** và ghi `XONG!`.
- Mã nguồn mới đã lên GitHub (`main` = `e3f2d85`, 03/11/2026), nên slide 14 trỏ tới repo được. Nhớ rằng bản dựng sẵn `slides/Project_IoT_ThuyetTrinh.pptx` (25 slide, 4 phần cho 4 người, `build_slides.py`) đã có; bộ này là phương án 25 slide kiểu Gamota.
- Chạy thật những việc đang ghi "chưa kiểm chứng" nếu muốn đổi chữ trên slide (bấm theo gợi ý đã hiệu chỉnh và đếm `Thanh cong`; hiệu chỉnh lại cho tờ giấy mới), rồi **sửa `05_SO_LIEU_VA_NGUON.md` trước**, sau đó mới sửa slide.
