#!/usr/bin/env python3
"""
Dựng bộ slide 15 trang (tiếng Việt, 16:9, nền tối giống màn hình app) cho mã HAI NHÓM hiện tại:
camera -> vision.py -> control.py (NHÓM 1: bấm phím gì) -> success.py (NHÓM 2: đã tới chưa) -> screen.py.

    python3 slides/build_slides.py        ->  slides/Project_IoT_ThuyetTrinh.pptx
    python3 slides/export_pdf.py          ->  slides/Project_IoT_ThuyetTrinh.pdf   (LibreOffice, hoặc PowerPoint trên Windows)
    python3 slides/render_previews.py     ->  slides/preview/slide_XX.png
    python3 slides/verify_slides.py       ->  kiểm số trang, ghi chú, chân trang, chú thích "mô phỏng", tính năng đã bỏ

Mọi con số lấy từ slides/05_SO_LIEU_VA_NGUON.md (kiểm lại bằng slides/tools/check_facts.py sau mỗi lần sửa mã).
Ảnh thật nằm trong slides/assets/real/ (không đưa lên repo công khai); thiếu ảnh nào thì slide hiện khung "[Ảnh: ...]" thay vào.
Cần: python-pptx, Pillow. Phông Arial / Courier New có sẵn trên macOS lẫn Windows, đủ dấu tiếng Việt.
"""

import os
import re
import sys
from datetime import datetime

from lxml import etree
from PIL import Image, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

if sys.platform == "win32":  # Terminal Windows (cp1252) không in được tiếng Việt
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

SLIDES_DIR = os.path.dirname(os.path.abspath(__file__))
REAL_DIR = os.path.join(SLIDES_DIR, "assets", "real")
OUT_PPTX = os.path.join(SLIDES_DIR, "Project_IoT_ThuyetTrinh.pptx")
TOTAL = 15
FOOTER_TITLE = "Hệ thống hỗ trợ gắp vật · cánh tay robot 4 bậc tự do"

# ==============================================================================
# Màu: lấy đúng bảng màu của screen.py (BGR đổi sang RGB) để slide trông như màn hình app
# ==============================================================================
BG = RGBColor(0x19, 0x1B, 0x1E)        # nền
BG2 = RGBColor(0x20, 0x22, 0x26)       # dải nền phụ
CARD = RGBColor(0x27, 0x2A, 0x2E)      # thẻ
EDGE = RGBColor(0x46, 0x4C, 0x52)      # viền
WHITE = RGBColor(0xF5, 0xF5, 0xF5)
MUTED = RGBColor(0x9B, 0xA0, 0xA5)
AMBER = RGBColor(0xFF, 0xB9, 0x28)     # phím, lệnh, điểm nhấn
AMBER_DK = RGBColor(0x62, 0x3E, 0x1C)
GREEN = RGBColor(0x5A, 0xD7, 0x6E)     # đã có / XONG
GREEN_DK = RGBColor(0x2A, 0x58, 0x32)
RED = RGBColor(0xF5, 0x55, 0x55)       # chưa / giới hạn
RED_DK = RGBColor(0x6E, 0x28, 0x28)
DARK = RGBColor(0x19, 0x1B, 0x1E)      # chữ tối trên nền hổ phách / xanh

FONT = "Arial"
MONO = "Courier New"
LEFT, CENTER, RIGHT = PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.RIGHT
TOP, MIDDLE, BOTTOM = MSO_ANCHOR.TOP, MSO_ANCHOR.MIDDLE, MSO_ANCHOR.BOTTOM


# ==============================================================================
# Đo chữ: dùng đúng tệp phông Arial để biết một dòng rộng bao nhiêu, ngắt thành mấy dòng
# ==============================================================================
FONT_FILES = {
    False: ("/System/Library/Fonts/Supplemental/Arial.ttf", "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf"),
    True: ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "C:/Windows/Fonts/arialbd.ttf",
           "/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf"),
}
_pil_fonts = {}
# Không ngắt dòng giữa số và đơn vị ("8,5 mm"), quanh dấu nhân ("S × 15") và trong "109 / 109"
NO_BREAK = [(re.compile(r"(\d)\s+(mm|cm|ms|Hz|V|giây|°)(?!\w)"), "\\1\u00a0\\2"),
            (re.compile(r"\s+×\s+"), "\u00a0×\u00a0"),
            (re.compile(r"\s*≈\s+"), "\u00a0≈\u00a0"),
            (re.compile(r"(\d)\s+/\s+(\d)"), "\\1\u00a0/\u00a0\\2")]


def text_w(s, size, bold=False):
    """Bề rộng (inch) của một dòng chữ Arial cỡ `size` pt (không có tệp phông thì ước lượng)."""
    if bold not in _pil_fonts:
        path = next((f for f in FONT_FILES[bold] if os.path.exists(f)), None)
        _pil_fonts[bold] = ImageFont.truetype(path, 100) if path else None
    font = _pil_fonts[bold]
    return (font.getlength(s) if font else len(s) * (60 if bold else 54)) / 100 * size / 72


def n_lines(s, size, width, bold=False):
    """Số dòng khi ngắt chữ theo từ trong hộp rộng `width` inch."""
    lines, cur = 0, ""
    for para in s.split("\n"):
        cur = ""
        for word in para.split():
            cand = f"{cur} {word}".strip()
            if cur and text_w(cand, size, bold) > width:
                lines, cur = lines + 1, word
            else:
                cur = cand
        lines += 1
    return lines


def plain(item):
    """Chữ thuần của một đoạn (chuỗi hoặc danh sách run)."""
    return item if isinstance(item, str) else "".join(r if isinstance(r, str) else r[0] for r in item)


# ==============================================================================
# Hàm vẽ nhỏ (đơn vị: inch, cỡ chữ: point)
# ==============================================================================
def new_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Bố cục trống
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = BG
    return slide


def text(slide, x, y, w, h, paras, size=18, color=WHITE, bold=False, font=FONT, align=LEFT, anchor=TOP,
         spacing=1.1, after=0, spc=None):
    """
    Hộp chữ không tự co. paras: chuỗi, hoặc danh sách đoạn; mỗi đoạn là chuỗi hoặc danh sách run,
    mỗi run là chuỗi hoặc (chuỗi, {"color", "bold", "size", "font"}).
    """
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    fill_paragraphs(tf, paras, size, color, bold, font, align, spacing, after, spc)
    return box


def fill_paragraphs(tf, paras, size, color, bold, font, align, spacing=1.1, after=0, spc=None):
    if isinstance(paras, (str, tuple)):
        paras = [paras]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = spacing
        if after:
            p.space_after = Pt(after)
        for run_spec in ([para] if isinstance(para, (str, tuple)) else para):
            add_run(p, run_spec, size, color, bold, font, spc)
    return tf


def add_run(p, run_spec, size, color, bold, font, spc=None):
    s, style = (run_spec, {}) if isinstance(run_spec, str) else run_spec
    for pat, rep in NO_BREAK:
        s = pat.sub(rep, s)
    run = p.add_run()
    run.text = s
    f = run.font
    f.name = style.get("font", font)
    f.size = Pt(style.get("size", size))
    f.bold = style.get("bold", bold)
    f.color.rgb = style.get("color", color)
    if spc or style.get("spc"):
        run._r.get_or_add_rPr().set("spc", str(style.get("spc", spc)))  # Giãn chữ (1/100 pt)
    return run


def bullets(slide, x, y, w, h, items, size=16, color=WHITE, mark="•", mark_color=AMBER, after=8, indent=0.26, spacing=1.08):
    """Danh sách gạch đầu dòng thụt treo (dòng thứ hai thẳng hàng với chữ, không thẳng hàng với dấu)."""
    box = text(slide, x, y, w, h, items, size, color, spacing=spacing, after=after)
    for p in box.text_frame.paragraphs:
        pPr = p._p.get_or_add_pPr()
        pPr.set("marL", str(int(Inches(indent))))
        pPr.set("indent", str(-int(Inches(indent))))
        clr = etree.SubElement(pPr, qn("a:buClr"))
        etree.SubElement(clr, qn("a:srgbClr")).set("val", str(mark_color))
        etree.SubElement(pPr, qn("a:buFont")).set("typeface", FONT)
        etree.SubElement(pPr, qn("a:buChar")).set("char", mark)
    return box


def steps(slide, x, y, w, items, size=15, color=WHITE, dot_color=AMBER, d=0.36, gap=0.14, fg=DARK, spacing=1.05):
    """Danh sách đánh số; mỗi mục cao đúng theo số dòng đo bằng phông Arial. Trả về y ngay dưới mục cuối."""
    tx, tw = x + d + 0.14, w - d - 0.14
    line_h = size * 1.2 * spacing / 72
    for i, it in enumerate(items):
        h = n_lines(plain(it), size, tw - 0.05) * line_h
        dot(slide, x, y + (line_h - d) / 2, i + 1, dot_color, d=d, size=max(11, size - 3), fg=fg)
        text(slide, tx, y, tw, h + 0.04, [it] if isinstance(it, list) else it, size, color, spacing=spacing)
        y += max(h, d) + gap
    return y


def box(slide, x, y, w, h, fill=CARD, edge=EDGE, edge_w=1.0, radius=0.08, shape=MSO_SHAPE.ROUNDED_RECTANGLE, dash=False):
    shp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        shp.adjustments[0] = min(0.5, radius / max(0.01, min(w, h)))
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid()
        shp.fill.fore_color.rgb = fill
    if edge is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = edge
        shp.line.width = Pt(edge_w)
        if dash:
            etree.SubElement(shp.line._get_or_add_ln(), qn("a:prstDash")).set("val", "dash")
    shp.shadow.inherit = False  # Bỏ bóng đổ mặc định của theme
    return shp


def label_in(shp, paras, size=14, color=WHITE, bold=False, align=CENTER, anchor=MIDDLE, font=FONT, margin=0.04):
    """Chữ nằm trong một hình (phím, chip, nút)."""
    tf = shp.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left = tf.margin_right = Inches(margin)
    tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    fill_paragraphs(tf, paras, size, color, bold, font, align, spacing=1.0)
    return shp


def chip(slide, x, y, w, h, s, fill=None, color=AMBER, edge=None, size=11, bold=True):
    """Nhãn bo tròn: nền đặc (fill) hoặc chỉ viền (edge). w=None: rộng vừa chữ."""
    if w is None:
        w = chip_w(s, size, bold)
    shp = box(slide, x, y, w, h, fill=fill, edge=edge, edge_w=1.25, radius=h / 2)
    return label_in(shp, s, size, color, bold, margin=0.08)


def chip_w(s, size=11, bold=True):
    return text_w(s, size, bold) + 0.4


def keycap(slide, x, y, letter, w=0.46, h=0.42, size=17):
    """Phím màu hổ phách chữ tối, giống phím vẽ trên màn hình app."""
    shp = box(slide, x, y, w, h, fill=AMBER, edge=None, radius=0.07)
    return label_in(shp, letter, size, DARK, True, margin=0.0)


def dot(slide, x, y, n, color=AMBER, d=0.42, size=15, fg=DARK):
    """Vòng tròn đánh số."""
    shp = box(slide, x, y, d, d, fill=color, edge=None, shape=MSO_SHAPE.OVAL)
    return label_in(shp, str(n), size, fg, True, margin=0.0)


