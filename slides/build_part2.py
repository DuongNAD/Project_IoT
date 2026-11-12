#!/usr/bin/env python3
"""
Dựng các slide MỚI của phần 2 (Computer vision & Hỗ trợ gắp) thành một tệp riêng để nhập vào Canva:
  1 slide ngăn phần · 1 sơ đồ luồng dữ liệu · 1 slide hình "Nhận diện vật" (lấy từ build_slides.py) ·
  6 slide code thật (main.py, cameras.py, vision.py x2, success.py, screen.py).
Code trên slide đọc thẳng từ các tệp .py của dự án (tìm theo tên hàm, ghi đúng số dòng), nên luôn khớp mã hiện tại.
Dòng code dài được ngắt xuống dòng ngay trên slide (nội dung giữ nguyên); số tròn cạnh dòng code ứng với các bước ở trên khung code.

    python slides/build_part2.py      ->  slides/Phan2_LuongDuLieu_Code.pptx (+ .pdf, ảnh preview_phan2/slide_XX.png)
                                          slides/KetLuan.pptx (+ .pdf, ảnh preview_ketluan/): Kết luận + Tóm tắt và hỏi đáp (hai slide cuối)
"""

import os
import re
import sys

from pptx import Presentation
from pptx.util import Emu, Inches, Pt

import build_slides as B
from build_slides import (BG2, CARD, CENTER, INDIGO, INK, LINE, M, MIDDLE, MONO, MUTED, ORANGE, ORANGE_SOFT, RIGHT, STATEMENT, TEAL,
                          TEAL_SOFT, TEXT2, W, box, chip, chip_w, dot, header, label, line, name, new_slide, notes, rule, text)

PROJECT = os.path.dirname(B.SLIDES_DIR)
OUT = os.path.join(B.SLIDES_DIR, "Phan2_LuongDuLieu_Code.pptx")
PREVIEW_DIR = os.path.join(B.SLIDES_DIR, "preview_phan2")
CONCLUSION_OUT = os.path.join(B.SLIDES_DIR, "KetLuan.pptx")  # Slide kết luận riêng, để tải lên Canva
CONCLUSION_PREVIEW_DIR = os.path.join(B.SLIDES_DIR, "preview_ketluan")
EYEBROW = "02 · Computer vision & Hỗ trợ gắp"


# ==============================================================================
# Đọc code thật: tìm dòng theo nội dung, khối hàm theo thụt lề
# ==============================================================================
def src(path):
    with open(os.path.join(PROJECT, path), encoding="utf-8") as f:
        return f.read().split("\n")


def find(path, needle, start=1):
    """Số dòng (đếm từ 1) đầu tiên từ dòng `start` có chứa `needle`."""
    for no, line_ in enumerate(src(path)[start - 1:], start):
        if needle in line_:
            return no
    raise SystemExit(f"Không thấy {needle!r} trong {path}: mã đã đổi, sửa build_part2.py")


def span(path, needle):
    """(dòng đầu, dòng cuối) của hàm / lớp bắt đầu ở dòng có `needle`: tới dòng cuối còn thụt lề sâu hơn dòng đầu."""
    lines, first = src(path), find(path, needle)
    indent = len(lines[first - 1]) - len(lines[first - 1].lstrip())
    last = first
    for no in range(first + 1, len(lines) + 1):
        t = lines[no - 1]
        if t.strip() and len(t) - len(t.lstrip()) <= indent and not t.lstrip().startswith((")", "]", "}")):
            break
        if t.strip():
            last = no
    return first, last


def lines_text(ranges, dash="-"):
    return ", ".join(str(a) if a == b else f"{a}{dash}{b}" for a, b in ranges)


def where(path, ranges):
    return f"{path}:" + lines_text(ranges).replace(" ", "")


# ==============================================================================
# Khung code: số dòng thật, tô màu đơn giản, ngắt dòng dài, số tròn đánh dấu bước
# ==============================================================================
KEYWORDS = re.compile(r"\b(def|class|return|if|elif|else|for|in|not|and|or|is|None|True|False|with|while|continue|break|import|from|"
                      r"lambda|try|except|as|raise)\b")
