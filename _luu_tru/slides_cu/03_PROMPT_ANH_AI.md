# 03 · Prompt ảnh AI

Antigravity (Gemini) tự tạo ảnh bằng công cụ ảnh của nó từ các prompt dưới đây (tiếng Anh, vì mô hình ảnh hiểu tốt hơn).
**Chỉ 2 ảnh bắt buộc** (prompt 1 cho slide 2, prompt 3 cho slide 14) + 4 ảnh tùy chọn (prompt 2, 4, 5, 6: **không dùng trong deck mặc định**). Ảnh thật vẫn là chủ đạo của bộ slide; ảnh AI chỉ để hình dung khái niệm.
Bản trước có ảnh AI thứ ba cho slide "S1/S2 hai camera cùng đồng ý"; slide đó đã bỏ cùng S1/S2 nên prompt 2 được viết lại thành tùy chọn.

## Quy tắc (bắt buộc)

1. **Không chữ, không số, không logo, không watermark, không khuôn mặt** trong mọi ảnh (mô hình ảnh vẽ chữ và dấu tiếng Việt rất tệ; mọi chữ do PPTX tự vẽ).
2. Mỗi prompt: tạo **3 biến thể**, chọn 1 ảnh tốt nhất, lưu **PNG** đúng tên và kích thước vào `slides/assets/ai/`, kèm file `<tên>.prompt.txt` ghi prompt đã dùng và biến thể được chọn.
3. Kiểm theo danh sách ở cuối file; ảnh không đạt thì tạo lại (tối đa 3 lượt mỗi prompt). Vẫn không đạt thì **để trống ảnh đó** và ghi vào báo cáo: bản dựng sẽ vẽ ô "THIẾU ẢNH", slide vẫn dùng được.
4. Trên slide, ảnh AI **luôn kèm nhãn "Minh họa (AI)"** và **không đặt ở slide kết quả hay bằng chứng** (5, 6, 8, 9, 10, 11, 12, 13); mặc định chỉ có ở slide 2 và 14.
5. **Cánh tay phải đúng loại.** Mô hình ảnh hay vẽ cánh tay công nghiệp 6 trục màu cam hoặc robot hình người; cánh tay của dự án là *cánh tay để bàn nhỏ, màu đen, 4 trục (đế, vai, khuỷu, kẹp), tay kẹp hai ngón song song, không có cổ tay*. Đính kèm ảnh tham chiếu: `assets/real/hw_arm_gripper.jpg` và `assets/real/demo_06_grip_top.jpg` (chỉ để lấy hình dạng cánh tay, kẹp và cốc; **không** chép nền, laptop hay mặt bàn).

## Khối phong cách (dán vào đầu MỌI prompt)

```text
STYLE: Flat editorial vector illustration with a subtle paper-grain texture, calm and technical, generous negative space, soft diffuse shadows only.
Use ONLY this palette and its tints: warm milk-white background #FBF8F1, ivory #F3EDE1, brown-charcoal line work #2B2520, deep teal #2F6A56,
terracotta #A64B24, dusty indigo #5C5A8E. Consistent 2 px outlines. No gradients except very soft shadows.
ABSOLUTELY NO text, letters, numbers, digits, characters, logos, brand marks, watermarks, UI screenshots or code anywhere in the image.
No photorealism, no 3D render, no glossy or neon effects, no human faces.

ARM (use whenever a robot arm appears): a small DESKTOP 4-axis robot arm made of black angular bracket links, four rectangular black hobby servos
with orange-yellow-brown wire bundles, a rotating base, a shoulder, an elbow and a two-finger parallel-linkage gripper with two long slender fingers.
It has NO wrist joint. It is NOT an industrial orange robot, NOT humanoid, NOT a six-axis arm.
CUP: a small orange-red paper cup about 5 cm tall with a slightly wider lid.
SHEET: a white A4 sheet with a small black-and-white square pattern (an abstract marker, unreadable) near each of its four corners.
```

---