def line(slide, x1, y1, x2, y2, color=AMBER, width=2.0, head=False, dash=False):
    """Đoạn thẳng (head=True: có mũi tên ở cuối)."""
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = color
    c.line.width = Pt(width)
    ln = c.line._get_or_add_ln()
    if dash:
        etree.SubElement(ln, qn("a:prstDash")).set("val", "dash")
    if head:
        tail = etree.SubElement(ln, qn("a:tailEnd"))
        tail.set("type", "triangle")
        tail.set("w", "med")
        tail.set("len", "med")
    return c


def image(slide, name, x, y, w, h=None, mode="cover", focus=(0.5, 0.5), edge=EDGE):
    """
    Ảnh trong khung w x h. mode="cover": cắt bớt cho đầy khung, giữ tỉ lệ (focus = điểm giữ lại, 0..1);
    h=None: giữ nguyên tỉ lệ ảnh. Thiếu tệp thì vẽ khung "[Ảnh: tên tệp]" để vẫn dựng được slide.
    """
    path = name if os.path.isabs(name) else os.path.join(REAL_DIR, name)
    if not os.path.exists(path):
        hh = h if h is not None else w * 9 / 16
        ph = box(slide, x, y, w, hh, fill=BG2, edge=MUTED, dash=True, radius=0.05)
        label_in(ph, f"[Ảnh: {os.path.basename(name)}]", 13, MUTED)
        return ph
    iw, ih = Image.open(path).size
    if h is None:
        h = w * ih / iw
    pic = slide.shapes.add_picture(path, Inches(x), Inches(y), Inches(w), Inches(h))
    if mode == "cover":
        box_ratio, img_ratio = w / h, iw / ih
        if img_ratio > box_ratio:  # Ảnh rộng hơn khung: cắt hai bên
            keep = box_ratio / img_ratio
            left = min(max(focus[0] - keep / 2, 0.0), 1.0 - keep)
            pic.crop_left, pic.crop_right = left, 1.0 - keep - left
        elif img_ratio < box_ratio:  # Ảnh cao hơn khung: cắt trên dưới
            keep = img_ratio / box_ratio
            top = min(max(focus[1] - keep / 2, 0.0), 1.0 - keep)
            pic.crop_top, pic.crop_bottom = top, 1.0 - keep - top
    if edge is not None:
        pic.line.color.rgb = edge
        pic.line.width = Pt(0.75)
    return pic


def header(slide, tag, title, size=28):
    text(slide, 0.6, 0.38, 12.1, 0.3, tag.upper(), 13, AMBER, True, spc=120)
    text(slide, 0.6, 0.66, 12.1, 0.62, title, size, WHITE, True, anchor=TOP)
    box(slide, 0.6, 1.36, 0.8, 0.05, fill=AMBER, edge=None, shape=MSO_SHAPE.RECTANGLE)


def footer(slide, n):
    text(slide, 0.6, 7.04, 8.0, 0.25, FOOTER_TITLE, 11, MUTED)
    text(slide, 10.73, 7.04, 2.0, 0.25, f"Trang {n} / {TOTAL}", 11, MUTED, align=RIGHT)


def notes(slide, s):
    slide.notes_slide.notes_text_frame.text = s.strip()


def caption(slide, x, y, w, s, size=11.5, h=0.45, color=MUTED, align=LEFT):
    return text(slide, x, y, w, h, s, size, color, align=align, spacing=1.05)


def card_title(slide, x, y, w, s, color=AMBER, size=13):
    return text(slide, x, y, w, 0.3, s.upper(), size, color, True, spc=60)


# ==============================================================================
# Slide 1: Bìa
# ==============================================================================
def slide_01(prs):
    s = new_slide(prs)
    text(s, 0.6, 0.95, 6.9, 0.3, "ĐỒ ÁN IoT · [MÔN HỌC] · [NGÀY BÁO CÁO]", 13, AMBER, True, spc=120)
    text(s, 0.6, 1.4, 6.85, 2.3, "Hệ thống hỗ trợ gắp vật cho cánh tay robot 4 bậc tự do bằng thị giác máy tính",
         34, WHITE, True, spacing=1.02)
    text(s, 0.6, 3.72, 6.7, 0.95,
         "Hai camera chỉ cho người điều khiển bấm phím nào, mấy lần; rồi kiểm tra ba servo đã tới góc gợi ý chưa.",
         18, MUTED, spacing=1.12)
    chips = [("2 CAMERA + ArUco", WHITE), ("NHÓM 1 · ĐIỀU KHIỂN", AMBER), ("NHÓM 2 · SUCCESS", GREEN)]
    x = 0.6
    for label, col in chips:
        w = chip_w(label, 11)
        chip(s, x, 4.86, w, 0.4, label, edge=col, color=col, size=11)
        x += w + 0.14
    team = box(s, 0.6, 5.55, 6.75, 1.2, fill=CARD)
    text(s, 0.85, 5.7, 3.3, 0.95, [
        [("Sinh viên thực hiện", {"color": MUTED, "size": 12})], "[...]",
        [("Lớp / Môn học", {"color": MUTED, "size": 12})], "[...]"], 15, WHITE, spacing=1.0)
    text(s, 4.2, 5.7, 3.0, 0.95, [
        [("Giảng viên hướng dẫn", {"color": MUTED, "size": 12})], "[...]",
        [("Ngày báo cáo", {"color": MUTED, "size": 12})], "[...]"], 15, WHITE, spacing=1.0)
    image(s, "demo_06_grip_side.jpg", 7.75, 0.95, 4.98, 2.8)
    image(s, "demo_06_grip_top.jpg", 7.75, 3.88, 4.98, 2.8)
    caption(s, 7.75, 6.74, 4.98, "Ảnh thật từ hai camera của hệ thống (ngang, trên) · 02/11/2026 20:32:52 · người bấm phím", 11, 0.3)
    notes(s, """
Em chào thầy cô và các bạn. Nhóm em xin trình bày đề tài: hệ thống hỗ trợ gắp vật cho cánh tay robot bốn bậc tự do bằng thị giác máy tính. Nói ngắn gọn: hai camera nhìn tờ giấy và vật, chương trình cho người điều khiển biết phải bấm phím nào, bấm mấy lần, rồi kiểm tra ba servo đã tới góc gợi ý chưa.

Bài nói khoảng mười lăm phút: bài toán; hệ thống và phần cứng; cách hệ thống nhìn tờ giấy và tìm vật; nhóm một, phần điều khiển; nhóm hai, phần success; thử trên cánh tay thật; hai sự cố nhóm gặp; và cuối cùng là những gì nhóm đã và chưa kiểm chứng.

Hai ảnh bên phải là ảnh thật từ hai camera của hệ thống, lúc cánh tay đang kẹp cốc do người bấm phím, không phải ảnh dựng.

Nếu được hỏi: ai làm phần nào? [...điền phân công; nhóm một là điều khiển, nhóm hai là success].

Nguồn: ảnh demo_06_grip_side, demo_06_grip_top (khung cắt từ video buổi thử 02/11/2026, 20:32:52).
""")


# ==============================================================================
# Slide 2: Bài toán
# ==============================================================================
def slide_02(prs):
    s = new_slide(prs)
    header(s, "01 · Bài toán", "Ba câu hỏi trước mỗi lần gắp")
    card_title(s, 0.6, 1.72, 7.2, "Trước mỗi lần gắp, người điều khiển phải tự trả lời", MUTED, 12)
    rows = [
        ("Vật đang ở đâu trên bàn?", "PHẦN NHÌN · vision.py", WHITE),
        ("Ba servo ở góc nào? Bấm phím nào, mấy lần?", "NHÓM 1 · ĐIỀU KHIỂN · control.py", AMBER),
        ("Đã tới đúng góc chưa?", "NHÓM 2 · SUCCESS · success.py", GREEN),
    ]
    for i, (q, who, col) in enumerate(rows):
        y = 2.12 + i * 1.42
        box(s, 0.6, y, 7.3, 1.24, fill=CARD)
        dot(s, 0.85, y + 0.22, i + 1, d=0.5, size=18)
        text(s, 1.55, y + 0.17, 6.28, 0.45, q, 20, WHITE, True)
        text(s, 1.55, y + 0.7, 6.28, 0.35, [[("→  ", {"color": col}), (who, {"color": col, "bold": True})]], 14)
    box(s, 8.25, 2.12, 4.48, 4.08, fill=CARD)
    card_title(s, 8.55, 2.35, 4.0, "Vì sao khó", RED)
    bullets(s, 8.55, 2.8, 3.95, 2.3, [
        "Mỗi phím chỉ nhích 2°: tới được vật có khi phải bấm hơn 20 lần",
        "Mắt người khó ước lượng độ sâu qua một góc nhìn",
        "Gợi ý chỉ đúng khi mô hình hình học khớp cánh tay thật (slide 11)",
    ], 16, after=10, mark_color=RED)
    box(s, 8.5, 5.08, 3.98, 0.9, fill=BG2, edge=None, radius=0.06)
    text(s, 8.68, 5.15, 3.7, 0.25, "VÍ DỤ Ở SLIDE 7", 10.5, MUTED, True, spc=40)
    keycap(s, 8.68, 5.45, "D", 0.4, 0.38, 15)
    text(s, 9.13, 5.45, 0.5, 0.38, "× 8", 15, WHITE, True, anchor=MIDDLE)
    keycap(s, 9.72, 5.45, "S", 0.4, 0.38, 15)
    text(s, 10.17, 5.45, 0.65, 0.38, "× 16", 15, WHITE, True, anchor=MIDDLE)
    text(s, 10.85, 5.45, 1.6, 0.38, "= 24 lần bấm", 15, AMBER, True, anchor=MIDDLE)
    text(s, 0.6, 6.42, 12.1, 0.45, [[("Hệ thống trả lời ba câu này; ", {"color": WHITE}),
                                    ("người vẫn là người bấm phím.", {"color": AMBER, "bold": True})]], 19)
    footer(s, 2)
    notes(s, """
Bài toán rất cụ thể. Cánh tay của nhóm có bốn servo, điều khiển bằng bàn phím, mỗi lần bấm một phím thì một servo nhích hai độ. Trước mỗi lần gắp, người điều khiển phải tự trả lời ba câu hỏi: vật đang ở đâu trên bàn; ba servo phải ở góc nào, phải bấm phím nào, mấy lần; và đã tới đúng góc chưa.

Khó nhất là mắt người khó ước lượng độ sâu, mỗi phím lại chỉ nhích hai độ nên tới được vật có khi phải bấm hơn hai mươi lần, như ví dụ hai mươi bốn lần ở slide bảy. Và nếu mô hình hình học không khớp cánh tay thật thì gợi ý nào cũng lệch.

Hệ thống của nhóm trả lời đúng ba câu hỏi này, mỗi câu bằng một thành phần riêng: phần nhìn trả lời câu một, nhóm một trả lời câu hai, nhóm hai trả lời câu ba. Người vẫn là người bấm phím.

Nếu được hỏi: vì sao không để chương trình tự điều khiển luôn? Vì mô hình hình học chỉ khớp cánh tay thật cỡ một xăng-ti-mét (slide 11) và tay kẹp chưa giữ chắc cốc thon (slide 9), nên nhóm chọn hướng hỗ trợ người điều khiển. Bản trước có chế độ tự gửi phím, nhóm đã bỏ để mã giải thích được trong một phút.

Nguồn: README.md mục 3; control.py; success.py.
""")