TOKEN = re.compile(r"(f?\"[^\"]*\"|f?'[^']*'|\b\d+(?:\.\d+)?\b|" + KEYWORDS.pattern + ")")
ROW = 1.12  # Khoảng cách dòng code = 1,12 lần cỡ chữ
STYLE = {"code": (INK, False, False), "kw": (TEAL, True, False), "str": (ORANGE, False, False), "num": (INDIGO, False, False),
         "com": (MUTED, False, True)}


def comment_start(s):
    """Vị trí dấu # mở chú thích (bỏ qua # nằm trong chuỗi), không có thì len(s)."""
    quote, i = None, 0
    while i < len(s):
        c = s[i]
        if quote:
            if c == "\\":
                i += 1
            elif c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif c == "#":
            return i
        i += 1
    return len(s)


def styled(s, in_doc):
    """Danh sách kiểu cho từng ký tự của một dòng code."""
    if in_doc or s.strip().startswith('"""'):
        return ["com"] * len(s)
    cut = comment_start(s)
    kinds = ["code"] * cut + ["com"] * (len(s) - cut)
    for m in TOKEN.finditer(s[:cut]):
        tok = m.group(0)
        kind = "str" if tok[-1] in "\"'" else "num" if tok[0].isdigit() else "kw"
        kinds[m.start():m.end()] = [kind] * len(tok)
    return kinds


