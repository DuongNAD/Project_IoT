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
    "ctrl": ("03", "Code điều khiển", ["flow", "fwcode", "ik", "screen", "remote", "calib"]),
    "succ": ("04", "Success", ["success", "trial", "results", "limits"]),
}
TITLES = {
    "parts": "Danh sách linh kiện", "comp1": "Arduino Uno R3 và PCA9685", "comp2": "Servo, nguồn, HC-05, camera",
    "circuit": "Sơ đồ mạch", "heat": "Bảo vệ servo kẹp", "a4": "Hệ tọa độ từ tờ A4", "objects": "Nhận diện vật",
    "flow": "Lưu đồ thuật toán", "fwcode": "Code firmware", "ik": "Động học ngược", "screen": "Giao diện chương trình",
    "remote": "Điều khiển từ xa",
    "calib": "Hiệu chỉnh mô hình", "success": "Điều kiện hoàn thành", "trial": "Thử nghiệm trên cánh tay thật",
    "results": "Kết quả", "limits": "Hạn chế, hướng phát triển",
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
    caption(s, 7.35, 7.0, 5.3, "Ảnh từ hai camera của hệ thống · 02/11/2026", 10, 0.3)
    label(s, M, 1.0, 5.8, "Đồ án IoT · [Môn học] · [Ngày báo cáo]", TEAL)
    text(s, M, 1.42, 5.8, 2.0, "Hệ thống hỗ trợ gắp vật cho cánh tay robot 4 bậc tự do bằng thị giác máy tính",
         30, INK, True, spacing=1.05)
    text(s, M, 3.5, 5.6, 1.0, "Hai camera · gợi ý phím bấm · kiểm tra góc servo",
         16, TEXT2, spacing=1.15)
    label(s, M, 4.82, 5.8, "Nhóm thực hiện", MUTED, 10)
    for i, key in enumerate(("hw", "cv", "ctrl", "succ")):
        x, y = M + (i % 2) * 2.95, 5.18 + (i // 2) * 0.66
        text(s, x, y, 2.85, 0.6, [[(name(key), {"bold": True, "size": 14})],
                                  [(TEAM[key][1], {"color": TEXT2, "size": 11})]], 14, INK, spacing=1.05)
    text(s, M, 6.62, 5.8, 0.3, "Giảng viên hướng dẫn: [...] · Lớp: [...]", 11, MUTED)
    notes(s, """
Em chào thầy cô và các bạn. Nhóm em gồm bốn thành viên, xin trình bày đề tài: hệ thống hỗ trợ gắp vật cho cánh tay robot bốn bậc tự do bằng thị giác máy tính. Hai camera xác định vị trí vật; chương trình gợi ý phím cần bấm và kiểm tra ba servo đã tới góc gợi ý hay chưa.

Hai ảnh bên phải được chụp từ hai camera của hệ thống trong buổi thử ngày 2/11.

Nếu được hỏi: vì sao chọn đề tài này? [...điền lý do của nhóm].

Nguồn: ảnh demo_06_grip_side, demo_06_grip_top (khung cắt từ video buổi thử 02/11/2026, 20:32:52).
""")


# ==============================================================================
# Nhóm 4 người và phân công
# ==============================================================================
def slide_team(prs, n):
    s = new_slide(prs, alt=True)
    header(s, "Nhóm 4 người", "Thành viên và phân công")
    members = [
        ("hw", ORANGE, "Linh kiện, sơ đồ mạch, lắp ráp cánh tay và camera",
         "Arduino Uno · PCA9685 · MG996R"),
        ("cv", TEAL, "Hệ tọa độ từ tờ A4, nhận diện vật", "vision.py · cameras.py"),
        ("ctrl", TEAL, "Firmware Arduino, động học ngược, lệnh bấm phím, hiệu chỉnh",
         "robot_arm_4dof.ino · control.py"),
        ("succ", TEAL, "Điều kiện hoàn thành, giao diện, kiểm thử",
         "success.py · screen.py · tests/"),
    ]
    cw, gap = (CW - 3 * 0.25) / 4, 0.25
    for i, (key, col, desc, files) in enumerate(members):
        x = M + i * (cw + gap)
        box(s, x, 1.95, cw, 3.85, fill=CARD)
        box(s, x, 1.95, cw, 0.07, fill=col)
        label(s, x + 0.22, 2.22, cw - 0.4, f"{SECTIONS[key][0]} · {TEAM[key][1]}", col, 10.5)
        text(s, x + 0.22, 2.55, cw - 0.4, 0.4, name(key), 18, INK, True)
        text(s, x + 0.22, 3.1, cw - 0.4, 1.6, desc, 14, TEXT2, spacing=1.12)
        text(s, x + 0.22, 4.78, cw - 0.4, 0.5, files, 10.5, TEAL if col == TEAL else ORANGE, font=MONO if col == TEAL else FONT,
             spacing=1.05)
        rule(s, x + 0.22, 5.3, cw - 0.44)
        SLOT_BOXES[key] = text(s, x + 0.22, 5.4, cw - 0.4, 0.3, "…", 11, MUTED)
    text(s, M, 6.15, CW, 0.4, [[("Thứ tự trình bày:  ", {"color": TEXT2}),
                                ("phần cứng  →  computer vision  →  điều khiển  →  success", {"color": INK, "bold": True})]], 14)
    footer(s, n)
    notes(s, """
Nhóm có bốn thành viên. {hw} phụ trách linh kiện, sơ đồ mạch và lắp ráp. {cv} phụ trách computer vision: hệ tọa độ từ tờ A4 và nhận diện vật. {ctrl} phụ trách firmware Arduino và code điều khiển trên laptop. {succ} phụ trách khối success, giao diện và kiểm thử; {cv} và {succ} cùng thực hiện hai phần này.

Bài trình bày đi theo luồng dữ liệu: phần cứng, computer vision, điều khiển, success. Mở đầu, {hw} trình bày bài toán, sơ đồ khối và phần linh kiện.

Nếu được hỏi: ai làm firmware? {ctrl}. Phần success và computer vision chia thế nào? Hai bạn làm chung; khi trình bày, {cv} nói phần computer vision, {succ} nói phần success.

Nguồn: README.md (các khối của mã); phân công do nhóm tự khai.
""")


# ==============================================================================
# Mở đầu · Bài toán
# ==============================================================================
def slide_problem(prs, n):
    s = new_slide(prs)
    header(s, "Mở đầu", "Bài toán", "hw")
    label(s, M, 1.95, 7.2, "Ba câu hỏi khi điều khiển bằng bàn phím")
    rows = [("Vật ở đâu trên bàn?", "02 · COMPUTER VISION"),
            ("Bấm phím nào, bao nhiêu lần?", "03 · ĐIỀU KHIỂN"),
            ("Đã tới đúng góc chưa?", "04 · SUCCESS")]
    for i, (q, who) in enumerate(rows):
        y = 2.45 + i * 1.12
        rule(s, M, y, 7.2)
        dot(s, M, y + 0.26, i + 1, d=0.42, size=15)
        text(s, M + 0.65, y + 0.24, 6.55, 0.45, q, 19, INK)
        chip(s, M + 0.65, y + 0.7, who)
    rule(s, M, 2.45 + 3 * 1.12, 7.2)
    box(s, 8.35, 1.95, W - M - 8.35, 3.86, fill=ORANGE_SOFT)
    label(s, 8.65, 2.2, 3.8, "Khó khăn", ORANGE)
    text(s, 8.65, 2.65, 3.75, 1.9, ["Mỗi phím chỉ quay 2°", "Khó ước lượng độ sâu bằng mắt",
                                   "Cần mô hình khớp cánh tay thật"], 16, INK, spacing=1.15, after=10)
    text(s, 8.65, 4.62, 3.75, 0.3, f"VÍ DỤ Ở SLIDE {num('ik')}", 10, ORANGE, True, spc=100)
    keycap(s, 8.65, 4.98, "D", 0.4, 0.38, 15)
    text(s, 9.1, 4.98, 0.5, 0.38, "× 8", 15, INK, True, anchor=MIDDLE)
    keycap(s, 9.7, 4.98, "S", 0.4, 0.38, 15)
    text(s, 10.15, 4.98, 0.65, 0.38, "× 16", 15, INK, True, anchor=MIDDLE)
    text(s, 10.85, 4.98, 1.6, 0.38, "= 24 lần bấm", 15, ORANGE, True, anchor=MIDDLE)
    text(s, M, 6.25, CW, 0.45, [[("Hệ thống gợi ý; ", {"color": INK}),
                                ("người dùng bấm phím.", {"color": TEAL, "bold": True})]], 18)
    footer(s, n)
    notes(s, """
Em là {hw}, phụ trách linh kiện. Em xin mở đầu bằng bài toán.

Cánh tay có bốn servo, điều khiển bằng bàn phím; mỗi lần bấm, một servo quay 2 độ. Người điều khiển cần biết ba điều: vật ở đâu, cần bấm phím nào và bao nhiêu lần, và cánh tay đã tới đúng góc chưa.

Khó khăn là mắt người khó ước lượng độ sâu, và mỗi bước chỉ 2 độ nên một lần tiếp cận có thể cần hơn 20 lần bấm, như ví dụ 24 lần ở phần điều khiển. Ngoài ra, gợi ý chỉ chính xác khi mô hình hình học khớp với cánh tay thật.

Hệ thống giải quyết ba câu hỏi bằng ba khối: computer vision, điều khiển và success. Hệ thống chỉ gợi ý; người dùng là người bấm phím.

Nếu được hỏi: vì sao không để chương trình tự điều khiển? Mô hình hình học hiện chỉ khớp cánh tay thật ở mức khoảng 1 cm và tay kẹp chưa giữ chắc vật thon, nên nhóm chọn hướng hỗ trợ người điều khiển. Bản trước có chế độ tự gửi phím; nhóm đã bỏ để mã nguồn đơn giản hơn.

Nguồn: README.md mục 3; control.py; success.py.
""")


# ==============================================================================
# Mở đầu · Hệ thống (sơ đồ khối)
# ==============================================================================
def slide_system(prs, n):
    s = new_slide(prs)
    header(s, "Mở đầu", "Sơ đồ khối hệ thống", "hw")
    gap, y, h = 0.5, 2.2, 1.5
    w = (CW - 4 * gap) / 5
    blocks = [
        ("CẢM BIẾN", "Hai camera", "OBSBOT (trên), MacBook (ngang)", None, False),
        ("NHÌN · vision.py", "Tìm vật", ["ArUco, tách màu", "→ (X, Y) cm"], "02", False),
        ("ĐIỀU KHIỂN · control.py", "Điều khiển", ["góc 3 servo", "→ phím cần bấm"], "03", True),
        ("SUCCESS · success.py", "Success", "kiểm tra góc 3 servo", "04", True),
        ("MÀN HÌNH · screen.py", "Hiển thị", "lệnh bấm, kết quả", None, False),
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
    text(s, lx + 0.4, top - 0.29, rx - lx - 0.8, 0.27, "người dùng bấm phím", 11, ORANGE, align=CENTER)
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
    text(s, cx + 0.43, y + h + 0.1, 2.4, 0.5, ["JSON ~5 gói/giây"], 10.5, ORANGE, spacing=1.0)
    box(s, M, hy, 4.45, hh, fill=TEAL_SOFT)
    label(s, M + 0.2, hy + 0.12, 4.1, "Plan nối hai khối", TEAL, 10)
    text(s, M + 0.2, hy + 0.42, 4.1, 0.55, "Góc hiện tại, góc cần tới, lệnh bấm. Khối điều khiển tạo, khối success đọc.",
         12, INK, spacing=1.05)
    box(s, M, 5.62, CW, 1.0, fill=BG2)
    code = [("plan   = self.control.update(self.tracker.objects)", "# khối điều khiển"),
            ("result = self.success.update(plan)", "# khối success"),
            ("screen = build_screen(..., plan, result)", "# màn hình (main.py:194-197)")]
    text(s, M + 0.25, 5.74, CW - 0.4, 0.85, [[(c.ljust(53), {}), (k, {"color": MUTED})] for c, k in code], 12.5, INK, font=MONO,
         spacing=1.12)
    footer(s, n)
    notes(s, """
Đây là sơ đồ khối của hệ thống, đọc từ trái sang phải; số trên mỗi khối là phần trình bày tương ứng.

Hai camera cùng quan sát tờ A4: OBSBOT đặt phía trên để tính vị trí vật, camera MacBook đặt phía trước để quan sát độ cao của tay kẹp. Khối computer vision dò bốn mã ArUco để đổi pixel sang xăng-ti-mét, rồi tách màu để xác định vị trí X, Y của vật.

Khối điều khiển tính góc cần tới của ba servo và lập danh sách phím cần bấm. Khối success kiểm tra ba servo đã tới các góc đó chưa. Hai khối trao đổi qua một đối tượng duy nhất là Plan, nên có thể phát triển và kiểm thử riêng. Ba dòng mã bên dưới là phần chương trình chạy ở mỗi khung hình.

Người dùng bấm phím theo gợi ý. Phím được gửi xuống Arduino qua USB ở 9600 baud; Arduino điều khiển bốn servo qua PCA9685 và gửi lại gói JSON chứa bốn góc servo, khoảng 5 gói mỗi giây. Phần cứng này là phần một, em trình bày tiếp theo.

Nếu được hỏi: chương trình có tự gửi phím không? Không, chỉ gửi khi người dùng bấm. Vì sao trong code gọi là nhóm 1, nhóm 2? Đó là tên hai khối trong mã nguồn (control.py, success.py). Có dùng Bluetooth không? Có, khi điều khiển từ xa: máy Dell gửi phím qua module HC-05 ở chân D2, D3 (slide Điều khiển từ xa); laptop đặt cạnh cánh tay vẫn dùng cáp USB.

Nguồn: README.md (sơ đồ đầu trang, mục 1 và 3); main.py:194-197; robot_arm_4dof.ino:6,8,86,203-207; control.py (ArduinoSerialLink).
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
    row = min(0.68, 3.6 / len(keys))  # 5 mục cao 0,68 inch; nhiều mục hơn thì co lại cho vừa thẻ
    for i, k in enumerate(keys):
        y = 2.0 + i * row
        rule(s, 8.05, y, W - M - 8.35)
        text(s, 8.05, y + row / 2 - 0.18, 0.7, 0.4, str(num(k)), 16, col, True)
        text(s, 8.75, y + row / 2 - 0.18, W - M - 9.1, 0.4, TITLES[k], 16, INK)
    rule(s, 8.05, 2.0 + len(keys) * row, W - M - 8.35)
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
        "hw": "Tiếp theo là phần linh kiện, gồm: danh sách linh kiện, giới thiệu các linh kiện chính, sơ đồ mạch và giải pháp bảo vệ servo kẹp. Mỗi linh kiện được trình bày theo thông số và vai trò trong hệ thống.",
        "cv": "Em là {cv}, phụ trách computer vision cùng {succ}. Phần này xác định vị trí vật trên bàn theo xăng-ti-mét, gồm hai nội dung: hệ tọa độ từ tờ A4 với bốn mã ArUco, và nhận diện vật.",
        "ctrl": "Em là {ctrl}, phụ trách code điều khiển: firmware trên Arduino và khối điều khiển trên laptop. Phần này gồm lưu đồ thuật toán, code firmware, động học ngược, giao diện chương trình, điều khiển từ xa và hiệu chỉnh mô hình cánh tay.",
        "succ": "Em là {succ}, phụ trách khối success cùng {cv}. Phần cuối gồm điều kiện hoàn thành, thử nghiệm trên cánh tay thật, kết quả, hạn chế và hướng phát triển.",
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
        ("Arduino Uno R3", "1", "Vi điều khiển chính"),
        ("Mạch PCA9685 (16 kênh PWM)", "1", "Tạo xung PWM cho servo"),
        ("Servo MG996R", "4", "Đế, vai, khuỷu, kẹp"),
        ("Nguồn tổ ong 5–6 V", "1", "Cấp nguồn cho servo"),
        ("Module Bluetooth HC-05", "1", "Nhận phím từ máy Dell"),
        ("Khung cánh tay 4 bậc tự do, tay kẹp", "1", "Cơ khí"),
        ("Camera OBSBOT Meet SE", "1", "Camera phía trên"),
        ("Camera MacBook (có sẵn)", "1", "Camera phía trước"),
        ("Tờ A4 in 4 mã ArUco", "1", "Hệ tọa độ (cm)"),
        ("Laptop, cáp USB, dây cắm", "—", "Chạy chương trình, cấp nguồn Arduino"),
    ]
    cols = [(M, 0.45, "#"), (M + 0.45, 4.55, "LINH KIỆN"), (M + 5.0, 0.7, "SL"), (M + 5.7, CW - 5.7, "VAI TRÒ")]
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
Đây là danh sách linh kiện. Arduino Uno R3 là vi điều khiển chính: nhận phím từ laptop và điều khiển mạch PCA9685. PCA9685 tạo xung PWM cho bốn servo MG996R ở đế, vai, khuỷu và kẹp. Nguồn tổ ong 5–6 V cấp riêng cho servo. Module HC-05 nhận phím qua Bluetooth khi điều khiển từ xa bằng máy Dell. Phần quan sát gồm camera OBSBOT phía trên, camera MacBook phía trước và tờ A4 in bốn mã ArUco. Laptop chạy chương trình Python và cấp nguồn cho Arduino qua USB.

Nếu được hỏi: mua linh kiện ở đâu, giá bao nhiêu? [...điền nếu thầy cô hỏi]. Khung cánh tay làm bằng vật liệu gì? [...điền].

Nguồn: README.md mục 1; robot_arm_4dof/robot_arm_4dof.ino:1-8,86-90; robot_arm_4dof/flash.sh:19 (arduino:avr:uno); cameras.py.
""")


# ==============================================================================
# 01 · Linh kiện · giới thiệu (1): ảnh mạch thật đánh số, Arduino Uno R3 và PCA9685
# ==============================================================================
HW_PHOTO_MARKS = [  # (số, x, y tương đối trong ảnh hw_electronics.jpg 800 x 678, tên ngắn cho chú thích)
    (1, 0.27, 0.65, "Arduino"), (2, 0.27, 0.885, "PCA9685"), (3, 0.44, 0.69, "HC-05"),
    (4, 0.30, 0.25, "Nguồn tổ ong"), (5, 0.62, 0.45, "Servo đế"),
]


def slide_comp1(prs, n):
    s = new_slide(prs)
    header(s, "01 · Linh kiện", "Arduino Uno R3 và PCA9685", "hw")
    pw = 4.95
    ph = image(s, "hw_electronics.jpg", M, 1.98, pw, None, mode="fit")
    for k, fx, fy, _nm in HW_PHOTO_MARKS:
        dot(s, M + fx * pw - 0.19, 1.98 + fy * ph - 0.19, k, ORANGE, d=0.38, size=13)
    caption(s, M, 1.98 + ph + 0.12, pw, " · ".join(f"({k}) {nm}" for k, _x, _y, nm in HW_PHOTO_MARKS), 10, 0.3)
    rx, rw = 6.35, W - M - 6.35
    blocks = [
        (1, "Arduino Uno R3", "ATmega328P · 16 MHz · 14 chân số, 6 analog · 5 V",
         "Nhận phím (USB / HC-05), điều khiển PCA9685 qua I²C, gửi trạng thái mỗi 200 ms"),
        (2, "Mạch PCA9685", "16 kênh PWM 12 bit · I²C 0x40 · 50 Hz",
         "Kênh 0–3 → 4 servo; nguồn servo vào cổng V+"),
    ]
    y, line_h = 1.98, 14 * 1.2 * 1.08 / 72
    for k, nm, spec, role in blocks:
        h_spec = n_lines(spec, 14, rw - 0.55) * line_h
        h_role = n_lines(role, 14, rw - 0.55) * line_h
        rule(s, rx, y, rw)
        dot(s, rx, y + 0.18, k, ORANGE, d=0.36, size=13)
        text(s, rx + 0.5, y + 0.16, rw - 0.5, 0.38, nm, 18, INK, True)
        text(s, rx + 0.5, y + 0.62, rw - 0.5, 0.3, "THÔNG SỐ", 10, MUTED, True, spc=150)
        text(s, rx + 0.5, y + 0.88, rw - 0.5, h_spec + 0.05, spec, 14, TEXT2, spacing=1.08)
        yr = y + 0.88 + h_spec + 0.14
        text(s, rx + 0.5, yr, rw - 0.5, 0.3, "VAI TRÒ", 10, TEAL, True, spc=150)
        text(s, rx + 0.5, yr + 0.26, rw - 0.5, h_role + 0.05, role, 14, INK, spacing=1.08)
        y = yr + 0.26 + h_role + 0.3
    footer(s, n)
    notes(s, """
Ảnh bên trái là mạch của nhóm, các linh kiện được đánh số: (1) Arduino Uno R3, (2) PCA9685, (3) HC-05, (4) nguồn tổ ong, (5) servo MG996R ở đế.

Arduino Uno R3 dùng vi điều khiển ATmega328P, 16 MHz, 14 chân số và 6 chân analog, cấp nguồn 5 V qua USB. Trong hệ thống, Arduino nhận phím từ laptop qua USB ở 9600 baud hoặc từ HC-05, giới hạn góc servo, gửi lệnh cho PCA9685 qua I²C, và gửi gói JSON chứa bốn góc servo mỗi 200 ms.

PCA9685 là mạch 16 kênh PWM 12 bit, giao tiếp I²C ở địa chỉ 0x40, đặt tần số 50 Hz cho servo. Kênh 0 đến 3 nối với đế, vai, khuỷu và kẹp; góc 0–180 độ được đổi thành độ rộng xung 125–575 trên thang 4096. Nguồn servo cấp vào cổng V+ của mạch.

Nếu được hỏi: vì sao dùng PCA9685 thay vì nối servo trực tiếp vào Arduino? PCA9685 tạo xung cho nhiều servo cùng lúc và có cổng nguồn riêng cho servo; Arduino chỉ cần gửi lệnh qua hai dây I²C.

Nguồn: robot_arm_4dof.ino:1-12,41-45,86-90 (Wire, Adafruit_PWMServoDriver 0x40, setPWMFreq 50, SERVOMIN 125, SERVOMAX 575); README.md mục 1; thông số Arduino Uno R3 theo trang sản phẩm của Arduino; ảnh hw_electronics.
""")


# ==============================================================================
# 01 · Linh kiện · giới thiệu (2): servo, nguồn, HC-05, camera
# ==============================================================================
def slide_comp2(prs, n):
    s = new_slide(prs, alt=True)
    header(s, "01 · Linh kiện", "Servo, nguồn, HC-05 và camera", "hw")
    cards = [
        ("Servo MG996R × 4", "Bánh răng kim loại · 0–180° · xung 0,5–2,5 ms",
         "Đế, vai, khuỷu, kẹp · mỗi phím 2° (kẹp 5°)", True),
        ("Nguồn tổ ong 5–6 V", "Nguồn xung 5–6 V",
         "Cấp riêng cho servo qua PCA9685 · chung GND", False),
        ("Module Bluetooth HC-05", "Bluetooth SPP · UART 9600 baud",
         "Nối D2, D3 · nhận phím từ máy Dell", False),
        ("Hai camera 1920 × 1080", "OBSBOT Meet SE (trên) · camera MacBook (ngang)",
         "Cùng quan sát tờ A4 có 4 mã ArUco", False),
    ]
    cw, ch = (CW - 0.25) / 2, 2.27
    for i, (nm, spec, role, keys) in enumerate(cards):
        x, y = M + (i % 2) * (cw + 0.25), 1.95 + (i // 2) * (ch + 0.2)
        box(s, x, y, cw, ch, fill=CARD)
        box(s, x, y, 0.07, ch, fill=ORANGE)
        text(s, x + 0.3, y + 0.18, cw - 0.5, 0.36, nm, 17, INK, True)
        text(s, x + 0.3, y + 0.62, cw - 0.5, 0.5, spec, 13, TEXT2, spacing=1.06)
        text(s, x + 0.3, y + 1.12, cw - 0.5, 0.6, role, 15, INK, spacing=1.08)
        if keys:
            kx = x + 0.3
            for pair in ("A D", "W S", "I K", "J L"):
                for ch_ in pair.split():
                    keycap(s, kx, y + 1.78, ch_, 0.34, 0.32, 12)
                    kx += 0.39
                kx += 0.18
    footer(s, n)
    notes(s, """
Tiếp theo là các linh kiện còn lại. Bốn servo MG996R dùng bánh răng kim loại, góc quay 0–180 độ, độ rộng xung 0,5–2,5 ms. Mỗi lần bấm, đế, vai và khuỷu quay 2 độ, kẹp quay 5 độ; tám phím bên dưới là cặp phím của từng servo. Servo này không phản hồi vị trí, nên trạng thái XONG ở phần success dựa trên góc đã ra lệnh.

Nguồn tổ ong 5–6 V cấp riêng cho servo qua cổng V+ của PCA9685, vì servo tiêu thụ dòng lớn; GND được nối chung.

HC-05 là module Bluetooth nối chân D2, D3 của Arduino. Firmware nhận phím từ HC-05 giống như từ USB. Khi điều khiển từ xa, máy Dell gửi phím qua HC-05, còn Mac vẫn nhận góc servo qua USB.

Hai camera có độ phân giải 1920 × 1080: OBSBOT Meet SE đặt phía trên để tính vị trí vật, camera MacBook đặt phía trước để quan sát độ cao tay kẹp.

Nếu được hỏi: mô-men xoắn của MG996R là bao nhiêu? Theo datasheet khoảng 10 kg·cm ở 6 V; nhóm chưa đo. Vì sao không dùng servo có phản hồi vị trí? Ngoài phạm vi linh kiện hiện có; đây là một hướng phát triển.

Nguồn: robot_arm_4dof.ino:5-6,13-21,86-87,121-152; README.md mục 1; cameras.py; datasheet MG996R (dải xung).
""")


# ==============================================================================
# 01 · Linh kiện · sơ đồ mạch
# ==============================================================================
def slide_circuit(prs, n):
    s = new_slide(prs)
    header(s, "01 · Linh kiện", "Sơ đồ mạch", "hw")
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
    caption(s, M, 4.82, 2.3, "Cam NGANG: camera MacBook", 10, 0.45)
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
    block(px, 5.85, pw_, 0.75, "HC-05 (Bluetooth)", "TXD → D2 · RXD ← D3", fill=CARD, edge=INDIGO)
    for y_pin, x_turn, y_end, lab in ((4.45, 6.3, 6.07, "TXD → D2"), (4.85, 6.6, 6.38, "RXD ← D3")):
        line(s, ax + aw + 0.05, y_pin, x_turn, y_pin, INDIGO, 1.75)
        line(s, x_turn, y_pin, x_turn, y_end, INDIGO, 1.75)
        line(s, x_turn, y_end, px - 0.05, y_end, INDIGO, 1.75)
    # Chú giải
    legend = [(TEAL, "tín hiệu: I²C, xung servo"), (ORANGE, "nguồn servo 5–6 V"), (INK, "USB, 5 V logic"),
              (MUTED, "GND (nối chung)"), (INDIGO, "HC-05 (Bluetooth)")]
    for i, (col, lab) in enumerate(legend):
        y = 5.48 + i * 0.26
        box(s, M, y + 0.1, 0.3, 0.06, fill=col)
        text(s, M + 0.4, y, 2.5, 0.26, lab, 10, TEXT2)
    caption(s, 9.45, 5.85, W - M - 9.45, "Theo firmware và README; I²C của Arduino Uno: A4 (SDA), A5 (SCL).", 10, 0.75)
    footer(s, n)
    notes(s, """
Đây là sơ đồ đấu dây. Laptop nối Arduino qua USB ở 9600 baud: phím đi xuống, gói JSON đi lên; cáp này cũng cấp nguồn cho Arduino. Arduino nối PCA9685 bằng bốn dây: 5 V, GND, SDA ở chân A4 và SCL ở chân A5.

PCA9685 xuất xung ở kênh 0–3 cho bốn servo đế, vai, khuỷu và kẹp; mỗi servo có ba dây: tín hiệu, V+ và GND. Nguồn tổ ong 5–6 V cấp vào cổng V+ của PCA9685, chỉ dùng cho servo. HC-05 nối TXD vào D2 và RXD vào D3 của Arduino. Camera OBSBOT nối laptop qua USB. GND của Arduino, PCA9685 và nguồn servo được nối chung.

Nếu được hỏi: vì sao dùng A4 và A5? Đây là hai chân I²C (SDA, SCL) của Arduino Uno. Chân RXD của HC-05 có dùng cầu chia áp không? [...điền theo mạch thật]. Vì sao phải nối chung GND? Để tín hiệu xung và nguồn servo có cùng mức tham chiếu.

Nguồn: robot_arm_4dof.ino:1-8,86-90 (Wire, SoftwareSerial BT(2, 3), PCA9685 0x40); README.md mục 1 (nguồn riêng vào cổng xanh); ảnh hw_electronics.
""")


# ==============================================================================
# 01 · Linh kiện · sự cố servo kẹp nóng
# ==============================================================================
def slide_heat(prs, n):
    s = new_slide(prs)
    header(s, "01 · Linh kiện", "Bảo vệ servo kẹp khỏi quá nhiệt", "hw")
    box(s, M, 1.95, 4.85, 3.85, fill=ORANGE_SOFT)
    label(s, M + 0.28, 2.18, 4.3, "Nguyên nhân", ORANGE)
    steps(s, M + 0.28, 2.65, 4.3, [
        "Firmware cũ giữ xung liên tục",
        "Kẹp bị chặn, servo vẫn chịu tải",
        "Lệnh 175°: xung vượt mức 2,5 ms",
    ], 15, dot_color=ORANGE, d=0.36, gap=0.3)
    x2 = M + 4.85 + 0.3
    box(s, x2, 1.95, W - M - x2, 3.85, fill=TEAL_SOFT)
    label(s, x2 + 0.28, 2.18, 6.2, "Giải pháp trong firmware", TEAL)
    fixes = ["Giới hạn góc kẹp 160°, bước 5°",
             "Mở hết (95°), 5 s không có lệnh → ngắt xung",
             "Khép liên tục quá 60 s → ngắt xung",
             None,  # Hàng phím X / Z vẽ riêng
             "Giao diện báo trạng thái nghỉ"]
    for i, st in enumerate(fixes):
        y = 2.65 + i * 0.6
        dot(s, x2 + 0.28, y, i + 1, d=0.36, size=13)
        if st is None:
            keycap(s, x2 + 0.82, y - 0.03, "X", 0.42, 0.4, 15)
            text(s, x2 + 1.32, y - 0.03, 2.0, 0.4, "nghỉ kẹp", 15, INK, anchor=MIDDLE)
            keycap(s, x2 + 3.25, y - 0.03, "Z", 0.42, 0.4, 15)
            text(s, x2 + 3.75, y - 0.03, 2.6, 0.4, "nghỉ cả 4 servo", 15, INK, anchor=MIDDLE)
        else:
            text(s, x2 + 0.82, y + 0.02, W - M - x2 - 1.0, 0.4, st, 15, INK)
    chip(s, M, 6.1, "ĐÃ NẠP VÀ KIỂM TRA TRÊN MẠCH (02/11)", size=11, h=0.4)
    footer(s, n)
    notes(s, """
Phần cuối của linh kiện là bảo vệ servo kẹp khỏi quá nhiệt. Có hai nguyên nhân: firmware cũ giữ xung PWM liên tục, nên khi kẹp bị chặn servo vẫn chịu tải; và lệnh đóng 175 độ tương ứng xung khoảng 2,74 ms, vượt dải 0,5–2,5 ms của MG996R.

Firmware mới có các biện pháp: giới hạn góc kẹp 160 độ; mở hết mà 5 giây không có lệnh thì ngắt xung; khép liên tục quá 60 giây cũng ngắt xung; phím X cho servo kẹp nghỉ, phím Z cho cả bốn servo nghỉ; và giao diện hiển thị khi cánh tay đang nghỉ.

Firmware này đã được nạp và kiểm tra trên mạch ngày 2/11. Nhóm chưa đo nhiệt độ servo sau thay đổi.

Tiếp theo, {cv} trình bày phần computer vision.

Nếu được hỏi: dùng phím Z cần chú ý gì? Cả bốn servo mất xung nên cánh tay hạ xuống theo trọng lực; cần đưa tay kẹp xuống vị trí trống trước. Giới hạn 160 độ có vượt dải xung không? Có, xung khoảng 2,56 ms, hơi vượt dải danh định 2,5 ms; nhóm chấp nhận để kẹp chặt hơn, kèm cơ chế tự ngắt xung sau 60 giây. Vì sao khi ngắt xung lúc mở hết thì hàm kẹp khép lại? Khi mất xung, hai hàm kẹp khép thành hình chữ V hẹp, khe còn khoảng 1–2 cm (ước lượng từ ảnh), nên khi tiếp cận cần bấm J để mở lại.

Nguồn: robot_arm_4dof.ino:16-23,160-176,191-201; control.py (trạng thái relaxed, cảnh báo FIRMWARE CU KHONG CO PHIM Z); README.md mục 6; 05_SO_LIEU_VA_NGUON.md mục 6.
""")


# ==============================================================================
# 02 · Computer vision · tờ A4 thành hệ tọa độ
# ==============================================================================
def slide_a4(prs, n):
    s = new_slide(prs, alt=True)
    header(s, "02 · Computer vision", "Hệ tọa độ từ tờ A4 và mã ArUco", "cv")
    pw = (CW - 0.4) / 2
    ph = pw * 9 / 16 * 0.98
    image(s, "sw_annot_top.jpg", M, 1.95, pw, ph)
    image(s, "sw_annot_side.jpg", M + pw + 0.4, 1.95, pw, ph)
    caption(s, M, 1.95 + ph + 0.12, pw, "Cam TRÊN: lưới 5 cm; cốc ở X = 16,5 cm, Y = 13,8 cm", 10.5, 0.3)
    caption(s, M + pw + 0.4, 1.95 + ph + 0.12, pw, "Cam NGANG: cùng lưới tọa độ", 10.5, 0.3)
    cols = [("4 mã ở 4 góc", ["DICT_4X4_50 · ID 0–3", "cạnh 2,8 cm"]),
            ("Homography", "pixel ↔ cm, hai camera"),
            ("Khi mã bị che", "dùng vị trí đã lưu"),
            ("Bù thị sai", ["sai lệch 1,2 → 0,2 cm", "(một phép đo)"])]
    y0 = 1.95 + ph + 0.62
    for i, (t, d) in enumerate(cols):
        x = M + i * (CW / 4)
        dot(s, x, y0, i + 1, d=0.34, size=12)
        text(s, x + 0.46, y0 + 0.01, CW / 4 - 0.6, 0.32, t, 14.5, INK, True)
        text(s, x + 0.46, y0 + 0.38, CW / 4 - 0.6, 1.0, d, 13, TEXT2, spacing=1.06)
    footer(s, n)
    notes(s, """
Trước hết, hệ thống cần biết vị trí vật theo xăng-ti-mét. Nhóm in tờ A4 có bốn mã ArUco ở bốn góc; mỗi mã có số định danh, và OpenCV xác định được bốn góc của từng mã.

Từ kích thước thật của tờ giấy, 29,7 × 21 cm, chương trình tính phép biến đổi homography để đổi pixel sang tọa độ trên tờ giấy, cho cả hai camera. Gốc tọa độ đặt ở mã số 0. Khi một vài mã bị che, chương trình dùng vị trí đã lưu.

Camera phía trên đặt cao khoảng 46 cm, nên phần trên của vật cao 5 cm bị lệch khoảng 1 cm so với vị trí thật; đây là sai số thị sai. Nhóm bù sai số này theo độ cao vật; ở một vị trí đã đo, sai lệch giữa hai camera giảm từ 1,2 cm xuống 0,2 cm. Hai ảnh là lưới tọa độ chương trình vẽ trên khung hình camera đã lưu.

Nếu được hỏi: vì sao dùng ArUco? Mã có số định danh, xác định rõ bốn góc, nhận được khi nhìn nghiêng và có sẵn trong OpenCV. Tờ giấy là hệ quy chiếu chung cho cả hai camera, nên khi đổi vị trí camera không cần đo lại bằng thước. Độ cao 46 cm đo thế nào? Ước lượng từ ảnh, chưa đo bằng thước; con số 0,2 cm là kết quả của một phép đo.

Nguồn: generate_aruco_a4.py:3,31-36; vision.py:24-30,152-170,486-505,557-562; tests/test_vision.py:223-243; README.md mục 4.
""")


# ==============================================================================
# 02 · Computer vision · nhận diện vật
# ==============================================================================
def slide_objects(prs, n):
    s = new_slide(prs)
    header(s, "02 · Computer vision", "Nhận diện vật", "cv")
    cards = [
        ("MẶC ĐỊNH", TEAL, TEAL_SOFT, "Tách màu trên ảnh phẳng",
         "Lọc theo màu và kích thước; loại tay người, mép giấy, thân robot"),
        ("BỔ SUNG", TEAL, BG2, "Mã ArUco ID 10–29",
         "Dán lên vật để định vị ổn định"),
        ("TÙY CHỌN · --yolo", INDIGO, BG2, "YOLO11s (bộ COCO)",
         "Nhận tên vật; chưa huấn luyện lại"),
    ]
    cw = (CW - 0.5) / 3
    for i, (tag, col, fill, title, desc) in enumerate(cards):
        x = M + i * (cw + 0.25)
        box(s, x, 1.95, cw, 2.0, fill=fill)
        chip(s, x + 0.22, 2.15, tag, col, CARD if fill != BG2 else (INDIGO_SOFT if col == INDIGO else TEAL_SOFT), size=10)
        text(s, x + 0.22, 2.62, cw - 0.4, 0.36, title, 16, INK, True)
        text(s, x + 0.22, 3.08, cw - 0.4, 0.85, desc, 14, TEXT2, spacing=1.08)
    image(s, "ui_guide_cameras.png", M, 4.25, 7.6, 2.3, mode="cover", focus=(0.5, 0.45))
    caption(s, M, 6.68, 7.6, "Ví dụ YOLO nhận nhầm bộ phận robot (giao diện bản trước)", 10, 0.3)
    bx = M + 7.6 + 0.35
    box(s, bx, 4.19, W - M - bx, 2.42, fill=BG2)
    label(s, bx + 0.25, 4.38, 3.6, "Chọn mục tiêu", TEAL, 10.5)
    bullets(s, bx + 0.25, 4.78, W - M - bx - 0.45, 1.75, [
        "Ưu tiên vật gần đế nhất",
        [("TAB", {"bold": True}), " đổi vật"],
        "Trung bình 10 khung hình",
        "Lưu vị trí 120 s khi bị che",
    ], 15, after=9)
    footer(s, n)
    notes(s, """
Sau khi có hệ tọa độ, chương trình cần tìm vật. Cách mặc định là tách màu trên ảnh phẳng của tờ A4: vật có màu đậm như cốc đỏ được tách ra mà không cần dán mã. Bộ lọc loại các vùng quá lớn, chạm mép giấy hoặc dính vào thân robot, nên tay người không bị nhận là vật.

Cách thứ hai là dán mã ArUco số 10 đến 29 lên vật. Cách thứ ba là YOLO11 với trọng số COCO, chưa huấn luyện lại, chỉ bật khi cần. Ảnh bên dưới từ giao diện bản trước cho thấy YOLO nhận nhầm bộ phận robot thành chai và máy bay, nắp cốc thành đĩa ném; vì vậy bản hiện tại tắt YOLO mặc định.

Khi có nhiều vật, vật gần đế nhất được chọn trước, phím TAB để đổi vật. Vị trí được lấy trung bình 10 khung hình để giảm nhiễu, và được lưu trong 120 giây khi tay kẹp che vật.

Tiếp theo, {ctrl} trình bày phần code điều khiển.

Nếu được hỏi: có huấn luyện YOLO không? Chưa; huấn luyện cho vật thật là hướng phát triển. Vì sao vẫn giữ YOLO? Để nhận tên vật khi cần; vị trí theo xăng-ti-mét luôn tính từ homography của tờ giấy.

Nguồn: main.py:59 (--yolo); vision.py:43-47,271-300,365-368,476-486,491-492,507-515; control.py:68-69,542-566.
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
    header(s, "03 · Code điều khiển", "Lưu đồ thuật toán", "ctrl")
    label(s, M, 1.88, 5.6, "Firmware Arduino · robot_arm_4dof.ino", ORANGE, 10)
    cx = 2.55
    node(s, cx - 0.65, 2.25, 1.3, 0.38, "Bắt đầu", "term", fill=ORANGE_SOFT, edge=ORANGE, size=11, bold=True)
    node(s, 0.85, 2.85, 3.4, 0.64, ["setup(): USB, HC-05 9600 baud", "PCA9685 50 Hz · servo 90/90/90/95"], size=10.5)
    decs = [(3.72, "Có phím?", ["Đổi góc (có giới hạn)", "xuất xung · gửi JSON"]),
            (4.72, "Kẹp quá hạn?", ["mở 5 s / khép 60 s", "→ ngắt xung kẹp"]),
            (5.72, "Đủ 200 ms?", "Gửi JSON trạng thái")]
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
    steps_ = [("Đọc ảnh hai camera", BG2, LINE),
              ("vision.py: tờ A4 và vật → (X, Y) cm", BG2, LINE),
              ("control.py: động học ngược → Plan", TEAL_SOFT, TEAL),
              ("success.py: kiểm tra 3 servo → Result", TEAL_SOFT, TEAL),
              ("screen.py: hiển thị lệnh và kết quả", BG2, LINE)]
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
         [[("Khi bấm phím: ", {"bold": True, "color": ORANGE}),
           "control.press() gửi ký tự xuống Arduino qua USB"]],
         11, INK, anchor=MIDDLE, spacing=1.05)
    footer(s, n)
    notes(s, """
Bên trái là lưu đồ firmware trên Arduino. Hàm setup mở cổng USB và HC-05 ở 9600 baud, đặt PCA9685 ở 50 Hz và đưa bốn servo về 90, 90, 90, 95 độ. Vòng lặp loop thực hiện ba việc: khi có phím thì đổi góc trong giới hạn, xuất xung và gửi trạng thái; khi kẹp giữ quá thời gian thì ngắt xung; và cứ 200 ms gửi một gói JSON.

Bên phải là chương trình Python trên laptop, chạy ở mỗi khung hình: đọc hai camera, tìm tờ giấy và vật, tính góc và lệnh bấm phím, kiểm tra điều kiện hoàn thành, rồi hiển thị. Khi người dùng bấm phím, main.py gọi hàm press của khối điều khiển để gửi ký tự xuống Arduino qua USB; nếu chưa kết nối Arduino, chương trình chạy ở chế độ mô phỏng.

Nếu được hỏi: vì sao firmware đọc HC-05 trước USB? Để phím từ Bluetooth không bị bỏ qua khi USB cũng có dữ liệu; mỗi vòng chỉ đọc một ký tự. Vì sao không gửi trực tiếp lệnh góc? Để Arduino chỉ cần xử lý từng phím, giống khi điều khiển bằng tay.

Nguồn: robot_arm_4dof.ino:84-208; main.py:187-205,229-239; control.py:606-618 (press); success.py.
""")


# ==============================================================================
# 03 · Code điều khiển · code firmware
# ==============================================================================
def slide_fwcode(prs, n):
    s = new_slide(prs)
    header(s, "03 · Code điều khiển", "Code firmware Arduino", "ctrl")
    pw = (CW - 0.3) / 2
    blocks = [
        ("1 · Nhận phím, đổi góc (loop)", [
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
        ("2 · Góc → xung, gửi trạng thái", [
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
    facts = [("2° / 5°", "bước mỗi lần bấm"), ("125 → 575", "xung ứng với 0–180°"),
             ("9600 baud", "USB và HC-05")]
    fw = (CW - 0.5) / 3
    for i, (big, desc) in enumerate(facts):
        x = M + i * (fw + 0.25)
        box(s, x, 6.05, fw, 0.75, fill=TEAL_SOFT)
        bw = text_w(big, 18, True) + 0.25
        text(s, x + 0.2, 6.05, bw, 0.75, big, 18, TEAL, True, anchor=MIDDLE)
        text(s, x + 0.2 + bw, 6.05, fw - 0.3 - bw, 0.75, desc, 13, INK, anchor=MIDDLE, spacing=1.02)
    footer(s, n)
    notes(s, """
Đây là phần code chính của firmware, đã rút gọn. Bên trái: mỗi vòng lặp đọc một ký tự, ưu tiên HC-05 rồi đến USB; lệnh switch đổi góc theo từng phím, qua hàm constrain để giữ trong giới hạn: đế 0–180 độ, vai và khuỷu 25–155 độ, kẹp 95–160 độ; sau đó xuất góc mới ra servo.

Bên phải: hàm setServoAngle đổi góc thành độ rộng xung bằng hàm map, từ 125 đến 575, rồi gửi cho PCA9685. Cứ 200 ms, firmware gửi một gói JSON như dòng ví dụ, gồm thời gian chạy, bốn góc servo và hai cờ báo servo kẹp hoặc cả cánh tay đang nghỉ. Chương trình trên laptop đọc gói này để biết góc hiện tại.

Nếu được hỏi: vì sao dùng JSON? Dễ đọc bằng Python và có thể thêm cờ trạng thái. Thời gian chạy t dùng làm gì? Khi t trở về gần 0 nghĩa là Arduino vừa khởi động lại; chương trình báo ARDUINO VUA RESET. Dòng JSON trên slide là ví dụ đúng định dạng, giá trị t là giả định.

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
    header(s, "03 · Code điều khiển", "Động học ngược", "ctrl")
    arm_diagram(s)
    caption(s, M, 5.6, 5.7, "Mô hình mặc định (mm) · vai 90° ↔ θ2 = 45° · khuỷu 90° ↔ θ3 = −45°", 11, 0.45)
    items = ["Đổi (X, Y) cm sang tọa độ robot (mm)",
             [("Đế: ", {"bold": True}), ("θ1 = atan2(y, x)", {"font": MONO, "bold": True, "color": TEAL})],
             "Vai, khuỷu: tam giác hai khâu, khuỷu hướng lên",
             "Làm tròn 2°; số lần bấm = độ lệch ÷ 2°"]
    steps(s, 6.9, 2.05, W - M - 6.9, items, 16, gap=0.3)
    box(s, 6.9, 4.98, W - M - 6.9, 1.82, fill=TEAL_SOFT)
    label(s, 7.15, 5.1, 5.3, "Ví dụ · cốc ở (20,1; 7,4) cm", TEAL, 10.5)
    text(s, 7.15, 5.42, 5.4, 0.45, "đế 74° · vai 58° · khuỷu 90°", 23, INK, True)
    text(s, 7.15, 5.98, 1.75, 0.42, "Từ Home 90/90/90:", 12.5, TEXT2, anchor=MIDDLE)
    keycap(s, 8.92, 5.98, "D", 0.42, 0.4, 15)
    text(s, 9.4, 5.98, 0.6, 0.42, "× 8", 16, INK, True, anchor=MIDDLE)
    keycap(s, 10.02, 5.98, "S", 0.42, 0.4, 15)
    text(s, 10.5, 5.98, 0.7, 0.42, "× 16", 16, INK, True, anchor=MIDDLE)
    text(s, 11.22, 5.98, 1.35, 0.42, "khuỷu đã đúng", 11.5, TEAL, True, anchor=MIDDLE)
    text(s, 7.15, 6.47, 5.4, 0.3, f"theo mô hình đã hiệu chỉnh (slide {num('calib')})", 10.5, TEXT2)
    footer(s, n)
    notes(s, """
Khi biết vị trí X, Y của vật, khối điều khiển tính góc cần tới của ba servo; đây là bài toán động học ngược.

Hình bên trái là cánh tay nhìn ngang: trục vai cao 70 mm so với mặt bàn, khâu vai dài 105 mm, khâu khuỷu dài 100 mm, tâm kẹp lệch 65 mm ra trước và 25 mm xuống dưới. Đây là số đo bằng thước của mô hình mặc định; các thông số này được hiệu chỉnh ở cuối phần.

Thuật toán có bốn bước: đổi tọa độ trên giấy sang tọa độ robot; tính góc đế bằng atan2(y, x); giải tam giác hai khâu cho vai và khuỷu, chọn nghiệm khuỷu hướng lên, với điểm kẹp cao 25 mm; cuối cùng đổi sang góc servo, làm tròn theo bước 2 độ, và số lần bấm bằng độ lệch chia 2.

Ví dụ, cốc ở (20,1; 7,4) cm cho góc gợi ý: đế 74, vai 58, khuỷu 90 độ. Từ vị trí Home 90/90/90, cần bấm D 8 lần và S 16 lần; khuỷu đã đúng góc. Cánh tay không có servo cổ tay nên không điều chỉnh được hướng tay kẹp.

Nếu được hỏi: công thức được kiểm tra thế nào? Bộ test đưa kết quả động học ngược vào động học thuận trên hơn 100 điểm trong tầm với, sai số dưới 0,1 mm. Vì sao chọn nghiệm khuỷu hướng lên? Tam giác hai khâu có hai nghiệm; chọn một chiều cố định để mỗi điểm chỉ có một bộ góc. Vật ngoài tầm với thì sao? Giao diện báo VAT NGOAI TAM VOI và khoảng cách cần dời vật lại gần.

Nguồn: control.py:36-67,98-161,174-195,221-245; tests/test_control.py:16-35; 05_SO_LIEU_VA_NGUON.md mục 3 và 16 (ví dụ tính lại bằng check_facts.py --deep).
""")


# ==============================================================================
# 03 · Code điều khiển · màn hình hai ô
# ==============================================================================
def slide_screen(prs, n):
    s = new_slide(prs)
    header(s, "03 · Code điều khiển", "Giao diện chương trình", "ctrl")
    ih = image(s, "ui_screen_before.png", M, 1.95, 7.85, None, mode="fit")
    caption(s, M, 1.95 + ih + 0.13, 7.85, "Chạy trên ảnh camera đã lưu, cánh tay mô phỏng; chữ không dấu do OpenCV.", 10.5, 0.3)
    rx, rw = 9.05, W - M - 9.05
    dot(s, rx, 1.98, 1, d=0.38, size=13)
    text(s, rx + 0.5, 1.98, rw - 0.5, 0.34, "Ô điều khiển", 15.5, INK, True)
    text(s, rx + 0.5, 2.34, rw - 0.5, 0.95, "phím, số lần, góc hiện tại → góc đích", 13,
         TEXT2, spacing=1.06)
    dot(s, rx, 3.32, 2, d=0.38, size=13)
    text(s, rx + 0.5, 3.32, rw - 0.5, 0.34, "Ô success", 15.5, INK, True)
    text(s, rx + 0.5, 3.68, rw - 0.5, 0.7, "XONG khi cả ba servo tới góc", 13, TEXT2, spacing=1.06)
    box(s, rx, 4.5, rw, 1.25, fill=BG2)
    label(s, rx + 0.2, 4.6, rw - 0.3, "Trái / phải theo cam ngang", TEXT2, 10)
    keycap(s, rx + 0.2, 4.93, "A", 0.42, 0.4, 15)
    text(s, rx + 0.7, 4.93, 1.1, 0.4, "sang phải", 13.5, INK, anchor=MIDDLE)
    keycap(s, rx + 1.9, 4.93, "D", 0.42, 0.4, 15)
    text(s, rx + 2.4, 4.93, 1.2, 0.4, "sang trái", 13.5, INK, anchor=MIDDLE)
    text(s, rx + 0.2, 5.4, rw - 0.3, 0.3, "W S vai · I K khuỷu · mỗi lần 2°", 11.5, TEXT2)
    text(s, rx, 6.0, rw, 0.4, [[("Ví dụ: ", {"color": MUTED}), ("BẤM S × 15", {"color": TEAL, "bold": True}),
                                ", còn 18 lần"]], 13, INK)
    footer(s, n)
    notes(s, """
Đây là giao diện chương trình, chạy trên ảnh camera đã lưu với cánh tay mô phỏng. Hai khung camera phía trên có lưới tọa độ, vòng DICH quanh vật và dấu KEP là vị trí tay kẹp theo mô hình.

Bên dưới là hai ô nối nhau. Ô một lấy từ Plan của khối điều khiển: một lệnh chính. Trong ảnh, cốc ở (16,5; 13,8) cm, lệnh là bấm S 15 lần để hạ vai 30 độ, tổng còn 18 lần bấm. Ba hàng bên dưới là ba servo; hàng đã đạt ghi ĐÃ ĐÚNG, như hàng đế chỉ lệch 2 độ. Ô hai lấy từ kết quả của khối success: CHƯA XONG kèm số lần bấm còn lại, hoặc XONG.

Chữ không dấu vì OpenCV không hiển thị được dấu tiếng Việt. Trái, phải tính theo camera MacBook đặt trước robot: phím A quay đế sang phải, phím D sang trái.

Nếu được hỏi: chương trình có tự gửi phím không? Không; chỉ gửi khi người dùng bấm. Vì sao chỉ hiển thị một lệnh chính? Để người điều khiển thực hiện ngay, không cần đọc bảng số. Thứ tự lệnh thế nào? Đế, rồi vai, rồi khuỷu; servo đã đạt được bỏ qua. Ảnh đã lưu thì gợi ý lấy từ đâu? Chương trình đọc khung hình đã lưu như camera đang chạy; cánh tay mô phỏng đặt ở Home.

Nguồn: screen.py:157-239,249-259; main.py:178-205; control.py:211-217; ảnh ui_screen_before (tạo bằng slides/tools/make_screen_images.py).
""")


# ==============================================================================
# 03 · Code điều khiển · điều khiển từ xa: Mac (camera, xử lý) + máy Dell (Bluetooth)
# ==============================================================================
def slide_remote(prs, n):
    s = new_slide(prs)
    header(s, "03 · Code điều khiển", "Điều khiển từ xa", "ctrl")

    def block(x, y, w, h, tag, title, desc, tag_color, fill=CARD, edge=None):
        box(s, x, y, w, h, fill=fill, edge=edge, edge_w=2.0)
        text(s, x + 0.18, y + 0.14, w - 0.36, 0.25, tag, 10, tag_color, True)
        text(s, x + 0.18, y + 0.42, w - 0.36, 0.32, title, 15, INK, True)
        text(s, x + 0.18, y + 0.8, w - 0.36, 0.5, desc, 11.5, TEXT2, spacing=1.05)

    bw, bh = 3.2, 1.55
    mac_x, uno_x, top = M, 5.35, 2.0
    dell_x, dell_y, dell_h = 3.08, 4.6, 1.45
    block(mac_x, top, bw, bh, "MAC · main.py", "Camera + xử lý", "2 camera · vision · control · success", TEAL, edge=TEAL)
    block(uno_x, top, bw, bh, "ARDUINO UNO", "Servo + HC-05", "Firmware giữ nguyên", ORANGE, fill=ORANGE_SOFT)
    block(dell_x, dell_y, bw, dell_h, "DELL · remote.py", "Người điều khiển", "Cách ~2 m · bàn phím", TEAL, edge=LINE)
    # USB: Arduino báo góc servo về Mac
    uy = top + 0.78
    line(s, uno_x - 0.05, uy, mac_x + bw + 0.05, uy, MUTED, 1.75, head=True)
    text(s, mac_x + bw, uy - 0.36, uno_x - mac_x - bw, 0.28, "USB · góc servo", 10.5, MUTED, align=CENTER)
    # Wi-Fi: Mac gửi ảnh màn hình sang Dell
    wx, ly = mac_x + 1.1, dell_y + dell_h / 2
    line(s, wx, top + bh + 0.05, wx, ly, TEAL, 1.75, dash=True)
    line(s, wx, ly, dell_x - 0.05, ly, TEAL, 1.75, head=True, dash=True)
    text(s, wx + 0.12, top + bh + 0.3, 1.8, 0.6, [[("Wi-Fi", {"bold": True})], "ảnh 2 cam + XONG"], 11.5, TEAL, spacing=1.05)
    # Bluetooth: Dell gửi phím tới HC-05
    bx = uno_x + 2.1
    line(s, dell_x + bw + 0.05, ly, bx, ly, TEAL, 2.5)
    line(s, bx, ly, bx, top + bh + 0.05, TEAL, 2.5, head=True)
    text(s, bx + 0.14, top + bh + 0.3, 1.4, 0.6, [[("Bluetooth", {"bold": True})], "phím"], 11.5, TEAL, spacing=1.05)

    rx, rw = 9.05, W - M - 9.05
    label(s, rx, 1.98, rw, "Một lần bấm phím", TEXT2, 10.5)
    y = steps(s, rx, 2.35, rw, ["Dell gõ D, gửi qua Bluetooth", "Uno quay đế 2°", "Góc mới về Mac qua USB",
                                "Mac tính lại lệnh, ảnh mới về Dell"], 13.5, d=0.32, gap=0.12)
    box(s, rx, y + 0.15, rw, 1.32, fill=BG2)
    label(s, rx + 0.2, y + 0.25, rw - 0.3, "Chuẩn bị", TEXT2, 10)
    bullets(s, rx + 0.2, y + 0.55, rw - 0.35, 0.9, ["HC-05 ghép đôi với Dell", "Hai máy cùng Wi-Fi", "Mac cắm USB vào Uno"],
            12.5, after=2)
    cw_ = chip(s, M, 6.28, "Chưa thử trên phần cứng thật", ORANGE, ORANGE_SOFT, 10)
    text(s, M + cw_ + 0.15, 6.28, 7.4 - cw_, 0.34, "Đã chạy thử với cánh tay mô phỏng", 11.5, TEXT2, anchor=MIDDLE)
    footer(s, n)
    notes(s, """
Đây là cách điều khiển từ xa. Mac đặt cạnh cánh tay, chạy chương trình với hai camera và cắm USB vào Arduino. Người điều khiển ngồi ở máy Dell, cách khoảng 2 m, chạy chương trình remote.py.

Hệ thống có ba đường nối. Wi-Fi: Mac gửi ảnh màn hình, gồm hai camera, lệnh bấm phím và kết quả success, sang Dell, tối đa 10 ảnh mỗi giây. Bluetooth: Dell gửi phím tới module HC-05 trên mạch Arduino. USB: sau mỗi phím, Arduino gửi góc servo mới về Mac; Mac tính lại lệnh, kiểm tra success, và ảnh mới về Dell.

Ảnh không gửi qua Bluetooth vì HC-05 chạy 9600 baud, khoảng 1 KB mỗi giây, trong khi một ảnh màn hình khoảng 120 KB, tức gần 2 phút cho một ảnh. Firmware không cần sửa: nó đã nhận phím từ HC-05 và gửi góc qua USB.

Phím H về Home và Z ngắt xung phải bấm hai lần trong 2 giây mới được gửi, để tránh bấm nhầm.

Nếu được hỏi: vì sao Mac vẫn cắm USB? Để nhận góc servo và cấp nguồn cho Arduino; không có góc thì không tính được lệnh và success. Vì sao không gửi phím qua Wi-Fi? Làm được qua Mac; nhóm dùng Bluetooth để module HC-05 trên mạch nhận phím trực tiếp. Hai máy khác mạng thì sao? Dùng điểm phát Wi-Fi của điện thoại, hoặc ngrok. Đường dẫn có mã 6 số, lưu trong máy và giữ nguyên giữa các lần chạy, để người khác cùng mạng không xem hay bấm được. Đã thử trên phần cứng thật chưa? Chưa; mới chạy thử với cánh tay mô phỏng trên một máy.

Nguồn: remote.py; phone.py; main.py (start_phone); robot_arm_4dof.ino (đọc HC-05 trước USB); README.md mục 2.
""")


# ==============================================================================
# 03 · Code điều khiển · sự cố mô hình lệch và hiệu chỉnh
# ==============================================================================
def slide_calib(prs, n):
    s = new_slide(prs)
    header(s, "03 · Code điều khiển", "Hiệu chỉnh mô hình cánh tay", "ctrl")
    label(s, M, 1.95, 5.3, "Sai lệch của mô hình mặc định", TEXT2, 10.5)
    for i, (big, desc) in enumerate([("5,4 cm", "mẫu 20:32 · servo [85, 60, 90]"),
                                     ("3,5 cm", "mẫu 20:46 · servo [80, 70, 75]"),
                                     ("5,9 cm", "mẫu 21:03 · servo [75, 85, 50]")]):
        y = 2.3 + i * 0.6
        rule(s, M, y, 5.3)
        text(s, M, y + 0.04, 1.7, 0.55, big, 25, ORANGE, True, anchor=MIDDLE)
        text(s, M + 1.8, y + 0.04, 3.5, 0.55, desc, 13, TEXT2, anchor=MIDDLE)
    rule(s, M, 2.3 + 3 * 0.6, 5.3)
    text(s, M, 4.2, 5.3, 0.5, "Sai lệch có hệ thống, hiệu chỉnh được", 13, TEXT2,
         spacing=1.05)
    label(s, M, 4.82, 5.3, "Cách hiệu chỉnh", TEAL, 10.5)
    steps(s, M, 5.18, 5.3, [
        "Đặt kẹp quanh cốc; ghi góc servo và vị trí cốc",
        "10 mẫu; khớp thông số mô hình (Levenberg–Marquardt)",
        "Lưu vào calibration.json",
    ], 13.5, d=0.3, gap=0.1)
    iw = W - M - 6.45
    image(s, "calib_before_after_side.jpg", 6.45, 1.95, iw, iw * 9 / 16)
    ih = iw * 9 / 16
    caption(s, 6.45, 1.95 + ih + 0.12, iw, "Mẫu 21:03 (thuộc tập khớp): MAC DINH lệch ≈ 5 cm, SAU HIEU CHINH ≈ 1 cm", 10, 0.45)
    bw = (iw - 0.25) / 2
    for i, (big, desc) in enumerate([("8,5 mm", ["sai số khớp RMS", "trên 10 mẫu"]), ("11,6 mm", ["bỏ-một-mẫu", "(leave-one-out)"])]):
        x = 6.45 + i * (bw + 0.25)
        nw = text_w(big, 20, True) + 0.2
        box(s, x, 5.98, bw, 0.82, fill=TEAL_SOFT)
        text(s, x + 0.18, 5.98, nw, 0.82, big, 20, TEAL, True, anchor=MIDDLE)
        text(s, x + 0.18 + nw, 5.98, bw - 0.26 - nw, 0.82, desc, 11, INK, anchor=MIDDLE, spacing=1.02)
    footer(s, n)
    notes(s, """
Gợi ý trên màn hình được tính từ mô hình cánh tay, không đo trực tiếp bằng camera, nên độ chính xác của gợi ý phụ thuộc vào mô hình.

Trong buổi thử, người điều khiển đặt hai ngón kẹp quanh cốc, nhóm ghi lại ba góc servo và vị trí cốc. Với ba mẫu đầu, đầu kẹp theo mô hình mặc định cách cốc 5,4 cm, 3,5 cm và 5,9 cm, cùng chiều và cùng độ lớn, tức là sai lệch có hệ thống.

Nhóm hiệu chỉnh bằng 10 mẫu ở các vị trí khác nhau: khớp lại vị trí và hướng đế, góc chuẩn của vai và khuỷu, và độ lệch của càng kẹp, bằng thuật toán Levenberg–Marquardt. Sai số khớp còn 8,5 mm, và 11,6 mm khi kiểm tra bỏ-một-mẫu. Trong ảnh, dấu màu cam là mô hình mặc định, dấu màu xanh là sau hiệu chỉnh; mẫu này thuộc tập khớp nên chỉ dùng để minh họa.

Lưu ý: 8,5 mm là sai số trên chính các mẫu dùng để khớp; gợi ý mới chưa được thử trên cánh tay thật; và kết quả hiệu chỉnh chỉ áp dụng cho vị trí tờ giấy và robot lúc đo.

Tiếp theo, {succ} trình bày khối success và kết quả.

Nếu được hỏi: nguyên nhân sai lệch là gì? Có ba: vị trí và hướng đế khác mặc định; góc chuẩn của vai và khuỷu phụ thuộc cách lắp cần servo, thước không đo được; và càng kẹp gắn cứng vào khâu khuỷu nên điểm kẹp quay theo khâu, trong khi mô hình cũ giữ độ lệch cố định. Vì sao không đo lại bằng thước? Thước đo được chiều dài khâu nhưng không đo được góc lắp cần servo; hiệu chỉnh từ các mẫu xử lý được cả hai.

Nguồn: calibration.json (mục arm, claw, arm_fit); calibration.py:16-20,77-105; arm_fit.py:1-45; tests/test_arm_fit.py:80-91; 05_SO_LIEU_VA_NGUON.md mục 8 và 16; ảnh calib_before_after_side.
""")


# ==============================================================================
# 04 · Success · luật success
# ==============================================================================
def slide_success(prs, n):
    s = new_slide(prs)
    header(s, "04 · Success", "Điều kiện hoàn thành", "succ")
    rows = [("± 2°", "sai lệch tối đa mỗi servo"),
            ("3 servo", "đế, vai, khuỷu (không xét kẹp)"),
            ("1 giây", "giữ liên tục để tính 1 lần")]
    for i, (big, desc) in enumerate(rows):
        y = 1.95 + i * 0.85
        rule(s, M, y, 5.8)
        text(s, M, y + 0.05, 1.85, 0.75, big, 30, TEAL, True, anchor=MIDDLE)
        text(s, M + 1.95, y + 0.05, 3.85, 0.75, desc, 15, INK, anchor=MIDDLE, spacing=1.05)
    rule(s, M, 1.95 + 3 * 0.85, 5.8)
    chip(s, M, 4.75, "KIỂM THỬ: 7 TEST + ĐẦU–CUỐI", size=10)
    ih = image(s, "ui_screen_done.png", 6.9, 1.95, W - M - 6.9, None, mode="fit")
    caption(s, 6.9, 1.95 + ih + 0.12, W - M - 6.9, "Mô phỏng trên ảnh đã lưu: đủ phím → XONG",
            10, 0.3)
    for i, (title, body) in enumerate([
        ("Phạm vi", "Không xét tay kẹp: vật thon dễ trượt khi kẹp"),
        ("Lưu ý", "XONG dựa trên góc đã ra lệnh; servo không phản hồi vị trí"),
    ]):
        x = M + i * ((CW + 0.25) / 2)
        box(s, x, 5.7, (CW - 0.25) / 2, 1.12, fill=ORANGE_SOFT)
        label(s, x + 0.22, 5.8, 5.4, title, ORANGE, 10.5)
        text(s, x + 0.22, 6.12, (CW - 0.25) / 2 - 0.4, 0.7, body, 14, INK, spacing=1.05)
    footer(s, n)
    notes(s, """
Khối success kiểm tra ba servo đế, vai, khuỷu đã tới góc mà khối điều khiển gợi ý hay chưa. Khối này chỉ đọc Plan, không phụ thuộc vào camera, động học hay cổng USB.

Điều kiện gồm ba ý. Mỗi servo lệch không quá một bước bấm, tức 2 độ; nhóm chọn 2 độ vì mô hình hình học cũng chỉ chính xác ở mức đó. Chỉ xét ba servo của cánh tay, không xét tay kẹp. Cả ba phải giữ đúng liên tục 1 giây mới tính thêm một lần hoàn thành.

Tay kẹp không được xét vì cốc thử nghiệm thon dần về đáy: khi khép đến 150–160 độ, cốc bị đẩy ra; trong buổi thử cốc bị đổ khoảng 3 lần.

Lưu ý: trạng thái XONG nghĩa là ba góc đã ra lệnh đạt mục tiêu, vì MG996R không phản hồi vị trí thật. Ảnh bên phải là mô phỏng trên ảnh đã lưu; bản này chưa được đếm trên cánh tay thật.

Nếu được hỏi: vì sao cần giữ 1 giây? Để trường hợp đi qua mục tiêu không bị tính. Có kiểm tra bằng camera không? Bản trước có, dựa trên hai camera; nhóm đã bỏ để mã đơn giản hơn. Số lần hoàn thành hiển thị ở đâu? Ở dòng Thanh cong: N lan trong ô success; chưa ghi ra file. Khi không thấy vật? Không báo XONG; trạng thái là chưa thấy vật.

Nguồn: success.py:16-17,19,22-75; tests/test_success.py (7 test); tests/test_end_to_end.py:11-47; robot_arm_4dof.ino:70-83; README.md mục 6; ảnh ui_screen_done (tạo bằng slides/tools/make_screen_images.py).
""")


# ==============================================================================
# 04 · Success · thử trên cánh tay thật
# ==============================================================================
def slide_trial(prs, n):
    s = new_slide(prs, alt=True)
    header(s, "04 · Success", "Thử nghiệm trên cánh tay thật", "succ")
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
    w1 = chip(s, M, 6.5, "ĐIỀU KHIỂN BẰNG BÀN PHÍM", TEAL, TEAL_SOFT, size=10.5, h=0.36)
    text(s, M + w1 + 0.2, 6.5, 11.95 - (M + w1 + 0.2) - 0.1, 0.36,
         "02/11/2026 · ba khung hình cách nhau 10 giây · giao diện bản trước", 10.5, MUTED, anchor=MIDDLE)
    footer(s, n)
    notes(s, """
Đây là buổi thử trên cánh tay thật ngày 2/11. Ba cột cách nhau 10 giây; hàng trên là camera ngang, hàng dưới là camera phía trên: cốc nằm giữa hai ngón kẹp, được chuyển sang trái, rồi đặt xuống. Nhóm thực hiện thao tác này nhiều lần.

Người điều khiển bấm phím dựa trên hình ảnh từ hai camera, với giao diện bản trước khi đơn giản hóa. Trong buổi thử, cốc bị đổ khoảng 3 lần và được dựng lại bằng tay. Nhóm chưa có số liệu tỉ lệ thành công.

Góc servo lúc kẹp, đọc từ giao diện bản cũ: đế khoảng 85, vai 60–65, khuỷu 85–90 độ. Các mẫu đặt kẹp quanh cốc trong buổi này cũng là dữ liệu {ctrl} dùng để hiệu chỉnh mô hình.

Nếu được hỏi: có video không? [...điền: có / không; nếu có thì chiếu đoạn 20–30 giây]. Kẹp có giữ chắc không? Chưa: cốc thon bị đẩy ra khi khép đến 150–160 độ.

Nguồn: ảnh demo_06, demo_07, demo_08 (khung cắt từ video 02/11/2026, 20:32:52 đến 20:33:12); 05_SO_LIEU_VA_NGUON.md mục 7.
""")


# ==============================================================================
# 04 · Success · kết quả
# ==============================================================================
def slide_results(prs, n):
    s = new_slide(prs, alt=True)
    header(s, "04 · Success", "Kết quả", "succ")
    pw = (CW - 0.3) / 2
    box(s, M, 1.95, pw, 3.4, fill=TEAL_SOFT)
    label(s, M + 0.28, 2.12, pw - 0.5, "Đã thực hiện", TEAL, 10.5)
    bullets(s, M + 0.28, 2.5, pw - 0.5, 2.8, [
        "Hệ tọa độ chung cho hai camera",
        "Kẹp, di chuyển cốc trên cánh tay thật (02/11)",
        "Hiệu chỉnh mô hình từ 10 mẫu",
        "Firmware bảo vệ servo kẹp đã nạp, kiểm tra",
        "Giao diện gợi ý phím, kiểm tra góc",
    ], 16, after=14)
    x2 = M + pw + 0.3
    box(s, x2, 1.95, pw, 3.4, fill=CARD)
    label(s, x2 + 0.28, 2.12, pw - 0.5, "Chưa thực hiện", ORANGE, 10.5)
    bullets(s, x2 + 0.28, 2.5, pw - 0.5, 2.8, [
        "Đếm XONG trên cánh tay thật (bản mới)",
        "Kiểm tra gợi ý mới trên phần cứng",
        "Kẹp chắc vật thon",
        "Đo nhiệt độ servo",
        "Hiệu chỉnh cho tờ giấy mới",
        "Dashboard IoT / MQTT",
    ], 16, after=8, mark="—", mark_color=ORANGE, indent=0.3)
    stats = [("122 / 122", ["test tự động", "đều đạt"], TEAL),
             ("11", ["tệp test"], INK),
             ("8,5 mm", ["sai số hiệu chỉnh", "trên 10 mẫu"], TEAL)]
    sw = (CW - 0.5) / 3
    for i, (big, desc, col) in enumerate(stats):
        x = M + i * (sw + 0.25)
        bw = text_w(big, 32, True) + 0.3
        box(s, x, 5.55, sw, 1.27, fill=CARD)
        text(s, x + 0.25, 5.55, bw, 1.27, big, 32, col, True, anchor=MIDDLE)
        text(s, x + 0.25 + bw, 5.55, sw - 0.35 - bw, 1.27, desc, 12.5, TEXT2, anchor=MIDDLE, spacing=1.05)
    footer(s, n)
    notes(s, """
Slide này tổng hợp những việc đã thực hiện và chưa thực hiện.

Đã thực hiện: hệ tọa độ chung cho hai camera; kẹp và di chuyển cốc trên cánh tay thật bằng bàn phím; hiệu chỉnh mô hình từ 10 mẫu với sai số 8,5 mm; firmware bảo vệ servo kẹp đã nạp và kiểm tra; giao diện gợi ý phím và kiểm tra góc; điều khiển từ xa bằng máy Dell, mới chạy thử với cánh tay mô phỏng. 122 test tự động đều đạt, chạy khoảng 10 giây, không cần camera hay Arduino.

Chưa thực hiện: đếm số lần XONG trên cánh tay thật với bản mới; kiểm tra gợi ý mới trên phần cứng; kẹp chắc vật thon; đo nhiệt độ servo; hiệu chỉnh cho tờ giấy mới; dashboard IoT qua MQTT và cảm biến lực, vốn có trong kế hoạch ngày 28/10.

Nếu được hỏi: vì sao chưa chạy bản mới trên cánh tay thật? Mã được đơn giản hóa ngày 2/11; thử nghiệm bản mới trên cánh tay thật là bước tiếp theo. Test gồm những gì? Điều khiển 29, computer vision 15, camera 13, hiệu chỉnh 11, Serial 9, chương trình chính 8, success 7, độ bền 6, khớp mô hình 5, màn hình 4, đầu–cuối 2. Có bắt buộc dashboard IoT không? [...điền theo yêu cầu đề bài]; nếu có, nhóm có thể thêm MQTT từ gói JSON hiện có.

Nguồn: 05_SO_LIEU_VA_NGUON.md mục 4, 6, 7, 8, 11, 13; lệnh .venv/bin/python -m pytest -q (122 passed, 04/11/2026).
""")


# ==============================================================================
# 04 · Success · hạn chế và việc tiếp theo
# ==============================================================================
def slide_limits(prs, n):
    s = new_slide(prs)
    header(s, "04 · Success", "Hạn chế và hướng phát triển", "succ")
    pw = (CW - 0.3) / 2
    box(s, M, 1.95, pw, 3.95, fill=BG2)
    label(s, M + 0.28, 2.15, pw - 0.5, "Hạn chế", ORANGE, 10.5)
    bullets(s, M + 0.28, 2.55, pw - 0.5, 3.3, [
        "Điều khiển vòng hở (không phản hồi vị trí)",
        "Hiệu chỉnh phụ thuộc vị trí giấy và robot",
        "Tay kẹp chưa giữ chắc vật thon",
        "YOLO chưa huấn luyện cho vật thật",
        "Chưa có số liệu tỉ lệ hoàn thành",
    ], 16, after=12, mark="—", mark_color=ORANGE, indent=0.3)
    x2 = M + pw + 0.3
    box(s, x2, 1.95, pw, 3.95, fill=TEAL_SOFT)
    label(s, x2 + 0.28, 2.15, pw - 0.5, "Hướng phát triển", TEAL, 10.5)
    steps(s, x2 + 0.28, 2.58, pw - 0.5, [
        "Thử nghiệm bản mới trên cánh tay thật",
        "Cải thiện tay kẹp, đưa kẹp vào success",
        "Hiệu chỉnh lại khi đổi tờ giấy",
        "Phản hồi vị trí đầu kẹp bằng camera",
        "Dashboard IoT (MQTT) từ dữ liệu JSON",
    ], 16, d=0.34, gap=0.22)
    rule(s, M, 6.12, CW)
    label(s, M, 6.27, 2.7, "Lỗi tích hợp đã xử lý", TEXT2, 10)
    bullets(s, 3.55, 6.24, W - M - 3.55, 0.6, [
        "Thứ tự camera trên macOS thay đổi: tìm camera theo tên",
        "Arduino tự reset khi mở lại cổng USB: giữ một kết nối",
    ], 12, after=1, indent=0.2)
    footer(s, n)
    notes(s, """
Hệ thống hiện có năm hạn chế. Thứ nhất, điều khiển vòng hở: trạng thái XONG dựa trên góc đã ra lệnh vì MG996R không phản hồi vị trí. Thứ hai, kết quả hiệu chỉnh phụ thuộc vị trí tờ giấy và robot. Thứ ba, tay kẹp chưa giữ chắc vật thon. Thứ tư, YOLO chưa được huấn luyện cho vật thật. Thứ năm, chưa có số liệu tỉ lệ hoàn thành và nhiệt độ servo.

Hướng phát triển: thử nghiệm bản mới trên cánh tay thật và đếm số lần XONG; cải thiện tay kẹp, ví dụ tăng ma sát hoặc dùng vật thân thẳng, rồi đưa kẹp vào điều kiện success; hiệu chỉnh lại khi đổi tờ giấy; đo vị trí đầu kẹp bằng camera để có phản hồi vòng kín; và thêm dashboard IoT qua MQTT nếu đề bài yêu cầu.

Dòng dưới là hai lỗi tích hợp đã xử lý: thứ tự camera trên macOS thay đổi giữa các lần chạy, nên chương trình tìm camera theo tên; Arduino Uno tự khởi động lại mỗi khi cổng USB được mở lại, nên chương trình giữ một kết nối duy nhất và báo khi Arduino vừa reset.

Nếu được hỏi: phát hiện Arduino reset bằng cách nào? Gói JSON có thời gian chạy t; khi t trở về gần 0, giao diện báo ARDUINO VUA RESET. Vì sao camera đổi thứ tự? OpenCV đánh số camera theo uniqueID, còn danh sách của hệ điều hành xếp camera dùng gần nhất lên đầu. Đo đầu kẹp bằng camera thế nào? Ví dụ dán mã ArUco lên càng kẹp và dùng homography của tờ giấy; đây là hướng đề xuất, chưa thực hiện. Có thể chuyển sang tự gửi phím không? Về kỹ thuật là gửi phím theo Plan; nhóm chỉ thực hiện khi đo được độ lệch còn lại.

Nguồn: 05_SO_LIEU_VA_NGUON.md mục 4, 6, 8, 9, 10, 13; cameras.py:4-12,75-115; control.py (ArduinoSerialLink: mở lại cổng, phát hiện reset); README.md mục 5 và 6.
""")


# ==============================================================================
# Tóm lại + hỏi đáp
# ==============================================================================
def slide_summary(prs, n):
    s = new_slide(prs)
    label(s, M, 0.6, 6.0, "Tổng kết", TEAL)
    for i, st in enumerate(["Hai camera xác định vị trí vật theo cm.",
                            "Khối điều khiển tính góc servo và phím cần bấm.",
                            "Khối success kiểm tra ba servo đã tới góc gợi ý."]):
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
    text(s, M, 5.42, CW, 0.6, "Cảm ơn thầy cô và các bạn đã lắng nghe", 26, TEAL, True, align=CENTER)
    text(s, M, 6.1, CW, 0.4, "  ·  ".join(name(k) for k in ("hw", "cv", "ctrl", "succ")) + "  ·  hỏi đáp", 13, TEXT2,
         align=CENTER)
    footer(s, n)
    notes(s, """
Tổng kết: hai camera xác định vị trí vật theo xăng-ti-mét trên tờ A4; khối điều khiển tính góc servo và phím cần bấm; khối success kiểm tra ba servo đã tới góc gợi ý.

Các hạn chế và việc chưa thực hiện đã nêu ở phần kết quả. Mã nguồn có trên GitHub theo đường dẫn trên slide.

Nếu thầy cô muốn, nhóm có thể demo trực tiếp: [...điền kịch bản demo 2–3 phút].

Nhóm em cảm ơn thầy cô và các bạn đã lắng nghe, và xin nhận câu hỏi; câu hỏi phần nào thì thành viên phụ trách phần đó trả lời.

Nếu được hỏi: việc nào nên làm tiếp theo? Thử nghiệm bản mới trên cánh tay thật để có số lần XONG đầu tiên.

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
    ("remote", slide_remote, "ctrl"),
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