## Prompt 1 · `ai_01_problem_depth.png` (bắt buộc)

- **Dùng ở:** slide 2, thẻ "KHÓ Ở ĐÂU". **Tỉ lệ:** vuông 1:1, **1536 × 1536 px**. **Nhãn:** "Minh họa (AI)".
- **Ảnh tham chiếu:** `assets/real/hw_arm_gripper.jpg`.

```text
[STYLE + ARM + CUP + SHEET blocks above]
Subject: a clean three-quarter view of a desk, seen from above-left. In the foreground an operator's two hands rest on a laptop keyboard
(only the hands and the keyboard are visible, no faces, the laptop screen is not shown). In the middle ground the small black 4-axis desktop
robot arm reaches toward one orange-red paper cup standing on a white A4 sheet with a small marker pattern at each corner.
The idea is UNCERTAIN DEPTH: draw two faint dashed projection lines, one running from the gripper tip and one from the cup, that run toward each other
but visibly do not meet, with a thin terracotta double-headed bracket between their ends marking the unknown gap.
Mood: calm but slightly tense. Teal accents on the arm, terracotta on the cup and on the gap bracket.
Composition: square, subject centred, generous margins on all sides so it can sit inside a rounded card.
```

**Alt text:** `Minh họa AI: hai bàn tay trên bàn phím laptop, cánh tay robot đen vươn tới cốc đỏ trên tờ giấy A4, hai đường nét đứt gần chạm nhau nhưng không gặp nhau để thể hiện khó ước lượng độ sâu`

## Prompt 2 · `ai_02_two_cameras.png` (tùy chọn, không dùng trong deck mặc định)

- **Dùng ở:** không có slide mặc định (bản trước dùng cho slide S1/S2 đã bỏ). Dùng nếu bạn muốn một ảnh "hai camera, một cảnh" cho tài liệu hoặc slide 3. **Tỉ lệ:** 4:3, **1600 × 1200 px**. **Nhãn:** "Minh họa (AI)".
- **Ảnh tham chiếu:** `assets/real/hw_overview_side.jpg` (chỉ lấy bố cục tờ giấy, cốc và cánh tay; không chép nền).

```text
[STYLE + ARM + CUP + SHEET blocks above]
Subject: a clean concept illustration of ONE scene watched by TWO fixed cameras. A white A4 sheet lies on a tabletop with a small marker pattern at each corner;
one orange-red paper cup stands on it and the small black 4-axis robot arm waits at the edge of the sheet.
Camera A: a small black cylindrical camera on a thin boom high above, looking straight down, with a translucent teal view cone that covers the whole sheet.
Camera B: a small black camera low in front of the sheet at table height, looking along the table, with a translucent dusty-indigo view cone.
Where the two cones overlap above the sheet draw a soft terracotta glow with a thin dotted coordinate grid on the sheet, to suggest one shared coordinate system.
Minimal and technical; lots of negative space around the subject.
```

**Alt text:** `Minh họa AI: hai camera, một phía trên nhìn xuống và một đặt thấp nhìn ngang, cùng quan sát tờ giấy A4 có cốc đỏ và cánh tay robot; vùng giao của hai chùm nhìn có lưới tọa độ chung`

## Prompt 3 · `ai_03_future_autonomous.png` (bắt buộc)

- **Dùng ở:** slide 14, panel phải (chỉ là hướng phát triển, không phải kết quả: bản hiện tại để người bấm phím). **Tỉ lệ:** 4:5 dọc, **1200 × 1500 px**. **Nhãn:** "Hướng phát triển (minh họa AI), không phải kết quả đã đạt".
- **Ảnh tham chiếu:** `assets/real/hw_arm_gripper.jpg`.