# ==============================================================================
# Slide 3: Hệ thống (sơ đồ hai nhóm)
# ==============================================================================
def slide_03(prs):
    s = new_slide(prs)
    header(s, "02 · Hệ thống", "Hai camera nhìn, nhóm 1 tính, nhóm 2 kiểm")
    w, gap, y, h = 2.02, 0.5, 2.05, 1.62
    blocks = [
        ("CẢM BIẾN", "Hai camera", "OBSBOT nhìn xuống, MacBook nhìn ngang; tờ A4 có 4 mã ArUco", EDGE, MUTED),
        ("NHÌN · vision.py", "Tìm vật", "ArUco → homography; tách màu → (X, Y) cm", EDGE, MUTED),
        ("NHÓM 1 · control.py", "Điều khiển", "vị trí vật → góc 3 servo → phím cần bấm", AMBER, AMBER),
        ("NHÓM 2 · success.py", "Success", "3 servo đã tới góc chưa? đếm số lần", GREEN, GREEN),
        ("MÀN HÌNH · screen.py", "Lệnh + kết luận", "phím to, số lần; XONG hoặc CHƯA XONG", EDGE, MUTED),
    ]
    xs = [0.6 + i * (w + gap) for i in range(5)]
    for x, (tag, title, desc, edge, tagc) in zip(xs, blocks):
        thick = edge in (AMBER, GREEN)
        box(s, x, y, w, h, fill=CARD, edge=edge, edge_w=2.25 if thick else 1.0)
        text(s, x + 0.14, y + 0.13, w - 0.24, 0.25, tag, 10.5, tagc, True)
        text(s, x + 0.14, y + 0.42, w - 0.24, 0.35, title, 16, WHITE, True)
        text(s, x + 0.14, y + 0.82, w - 0.24, 0.75, desc, 12.5, MUTED, spacing=1.05)
    mid = y + h / 2
    for i, lab in enumerate(["ảnh", "(X, Y)", "Plan", "Result"]):
        x1, x2 = xs[i] + w + 0.05, xs[i + 1] - 0.05
        strong = lab == "Plan"
        line(s, x1, mid, x2, mid, AMBER if strong else MUTED, 3.5 if strong else 1.75, head=True)
        text(s, x1 - 0.25, mid - 0.4, x2 - x1 + 0.5, 0.3, lab, 13 if strong else 11, AMBER if strong else MUTED, strong, align=CENTER)
    # Vòng người: nhìn màn hình rồi bấm phím, phím đi qua nhóm 1 xuống Arduino
    lx, rx, top = xs[2] + w / 2, xs[4] + w / 2, 1.72
    line(s, rx, y, rx, top, MUTED, 1.5, dash=True)
    line(s, rx, top, lx, top, MUTED, 1.5, dash=True)
    line(s, lx, top, lx, y - 0.02, MUTED, 1.5, head=True, dash=True)
    text(s, lx + 0.3, top - 0.29, rx - lx - 0.6, 0.27, "người nhìn màn hình rồi bấm phím", 11.5, WHITE, align=CENTER)
    # Hàng phần cứng dưới nhóm 1, nhóm 2, màn hình
    hy, hh = 4.45, 1.05
    hw = [("Arduino Uno", "nhận phím, gửi JSON"), ("PCA9685", "I²C 0x40 · xung 50 Hz"), ("4 servo MG996R", "đế · vai · khuỷu · kẹp")]
    for i, (t1, t2) in enumerate(hw):
        x = xs[2 + i]
        box(s, x, hy, w, hh, fill=BG2, edge=EDGE)
        text(s, x + 0.14, hy + 0.15, w - 0.24, 0.32, t1, 15, WHITE, True)
        text(s, x + 0.14, hy + 0.55, w - 0.24, 0.4, t2, 12, MUTED)
        if i < 2:
            line(s, x + w + 0.05, hy + hh / 2, xs[3 + i] - 0.05, hy + hh / 2, MUTED, 1.75, head=True)
    cx = xs[2] + w / 2
    line(s, cx - 0.32, y + h + 0.04, cx - 0.32, hy - 0.04, AMBER, 2.0, head=True)
    line(s, cx + 0.32, hy - 0.04, cx + 0.32, y + h + 0.04, GREEN, 2.0, head=True)
    text(s, xs[1] + 0.3, y + h + 0.2, cx - 0.42 - xs[1] - 0.3, 0.5, ["phím · USB 9600 baud"], 11, AMBER, align=RIGHT)
    text(s, cx + 0.45, y + h + 0.2, 2.3, 0.5, ["JSON ~5 gói/giây", "(góc servo đã ra lệnh)"], 11, GREEN, spacing=1.0)
    box(s, 0.6, hy, 4.45, hh, fill=CARD, edge=AMBER, edge_w=1.0)
    text(s, 0.8, hy + 0.12, 4.1, 0.3, "CHỈ MỘT ĐỐI TƯỢNG NỐI HAI NHÓM", 11, AMBER, True, spc=40)
    text(s, 0.8, hy + 0.42, 4.1, 0.6, "Plan = góc hiện tại, góc cần tới, lệnh bấm cho từng servo. Nhóm 1 tạo ra, nhóm 2 chỉ đọc.", 13, WHITE, spacing=1.05)
    box(s, 0.6, 5.8, 12.13, 1.05, fill=BG2, edge=None, radius=0.06)
    code = [("plan   = self.control.update(self.tracker.objects)", "# NHÓM 1: vật ở đâu -> góc cần tới -> bấm phím gì"),
            ("result = self.success.update(plan)", "# NHÓM 2: đã tới chưa"),
            ("screen = build_screen(..., plan, result)", "# main.py:171-174, mỗi khung hình")]
    text(s, 0.85, 5.9, 11.7, 0.9, [[(c.ljust(53), {}), (k, {"color": MUTED})] for c, k in code], 13, WHITE, font=MONO, spacing=1.12)
    footer(s, 3)
    notes(s, """
Đây là toàn bộ hệ thống trên một trang, đọc từ trái sang phải.

Hai camera cùng quay tờ giấy A4: OBSBOT treo trên nhìn xuống để tính vị trí vật, camera MacBook đặt thấp phía trước để người điều khiển nhìn độ cao và độ sát của hai ngón kẹp. Phần nhìn dò bốn mã ArUco để đổi pixel sang xăng-ti-mét, rồi tách màu để ra vị trí X, Y của vật.

Hai ô ở giữa là điểm chính của thiết kế. Nhóm một lo điều khiển: biết vật ở đâu thì tính ba servo cần ở góc nào và lập danh sách phím cần bấm. Nhóm hai lo success: chỉ trả lời một câu, ba servo đã tới góc đó chưa. Hai nhóm chỉ nói chuyện qua một đối tượng tên là Plan, nên làm riêng và kiểm riêng được; ba dòng mã ở dưới là đúng những gì chương trình làm mỗi khung hình.

Người nhìn màn hình rồi bấm phím. Phím đi xuống Arduino qua cáp USB, chín nghìn sáu trăm baud; Arduino điều khiển bốn servo qua mạch PCA9685 và gửi ngược lên gói JSON chứa bốn góc servo, khoảng năm gói mỗi giây. Đó là phần IoT của hệ thống.

Nếu được hỏi: chương trình có tự gửi phím không? Không, chỉ gửi khi người bấm. Có Bluetooth không? Firmware có sẵn đường nhận phím từ module HC-05 ở chân D2, D3, nhưng chương trình trên laptop chỉ dùng cáp USB.

Nguồn: README.md (sơ đồ đầu trang, mục 1 và 3); main.py:171-174; robot_arm_4dof.ino:6,8,86,203-207; control.py (ArduinoSerialLink).
""")


# ==============================================================================
# Slide 4: Phần cứng
# ==============================================================================
def slide_04(prs):
    s = new_slide(prs)
    header(s, "02 · Phần cứng", "Arduino Uno, PCA9685 và bốn servo MG996R")
    pw, ph1, ph2 = 3.0, 1.69, 2.2
    photos = [
        ("hw_overview_top.jpg", 0.6, 1.7, ph1, "Cam TRÊN · OBSBOT Meet SE nhìn xuống"),
        ("hw_overview_side.jpg", 3.75, 1.7, ph1, "Cam NGANG · camera MacBook đặt thấp"),
        ("hw_electronics.jpg", 0.6, 3.93, ph2, "Arduino Uno + PCA9685 + nguồn tổ ong"),
        ("hw_arm_gripper.jpg", 3.75, 3.93, ph2, "Cánh tay 4 servo, tay kẹp hai ngón"),
    ]
    for name, x, y, h, cap in photos:
        image(s, name, x, y, pw, h)
        caption(s, x, y + h + 0.05, pw, cap, 11, 0.3)
    rx = 7.15
    card_title(s, rx, 1.72, 5.6, "4 servo · phím · giới hạn góc", MUTED, 12)
    rows = [("KÊNH 0", "Đế (xoay)", "A", "D", "0–180°"), ("KÊNH 1", "Vai", "W", "S", "25–155°"),
            ("KÊNH 2", "Khuỷu", "I", "K", "25–155°"), ("KÊNH 3", "Kẹp", "J", "L", "95–160°")]
    for i, (ch, name, k1, k2, lim) in enumerate(rows):
        y = 2.1 + i * 0.66
        box(s, rx, y, 5.58, 0.56, fill=CARD)
        text(s, rx + 0.18, y + 0.15, 0.9, 0.3, ch, 11, MUTED, True)
        text(s, rx + 1.05, y + 0.12, 1.8, 0.35, name, 16, WHITE, True)
        keycap(s, rx + 2.85, y + 0.07, k1, 0.44, 0.42, 16)
        keycap(s, rx + 3.37, y + 0.07, k2, 0.44, 0.42, 16)
        text(s, rx + 4.05, y + 0.12, 1.4, 0.35, lim, 16, AMBER if i == 3 else WHITE, True, align=RIGHT)
    bullets(s, rx, 4.88, 5.6, 2.0, [
        [("Mỗi lần bấm: ", {"bold": True}), "đế, vai, khuỷu nhích 2°; kẹp 5°"],
        [("PCA9685: ", {"bold": True}), "I²C 0x40, xung 50 Hz; nguồn riêng 5–6 V, không lấy từ USB"],
        [("Laptop ↔ Arduino: ", {"bold": True}), "USB 9600 baud; HC-05 (D2/D3) có sẵn trong firmware, tùy chọn"],
    ], 14.5, after=7)
    footer(s, 4)
    notes(s, """
Phần cứng gồm ba khối. Khối điều khiển là Arduino Uno cộng mạch PCA9685 sinh xung cho servo, trong ảnh dưới bên trái. Khối chấp hành là cánh tay bốn bậc tự do dùng servo MG996R: kênh không là đế, kênh một là vai, kênh hai là khuỷu, kênh ba là tay kẹp. Khối cảm biến là hai camera: OBSBOT Meet SE treo trên nhìn xuống, và camera của MacBook đặt thấp phía trước, cả hai ở độ phân giải 1920 nhân 1080.

Mỗi servo có giới hạn cứng trong firmware, như bảng bên phải. Mỗi lần bấm một phím, đế, vai và khuỷu nhích hai độ để căn cho chính xác, còn tay kẹp nhích năm độ. Điểm cần nhớ về nguồn: servo lấy điện từ nguồn tổ ong riêng năm đến sáu vôn cấp vào PCA9685, không lấy từ cổng USB của laptop.

Bốn ảnh ở đây đều là ảnh thật; hai ảnh trên là hai camera của hệ thống nhìn cùng một cảnh.

Nếu được hỏi: tay kẹp có mấy ngón? Hai ngón, cơ cấu song song, một servo. Vì sao giới hạn kẹp là 160 độ? Xem slide 12. Có phản hồi vị trí không? Không: MG996R ở đây chỉ nhận lệnh góc, Arduino báo lại góc đã ra lệnh (slide 9). Chạy trên Windows được không? Mã có phần tìm cổng COM và tên camera trên Windows, nhưng nhóm chạy và chụp ảnh trên macOS.

Nguồn: README.md mục 1; robot_arm_4dof/flash.sh:19 (arduino:avr:uno); robot_arm_4dof.ino:6,8,13-14,19-21,86-90,121-152; control.py:56-63.
""")


