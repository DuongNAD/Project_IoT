#!/usr/bin/env python3
"""
Dựng bộ slide thuyết trình (tiếng Việt, 16:9) cho mã hiện tại, theo phong cách slide Gamota (06_PHONG_CACH.md):
nền trắng sữa ấm, chữ nâu than, nhấn xanh teal (code, bằng chứng) và đất nung (phần cứng, điều chưa kiểm chứng), thẻ phẳng.
camera -> vision.py -> control.py (khối điều khiển: bấm phím gì) -> success.py (khối success: đã tới chưa) -> screen.py.
Nhóm 4 người, 4 phần theo đường đi của dữ liệu, mỗi phần mở bằng một slide ngăn:
01 linh kiện (danh sách, giới thiệu, sơ đồ mạch) -> 02 computer vision -> 03 code điều khiển (lưu đồ, code firmware, IK) -> 04 success.
Thứ tự slide nằm ở ORDER (cuối tệp); tên người ở TEAM (đầu tệp).

    python3 slides/build_slides.py        ->  slides/Project_IoT_ThuyetTrinh.pptx
    python3 slides/export_pdf.py          ->  slides/Project_IoT_ThuyetTrinh.pdf   (LibreOffice, hoặc PowerPoint trên Windows)
    python3 slides/render_previews.py     ->  slides/preview/slide_XX.png
    python3 slides/verify_slides.py       ->  kiểm số trang, ghi chú, số trang, chú thích "mô phỏng", tính năng đã bỏ

Mọi con số lấy từ slides/05_SO_LIEU_VA_NGUON.md (kiểm lại bằng slides/tools/check_facts.py sau mỗi lần sửa mã); thông số
linh kiện (Arduino Uno R3, PCA9685, MG996R) theo datasheet. Ảnh thật nằm trong slides/assets/real/; thiếu ảnh nào thì slide
hiện khung "[Ảnh: ...]" thay vào. Cần: python-pptx, Pillow. Phông Arial / Courier New có sẵn trên macOS lẫn Windows.
Mở được bằng PowerPoint, Keynote, LibreOffice (Keynote khắt khe hơn: xem line() và add_notes_master_id()).
"""

import math
import os
import re
import sys
import zipfile
from datetime import datetime

from lxml import etree
from PIL import Image, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

if sys.platform == "win32":  # Terminal Windows (cp1252) không in được tiếng Việt
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

SLIDES_DIR = os.path.dirname(os.path.abspath(__file__))
REAL_DIR = os.path.join(SLIDES_DIR, "assets", "real")
OUT_PPTX = os.path.join(SLIDES_DIR, "Project_IoT_ThuyetTrinh.pptx")
W, M = 13.333, 0.8   # Khổ ngang và lề (inch)
CW = W - 2 * M       # Bề rộng nội dung

# Nhóm 4 người: ĐIỀN TÊN THẬT VÀO ĐÂY. Bìa, slide nhóm, nhãn người nói ở góc trên phải và ghi chú đều lấy từ bảng này.
TEAM = {
    "hw": ("[Tên A]", "Linh kiện"),
    "cv": ("[Tên B]", "Computer vision"),
    "ctrl": ("[Tên C]", "Code điều khiển"),
    "succ": ("[Tên D]", "Success"),
}

# ==============================================================================
# Màu: bảng màu slide Gamota. Teal = code tất định / bằng chứng đã có; đất nung = phần cứng, rủi ro, chưa kiểm chứng;
# chàm = YOLO11 (tùy chọn); xám ấm = trung tính
# ==============================================================================
BG = RGBColor(0xFB, 0xF8, 0xF1)        # nền
BG2 = RGBColor(0xF3, 0xED, 0xE1)       # nền xen kẽ, panel trung tính
CARD = RGBColor(0xFF, 0xFD, 0xF8)      # thẻ, khung ảnh
INK = RGBColor(0x2B, 0x25, 0x20)       # chữ chính
TEXT2 = RGBColor(0x62, 0x59, 0x4F)     # chữ mô tả
MUTED = RGBColor(0x87, 0x7D, 0x72)     # chú thích, số trang
LINE = RGBColor(0xE2, 0xD9, 0xC8)      # đường kẻ mảnh
TEAL, TEAL_SOFT = RGBColor(0x2F, 0x6A, 0x56), RGBColor(0xE4, 0xEC, 0xDF)
ORANGE, ORANGE_SOFT = RGBColor(0xA6, 0x4B, 0x24), RGBColor(0xF5, 0xE3, 0xD3)
INDIGO, INDIGO_SOFT = RGBColor(0x5C, 0x5A, 0x8E), RGBColor(0xEA, 0xE6, 0xEF)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
STATEMENT = RGBColor(0xF1, 0xE7, 0xD3)  # nền slide ngăn phần