```text
[STYLE + ARM + CUP + SHEET blocks above]
Subject: an optimistic near-future workshop scene, 4:5 portrait. The small black 4-axis desktop robot arm places orange-red paper cups one by one
into a shallow wooden tray on a tidy table; three cups already sit in the tray, a fourth is held in the gripper, a fifth still stands on the white A4 sheet.
Soft teal dotted arcs show the planned motion paths from the sheet to the tray. A subtle translucent dusty-indigo overhead camera frustum covers the sheet
and the tray. Warm window light from the left with long soft shadows. Calm and hopeful. Leave generous empty space at the top.
```

**Alt text:** `Minh họa AI về hướng phát triển: cánh tay robot đặt từng cốc đỏ vào khay gỗ, đường chấm xanh là quỹ đạo đã lập kế hoạch, camera phía trên bao quát tờ giấy và khay`

## Prompt 4 · `ai_04_cover_alt.png` (tùy chọn: bìa minh họa thay cho bìa ảnh thật)

- **Dùng ở:** slide 1 nếu bạn muốn bìa minh họa; mặc định bìa dùng ảnh thật nên **bỏ qua** prompt này. **Tỉ lệ:** 4:5, **1200 × 1500 px**.

```text
[STYLE + ARM + CUP blocks above]
Subject: a poster-like 4:5 composition. A single small black 4-axis desktop robot arm in the centre holds one orange-red paper cup between its two fingers.
Behind it, a large faint measuring grid of thin brown-charcoal lines on warm paper, with four large square marker patterns (abstract black-and-white squares,
unreadable) forming the corners of the grid. Thin concentric teal and indigo arcs radiate from the two top corners like camera sight-lines converging on the cup.
Lots of negative space; leave the bottom third almost empty for a title.
```

## Prompt 5 · `ai_05_isometric_workbench.png` (tùy chọn: hình tổng quan góc isometric)

- **Dùng ở:** không có slide mặc định; dùng nếu bạn muốn một ảnh "toàn cảnh hệ thống" cho tài liệu hoặc poster. **Tỉ lệ:** 16:9, **1920 × 1080 px**.

```text
[STYLE + ARM + CUP + SHEET blocks above]
Subject: a 16:9 isometric flat illustration of a compact lab desk: a laptop whose screen shows only abstract coloured blocks (no readable text), a white A4 sheet
with a small marker pattern at each corner, the small black 4-axis robot arm on a clear acrylic base next to a blue Arduino-style circuit board and a metal mesh
power-supply box drawn as simple shapes, an overhead camera on a thin boom above the sheet and a second camera low in front of it, a few thin teal cables.
One orange-red paper cup on the sheet. Soft cast shadows, calm technical mood, everything simplified.
```

## Prompt 6 · `ai_06_qa_divider.png` (tùy chọn: nền cho slide hỏi đáp)

- **Dùng ở:** không có slide mặc định; dùng làm nền nếu bạn thêm slide "Hỏi đáp". **Tỉ lệ:** 16:9, **1920 × 1080 px**.

```text
[STYLE block above]
Subject: a very calm abstract 16:9 background: warm milk-white paper with a faint large grid of thin lines, a few soft translucent teal and indigo arcs
sweeping in from the right edge like camera sight-lines, and one tiny terracotta dot where they converge. Generous empty space on the left two thirds for a title.
No objects, no text.
```

---

## Danh sách kiểm sau khi tạo (mỗi ảnh)

- [ ] không có chữ, số, ký tự, logo, watermark, khuôn mặt (phóng to kiểm tra góc ảnh và trên thiết bị)
- [ ] cánh tay đúng loại: màu đen, **4 trục**, tay kẹp **hai ngón** song song, **không** cổ tay, không giống robot công nghiệp cam hay hình người
- [ ] chỉ dùng bảng màu đã cho, không neon, không bóng bẩy; hạt giấy mịn
- [ ] đúng tỉ lệ và kích thước; chủ thể không sát mép (để vừa thẻ bo góc)
- [ ] cốc nhỏ màu cam đỏ; tờ A4 trắng với bốn ô vuông nhỏ ở góc (không đọc được thành mã thật)
- [ ] đã lưu `assets/ai/<tên>.png` và `assets/ai/<tên>.prompt.txt`