# ==============================================================================
# Slide 5: Tờ A4 thành hệ tọa độ
# ==============================================================================
def slide_05(prs):
    s = new_slide(prs)
    header(s, "03 · Hệ thống nhìn", "Bốn mã ArUco biến tờ A4 thành thước đo bằng cm")
    image(s, "sw_annot_top.jpg", 0.6, 1.68, 5.95, 3.25)
    image(s, "sw_annot_side.jpg", 6.78, 1.68, 5.95, 3.25)
    caption(s, 0.6, 4.98, 5.95, "Cam TRÊN: lưới 5 cm dựng từ 4 mã; cốc đo được ở X = 16,5 cm, Y = 13,8 cm", 11.5, 0.3)
    caption(s, 6.78, 4.98, 5.95, "Cam NGANG: cùng tờ giấy nhìn nghiêng, cùng lưới tọa độ", 11.5, 0.3)
    cols = [
        ("4 mã ở 4 góc", "DICT_4X4_50, ID 0–3, cạnh 2,8 cm; in A4 đúng 100%"),
        ("Homography", "pixel ↔ cm cho cả hai camera; gốc ở mã ID 0, X dài 29,7 cm, Y rộng 21,0 cm"),
        ("Che mất mã vẫn chạy", "dùng vị trí đã nhớ; xô camera thì tự học lại; phím U dò lại"),
        ("Sửa lệch phối cảnh", "cam TRÊN treo ≈ 46 cm: vật cao 5 cm lệch ≈ 1 cm. Một phép đo: 1,2 → 0,2 cm"),
    ]
    for i, (t, d) in enumerate(cols):
        x = 0.6 + i * 3.08
        dot(s, x, 5.5, i + 1, d=0.36, size=13)
        text(s, x + 0.48, 5.5, 2.5, 0.32, t, 15.5, WHITE, True)
        text(s, x + 0.48, 5.86, 2.5, 1.05, d, 12.5, MUTED, spacing=1.05)
    footer(s, 5)
    notes(s, """
Điều đầu tiên hệ thống phải biết là vật nằm ở đâu, tính bằng xăng-ti-mét. Nhóm in một tờ A4 có bốn mã ArUco ở bốn góc; mỗi mã có số định danh và OpenCV tìm được bốn góc của mã.

Biết bốn góc ngoài đời cách nhau hai mươi chín phẩy bảy nhân hai mươi mốt xăng-ti-mét, chương trình tính phép biến đổi phẳng gọi là homography, đổi từng pixel sang tọa độ trên tờ giấy, cho cả hai camera. Gốc tọa độ ở mã số không. Che mất một hai mã thì chương trình dùng vị trí đã nhớ.

Một chi tiết nhóm phải sửa: camera trên treo cao khoảng bốn mươi sáu xăng-ti-mét, nên nắp cốc cao năm xăng-ti-mét bị lệch ra xa tâm ảnh khoảng một xăng-ti-mét. Nhóm sửa bằng một công thức tỉ lệ theo độ cao vật; ở một vị trí đã đo, hai camera lệch nhau một phẩy hai xăng-ti-mét trước khi sửa và không phẩy hai sau khi sửa. Hai ảnh là lưới do chương trình vẽ lên khung hình camera thật đã lưu.

Nếu được hỏi: vì sao ArUco? Vì mã có số định danh, cho bốn góc rõ ràng, chịu được nhìn nghiêng, và OpenCV có sẵn. Tờ giấy là hệ quy chiếu chung cho cả hai camera, nên đổi camera hay đổi chỗ đặt không phải đo lại bằng thước. Độ cao bốn mươi sáu xăng-ti-mét đo thế nào? Ước từ ảnh, chưa đo bằng thước; con số không phẩy hai chỉ là một phép đo.

Nguồn: generate_aruco_a4.py:3,31-36; vision.py:24-30,152-170,486-505,557-562; tests/test_vision.py:223-243; README.md mục 4.
""")


# ==============================================================================
# Slide 6: Nhận diện vật
# ==============================================================================
def slide_06(prs):
    s = new_slide(prs)
    header(s, "03 · Nhận diện vật", "Tìm vật bằng màu; YOLO chỉ là tùy chọn")
    cards = [
        ("MẶC ĐỊNH", GREEN, "Tách màu trên giấy trắng",
         "Dựng ảnh phẳng của tờ A4 rồi tách vật có màu đậm (cốc đỏ). Bỏ khối rộng > 8 cm, dài > 18 cm, chạm mép giấy, "
         "hoặc dính phần đen của cánh tay: bàn tay người không bị nhận thành vật."),
        ("CHẮC NHẤT", GREEN, "Mã ArUco ID 10–29 trên vật",
         "Dán mã lên vật: cho vị trí chắc chắn; kích thước vật tra bảng OBJECT_SPECS."),
        ("TÙY CHỌN · --yolo", AMBER, "YOLO11s (bộ COCO)",
         "Nhận tên vật. Trọng số có sẵn, nhóm chưa huấn luyện lại. Bỏ 12 lớp không phải vật cần gắp; vật YOLO tìm ra cũng phải có màu."),
    ]
    for i, (tag, col, title, desc) in enumerate(cards):
        x = 0.6 + i * 4.11
        box(s, x, 1.7, 3.91, 2.55, fill=CARD, edge=col if i == 0 else EDGE, edge_w=1.5 if i == 0 else 1.0)
        chip(s, x + 0.2, 1.88, None, 0.34, tag, edge=col, color=col, size=10.5)
        text(s, x + 0.2, 2.34, 3.55, 0.38, title, 17, WHITE, True)
        text(s, x + 0.2, 2.78, 3.55, 1.42, desc, 13, MUTED, spacing=1.08)
    image(s, "ui_guide_cameras.png", 0.6, 4.45, 7.65, 2.2, mode="cover", focus=(0.5, 0.45))
    caption(s, 0.6, 6.68, 7.65, "Màn hình bản TRƯỚC khi đơn giản hóa (02/11): YOLO gọi chi tiết robot là bottle, airplane; nắp cốc là frisbee", 11, 0.3)
    box(s, 8.5, 4.45, 4.23, 2.2, fill=CARD)
    card_title(s, 8.75, 4.6, 3.9, "Chọn vật nào?", AMBER, 12.5)
    bullets(s, 8.75, 4.98, 3.85, 1.65, [
        "Vật gần đế nhất được chọn trước",
        [("TAB", {"bold": True, "color": AMBER}), " đổi sang vật khác"],
        "Trung bình 10 khung cho đỡ rung",
        "Bị che (kẹp che cốc): nhớ vị trí 120 giây",
    ], 14, after=4)
    footer(s, 6)
    notes(s, """
Biết tờ giấy rồi thì phải tìm vật. Cách mặc định là tách màu trên nền giấy trắng: chương trình dựng ảnh phẳng của tờ A4 rồi tách vật có màu đậm như cốc đỏ, không cần mã. Bàn tay người đưa vào không bị nhận thành vật, vì bộ lọc bỏ khối quá to, chạm mép giấy, hoặc dính vào phần đen của cánh tay.

Cách chắc nhất là dán mã ArUco số mười tới hai mươi chín lên vật. Cách thứ ba là YOLO11 bản COCO, nhóm chưa huấn luyện lại, và nó chỉ là tùy chọn. Lý do ở ảnh bên dưới: trên màn hình bản trước, YOLO gọi chi tiết robot là chai và máy bay, gọi nắp cốc là đĩa ném. Vì vậy bản hiện tại tắt YOLO mặc định.

Khi có nhiều vật, vật gần đế nhất được chọn trước, phím TAB đổi vật; vị trí lấy trung bình mười khung cho đỡ rung, và khi càng kẹp che mất cốc thì chương trình nhớ vị trí cũ trong hai phút.

Nếu được hỏi: có huấn luyện YOLO không? Chưa; huấn luyện lại cho vật thật là việc có thể làm sau. Vì sao còn giữ YOLO? Để nhận tên vật khi cần; còn vị trí xăng-ti-mét luôn tính từ homography của tờ giấy. Ảnh chụp màn hình lấy ở đâu? Từ giao diện cũ trước khi đơn giản hóa; hiện tượng nhận nhầm là có thật và là lý do YOLO bị tắt.

Nguồn: main.py:53 (--yolo); vision.py:43-47,271-300,365-368,476-486,491-492,507-515; control.py:68-69,542-566.
""")


# ==============================================================================
# Slide 7: NHÓM 1 · Điều khiển (động học ngược)
# ==============================================================================
def arm_diagram(s):
    """Cánh tay nhìn ngang ở tư thế servo vai 90°, khuỷu 90° (mô hình mặc định), tỉ lệ 1 inch = 55 mm."""
    k = 1 / 55.0
    table_y, sx = 5.2, 1.65
    sy = table_y - 70 * k
    ex, ey = sx + 105 * k * 0.7071, sy - 105 * k * 0.7071
    wx, wy = ex + 100 * k, ey
    tx, ty = wx + 65 * k, wy + 25 * k
    line(s, 0.75, table_y, 6.35, table_y, MUTED, 1.5)
    text(s, 4.95, table_y + 0.06, 1.4, 0.25, "mặt bàn", 11, MUTED, align=RIGHT)
    box(s, sx - 0.3, table_y - 0.42, 0.6, 0.42, fill=EDGE, edge=None, shape=MSO_SHAPE.RECTANGLE)
    line(s, sx, table_y - 0.42, sx, sy, EDGE, 7)
    line(s, sx, sy, ex, ey, AMBER, 7)
    line(s, ex, ey, wx, wy, AMBER, 7)
    line(s, wx, wy, tx, wy, MUTED, 1.75, dash=True)
    line(s, tx, wy, tx, ty, MUTED, 1.75, dash=True)
    for (jx, jy) in ((sx, sy), (ex, ey), (wx, wy)):
        box(s, jx - 0.1, jy - 0.1, 0.2, 0.2, fill=WHITE, edge=AMBER, edge_w=2, shape=MSO_SHAPE.OVAL)
    box(s, tx - 0.09, ty - 0.09, 0.18, 0.18, fill=RED, edge=None, shape=MSO_SHAPE.OVAL)
    text(s, 0.6, (sy + table_y) / 2 - 0.16, sx - 0.4 - 0.6, 0.3, "d1 = 70", 13, WHITE, True, align=RIGHT)
    text(s, sx - 1.05, ey + 0.38, 1.25, 0.3, "L2 = 105", 13, AMBER, True, align=RIGHT)
    text(s, (ex + wx) / 2 - 0.65, ey - 0.42, 1.3, 0.3, "L3 = 100", 13, AMBER, True, align=CENTER)
    text(s, (wx + tx) / 2 - 0.62, wy - 0.42, 1.24, 0.3, "L4r = 65", 12, MUTED, True, align=CENTER)
    text(s, tx + 0.12, (wy + ty) / 2 - 0.15, 1.0, 0.3, "L4z = 25", 12, MUTED, True)
    text(s, tx - 1.0, ty + 0.14, 1.6, 0.3, "điểm kẹp", 12, RED, True, align=CENTER)
    text(s, sx + 0.18, sy - 0.05, 0.9, 0.3, "θ2", 13, WHITE, True)
    text(s, ex + 0.12, ey + 0.08, 0.9, 0.3, "θ3", 13, WHITE, True)