FONT = "Arial"
MONO = "Courier New"
LEFT, CENTER, RIGHT = PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.RIGHT
TOP, MIDDLE, BOTTOM = MSO_ANCHOR.TOP, MSO_ANCHOR.MIDDLE, MSO_ANCHOR.BOTTOM
RECT, ROUND, OVAL = MSO_SHAPE.RECTANGLE, MSO_SHAPE.ROUNDED_RECTANGLE, MSO_SHAPE.OVAL


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
# Không ngắt dòng giữa số và đơn vị ("8,5 mm"), quanh dấu nhân ("S × 15"), sau dấu ≈ và trong "109 / 109"
NO_BREAK = [(re.compile(r"(\d)\s+(mm|cm|ms|Hz|V|giây|phút|°)(?!\w)"), "\\1\u00a0\\2"),
            (re.compile(r"\s+×\s+"), "\u00a0×\u00a0"),
            (re.compile(r"\s+≈"), "\u00a0≈"),
            (re.compile(r"≈\s+"), "≈\u00a0"),
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
    lines = 0
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


def name(key):
    return TEAM[key][0]


def presenter(key):
    return f"{TEAM[key][0]} · {TEAM[key][1]}"


# ==============================================================================
# Hàm vẽ nhỏ (đơn vị: inch, cỡ chữ: point)
# ==============================================================================
def new_slide(prs, alt=False, bg=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Bố cục trống
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = bg or (BG2 if alt else BG)
    return slide


def text(slide, x, y, w, h, paras, size=18, color=INK, bold=False, font=FONT, align=LEFT, anchor=TOP,
         spacing=1.1, after=0, spc=None):
    """
    Hộp chữ không tự co. paras: chuỗi, hoặc danh sách đoạn; mỗi đoạn là chuỗi hoặc danh sách run,
    mỗi run là chuỗi hoặc (chuỗi, {"color", "bold", "size", "font", "spc"}).
    """
    box_ = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box_.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    fill_paragraphs(tf, paras, size, color, bold, font, align, spacing, after, spc)
    return box_


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


def label(slide, x, y, w, s, color=TEXT2, size=11, align=LEFT):
    """Nhãn hoa nhỏ, giãn chữ, như nhãn trên slide Gamota."""
    return text(slide, x, y, w, 0.3, s.upper(), size, color, True, align=align, spc=200)


def bullets(slide, x, y, w, h, items, size=16, color=INK, mark="•", mark_color=TEAL, after=8, indent=0.26, spacing=1.08):
    """Danh sách gạch đầu dòng thụt treo (dòng thứ hai thẳng hàng với chữ, không thẳng hàng với dấu)."""
    tb = text(slide, x, y, w, h, items, size, color, spacing=spacing, after=after)
    for p in tb.text_frame.paragraphs:
        pPr = p._p.get_or_add_pPr()
        pPr.set("marL", str(int(Inches(indent))))
        pPr.set("indent", str(-int(Inches(indent))))
        clr = etree.SubElement(pPr, qn("a:buClr"))
        etree.SubElement(clr, qn("a:srgbClr")).set("val", str(mark_color))
        etree.SubElement(pPr, qn("a:buFont")).set("typeface", FONT)
        etree.SubElement(pPr, qn("a:buChar")).set("char", mark)
    return tb


def steps(slide, x, y, w, items, size=15, color=INK, dot_color=TEAL, d=0.36, gap=0.14, fg=WHITE, spacing=1.05):
    """Danh sách đánh số; mỗi mục cao đúng theo số dòng đo bằng phông Arial. Trả về y ngay dưới mục cuối."""
    tx, tw = x + d + 0.16, w - d - 0.16
    line_h = size * 1.2 * spacing / 72
    for i, it in enumerate(items):
        h = n_lines(plain(it), size, tw - 0.05) * line_h
        dot(slide, x, y + (line_h - d) / 2, i + 1, dot_color, d=d, size=max(11, size - 3), fg=fg)
        text(slide, tx, y, tw, h + 0.04, [it] if isinstance(it, list) else it, size, color, spacing=spacing)
        y += max(h, d) + gap
    return y


def box(slide, x, y, w, h, fill=CARD, edge=None, edge_w=0.75, radius=0.06, shape=RECT):
    shp = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if shape == ROUND:
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
    style = shp._element.find(qn("p:style"))  # Kiểu mặc định của python-pptx kèm bóng đổ theo theme: bỏ hẳn cho phẳng
    if style is not None:
        shp._element.remove(style)
    return shp


def label_in(shp, paras, size=14, color=INK, bold=False, align=CENTER, anchor=MIDDLE, font=FONT, margin=0.04, spc=None):
    """Chữ nằm trong một hình (phím, chip, chấm số)."""
    tf = shp.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left = tf.margin_right = Inches(margin)
    tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    fill_paragraphs(tf, paras, size, color, bold, font, align, spacing=1.0, spc=spc)
    return shp


def chip_w(s, size=10.5):
    return text_w(s, size, True) + len(s) * 1.0 / 72 + 0.3  # chữ + giãn chữ 1 pt mỗi ký tự + đệm


def chip(slide, x, y, s, color=TEAL, soft=TEAL_SOFT, size=10.5, h=0.34, w=None):
    """Nhãn chữ nhật nền nhạt, chữ đậm cùng màu (như nhãn ĐẠT / CHƯA ĐẠT của slide Gamota). Trả về bề rộng."""
    w = w or chip_w(s, size)
    label_in(box(slide, x, y, w, h, fill=soft), s, size, color, True, margin=0.06, spc=100)
    return w


def keycap(slide, x, y, letter, w=0.44, h=0.42, size=16):
    """Phím bàn phím: nền nâu than, chữ trắng sữa."""
    return label_in(box(slide, x, y, w, h, fill=INK, radius=0.06, shape=ROUND), letter, size, BG, True, margin=0.0)


def dot(slide, x, y, n, color=TEAL, d=0.42, size=15, fg=WHITE):
    """Chấm tròn đánh số."""
    return label_in(box(slide, x, y, d, d, fill=color, shape=OVAL), str(n), size, fg, True, margin=0.0)


def line(slide, x1, y1, x2, y2, color=MUTED, width=1.5, head=False, dash=False):
    """
    Đoạn thẳng từ (x1, y1) tới (x2, y2), head=True: có mũi tên ở cuối. Vẽ bằng hình chữ nhật mảnh xoay theo hướng
    (nét đứt: nhiều đoạn ngắn) và tam giác, không dùng connector <p:cxnSp> (Keynote khắt khe với connector của python-pptx).
    """
    thick = width / 72
    length = math.hypot(x2 - x1, y2 - y1)
    if length < 1e-6:
        return
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
    head_len = max(0.13, 3.2 * thick) if head else 0.0
    body = max(length - head_len * 0.9, 0.0)
    pieces = [(0.0, body)] if not dash else [(a, min(a + 0.09, body)) for a in frange(0.0, body, 0.15)]
    for a, b in pieces:
        mid = (a + b) / 2
        cx, cy = x1 + ux * mid, y1 + uy * mid
        if abs(uy) > 0.999:  # Đoạn dọc: hình chữ nhật đứng, khỏi xoay (khung chưa xoay không thò ra ngoài slide)
            box(slide, cx - thick / 2, cy - (b - a) / 2, thick, b - a, fill=color)
        else:
            bar = box(slide, cx - (b - a) / 2, cy - thick / 2, b - a, thick, fill=color)
            if abs(ux) < 0.999:
                bar.rotation = angle
    if head:
        cx, cy = x1 + ux * (length - head_len / 2), y1 + uy * (length - head_len / 2)
        tri = box(slide, cx - head_len * 0.45, cy - head_len / 2, head_len * 0.9, head_len, fill=color,
                  shape=MSO_SHAPE.ISOSCELES_TRIANGLE)
        tri.rotation = angle + 90  # Tam giác gốc chĩa lên trên; xoay theo chiều kim đồng hồ cho chĩa theo hướng đoạn thẳng


def frange(start, stop, step):
    while start < stop:
        yield start
        start += step


def rule(slide, x, y, w, color=LINE):
    """Đường kẻ ngang mảnh 0,75 pt."""
    box(slide, x, y, w, 0.75 / 72, fill=color)


def image(slide, img, x, y, w, h=None, mode="cover", focus=(0.5, 0.5), frame=True):
    """
    Ảnh trong khung w x h. mode="cover": cắt bớt cho đầy khung, giữ tỉ lệ (focus = điểm giữ lại, 0..1);
    h=None: giữ nguyên tỉ lệ ảnh. frame=True: thẻ ngà viền mảnh bao quanh (đệm 0,06 in), như slide Gamota.
    Thiếu tệp thì vẽ khung "[Ảnh: tên tệp]" để vẫn dựng được slide.
    """
    path = img if os.path.isabs(img) else os.path.join(REAL_DIR, img)
    if h is None:
        if os.path.exists(path):
            iw, ih = Image.open(path).size
            h = w * ih / iw
        else:
            h = w * 9 / 16
    if frame:
        box(slide, x - 0.06, y - 0.06, w + 0.12, h + 0.12, fill=CARD, edge=LINE)
    if not os.path.exists(path):
        label_in(box(slide, x, y, w, h, fill=BG2, edge=MUTED), f"[Ảnh: {os.path.basename(img)}]", 13, MUTED)
        return h
    iw, ih = Image.open(path).size
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
    return h


def header(slide, eyebrow, title, who=None):
    """Nhãn phần (teal) + tiêu đề 30 pt (tự thu nhỏ tới 24 pt cho vừa một dòng) + tên người nói ở góc trên phải."""
    label(slide, M, 0.6, 7.6, eyebrow, TEAL)
    size = 30
    while size > 24 and text_w(title, size, True) > CW:
        size -= 1
    text(slide, M, 0.92, CW, 0.8, title, size, INK, True)
    if who:
        text(slide, 8.6, 0.6, W - M - 8.6, 0.3, presenter(who), 10.5, MUTED, align=RIGHT)


def footer(slide, n):
    text(slide, W - M - 0.8, 6.9, 0.8, 0.3, str(n), 10, MUTED, align=RIGHT)


def notes(slide, s):
    for key, (person, _role) in TEAM.items():
        s = s.replace("{" + key + "}", person)
    slide.notes_slide.notes_text_frame.text = s.strip()


def caption(slide, x, y, w, s, size=11, h=0.45, color=MUTED, align=LEFT):
    return text(slide, x, y, w, h, s, size, color, align=align, spacing=1.05)


# ==============================================================================
# Thứ tự slide và 4 phần (mỗi người một phần). num("ik") = số trang của slide "ik", dùng cho chữ "xem slide ..."
# ==============================================================================
SECTIONS = {  # phần -> (số phần, tên phần, các slide phần đó trình bày sau slide ngăn)
    "hw": ("01", "Linh kiện", ["parts", "comp1", "comp2", "circuit", "heat"]),
    "cv": ("02", "Computer vision", ["a4", "objects"]),
    "ctrl": ("03", "Code điều khiển", ["flow", "fwcode", "ik", "screen", "calib"]),
    "succ": ("04", "Success", ["success", "trial", "results", "limits"]),
}
TITLES = {
    "parts": "Danh sách linh kiện", "comp1": "Arduino Uno R3 và PCA9685", "comp2": "Servo, nguồn, HC-05, camera",
    "circuit": "Sơ đồ mạch", "heat": "Sự cố: servo kẹp nóng", "a4": "Tờ A4 thành thước đo", "objects": "Tìm vật bằng màu",
    "flow": "Lưu đồ thuật toán", "fwcode": "Code firmware", "ik": "Động học ngược", "screen": "Màn hình lệnh bấm phím",
    "calib": "Sự cố: mô hình lệch, hiệu chỉnh", "success": "Luật success", "trial": "Thử trên cánh tay thật",
    "results": "Kết quả", "limits": "Hạn chế, việc tiếp theo",
}
SLOT_BOXES = {}  # Ô "Slide a–b · ≈ N phút" trên slide nhóm, điền sau khi dựng xong (cần số trang và độ dài lời nói)


def num(key):
    return next(i for i, (k, _f, _o) in enumerate(ORDER, 1) if k == key)


# ==============================================================================
# Bìa
# ==============================================================================
def slide_cover(prs, n):
    s = new_slide(prs)
    box(s, 6.9, 0, W - 6.9, 7.5, fill=BG2)
    image(s, "demo_06_grip_side.jpg", 7.35, 0.62, 5.3, 2.98)
    image(s, "demo_06_grip_top.jpg", 7.35, 3.88, 5.3, 2.98)
    caption(s, 7.35, 7.0, 5.3, "Ảnh thật từ hai camera của hệ thống · 02/11/2026 20:32:52 · người bấm phím", 10, 0.3)
    label(s, M, 1.0, 5.8, "Đồ án IoT · [Môn học] · [Ngày báo cáo]", TEAL)
    text(s, M, 1.42, 5.8, 2.0, "Hệ thống hỗ trợ gắp vật cho cánh tay robot 4 bậc tự do bằng thị giác máy tính",
         30, INK, True, spacing=1.05)
    text(s, M, 3.5, 5.6, 1.0, "Hai camera chỉ cho người điều khiển bấm phím nào, mấy lần; rồi kiểm tra ba servo đã tới góc gợi ý chưa.",
         16, TEXT2, spacing=1.15)
    label(s, M, 4.82, 5.8, "Nhóm thực hiện", MUTED, 10)
    for i, key in enumerate(("hw", "cv", "ctrl", "succ")):
        x, y = M + (i % 2) * 2.95, 5.18 + (i // 2) * 0.66
        text(s, x, y, 2.85, 0.6, [[(name(key), {"bold": True, "size": 14})],
                                  [(TEAM[key][1], {"color": TEXT2, "size": 11})]], 14, INK, spacing=1.05)
    text(s, M, 6.62, 5.8, 0.3, "Giảng viên hướng dẫn: [...] · Lớp: [...]", 11, MUTED)
    notes(s, """
Em chào thầy cô và các bạn. Nhóm em gồm bốn người xin trình bày đề tài: hệ thống hỗ trợ gắp vật cho cánh tay robot bốn bậc tự do bằng thị giác máy tính. Nói ngắn gọn: hai camera nhìn tờ giấy và vật, chương trình cho người điều khiển biết phải bấm phím nào, bấm mấy lần, rồi kiểm tra ba servo đã tới góc gợi ý chưa.

Hai ảnh bên phải là ảnh thật từ hai camera của hệ thống, lúc cánh tay đang kẹp cốc do người bấm phím, không phải ảnh dựng.

Nếu được hỏi: vì sao chọn đề tài này? [...điền lý do của nhóm].

Nguồn: ảnh demo_06_grip_side, demo_06_grip_top (khung cắt từ video buổi thử 02/11/2026, 20:32:52).
""")


# ==============================================================================
# Nhóm 4 người và phân công
# ==============================================================================
def slide_team(prs, n):
    s = new_slide(prs, alt=True)
    header(s, "Nhóm 4 người", "Bốn người, bốn phần việc nối thành một hệ thống")
    members = [
        ("hw", ORANGE, "Nguồn 5–6 V, Arduino Uno, mạch PCA9685 và bốn servo MG996R; sơ đồ mạch, lắp cánh tay, đặt hai camera",
         "Arduino Uno · PCA9685 · MG996R"),
        ("cv", TEAL, "Tờ A4 bốn mã ArUco, đổi pixel sang cm, tìm vật bằng màu; cùng làm khối success", "vision.py · cameras.py"),
        ("ctrl", TEAL, "Firmware Arduino và code điều khiển cánh tay trên laptop: động học ngược, lệnh bấm phím, cổng USB, hiệu chỉnh",
         "robot_arm_4dof.ino · control.py"),
        ("succ", TEAL, "Luật success: ba servo tới góc gợi ý, giữ một giây; màn hình, kiểm thử; cùng làm computer vision",
         "success.py · screen.py · tests/"),
    ]
    cw, gap = (CW - 3 * 0.25) / 4, 0.25
    for i, (key, col, desc, files) in enumerate(members):
        x = M + i * (cw + gap)
        box(s, x, 1.95, cw, 3.85, fill=CARD)
        box(s, x, 1.95, cw, 0.07, fill=col)
        label(s, x + 0.22, 2.22, cw - 0.4, f"{SECTIONS[key][0]} · {TEAM[key][1]}", col, 10.5)
        text(s, x + 0.22, 2.55, cw - 0.4, 0.4, name(key), 18, INK, True)
        text(s, x + 0.22, 3.1, cw - 0.4, 1.6, desc, 12.5, TEXT2, spacing=1.12)
        text(s, x + 0.22, 4.78, cw - 0.4, 0.5, files, 10.5, TEAL if col == TEAL else ORANGE, font=MONO if col == TEAL else FONT,
             spacing=1.05)
        rule(s, x + 0.22, 5.3, cw - 0.44)
        SLOT_BOXES[key] = text(s, x + 0.22, 5.4, cw - 0.4, 0.3, "…", 11, MUTED)
    text(s, M, 6.15, CW, 0.4, [[("Thứ tự trình bày theo đường đi của dữ liệu:  ", {"color": TEXT2}),
                                ("phần cứng  →  camera nhìn  →  điều khiển  →  success", {"color": INK, "bold": True})]], 14)
    footer(s, n)
    notes(s, """
Nhóm em có bốn người, mỗi người một phần. {hw} phụ trách linh kiện: Arduino, mạch PCA9685, bốn servo và nguồn, sơ đồ mạch, lắp cánh tay và đặt hai camera. {cv} phụ trách computer vision: tờ giấy có mã ArUco, đổi pixel sang xăng-ti-mét và tìm vật. {ctrl} viết code điều khiển cánh tay: firmware Arduino và phần điều khiển trên laptop. {succ} phụ trách khối success: khi nào thì coi là đã tới; {cv} và {succ} cùng làm hai phần này.

Bài nói chia đúng bốn phần theo đường đi của dữ liệu trong hệ thống: phần cứng, rồi camera nhìn, rồi điều khiển, rồi success, nên mỗi người nói đúng phần mình làm. Mở đầu, {hw} trình bày bài toán, tổng quan hệ thống và phần linh kiện.

Nếu được hỏi: ai làm firmware? {ctrl}, cùng phần điều khiển trên laptop. Phần success và computer vision chia thế nào? Hai bạn làm chung; khi trình bày, {cv} nói phần nhìn, {succ} nói phần success.

Nguồn: README.md (các khối của mã); phân công do nhóm tự khai.
""")


# ==============================================================================
# Mở đầu · Bài toán
# ==============================================================================
def slide_problem(prs, n):
    s = new_slide(prs)
    header(s, "Mở đầu · Bài toán", "Ba câu hỏi trước mỗi lần gắp", "hw")
    label(s, M, 1.95, 7.2, "Trước mỗi lần gắp, người điều khiển phải tự trả lời")
    rows = [("Vật đang ở đâu trên bàn?", "02 · COMPUTER VISION"),
            ("Ba servo ở góc nào? Bấm phím nào, mấy lần?", "03 · ĐIỀU KHIỂN"),
            ("Đã tới đúng góc chưa?", "04 · SUCCESS")]
    for i, (q, who) in enumerate(rows):
        y = 2.45 + i * 1.12
        rule(s, M, y, 7.2)
        dot(s, M, y + 0.26, i + 1, d=0.42, size=15)
        text(s, M + 0.65, y + 0.24, 6.55, 0.45, q, 19, INK)
        chip(s, M + 0.65, y + 0.7, who)
    rule(s, M, 2.45 + 3 * 1.12, 7.2)
    box(s, 8.35, 1.95, W - M - 8.35, 3.86, fill=ORANGE_SOFT)
    label(s, 8.65, 2.2, 3.8, "Vì sao khó", ORANGE)
    text(s, 8.65, 2.65, 3.75, 1.9, ["Mỗi phím chỉ nhích 2°", "Mắt người khó ước lượng độ sâu",
                                   "Gợi ý chỉ đúng khi mô hình khớp cánh tay thật"], 16, INK, spacing=1.15, after=10)
    text(s, 8.65, 4.62, 3.75, 0.3, f"VÍ DỤ Ở SLIDE {num('ik')}", 10, ORANGE, True, spc=100)
    keycap(s, 8.65, 4.98, "D", 0.4, 0.38, 15)
    text(s, 9.1, 4.98, 0.5, 0.38, "× 8", 15, INK, True, anchor=MIDDLE)
    keycap(s, 9.7, 4.98, "S", 0.4, 0.38, 15)
    text(s, 10.15, 4.98, 0.65, 0.38, "× 16", 15, INK, True, anchor=MIDDLE)
    text(s, 10.85, 4.98, 1.6, 0.38, "= 24 lần bấm", 15, ORANGE, True, anchor=MIDDLE)
    text(s, M, 6.25, CW, 0.45, [[("Hệ thống trả lời ba câu này; ", {"color": INK}),
                                ("người vẫn là người bấm phím.", {"color": TEAL, "bold": True})]], 18)
    footer(s, n)
    notes(s, """
Em là {hw}, phụ trách linh kiện. Em xin mở đầu bằng bài toán.

Cánh tay của nhóm có bốn servo, điều khiển bằng bàn phím, mỗi lần bấm một phím thì một servo nhích hai độ. Trước mỗi lần gắp, người điều khiển phải tự trả lời ba câu hỏi: vật đang ở đâu trên bàn; ba servo phải ở góc nào, phải bấm phím nào, mấy lần; và đã tới đúng góc chưa.

Khó nhất là mắt người khó ước lượng độ sâu, mỗi phím lại chỉ nhích hai độ nên tới được vật có khi phải bấm hơn hai mươi lần, như ví dụ hai mươi bốn lần ở phần điều khiển. Và nếu mô hình hình học không khớp cánh tay thật thì gợi ý nào cũng lệch.

Hệ thống trả lời đúng ba câu hỏi này, mỗi câu bằng một khối riêng, cũng là phần việc của từng bạn: computer vision trả lời câu một, khối điều khiển trả lời câu hai, khối success trả lời câu ba. Người vẫn là người bấm phím.

Nếu được hỏi: vì sao không để chương trình tự điều khiển luôn? Vì mô hình hình học chỉ khớp cánh tay thật cỡ một xăng-ti-mét (phần hiệu chỉnh) và tay kẹp chưa giữ chắc cốc thon (phần success), nên nhóm chọn hướng hỗ trợ người điều khiển. Bản trước có chế độ tự gửi phím, nhóm đã bỏ để mã giải thích được trong một phút.

Nguồn: README.md mục 3; control.py; success.py.
""")


# ==============================================================================
# Mở đầu · Hệ thống (sơ đồ khối)
# ==============================================================================
def slide_system(prs, n):
    s = new_slide(prs)
    header(s, "Mở đầu · Sơ đồ khối", "Camera nhìn, khối điều khiển tính, khối success kiểm", "hw")
    gap, y, h = 0.5, 2.2, 1.5
    w = (CW - 4 * gap) / 5
    blocks = [
        ("CẢM BIẾN", "Hai camera", "OBSBOT nhìn xuống, MacBook nhìn ngang; tờ A4 có 4 mã ArUco", None, False),
        ("NHÌN · vision.py", "Tìm vật", "ArUco → homography; tách màu → (X, Y) cm", "02", False),
        ("ĐIỀU KHIỂN · control.py", "Điều khiển", "vị trí vật → góc 3 servo → phím cần bấm", "03", True),
        ("SUCCESS · success.py", "Success", "3 servo đã tới góc chưa? đếm số lần", "04", True),
        ("MÀN HÌNH · screen.py", "Lệnh + kết luận", "phím to, số lần; XONG hoặc CHƯA XONG", None, False),
    ]
    xs = [M + i * (w + gap) for i in range(5)]
    for x, (tag, title, desc, sec, strong) in zip(xs, blocks):
        box(s, x, y, w, h, fill=CARD, edge=TEAL if strong else LINE, edge_w=2.0 if strong else 0.75)
        if sec:
            dot(s, x + w - 0.36, y - 0.14, sec, d=0.34, size=10)
        text(s, x + 0.15, y + 0.14, w - 0.3, 0.25, tag, 10, TEAL if strong else MUTED, True)
        text(s, x + 0.15, y + 0.42, w - 0.3, 0.32, title, 15, INK, True)
        text(s, x + 0.15, y + 0.8, w - 0.3, 0.68, desc, 11.5, TEXT2, spacing=1.05)
    mid = y + h / 2
    for i, lab in enumerate(["ảnh", "(X, Y)", "Plan", "Result"]):
        x1, x2 = xs[i] + w + 0.05, xs[i + 1] - 0.05
        strong = lab == "Plan"
        line(s, x1, mid, x2, mid, TEAL if strong else MUTED, 3.0 if strong else 1.5, head=True)
        text(s, x1 - 0.25, mid - 0.38, x2 - x1 + 0.5, 0.28, lab, 12 if strong else 10.5, TEAL if strong else MUTED, strong,
             align=CENTER)
    lx, rx, top = xs[2] + w / 2, xs[4] + w / 2, 1.92
    line(s, rx, y, rx, top, ORANGE, 1.5, dash=True)
    line(s, rx, top, lx, top, ORANGE, 1.5, dash=True)
    line(s, lx, top, lx, y - 0.16, ORANGE, 1.5, head=True, dash=True)
    text(s, lx + 0.4, top - 0.29, rx - lx - 0.8, 0.27, "người nhìn màn hình rồi bấm phím", 11, ORANGE, align=CENTER)
    hy, hh = 4.35, 0.95
    hw = [("Arduino Uno", "nhận phím, gửi JSON"), ("PCA9685", "I²C 0x40 · xung 50 Hz"), ("4 servo MG996R", "đế · vai · khuỷu · kẹp")]
    for i, (t1, t2) in enumerate(hw):
        x = xs[2 + i]
        box(s, x, hy, w, hh, fill=ORANGE_SOFT)
        text(s, x + 0.15, hy + 0.14, w - 0.3, 0.3, t1, 14, INK, True)
        text(s, x + 0.15, hy + 0.5, w - 0.3, 0.35, t2, 11.5, TEXT2)
        if i < 2:
            line(s, x + w + 0.05, hy + hh / 2, xs[3 + i] - 0.05, hy + hh / 2, MUTED, 1.5, head=True)
    dot(s, xs[4] + w - 0.36, hy - 0.14, "01", ORANGE, d=0.34, size=10)
    cx = xs[2] + w / 2
    line(s, cx - 0.3, y + h + 0.04, cx - 0.3, hy - 0.04, TEAL, 1.75, head=True)
    line(s, cx + 0.3, hy - 0.04, cx + 0.3, y + h + 0.04, ORANGE, 1.75, head=True)
    text(s, xs[1], y + h + 0.17, cx - 0.42 - xs[1], 0.5, "phím · USB 9600 baud", 10.5, TEAL, align=RIGHT)
    text(s, cx + 0.43, y + h + 0.1, 2.4, 0.5, ["JSON ~5 gói/giây", "(góc servo đã ra lệnh)"], 10.5, ORANGE, spacing=1.0)
    box(s, M, hy, 4.45, hh, fill=TEAL_SOFT)
    label(s, M + 0.2, hy + 0.12, 4.1, "Chỉ một đối tượng nối hai khối", TEAL, 10)
    text(s, M + 0.2, hy + 0.42, 4.1, 0.55, "Plan = góc hiện tại, góc cần tới, lệnh bấm từng servo. Điều khiển tạo ra, success chỉ đọc.",
         12, INK, spacing=1.05)
    box(s, M, 5.62, CW, 1.0, fill=BG2)
    code = [("plan   = self.control.update(self.tracker.objects)", "# ĐIỀU KHIỂN: vật ở đâu -> góc cần tới -> bấm phím gì"),
            ("result = self.success.update(plan)", "# SUCCESS: đã tới chưa"),
            ("screen = build_screen(..., plan, result)", "# main.py:171-174, mỗi khung hình")]
    text(s, M + 0.25, 5.74, CW - 0.4, 0.85, [[(c.ljust(53), {}), (k, {"color": MUTED})] for c, k in code], 12.5, INK, font=MONO,
         spacing=1.12)
    footer(s, n)
    notes(s, """
Đây là sơ đồ khối của toàn hệ thống, đọc từ trái sang phải; số trên mỗi khối là phần việc của từng bạn.

Hai camera cùng quay tờ giấy A4: OBSBOT treo trên nhìn xuống để tính vị trí vật, camera MacBook đặt thấp phía trước để người điều khiển nhìn độ cao và độ sát của hai ngón kẹp. Khối nhìn, phần hai, dò bốn mã ArUco để đổi pixel sang xăng-ti-mét rồi tách màu để ra vị trí X, Y của vật.

Hai khối ở giữa là điểm chính của thiết kế. Khối điều khiển, phần ba, biết vật ở đâu thì tính ba servo cần ở góc nào và lập danh sách phím cần bấm. Khối success, phần bốn, chỉ trả lời một câu: ba servo đã tới góc đó chưa. Hai khối chỉ nói chuyện qua một đối tượng tên là Plan, nên làm riêng và kiểm riêng được; ba dòng mã ở dưới là đúng những gì chương trình làm mỗi khung hình.

Người nhìn màn hình rồi bấm phím. Phím đi xuống Arduino qua cáp USB, chín nghìn sáu trăm baud; Arduino điều khiển bốn servo qua mạch PCA9685 và gửi ngược lên gói JSON chứa bốn góc servo, khoảng năm gói mỗi giây. Hàng phần cứng này là phần một, phần em trình bày tiếp theo.

Nếu được hỏi: chương trình có tự gửi phím không? Không, chỉ gửi khi người bấm. Vì sao trong code gọi là nhóm 1, nhóm 2? Đó là tên hai khối trong mã nguồn (control.py, success.py). Có Bluetooth không? Firmware có sẵn đường nhận phím từ module HC-05 ở chân D2, D3, nhưng chương trình trên laptop chỉ dùng cáp USB.

Nguồn: README.md (sơ đồ đầu trang, mục 1 và 3); main.py:171-174; robot_arm_4dof.ino:6,8,86,203-207; control.py (ArduinoSerialLink).
""")


# ==============================================================================
# Slide ngăn phần: số phần, tên phần, người nói, các slide của phần
# ==============================================================================
def slide_divider(prs, n, key):
    s = new_slide(prs, bg=STATEMENT)
    sec_no, sec_name, keys = SECTIONS[key]
    col = ORANGE if key == "hw" else TEAL
    label(s, M, 1.3, 6.0, f"Phần {sec_no} / 04", col)
    text(s, M, 1.62, 3.4, 1.7, sec_no, 110, col, True)
    text(s, M, 3.45, 6.6, 0.85, sec_name, 44, INK, True)
    text(s, M, 4.38, 6.6, 0.45, name(key), 22, TEXT2)
    box(s, 7.75, 1.3, W - M - 7.75, 4.55, fill=CARD)
    label(s, 8.05, 1.55, 4.3, "Phần này gồm", TEXT2, 10.5)
    for i, k in enumerate(keys):
        y = 2.0 + i * 0.68
        rule(s, 8.05, y, W - M - 8.35)
        text(s, 8.05, y + 0.16, 0.7, 0.4, str(num(k)), 16, col, True)
        text(s, 8.75, y + 0.16, W - M - 9.1, 0.4, TITLES[k], 16, INK)
    rule(s, 8.05, 2.0 + len(keys) * 0.68, W - M - 8.35)
    x = M
    for k, (no, nm, _ks) in SECTIONS.items():
        lab = f"{no}  {nm}"
        w = chip_w(lab, 10.5) + 0.2
        if k == key:
            chip(s, x, 6.25, lab, WHITE, col, size=10.5, w=w)
        else:
            chip(s, x, 6.25, lab, TEXT2, BG2, size=10.5, w=w)
        x += w + 0.12
    footer(s, n)
    intro = {
        "hw": "Sau phần tổng quan, em đi vào phần việc của mình: linh kiện. Em sẽ đi qua danh sách linh kiện, giới thiệu từng linh kiện chính, sơ đồ mạch, và một sự cố phần cứng nhóm đã gặp là servo kẹp bị nóng.",
        "cv": "Em là {cv}, phụ trách computer vision cùng {succ}. Phần của em trả lời câu hỏi đầu tiên: vật đang ở đâu trên bàn, tính bằng xăng-ti-mét. Em trình bày hai việc: biến tờ A4 thành thước đo bằng bốn mã ArUco, rồi tìm vật bằng màu.",
        "ctrl": "Em là {ctrl}, phụ trách code điều khiển cánh tay: firmware chạy trên Arduino và khối điều khiển chạy trên laptop. Em trình bày lưu đồ thuật toán, phần code chính của firmware, động học ngược, màn hình chỉ lệnh bấm phím, và sự cố mô hình lệch cùng cách hiệu chỉnh.",
        "succ": "Em là {succ}, phụ trách khối success cùng {cv}. Phần cuối gồm luật success, buổi thử trên cánh tay thật, những gì nhóm đã có và chưa kiểm chứng, rồi hạn chế và việc tiếp theo.",
    }[key]
    notes(s, intro + """

Nếu được hỏi: phần này nằm ở đâu trong mã nguồn? Xem tên tệp trên slide nhóm (slide 2).

Nguồn: phân công của nhóm; README.md (các khối của mã).
""")


# ==============================================================================
# 01 · Linh kiện · danh sách
# ==============================================================================
def slide_parts(prs, n):
    s = new_slide(prs)
    header(s, "01 · Linh kiện", "Danh sách linh kiện", "hw")
    rows = [
        ("Arduino Uno R3", "1", "Bộ não: nhận phím, điều khiển PCA9685, gửi góc servo về laptop"),
        ("Mạch PCA9685 (16 kênh PWM)", "1", "Tạo xung 50 Hz cho 4 servo, nhận lệnh qua I²C"),
        ("Servo MG996R", "4", "Đế, vai, khuỷu, kẹp"),
        ("Nguồn tổ ong 5–6 V", "1", "Nguồn riêng cho servo, không lấy từ cổng USB"),
        ("Module Bluetooth HC-05", "1", "Nhận phím không dây (tùy chọn)"),
        ("Khung cánh tay 4 bậc tự do, tay kẹp hai ngón", "1", "Phần cơ khí"),
        ("Camera OBSBOT Meet SE", "1", "Cam TRÊN: nhìn xuống tờ giấy"),
        ("Camera MacBook (có sẵn)", "1", "Cam NGANG: nhìn từ phía trước"),
        ("Tờ A4 in 4 mã ArUco", "1", "Thước đo bằng cm cho cả hai camera"),
        ("Laptop, cáp USB, dây cắm", "—", "Chạy chương trình Python, cấp nguồn cho Arduino qua USB"),
    ]
    cols = [(M, 0.45, "#"), (M + 0.45, 4.55, "LINH KIỆN"), (M + 5.0, 0.7, "SL"), (M + 5.7, CW - 5.7, "VAI TRÒ TRONG HỆ THỐNG")]
    for x, w, lab in cols:
        text(s, x, 1.98, w, 0.28, lab, 10, TEXT2, True, align=CENTER if lab == "SL" else LEFT, spc=150)
    rh = 0.425
    for i, (part, qty, role) in enumerate(rows):
        y = 2.32 + i * rh
        if i % 2 == 0:
            box(s, M, y, CW, rh, fill=BG2)
        text(s, M + 0.08, y, 0.4, rh, str(i + 1), 12.5, MUTED, True, anchor=MIDDLE)
        text(s, M + 0.45, y, 4.5, rh, part, 14, INK, True, anchor=MIDDLE)
        text(s, M + 5.0, y, 0.7, rh, qty, 14, ORANGE if qty == "4" else INK, True, align=CENTER, anchor=MIDDLE)
        text(s, M + 5.7, y, CW - 5.8, rh, role, 13, TEXT2, anchor=MIDDLE)
    footer(s, n)
    notes(s, """
Đây là danh sách linh kiện của hệ thống. Arduino Uno R3 là bộ não: nhận phím từ laptop, ra lệnh cho mạch PCA9685 và gửi góc servo ngược về laptop. Mạch PCA9685 tạo xung năm mươi héc cho bốn servo MG996R ở đế, vai, khuỷu và kẹp. Nguồn tổ ong năm đến sáu vôn chỉ nuôi servo. Module Bluetooth HC-05 cho phép gửi phím không dây nhưng không bắt buộc. Phần nhìn có camera OBSBOT treo trên, camera có sẵn của MacBook nhìn ngang, và tờ A4 in bốn mã ArUco làm thước đo. Laptop chạy chương trình Python và cấp nguồn cho Arduino qua cáp USB.

Nếu được hỏi: mua linh kiện ở đâu, giá bao nhiêu? [...điền nếu thầy cô hỏi]. Khung cánh tay bằng gì? [...điền].

Nguồn: README.md mục 1; robot_arm_4dof/robot_arm_4dof.ino:1-8,86-90; robot_arm_4dof/flash.sh:19 (arduino:avr:uno); cameras.py.
""")


# ==============================================================================
# 01 · Linh kiện · giới thiệu (1): ảnh mạch thật đánh số, Arduino Uno R3 và PCA9685
# ==============================================================================
HW_PHOTO_MARKS = [  # (số, x, y tương đối trong ảnh hw_electronics.jpg 800 x 678, tên)
    (1, 0.27, 0.65, "Arduino Uno R3"), (2, 0.27, 0.885, "PCA9685"), (3, 0.44, 0.69, "HC-05"),
    (4, 0.30, 0.25, "Nguồn tổ ong 5–6 V"), (5, 0.62, 0.45, "Servo MG996R (đế)"),
]


def slide_comp1(prs, n):
    s = new_slide(prs)
    header(s, "01 · Linh kiện", "Mạch điều khiển: Arduino Uno R3 và PCA9685", "hw")
    pw = 4.95
    ph = image(s, "hw_electronics.jpg", M, 1.98, pw, None, mode="fit")
    for k, fx, fy, _nm in HW_PHOTO_MARKS:
        dot(s, M + fx * pw - 0.19, 1.98 + fy * ph - 0.19, k, ORANGE, d=0.38, size=13)
    caption(s, M, 1.98 + ph + 0.12, pw, "Ảnh thật: " + " · ".join(f"({k}) {nm.split(' 5')[0]}" for k, _x, _y, nm in HW_PHOTO_MARKS),
            10, 0.5)
    rx, rw = 6.35, W - M - 6.35
    blocks = [
        (1, "Arduino Uno R3", "ATmega328P · 16 MHz · 14 chân số, 6 chân analog · chạy 5 V qua cổng USB",
         "Nhận phím (USB 9600 baud hoặc HC-05), đổi góc trong giới hạn, ra lệnh cho PCA9685 qua I²C, "
         "gửi JSON bốn góc servo mỗi 200 ms"),
        (2, "Mạch PCA9685", "16 kênh PWM 12 bit · giao tiếp I²C, địa chỉ 0x40 · tần số đặt 50 Hz",
         "Kênh 0–3 cho đế, vai, khuỷu, kẹp; góc 0–180° đổi thành xung 125–575 trên thang 4096; "
         "nguồn servo cắm vào cổng xanh V+"),
    ]
    y, line_h = 1.98, 13 * 1.2 * 1.08 / 72
    for k, nm, spec, role in blocks:
        h_spec = n_lines(spec, 13, rw - 0.55) * line_h
        h_role = n_lines(role, 13, rw - 0.55) * line_h
        rule(s, rx, y, rw)
        dot(s, rx, y + 0.18, k, ORANGE, d=0.36, size=13)
        text(s, rx + 0.5, y + 0.16, rw - 0.5, 0.38, nm, 18, INK, True)
        text(s, rx + 0.5, y + 0.62, rw - 0.5, 0.3, "THÔNG SỐ", 10, MUTED, True, spc=150)
        text(s, rx + 0.5, y + 0.88, rw - 0.5, h_spec + 0.05, spec, 13, TEXT2, spacing=1.08)
        yr = y + 0.88 + h_spec + 0.14
        text(s, rx + 0.5, yr, rw - 0.5, 0.3, "TRONG HỆ THỐNG", 10, TEAL, True, spc=150)
        text(s, rx + 0.5, yr + 0.26, rw - 0.5, h_role + 0.05, role, 13, INK, spacing=1.08)
        y = yr + 0.26 + h_role + 0.3
    footer(s, n)
    notes(s, """
Ảnh bên trái là mạch thật của nhóm, em đánh số từng linh kiện: một là Arduino Uno R3, hai là mạch PCA9685, ba là module HC-05, bốn là nguồn tổ ong, năm là servo MG996R ở đế cánh tay.

Arduino Uno R3 dùng vi điều khiển ATmega328P, chạy mười sáu mê-ga-héc, có mười bốn chân số và sáu chân analog, lấy điện năm vôn từ cổng USB. Trong hệ thống, nó nhận phím từ laptop qua cáp USB ở chín nghìn sáu trăm baud hoặc từ module HC-05, đổi góc servo trong giới hạn, ra lệnh cho mạch PCA9685 qua chuẩn I²C, và cứ hai trăm mi-li-giây gửi lên laptop một gói JSON chứa bốn góc servo.

PCA9685 là mạch mười sáu kênh PWM mười hai bit, giao tiếp I²C ở địa chỉ 0x40; nhóm đặt tần số năm mươi héc cho servo. Kênh không tới ba nối với đế, vai, khuỷu và kẹp; góc từ không tới một trăm tám mươi độ được đổi thành độ rộng xung từ một trăm hai mươi lăm tới năm trăm bảy mươi lăm trên thang 4096. Nguồn của servo cắm vào cổng xanh V+ trên mạch này.

Nếu được hỏi: vì sao dùng PCA9685 thay vì cắm servo thẳng vào Arduino? Mạch lo việc tạo xung cho nhiều servo cùng lúc và có cổng nguồn riêng cho servo; Arduino chỉ cần gửi lệnh qua hai dây I²C.

Nguồn: robot_arm_4dof.ino:1-12,41-45,86-90 (Wire, Adafruit_PWMServoDriver 0x40, setPWMFreq 50, SERVOMIN 125, SERVOMAX 575); README.md mục 1; thông số Arduino Uno R3 theo trang sản phẩm của Arduino; ảnh hw_electronics.
""")


# ==============================================================================
# 01 · Linh kiện · giới thiệu (2): servo, nguồn, HC-05, camera
# ==============================================================================
def slide_comp2(prs, n):
    s = new_slide(prs, alt=True)
    header(s, "01 · Linh kiện", "Servo MG996R, nguồn riêng, HC-05 và hai camera", "hw")
    cards = [
        ("Servo MG996R × 4", "Bánh răng kim loại · quay 0–180° · xung 0,5–2,5 ms (datasheet)",
         "Đế, vai, khuỷu, kẹp; mỗi lần bấm nhích 2° (kẹp 5°). Không báo vị trí thật về, nên XONG dựa trên góc đã ra lệnh.", True),
        ("Nguồn tổ ong 5–6 V", "Nguồn xung chỉnh ra 5–6 V",
         "Chỉ nuôi 4 servo qua cổng xanh của PCA9685; servo kéo dòng lớn nên không lấy từ cổng USB. GND nối chung.", False),
        ("Module Bluetooth HC-05 (tùy chọn)", "Bluetooth SPP · UART 9600 baud",
         "Nối D2 (RX) và D3 (TX) của Arduino; firmware nhận phím từ HC-05 như từ USB. Chương trình trên laptop dùng cáp USB.", False),
        ("Hai camera 1920 × 1080", "OBSBOT Meet SE (cam TRÊN, treo nhìn xuống) · camera MacBook (cam NGANG)",
         "Cùng nhìn tờ A4 có 4 mã ArUco: cam TRÊN tính vị trí vật, cam NGANG cho người điều khiển nhìn độ cao.", False),
    ]
    cw, ch = (CW - 0.25) / 2, 2.27
    for i, (nm, spec, role, keys) in enumerate(cards):
        x, y = M + (i % 2) * (cw + 0.25), 1.95 + (i // 2) * (ch + 0.2)
        box(s, x, y, cw, ch, fill=CARD)
        box(s, x, y, 0.07, ch, fill=ORANGE)
        text(s, x + 0.3, y + 0.18, cw - 0.5, 0.36, nm, 17, INK, True)
        text(s, x + 0.3, y + 0.6, cw - 0.5, 0.5, spec, 12, TEXT2, spacing=1.06)
        text(s, x + 0.3, y + 1.15 if not keys else y + 1.05, cw - 0.5, 0.85, role, 12.5, INK, spacing=1.08)
        if keys:
            kx = x + 0.3
            for pair in ("A D", "W S", "I K", "J L"):
                for ch_ in pair.split():
                    keycap(s, kx, y + 1.78, ch_, 0.34, 0.32, 12)
                    kx += 0.39
                kx += 0.18
    footer(s, n)
    notes(s, """
Tiếp theo là các linh kiện còn lại. Bốn servo MG996R bánh răng kim loại, quay từ không tới một trăm tám mươi độ, nhận xung từ không phẩy năm tới hai phẩy năm mi-li-giây. Mỗi lần bấm phím, đế, vai và khuỷu nhích hai độ, kẹp nhích năm độ; tám phím ở hàng dưới là cặp phím của từng servo. Servo này không báo vị trí thật về, nên chữ XONG ở phần success dựa trên góc đã ra lệnh.

Nguồn tổ ong năm tới sáu vôn chỉ nuôi servo, cắm vào cổng xanh của PCA9685; bốn servo kéo dòng lớn nên nhóm không lấy điện từ cổng USB của laptop, và GND được nối chung.

HC-05 là module Bluetooth, nối chân D2, D3 của Arduino; firmware nhận phím từ nó như từ cáp USB, nhưng chương trình trên laptop dùng cáp USB, nên đây là phần tùy chọn.

Cuối cùng là hai camera 1920 nhân 1080: OBSBOT Meet SE treo trên nhìn xuống để tính vị trí vật, và camera của MacBook nhìn ngang để người điều khiển thấy độ cao của kẹp.

Nếu được hỏi: mô-men xoắn của MG996R bao nhiêu? Theo datasheet khoảng mười ki-lô-gam xăng-ti-mét ở sáu vôn; nhóm chưa đo. Vì sao không dùng servo có phản hồi vị trí? Nằm ngoài linh kiện nhóm có; đây là một hướng phát triển.

Nguồn: robot_arm_4dof.ino:5-6,13-21,86-87,121-152; README.md mục 1; cameras.py; datasheet MG996R (dải xung).
""")


# ==============================================================================
# 01 · Linh kiện · sơ đồ mạch
# ==============================================================================
def slide_circuit(prs, n):
    s = new_slide(prs)
    header(s, "01 · Linh kiện", "Sơ đồ mạch: Arduino, PCA9685, 4 servo và nguồn riêng", "hw")
    pins_y = [2.65, 3.0, 3.35, 3.7]

    def block(x, y, w, h, title, sub=None, fill=CARD, edge=INK):
        box(s, x, y, w, h, fill=fill, edge=edge, edge_w=1.25)
        text(s, x + 0.12, y + 0.08, w - 0.2, 0.3, title, 13, INK, True)
        if sub:
            text(s, x + 0.12, y + 0.38, w - 0.2, 0.3, sub, 10.5, TEXT2)

    # Laptop và camera
    block(M, 2.05, 1.75, 0.95, "Laptop", "MacBook · main.py")
    block(M, 3.8, 1.75, 0.95, "Cam TRÊN", "OBSBOT Meet SE")
    line(s, M + 0.87, 3.8, M + 0.87, 3.0, INK, 1.75, head=True)
    text(s, M + 0.95, 3.25, 0.8, 0.3, "USB", 10, TEXT2)
    caption(s, M, 4.82, 2.3, "Cam NGANG: camera có sẵn của MacBook", 10, 0.45)
    # Arduino
    ax, aw = 3.8, 2.25
    block(ax, 1.95, aw, 3.55, "Arduino Uno R3")
    ard_pins = [("5V", pins_y[0]), ("GND", pins_y[1]), ("A4 · SDA", pins_y[2]), ("A5 · SCL", pins_y[3]),
                ("D2 · RX", 4.45), ("D3 · TX", 4.85)]
    for lab, y in ard_pins:
        text(s, ax + 0.9, y - 0.14, aw - 1.0, 0.28, lab, 10.5, INK, True, align=RIGHT)
        box(s, ax + aw - 0.05, y - 0.05, 0.1, 0.1, fill=INK, shape=OVAL)
    text(s, ax + 0.1, 2.36, 0.8, 0.28, "USB", 10.5, INK, True)
    line(s, M + 1.75, 2.5, ax, 2.5, INK, 2.0, head=True)
    text(s, M + 1.8, 2.16, ax - M - 1.85, 0.3, "USB 9600 baud", 10, INK, True)
    text(s, M + 1.8, 2.58, ax - M - 1.85, 0.3, "phím ↓ JSON ↑", 10, TEXT2)
    # PCA9685
    px, pw_ = 7.15, 2.0
    block(px, 2.0, pw_, 2.05, "PCA9685", None)
    for lab, y in zip(("VCC", "GND", "SDA", "SCL"), pins_y):
        text(s, px + 0.12, y - 0.14, 0.8, 0.28, lab, 10.5, INK, True)
        box(s, px - 0.05, y - 0.05, 0.1, 0.1, fill=INK, shape=OVAL)
    for i, y in enumerate(pins_y):
        text(s, px + 0.9, y - 0.14, pw_ - 1.0, 0.28, f"kênh {i}", 10.5, INK, True, align=RIGHT)
        box(s, px + pw_ - 0.05, y - 0.05, 0.1, 0.1, fill=TEAL, shape=OVAL)
    wire = [(INK, 2.0), (MUTED, 2.0), (TEAL, 2.0), (TEAL, 2.0)]
    for (col, wd), y in zip(wire, pins_y):
        line(s, ax + aw + 0.05, y, px - 0.05, y, col, wd)
    text(s, ax + aw + 0.2, pins_y[2] - 0.33, 1.2, 0.25, "I²C", 10, TEAL, True)
    # 4 servo
    sx, sw = 10.35, W - M - 10.35
    text(s, sx, 2.12, sw, 0.28, "4 SERVO MG996R", 10, ORANGE, True, spc=150)
    for (lab, keys), y in zip((("Kênh 0 · Đế", "A/D"), ("Kênh 1 · Vai", "W/S"), ("Kênh 2 · Khuỷu", "I/K"), ("Kênh 3 · Kẹp", "J/L")),
                              pins_y):
        line(s, px + pw_ + 0.05, y, sx, y, TEAL, 2.0)
        box(s, sx, y - 0.16, sw, 0.32, fill=ORANGE_SOFT)
        text(s, sx + 0.1, y - 0.16, sw - 0.65, 0.32, lab, 10.5, INK, True, anchor=MIDDLE)
        text(s, sx + sw - 0.6, y - 0.16, 0.52, 0.32, keys, 10, TEXT2, align=RIGHT, anchor=MIDDLE)
    caption(s, sx, 3.95, sw, "mỗi servo 3 dây: xung, V+, GND", 10, 0.3)
    # Nguồn servo
    block(px, 4.75, pw_, 0.75, "Nguồn tổ ong", "5–6 V cho servo", fill=ORANGE_SOFT, edge=ORANGE)
    line(s, px + pw_ / 2, 4.75, px + pw_ / 2, 4.08, ORANGE, 3.0, head=True)
    text(s, px + pw_ / 2 + 0.12, 4.25, 2.0, 0.3, "V+ / GND · cổng xanh", 10, ORANGE, True)
    # HC-05
    block(px, 5.85, pw_, 0.75, "HC-05 (tùy chọn)", "TXD → D2 · RXD ← D3", fill=CARD, edge=INDIGO)
    for y_pin, x_turn, y_end, lab in ((4.45, 6.3, 6.07, "TXD → D2"), (4.85, 6.6, 6.38, "RXD ← D3")):
        line(s, ax + aw + 0.05, y_pin, x_turn, y_pin, INDIGO, 1.75)
        line(s, x_turn, y_pin, x_turn, y_end, INDIGO, 1.75)
        line(s, x_turn, y_end, px - 0.05, y_end, INDIGO, 1.75)
    # Chú giải
    legend = [(TEAL, "tín hiệu: I²C, xung servo"), (ORANGE, "nguồn servo 5–6 V"), (INK, "USB, 5 V logic"),
              (MUTED, "GND (nối chung)"), (INDIGO, "HC-05 (tùy chọn)")]
    for i, (col, lab) in enumerate(legend):
        y = 5.48 + i * 0.26
        box(s, M, y + 0.1, 0.3, 0.06, fill=col)
        text(s, M + 0.4, y, 2.5, 0.26, lab, 10, TEXT2)
    caption(s, 9.45, 5.85, W - M - 9.45, "Vẽ lại theo firmware (PCA9685 ở 0x40, HC-05 ở D2/D3) và README. "
            "Chân I²C của Arduino Uno là A4 (SDA), A5 (SCL).", 10, 0.75)
    footer(s, n)
    notes(s, """
Đây là sơ đồ đấu dây của hệ thống. Laptop nối Arduino bằng cáp USB: phím đi xuống, gói JSON đi lên, chín nghìn sáu trăm baud; cáp này cũng cấp nguồn cho Arduino. Arduino nối mạch PCA9685 bằng bốn dây: năm vôn, GND, và hai dây I²C, SDA ở chân A4, SCL ở chân A5.

PCA9685 xuất xung ở kênh không tới ba cho bốn servo: đế, vai, khuỷu và kẹp, mỗi servo ba dây gồm tín hiệu, V+ và GND. Nguồn tổ ong năm tới sáu vôn cấp vào cổng xanh V+ của PCA9685 và chỉ dùng cho servo. Module HC-05 có chân TXD nối D2 và RXD nối D3 của Arduino. Camera OBSBOT cắm vào laptop qua USB; camera ngang là camera có sẵn của MacBook. GND của Arduino, PCA9685 và nguồn servo nối chung.

Nếu được hỏi: vì sao A4 và A5? Đó là hai chân I²C, SDA và SCL, của Arduino Uno. HC-05 có dùng cầu chia áp cho chân RXD không? [...điền theo mạch thật]. Vì sao phải nối chung GND? Để tín hiệu xung từ PCA9685 và nguồn servo có chung mức tham chiếu.

Nguồn: robot_arm_4dof.ino:1-8,86-90 (Wire, SoftwareSerial BT(2, 3), PCA9685 0x40); README.md mục 1 (nguồn riêng vào cổng xanh); ảnh hw_electronics.
""")


# ==============================================================================
# 01 · Linh kiện · sự cố servo kẹp nóng
# ==============================================================================
def slide_heat(prs, n):
    s = new_slide(prs)
    header(s, "01 · Linh kiện · Sự cố", "Servo kẹp nóng vì xung PWM không bao giờ nghỉ", "hw")
    box(s, M, 1.95, 4.85, 3.85, fill=ORANGE_SOFT)
    label(s, M + 0.28, 2.18, 4.3, "Nguyên nhân", ORANGE)
    steps(s, M + 0.28, 2.65, 4.3, [
        "Firmware cũ không bao giờ ngắt xung: kẹp giữ vật hay chạm chốt chặn thì servo bị ép liên tục, đứng yên cũng vậy",
        "Lệnh đóng kẹp cũ 175° (xung ≈ 2,74 ms), vượt dải 0,5–2,5 ms của MG996R",
    ], 15, dot_color=ORANGE, d=0.36, gap=0.3)
    x2 = M + 4.85 + 0.3
    box(s, x2, 1.95, W - M - x2, 3.85, fill=TEAL_SOFT)
    label(s, x2 + 0.28, 2.18, 6.2, "Cách xử lý trong firmware", TEAL)
    fixes = ["Giới hạn cứng góc kẹp 160°; mỗi lần bấm kẹp chỉ nhích 5°",
             "Kẹp mở hết cỡ (95°) mà 5 giây không có lệnh → ngắt xung",
             "Kẹp đã khép quá 60 giây → ngắt xung (vật có thể tuột)",
             None,  # Hàng phím X / Z vẽ riêng
             "Màn hình biết tay đang nghỉ: CANH TAY DANG NGHI"]
    for i, st in enumerate(fixes):
        y = 2.65 + i * 0.6
        dot(s, x2 + 0.28, y, i + 1, d=0.36, size=13)
        if st is None:
            keycap(s, x2 + 0.82, y - 0.03, "X", 0.42, 0.4, 15)
            text(s, x2 + 1.32, y - 0.03, 2.0, 0.4, "kẹp nghỉ ngay", 15, INK, anchor=MIDDLE)
            keycap(s, x2 + 3.25, y - 0.03, "Z", 0.42, 0.4, 15)
            text(s, x2 + 3.75, y - 0.03, 2.6, 0.4, "cả 4 servo nghỉ", 15, INK, anchor=MIDDLE)
        else:
            text(s, x2 + 0.82, y + 0.02, W - M - x2 - 1.0, 0.4, st, 15, INK)
    done = "ĐÃ NẠP VÀ KIỂM TRÊN MẠCH THẬT (02/11, 21:42 và 21:54)"
    w1 = chip(s, M, 6.1, done, size=11, h=0.4)
    chip(s, M + w1 + 0.2, 6.1, "CHƯA ĐO NHIỆT ĐỘ SERVO", ORANGE, ORANGE_SOFT, size=11, h=0.4)
    footer(s, n)
    notes(s, """
Cuối phần linh kiện là một sự cố phần cứng nhóm gặp: servo tay kẹp bị nóng. Có hai nguyên nhân. Firmware cũ không bao giờ ngắt xung PWM, nên khi kẹp giữ vật hay chạm chốt chặn thì servo bị ép liên tục. Và lệnh đóng cũ một trăm bảy mươi lăm độ cho xung khoảng hai phẩy bảy bốn mi-li-giây, vượt dải không phẩy năm đến hai phẩy năm của MG996R.

Firmware mới xử lý theo từng lớp: giới hạn cứng góc kẹp một trăm sáu mươi độ; kẹp mở hết cỡ năm giây không có lệnh thì ngắt xung, kẹp đã khép quá sáu mươi giây cũng ngắt; phím X cho kẹp nghỉ ngay, phím Z cho cả bốn servo nghỉ; và màn hình biết khi tay đang nghỉ.

Firmware này đã nạp lúc chín giờ bốn mươi hai và chín giờ năm mươi tư tối ngày hai tháng mười một, và kiểm trên mạch thật. Nhưng nhóm chưa đo nhiệt độ servo, nên chưa có con số nguội đi bao nhiêu.

Phần linh kiện là vậy. Tiếp theo, {cv} trình bày computer vision.

Nếu được hỏi: phím Z có gì cần chú ý? Cả bốn servo mất xung nên cánh tay tự sụp theo trọng lực: phải hạ đầu kẹp tựa xuống chỗ trống trước. Vì sao không dùng cảm biến nhiệt? Chưa có trong phần cứng; đây là việc có thể thêm. Giới hạn một trăm sáu mươi có vượt dải xung không? Có, hơi vượt: xung khoảng hai phẩy năm sáu mi-li-giây so với dải danh định hai phẩy năm; chủ máy chấp nhận để kẹp chặt hơn và vẫn có tự nhả xung sau sáu mươi giây. Vì sao ngắt xung khi mở hết cỡ thì hàm khép lại? Khi mất xung, hai hàm rơi thành hình chữ V hẹp, khe còn khoảng một đến hai xăng-ti-mét (ước lượng từ ảnh), nên khi tiếp cận phải bấm J lại.

Nguồn: robot_arm_4dof.ino:16-23,160-176,191-201; control.py (trạng thái relaxed, cảnh báo FIRMWARE CU KHONG CO PHIM Z); README.md mục 6; 05_SO_LIEU_VA_NGUON.md mục 6.
""")


# ==============================================================================
# 02 · Computer vision · tờ A4 thành hệ tọa độ
# ==============================================================================
def slide_a4(prs, n):
    s = new_slide(prs, alt=True)
    header(s, "02 · Computer vision", "Bốn mã ArUco biến tờ A4 thành thước đo bằng cm", "cv")
    pw = (CW - 0.4) / 2
    ph = pw * 9 / 16 * 0.98
    image(s, "sw_annot_top.jpg", M, 1.95, pw, ph)
    image(s, "sw_annot_side.jpg", M + pw + 0.4, 1.95, pw, ph)
    caption(s, M, 1.95 + ph + 0.12, pw, "Cam TRÊN: lưới 5 cm dựng từ 4 mã; cốc đo được ở X = 16,5 cm, Y = 13,8 cm", 10.5, 0.3)
    caption(s, M + pw + 0.4, 1.95 + ph + 0.12, pw, "Cam NGANG: cùng tờ giấy nhìn nghiêng, cùng lưới tọa độ", 10.5, 0.3)
    cols = [("4 mã ở 4 góc", "DICT_4X4_50, ID 0–3, cạnh 2,8 cm; in A4 đúng 100%"),
            ("Homography", "pixel ↔ cm cho cả hai camera; gốc ở mã ID 0, X dài 29,7 cm, Y rộng 21,0 cm"),
            ("Che mất mã vẫn chạy", "dùng vị trí đã nhớ; xô camera thì tự học lại; phím U dò lại"),
            ("Sửa lệch phối cảnh", "cam TRÊN treo ≈ 46 cm: vật cao 5 cm lệch ≈ 1 cm. Một phép đo: 1,2 → 0,2 cm")]
    y0 = 1.95 + ph + 0.62
    for i, (t, d) in enumerate(cols):
        x = M + i * (CW / 4)
        dot(s, x, y0, i + 1, d=0.34, size=12)
        text(s, x + 0.46, y0 + 0.01, CW / 4 - 0.6, 0.32, t, 14.5, INK, True)
        text(s, x + 0.46, y0 + 0.38, CW / 4 - 0.6, 1.0, d, 12, TEXT2, spacing=1.06)
    footer(s, n)
    notes(s, """
Điều đầu tiên hệ thống phải biết là vật nằm ở đâu, tính bằng xăng-ti-mét. Nhóm in một tờ A4 có bốn mã ArUco ở bốn góc; mỗi mã có số định danh và OpenCV tìm được bốn góc của mã.

Biết bốn góc ngoài đời cách nhau hai mươi chín phẩy bảy nhân hai mươi mốt xăng-ti-mét, chương trình tính phép biến đổi phẳng gọi là homography, đổi từng pixel sang tọa độ trên tờ giấy, cho cả hai camera. Gốc tọa độ ở mã số không. Che mất một hai mã thì chương trình dùng vị trí đã nhớ.

Một chi tiết nhóm phải sửa: camera trên treo cao khoảng bốn mươi sáu xăng-ti-mét, nên nắp cốc cao năm xăng-ti-mét bị lệch ra xa tâm ảnh khoảng một xăng-ti-mét. Nhóm sửa bằng một công thức tỉ lệ theo độ cao vật; ở một vị trí đã đo, hai camera lệch nhau một phẩy hai xăng-ti-mét trước khi sửa và không phẩy hai sau khi sửa. Hai ảnh là lưới do chương trình vẽ lên khung hình camera thật đã lưu.

Nếu được hỏi: vì sao ArUco? Vì mã có số định danh, cho bốn góc rõ ràng, chịu được nhìn nghiêng, và OpenCV có sẵn. Tờ giấy là hệ quy chiếu chung cho cả hai camera, nên đổi camera hay đổi chỗ đặt không phải đo lại bằng thước. Độ cao bốn mươi sáu xăng-ti-mét đo thế nào? Ước từ ảnh, chưa đo bằng thước; con số không phẩy hai chỉ là một phép đo.

Nguồn: generate_aruco_a4.py:3,31-36; vision.py:24-30,152-170,486-505,557-562; tests/test_vision.py:223-243; README.md mục 4.
""")


# ==============================================================================
# 02 · Computer vision · nhận diện vật
# ==============================================================================
def slide_objects(prs, n):
    s = new_slide(prs)
    header(s, "02 · Computer vision", "Tìm vật bằng màu; YOLO chỉ là tùy chọn", "cv")
    cards = [
        ("MẶC ĐỊNH", TEAL, TEAL_SOFT, "Tách màu trên giấy trắng",
         "Dựng ảnh phẳng của tờ A4 rồi tách vật có màu đậm (cốc đỏ). Bỏ khối rộng > 8 cm, dài > 18 cm, chạm mép giấy "
         "hoặc dính phần đen của cánh tay: bàn tay người không bị nhận thành vật."),
        ("CHẮC NHẤT", TEAL, BG2, "Mã ArUco ID 10–29 trên vật",
         "Dán mã lên vật: cho vị trí chắc chắn; kích thước vật tra bảng OBJECT_SPECS."),
        ("TÙY CHỌN · --yolo", INDIGO, BG2, "YOLO11s (bộ COCO)",
         "Nhận tên vật. Trọng số có sẵn, nhóm chưa huấn luyện lại. Bỏ 12 lớp không phải vật cần gắp; vật YOLO tìm ra cũng phải có màu."),
    ]
    cw = (CW - 0.5) / 3
    for i, (tag, col, fill, title, desc) in enumerate(cards):
        x = M + i * (cw + 0.25)
        box(s, x, 1.95, cw, 2.42, fill=fill)
        chip(s, x + 0.22, 2.15, tag, col, CARD if fill != BG2 else (INDIGO_SOFT if col == INDIGO else TEAL_SOFT), size=10)
        text(s, x + 0.22, 2.62, cw - 0.4, 0.36, title, 16, INK, True)
        text(s, x + 0.22, 3.05, cw - 0.4, 1.3, desc, 12.5, TEXT2, spacing=1.08)
    image(s, "ui_guide_cameras.png", M, 4.62, 7.6, 1.95, mode="cover", focus=(0.5, 0.45))
    caption(s, M, 6.68, 7.6, "Màn hình bản TRƯỚC khi đơn giản hóa (02/11): YOLO gọi chi tiết robot là bottle, airplane; nắp cốc là frisbee", 10, 0.3)
    bx = M + 7.6 + 0.35
    box(s, bx, 4.56, W - M - bx, 2.07, fill=BG2)
    label(s, bx + 0.25, 4.72, 3.6, "Chọn vật nào?", TEAL, 10.5)
    bullets(s, bx + 0.25, 5.08, W - M - bx - 0.45, 1.55, [
        "Vật gần đế nhất được chọn trước",
        [("TAB", {"bold": True}), " đổi sang vật khác"],
        "Trung bình 10 khung cho đỡ rung",
        "Bị che (kẹp che cốc): nhớ vị trí 120 giây",
    ], 13, after=3)
    footer(s, n)
    notes(s, """
Biết tờ giấy rồi thì phải tìm vật. Cách mặc định là tách màu trên nền giấy trắng: chương trình dựng ảnh phẳng của tờ A4 rồi tách vật có màu đậm như cốc đỏ, không cần mã. Bàn tay người đưa vào không bị nhận thành vật, vì bộ lọc bỏ khối quá to, chạm mép giấy, hoặc dính vào phần đen của cánh tay.

Cách chắc nhất là dán mã ArUco số mười tới hai mươi chín lên vật. Cách thứ ba là YOLO11 bản COCO, nhóm chưa huấn luyện lại, và nó chỉ là tùy chọn. Lý do ở ảnh bên dưới: trên màn hình bản trước, YOLO gọi chi tiết robot là chai và máy bay, gọi nắp cốc là đĩa ném. Vì vậy bản hiện tại tắt YOLO mặc định.

Khi có nhiều vật, vật gần đế nhất được chọn trước, phím TAB đổi vật; vị trí lấy trung bình mười khung cho đỡ rung, và khi càng kẹp che mất cốc thì chương trình nhớ vị trí cũ trong hai phút.

Có vị trí vật rồi, {ctrl} trình bày phần code điều khiển.

Nếu được hỏi: có huấn luyện YOLO không? Chưa; huấn luyện lại cho vật thật là việc có thể làm sau. Vì sao còn giữ YOLO? Để nhận tên vật khi cần; còn vị trí xăng-ti-mét luôn tính từ homography của tờ giấy. Ảnh chụp màn hình lấy ở đâu? Từ giao diện cũ trước khi đơn giản hóa; hiện tượng nhận nhầm là có thật và là lý do YOLO bị tắt.

Nguồn: main.py:53 (--yolo); vision.py:43-47,271-300,365-368,476-486,491-492,507-515; control.py:68-69,542-566.
""")


# ==============================================================================
# 03 · Code điều khiển · lưu đồ thuật toán (firmware + chương trình laptop)
# ==============================================================================
def node(s, x, y, w, h, txt, kind="proc", fill=CARD, edge=INK, size=10.5, bold=False):
    shape = {"proc": ROUND, "dec": MSO_SHAPE.DIAMOND, "term": OVAL}[kind]
    shp = box(s, x, y, w, h, fill=fill, edge=edge, edge_w=1.0, radius=0.08, shape=shape)
    return label_in(shp, txt, size, INK, bold, margin=0.06 if kind != "dec" else 0.0)


def slide_flow(prs, n):
    s = new_slide(prs)
    header(s, "03 · Code điều khiển", "Lưu đồ: firmware Arduino và chương trình trên laptop", "ctrl")
    label(s, M, 1.88, 5.6, "Firmware Arduino · robot_arm_4dof.ino", ORANGE, 10)
    cx = 2.55
    node(s, cx - 0.65, 2.25, 1.3, 0.38, "Bắt đầu", "term", fill=ORANGE_SOFT, edge=ORANGE, size=11, bold=True)
    node(s, 0.85, 2.85, 3.4, 0.64, "setup(): USB + HC-05 9600 baud · PCA9685 50 Hz · servo về 90/90/90/95", size=10.5)
    decs = [(3.72, "Có phím?", "Đổi góc theo phím (giới hạn) · xuất xung · gửi JSON ngay"),
            (4.72, "Kẹp quá hạn?", "mở 5 s / khép 60 s → ngắt xung kẹp"),
            (5.72, "Đủ 200 ms?", "Gửi JSON bốn góc servo")]
    line(s, cx, 2.63, cx, 2.85, INK, 1.25, head=True)
    line(s, cx, 3.49, cx, decs[0][0], INK, 1.25, head=True)
    for i, (y, q, act) in enumerate(decs):
        node(s, cx - 1.1, y, 2.2, 0.78, q, "dec", fill=CARD, size=11, bold=True)
        node(s, 4.35, y + 0.05, 2.05, 0.68, act, fill=TEAL_SOFT, edge=TEAL, size=10)
        line(s, cx + 1.1, y + 0.39, 4.35, y + 0.39, TEAL, 1.25, head=True)
        text(s, cx + 1.18, y + 0.1, 0.5, 0.25, "có", 10, TEAL, True)
        if i < 2:
            line(s, cx, y + 0.78, cx, decs[i + 1][0], INK, 1.25, head=True)
            text(s, cx + 0.08, y + 0.8, 0.7, 0.22, "không", 10, MUTED)
    yb = decs[-1][0] + 0.78
    line(s, cx, yb, cx, 6.72, INK, 1.25)
    line(s, cx, 6.72, 0.95, 6.72, INK, 1.25)
    line(s, 0.95, 6.72, 0.95, decs[0][0] + 0.39, INK, 1.25)
    line(s, 0.95, decs[0][0] + 0.39, cx - 1.1, decs[0][0] + 0.39, INK, 1.25, head=True)
    text(s, 1.02, 6.45, 1.2, 0.25, "loop()", 10, MUTED, True, font=MONO)
    # Chương trình trên laptop
    lx, lw = 7.0, 3.65
    label(s, lx, 1.88, 5.6, "Chương trình laptop · main.py, mỗi khung hình", TEAL, 10)
    steps_ = [("Đọc 2 camera: OBSBOT (trên), MacBook (ngang)", BG2, LINE),
              ("vision.py: 4 mã ArUco → homography; tách màu → vật (X, Y) cm", BG2, LINE),
              ("control.py: chọn vật, động học ngược → Plan (phím, số lần)", TEAL_SOFT, TEAL),
              ("success.py: 3 servo lệch ≤ 2°, giữ 1 s → XONG, đếm", TEAL_SOFT, TEAL),
              ("screen.py: vẽ lệnh bấm phím và kết luận", BG2, LINE)]
    ys = [2.25 + i * 0.72 for i in range(len(steps_))]
    for i, ((txt, fill, edge), y) in enumerate(zip(steps_, ys)):
        node(s, lx, y, lw, 0.52, txt, fill=fill, edge=edge, size=10.5)
        if i < len(steps_) - 1:
            line(s, lx + lw / 2, y + 0.52, lx + lw / 2, ys[i + 1], INK, 1.25, head=True)
    yl = ys[-1] + 0.26
    line(s, lx + lw, yl, 11.0, yl, INK, 1.25)
    line(s, 11.0, yl, 11.0, ys[0] + 0.26, INK, 1.25)
    line(s, 11.0, ys[0] + 0.26, lx + lw, ys[0] + 0.26, INK, 1.25, head=True)
    text(s, 11.12, 3.6, W - M - 11.12, 0.6, ["lặp lại", "mỗi khung hình"], 10.5, MUTED, spacing=1.05)
    box(s, lx, 5.98, W - M - lx, 0.7, fill=ORANGE_SOFT)
    text(s, lx + 0.2, 5.98, W - M - lx - 0.35, 0.7,
         [[("Khi người bấm phím: ", {"bold": True, "color": ORANGE}),
           "main.py gọi control.press(phím) → gửi ký tự xuống Arduino qua cáp USB (chưa cắm thì mô phỏng)"]],
         11, INK, anchor=MIDDLE, spacing=1.05)
    footer(s, n)
    notes(s, """
Bên trái là lưu đồ firmware chạy trên Arduino. Khi khởi động, hàm setup mở cổng USB và cổng HC-05 ở chín nghìn sáu trăm baud, đặt PCA9685 ở năm mươi héc và đưa bốn servo về chín mươi, chín mươi, chín mươi, chín mươi lăm độ. Sau đó vòng lặp loop làm ba việc: có phím thì đổi góc trong giới hạn, xuất xung và gửi trạng thái ngay; kẹp quá hạn giữ thì ngắt xung; và cứ hai trăm mi-li-giây gửi gói JSON một lần.

Bên phải là chương trình Python trên laptop, chạy mỗi khung hình: đọc hai camera, vision tìm tờ giấy và vật, khối điều khiển tính góc và lệnh bấm phím, khối success kiểm tra, rồi vẽ màn hình. Song song, khi người bấm phím, main.py gọi hàm press của khối điều khiển để gửi ký tự đó xuống Arduino qua cáp USB; nếu chưa cắm Arduino thì chương trình chạy mô phỏng.

Nếu được hỏi: vì sao firmware đọc HC-05 trước USB? Để phím không dây không bị chặn khi USB cũng có dữ liệu; mỗi vòng chỉ đọc một ký tự. Vì sao không gửi lệnh góc trực tiếp? Để Arduino chỉ cần hiểu từng phím, giống hệt khi người điều khiển bằng tay.

Nguồn: robot_arm_4dof.ino:84-208; main.py:164-180,204-214; control.py:606-618 (press); success.py.
""")


# ==============================================================================
# 03 · Code điều khiển · code firmware
# ==============================================================================
def slide_fwcode(prs, n):
    s = new_slide(prs)
    header(s, "03 · Code điều khiển", "Firmware: nhận phím, đổi góc, gửi trạng thái", "ctrl")
    pw = (CW - 0.3) / 2
    blocks = [
        ("1 · Nhận phím, đổi góc trong giới hạn (loop)", [
            ("char cmd = 0;", None),
            ("if (BT.available()) {", None),
            ("  cmd = BT.read();", "// HC-05"),
            ("} else if (Serial.available()) {", None),
            ("  cmd = Serial.read();", "// cáp USB"),
            ("}", None),
            ("switch (cmd) {", None),
            ("  case 'a': case 'A':", None),
            ("    angleBase = constrain(angleBase + STEP_ARM, 0, 180);", None),
            ("    break;", None),
            ("  ...", "// d, w, s, i, k, j, l, h, x, z"),
            ("}", None),
            ("setServoAngle(0, angleBase);", None),
        ]),
        ("2 · Góc → xung, gửi trạng thái về laptop", [
            ("void setServoAngle(uint8_t channel, int angle) {", None),
            ("  int pulse = map(angle, 0, 180, SERVOMIN, SERVOMAX);", None),
            ("  pwm.setPWM(channel, 0, pulse);", None),
            ("}", None),
            ("", None),
            ("if (millis() - lastReportMs >= 200) {", None),
            ("  lastReportMs = millis();", None),
            ("  sendServoState();", "// 5 lần mỗi giây"),
            ("}", None),
            ("", None),
            ("// ví dụ một gói JSON gửi lên:", None),
            ('// {"t":5120,"servo":[90,90,90,95],', None),
            ('//  "relax":0,"armrelax":0}', None),
        ]),
    ]
    for i, (title, code) in enumerate(blocks):
        x = M + i * (pw + 0.3)
        box(s, x, 1.95, pw, 3.9, fill=BG2)
        label(s, x + 0.25, 2.1, pw - 0.4, title, TEAL, 10)
        paras = []
        for ln, cm in code:
            runs = [(ln, {"color": MUTED if ln.strip().startswith("//") else INK})]
            if cm:
                runs.append(("  " + cm, {"color": MUTED}))
            paras.append(runs)
        text(s, x + 0.25, 2.48, pw - 0.4, 3.3, paras, 11, INK, font=MONO, spacing=1.08)
    facts = [("2° / 5°", "STEP_ARM / STEP_GRIP: mỗi lần bấm"), ("125 → 575", "SERVOMIN → SERVOMAX ≈ 0–180°"),
             ("9600 baud", "USB và HC-05 cùng tốc độ")]
    fw = (CW - 0.5) / 3
    for i, (big, desc) in enumerate(facts):
        x = M + i * (fw + 0.25)
        box(s, x, 6.05, fw, 0.75, fill=TEAL_SOFT)
        bw = text_w(big, 18, True) + 0.25
        text(s, x + 0.2, 6.05, bw, 0.75, big, 18, TEAL, True, anchor=MIDDLE)
        text(s, x + 0.2 + bw, 6.05, fw - 0.3 - bw, 0.75, desc, 11, INK, anchor=MIDDLE, spacing=1.02)
    footer(s, n)
    notes(s, """
Đây là phần code chính của firmware, đã rút gọn. Bên trái: mỗi vòng lặp đọc một ký tự, ưu tiên HC-05 rồi tới cáp USB; lệnh switch đổi góc theo từng phím, luôn qua hàm constrain để không vượt giới hạn, ví dụ đế từ không tới một trăm tám mươi độ, vai và khuỷu từ hai mươi lăm tới một trăm năm mươi lăm, kẹp từ chín mươi lăm tới một trăm sáu mươi; rồi xuất góc mới ra servo.

Bên phải: hàm setServoAngle đổi góc thành độ rộng xung bằng hàm map, từ một trăm hai mươi lăm tới năm trăm bảy mươi lăm, rồi gửi cho PCA9685; và cứ hai trăm mi-li-giây firmware gửi một gói JSON như dòng ví dụ, gồm thời gian chạy, bốn góc servo và hai cờ cho biết servo kẹp hay cả cánh tay đang nghỉ. Chương trình trên laptop đọc gói này để biết góc hiện tại.

Nếu được hỏi: vì sao gửi JSON? Dễ đọc bằng Python và có chỗ cho cờ trạng thái. Thời gian chạy t dùng làm gì? Khi t quay về gần không là Arduino vừa khởi động lại, chương trình báo ARDUINO VUA RESET. Dòng JSON trên slide là ví dụ minh họa đúng định dạng, số t là giả định.

Nguồn: robot_arm_4dof.ino:9-14,41-45,69-83,101-150,203-207.
""")


# ==============================================================================
# 03 · Code điều khiển · động học ngược
# ==============================================================================
def arm_diagram(s):
    """Cánh tay nhìn ngang ở tư thế servo vai 90°, khuỷu 90° (mô hình mặc định), tỉ lệ 1 inch = 60 mm."""
    k = 1 / 60.0
    table_y, sx = 5.25, 2.05
    sy = table_y - 70 * k
    ex, ey = sx + 105 * k * 0.7071, sy - 105 * k * 0.7071
    wx, wy = ex + 100 * k, ey
    tx, ty = wx + 65 * k, wy + 25 * k
    line(s, M, table_y, 6.4, table_y, LINE, 1.5)
    text(s, 4.95, table_y + 0.07, 1.45, 0.25, "mặt bàn", 10.5, MUTED, align=RIGHT)
    box(s, sx - 0.3, table_y - 0.42, 0.6, 0.42, fill=BG2, edge=LINE)
    line(s, sx, table_y - 0.42, sx, sy, MUTED, 6)
    line(s, sx, sy, ex, ey, INK, 6)
    line(s, ex, ey, wx, wy, INK, 6)
    line(s, wx, wy, tx, wy, MUTED, 1.5, dash=True)
    line(s, tx, wy, tx, ty, MUTED, 1.5, dash=True)
    for (jx, jy) in ((sx, sy), (ex, ey), (wx, wy)):
        box(s, jx - 0.09, jy - 0.09, 0.18, 0.18, fill=CARD, edge=INK, edge_w=2, shape=OVAL)
    box(s, tx - 0.09, ty - 0.09, 0.18, 0.18, fill=ORANGE, shape=OVAL)
    text(s, M, (sy + table_y) / 2 - 0.16, sx - 0.42 - M, 0.3, "d1 = 70", 12.5, TEXT2, True, align=RIGHT)
    text(s, sx - 1.05, ey + 0.38, 1.25, 0.3, "L2 = 105", 12.5, INK, True, align=RIGHT)
    text(s, (ex + wx) / 2 - 0.65, ey - 0.42, 1.3, 0.3, "L3 = 100", 12.5, INK, True, align=CENTER)
    text(s, (wx + tx) / 2 - 0.62, wy - 0.42, 1.24, 0.3, "L4r = 65", 11.5, MUTED, True, align=CENTER)
    text(s, tx + 0.12, (wy + ty) / 2 - 0.15, 0.75, 0.3, "L4z = 25", 11.5, MUTED, True)
    text(s, tx - 1.0, ty + 0.14, 1.6, 0.3, "điểm kẹp", 11.5, ORANGE, True, align=CENTER)
    text(s, sx + 0.18, sy - 0.05, 0.9, 0.3, "θ2", 12.5, TEAL, True)
    text(s, ex + 0.12, ey + 0.08, 0.9, 0.3, "θ3", 12.5, TEAL, True)


def slide_ik(prs, n):
    s = new_slide(prs)
    header(s, "03 · Code điều khiển", "Từ vị trí (X, Y) của vật tính ra góc ba servo", "ctrl")
    arm_diagram(s)
    caption(s, M, 5.6, 5.7, "Mô hình mặc định (mm, đo bằng thước): servo vai 90° ↔ θ2 = 45°, servo khuỷu 90° ↔ θ3 = −45°. "
            "Không có servo cổ tay nên hướng ngón kẹp không chọn được.", 11, 0.75)
    items = ["Đổi (X, Y) cm trên giấy sang tọa độ robot (mm) theo vị trí và hướng của đế",
             [("Đế: ", {"bold": True}), ("θ1 = atan2(y, x)", {"font": MONO, "bold": True, "color": TEAL})],
             "Vai, khuỷu: giải tam giác hai khâu, chọn nghiệm khuỷu hướng lên; điểm kẹp cao 25 mm",
             "Đổi ra góc servo, làm tròn bội số 2°; số lần bấm = độ lệch ÷ 2°"]
    steps(s, 6.9, 1.98, W - M - 6.9, items, 15, gap=0.2)
    box(s, 6.9, 4.98, W - M - 6.9, 1.82, fill=TEAL_SOFT)
    label(s, 7.15, 5.1, 5.3, "Ví dụ · cốc ở (20,1; 7,4) cm", TEAL, 10.5)
    text(s, 7.15, 5.42, 5.4, 0.45, "đế 74° · vai 58° · khuỷu 90°", 23, INK, True)
    text(s, 7.15, 5.98, 1.75, 0.42, "Từ Home 90/90/90:", 12.5, TEXT2, anchor=MIDDLE)
    keycap(s, 8.92, 5.98, "D", 0.42, 0.4, 15)
    text(s, 9.4, 5.98, 0.6, 0.42, "× 8", 16, INK, True, anchor=MIDDLE)
    keycap(s, 10.02, 5.98, "S", 0.42, 0.4, 15)
    text(s, 10.5, 5.98, 0.7, 0.42, "× 16", 16, INK, True, anchor=MIDDLE)
    text(s, 11.22, 5.98, 1.35, 0.42, "khuỷu đã đúng", 11.5, TEAL, True, anchor=MIDDLE)
    text(s, 7.15, 6.47, 5.4, 0.3, f"robot x = 240 mm, y = −73 mm · dùng mô hình đã hiệu chỉnh (slide {num('calib')})", 10.5, TEXT2)
    footer(s, n)
    notes(s, """
Biết vật ở X, Y, khối điều khiển tính ba servo cần ở góc nào: đây là bài toán động học ngược.

Cánh tay nhìn ngang như hình: trục vai cao bảy mươi mi-li-mét so với mặt bàn, khâu vai dài một trăm linh năm, khâu khuỷu dài một trăm, tâm hai ngón kẹp lệch sáu mươi lăm ra trước và hai mươi lăm xuống dưới. Đó là số đo bằng thước của mô hình mặc định; ở cuối phần này em sẽ cho thấy chúng được hiệu chỉnh lại.

Có bốn bước: đổi tọa độ trên giấy sang tọa độ robot; góc đế bằng a-tan-hai của y trên x; vai và khuỷu giải tam giác hai khâu, chọn nghiệm khuỷu hướng lên, với điểm kẹp cao hai mươi lăm mi-li-mét; cuối cùng đổi ra góc servo, làm tròn bội số hai độ, rồi độ lệch chia hai là số lần bấm.

Ví dụ cốc ở hai mươi phẩy một và bảy phẩy bốn xăng-ti-mét: gợi ý đế bảy mươi bốn, vai năm mươi tám, khuỷu chín mươi độ. Từ Home, khi ba servo đều ở chín mươi độ, bấm D tám lần và S mười sáu lần; khuỷu đã đúng. Cánh tay không có servo cổ tay nên hướng ngón kẹp không chọn được.

Nếu được hỏi: công thức có được kiểm lại không? Có: trong bộ test, chương trình đưa kết quả động học ngược vào động học thuận trên hơn một trăm điểm trong tầm với và thấy sai số dưới không phẩy một mi-li-mét. Vì sao nghiệm khuỷu hướng lên? Tam giác hai khâu có hai nghiệm; code luôn chọn khuỷu hướng lên để mỗi điểm chỉ có một bộ góc. Vật ngoài tầm với thì sao? Màn hình báo VAT NGOAI TAM VOI và cần dời vật lại gần thêm bao nhiêu mi-li-mét.

Nguồn: control.py:36-67,98-161,174-195,221-245; tests/test_control.py:16-35; 05_SO_LIEU_VA_NGUON.md mục 3 và 16 (ví dụ tính lại bằng check_facts.py --deep).
""")


# ==============================================================================
# 03 · Code điều khiển · màn hình hai ô
# ==============================================================================
def slide_screen(prs, n):
    s = new_slide(prs)
    header(s, "03 · Code điều khiển", "Màn hình chỉ nói một việc: bấm phím nào, mấy lần", "ctrl")
    ih = image(s, "ui_screen_before.png", M, 1.95, 7.85, None, mode="fit")
    caption(s, M, 1.95 + ih + 0.13, 7.85, "Màn hình thật của chương trình, chạy trên ảnh camera thật đã lưu (20:27); cánh tay MÔ PHỎNG "
            "(chân trang ghi USB Arduino: MO PHONG). Chữ không dấu vì OpenCV không vẽ được dấu.", 10.5, 0.5)
    rx, rw = 9.05, W - M - 9.05
    dot(s, rx, 1.98, 1, d=0.38, size=13)
    text(s, rx + 0.5, 1.98, rw - 0.5, 0.34, "Ô điều khiển", 15.5, INK, True)
    text(s, rx + 0.5, 2.34, rw - 0.5, 0.95, "phím to, số lần, hạ / quay bao nhiêu độ; ba hàng servo: góc hiện tại → góc đích", 12.5,
         TEXT2, spacing=1.06)
    dot(s, rx, 3.32, 2, d=0.38, size=13)
    text(s, rx + 0.5, 3.32, rw - 0.5, 0.34, "Ô success", 15.5, INK, True)
    text(s, rx + 0.5, 3.68, rw - 0.5, 0.7, "CHƯA XONG, còn N lần bấm; hoặc XONG! khi cả ba servo tới góc", 12.5, TEXT2, spacing=1.06)
    box(s, rx, 4.5, rw, 1.25, fill=BG2)
    label(s, rx + 0.2, 4.6, rw - 0.3, "Trái / phải theo cam ngang", TEXT2, 10)
    keycap(s, rx + 0.2, 4.93, "A", 0.42, 0.4, 15)
    text(s, rx + 0.7, 4.93, 1.1, 0.4, "sang phải", 13.5, INK, anchor=MIDDLE)
    keycap(s, rx + 1.9, 4.93, "D", 0.42, 0.4, 15)
    text(s, rx + 2.4, 4.93, 1.2, 0.4, "sang trái", 13.5, INK, anchor=MIDDLE)
    text(s, rx + 0.2, 5.4, rw - 0.3, 0.3, "W S vai · I K khuỷu · mỗi lần 2°", 11.5, TEXT2)
    text(s, rx, 5.95, rw, 0.85, [[("Trong ảnh: ", {"color": MUTED}), "cốc ở (16,5; 13,8) cm"],
                                 [("→ ", {"color": TEAL}), ("BẤM S × 15", {"color": TEAL, "bold": True}), ", hạ vai 30°"],
                                 "đế đã đúng · còn 18 lần bấm"], 12.5, INK, spacing=1.08)
    footer(s, n)
    notes(s, """
Đây là màn hình của chương trình, chạy trên ảnh camera thật đã lưu với cánh tay mô phỏng, nên chân trang ghi mô phỏng. Hai khung camera ở trên có lưới tọa độ, vòng DICH quanh cốc và dấu KEP là chỗ đầu kẹp theo mô hình.

Bên dưới là hai ô nối nhau bằng một mũi tên. Ô một vẽ từ Plan của khối điều khiển: một lệnh to. Trong ảnh, cốc ở mười sáu phẩy năm và mười ba phẩy tám xăng-ti-mét, lệnh là bấm S mười lăm lần, hạ vai ba mươi độ, còn mười tám lần bấm. Ba hàng bên dưới là ba servo; hàng nào đã đúng thì ghi ĐÃ ĐÚNG, như hàng đế chỉ lệch hai độ. Ô hai vẽ từ kết quả của khối success: chưa xong, còn bao nhiêu lần bấm, hoặc XONG.

Chữ không dấu vì OpenCV không vẽ được dấu tiếng Việt. Trái phải nhìn theo camera MacBook đặt trước robot, nên phím A quay đế sang phải, phím D sang trái. Màn hình chỉ cho biết phải bấm gì; người điều khiển là người bấm.

Nếu được hỏi: có tự gửi phím không? Không; chương trình chỉ gửi phím khi người bấm. Vì sao chỉ một lệnh to? Để người điều khiển làm theo được ngay, không phải đọc bảng số. Vì sao thứ tự đế, rồi vai, rồi khuỷu? Là thứ tự code lập lệnh; hàng nào đã đúng thì được bỏ qua. Ảnh camera là ảnh cũ mà vẫn có gợi ý? Ảnh là khung camera thật lúc hai mươi giờ hai mươi bảy, chương trình đọc nó như camera đang chạy, còn cánh tay mô phỏng đặt ở Home. Gợi ý trên ảnh này là đế 88, vai 60, khuỷu 84, gần tư thế người thật sự ôm cốc lúc hai mươi giờ ba mươi hai, khoảng 85, 60, 90 (đọc từ màn hình bản cũ); nhưng chưa rõ lần ôm đó có nằm trong mười mẫu khớp hay không, nên chỉ nói là gần.

Nguồn: screen.py:157-239,249-259; main.py:155-180; control.py:211-217; ảnh ui_screen_before (tạo bằng slides/tools/make_screen_images.py).
""")


# ==============================================================================
# 03 · Code điều khiển · sự cố mô hình lệch và hiệu chỉnh
# ==============================================================================
def slide_calib(prs, n):
    s = new_slide(prs)
    header(s, "03 · Code điều khiển · Sự cố", "Mô hình lệch 3,5–5,9 cm; 10 lần ôm cốc sửa còn 8,5 mm", "ctrl")
    label(s, M, 1.95, 5.3, "Đầu kẹp theo mô hình mặc định cách cốc thật", TEXT2, 10.5)
    for i, (big, desc) in enumerate([("5,4 cm", "ôm lúc 20:32 · servo [85, 60, 90]"),
                                     ("3,5 cm", "ôm lúc 20:46 · servo [80, 70, 75]"),
                                     ("5,9 cm", "ôm lúc 21:03 · servo [75, 85, 50]")]):
        y = 2.3 + i * 0.6
        rule(s, M, y, 5.3)
        text(s, M, y + 0.04, 1.7, 0.55, big, 25, ORANGE, True, anchor=MIDDLE)
        text(s, M + 1.8, y + 0.04, 3.5, 0.55, desc, 13, TEXT2, anchor=MIDDLE)
    rule(s, M, 2.3 + 3 * 0.6, 5.3)
    text(s, M, 4.2, 5.3, 0.5, "Cùng chiều, cùng cỡ: lệch có hệ thống, nên sửa được bằng cách khớp lại mô hình", 12.5, TEXT2,
         spacing=1.05)
    label(s, M, 4.82, 5.3, "Cách sửa: hiệu chỉnh bằng các lần ôm cốc", TEAL, 10.5)
    steps(s, M, 5.18, 5.3, [
        "Người bấm phím cho hai ngón ôm quanh cốc; ghi 3 góc servo và vị trí cốc",
        "10 lần ở các chỗ khác nhau; khớp vị trí, hướng đế, 2 góc chuẩn và càng kẹp (Levenberg–Marquardt)",
        "Lưu vào calibration.json",
    ], 12.5, d=0.28, gap=0.08)
    iw = W - M - 6.45
    image(s, "calib_before_after_side.jpg", 6.45, 1.95, iw, iw * 9 / 16)
    ih = iw * 9 / 16
    caption(s, 6.45, 1.95 + ih + 0.12, iw, "Cam NGANG lúc ôm cốc 21:03: dấu MAC DINH cách cốc ≈ 5 cm, dấu SAU HIEU CHINH "
            "≈ 1 cm. Lần ôm này nằm trong 10 mẫu khớp: chỉ là minh họa.", 10, 0.45)
    bw = (iw - 0.25) / 2
    for i, (big, desc) in enumerate([("8,5 mm", ["sai số khớp RMS", "trên 10 mẫu"]), ("11,6 mm", ["bỏ-một-mẫu", "(leave-one-out)"])]):
        x = 6.45 + i * (bw + 0.25)
        nw = text_w(big, 20, True) + 0.2
        box(s, x, 5.98, bw, 0.82, fill=TEAL_SOFT)
        text(s, x + 0.18, 5.98, nw, 0.82, big, 20, TEAL, True, anchor=MIDDLE)
        text(s, x + 0.18 + nw, 5.98, bw - 0.26 - nw, 0.82, desc, 11, INK, anchor=MIDDLE, spacing=1.02)
    footer(s, n)
    notes(s, """
Đây là chỗ nhóm học được nhiều nhất. Gợi ý trên màn hình tính từ mô hình cánh tay chứ không đo bằng camera, nên mô hình lệch thì gợi ý nào cũng lệch.

Bằng chứng ở cột trái: trong buổi thử trên cánh tay thật, người điều khiển bấm phím cho hai ngón kẹp ôm quanh cốc, nhóm ghi ba góc servo và vị trí cốc. Đưa ba tư thế đầu vào mô hình mặc định, đầu kẹp theo mô hình cách cốc thật năm phẩy bốn, ba phẩy năm và năm phẩy chín xăng-ti-mét, cùng chiều, cùng cỡ: lỗi có hệ thống chứ không phải nhiễu.

Cách sửa là hiệu chỉnh bằng trình diễn: mười lần ôm cốc ở các chỗ khác nhau, khớp lại vị trí và hướng đế, hai góc chuẩn của vai và khuỷu, và càng kẹp, bằng thuật toán Levenberg–Marquardt viết thuần numpy. Sai số khớp còn tám phẩy năm mi-li-mét, và mười một phẩy sáu khi bỏ lần lượt từng mẫu. Trong ảnh, dấu cam là mô hình mặc định, dấu xanh là sau hiệu chỉnh, sát cốc; lần ôm này nằm trong mười mẫu nên chỉ là minh họa.

Giới hạn nhóm nói thẳng: tám phẩy năm là sai số trên chính mười mẫu dùng để khớp; nhóm chưa thử bấm theo gợi ý mới trên cánh tay thật; và hiệu chỉnh chỉ đúng với tờ giấy và chỗ đặt robot lúc đo.

Phần cuối, {succ} trình bày khối success và kết quả.

Nếu được hỏi: nguyên nhân lệch là gì? Có ba: vị trí và hướng của đế khác mặc định; hai góc chuẩn của vai và khuỷu khi servo ở chín mươi độ khác bốn mươi lăm độ, vì phụ thuộc cách lắp cần servo mà thước không đo được; và càng kẹp gắn cứng vào khâu khuỷu nên điểm kẹp quay theo khâu đó, trong khi mô hình cũ giữ độ lệch cố định theo phương ngang. Con số năm phẩy bốn có độc lập không? Màn hình bản cũ lúc hai mươi giờ ba mươi hai báo sai số đầu kẹp năm mươi sáu mi-li-mét, cùng cỡ. Vì sao không đo lại bằng thước? Thước đo được chiều dài các khâu, không đo được góc lắp cần servo; hiệu chỉnh bằng trình diễn làm được cả hai việc. Ví dụ sau hiệu chỉnh? Cốc ở hai mươi phẩy một và bảy phẩy bốn cho gợi ý bảy mươi bốn, năm mươi tám, chín mươi; hai tư thế người căn tay quanh cốc ở chỗ đó cho đầu kẹp theo mô hình cách cốc khoảng năm đến sáu mi-li-mét, nhưng chưa rõ hai tư thế đó có nằm trong mười mẫu khớp hay không, nên chỉ nói là gần.

Nguồn: calibration.json (mục arm, claw, arm_fit); calibration.py:16-20,77-105; arm_fit.py:1-45; tests/test_arm_fit.py:80-91; 05_SO_LIEU_VA_NGUON.md mục 8 và 16; ảnh calib_before_after_side.
""")


# ==============================================================================
# 04 · Success · luật success
# ==============================================================================
def slide_success(prs, n):
    s = new_slide(prs)
    header(s, "04 · Success", "XONG khi ba servo tới góc gợi ý và giữ yên một giây", "succ")
    rows = [("± 2°", "mỗi servo lệch không quá một bước bấm so với góc gợi ý (lệch 3° là chưa)"),
            ("3 servo", "đế, vai, khuỷu; tay kẹp không tính"),
            ("1 giây", "giữ đúng liên tục một giây mới đếm thêm một lần thành công")]
    for i, (big, desc) in enumerate(rows):
        y = 1.95 + i * 0.85
        rule(s, M, y, 5.8)
        text(s, M, y + 0.05, 1.85, 0.75, big, 30, TEAL, True, anchor=MIDDLE)
        text(s, M + 1.95, y + 0.05, 3.85, 0.75, desc, 14, INK, anchor=MIDDLE, spacing=1.05)
    rule(s, M, 1.95 + 3 * 0.85, 5.8)
    chip(s, M, 4.68, "ĐÃ KIỂM: 7 TEST + CHUỖI ĐẦU–CUỐI", size=10)
    chip(s, M, 5.08, "CHƯA ĐẾM TRÊN CÁNH TAY THẬT", ORANGE, ORANGE_SOFT, size=10)
    ih = image(s, "ui_screen_done.png", 6.9, 1.95, W - M - 6.9, None, mode="fit")
    caption(s, 6.9, 1.95 + ih + 0.12, W - M - 6.9, "Mô phỏng: bấm đủ phím theo lệnh → XONG! và đếm 1 lần (ảnh thật đã lưu, 20:32:52)",
            10, 0.3)
    for i, (title, body) in enumerate([
        ("Vì sao kẹp không tính", "Cốc thon dần xuống đáy: hai ngón đẩy cốc ra ở 150–160°; cốc đổ khoảng 3 lần trong buổi thử."),
        ("Giới hạn của chữ XONG", "Arduino báo lại góc đã RA LỆNH; MG996R không báo vị trí thật. XONG = đã bấm đủ phím, chưa phải đo thấy kẹp sát cốc."),
    ]):
        x = M + i * ((CW + 0.25) / 2)
        box(s, x, 5.7, (CW - 0.25) / 2, 1.12, fill=ORANGE_SOFT)
        label(s, x + 0.22, 5.8, 5.4, title, ORANGE, 10.5)
        text(s, x + 0.22, 6.12, (CW - 0.25) / 2 - 0.4, 0.7, body, 12.5, INK, spacing=1.05)
    footer(s, n)
    notes(s, """
Khối success chỉ trả lời một câu: ba servo đế, vai, khuỷu đã tới góc khối điều khiển gợi ý chưa. Nó không biết gì về camera, động học hay cổng USB, chỉ đọc Plan.

Quy tắc có ba điều. Mỗi servo lệch không quá một bước bấm, tức hai độ, là đã tới; nhóm chọn hai độ vì mô hình hình học vốn chỉ chính xác cỡ đó. Chỉ tính ba servo của cánh tay, không tính tay kẹp. Và cả ba phải giữ đúng liên tục một giây mới đếm thêm một lần thành công; lướt qua thì không đếm.

Tay kẹp không tính vì cốc nhóm dùng thon dần xuống đáy: khép hai ngón tới một trăm năm mươi, một trăm sáu mươi độ thì cốc bị đẩy ra, và trong buổi thử cốc đổ khoảng ba lần.

Hai điều nhóm nói thẳng. Chữ XONG nghĩa là ba góc lệnh đã tới, vì MG996R không báo vị trí thật; nó chưa phải bằng chứng hai ngón kẹp đang sát cốc. Và ảnh bên phải là mô phỏng trên ảnh thật đã lưu; trên cánh tay thật nhóm chưa có lần đếm nào cho bản này.

Nếu được hỏi: vì sao giữ một giây? Để lướt qua mục tiêu không bị tính là thành công. Có thể kiểm bằng camera không? Bản trước có làm, bằng hai tín hiệu từ hai camera; nhóm đã bỏ để mã đơn giản. Đếm ở đâu? Ở dòng Thanh cong: N lan trên ô success; chưa ghi ra file. Không thấy vật thì sao? Không bao giờ báo xong: trạng thái là chưa thấy vật.

Nguồn: success.py:16-17,19,22-75; tests/test_success.py (7 test); tests/test_end_to_end.py:11-47; robot_arm_4dof.ino:70-83; README.md mục 6; ảnh ui_screen_done (tạo bằng slides/tools/make_screen_images.py).
""")


# ==============================================================================
# 04 · Success · thử trên cánh tay thật
# ==============================================================================
def slide_trial(prs, n):
    s = new_slide(prs, alt=True)
    header(s, "04 · Success · Thử thật", "Cốc đỏ được kẹp, chuyển sang trái và đặt xuống", "succ")
    x0, w, gap = 2.0, 3.3, 0.22
    h = w * 9 / 16
    cols = [("demo_06_grip", "20:32:52 · KẸP"), ("demo_07_carry", "20:33:02 · CHUYỂN SANG TRÁI"), ("demo_08_place", "20:33:12 · ĐẶT XUỐNG")]
    for c, (stem, lab) in enumerate(cols):
        x = x0 + c * (w + gap)
        text(s, x, 1.92, w, 0.3, lab, 11, TEAL, True, align=CENTER, spc=100)
        image(s, f"{stem}_side.jpg", x, 2.3, w, h)
        image(s, f"{stem}_top.jpg", x, 2.3 + h + 0.2, w, h)
    for r, lab in enumerate(["CAM NGANG", "CAM TRÊN"]):
        y = 2.3 + r * (h + 0.2)
        text(s, M, y, 1.0, h, lab.split(" "), 11, TEXT2, True, anchor=MIDDLE, spacing=1.0, spc=100)
    w1 = chip(s, M, 6.5, "NGƯỜI BẤM PHÍM · KHÔNG TỰ ĐỘNG", ORANGE, ORANGE_SOFT, size=10.5, h=0.36)
    text(s, M + w1 + 0.2, 6.47, 11.95 - (M + w1 + 0.2) - 0.1, 0.45,
         "02/11/2026 · khung cắt từ video, cách nhau 10 giây · màn hình bản trước khi đơn giản hóa · "
         "cốc đổ khoảng 3 lần, dựng lại bằng tay · chưa có tỉ lệ thành công", 10.5, MUTED, spacing=1.05)
    footer(s, n)
    notes(s, """
Đây là bằng chứng cánh tay thật làm được việc. Ba cột cách nhau mười giây trong buổi thử ngày hai tháng mười một, hàng trên là camera ngang, hàng dưới là camera trên: cốc nằm giữa hai ngón kẹp, cốc được chuyển sang trái, rồi đặt xuống và cánh tay rút về. Nhóm làm vòng này nhiều lần.

Ba điều cần nói rõ. Đây là người bấm phím nhìn hình hai camera, trên màn hình bản trước khi đơn giản hóa, chưa phải tự động. Cốc bị đổ khoảng ba lần và được dựng lại bằng tay. Và đây chưa phải số liệu tỉ lệ thành công: nhóm chưa có tỉ lệ nào.

Góc servo lúc kẹp, đọc từ màn hình bản cũ: đế khoảng tám mươi lăm, vai sáu mươi đến sáu mươi lăm, khuỷu tám mươi lăm đến chín mươi độ. Những lần ôm cốc trong buổi này cũng là dữ liệu mà {ctrl} đã dùng để hiệu chỉnh mô hình.

Nếu được hỏi: có video không? [...điền: có / không; nếu có thì chiếu đoạn 20–30 giây]. Kẹp có giữ chắc không? Không hẳn: cốc đổ khoảng ba lần, và các lần thử sau cho thấy cốc thon bị đẩy ra ở 150–160 độ.

Nguồn: ảnh demo_06, demo_07, demo_08 (khung cắt từ video 02/11/2026, 20:32:52 đến 20:33:12); 05_SO_LIEU_VA_NGUON.md mục 7.
""")


# ==============================================================================
# 04 · Success · kết quả
# ==============================================================================
def slide_results(prs, n):
    s = new_slide(prs, alt=True)
    header(s, "04 · Success · Kết quả", "Đã có bằng chứng, và những điều chưa kiểm chứng", "succ")
    pw = (CW - 0.3) / 2
    box(s, M, 1.95, pw, 3.4, fill=TEAL_SOFT)
    label(s, M + 0.28, 2.12, pw - 0.5, "Đã có bằng chứng", TEAL, 10.5)
    bullets(s, M + 0.28, 2.5, pw - 0.5, 2.8, [
        "Hệ tọa độ từ tờ A4 chạy trên cả hai camera (ảnh thật)",
        "Cánh tay thật ôm cốc và chuyển sang trái khi người bấm phím (02/11)",
        "Mô hình khớp 10 lần ôm thật: 8,5 mm, bỏ-một-mẫu 11,6 mm",
        "Firmware chống nóng và phím Z đã nạp, kiểm trên mạch thật",
        "109 test tự động pass, không cần camera hay Arduino",
    ], 14, after=6)
    x2 = M + pw + 0.3
    box(s, x2, 1.95, pw, 3.4, fill=CARD)
    label(s, x2 + 0.28, 2.12, pw - 0.5, "Chưa kiểm chứng", ORANGE, 10.5)
    bullets(s, x2 + 0.28, 2.5, pw - 0.5, 2.8, [
        "Số lần XONG trên cánh tay thật: bản mới mới chạy bằng test và ảnh đã lưu",
        "Bấm đúng theo gợi ý mới thì hai ngón có ôm quanh cốc không",
        "Kẹp giữ chắc cốc thon (cần ma sát hoặc vật thân thẳng)",
        "Nhiệt độ servo kẹp sau khi thêm ngắt xung",
        "Hiệu chỉnh cho tờ giấy mới hoặc robot đặt chỗ khác",
        "Dashboard IoT / MQTT, cảm biến lực: có trong kế hoạch 28/10, chưa làm",
    ], 13, after=4, mark="—", mark_color=ORANGE, indent=0.3)
    stats = [("109 / 109", ["test tự động", "đều pass"], TEAL),
             ("11", ["tệp test, từ động học", "tới màn hình và Serial"], INK),
             ("0", ["lần đếm XONG trên", "cánh tay thật (bản mới)"], ORANGE)]
    sw = (CW - 0.5) / 3
    for i, (big, desc, col) in enumerate(stats):
        x = M + i * (sw + 0.25)
        bw = text_w(big, 32, True) + 0.3
        box(s, x, 5.55, sw, 1.27, fill=CARD)
        text(s, x + 0.25, 5.55, bw, 1.27, big, 32, col, True, anchor=MIDDLE)
        text(s, x + 0.25 + bw, 5.55, sw - 0.35 - bw, 1.27, desc, 12.5, TEXT2, anchor=MIDDLE, spacing=1.05)
    footer(s, n)
    notes(s, """
Slide này nói thật những gì nhóm có và chưa có.

Có bằng chứng: hệ tọa độ chạy trên cả hai camera; cánh tay thật ôm cốc và chuyển sang trái khi người bấm phím; mô hình khớp mười lần ôm thật với sai số tám phẩy năm mi-li-mét; firmware chống nóng đã nạp và kiểm trên mạch; và một trăm linh chín test tự động đều pass trong khoảng chín giây, không cần camera hay Arduino thật.

Chưa kiểm chứng: số lần XONG trên cánh tay thật cho bản mới; bấm theo gợi ý mới thì hai ngón có ôm quanh cốc không; kẹp giữ chắc cốc thon; nhiệt độ servo; hiệu chỉnh cho tờ giấy mới; và dashboard IoT với MQTT, cảm biến lực, vốn có trong kế hoạch ngày hai mươi tám tháng mười nhưng chưa làm.

Tóm lại: một trăm linh chín trên một trăm linh chín test pass, và chưa có lần đếm XONG nào trên cánh tay thật.

Nếu được hỏi: vì sao chưa chạy bản mới trên cánh tay thật? Nhóm đơn giản hóa mã ngay trong ngày để giải thích được trong một phút; chạy bản mới với cánh tay là bước đầu của việc tiếp theo. Test gồm những gì? Điều khiển 29, nhìn 15, camera 13, hiệu chỉnh 11, Serial 9, chương trình chính 8, success 7, độ bền 6, khớp mô hình 5, màn hình 4, đầu–cuối 2. Có bắt buộc dashboard IoT không? [...điền theo yêu cầu đề bài]; nếu có, nhóm sẽ thêm MQTT từ gói JSON hiện có.

Nguồn: 05_SO_LIEU_VA_NGUON.md mục 4, 6, 7, 8, 11, 13; lệnh .venv/bin/python -m pytest -q (109 passed, 03/11/2026).
""")


# ==============================================================================
# 04 · Success · hạn chế và việc tiếp theo
# ==============================================================================
def slide_limits(prs, n):
    s = new_slide(prs)
    header(s, "04 · Success · Hướng phát triển", "Hạn chế hiện tại và việc tiếp theo", "succ")
    pw = (CW - 0.3) / 2
    box(s, M, 1.95, pw, 3.95, fill=BG2)
    label(s, M + 0.28, 2.15, pw - 0.5, "Hạn chế", ORANGE, 10.5)
    bullets(s, M + 0.28, 2.55, pw - 0.5, 3.3, [
        "Vòng hở: XONG dựa trên góc lệnh, MG996R không báo vị trí thật",
        "Hiệu chỉnh gắn với một tờ giấy và một chỗ đặt robot",
        "Tay kẹp hai ngón phi tuyến, chưa giữ chắc cốc thon",
        "YOLO bản COCO chưa huấn luyện lại, hay gọi nhầm",
        "Chưa có tỉ lệ thành công, chưa đo nhiệt độ servo",
    ], 15, after=11, mark="—", mark_color=ORANGE, indent=0.3)
    x2 = M + pw + 0.3
    box(s, x2, 1.95, pw, 3.95, fill=TEAL_SOFT)
    label(s, x2 + 0.28, 2.15, pw - 0.5, "Việc tiếp theo", TEAL, 10.5)
    steps(s, x2 + 0.28, 2.58, pw - 0.5, [
        "Chạy bản mới trên cánh tay thật, đếm số lần XONG",
        "Dán ma sát lên hai ngón hoặc dùng vật thân thẳng, rồi mới tính kẹp vào success",
        "Hiệu chỉnh lại cho tờ giấy mới bằng arm_fit.py",
        "Đo đầu kẹp bằng camera để có vòng kín, thay vì tin góc lệnh",
        "Dashboard IoT (MQTT) từ gói JSON sẵn có, nếu đề bài yêu cầu",
    ], 14.5, d=0.32, gap=0.15)
    rule(s, M, 6.12, CW)
    label(s, M, 6.27, 2.7, "Hai lỗi tích hợp đã sửa", TEXT2, 10)
    bullets(s, 3.55, 6.24, W - M - 3.55, 0.6, [
        "Thứ tự camera trên macOS đổi giữa các lần chạy → tìm camera theo tên",
        "Arduino Uno tự reset khi cổng USB bị mở lại → giữ một kết nối duy nhất",
    ], 12, after=1, indent=0.2)
    footer(s, n)
    notes(s, """
Từ đó nhóm thấy năm hạn chế. Lớn nhất là vòng hở: chữ XONG dựa trên góc Arduino đã ra lệnh, vì MG996R không báo vị trí thật. Hiệu chỉnh gắn với một tờ giấy và một chỗ đặt robot. Tay kẹp chưa giữ chắc cốc thon. YOLO bản COCO hay gọi nhầm. Và chưa có tỉ lệ thành công, chưa đo nhiệt độ servo.

Việc tiếp theo, theo thứ tự: chạy bản mới trên cánh tay thật và đếm số lần XONG; dán ma sát lên hai ngón hoặc dùng vật thân thẳng, rồi mới tính kẹp vào success; hiệu chỉnh lại cho tờ giấy mới; đo đầu kẹp bằng camera để có vòng kín; và thêm dashboard IoT qua MQTT nếu đề bài yêu cầu.

Dòng dưới là hai lỗi tích hợp khó thấy nhóm đã sửa: thứ tự camera trên macOS đổi giữa các lần chạy, nên nhóm tìm camera theo tên; và Arduino Uno tự reset mỗi khi cổng USB bị mở lại, nên chương trình giữ một kết nối duy nhất và báo khi Arduino vừa reset.

Nếu được hỏi: chương trình phát hiện Arduino reset thế nào? Gói JSON có thời gian chạy t; t quay về gần không là Arduino vừa khởi động lại, màn hình báo ARDUINO VUA RESET. Vì sao camera đổi thứ tự? OpenCV đánh số camera theo uniqueID, còn danh sách của hệ điều hành xếp camera dùng gần nhất lên đầu. Đo đầu kẹp bằng camera thế nào? Ví dụ dán mã ArUco lên càng kẹp và dùng chính homography của tờ giấy; đây là hướng đề xuất, chưa làm. Có làm tự động không? Về kỹ thuật là gửi phím theo Plan; nhóm chỉ nên làm lại khi đo được độ lệch còn lại.

Nguồn: 05_SO_LIEU_VA_NGUON.md mục 4, 6, 8, 9, 10, 13; cameras.py:4-12,75-115; control.py (ArduinoSerialLink: mở lại cổng, phát hiện reset); README.md mục 5 và 6.
""")


# ==============================================================================
# Tóm lại + hỏi đáp
# ==============================================================================
def slide_summary(prs, n):
    s = new_slide(prs)
    label(s, M, 0.6, 6.0, "Tóm lại", TEAL)
    for i, st in enumerate(["Hai camera biến tờ A4 thành thước đo bằng cm.",
                            "Khối điều khiển biến vị trí vật thành phím cần bấm.",
                            "Khối success báo ba servo đã tới góc gợi ý chưa."]):
        y = 1.1 + i * 0.95
        rule(s, M, y, CW)
        dot(s, M, y + 0.24, i + 1, d=0.46, size=16)
        text(s, M + 0.7, y + 0.12, CW - 0.7, 0.7, st, 27, INK, True, anchor=MIDDLE)
    rule(s, M, 1.1 + 3 * 0.95, CW)
    for i, (k, v) in enumerate([("Mã nguồn", "github.com/DuongNAD/Project_IoT"), ("Video demo", "[...]")]):
        x = M + i * ((CW + 0.25) / 2)
        box(s, x, 4.25, (CW - 0.25) / 2, 0.72, fill=BG2)
        text(s, x + 0.25, 4.25, 1.6, 0.72, k.upper(), 10.5, TEXT2, True, anchor=MIDDLE, spc=150)
        text(s, x + 1.9, 4.25, (CW - 0.25) / 2 - 2.0, 0.72, v, 15, INK, True, anchor=MIDDLE)
    box(s, M, 5.25, CW, 1.45, fill=TEAL_SOFT)
    text(s, M, 5.42, CW, 0.6, "Nhóm em cảm ơn thầy cô và các bạn đã lắng nghe!", 26, TEAL, True, align=CENTER)
    text(s, M, 6.1, CW, 0.4, "  ·  ".join(name(k) for k in ("hw", "cv", "ctrl", "succ")) + "  ·  hỏi đáp", 13, TEXT2,
         align=CENTER)
    footer(s, n)
    notes(s, """
Tóm lại trong ba câu. Hai camera biến tờ giấy A4 thành thước đo bằng xăng-ti-mét. Khối điều khiển biến vị trí vật thành phím cần bấm. Và khối success báo ba servo đã tới góc gợi ý chưa.

Nhóm không cho rằng hệ thống đã hoàn hảo: những điều chưa kiểm chứng ở phần kết quả là thật. Nhưng mỗi người trong nhóm hiểu phần mình làm, mã đủ ngắn để giải thích trong một phút, và có thể sửa bất kỳ phần nào ngay tại đây. Mã nguồn ở GitHub theo đường dẫn trên slide.

Nếu thầy cô muốn, nhóm demo trực tiếp: [...điền kịch bản demo 2–3 phút].

Nhóm em cảm ơn thầy cô và các bạn, và xin nhận câu hỏi; câu hỏi phần nào thì bạn phụ trách phần đó trả lời.

Nếu được hỏi: việc nào làm trước? Chạy bản mới trên cánh tay thật để có số lần XONG đầu tiên, vì đó là chỗ còn thiếu bằng chứng nhất.

Nguồn: README.md; 05_SO_LIEU_VA_NGUON.md mục 4 đến 8.
""")


ORDER = [  # (khóa, hàm dựng, người nói: None = cả nhóm)
    ("cover", slide_cover, None),
    ("team", slide_team, None),
    ("problem", slide_problem, "hw"),
    ("system", slide_system, "hw"),
    ("div_hw", lambda p, n: slide_divider(p, n, "hw"), "hw"),
    ("parts", slide_parts, "hw"),
    ("comp1", slide_comp1, "hw"),
    ("comp2", slide_comp2, "hw"),
    ("circuit", slide_circuit, "hw"),
    ("heat", slide_heat, "hw"),
    ("div_cv", lambda p, n: slide_divider(p, n, "cv"), "cv"),
    ("a4", slide_a4, "cv"),
    ("objects", slide_objects, "cv"),
    ("div_ctrl", lambda p, n: slide_divider(p, n, "ctrl"), "ctrl"),
    ("flow", slide_flow, "ctrl"),
    ("fwcode", slide_fwcode, "ctrl"),
    ("ik", slide_ik, "ctrl"),
    ("screen", slide_screen, "ctrl"),
    ("calib", slide_calib, "ctrl"),
    ("div_succ", lambda p, n: slide_divider(p, n, "succ"), "succ"),
    ("success", slide_success, "succ"),
    ("trial", slide_trial, "succ"),
    ("results", slide_results, "succ"),
    ("limits", slide_limits, "succ"),
    ("summary", slide_summary, None),
]
TOTAL = len(ORDER)


def spoken_words(slide):
    """Số từ phần lời nói (trước đoạn "Nếu được hỏi") trong ghi chú của một slide."""
    return len(slide.notes_slide.notes_text_frame.text.split("Nếu được hỏi")[0].split())


def fill_team_slots(prs):
    """Điền "Slide a–b · ≈ N phút" của từng người trên slide nhóm (≈ 225 từ / phút khi đọc ghi chú)."""
    for key, tb in SLOT_BOXES.items():
        nums = [i for i, (_k, _f, owner) in enumerate(ORDER, 1) if owner == key]
        words = sum(spoken_words(prs.slides[i - 1]) for i in nums)
        minutes = max(1, round(words / 225))
        tb.text_frame.paragraphs[0].runs[0].text = f"Slide {nums[0]}–{nums[-1]} · ≈ {minutes} phút"


# ==============================================================================
def repack_like_powerpoint(path):
    """
    Đóng gói lại tệp như PowerPoint: mục zip kiểu FAT, không kèm quyền Unix (Python trên macOS / Linux ghi quyền 0600
    mà không có cờ "tệp thường"). Chỉ để phòng xa: lỗi Keynote "Định dạng tệp không hợp lệ" ngày 03/11/2026 không do việc này
    mà hết khi bỏ connector (xem line) và thêm notesMasterIdLst (xem add_notes_master_id).
    """
    tmp = path + ".tmp"
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            zi.create_system, zi.external_attr, zi.compress_type = 0, 0, zipfile.ZIP_DEFLATED
            zout.writestr(zi, zin.read(info.filename))
    os.replace(tmp, path)


def add_notes_master_id(prs):
    """python-pptx tạo notes master khi thêm ghi chú nhưng không ghi <p:notesMasterIdLst> vào presentation.xml như chuẩn yêu cầu."""
    pres = prs.part._element
    if pres.find(qn("p:notesMasterIdLst")) is not None:
        return
    rid = prs.part.relate_to(prs.part.notes_master_part, RT.NOTES_MASTER)
    lst = etree.Element(qn("p:notesMasterIdLst"))
    etree.SubElement(lst, qn("p:notesMasterId")).set(qn("r:id"), rid)
    pres.find(qn("p:sldMasterIdLst")).addnext(lst)


def build(out_path=OUT_PPTX):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)  # 16:9 đúng số của PowerPoint (13,333 x 7,5 in)
    prs._element.sldSz.attrib.pop("type", None)  # Mẫu mặc định ghi type="screen4x3" dù khổ đã đổi sang 16:9
    for n, (_key, make, _owner) in enumerate(ORDER, 1):
        make(prs, n)
    assert len(prs.slides) == TOTAL
    fill_team_slots(prs)
    add_notes_master_id(prs)
    props = prs.core_properties  # Mẫu mặc định của python-pptx ghi người sửa "Steve Canny", ngày tạo 2013
    props.title = "Hệ thống hỗ trợ gắp vật cho cánh tay robot 4 bậc tự do bằng thị giác máy tính"
    props.subject = "Đồ án IoT: hai camera chỉ bấm phím nào, mấy lần; success kiểm ba góc servo"
    props.last_modified_by = "build_slides.py"
    props.created = props.modified = datetime.now().replace(microsecond=0)
    prs.save(out_path)
    repack_like_powerpoint(out_path)
    missing = sorted({n for n in REQUIRED_IMAGES if not os.path.exists(os.path.join(REAL_DIR, n))})
    print(f"Đã lưu {out_path} ({len(prs.slides)} slide)")
    if missing:
        print(f"⚠️ Thiếu {len(missing)} ảnh trong {REAL_DIR} (slide hiện khung '[Ảnh: ...]'): {', '.join(missing)}")
    return out_path


REQUIRED_IMAGES = [
    "demo_06_grip_side.jpg", "demo_06_grip_top.jpg", "demo_07_carry_side.jpg", "demo_07_carry_top.jpg",
    "demo_08_place_side.jpg", "demo_08_place_top.jpg", "hw_electronics.jpg", "sw_annot_top.jpg", "sw_annot_side.jpg",
    "ui_guide_cameras.png", "ui_screen_before.png", "ui_screen_done.png", "calib_before_after_side.jpg",
]

if __name__ == "__main__":
    build()