def wrap(s, kinds, cols):
    """Ngắt một dòng dài thành nhiều hàng (ưu tiên chỗ trống); hàng sau thụt thêm 4 ký tự so với dòng gốc."""
    pad = len(s) - len(s.lstrip()) + 4
    rows, start, width = [], 0, cols
    while len(s) - start > width:
        cut = s.rfind(" ", start + width // 2, start + width)
        cut = cut + 1 if cut > start else start + width
        rows.append((s[start:cut].rstrip(), kinds[start:cut]))
        start, width = cut, cols - pad
    rows.append((s[start:], kinds[start:]))
    return [(t, k) if i == 0 else (" " * pad + t, ["code"] * pad + k) for i, (t, k) in enumerate(rows)]


def code_rows(path, ranges, cols):
    """Các hàng hiển thị: (số dòng hoặc None, chữ, kiểu từng ký tự). Hai đoạn cách nhau bằng hàng '...'; bỏ thụt lề chung."""
    lines = src(path)
    shown = [lines[n - 1] for a, b in ranges for n in range(a, b + 1) if lines[n - 1].strip()]
    dedent = min(len(t) - len(t.lstrip()) for t in shown)
    rows, in_doc = [], False
    for k, (a, b) in enumerate(ranges):
        if k:
            rows.append((None, "...", ["com"] * 3))
        for n in range(a, b + 1):
            s = lines[n - 1][dedent:].rstrip()
            starts_doc = s.count('"""') % 2 == 1
            for i, (t, kinds) in enumerate(wrap(s, styled(s, in_doc), cols)):
                rows.append((n if i == 0 else None, t, kinds))
            in_doc = in_doc != starts_doc
    return rows


def add_rows(tf, rows, size, numbers=False):
    """Mỗi hàng một đoạn, khoảng cách dòng cố định (hai cột số dòng / code luôn thẳng hàng)."""
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, (no, t, kinds) in enumerate(rows):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = Pt(size * ROW)
        p.space_before = p.space_after = Pt(0)
        if numbers:
            p.alignment = RIGHT
            runs = [(str(no) if no else "", "num_gutter")]
        else:
            runs, cur, kind = [], "", None
            for ch, kd in zip(t, kinds):
                if kd != kind and cur:
                    runs.append((cur, kind))
                    cur = ""
                cur, kind = cur + ch, kd
            runs.append((cur or " ", kind or "code"))
        for s, kind in runs:
            r = p.add_run()
            r.text = s
            color, bold, italic = (MUTED, False, False) if kind == "num_gutter" else STYLE[kind]
            r.font.name, r.font.size, r.font.bold, r.font.italic = MONO, Pt(size), bold, italic
            r.font.color.rgb = color


def code_panel(s, x, y, w, h, path, ranges, marks=()):
    """Khung code thật của `path` (các đoạn `ranges`); marks: [(nội dung tìm trong dòng, số tròn)]. Trả về cỡ chữ đã chọn."""
    box(s, x, y, w, h, fill=CARD, edge=LINE)
    box(s, x, y, 0.95, h, fill=BG2)
    text(s, x + 0.2, y + 0.08, w - 0.4, 0.26, f"{path}  ·  dòng " + lines_text(ranges, "–"), 10, MUTED, font=MONO,
         align=RIGHT)
    top, avail_h, code_x = y + 0.38, h - 0.47, x + 1.1
    for size in (12, 11.5, 11, 10.5, 10, 9.5, 9):
        cols = int((x + w - 0.15 - code_x) / (0.6 * size / 72))
        rows = code_rows(path, ranges, cols)
        if len(rows) * size * ROW / 72 <= avail_h:
            break
    else:
        raise SystemExit(f"Code quá dài cho một slide ({len(rows)} hàng ở 9 pt): {where(path, ranges)}")
    row_h = size * ROW / 72
    gutter = s.shapes.add_textbox(Inches(x + 0.35), Inches(top), Inches(0.55), Inches(avail_h))
    add_rows(gutter.text_frame, rows, size, numbers=True)
    body = s.shapes.add_textbox(Inches(code_x), Inches(top), Inches(x + w - 0.1 - code_x), Inches(avail_h))
    add_rows(body.text_frame, rows, size)
    lines = src(path)
    for needle, n in marks:
        no = next(no for a, b in ranges for no in range(a, b + 1) if needle in lines[no - 1])
        k = next(i for i, r in enumerate(rows) if r[0] == no)
        d = min(0.27, row_h * 1.25)
        dot(s, x + 0.06, top + k * row_h + row_h / 2 - d / 2 + 0.01, n, d=d, size=9.5)
    return size


def legend(s, items, y=1.78):
    """Hàng bước ở trên khung code: số tròn + chữ ngắn."""
    x = M
    for n, t in items:
        dot(s, x, y, n, d=0.3, size=11)
        w = B.text_w(t, 13) + 0.1
        text(s, x + 0.38, y, w, 0.3, t, 13, INK, anchor=MIDDLE)
        x += 0.38 + w + 0.3


def code_slide(prs, who, title, path, ranges, steps_, marks, notes_text):
    s = new_slide(prs)
    header(s, EYEBROW, title, who)
    legend(s, steps_)
    code_panel(s, M, 2.18, W - 2 * M, 5.1, path, ranges, marks)
    notes(s, notes_text + f"\n\nNguồn: {where(path, ranges)}.")
    return s


# ==============================================================================
# 1. Slide ngăn phần
# ==============================================================================
ITEMS = ["Sơ đồ luồng dữ liệu", "Vòng lặp mỗi khung hình · main.py", "Đọc camera · cameras.py", "Hệ tọa độ từ tờ A4 · vision.py",
         "Nhận diện vật · vision.py", "Điều kiện hoàn thành · success.py", "Màn hình · screen.py", "Thử nghiệm, kết quả, hạn chế"]


def slide_divider(prs):
    s = new_slide(prs, bg=STATEMENT)
    label(s, M, 1.3, 6.0, "Phần 02", TEAL)
    text(s, M, 1.62, 3.4, 1.7, "02", 110, TEAL, True)
    text(s, M, 3.45, 6.6, 1.6, ["Computer vision &", "Hỗ trợ gắp"], 44, INK, True, spacing=1.0)
    text(s, M, 5.13, 6.6, 0.45, f"{name('cv')}  –  {name('succ')}", 22, TEXT2)
    box(s, 7.75, 1.3, W - M - 7.75, 4.55, fill=CARD)
    label(s, 8.05, 1.55, 4.3, "Phần này gồm", TEXT2, 10.5)
    step = 3.7 / len(ITEMS)
    for i, item in enumerate(ITEMS):
        y = 2.0 + i * step
        rule(s, 8.05, y, W - M - 8.35)
        text(s, 8.05, y + (step - 0.3) / 2, 0.5, 0.3, f"{i + 1:02d}", 13, TEAL, True)
        text(s, 8.6, y + (step - 0.3) / 2, W - M - 8.9, 0.3, item, 14, INK)
    rule(s, 8.05, 2.0 + len(ITEMS) * step, W - M - 8.35)
    x = M
    for i, t in enumerate(["01  Linh kiện", "02  Computer vision & Hỗ trợ gắp", "03  Code điều khiển"]):
        w = chip_w(t, 10.5) + 0.2
        chip(s, x, 6.25, t, B.WHITE if i == 1 else TEXT2, TEAL if i == 1 else BG2, size=10.5, w=w)
        x += w + 0.12
    notes(s, """
Phần hai do {cv} và {succ} trình bày. {cv} trình bày computer vision: sơ đồ luồng dữ liệu của cả chương trình, vòng lặp mỗi khung hình, cách đọc camera, hệ tọa độ từ tờ A4 và nhận diện vật. {succ} trình bày hỗ trợ gắp: điều kiện hoàn thành, màn hình, rồi thử nghiệm, cách kiểm tra bằng mắt, kết quả và hạn chế.

Mỗi slide code lấy nguyên văn từ mã nguồn trên GitHub, có ghi tên tệp và số dòng ở góc trên khung code.

Nguồn: main.py, cameras.py, vision.py, success.py, screen.py (nhánh main).
""")


# ==============================================================================
# 2. Sơ đồ luồng dữ liệu
# ==============================================================================
def slide_dataflow(prs):
    s = new_slide(prs)
    header(s, EYEBROW, "Sơ đồ luồng dữ liệu", "cv")
    bx, bw, bh, pitch, y0 = M + 0.45, 3.55, 0.62, 1.03, 1.95
    blocks = [("CAMERA · cameras.py", "Camera.get_raw_frame()", name("cv").split()[-1], True),
              ("VISION · vision.py", "Vision.process_frame(ảnh)", name("cv").split()[-1], True),
              ("ĐIỀU KHIỂN · control.py", "Control.update(objects)", "phần 3", False),
              ("SUCCESS · success.py", "Success.update(plan)", name("succ").split()[-1], True),
              ("MÀN HÌNH · screen.py", "build_screen(..., plan, result)", name("succ").split()[-1], True)]
    tops = [y0 + i * pitch for i in range(len(blocks))]
    for (title, call, owner, ours), y in zip(blocks, tops):
        box(s, bx, y, bw, bh, fill=CARD if ours else BG2, edge=TEAL if ours else LINE, edge_w=1.75 if ours else 0.75)
        text(s, bx + 0.15, y + 0.07, bw - 1.0, 0.27, title, 12.5, INK, True)
        text(s, bx + 0.15, y + 0.34, bw - 0.3, 0.25, call, 10.5, TEAL if ours else TEXT2, font=MONO)
        text(s, bx + bw - 0.95, y + 0.07, 0.8, 0.25, owner, 10, MUTED, align=RIGHT)
    data = [("ảnh (BGR)", "ảnh", "mảng numpy cao × rộng × 3 (BGR), mỗi camera một ảnh; cam TRÊN để tìm vật, cam NGANG để người nhìn"),
            ("vision.objects", "vision.objects", 'danh sách vật [{"name", "x_cm", "y_cm", "px"}]: tọa độ trên tờ A4 (cm), đã bù thị sai'),
            ("plan", "Plan", "now: 4 góc servo hiện tại · goal: 3 góc cần tới · moves: phím, số lần, hướng, độ · found, reachable"),
            ("result", "Result", "state, done, joints_ok, next_move, remaining (số lần bấm còn lại), count")]
    cx, card_x = bx + bw / 2, 6.85
    for i, (arrow_label, card_title, card_body) in enumerate(data):
        y1, y2 = tops[i] + bh, tops[i + 1]
        mid = (y1 + y2) / 2
        line(s, cx, y1 + 0.02, cx, y2 - 0.02, TEAL, 2.0, head=True)
        text(s, cx + 0.14, mid - 0.14, 1.75, 0.28, arrow_label, 10.5, TEAL, True, font=MONO)
        line(s, bx + bw + 0.05, mid, card_x - 0.08, mid, LINE, 1.0, dash=True)
        box(s, card_x, mid - 0.4, W - M - card_x, 0.8, fill=CARD, edge=LINE)
        text(s, card_x + 0.18, mid - 0.33, 2.5, 0.27, card_title, 12, TEAL, True, font=MONO)
        text(s, card_x + 0.18, mid - 0.06, W - M - card_x - 0.35, 0.44, card_body, 11, TEXT2, spacing=1.02)
    # Arduino bên phải khối điều khiển: phím đi xuống, góc servo (JSON) đi lên
    nx, mid = bx + bw + 0.3, tops[2] + bh / 2
    box(s, nx, tops[2], 1.7, bh, fill=ORANGE_SOFT)
    text(s, nx + 0.1, tops[2] + 0.07, 1.55, 0.25, "Arduino · USB 9600", 10.5, INK, True)
    text(s, nx + 0.1, tops[2] + 0.34, 1.55, 0.25, "phím ↓  ·  JSON góc ↑", 9.5, TEXT2)
    line(s, bx + bw + 0.02, mid - 0.09, nx - 0.02, mid - 0.09, ORANGE, 1.5, head=True)
    line(s, nx - 0.02, mid + 0.09, bx + bw + 0.02, mid + 0.09, ORANGE, 1.5, head=True)
    # Vòng lặp: từ khối màn hình quay về khối camera
    lx, first_mid, last_mid = M + 0.1, tops[0] + bh / 2, tops[-1] + bh / 2
    line(s, bx - 0.02, last_mid, lx, last_mid, MUTED, 1.5)
    line(s, lx, last_mid, lx, first_mid, MUTED, 1.5)
    line(s, lx, first_mid, bx - 0.02, first_mid, MUTED, 1.5, head=True)
    text(s, card_x, tops[-1] + 0.32, W - M - card_x, 0.45,
         [[("Lặp lại mỗi khung hình: ", {"color": TEXT2}), ("main.py · App.render()", {"color": INK, "bold": True, "font": MONO})]], 12)
    notes(s, """
Đây là sơ đồ luồng dữ liệu của chương trình trên laptop. Mỗi khung hình, dữ liệu đi một chiều qua năm khối, đọc từ trên xuống; mũi tên ghi tên biến thật trong mã.

Hai camera cho ảnh. vision.py dò bốn mã ArUco để có lưới tọa độ, rồi tìm vật có màu trên ảnh cam TRÊN; kết quả là vision.objects, danh sách vật với tọa độ X, Y theo xăng-ti-mét trên tờ A4. control.py, phần ba, tính góc servo cần tới và phím cần bấm, đóng gói thành một đối tượng Plan; góc cần tới chỉ có sau khi người điều khiển bấm R để chụp vị trí vật. success.py chỉ đọc Plan và trả về Result: đã tới chưa, còn bao nhiêu lần bấm, đã thành công mấy lần. screen.py vẽ hai camera và hai ô chữ từ Plan và Result.

Bên phải: người dùng bấm phím, phím được gửi xuống Arduino qua USB 9600 baud; Arduino gửi lại góc servo dạng JSON năm lần mỗi giây, khối điều khiển dùng góc này làm góc hiện tại. Khi điều khiển từ xa, máy Dell xem đúng màn hình này qua Wi-Fi (share.py) và gửi phím thẳng tới Arduino qua Bluetooth HC-05; phím R vẫn bấm trên Mac.

Nếu được hỏi: vì sao chia thành các khối như vậy? Mỗi khối chỉ nhận một loại dữ liệu và trả một loại dữ liệu, nên làm và sửa riêng được từng khối; ví dụ success.py chỉ cần một Plan, không cần camera hay Arduino. Dữ liệu có được lưu lại không? Không; mỗi khung hình tính lại từ đầu, chỉ có vị trí mã ArUco, đích đã chụp bằng phím R và số lần thành công được nhớ.

Nguồn: main.py:{render}; success.py:{result}; robot_arm_4dof.ino (gói JSON mỗi 200 ms).
""".replace("{render}", "{}-{}".format(*span("main.py", "    def render")))
       .replace("{result}", "{}-{}".format(*span("success.py", "class Result"))))


# ==============================================================================
# 3-8. Slide code
# ==============================================================================
def slide_main(prs):
    ranges = [span("main.py", "    def _frame"), span("main.py", "    def render")]
    code_slide(prs, "cv", "Vòng lặp mỗi khung hình · main.py", "main.py", ranges,
               [(1, "Đọc khung camera"), (2, "vision"), (3, "control → Plan"), (4, "success → Result"), (5, "Vẽ màn hình")],
               [("raw = cam.get_raw_frame()", 1), ("self.vision.process_frame", 2), ("plan = self.control.update", 3),
                ("result = self.success.update", 4), ("screen = build_screen", 5)],
               """
Đây là phần chạy ở mỗi khung hình trong main.py, nối các khối của sơ đồ trước.

Hàm _frame lấy ảnh của một camera. Số 1: đọc khung mới nhất của camera; nếu chưa có hình hoặc mất tín hiệu thì hiện ô "Dang cho tin hieu" và xóa danh sách vật cũ, để không gợi ý theo dữ liệu đã cũ. Số 2: ảnh được đưa vào vision.process_frame để dò mã ArUco và tìm vật.

Hàm render: số 3, khối điều khiển nhận vision.objects và trả về plan; số 4, khối success nhận plan và trả về result; số 5, build_screen vẽ màn hình từ hai ảnh camera, plan và result.

Nếu được hỏi: một giây chạy bao nhiêu khung? Tùy camera và máy: mỗi vòng đọc một khung của mỗi camera rồi xử lý ngay. Mất tín hiệu thì sao? Ô camera hiện "Dang cho tin hieu"; cắm lại cáp rồi chạy lại chương trình.""")


def slide_cameras(prs):
    ranges = [span("cameras.py", "    def __init__"), span("cameras.py", "    def get_raw_frame")]
    code_slide(prs, "cv", "Đọc camera · cameras.py", "cameras.py", ranges,
               [(1, "Ảnh tĩnh để chạy thử"), (2, "Mở camera theo chỉ số"), (3, "Đọc khung mới nhất")],
               [("if source.lower().endswith", 1), ("elif source.isdigit()", 2), ("ok, frame = self.cap.read()", 3)],
               """
Phần này trả lời: hai camera được đọc thế nào.

Số 1: nguồn có thể là một ảnh .png hoặc .jpg; lần đọc nào cũng trả lại đúng ảnh đó, để chạy thử không cần camera. Số 2: camera mở theo chỉ số OpenCV: số ghi ở --top là cam TRÊN, số ghi ở --side là cam NGANG; trên Windows mở qua DirectShow. Bộ đệm chỉ giữ một khung để hình không bị trễ. Số 3: mỗi vòng lặp, get_raw_frame đọc khung mới nhất; không có hình thì trả về None và main.py hiện ô "Dang cho tin hieu".

Nếu được hỏi: camera nào là cam TRÊN? Chọn bằng chỉ số khi chạy, ví dụ --top 0 --side 1; macOS có thể đổi thứ tự camera giữa các lần chạy, nên nhìn hai khung hình, thấy đảo thì chạy lại với hai số đổi chỗ. Rút cáp camera thì sao? Ô camera hiện "Dang cho tin hieu"; cắm lại rồi chạy lại chương trình, bản này không tự mở lại camera.""")


def slide_sheet(prs):
    ranges = [span("vision.py", "def marker_corners_cm"), span("vision.py", "class Sheet")]
    code_slide(prs, "cv", "Hệ tọa độ từ tờ A4 · vision.py", "vision.py", ranges,
               [(1, "Góc mã theo cm"), (2, "Dò mã ArUco"), (3, "Nhớ mã bị che"), (4, "Tính homography")],
               [("def marker_corners_cm", 1), ("DETECTOR.detectMarkers", 2), ("self.markers.update(seen)", 3),
                ("cv2.findHomography", 4)],
               """
Phần này dựng hệ tọa độ xăng-ti-mét trên tờ A4 cho cả hai camera.

Số 1: marker_corners_cm cho tọa độ thật bốn góc của mỗi mã ArUco trên tờ giấy: mã cạnh 2,8 cm, cách mép giấy 0,25 cm, gốc tọa độ ở góc ngoài mã số 0. Số 2: mỗi khung hình, OpenCV dò các mã ArUco và trả về bốn góc pixel của từng mã. Số 3: vị trí mã được nhớ trong self.markers; khi cánh tay che mất một vài mã, chương trình dùng vị trí đã nhớ. Số 4: có từ hai mã trở lên, tức tám cặp điểm pixel và xăng-ti-mét, findHomography tính ma trận đổi pixel sang xăng-ti-mét; ma trận nghịch đảo đổi ngược lại để vẽ lưới.

Nếu được hỏi: vì sao hai mã là đủ? Homography cần ít nhất bốn cặp điểm; mỗi mã cho bốn góc, hai mã cho tám. Dời camera thì sao? Bấm phím U để quên vị trí mã đã nhớ và dò lại.""")


def slide_objects_overview(prs):
    """Slide hình 'Nhận diện vật' của bộ slide chính (3 bước tách màu, ảnh cam TRÊN, chọn mục tiêu), đặt trước slide code."""
    B.slide_objects(prs, "")
    tf = prs.slides[-1].notes_slide.notes_text_frame
    tf.text = tf.text.replace(f"Tiếp theo, {name('succ')} trình bày nửa sau của phần này: hỗ trợ gắp.",
                              "Slide sau là đoạn code thật của ba bước này trong vision.py.")


def slide_objects(prs):
    ranges = [span("vision.py", "def find_objects")]
    code_slide(prs, "cv", "Nhận diện vật · vision.py", "vision.py", ranges,
               [(1, "Ảnh phẳng tờ A4"), (2, "Tách vùng có màu"), (3, "Lọc vật"), (4, "Bù thị sai")],
               [("flat = cv2.warpPerspective", 1), ("colored = cv2.inRange", 2), ("if not 1.5 <=", 3), ("# Bù thị sai", 4)],
               """
Sau khi có homography, find_objects tìm vật trên ảnh cam TRÊN.

Số 1: warpPerspective dựng ảnh phẳng của tờ A4, mỗi xăng-ti-mét là 8 pixel, nên mọi phép đo sau đó tính thẳng bằng xăng-ti-mét. Số 2: chuyển sang không gian màu HSV và giữ các điểm có độ bão hòa từ 90 trở lên; giấy trắng, bóng xám và thân robot đen bị bỏ. Phép mở ảnh bỏ nhiễu và dây điện mảnh.

Số 3: lọc từng khối màu. Nhỏ hơn 1,5 cm² là nhiễu; lớn hơn 50 cm² là bàn tay, không lọt miệng kẹp; cách mép giấy dưới 1 cm là vật thò từ ngoài vào.

Số 4: bù thị sai. Cam TRÊN treo cao 46 cm, nắp cốc cao 5 cm nên bị lệch ra xa tâm ảnh. Vị trí thật bằng điểm nhìn thẳng xuống cộng khoảng cách đo được nhân với (46 − 5) / 46. Ở một vị trí đã đo, sai lệch giữa hai camera giảm từ 1,2 cm xuống 0,2 cm.

Nếu được hỏi: vật màu trắng hoặc xám thì sao? Chưa nhận được, đây là một hạn chế. Vì sao không dùng YOLO? Bản trước có YOLO nhưng hay nhận nhầm bộ phận robot, nên nhóm bỏ để mã đơn giản.""")


def slide_success(prs):
    ranges = [(find("success.py", "TOLERANCE_STEPS ="), find("success.py", "HOLD_S =")), span("success.py", "def check"),
              span("success.py", "    def update")]
    code_slide(prs, "succ", "Điều kiện hoàn thành · success.py", "success.py", ranges,
               [(1, "Lệch ≤ 2°, giữ 1 giây"), (2, "Servo nào đã tới"), (3, "Trạng thái"), (4, "Đếm lần thành công")],
               [("TOLERANCE_STEPS =", 1), ("joints = [", 2), ("if not plan.found", 3), ("if result.done", 4)],
               """
Em là {succ}, trình bày phần hỗ trợ gắp, bắt đầu từ success.py.

Số 1: hai hằng số. Một servo được coi là đã tới nếu lệch không quá một bước bấm, tức 2 độ; cả ba servo phải giữ đúng liên tục 1 giây mới tính một lần thành công. Số 2: hàm check đọc Plan của khối điều khiển, so từng servo đế, vai, khuỷu với góc gợi ý, và cộng số lần bấm còn lại. Số 3: xếp trạng thái theo ưu tiên: chưa có đích (chưa bấm R), vật ngoài tầm với, còn phải bấm, hoặc xong. Hàm check không nhớ gì giữa hai lần gọi.

Số 4: lớp Success gọi check mỗi khung hình và đếm số lần thành công: bắt đầu tính giờ khi vừa xong, đủ 1 giây thì cộng một, giữ thêm không cộng nữa, rời góc thì tính lại từ đầu.

Nếu được hỏi: vì sao không xét tay kẹp? Kẹp chưa giữ chắc vật thon, nên đề tài chỉ xét ba góc servo. XONG có nghĩa là đã gắp được không? Không; XONG nghĩa là ba góc đã ra lệnh tới góc gợi ý, vì MG996R không báo vị trí thật.""")


def slide_screen(prs):
    ranges = [span("screen.py", "def build_screen")]
    first, last = ranges[0]
    ranges = [(first, find("screen.py", "# Chân trang", first) - 2)]
    code_slide(prs, "succ", "Màn hình · screen.py", "screen.py", ranges,
               [(1, "Hai camera"), (2, "Ô 1: lệnh bấm phím"), (3, "Ba dòng servo"), (4, "Ô 2: XONG / CHUA XONG")],
               [("img[:CAM_H] = np.hstack", 1), ("# Ô 1: ĐIỀU KHIỂN", 2), ("for i, (m, ok)", 3), ("# Ô 2: SUCCESS", 4)],
               """
screen.py chỉ vẽ, không tính gì; mọi chữ trên màn hình lấy từ Plan và Result.

Số 1: ghép hai ảnh camera thành hàng trên, mỗi ô 640 × 360. Số 2: ô một, điều khiển: nếu còn phải bấm thì hiện lệnh lớn, ví dụ "BAM S x15: HA XUONG 30 do"; các trạng thái khác hiện một câu nhắc. Số 3: ba dòng servo đế, vai, khuỷu với góc hiện tại, góc đích, và phím cần bấm; dòng đã tới ghi DA DUNG màu xanh. Số 4: ô hai, success: XONG màu xanh khi cả ba servo đã tới, không thì CHUA XONG kèm số lần bấm còn lại, và số lần thành công.

Nếu được hỏi: vì sao chữ không dấu? Phông chữ của OpenCV không vẽ được dấu tiếng Việt. Trái, phải theo hướng nào? Theo cam NGANG đặt trước robot: phím A sang phải, D sang trái.""")


def build(out, makers, title):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
    prs._element.sldSz.attrib.pop("type", None)
    for make in makers:
        make(prs)
    B.add_notes_master_id(prs)
    prs.core_properties.title = title
    prs.save(out)
    B.repack_like_powerpoint(out)
    print(f"Đã lưu {out} ({len(prs.slides)} slide)")


def export_previews(out, preview_dir):
    """PDF bằng LibreOffice hoặc PowerPoint (như export_pdf.py), rồi ảnh PNG từng slide."""
    import export_pdf as E

    E.PPTX, E.PDF = out, out[:-5] + ".pdf"
    soffice = E.find_soffice()
    if soffice:
        E.export_libreoffice(soffice)
    elif sys.platform == "win32":
        E.export_powerpoint()
    else:
        print("Không có LibreOffice / PowerPoint: bỏ qua PDF và ảnh xem trước")
        return
    import fitz

    os.makedirs(preview_dir, exist_ok=True)
    for i, page in enumerate(fitz.open(E.PDF), 1):
        page.get_pixmap(dpi=150).save(os.path.join(preview_dir, f"slide_{i:02d}.png"))
    print(f"Đã xuất {E.PDF} và ảnh trong {preview_dir}")


if __name__ == "__main__":
    build(OUT, (slide_divider, slide_dataflow, slide_main, slide_cameras, slide_sheet, slide_objects_overview, slide_objects, slide_success,
                slide_screen), "Phần 2: Computer vision & Hỗ trợ gắp (sơ đồ luồng dữ liệu, code)")
    export_previews(OUT, PREVIEW_DIR)
    build(CONCLUSION_OUT, (lambda prs: B.slide_conclusion(prs, ""), lambda prs: B.slide_summary(prs, "")), "Kết luận")  # Hai slide cuối của bộ slide chính
    export_previews(CONCLUSION_OUT, CONCLUSION_PREVIEW_DIR)