def slide_07(prs):
    s = new_slide(prs)
    header(s, "04 · Nhóm 1 · Điều khiển", "Từ vị trí (X, Y) của vật tính ra góc ba servo")
    arm_diagram(s)
    caption(s, 0.6, 5.55, 5.9, "Mô hình mặc định (mm, đo bằng thước): servo vai 90° ↔ θ2 = 45°, servo khuỷu 90° ↔ θ3 = −45°. "
            "Không có servo cổ tay nên hướng ngón kẹp không chọn được.", 12, 0.75)
    steps = [
        "Đổi (X, Y) cm trên giấy sang tọa độ robot (mm) theo vị trí và hướng của đế",
        [("Đế: ", {"bold": True}), ("θ1 = atan2(y, x)", {"font": MONO, "bold": True, "color": AMBER})],
        "Vai, khuỷu: giải tam giác hai khâu, chọn nghiệm khuỷu hướng lên; điểm kẹp cao 25 mm",
        "Đổi ra góc servo, làm tròn bội số 2°; số lần bấm = độ lệch ÷ 2°",
    ]
    for i, st in enumerate(steps):
        y = 1.72 + i * 0.78
        dot(s, 6.85, y + 0.02, i + 1, d=0.38, size=14)
        text(s, 7.38, y, 5.35, 0.72, [st] if isinstance(st, list) else st, 15.5, WHITE, spacing=1.05)
    box(s, 6.85, 4.95, 5.88, 1.9, fill=CARD, edge=AMBER, edge_w=1.25)
    text(s, 7.1, 5.07, 5.5, 0.28, "VÍ DỤ · CỐC Ở (20,1; 7,4) CM", 12, AMBER, True, spc=60)
    text(s, 7.1, 5.37, 5.5, 0.45, "đế 74° · vai 58° · khuỷu 90°", 24, WHITE, True)
    text(s, 7.1, 5.98, 1.75, 0.42, "Từ Home 90/90/90:", 13, MUTED, anchor=MIDDLE)
    keycap(s, 8.88, 5.98, "D", 0.44, 0.42, 16)
    text(s, 9.38, 5.98, 0.6, 0.42, "× 8", 17, WHITE, True, anchor=MIDDLE)
    keycap(s, 10.02, 5.98, "S", 0.44, 0.42, 16)
    text(s, 10.52, 5.98, 0.7, 0.42, "× 16", 17, WHITE, True, anchor=MIDDLE)
    text(s, 11.25, 5.98, 1.4, 0.42, "khuỷu đã đúng", 12, GREEN, True, anchor=MIDDLE)
    text(s, 7.1, 6.48, 5.5, 0.3, "robot x = 240 mm, y = −73 mm · dùng mô hình đã hiệu chỉnh (slide 11)", 11, MUTED)
    footer(s, 7)
    notes(s, """
Biết vật ở X, Y, nhóm một tính ba servo cần ở góc nào: đây là bài toán động học ngược.

Cánh tay nhìn ngang như hình: trục vai cao bảy mươi mi-li-mét so với mặt bàn, khâu vai dài một trăm linh năm, khâu khuỷu dài một trăm, tâm hai ngón kẹp lệch sáu mươi lăm ra trước và hai mươi lăm xuống dưới. Đó là số đo bằng thước của mô hình mặc định; slide mười một sẽ cho thấy chúng được hiệu chỉnh lại.

Có bốn bước: đổi tọa độ trên giấy sang tọa độ robot; góc đế bằng a-tan-hai của y trên x; vai và khuỷu giải tam giác hai khâu, chọn nghiệm khuỷu hướng lên, với điểm kẹp cao hai mươi lăm mi-li-mét; cuối cùng đổi ra góc servo, làm tròn bội số hai độ, rồi độ lệch chia hai là số lần bấm.

Ví dụ cốc ở hai mươi phẩy một và bảy phẩy bốn xăng-ti-mét: gợi ý đế bảy mươi bốn, vai năm mươi tám, khuỷu chín mươi độ. Từ Home, khi ba servo đều ở chín mươi độ, bấm D tám lần và S mười sáu lần; khuỷu đã đúng. Cánh tay không có servo cổ tay nên hướng ngón kẹp không chọn được.

Nếu được hỏi: công thức có được kiểm lại không? Có: trong bộ test, chương trình đưa kết quả động học ngược vào động học thuận trên hơn một trăm điểm trong tầm với và thấy sai số dưới không phẩy một mi-li-mét. Vì sao nghiệm khuỷu hướng lên? Tam giác hai khâu có hai nghiệm; code luôn chọn khuỷu hướng lên để mỗi điểm chỉ có một bộ góc. Vật ngoài tầm với thì sao? Màn hình báo VAT NGOAI TAM VOI và cần dời vật lại gần thêm bao nhiêu mi-li-mét.

Nguồn: control.py:36-67,98-161,174-195,221-245; tests/test_control.py:16-35; 05_SO_LIEU_VA_NGUON.md mục 3 và 16 (ví dụ tính lại bằng check_facts.py --deep).
""")


# ==============================================================================
# Slide 8: Màn hình hai phần
# ==============================================================================
def slide_08(prs):
    s = new_slide(prs)
    header(s, "04 · Màn hình hai phần", "Màn hình chỉ nói một việc: bấm phím nào, mấy lần")
    image(s, "ui_screen_before.png", 0.6, 1.66, 8.2, None, mode="fit")
    caption(s, 0.6, 6.38, 8.2, "Màn hình thật của chương trình, chạy trên ảnh camera thật đã lưu (20:27); cánh tay MÔ PHỎNG "
            "(chân trang ghi USB Arduino: MO PHONG). Chữ không dấu vì OpenCV không vẽ được dấu.", 11.5, 0.55)
    rx, rw = 9.1, 3.63
    dot(s, rx, 1.72, 1, d=0.4, size=14)
    text(s, rx + 0.52, 1.72, rw - 0.52, 0.35, "Phần 1 · Điều khiển", 16, AMBER, True)
    text(s, rx + 0.52, 2.08, rw - 0.52, 0.95, "phím to, số lần, hạ / quay bao nhiêu độ; ba hàng servo: góc hiện tại → góc đích", 13, WHITE, spacing=1.05)
    dot(s, rx, 3.08, 2, GREEN, d=0.4, size=14)
    text(s, rx + 0.52, 3.08, rw - 0.52, 0.35, "Phần 2 · Success", 16, GREEN, True)
    text(s, rx + 0.52, 3.44, rw - 0.52, 0.7, "CHƯA XONG, còn N lần bấm; hoặc XONG! khi cả ba servo tới góc", 13, WHITE, spacing=1.05)
    box(s, rx, 4.3, rw, 1.32, fill=CARD)
    text(s, rx + 0.18, 4.4, rw - 0.3, 0.28, "TRÁI / PHẢI NHÌN THEO CAM NGANG", 10.5, MUTED, True, spc=30)
    keycap(s, rx + 0.18, 4.75, "A", 0.44, 0.42, 16)
    text(s, rx + 0.7, 4.75, 1.2, 0.42, "sang phải", 14, WHITE, anchor=MIDDLE)
    keycap(s, rx + 1.9, 4.75, "D", 0.44, 0.42, 16)
    text(s, rx + 2.42, 4.75, 1.2, 0.42, "sang trái", 14, WHITE, anchor=MIDDLE)
    text(s, rx + 0.18, 5.24, rw - 0.3, 0.3, "W S vai · I K khuỷu · mỗi lần 2°", 12.5, MUTED)
    text(s, rx, 5.82, rw, 0.95, [[("Trong ảnh: ", {"color": MUTED}), "cốc ở (16,5; 13,8) cm"],
                                 [("→ ", {"color": AMBER}), ("BẤM S × 15", {"color": AMBER, "bold": True}), ", hạ vai 30°"],
                                 "đế đã đúng · còn 18 lần bấm"], 13, WHITE, spacing=1.08)
    footer(s, 8)
    notes(s, """
Đây là màn hình của chương trình, chạy trên ảnh camera thật đã lưu với cánh tay mô phỏng, nên chân trang ghi mô phỏng. Hai khung camera ở trên có lưới tọa độ, vòng DICH quanh cốc và dấu KEP là chỗ đầu kẹp theo mô hình.

Bên dưới là hai phần nối nhau bằng một mũi tên. Phần một vẽ từ Plan của nhóm một: một lệnh to. Trong ảnh, cốc ở mười sáu phẩy năm và mười ba phẩy tám xăng-ti-mét, lệnh là bấm S mười lăm lần, hạ vai ba mươi độ, còn mười tám lần bấm. Ba hàng bên dưới là ba servo; hàng nào đã đúng thì ghi ĐÃ ĐÚNG, như hàng đế chỉ lệch hai độ. Phần hai vẽ từ kết quả của nhóm hai: chưa xong, còn bao nhiêu lần bấm, hoặc XONG.

Chữ không dấu vì OpenCV không vẽ được dấu tiếng Việt. Trái phải nhìn theo camera MacBook đặt trước robot, nên phím A quay đế sang phải, phím D sang trái. Màn hình chỉ cho biết phải bấm gì; người điều khiển là người bấm.

Nếu được hỏi: có tự gửi phím không? Không; chương trình chỉ gửi phím khi người bấm. Vì sao chỉ một lệnh to? Để người điều khiển làm theo được ngay, không phải đọc bảng số. Vì sao thứ tự đế, rồi vai, rồi khuỷu? Là thứ tự code lập lệnh; hàng nào đã đúng thì được bỏ qua. Ảnh camera là ảnh cũ mà vẫn có gợi ý? Ảnh là khung camera thật lúc hai mươi giờ hai mươi bảy, chương trình đọc nó như camera đang chạy, còn cánh tay mô phỏng đặt ở Home. Gợi ý trên ảnh này là đế 88, vai 60, khuỷu 84, gần tư thế người thật sự ôm cốc lúc hai mươi giờ ba mươi hai, khoảng 85, 60, 90 (đọc từ màn hình bản cũ); nhưng chưa rõ lần ôm đó có nằm trong mười mẫu khớp hay không, nên chỉ nói là gần.

Nguồn: screen.py:157-239,249-259; main.py:155-180; control.py:211-217; ảnh ui_screen_before (tạo bằng slides/tools/make_screen_images.py).
""")


# ==============================================================================
# Slide 9: NHÓM 2 · Success
# ==============================================================================
def slide_09(prs):
    s = new_slide(prs)
    header(s, "05 · Nhóm 2 · Success", "XONG khi ba servo tới góc gợi ý và giữ yên một giây")
    rows = [("± 2°", "mỗi servo lệch không quá một bước bấm so với góc gợi ý (lệch 3° là chưa)"),
            ("3 servo", "đế, vai, khuỷu; tay kẹp không tính"),
            ("1 giây", "giữ đúng liên tục một giây mới đếm thêm một lần thành công")]
    for i, (big, desc) in enumerate(rows):
        y = 1.72 + i * 1.02
        box(s, 0.6, y, 5.95, 0.9, fill=CARD)
        text(s, 0.8, y, 1.75, 0.9, big, 30, GREEN, True, anchor=MIDDLE)
        text(s, 2.6, y, 3.8, 0.9, desc, 14.5, WHITE, anchor=MIDDLE, spacing=1.05)
    chip(s, 0.6, 4.83, 2.9, 0.38, "ĐÃ KIỂM: 7 TEST + CHUỖI ĐẦU–CUỐI", edge=GREEN, color=GREEN, size=10)
    chip(s, 3.62, 4.83, 2.93, 0.38, "CHƯA ĐẾM TRÊN CÁNH TAY THẬT", edge=RED, color=RED, size=10)
    image(s, "ui_screen_done.png", 6.85, 1.72, 5.88, None, mode="fit")
    caption(s, 6.85, 5.1, 5.88, "Mô phỏng: bấm đủ phím theo lệnh thì phần 2 báo XONG! và đếm 1 lần (ảnh camera thật đã lưu, 20:32:52)", 11, 0.4)
    for i, (title, col, body) in enumerate([
        ("Vì sao kẹp không tính", AMBER, "Cốc thon dần xuống đáy: hai ngón đẩy cốc ra ở 150–160°; cốc đổ khoảng 3 lần trong buổi thử."),
        ("Giới hạn của chữ XONG", RED, "Arduino báo lại góc đã RA LỆNH; MG996R không báo vị trí thật. XONG = đã bấm đủ phím, chưa phải đo thấy kẹp sát cốc."),
    ]):
        x = 0.6 + i * 6.15
        box(s, x, 5.58, 5.98, 1.27, fill=CARD, edge=col, edge_w=1.0)
        card_title(s, x + 0.2, 5.68, 5.6, title, col, 12)
        text(s, x + 0.2, 5.98, 5.6, 0.85, body, 13.5, WHITE, spacing=1.05)
    footer(s, 9)
    notes(s, """
Nhóm hai chỉ trả lời một câu: ba servo đế, vai, khuỷu đã tới góc nhóm một gợi ý chưa. Nó không biết gì về camera, động học hay cổng USB, chỉ đọc Plan.

Quy tắc có ba điều. Mỗi servo lệch không quá một bước bấm, tức hai độ, là đã tới; nhóm chọn hai độ vì mô hình hình học vốn chỉ chính xác cỡ đó. Chỉ tính ba servo của cánh tay, không tính tay kẹp. Và cả ba phải giữ đúng liên tục một giây mới đếm thêm một lần thành công; lướt qua thì không đếm.

Tay kẹp không tính vì cốc nhóm dùng thon dần xuống đáy: khép hai ngón tới một trăm năm mươi, một trăm sáu mươi độ thì cốc bị đẩy ra, và trong buổi thử cốc đổ khoảng ba lần.

Hai điều nhóm nói thẳng. Chữ XONG nghĩa là ba góc lệnh đã tới, vì MG996R không báo vị trí thật; nó chưa phải bằng chứng hai ngón kẹp đang sát cốc. Và ảnh bên phải là mô phỏng trên ảnh thật đã lưu; trên cánh tay thật nhóm chưa có lần đếm nào cho bản này.

Nếu được hỏi: vì sao giữ một giây? Để lướt qua mục tiêu không bị tính là thành công. Có thể kiểm bằng camera không? Bản trước có làm, bằng hai tín hiệu từ hai camera; nhóm đã bỏ để mã đơn giản. Đếm ở đâu? Ở dòng Thanh cong: N lan trên phần hai; chưa ghi ra file. Không thấy vật thì sao? Không bao giờ báo xong: trạng thái là chưa thấy vật.

Nguồn: success.py:16-17,19,22-75; tests/test_success.py (7 test); tests/test_end_to_end.py:11-47; robot_arm_4dof.ino:70-83; README.md mục 6; ảnh ui_screen_done (tạo bằng slides/tools/make_screen_images.py).
""")


# ==============================================================================
# Slide 10: Thử trên cánh tay thật
# ==============================================================================
def slide_10(prs):
    s = new_slide(prs)
    header(s, "06 · Thử trên cánh tay thật", "Cốc đỏ được kẹp, chuyển sang trái và đặt xuống")
    x0, w, gap = 1.62, 3.63, 0.12
    h = w * 9 / 16
    cols = [("demo_06_grip", "20:32:52 · KẸP"), ("demo_07_carry", "20:33:02 · CHUYỂN SANG TRÁI"), ("demo_08_place", "20:33:12 · ĐẶT XUỐNG")]
    for c, (stem, lab) in enumerate(cols):
        x = x0 + c * (w + gap)
        text(s, x, 1.66, w, 0.3, lab, 13, AMBER, True, align=CENTER)
        image(s, f"{stem}_side.jpg", x, 2.0, w, h)
        image(s, f"{stem}_top.jpg", x, 2.0 + h + gap, w, h)
    for r, lab in enumerate(["CAM\nNGANG", "CAM\nTRÊN"]):
        y = 2.0 + r * (h + gap)
        text(s, 0.6, y, 0.92, h, lab.split("\n"), 13, MUTED, True, anchor=MIDDLE, spacing=1.0)
    chip(s, 0.6, 6.35, 3.3, 0.42, "NGƯỜI BẤM PHÍM · KHÔNG TỰ ĐỘNG", fill=AMBER, color=DARK, size=11.5)
    text(s, 4.1, 6.3, 8.63, 0.55, "02/11/2026 · khung cắt từ video, cách nhau 10 giây · màn hình bản trước khi đơn giản hóa · "
         "cốc đổ khoảng 3 lần và được dựng lại bằng tay · chưa có tỉ lệ thành công", 12, MUTED, spacing=1.05)
    footer(s, 10)
    notes(s, """
Đây là bằng chứng cánh tay thật làm được việc. Ba cột cách nhau mười giây trong buổi thử ngày hai tháng mười một, hàng trên là camera ngang, hàng dưới là camera trên: cốc nằm giữa hai ngón kẹp, cốc được chuyển sang trái, rồi đặt xuống và cánh tay rút về. Nhóm làm vòng này nhiều lần.

Ba điều cần nói rõ. Đây là người bấm phím nhìn hình hai camera, trên màn hình bản trước khi đơn giản hóa, chưa phải tự động. Cốc bị đổ khoảng ba lần và được dựng lại bằng tay. Và đây chưa phải số liệu tỉ lệ thành công: nhóm chưa có tỉ lệ nào.

Góc servo lúc kẹp, đọc từ màn hình bản cũ: đế khoảng tám mươi lăm, vai sáu mươi đến sáu mươi lăm, khuỷu tám mươi lăm đến chín mươi độ. Chính những lần ôm cốc như thế này là dữ liệu để hiệu chỉnh mô hình, ở slide tiếp theo.

Nếu được hỏi: có video không? [...điền: có / không; nếu có thì chiếu đoạn 20–30 giây]. Kẹp có giữ chắc không? Không hẳn: cốc đổ khoảng ba lần, và các lần thử sau cho thấy cốc thon bị đẩy ra ở 150–160 độ.

Nguồn: ảnh demo_06, demo_07, demo_08 (khung cắt từ video 02/11/2026, 20:32:52 đến 20:33:12); 05_SO_LIEU_VA_NGUON.md mục 7.
""")


# ==============================================================================
# Slide 11: Sự cố 1 · mô hình lệch và hiệu chỉnh
# ==============================================================================
def slide_11(prs):
    s = new_slide(prs)
    header(s, "07 · Sự cố 1", "Mô hình lệch 3,5–5,9 cm; hiệu chỉnh bằng 10 lần ôm còn 8,5 mm", size=26)
    card_title(s, 0.6, 1.72, 5.4, "Đầu kẹp theo mô hình mặc định cách cốc thật", MUTED, 12)
    for i, (big, desc) in enumerate([("5,4 cm", "ôm lúc 20:32 · servo [85, 60, 90]"),
                                     ("3,5 cm", "ôm lúc 20:46 · servo [80, 70, 75]"),
                                     ("5,9 cm", "ôm lúc 21:03 · servo [75, 85, 50]")]):
        y = 2.06 + i * 0.62
        text(s, 0.6, y, 1.75, 0.55, big, 26, RED, True, anchor=MIDDLE)
        text(s, 2.4, y, 3.6, 0.55, desc, 14, WHITE, anchor=MIDDLE)
    text(s, 0.6, 3.98, 5.45, 0.55, "Cùng chiều, cùng cỡ: lệch có hệ thống, nên sửa được bằng cách khớp lại mô hình", 13.5, MUTED, spacing=1.05)
    card_title(s, 0.6, 4.66, 5.4, "Cách sửa: hiệu chỉnh bằng các lần ôm cốc", GREEN, 12)
    steps(s, 0.6, 5.02, 5.45, [
        "Người bấm phím cho hai ngón ôm quanh cốc; ghi 3 góc servo và vị trí cốc",
        "10 lần ở các chỗ khác nhau; khớp vị trí, hướng đế, 2 góc chuẩn và càng kẹp (Levenberg–Marquardt, numpy)",
        "Lưu vào calibration.json",
    ], 13, dot_color=GREEN, d=0.3, gap=0.1)
    image(s, "calib_before_after_side.jpg", 6.33, 1.7, 6.4, 3.5)
    caption(s, 6.33, 5.25, 6.4, "Khung cam NGANG lúc ôm cốc 21:03: dấu MAC DINH (mô hình mặc định) cách cốc ≈ 5 cm, dấu SAU HIEU CHINH ≈ 1 cm. "
            "Lần ôm này nằm trong 10 mẫu khớp: minh họa, không phải kiểm độc lập.", 11, 0.6)
    for i, (big, desc) in enumerate([("8,5 mm", ["sai số khớp (RMS)", "trên 10 mẫu"]), ("11,6 mm", ["bỏ-một-mẫu", "(leave-one-out)"])]):
        x = 6.33 + i * 3.25
        box(s, x, 5.98, 3.15, 0.87, fill=CARD, edge=GREEN, edge_w=1.0)
        text(s, x + 0.15, 5.98, 1.5, 0.87, big, 21, GREEN, True, anchor=MIDDLE)
        text(s, x + 1.62, 5.98, 1.48, 0.87, desc, 11.5, WHITE, anchor=MIDDLE, spacing=1.02)
    footer(s, 11)
    notes(s, """
Đây là chỗ nhóm học được nhiều nhất. Gợi ý trên màn hình tính từ mô hình cánh tay chứ không đo bằng camera, nên mô hình lệch thì gợi ý nào cũng lệch.

Bằng chứng ở cột trái: người điều khiển bấm phím cho hai ngón kẹp ôm quanh cốc, nhóm ghi ba góc servo và vị trí cốc. Đưa ba tư thế đầu vào mô hình mặc định, đầu kẹp theo mô hình cách cốc thật năm phẩy bốn, ba phẩy năm và năm phẩy chín xăng-ti-mét, cùng chiều, cùng cỡ: lỗi có hệ thống chứ không phải nhiễu.

Cách sửa là hiệu chỉnh bằng trình diễn: mười lần ôm cốc ở các chỗ khác nhau, khớp lại vị trí và hướng đế, hai góc chuẩn của vai và khuỷu, và càng kẹp, bằng thuật toán Levenberg–Marquardt viết thuần numpy. Sai số khớp còn tám phẩy năm mi-li-mét, và mười một phẩy sáu khi bỏ lần lượt từng mẫu. Trong ảnh, dấu cam là mô hình mặc định, dấu xanh là sau hiệu chỉnh, sát cốc; lần ôm này nằm trong mười mẫu nên chỉ là minh họa.

Giới hạn nhóm nói thẳng: tám phẩy năm là sai số trên chính mười mẫu dùng để khớp; nhóm chưa thử bấm theo gợi ý mới trên cánh tay thật; và hiệu chỉnh chỉ đúng với tờ giấy và chỗ đặt robot lúc đo.

Nếu được hỏi: nguyên nhân lệch là gì? Có ba: vị trí và hướng của đế khác mặc định; hai góc chuẩn của vai và khuỷu khi servo ở chín mươi độ khác bốn mươi lăm độ, vì phụ thuộc cách lắp cần servo mà thước không đo được; và càng kẹp gắn cứng vào khâu khuỷu nên điểm kẹp quay theo khâu đó, trong khi mô hình cũ giữ độ lệch cố định theo phương ngang. con số năm phẩy bốn có độc lập không? Màn hình bản cũ lúc hai mươi giờ ba mươi hai báo sai số đầu kẹp năm mươi sáu mi-li-mét, cùng cỡ. Vì sao không đo lại bằng thước? Thước đo được chiều dài các khâu, không đo được góc lắp cần servo; hiệu chỉnh bằng trình diễn làm được cả hai việc. Ví dụ sau hiệu chỉnh? Cốc ở hai mươi phẩy một và bảy phẩy bốn cho gợi ý bảy mươi bốn, năm mươi tám, chín mươi; hai tư thế người căn tay quanh cốc ở chỗ đó cho đầu kẹp theo mô hình cách cốc khoảng năm đến sáu mi-li-mét, nhưng chưa rõ hai tư thế đó có nằm trong mười mẫu khớp hay không, nên chỉ nói là gần. Vì sao ảnh ghi khoảng năm xăng-ti-mét mà cột trái ghi năm phẩy chín? Cột trái dùng vị trí cốc ghi lúc ôm; ảnh đo lại từ camera ngang với độ chính xác khoảng một xăng-ti-mét; hai số cùng cỡ.

Nguồn: calibration.json (mục arm, claw, arm_fit); calibration.py:16-20,77-105; arm_fit.py:1-45; tests/test_arm_fit.py:80-91; 05_SO_LIEU_VA_NGUON.md mục 8 và 16; ảnh calib_before_after_side.
""")


# ==============================================================================
# Slide 12: Sự cố 2 · servo kẹp nóng
# ==============================================================================
def slide_12(prs):
    s = new_slide(prs)
    header(s, "07 · Sự cố 2", "Servo kẹp nóng vì xung PWM không bao giờ nghỉ")
    box(s, 0.6, 1.72, 4.85, 3.85, fill=CARD, edge=RED, edge_w=1.0)
    card_title(s, 0.85, 1.9, 4.4, "Nguyên nhân", RED)
    steps(s, 0.85, 2.38, 4.4, [
        "Firmware cũ không bao giờ ngắt xung: kẹp giữ vật hay chạm chốt chặn thì servo bị ép liên tục, đứng yên cũng vậy",
        "Lệnh đóng kẹp cũ 175° (xung ≈ 2,74 ms), vượt dải 0,5–2,5 ms của MG996R",
    ], 15.5, dot_color=RED, d=0.36, gap=0.3, fg=WHITE, spacing=1.08)
    box(s, 5.7, 1.72, 7.03, 3.85, fill=CARD, edge=GREEN, edge_w=1.0)
    card_title(s, 5.95, 1.9, 6.5, "Cách xử lý trong firmware", GREEN)
    fixes = [
        "Giới hạn cứng góc kẹp 160°; mỗi lần bấm kẹp chỉ nhích 5°",
        "Kẹp mở hết cỡ (95°) mà 5 giây không có lệnh → ngắt xung",
        "Kẹp đã khép quá 60 giây → ngắt xung (vật có thể tuột)",
        None,  # Hàng phím X / Z vẽ riêng
        "Màn hình biết tay đang nghỉ: CANH TAY DANG NGHI",
    ]
    for i, st in enumerate(fixes):
        y = 2.38 + i * 0.6
        dot(s, 5.95, y, i + 1, GREEN, d=0.36, size=13)
        if st is None:
            keycap(s, 6.48, y - 0.03, "X", 0.42, 0.4, 15)
            text(s, 6.98, y - 0.03, 2.0, 0.4, "kẹp nghỉ ngay", 15.5, WHITE, anchor=MIDDLE)
            keycap(s, 8.95, y - 0.03, "Z", 0.42, 0.4, 15)
            text(s, 9.45, y - 0.03, 3.1, 0.4, "cả 4 servo nghỉ", 15.5, WHITE, anchor=MIDDLE)
        else:
            text(s, 6.48, y + 0.02, 6.1, 0.4, st, 15.5, WHITE)
    done = "ĐÃ NẠP VÀ KIỂM TRÊN MẠCH THẬT (02/11, 21:42 và 21:54)"
    chip(s, 0.6, 5.85, None, 0.44, done, edge=GREEN, color=GREEN, size=11.5)
    chip(s, 0.6 + chip_w(done, 11.5) + 0.2, 5.85, None, 0.44, "CHƯA ĐO NHIỆT ĐỘ SERVO", edge=RED, color=RED, size=11.5)
    footer(s, 12)
    notes(s, """
Sự cố thứ hai là phần cứng: servo tay kẹp bị nóng. Có hai nguyên nhân. Firmware cũ không bao giờ ngắt xung PWM, nên khi kẹp giữ vật hay chạm chốt chặn thì servo bị ép liên tục. Và lệnh đóng cũ một trăm bảy mươi lăm độ cho xung khoảng hai phẩy bảy bốn mi-li-giây, vượt dải không phẩy năm đến hai phẩy năm của MG996R.

Firmware mới xử lý theo từng lớp: giới hạn cứng góc kẹp một trăm sáu mươi độ; kẹp mở hết cỡ năm giây không có lệnh thì ngắt xung, kẹp đã khép quá sáu mươi giây cũng ngắt; phím X cho kẹp nghỉ ngay, phím Z cho cả bốn servo nghỉ; và màn hình biết khi tay đang nghỉ.

Firmware này đã nạp lúc chín giờ bốn mươi hai và chín giờ năm mươi tư tối ngày hai tháng mười một, và kiểm trên mạch thật. Nhưng nhóm chưa đo nhiệt độ servo, nên chưa có con số nguội đi bao nhiêu.

Nếu được hỏi: phím Z có gì cần chú ý? Cả bốn servo mất xung nên cánh tay tự sụp theo trọng lực: phải hạ đầu kẹp tựa xuống chỗ trống trước. Màn hình biết tay đang nghỉ nên ghi CANH TAY DANG NGHI thay vì tin các góc cũ. vì sao không dùng cảm biến nhiệt? Chưa có trong phần cứng; đây là việc có thể thêm. Giới hạn một trăm sáu mươi có vượt dải xung không? Có, hơi vượt: xung khoảng hai phẩy năm sáu mi-li-giây so với dải danh định hai phẩy năm; chủ máy chấp nhận để kẹp chặt hơn và vẫn có tự nhả xung sau sáu mươi giây. Vì sao ngắt xung khi mở hết cỡ thì hàm khép lại? Khi mất xung, hai hàm rơi thành hình chữ V hẹp, khe còn khoảng một đến hai xăng-ti-mét (ước lượng từ ảnh), nên khi tiếp cận phải bấm J lại.

Nguồn: robot_arm_4dof.ino:16-23,160-176,191-201; control.py (trạng thái relaxed, cảnh báo FIRMWARE CU KHONG CO PHIM Z); README.md mục 6; 05_SO_LIEU_VA_NGUON.md mục 6.
""")


# ==============================================================================
# Slide 13: Kết quả: đã có và chưa kiểm chứng
# ==============================================================================
def slide_13(prs):
    s = new_slide(prs)
    header(s, "08 · Kết quả", "Đã có bằng chứng, và những điều chưa kiểm chứng")
    box(s, 0.6, 1.72, 5.95, 3.55, fill=CARD, edge=GREEN, edge_w=1.25)
    card_title(s, 0.85, 1.88, 5.5, "Đã có bằng chứng", GREEN)
    bullets(s, 0.85, 2.3, 5.5, 2.9, [
        "Hệ tọa độ từ tờ A4 chạy trên cả hai camera (ảnh thật)",
        "Cánh tay thật ôm cốc và chuyển sang trái khi người bấm phím (02/11)",
        "Mô hình khớp 10 lần ôm thật: 8,5 mm, bỏ-một-mẫu 11,6 mm",
        "Firmware chống nóng và phím Z đã nạp, kiểm trên mạch thật",
        "109 test tự động pass, không cần camera hay Arduino",
    ], 15, after=8, mark_color=GREEN)
    box(s, 6.78, 1.72, 5.95, 3.55, fill=CARD, edge=RED, edge_w=1.25)
    card_title(s, 7.03, 1.88, 5.5, "Chưa kiểm chứng", RED)
    bullets(s, 7.03, 2.3, 5.5, 2.9, [
        "Số lần XONG trên cánh tay thật: bản mới mới chạy bằng test và ảnh đã lưu",
        "Bấm đúng theo gợi ý mới thì hai ngón có ôm quanh cốc không",
        "Kẹp giữ chắc cốc thon (cần ma sát hoặc vật thân thẳng)",
        "Nhiệt độ servo kẹp sau khi thêm ngắt xung",
        "Hiệu chỉnh cho tờ giấy mới hoặc robot đặt chỗ khác",
        "Dashboard IoT / MQTT, cảm biến lực: có trong kế hoạch 28/10, chưa làm",
    ], 14, after=5, mark="–", mark_color=RED)
    stats = [("109 / 109", ["test tự động pass", "(≈ 9 giây)"], GREEN),
             ("11", ["tệp test, từ động học", "tới màn hình và Serial"], WHITE),
             ("0", ["lần đếm XONG trên", "cánh tay thật (bản mới)"], RED)]
    for i, (big, desc, col) in enumerate(stats):
        x = 0.6 + i * 4.11
        bw = text_w(big, 30, True) + 0.3
        box(s, x, 5.5, 3.91, 1.35, fill=BG2, edge=None)
        text(s, x + 0.22, 5.5, bw, 1.35, big, 30, col, True, anchor=MIDDLE)
        text(s, x + 0.22 + bw, 5.5, 3.91 - 0.3 - bw, 1.35, desc, 13, MUTED, anchor=MIDDLE, spacing=1.05)
    footer(s, 13)
    notes(s, """
Slide này nói thật những gì nhóm có và chưa có.

Có bằng chứng: hệ tọa độ chạy trên cả hai camera; cánh tay thật ôm cốc và chuyển sang trái khi người bấm phím; mô hình khớp mười lần ôm thật với sai số tám phẩy năm mi-li-mét; firmware chống nóng đã nạp và kiểm trên mạch; và một trăm linh chín test tự động đều pass trong khoảng chín giây, không cần camera hay Arduino thật.

Chưa kiểm chứng: số lần XONG trên cánh tay thật cho bản mới; bấm theo gợi ý mới thì hai ngón có ôm quanh cốc không; kẹp giữ chắc cốc thon; nhiệt độ servo; hiệu chỉnh cho tờ giấy mới; và dashboard IoT với MQTT, cảm biến lực, vốn có trong kế hoạch ngày hai mươi tám tháng mười nhưng chưa làm.

Tóm lại: một trăm linh chín trên một trăm linh chín test pass, và chưa có lần đếm XONG nào trên cánh tay thật.

Nếu được hỏi: vì sao chưa chạy bản mới trên cánh tay thật? Nhóm đơn giản hóa mã ngay trong ngày để giải thích được trong một phút; chạy bản mới với cánh tay là bước đầu của việc tiếp theo. Test gồm những gì? Điều khiển 29, nhìn 15, camera 13, hiệu chỉnh 11, Serial 9, chương trình chính 8, success 7, độ bền 6, khớp mô hình 5, màn hình 4, đầu–cuối 2. Có bắt buộc dashboard IoT không? [...điền theo yêu cầu đề bài]; nếu có, nhóm sẽ thêm MQTT từ gói JSON hiện có.

Nguồn: 05_SO_LIEU_VA_NGUON.md mục 4, 6, 7, 8, 11, 13; lệnh .venv/bin/python -m pytest -q (109 passed, 03/11/2026).
""")


# ==============================================================================
# Slide 14: Hạn chế và việc tiếp theo
# ==============================================================================
def slide_14(prs):
    s = new_slide(prs)
    header(s, "09 · Hướng phát triển", "Hạn chế hiện tại và việc tiếp theo")
    box(s, 0.6, 1.72, 5.95, 4.15, fill=CARD, edge=AMBER, edge_w=1.0)
    card_title(s, 0.85, 1.88, 5.5, "Hạn chế", AMBER)
    bullets(s, 0.85, 2.32, 5.5, 3.5, [
        "Vòng hở: XONG dựa trên góc lệnh, MG996R không báo vị trí thật",
        "Hiệu chỉnh gắn với một tờ giấy và một chỗ đặt robot",
        "Tay kẹp hai ngón phi tuyến, chưa giữ chắc cốc thon",
        "YOLO bản COCO chưa huấn luyện lại, hay gọi nhầm",
        "Chưa có tỉ lệ thành công, chưa đo nhiệt độ servo",
    ], 16, after=13)
    box(s, 6.78, 1.72, 5.95, 4.15, fill=CARD, edge=GREEN, edge_w=1.0)
    card_title(s, 7.03, 1.88, 5.5, "Việc tiếp theo", GREEN)
    steps(s, 7.03, 2.32, 5.5, [
        "Chạy bản mới trên cánh tay thật, đếm số lần XONG",
        "Dán ma sát lên hai ngón hoặc dùng vật thân thẳng, rồi mới tính kẹp vào success",
        "Hiệu chỉnh lại cho tờ giấy mới bằng arm_fit.py",
        "Đo đầu kẹp bằng camera để có vòng kín, thay vì tin góc lệnh",
        "Dashboard IoT (MQTT) từ gói JSON sẵn có, nếu đề bài yêu cầu",
    ], 15, dot_color=GREEN, d=0.34, gap=0.17)
    box(s, 0.6, 6.12, 12.13, 0.76, fill=BG2, edge=None, radius=0.06)
    text(s, 0.85, 6.12, 2.6, 0.76, "HAI LỖI TÍCH HỢP ĐÃ SỬA", 11.5, AMBER, True, anchor=MIDDLE, spc=40)
    bullets(s, 3.55, 6.19, 9.0, 0.66, [
        "Thứ tự camera trên macOS đổi giữa các lần chạy → tìm camera theo tên",
        "Arduino Uno tự reset khi cổng USB bị mở lại → giữ một kết nối duy nhất",
    ], 12.5, after=2, indent=0.2)
    footer(s, 14)
    notes(s, """
Từ đó nhóm thấy năm hạn chế. Lớn nhất là vòng hở: chữ XONG dựa trên góc Arduino đã ra lệnh, vì MG996R không báo vị trí thật. Hiệu chỉnh gắn với một tờ giấy và một chỗ đặt robot. Tay kẹp chưa giữ chắc cốc thon. YOLO bản COCO hay gọi nhầm. Và chưa có tỉ lệ thành công, chưa đo nhiệt độ servo.

Việc tiếp theo, theo thứ tự: chạy bản mới trên cánh tay thật và đếm số lần XONG; dán ma sát lên hai ngón hoặc dùng vật thân thẳng, rồi mới tính kẹp vào success; hiệu chỉnh lại cho tờ giấy mới; đo đầu kẹp bằng camera để có vòng kín; và thêm dashboard IoT qua MQTT nếu đề bài yêu cầu.

Dải dưới là hai lỗi tích hợp khó thấy nhóm đã sửa: thứ tự camera trên macOS đổi giữa các lần chạy, nên nhóm tìm camera theo tên; và Arduino Uno tự reset mỗi khi cổng USB bị mở lại, nên chương trình giữ một kết nối duy nhất và báo khi Arduino vừa reset.

Nếu được hỏi: chương trình phát hiện Arduino reset thế nào? Gói JSON có thời gian chạy t; t quay về gần không là Arduino vừa khởi động lại, màn hình báo ARDUINO VUA RESET. Vì sao camera đổi thứ tự? OpenCV đánh số camera theo uniqueID, còn danh sách của hệ điều hành xếp camera dùng gần nhất lên đầu. đo đầu kẹp bằng camera thế nào? Ví dụ dán mã ArUco lên càng kẹp và dùng chính homography của tờ giấy; đây là hướng đề xuất, chưa làm. Có làm tự động không? Về kỹ thuật là gửi phím theo Plan; nhóm chỉ nên làm lại khi đo được độ lệch còn lại.

Nguồn: 05_SO_LIEU_VA_NGUON.md mục 4, 6, 8, 9, 10, 13; cameras.py:4-12,75-115; control.py (ArduinoSerialLink: mở lại cổng, phát hiện reset); README.md mục 5 và 6.
""")


# ==============================================================================
# Slide 15: Tóm lại + hỏi đáp
# ==============================================================================
def slide_15(prs):
    s = new_slide(prs)
    text(s, 0.6, 0.62, 12.1, 0.3, "TÓM LẠI", 13, AMBER, True, spc=120)
    box(s, 0.6, 0.92, 0.8, 0.05, fill=AMBER, edge=None, shape=MSO_SHAPE.RECTANGLE)
    for i, (st, col) in enumerate([("Hai camera biến tờ A4 thành thước đo bằng cm.", WHITE),
                                   ("Nhóm 1 biến vị trí vật thành phím cần bấm.", AMBER),
                                   ("Nhóm 2 báo ba servo đã tới góc gợi ý chưa.", GREEN)]):
        y = 1.3 + i * 0.95
        dot(s, 0.6, y + 0.08, i + 1, col, d=0.5, size=18)
        text(s, 1.35, y, 11.3, 0.7, st, 30, WHITE, True, anchor=MIDDLE)
    for i, (k, v) in enumerate([("Mã nguồn", "github.com/DuongNAD/Project_IoT"), ("Video demo", "[...]")]):
        x = 0.6 + i * 6.15
        box(s, x, 4.3, 5.98, 0.75, fill=CARD)
        text(s, x + 0.25, 4.3, 1.6, 0.75, k, 13, MUTED, True, anchor=MIDDLE)
        text(s, x + 1.85, 4.3, 4.0, 0.75, v, 16, WHITE, True, anchor=MIDDLE)
    box(s, 0.6, 5.35, 12.13, 1.45, fill=CARD, edge=AMBER, edge_w=1.5)
    text(s, 0.6, 5.5, 12.13, 0.65, "Nhóm em cảm ơn thầy cô và các bạn đã lắng nghe!", 28, AMBER, True, align=CENTER)
    text(s, 0.6, 6.2, 12.13, 0.4, "HỎI ĐÁP", 15, MUTED, True, align=CENTER, spc=200)
    footer(s, 15)
    notes(s, """
Tóm lại trong ba câu. Hai camera biến tờ giấy A4 thành thước đo bằng xăng-ti-mét. Nhóm một biến vị trí vật thành phím cần bấm. Và nhóm hai báo ba servo đã tới góc gợi ý chưa.

Nhóm không cho rằng hệ thống đã hoàn hảo: những điều ở slide mười ba là thật. Nhưng nhóm hiểu từng phần, mã đủ ngắn để giải thích trong một phút, và có thể sửa bất kỳ phần nào ngay tại đây. Mã nguồn ở GitHub theo đường dẫn trên slide.

Nếu thầy cô muốn, nhóm demo trực tiếp: [...điền kịch bản demo 2–3 phút].

Nhóm em cảm ơn thầy cô và các bạn, và xin nhận câu hỏi.

Nếu được hỏi: việc nào làm trước? Chạy bản mới trên cánh tay thật để có số lần XONG đầu tiên, vì đó là chỗ còn thiếu bằng chứng nhất.

Nguồn: README.md; 05_SO_LIEU_VA_NGUON.md mục 4 đến 8.
""")


# ==============================================================================
def build(out_path=OUT_PPTX):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    for make in (slide_01, slide_02, slide_03, slide_04, slide_05, slide_06, slide_07, slide_08,
                 slide_09, slide_10, slide_11, slide_12, slide_13, slide_14, slide_15):
        make(prs)
    assert len(prs.slides) == TOTAL
    props = prs.core_properties  # Mẫu mặc định của python-pptx ghi người sửa "Steve Canny", ngày tạo 2013
    props.title = "Hệ thống hỗ trợ gắp vật cho cánh tay robot 4 bậc tự do bằng thị giác máy tính"
    props.subject = "Đồ án IoT: hai camera chỉ bấm phím nào, mấy lần; success kiểm ba góc servo"
    props.last_modified_by = ""
    props.created = props.modified = datetime.now().replace(microsecond=0)
    prs.save(out_path)
    missing = sorted({n for n in REQUIRED_IMAGES if not os.path.exists(os.path.join(REAL_DIR, n))})
    print(f"Đã lưu {out_path} ({len(prs.slides)} slide)")
    if missing:
        print(f"⚠️ Thiếu {len(missing)} ảnh trong {REAL_DIR} (slide hiện khung '[Ảnh: ...]'): {', '.join(missing)}")
    return out_path


REQUIRED_IMAGES = [
    "demo_06_grip_side.jpg", "demo_06_grip_top.jpg", "demo_07_carry_side.jpg", "demo_07_carry_top.jpg",
    "demo_08_place_side.jpg", "demo_08_place_top.jpg", "hw_overview_top.jpg", "hw_overview_side.jpg",
    "hw_electronics.jpg", "hw_arm_gripper.jpg", "sw_annot_top.jpg", "sw_annot_side.jpg", "ui_guide_cameras.png",
    "ui_screen_before.png", "ui_screen_done.png", "calib_before_after_side.jpg",
]

if __name__ == "__main__":
    build()
