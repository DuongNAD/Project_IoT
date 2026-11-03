"""Build 15-slide technical presentation for 4-DOF Robot Arm Grasp Assist system.

Strictly follows project specifications, color palette, typography, keycaps,
native shapes, Vietnamese speaker notes, footers, and asset embedding.
"""

import os
import sys

# Ensure UTF-8 stdout on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

from slides.generate_asset import generate_guide_screen_asset, ASSETS_DIR

# ==============================================================================
# BẢNG MÀU CHUẨN DARK THEME (guide_screen.py)
# ==============================================================================
BG_COLOR = RGBColor(25, 27, 30)        # #191B1E - Nền tối chính
CARD_COLOR = RGBColor(39, 42, 46)      # #272A2E - Nền thẻ khối
BORDER_COLOR = RGBColor(70, 76, 82)    # #464C52 - Viền phân cách
PRIMARY_TEXT = RGBColor(245, 245, 245) # #F5F5F5 - Chữ chính
MUTED_TEXT = RGBColor(155, 160, 165)   # #9BA0A5 - Chữ phụ, chú thích
AMBER = RGBColor(255, 185, 40)          # #FFB928 - Điểm nhấn cam, keycap
GREEN = RGBColor(90, 215, 110)         # #5AD76E - Điểm nhấn xanh lá (thành công)
RED = RGBColor(245, 85, 85)            # #F55555 - Điểm nhấn đỏ (cảnh báo, lỗi)
DARK_TEXT = RGBColor(25, 27, 30)       # #191B1E - Chữ tối trên nền cam/xanh
AMBER_DK = RGBColor(98, 62, 28)        # #623E1C - Nền cam tối
GREEN_DK = RGBColor(42, 88, 50)        # #2A5832 - Nền xanh lá tối

FONT_MAIN = "Arial"
FONT_CODE = "Courier New"


# ==============================================================================
# HELPER FUNCTIONS DỰNG SLIDE, SHAPE, TEXT, KEYCAP
# ==============================================================================
def create_deck():
    """Tạo đối tượng Presentation tỉ lệ 16:9 widescreen (13.333 x 7.5 inches)."""
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs


def add_slide_with_bg(prs):
    """Thêm một slide trắng với nền tối chuẩn #191B1E."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Đặt background fill cho slide
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = BG_COLOR

    # Thêm hình chữ nhật phủ toàn màn hình để đảm bảo tương thích 100% mọi viewer
    bg_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg_shape.fill.solid()
    bg_shape.fill.fore_color.rgb = BG_COLOR
    bg_shape.line.fill.background()
    return slide


def add_header(slide, tag_text, title_text):
    """Thêm tiêu đề chuẩn cho slide với Tag cam và đường gạch tinh tế."""
    # Tag phía trên tiêu đề
    tag_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.42), Inches(11.733), Inches(0.32))
    tf_tag = tag_box.text_frame
    tf_tag.word_wrap = True
    tf_tag.margin_left = tf_tag.margin_top = tf_tag.margin_right = tf_tag.margin_bottom = 0
    p_tag = tf_tag.paragraphs[0]
    p_tag.text = tag_text.upper()
    p_tag.font.name = FONT_MAIN
    p_tag.font.size = Pt(13)
    p_tag.font.bold = True
    p_tag.font.color.rgb = AMBER

    # Tiêu đề chính (>= 28 pt)
    title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(11.733), Inches(0.65))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    tf_title.margin_left = tf_title.margin_top = tf_title.margin_right = tf_title.margin_bottom = 0
    p_title = tf_title.paragraphs[0]
    p_title.text = title_text
    p_title.font.name = FONT_MAIN
    p_title.font.size = Pt(28)
    p_title.font.bold = True
    p_title.font.color.rgb = PRIMARY_TEXT

    # Dải phân cách mỏng
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.42), Inches(11.733), Inches(0.02))
    line.fill.solid()
    line.fill.fore_color.rgb = BORDER_COLOR
    line.line.fill.background()


def add_footer(slide, slide_num, total_slides=15):
    """Thêm footer chuẩn gồm tên đề tài và số trang."""
    # Tiêu đề ngắn bên trái
    left_box = slide.shapes.add_textbox(Inches(0.8), Inches(6.92), Inches(8.5), Inches(0.38))
    tf_left = left_box.text_frame
    tf_left.margin_left = tf_left.margin_top = tf_left.margin_right = tf_left.margin_bottom = 0
    p_left = tf_left.paragraphs[0]
    p_left.text = "Hệ thống hỗ trợ gắp vật 4-DOF - IoT Robot Arm"
    p_left.font.name = FONT_MAIN
    p_left.font.size = Pt(14)
    p_left.font.color.rgb = MUTED_TEXT

    # Số trang bên phải
    right_box = slide.shapes.add_textbox(Inches(9.5), Inches(6.92), Inches(3.033), Inches(0.38))
    tf_right = right_box.text_frame
    tf_right.margin_left = tf_right.margin_top = tf_right.margin_right = tf_right.margin_bottom = 0
    p_right = tf_right.paragraphs[0]
    p_right.alignment = PP_ALIGN.RIGHT
    p_right.text = f"Trang {slide_num} / {total_slides}"
    p_right.font.name = FONT_MAIN
    p_right.font.size = Pt(14)
    p_right.font.bold = True
    p_right.font.color.rgb = MUTED_TEXT


def add_card(slide, left, top, width, height, bg_color=CARD_COLOR, border_color=BORDER_COLOR, border_width=1.0):
    """Vẽ khối thẻ bo góc (Rounded Rectangle) chuẩn dark theme."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    if border_color:
        card.line.color.rgb = border_color
        card.line.width = Pt(border_width)
    else:
        card.line.fill.background()
    return card


def add_keycap(slide, left, top, letter, width=Inches(0.48), height=Inches(0.38), bg_color=AMBER, fg_color=DARK_TEXT):
    """Vẽ nút phím kiểu Keycap màu cam chữ tối bo tròn chuẩn guide_screen.py."""
    key = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    key.fill.solid()
    key.fill.fore_color.rgb = bg_color
    key.line.fill.background()

    tf = key.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = letter
    p.font.name = FONT_MAIN
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = fg_color
    return key


def add_arrow(slide, left, top, width, height, color=AMBER, direction="right"):
    """Vẽ mũi tên liên kết giữa các khối."""
    shape_type = MSO_SHAPE.RIGHT_ARROW if direction == "right" else MSO_SHAPE.DOWN_ARROW
    arrow = slide.shapes.add_shape(shape_type, left, top, width, height)
    arrow.fill.solid()
    arrow.fill.fore_color.rgb = color
    arrow.line.fill.background()
    return arrow


def set_speaker_notes(slide, notes_text):
    """Thiết lập speaker notes cho slide."""
    notes_slide = slide.notes_slide
    tf = notes_slide.notes_text_frame
    tf.text = notes_text.strip()


# ==============================================================================
# SLIDE 1: TIÊU ĐỀ ĐỀ TÀI
# ==============================================================================
def build_slide_1(prs):
    slide = add_slide_with_bg(prs)

    # Thẻ lớn trung tâm
    main_card = add_card(slide, Inches(1.2), Inches(0.9), Inches(10.933), Inches(5.7),
                         bg_color=CARD_COLOR, border_color=BORDER_COLOR, border_width=1.5)

    # Dải viền trang trí màu cam trên đỉnh thẻ
    top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.2), Inches(0.9), Inches(10.933), Inches(0.08))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = AMBER
    top_bar.line.fill.background()

    # Nhãn dự án
    tag_box = slide.shapes.add_textbox(Inches(1.8), Inches(1.3), Inches(9.733), Inches(0.4))
    tf_tag = tag_box.text_frame
    p_tag = tf_tag.paragraphs[0]
    p_tag.alignment = PP_ALIGN.CENTER
    p_tag.text = "ĐỒ ÁN TỐT NGHIỆP / BÁO CÁO KỸ THUẬT IoT & ROBOTICS"
    p_tag.font.name = FONT_MAIN
    p_tag.font.size = Pt(15)
    p_tag.font.bold = True
    p_tag.font.color.rgb = AMBER

    # Tên đề tài lớn
    title_box = slide.shapes.add_textbox(Inches(1.8), Inches(1.75), Inches(9.733), Inches(1.4))
    tf_title = title_box.text_frame
    tf_title.word_wrap = True
    p_title = tf_title.paragraphs[0]
    p_title.alignment = PP_ALIGN.CENTER
    p_title.text = "HỆ THỐNG HỖ TRỢ GẮP VẬT CHO CÁNH TAY ROBOT 4-DOF"
    p_title.font.name = FONT_MAIN
    p_title.font.size = Pt(32)
    p_title.font.bold = True
    p_title.font.color.rgb = PRIMARY_TEXT

    # Phụ đề công nghệ
    sub_box = slide.shapes.add_textbox(Inches(1.8), Inches(3.1), Inches(9.733), Inches(0.5))
    tf_sub = sub_box.text_frame
    p_sub = tf_sub.paragraphs[0]
    p_sub.alignment = PP_ALIGN.CENTER
    p_sub.text = "Thị giác máy tính 2 Camera • Định vị ArUco • Nhận diện YOLO11 • Động học ngược"
    p_sub.font.name = FONT_MAIN
    p_sub.font.size = Pt(18)
    p_sub.font.color.rgb = MUTED_TEXT

    # 4 huy hiệu công nghệ (Pills)
    pill_w = Inches(2.25)
    pill_h = Inches(0.55)
    pills_data = [
        ("DUAL CAMERA", GREEN),
        ("ARUCO GRID A4", AMBER),
        ("YOLO11s MODEL", GREEN),
        ("ANALYTICAL IK", AMBER),
    ]
    start_x = Inches(1.8)
    gap_x = Inches(0.24)
    for i, (text, col) in enumerate(pills_data):
        x = start_x + i * (pill_w + gap_x)
        p_card = add_card(slide, x, Inches(3.75), pill_w, pill_h, bg_color=RGBColor(28, 30, 34), border_color=col, border_width=1.0)
        p_box = slide.shapes.add_textbox(x, Inches(3.75), pill_w, pill_h)
        tf_p = p_box.text_frame
        tf_p.vertical_anchor = MSO_ANCHOR.MIDDLE
        p_p = tf_p.paragraphs[0]
        p_p.alignment = PP_ALIGN.CENTER
        p_p.text = text
        p_p.font.name = FONT_CODE
        p_p.font.size = Pt(14)
        p_p.font.bold = True
        p_p.font.color.rgb = col

    # Dải phân cách thông tin
    sep = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(2.2), Inches(4.55), Inches(8.933), Inches(0.015))
    sep.fill.solid()
    sep.fill.fore_color.rgb = BORDER_COLOR
    sep.line.fill.background()

    # Bảng thông tin nhóm và giảng viên (2 cột)
    meta_box = slide.shapes.add_textbox(Inches(2.2), Inches(4.75), Inches(8.933), Inches(1.6))
    tf_meta = meta_box.text_frame
    tf_meta.word_wrap = True

    p1 = tf_meta.paragraphs[0]
    p1.text = "Sinh viên thực hiện: [...]                      Giảng viên hướng dẫn: [...]"
    p1.font.name = FONT_MAIN
    p1.font.size = Pt(17)
    p1.font.color.rgb = PRIMARY_TEXT

    p2 = tf_meta.add_paragraph()
    p2.text = "Lớp / Môn học: [...]                           Thời gian báo cáo: [...]"
    p2.font.name = FONT_MAIN
    p2.font.size = Pt(17)
    p2.font.color.rgb = MUTED_TEXT

    p3 = tf_meta.add_paragraph()
    p3.text = "Mã nguồn đồ án: GraspAssist4DOF + OpenCV + PyTorch + PCA9685 Firmware"
    p3.font.name = FONT_CODE
    p3.font.size = Pt(14)
    p3.font.color.rgb = AMBER

    set_speaker_notes(slide,
        "Kính thưa quý thầy cô và các bạn, hôm nay nhóm chúng em xin được trình bày đề tài: "
        "Hệ thống hỗ trợ gắp vật cho cánh tay robot 4 bậc tự do sử dụng 2 camera, ArUco, YOLO11 và động học ngược. "
        "Mục tiêu của dự án là xây dựng một hệ thống thị giác thông minh có khả năng quan sát không gian làm việc, "
        "tự động tính toán góc quay của từng khớp và hướng dẫn người điều khiển thao tác gắp vật một cách trực quan, chính xác. "
        "Sau đây, em xin phép đại diện nhóm đi vào chi tiết cấu trúc phần cứng và giải thuật phần mềm của hệ thống."
    )


# ==============================================================================
# SLIDE 2: BÀI TOÁN THỰC TẾ VÀ MỤC TIÊU HỆ THỐNG
# ==============================================================================
def build_slide_2(prs):
    slide = add_slide_with_bg(prs)
    add_header(slide, "ĐẶT VẤN ĐỀ & MỤC TIÊU", "BÀI TOÁN THỰC TẾ VÀ MỤC TIÊU GIẢI PHÁP")
    add_footer(slide, 2)

    # Cột trái: Thách thức thực tế (Viền Đỏ)
    card_l = add_card(slide, Inches(0.8), Inches(1.60), Inches(5.7), Inches(5.18),
                      border_color=RED, border_width=1.5)
    # Header thẻ trái
    box_lh = slide.shapes.add_textbox(Inches(1.1), Inches(1.75), Inches(5.1), Inches(0.45))
    tf_lh = box_lh.text_frame
    tf_lh.margin_left = tf_lh.margin_top = tf_lh.margin_right = tf_lh.margin_bottom = 0
    p_lh = tf_lh.paragraphs[0]
    p_lh.text = "THÁCH THỨC ĐIỀU KHIỂN THỦ CÔNG"
    p_lh.font.name = FONT_MAIN
    p_lh.font.size = Pt(20)
    p_lh.font.bold = True
    p_lh.font.color.rgb = RED

    # Nội dung thách thức
    box_lc = slide.shapes.add_textbox(Inches(1.1), Inches(2.30), Inches(5.1), Inches(4.3))
    tf_lc = box_lc.text_frame
    tf_lc.word_wrap = True
    tf_lc.margin_left = tf_lc.margin_top = tf_lc.margin_right = tf_lc.margin_bottom = 0

    challenges = [
        "Khó ước lượng không gian 3D: Người điều khiển khó phán đoán khoảng cách sâu và độ cao chỉ qua một góc nhìn duy nhất.",
        "Dò phím mò mẫm: Cánh tay 4 khớp tự do dễ bị va đập mặt bàn hoặc gạt đổ vật khi dịch chuyển các góc không đồng bộ.",
        "Thiếu phản hồi vị trí: Servo RC thông thường không có encoder phản hồi, dễ lệch góc khi chịu tải trọng vật nặng.",
        "Đánh giá chủ quan: Khó xác định vật đã kẹp chắc chắn hay chưa khi chưa nhấc hẳn lên khỏi vùng làm việc."
    ]
    for i, ch in enumerate(challenges):
        p = tf_lc.paragraphs[0] if i == 0 else tf_lc.add_paragraph()
        p.text = f"• {ch}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(16.5)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(8)

    # Cột phải: Mục tiêu giải pháp đề xuất (Viền Xanh lá)
    card_r = add_card(slide, Inches(6.833), Inches(1.60), Inches(5.7), Inches(5.18),
                      border_color=GREEN, border_width=1.5)
    # Header thẻ phải
    box_rh = slide.shapes.add_textbox(Inches(7.133), Inches(1.75), Inches(5.1), Inches(0.45))
    tf_rh = box_rh.text_frame
    tf_rh.margin_left = tf_rh.margin_top = tf_rh.margin_right = tf_rh.margin_bottom = 0
    p_rh = tf_rh.paragraphs[0]
    p_rh.text = "MỤC TIÊU & GIẢI PHÁP ĐỀ XUẤT"
    p_rh.font.name = FONT_MAIN
    p_rh.font.size = Pt(20)
    p_rh.font.bold = True
    p_rh.font.color.rgb = GREEN

    # Nội dung giải pháp
    box_rc = slide.shapes.add_textbox(Inches(7.133), Inches(2.30), Inches(5.1), Inches(4.3))
    tf_rc = box_rc.text_frame
    tf_rc.word_wrap = True
    tf_rc.margin_left = tf_rc.margin_top = tf_rc.margin_right = tf_rc.margin_bottom = 0

    solutions = [
        "Thị giác máy tính 2 Camera: Cam trên định vị phẳng (X, Y); Cam ngang kiểm tra cao độ (Z) và vạch nâng.",
        "Động học ngược giải tích (IK): Tự động tính toán góc 4 khớp chuẩn xác từng bước 5° và cảnh báo tầm với.",
        "Giao diện HUD hướng dẫn trực quan: Chỉ rõ từng phím bấm cần thao tác, số lần bấm và thứ tự di chuyển an toàn.",
        "Tự động thẩm định kết quả gắp: Hai camera độc lập tự động đối soát, phân loại lỗi trượt kẹp hoặc rơi vật."
    ]
    for i, sol in enumerate(solutions):
        p = tf_rc.paragraphs[0] if i == 0 else tf_rc.add_paragraph()
        p.text = f"• {sol}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(16.5)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(8)

    set_speaker_notes(slide,
        "Trong thực tế, việc điều khiển một cánh tay robot mini 4 bậc tự do gắp vật bằng tay cầm hoặc bàn phím "
        "thường gặp rất nhiều khó khăn do người vận hành không thể ước lượng chính xác khoảng cách 3 chiều và góc khớp. "
        "Để giải quyết bài toán này, nhóm đã xây dựng giải pháp hỗ trợ thông minh: sử dụng camera góc trên để định vị vật thể "
        "và giải động học ngược, kết hợp camera góc ngang để kiểm tra độ cao. Hệ thống đóng vai trò như một người trợ lý ảo, "
        "đưa ra hướng dẫn từng bước phím bấm và tự động đánh giá xem vật đã được gắp thành công hay chưa."
    )


# ==============================================================================
# SLIDE 3: KIẾN TRÚC VÀ THIẾT BỊ PHẦN CỨNG
# ==============================================================================
def build_slide_3(prs):
    slide = add_slide_with_bg(prs)
    add_header(slide, "THIẾT BỊ & PHẦN CỨNG", "KIẾN TRÚC VÀ THIẾT BỊ PHẦN CỨNG HỆ THỐNG")
    add_footer(slide, 3)

    # 3 Cột chức năng phần cứng
    col_w = Inches(3.7)
    col_h = Inches(5.18)
    cols_x = [Inches(0.8), Inches(4.816), Inches(8.833)]

    # Cột 1: Cơ cấu chấp hành & Servo
    add_card(slide, cols_x[0], Inches(1.60), col_w, col_h)
    box1 = slide.shapes.add_textbox(cols_x[0] + Inches(0.2), Inches(1.75), col_w - Inches(0.4), col_h - Inches(0.3))
    tf1 = box1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_right = tf1.margin_top = tf1.margin_bottom = 0
    p1 = tf1.paragraphs[0]
    p1.text = "CƠ CẤU CHẤP HÀNH"
    p1.font.name = FONT_MAIN
    p1.font.size = Pt(20)
    p1.font.bold = True
    p1.font.color.rgb = AMBER
    p1.space_after = Pt(8)

    items1 = [
        "4x Động cơ RC Servo MG996R: Bánh răng kim loại, lực kéo cao.",
        "Kênh 0 (Đế): Quay 0° – 180° (Mặc định 90° hướng thẳng).",
        "Kênh 1 (Vai): Nâng hạ 25° – 155° (Mặc định 90°).",
        "Kênh 2 (Khuỷu): Gập duỗi 25° – 155° (Mặc định 90°).",
        "Kênh 3 (Kẹp): Đóng mở 95° – 175° (95° mở rộng, 165° kẹp chặt)."
    ]
    for item in items1:
        p = tf1.add_paragraph()
        p.text = f"• {item}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(15)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(6)

    # Cột 2: Điều khiển xung & Vi điều khiển
    add_card(slide, cols_x[1], Inches(1.60), col_w, col_h)
    box2 = slide.shapes.add_textbox(cols_x[1] + Inches(0.2), Inches(1.75), col_w - Inches(0.4), col_h - Inches(0.3))
    tf2 = box2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_right = tf2.margin_top = tf2.margin_bottom = 0
    p2 = tf2.paragraphs[0]
    p2.text = "ĐIỀU KHIỂN & KẾT NỐI"
    p2.font.name = FONT_MAIN
    p2.font.size = Pt(20)
    p2.font.bold = True
    p2.font.color.rgb = GREEN
    p2.space_after = Pt(8)

    items2 = [
        "Mạch xung PCA9685: Chuẩn I2C địa chỉ 0x40, tần số 50Hz cấp xung servo.",
        "Độ rộng xung PWM: 125 (~0°) đến 575 (~180°) xung 12-bit.",
        "Vi điều khiển trung tâm: Bo mạch Arduino [...] cấp xung và đọc lệnh 9600 baud.",
        "Module Bluetooth HC-05: Chân RX=D2, TX=D3, baud 9600, MAC 98D351F6AF14.",
        "Nguồn rời 5V–6V dòng cao: Nuôi riêng 4 servo, chống sụt áp reset Arduino."
    ]
    for item in items2:
        p = tf2.add_paragraph()
        p.text = f"• {item}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(15)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(6)

    # Cột 3: Cảm biến thị giác & Máy tính trạm
    add_card(slide, cols_x[2], Inches(1.60), col_w, col_h)
    box3 = slide.shapes.add_textbox(cols_x[2] + Inches(0.2), Inches(1.75), col_w - Inches(0.4), col_h - Inches(0.3))
    tf3 = box3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_right = tf3.margin_top = tf3.margin_bottom = 0
    p3 = tf3.paragraphs[0]
    p3.text = "THỊ GIÁC & MÁY TRẠM"
    p3.font.name = FONT_MAIN
    p3.font.size = Pt(20)
    p3.font.bold = True
    p3.font.color.rgb = AMBER
    p3.space_after = Pt(8)

    items3 = [
        "Cam 1 (Nhìn ngang): Webcam laptop đặt thấp quan sát cao độ gắp.",
        "Cam 2 (Nhìn trên xuống): Camera điện thoại gắn giá cao vuông góc mặt bàn.",
        "Hỗ trợ kết nối Cam 2: iPhone Continuity, Iriun, DroidCam, Wi-Fi IP Webcam.",
        "Máy tính xử lý trung tâm: Laptop [...] chạy mô hình YOLO11s và giải IK.",
        "Tăng tốc phần cứng: Tự động nhận diện PyTorch MPS (Apple Silicon), CUDA hoặc CPU."
    ]
    for item in items3:
        p = tf3.add_paragraph()
        p.text = f"• {item}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(15)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(6)

    set_speaker_notes(slide,
        "Về mặt phần cứng, cánh tay robot sử dụng 4 servo MG996R bánh răng kim loại, mang lại lực kẹp và độ ổn định cao. "
        "Do dòng khởi động của 4 servo khá lớn, nhóm sử dụng module mở rộng PCA9685 giao tiếp qua chuẩn I2C địa chỉ 0x40 ở tần số 50Hz, "
        "được cấp nguồn rời từ 5 đến 6V độc lập với Arduino. Dữ liệu điều khiển được truyền từ máy tính xử lý trung tâm xuống Arduino "
        "thông qua cáp USB hoặc module Bluetooth HC-05 gắn ở chân D2 và D3 với tốc độ 9600 baud."
    )


# ==============================================================================
# SLIDE 4: KIẾN TRÚC PHẦN MỀM VÀ LUỒNG XỬ LÝ
# ==============================================================================
def build_slide_4(prs):
    slide = add_slide_with_bg(prs)
    add_header(slide, "KIẾN TRÚC PHẦN MỀM", "KIẾN TRÚC PHẦN MỀM VÀ LUỒNG DỮ LIỆU THỜI GIAN THỰC")
    add_footer(slide, 4)

    # Sơ đồ khối Native PowerPoint Shapes
    # Hàng 1: Hai camera đầu vào
    cam1 = add_card(slide, Inches(0.8), Inches(1.7), Inches(2.5), Inches(1.0), bg_color=RGBColor(32, 35, 40), border_color=AMBER)
    b_c1 = slide.shapes.add_textbox(Inches(0.8), Inches(1.7), Inches(2.5), Inches(1.0))
    tf_c1 = b_c1.text_frame
    tf_c1.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf_c1.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "Cam 1: Ngang (Webcam)\nCameraStream (Buffer=1)"
    p.font.name = FONT_MAIN
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_TEXT

    cam2 = add_card(slide, Inches(0.8), Inches(3.0), Inches(2.5), Inches(1.0), bg_color=RGBColor(32, 35, 40), border_color=AMBER)
    b_c2 = slide.shapes.add_textbox(Inches(0.8), Inches(3.0), Inches(2.5), Inches(1.0))
    tf_c2 = b_c2.text_frame
    tf_c2.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf_c2.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "Cam 2: Trên (Điện thoại)\nCameraStream (Buffer=1)"
    p.font.name = FONT_MAIN
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_TEXT

    # Mũi tên từ 2 Cam vào Tracker
    add_arrow(slide, Inches(3.4), Inches(2.6), Inches(0.6), Inches(0.3), color=AMBER)

    # Khối 2: ArucoYoloTracker
    tracker = add_card(slide, Inches(4.1), Inches(1.9), Inches(2.8), Inches(1.8), bg_color=RGBColor(32, 35, 40), border_color=GREEN)
    b_tr = slide.shapes.add_textbox(Inches(4.1), Inches(1.9), Inches(2.8), Inches(1.8))
    tf_tr = b_tr.text_frame
    tf_tr.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf_tr.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "ArucoYoloTracker\n• YOLO11s (Luồng nền)\n• ArUco ID 0-3 góc A4\n• Homography (px → cm)\n• Lọc SMA-10 khung hình"
    p.font.name = FONT_MAIN
    p.font.size = Pt(14)
    p.font.color.rgb = PRIMARY_TEXT

    # Mũi tên từ Tracker vào GraspAssist
    add_arrow(slide, Inches(7.0), Inches(2.6), Inches(0.6), Inches(0.3), color=GREEN)

    # Khối 3: GraspAssist4DOF
    assist = add_card(slide, Inches(7.5), Inches(1.7), Inches(5.0), Inches(2.2), bg_color=RGBColor(35, 42, 38), border_color=GREEN)
    b_as = slide.shapes.add_textbox(Inches(7.5), Inches(1.7), Inches(5.0), Inches(2.2))
    tf_as = b_as.text_frame
    tf_as.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_as.margin_left = tf_as.margin_right = tf_as.margin_top = tf_as.margin_bottom = 0
    p = tf_as.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "GraspAssist4DOF (Bộ điều phối trung tâm)\n• Động học ngược giải tích IK (Nghiệm khuỷu lên)\n• Máy trạng thái 5 bước gắp (Điểm chờ → Kiểm tra)\n• Phím bấm WASD/IK/JL bước 5° & Auto-Step (P)\n• Xác nhận 2 camera S1 + S2 (80%, Timeout 3s)"
    p.font.name = FONT_MAIN
    p.font.size = Pt(14)
    p.font.color.rgb = PRIMARY_TEXT

    # Phân nhánh xuống giao tiếp phần cứng và hiển thị
    add_arrow(slide, Inches(8.5), Inches(4.0), Inches(0.3), Inches(0.5), color=AMBER, direction="down")
    add_arrow(slide, Inches(11.0), Inches(4.0), Inches(0.3), Inches(0.5), color=GREEN, direction="down")

    # Khối 4: Giao tiếp phần cứng Arduino
    hw_card = add_card(slide, Inches(6.8), Inches(4.6), Inches(3.6), Inches(1.9), bg_color=RGBColor(32, 35, 40), border_color=BORDER_COLOR)
    b_hw = slide.shapes.add_textbox(Inches(6.8), Inches(4.6), Inches(3.6), Inches(1.9))
    tf_hw = b_hw.text_frame
    tf_hw.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_hw.margin_left = tf_hw.margin_right = tf_hw.margin_top = tf_hw.margin_bottom = 0
    p = tf_hw.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "ArduinoSerialLink & Phần cứng\n• USB Serial / Bluetooth HC-05 (9600)\n• Gói tin JSON trạng thái góc 5Hz\n• PCA9685 I2C 0x40 50Hz\n• 4x Servo MG996R"
    p.font.name = FONT_MAIN
    p.font.size = Pt(14)
    p.font.color.rgb = PRIMARY_TEXT

    # Khối 5: Giao diện hiển thị kép
    ui_card = add_card(slide, Inches(10.6), Inches(4.6), Inches(1.9), Inches(1.9), bg_color=RGBColor(32, 35, 40), border_color=AMBER)
    b_ui = slide.shapes.add_textbox(Inches(10.6), Inches(4.6), Inches(1.9), Inches(1.9))
    tf_ui = b_ui.text_frame
    tf_ui.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_ui.margin_left = tf_ui.margin_right = tf_ui.margin_top = tf_ui.margin_bottom = 0
    p = tf_ui.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "Giao diện kép\n• Thanh HUD\n  (1280 × 175)\n• Cửa sổ Hướng dẫn\n  (1280 × 800)"
    p.font.name = FONT_MAIN
    p.font.size = Pt(14)
    p.font.color.rgb = PRIMARY_TEXT

    # Khối tóm tắt đặc tính kiến trúc (Bên trái dưới)
    summary_card = add_card(slide, Inches(0.8), Inches(4.4), Inches(5.8), Inches(2.1))
    b_sm = slide.shapes.add_textbox(Inches(1.0), Inches(4.5), Inches(5.4), Inches(1.9))
    tf_sm = b_sm.text_frame
    tf_sm.word_wrap = True
    tf_sm.margin_left = tf_sm.margin_right = tf_sm.margin_top = tf_sm.margin_bottom = 0
    p_sm = tf_sm.paragraphs[0]
    p_sm.text = "ĐẶC ĐIỂM THIẾT KẾ ĐA LUỒNG & CHỐNG TRỄ"
    p_sm.font.name = FONT_MAIN
    p_sm.font.size = Pt(16)
    p_sm.font.bold = True
    p_sm.font.color.rgb = AMBER
    p_sm.space_after = Pt(6)

    bullets = [
        "Zero-latency buffer: CameraStream duy trì buffersize=1, chống tích tụ trễ khung hình.",
        "YOLO Worker nền: Tách biệt luồng nhận diện AI giúp giao diện luôn giữ mượt mà 30+ FPS.",
        "Watchdog 4s: Tự động khởi động lại camera nếu mất tín hiệu video."
    ]
    for b in bullets:
        p = tf_sm.add_paragraph()
        p.text = f"• {b}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(14)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(4)

    set_speaker_notes(slide,
        "Kiến trúc phần mềm của hệ thống được tổ chức hoàn toàn theo hướng đa luồng để triệt tiêu độ trễ hình ảnh. "
        "Luồng CameraStream liên tục bắt khung hình mới nhất từ 2 camera, trong khi mô hình YOLO11 chạy trên một worker riêng "
        "để không gây sụt giảm FPS hiển thị. Tọa độ vật thể được ánh xạ từ pixel sang centimet thông qua ma trận Homography, "
        "sau đó đưa vào module GraspAssist4DOF để tính toán động học ngược. Kết quả góc quay được đồng bộ hai chiều với Arduino "
        "qua giao thức JSON ở tần số 5Hz và hiển thị trực quan lên cửa sổ hướng dẫn."
    )


# ==============================================================================
# SLIDE 5: THIẾT LẬP KHÔNG GIAN BÀN VÀ LƯỚI MÃ ARUCO
# ==============================================================================
def build_slide_5(prs):
    slide = add_slide_with_bg(prs)
    add_header(slide, "HỆ TỌA ĐỘ & ĐỊNH VỊ", "THIẾT LẬP KHÔNG GIAN BÀN VÀ LƯỚI MÃ ARUCO")
    add_footer(slide, 5)

    col_w = Inches(3.7)
    col_h = Inches(5.18)
    cols_x = [Inches(0.8), Inches(4.816), Inches(8.833)]

    # Cột 1: Tờ A4 & 4 góc ArUco
    add_card(slide, cols_x[0], Inches(1.60), col_w, col_h)
    box1 = slide.shapes.add_textbox(cols_x[0] + Inches(0.2), Inches(1.75), col_w - Inches(0.4), col_h - Inches(0.3))
    tf1 = box1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_right = tf1.margin_top = tf1.margin_bottom = 0
    p1 = tf1.paragraphs[0]
    p1.text = "LƯỚI ARUCO TỜ A4"
    p1.font.name = FONT_MAIN
    p1.font.size = Pt(20)
    p1.font.bold = True
    p1.font.color.rgb = AMBER
    p1.space_after = Pt(8)

    items1 = [
        "Khổ giấy A4 đặt ngang: Rộng W = 29.7 cm, Dài H = 21.0 cm.",
        "Bộ từ điển ArUco: DICT_4X4_50 (50 mã 4x4 bit, nhận diện nhanh).",
        "Kích thước mã in: 2.8 x 2.8 cm, đặt cách mép giấy 0.25 cm.",
        "ID 0 (Góc Trên-Trái): Gốc O (0.0, 0.0 cm).",
        "ID 1 (Góc Trên-Phải): Trục X (29.7, 0.0 cm).",
        "ID 2 (Góc Dưới-Phải): Điểm cực (29.7, 21.0 cm).",
        "ID 3 (Góc Dưới-Trái): Trục Y (0.0, 21.0 cm)."
    ]
    for item in items1:
        p = tf1.add_paragraph()
        p.text = f"• {item}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(14.5)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(5)

    # Cột 2: Phân bổ mã ArUco toàn hệ thống
    add_card(slide, cols_x[1], Inches(1.60), col_w, col_h)
    box2 = slide.shapes.add_textbox(cols_x[1] + Inches(0.2), Inches(1.75), col_w - Inches(0.4), col_h - Inches(0.3))
    tf2 = box2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_right = tf2.margin_top = tf2.margin_bottom = 0
    p2 = tf2.paragraphs[0]
    p2.text = "PHÂN BỔ MÃ TOÀN HỆ THỐNG"
    p2.font.name = FONT_MAIN
    p2.font.size = Pt(20)
    p2.font.bold = True
    p2.font.color.rgb = GREEN
    p2.space_after = Pt(8)

    items2 = [
        "ID 4 (Đế Robot): Tự động hiệu chỉnh tọa độ base_x_cm, base_y_cm.",
        "ID 5 (Đầu kẹp - Cam trên): Phản hồi vị trí kẹp thực tế (Closed-loop).",
        "ID 6 (Đầu kẹp - Cam ngang): Loại trừ khỏi S1 để chống báo gắp giả.",
        "ID 10–13: Vật mẫu (Hộp vuông 40mm, Hộp xanh 35x50mm, Hộp đỏ 30x60mm, Trụ 35x50mm).",
        "ID 14–29: Dải mã dự phòng cho các vật thể kiểm thử khác (35x35x40 mm)."
    ]
    for item in items2:
        p = tf2.add_paragraph()
        p.text = f"• {item}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(14.5)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(6)

    # Cột 3: Giải thuật Homography & Dự phòng
    add_card(slide, cols_x[2], Inches(1.60), col_w, col_h)
    box3 = slide.shapes.add_textbox(cols_x[2] + Inches(0.2), Inches(1.75), col_w - Inches(0.4), col_h - Inches(0.3))
    tf3 = box3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_right = tf3.margin_top = tf3.margin_bottom = 0
    p3 = tf3.paragraphs[0]
    p3.text = "HOMOGRAPHY & DỰ PHÒNG"
    p3.font.name = FONT_MAIN
    p3.font.size = Pt(20)
    p3.font.bold = True
    p3.font.color.rgb = AMBER
    p3.space_after = Pt(8)

    items3 = [
        "Ma trận Homography H: Chuyển đổi chính xác tọa độ pixel sang cm mặt bàn.",
        "Ánh xạ 8–16 điểm góc: Khớp 4 điểm góc của các mã ArUco thật với tọa độ cm.",
        "Ma trận nghịch đảo H_inv: Chiếu ngược tọa độ centimet lên pixel để vẽ thước đo.",
        "Dự phòng phân đoạn màu LAB: Tách nền giấy trắng (L:130-255, A:0-134, B:125-255) khi che mã.",
        "Gán ArUco ảo: Dán mã ảo bù trừ viền Quiet Zone nếu chưa in mã thật."
    ]
    for item in items3:
        p = tf3.add_paragraph()
        p.text = f"• {item}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(14.5)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(5)

    set_speaker_notes(slide,
        "Để xác định không gian làm việc một cách tuyệt đối, nhóm sử dụng một tờ giấy A4 đặt ngang kích thước 29.7 nhân 21 centimet làm mặt bàn chuẩn. "
        "Bốn góc tờ giấy được in 4 mã ArUco thuộc bộ từ điển DICT_4X4_50 từ ID 0 đến ID 3, mỗi mã có kích thước 2.8 centimet và đặt cách mép 2.5 milimet để OpenCV dễ dàng bắt góc. "
        "Hệ thống còn quy ước mã ID 4 gắn trên đế robot, mã ID 5 và 6 gắn trên đầu kẹp, cùng dải mã từ 10 đến 29 dành cho các vật thể. "
        "Nếu có góc bị che khuất, thuật toán phân đoạn màu LAB sẽ tự động kích hoạt để tìm biên giấy dự phòng."
    )


# ==============================================================================
# SLIDE 6: NHẬN DIỆN VẬT THỂ VÀ HỢP NHẤT DỮ LIỆU THỊ GIÁC
# ==============================================================================
def build_slide_6(prs):
    slide = add_slide_with_bg(prs)
    add_header(slide, "THỊ GIÁC MÁY TÍNH & AI", "NHẬN DIỆN VẬT THỂ VÀ HỢP NHẤT DỮ LIỆU THỊ GIÁC")
    add_footer(slide, 6)

    col_w = Inches(3.7)
    col_h = Inches(5.18)
    cols_x = [Inches(0.8), Inches(4.816), Inches(8.833)]

    # Cột 1: YOLO11s Luồng nền
    add_card(slide, cols_x[0], Inches(1.60), col_w, col_h)
    box1 = slide.shapes.add_textbox(cols_x[0] + Inches(0.2), Inches(1.75), col_w - Inches(0.4), col_h - Inches(0.3))
    tf1 = box1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_right = tf1.margin_top = tf1.margin_bottom = 0
    p1 = tf1.paragraphs[0]
    p1.text = "MÔ HÌNH YOLO11s"
    p1.font.name = FONT_MAIN
    p1.font.size = Pt(20)
    p1.font.bold = True
    p1.font.color.rgb = AMBER
    p1.space_after = Pt(8)

    items1 = [
        "Mô hình học sâu: YOLO11s chạy suy luận trên luồng nền độc lập.",
        "Vùng cắt A4: Cắt bao quanh tứ giác A4 (lề an toàn 10px), triệt nhiễu.",
        "Tham số Cam trên: conf = 0.12, imgsz = 960 phát hiện vật nhỏ.",
        "Lọc diện tích: Bỏ hộp quá lớn (> 40% A4) hoặc quá nhỏ (< 400 px²).",
        "Kiểm tra mép: Tâm vật cách mép tờ A4 tối thiểu 15 px."
    ]
    for item in items1:
        p = tf1.add_paragraph()
        p.text = f"• {item}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(14.5)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(5)

    # Cột 2: Dung hợp ArUco - YOLO11
    add_card(slide, cols_x[1], Inches(1.60), col_w, col_h)
    box2 = slide.shapes.add_textbox(cols_x[1] + Inches(0.2), Inches(1.75), col_w - Inches(0.4), col_h - Inches(0.3))
    tf2 = box2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_right = tf2.margin_top = tf2.margin_bottom = 0
    p2 = tf2.paragraphs[0]
    p2.text = "DUNG HỢP DỮ LIỆU"
    p2.font.name = FONT_MAIN
    p2.font.size = Pt(20)
    p2.font.bold = True
    p2.font.color.rgb = GREEN
    p2.space_after = Pt(8)

    items2 = [
        "Ưu tiên ArUco ID 10–29: Cung cấp chính xác kích thước 3 chiều (w, l, h).",
        "Khử trùng lặp (Threshold < 2.5 cm): Nếu YOLO cách ArUco < 2.5 cm thì bỏ YOLO.",
        "Bổ sung vật YOLO: Nếu cách xa >= 2.5 cm, gán nhãn YOLO:<cls> (35x40 mm).",
        "Sắp xếp theo độ gần: Ưu tiên gắp vật thể có khoảng cách gần đế robot nhất.",
        "Phím TAB / V: Chuyển đổi mục tiêu gắp cho người vận hành."
    ]
    for item in items2:
        p = tf2.add_paragraph()
        p.text = f"• {item}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(14.5)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(5)

    # Cột 3: Bộ lọc SMA-10 & Xử lý Cam ngang
    add_card(slide, cols_x[2], Inches(1.60), col_w, col_h)
    box3 = slide.shapes.add_textbox(cols_x[2] + Inches(0.2), Inches(1.75), col_w - Inches(0.4), col_h - Inches(0.3))
    tf3 = box3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_right = tf3.margin_top = tf3.margin_bottom = 0
    p3 = tf3.paragraphs[0]
    p3.text = "LỌC TỌA ĐỘ & CAM NGANG"
    p3.font.name = FONT_MAIN
    p3.font.size = Pt(20)
    p3.font.bold = True
    p3.font.color.rgb = AMBER
    p3.space_after = Pt(8)

    items3 = [
        "Lọc trung bình trượt 10 khung hình: deque(maxlen=10) khử rung lắc.",
        "Tọa độ cấp cho IK: Tính trung bình cộng của 10 vị trí gần nhất.",
        "Nhận diện Cam ngang: conf = 0.20, imgsz = 640 lọc nhiễu bàn ghế, laptop.",
        "Điểm chân đế vật: cy_base = y2 - 0.30*(y2 - y1) kiểm tra nằm vùng bàn.",
        "Vạch tham chiếu mặt bàn: Tỉ lệ SIDE_TABLE_Y_RATIO = 0.54 xác định cao độ."
    ]
    for item in items3:
        p = tf3.add_paragraph()
        p.text = f"• {item}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(14.5)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(5)

    set_speaker_notes(slide,
        "Nhằm tối ưu độ chính xác và khả năng thích ứng linh hoạt, hệ thống kết hợp song song cả mô hình học sâu YOLO11s và mã ArUco. "
        "Mô hình YOLO11s được cắt vùng xử lý sát bề mặt tờ A4 để loại bỏ nhiễu từ tay người hay bàn ghế xung quanh, trong khi các vật mẫu "
        "dán mã ArUco ID 10 đến 29 sẽ cung cấp ngay kích thước ba chiều thật từ bảng cấu hình. Hai nguồn dữ liệu này được khử trùng lặp "
        "với ngưỡng khoảng cách 2.5 centimet, sau đó làm mịn qua bộ lọc trung bình trượt 10 khung hình và ưu tiên gắp vật thể nằm gần đế robot nhất."
    )


# ==============================================================================
# SLIDE 7: ĐỘNG HỌC CÁNH TAY ROBOT VÀ QUY ĐỔI SERVO
# ==============================================================================
def build_slide_7(prs):
    slide = add_slide_with_bg(prs)
    add_header(slide, "ĐỘNG HỌC ROBOT 4-DOF", "ĐỘNG HỌC CÁNH TAY ROBOT VÀ QUY ĐỔI SERVO ARDUINO")
    add_footer(slide, 7)

    col_w = Inches(3.7)
    col_h = Inches(5.18)
    cols_x = [Inches(0.8), Inches(4.816), Inches(8.833)]

    # Cột 1: Kích thước cơ khí ARM_CONFIG
    add_card(slide, cols_x[0], Inches(1.60), col_w, col_h)
    box1 = slide.shapes.add_textbox(cols_x[0] + Inches(0.2), Inches(1.75), col_w - Inches(0.4), col_h - Inches(0.3))
    tf1 = box1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_right = tf1.margin_top = tf1.margin_bottom = 0
    p1 = tf1.paragraphs[0]
    p1.text = "THÔNG SỐ CƠ KHÍ"
    p1.font.name = FONT_MAIN
    p1.font.size = Pt(20)
    p1.font.bold = True
    p1.font.color.rgb = AMBER
    p1.space_after = Pt(8)

    items1 = [
        "Chiều cao trục vai d1: 70.0 mm (mặt bàn tới trục servo Vai).",
        "Khâu vai L2: 105.0 mm (Upper arm: Trục Vai → Trục Khuỷu).",
        "Khâu khuỷu L3: 100.0 mm (Forearm: Trục Khuỷu → Khớp kẹp).",
        "Độ vươn kẹp L4_r: 65.0 mm (khoảng cách ngang tới tâm ngón).",
        "Độ trễ kẹp L4_z: 25.0 mm (khoảng cách dọc hạ thấp đầu kẹp).",
        "Tầm với: Tối đa L2 + L3 = 205.0 mm, tối thiểu |L2 - L3| = 5.0 mm."
    ]
    for item in items1:
        p = tf1.add_paragraph()
        p.text = f"• {item}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(14.5)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(5)

    # Cột 2: Công thức Động học ngược giải tích
    add_card(slide, cols_x[1], Inches(1.60), col_w, col_h)
    box2 = slide.shapes.add_textbox(cols_x[1] + Inches(0.2), Inches(1.75), col_w - Inches(0.4), col_h - Inches(0.3))
    tf2 = box2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_right = tf2.margin_top = tf2.margin_bottom = 0
    p2 = tf2.paragraphs[0]
    p2.text = "ĐỘNG HỌC NGƯỢC (IK)"
    p2.font.name = FONT_MAIN
    p2.font.size = Pt(20)
    p2.font.bold = True
    p2.font.color.rgb = GREEN
    p2.space_after = Pt(8)

    items2 = [
        "Tâm cổ tay rw, zw: rw = max(5, r - L4_r), zw = (z + L4_z) - d1.",
        "Định lý cosin: D = (rw² + zw² - L2² - L3²) / (2*L2*L3).",
        "Điều kiện với tới: |D| <= 1.0 và r >= L4_r + 2.5 mm.",
        "Nghiệm khuỷu lên (Elbow-up): sin(θ3) <= 0 tránh chạm bàn:",
        "θ3 = atan2(-sqrt(1 - D²), D)",
        "θ2 = atan2(zw, rw) - atan2(L3*sin(θ3), L2 + L3*cos(θ3))",
        "Góc xoay đế: θ1 = atan2(y, x) tính theo tọa độ robot."
    ]
    for item in items2:
        p = tf2.add_paragraph()
        p.text = f"• {item}" if not item.startswith("θ") else f"   {item}"
        p.font.name = FONT_CODE if item.startswith("θ") or "D =" in item else FONT_MAIN
        p.font.size = Pt(14)
        p.font.color.rgb = AMBER if item.startswith("θ") else PRIMARY_TEXT
        p.space_after = Pt(4)

    # Cột 3: Ánh xạ Servo Arduino & Giới hạn
    add_card(slide, cols_x[2], Inches(1.60), col_w, col_h)
    box3 = slide.shapes.add_textbox(cols_x[2] + Inches(0.2), Inches(1.75), col_w - Inches(0.4), col_h - Inches(0.3))
    tf3 = box3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_right = tf3.margin_top = tf3.margin_bottom = 0
    p3 = tf3.paragraphs[0]
    p3.text = "QUY ĐỔI SERVO ARDUINO"
    p3.font.name = FONT_MAIN
    p3.font.size = Pt(20)
    p3.font.bold = True
    p3.font.color.rgb = AMBER
    p3.space_after = Pt(8)

    items3 = [
        "Quy ước chuẩn 90°: θ2 = 45.0°, θ3 = -45.0° (vị trí cân bằng).",
        "Servo Đế: raw_base = 90.0 + θ1 (Dải [0°, 180°]).",
        "Servo Vai: raw_shoulder = 90.0 + (θ2 - 45.0°) (Dải [25°, 155°]).",
        "Servo Khuỷu: raw_elbow = 90.0 + (θ3 + 45.0°) (Dải [25°, 155°]).",
        "Servo Kẹp: Mở 95° – 125°, Kẹp chặt 165° (Dải [95°, 175°]).",
        "Lượng tử hóa: SERVO_STEP_DEG = 5° (snap_and_clamp).",
        "Cảnh báo đỏ: Khi góc yêu cầu chạm giới hạn cứng."
    ]
    for item in items3:
        p = tf3.add_paragraph()
        p.text = f"• {item}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(14)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(4)

    set_speaker_notes(slide,
        "Cấu trúc cơ học của cánh tay được xác định bởi các thông số thực tế đo bằng thước: chiều cao khớp vai d1 bằng 70mm, "
        "khâu vai L2 dài 105mm, khâu khuỷu L3 dài 100mm, cùng độ vươn đầu kẹp L4r bằng 65mm. Thuật toán IK giải tích chọn nghiệm "
        "khuỷu hướng lên để tối ưu không gian vận động và tránh va quẹt với mặt bàn. Các góc khớp sau khi giải sẽ được ánh xạ sang góc xung servo "
        "với quy ước chuẩn 90 độ tương ứng theta2 bằng 45 độ và theta3 bằng âm 45 độ, sau đó làm tròn theo bước nhảy 5 độ nằm trong dải giới hạn an toàn tuyệt đối."
    )


# ==============================================================================
# SLIDE 8: CHUYỂN ĐỔI HỆ TỌA ĐỘ VÀ VÙNG LÀM VIỆC AN TOÀN
# ==============================================================================
def build_slide_8(prs):
    slide = add_slide_with_bg(prs)
    add_header(slide, "KHÔNG GIAN BÀN & AN TOÀN", "CHUYỂN ĐỔI HỆ TỌA ĐỘ VÀ VÙNG LÀM VIỆC AN TOÀN")
    add_footer(slide, 8)

    # Bố cục 2 cột
    card_l = add_card(slide, Inches(0.8), Inches(1.60), Inches(5.7), Inches(5.18))
    box_lh = slide.shapes.add_textbox(Inches(1.1), Inches(1.75), Inches(5.1), Inches(0.45))
    tf_lh = box_lh.text_frame
    tf_lh.margin_left = tf_lh.margin_top = tf_lh.margin_right = tf_lh.margin_bottom = 0
    p_lh = tf_lh.paragraphs[0]
    p_lh.text = "CHUYỂN ĐỔI TỌA ĐỘ A4 → ROBOT"
    p_lh.font.name = FONT_MAIN
    p_lh.font.size = Pt(20)
    p_lh.font.bold = True
    p_lh.font.color.rgb = AMBER

    box_lc = slide.shapes.add_textbox(Inches(1.1), Inches(2.25), Inches(5.1), Inches(4.4))
    tf_lc = box_lc.text_frame
    tf_lc.word_wrap = True
    tf_lc.margin_left = tf_lc.margin_top = tf_lc.margin_right = tf_lc.margin_bottom = 0

    items_l = [
        "Vị trí Đế Robot trên tờ A4: base_x_cm = 18.0, base_y_cm = -13.6 cm.",
        "Hướng đặt: robot_faces = 'down' (đế mép trên, vươn xuống bàn, hệ số s = -1.0).",
        "Công thức tọa độ Robot (mm):",
        "x_robot_mm = (y_cm - base_y_cm) * 10 = (y_cm + 13.6) * 10",
        "y_robot_mm = (x_cm - base_x_cm) * 10 = (x_cm - 18.0) * 10",
        "Chiều trục: +X_robot vươn sâu vào giấy, +Y_robot hướng sang bên trái.",
        "Thuận nghịch: robot_mm_to_table_cm() ánh xạ ngược chính xác sai số < 1e-9 cm."
    ]
    for item in items_l:
        p = tf_lc.add_paragraph()
        p.text = item if item.startswith("x_") or item.startswith("y_") else f"• {item}"
        p.font.name = FONT_CODE if "x_" in item or "y_" in item else FONT_MAIN
        p.font.size = Pt(15)
        p.font.color.rgb = AMBER if "x_" in item or "y_" in item else PRIMARY_TEXT
        p.space_after = Pt(5)

    card_r = add_card(slide, Inches(6.833), Inches(1.60), Inches(5.7), Inches(5.18))
    box_rh = slide.shapes.add_textbox(Inches(7.133), Inches(1.75), Inches(5.1), Inches(0.45))
    tf_rh = box_rh.text_frame
    tf_rh.margin_left = tf_rh.margin_top = tf_rh.margin_right = tf_rh.margin_bottom = 0
    p_rh = tf_rh.paragraphs[0]
    p_rh.text = "KIỂM SOÁT VÙNG AN TOÀN & CẢNH BÁO"
    p_rh.font.name = FONT_MAIN
    p_rh.font.size = Pt(20)
    p_rh.font.bold = True
    p_rh.font.color.rgb = GREEN

    box_rc = slide.shapes.add_textbox(Inches(7.133), Inches(2.25), Inches(5.1), Inches(4.4))
    tf_rc = box_rc.text_frame
    tf_rc.word_wrap = True
    tf_rc.margin_left = tf_rc.margin_top = tf_rc.margin_right = tf_rc.margin_bottom = 0

    items_r = [
        "Tầm với tối đa: max_reach = 205.0 mm (khoảng cách cổ tay rw² + zw²).",
        "Tầm với tối thiểu: min_reach = 5.0 mm (tránh điểm kỳ dị khâu gập sát đế).",
        "Cảnh báo NGOÀI TẦM VỚI: Hiển thị chữ đỏ rực rỡ khi khoảng cách dist > 205.0 mm.",
        "Khoảng cách dời vật: move_closer_mm = dist - (max_reach - 2.0 mm) báo số mm cần đẩy lại gần.",
        "Cảnh báo kẹp servo: Phát hiện khi góc yêu cầu vượt ngưỡng [lo - 2.5°, hi + 2.5°].",
        "Cập nhật vị trí đế qua ID 4: Tự động hiệu chỉnh lại base_x, base_y nếu tờ A4 bị xê dịch."
    ]
    for item in items_r:
        p = tf_rc.add_paragraph()
        p.text = f"• {item}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(15)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(5)

    set_speaker_notes(slide,
        "Do camera đo đạc vật thể trên hệ tọa độ centimet của tờ giấy A4, hệ thống cần chuyển đổi sang hệ quy chiếu milimet lấy gốc tại đế robot. "
        "Trong bố cục hiện tại, robot đặt ở mép trên tại tọa độ X bằng 18 và Y bằng âm 13.6 centimet, vươn xuống với cấu hình robot_faces bằng 'down'. "
        "Nếu mục tiêu nằm ngoài tầm với tối đa 205 milimet, hệ thống sẽ phát cảnh báo đỏ và tính toán chính xác số milimet cần dịch chuyển vật lại gần, "
        "đồng thời phát hiện kịp thời các trường hợp góc khớp bị chạm giới hạn cơ khí."
    )


# ==============================================================================
# SLIDE 9: QUY TRÌNH GẮP 5 BƯỚC VÀ THỨ TỰ THAO TÁC AN TOÀN
# ==============================================================================
def build_slide_9(prs):
    slide = add_slide_with_bg(prs)
    add_header(slide, "QUY TRÌNH GẮP VẬT", "QUY TRÌNH GẮP 5 BƯỚC VÀ THỨ TỰ THAO TÁC AN TOÀN")
    add_footer(slide, 9)

    # 5 Khối Stepper ngang
    step_w = Inches(2.05)
    step_h = Inches(1.85)
    arrow_w = Inches(0.35)
    start_x = Inches(0.8)
    gap_x = Inches(0.4)

    steps_info = [
        ("1. ĐIỂM CHỜ", "Cao +60mm", "Mở kẹp (J)", "Đưa kẹp trên cao", AMBER),
        ("2. HẠ XUỐNG", "Sát thân vật", "Kẹp mở", "Căn tâm đầu kẹp", AMBER),
        ("3. ĐÓNG KẸP", "Khóa vật", "Phím L (165°)", "Khóa mục tiêu", GREEN),
        ("4. NÂNG LÊN", "Cao +80mm", "Giữ kẹp chặt", "Nhấc khỏi mặt bàn", AMBER),
        ("5. KIỂM TRA", "Cửa sổ 30f", "2 Camera S1+S2", "Thẩm định kết quả", GREEN),
    ]

    for i, (title, sub1, sub2, sub3, col) in enumerate(steps_info):
        x = start_x + i * (step_w + arrow_w)
        card = add_card(slide, x, Inches(1.65), step_w, step_h, bg_color=RGBColor(32, 35, 40), border_color=col, border_width=1.2)
        box = slide.shapes.add_textbox(x, Inches(1.65), step_w, step_h)
        tf = box.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.text = f"{title}\n{sub1}\n{sub2}\n{sub3}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = PRIMARY_TEXT

        if i < 4:
            add_arrow(slide, x + step_w + Inches(0.05), Inches(2.4), arrow_w - Inches(0.1), Inches(0.25), color=BORDER_COLOR)

    # Thẻ lớn phía dưới: Thứ tự an toàn và Phím bấm Keycap
    lower_card = add_card(slide, Inches(0.8), Inches(3.75), Inches(11.733), Inches(2.95))
    lh_box = slide.shapes.add_textbox(Inches(1.1), Inches(3.9), Inches(11.133), Inches(0.45))
    tf_lh = lh_box.text_frame
    p_lh = tf_lh.paragraphs[0]
    p_lh.text = "THỨ TỰ ĐIỀU KHIỂN KHỚP AN TOÀN & BẢNG PHÍM TẮT KEYCAP"
    p_lh.font.name = FONT_MAIN
    p_lh.font.size = Pt(19)
    p_lh.font.bold = True
    p_lh.font.color.rgb = AMBER

    # 4 Hàng thứ tự an toàn: Đế (0) -> Kẹp (3) -> Vai (1) -> Khuỷu (2)
    rows_data = [
        ("ƯU TIÊN 1", "ĐẾ XOAY (Kênh 0)", "Quay trái (+5°) / Quay phải (-5°)", ["A", "D"], Inches(4.5)),
        ("ƯU TIÊN 2", "KẸP GẮP (Kênh 3)", "Mở kẹp (-5°) / Kẹp chặt (+5°)", ["J", "L"], Inches(5.0)),
        ("ƯU TIÊN 3", "KHỚP VAI (Kênh 1)", "Nâng vai lên (+5°) / Hạ vai (-5°)", ["W", "S"], Inches(5.5)),
        ("ƯU TIÊN 4", "KHỚP KHUỶU (Kênh 2)", "Gập khuỷu lên (+5°) / Duỗi hạ (-5°)", ["I", "K"], Inches(6.0)),
    ]

    for prio, joint, desc, keys, y_pos in rows_data:
        # Nhãn thứ tự
        t_box = slide.shapes.add_textbox(Inches(1.1), y_pos, Inches(1.5), Inches(0.4))
        p = t_box.text_frame.paragraphs[0]
        p.text = prio
        p.font.name = FONT_MAIN
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = GREEN

        # Tên khớp
        j_box = slide.shapes.add_textbox(Inches(2.6), y_pos, Inches(2.5), Inches(0.4))
        p = j_box.text_frame.paragraphs[0]
        p.text = joint
        p.font.name = FONT_MAIN
        p.font.size = Pt(15)
        p.font.bold = True
        p.font.color.rgb = PRIMARY_TEXT

        # Mô tả
        d_box = slide.shapes.add_textbox(Inches(5.2), y_pos, Inches(3.8), Inches(0.4))
        p = d_box.text_frame.paragraphs[0]
        p.text = desc
        p.font.name = FONT_MAIN
        p.font.size = Pt(14)
        p.font.color.rgb = MUTED_TEXT

        # Vẽ Keycap
        add_keycap(slide, Inches(9.2), y_pos, keys[0])
        add_keycap(slide, Inches(9.8), y_pos, keys[1])

    # Chế độ Auto-Step và phím Space
    auto_box = slide.shapes.add_textbox(Inches(10.5), Inches(4.5), Inches(1.8), Inches(1.9))
    tf_au = auto_box.text_frame
    tf_au.word_wrap = True
    p_au = tf_au.paragraphs[0]
    p_au.text = "TỰ ĐỘNG BƯỚC\nAuto-Step (Phím P)\nPhát 1 phím / 0.28s\ntheo đúng thứ tự an toàn."
    p_au.font.name = FONT_MAIN
    p_au.font.size = Pt(13)
    p_au.font.color.rgb = AMBER
    add_keycap(slide, Inches(11.0), Inches(5.7), "P")

    set_speaker_notes(slide,
        "Quy trình gắp vật được chia thành 5 bước tuần tự chặt chẽ: bắt đầu bằng việc đưa tay tới điểm chờ cao hơn vật 60mm với kẹp mở, "
        "hạ xuống sát tâm vật, bấm phím L để kẹp chặt ở góc 165 độ, nâng bổng vật lên 80mm và cuối cùng là giữ yên để kiểm tra. "
        "Để đảm bảo an toàn tuyệt đối, hệ thống quy định thứ tự dịch chuyển các khớp là Đế trước, rồi tới Kẹp, sau đó mới tới Vai và Khuỷu "
        "nhằm tránh va chạm ngang vào các vật lân cận. Người dùng có thể nhấn phím P để hệ thống tự động phát xung phím sau mỗi 0.28 giây theo đúng trình tự này."
    )


# ==============================================================================
# ==============================================================================
# SLIDE 10: CƠ CHẾ TỰ ĐỘNG XÁC NHẬN GẮP 2 CAMERA ĐỘC LẬP
# ==============================================================================
def build_slide_10(prs):
    slide = add_slide_with_bg(prs)
    add_header(slide, "TỰ ĐỘNG XÁC NHẬN GẮP", "CƠ CHẾ TỰ ĐỘNG XÁC NHẬN GẮP 2 CAMERA ĐỘC LẬP")
    add_footer(slide, 10)

    # 3 Cột logic xác nhận
    col_w = Inches(3.7)
    col_h = Inches(5.18)
    cols_x = [Inches(0.8), Inches(4.816), Inches(8.833)]

    # Cột 1: Cảm biến S1 và S2
    add_card(slide, cols_x[0], Inches(1.60), col_w, col_h)
    box1 = slide.shapes.add_textbox(cols_x[0] + Inches(0.2), Inches(1.75), col_w - Inches(0.4), col_h - Inches(0.3))
    tf1 = box1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_right = tf1.margin_top = tf1.margin_bottom = 0
    p1 = tf1.paragraphs[0]
    p1.text = "HAI KÊNH CẢM BIẾN ĐỘC LẬP"
    p1.font.name = FONT_MAIN
    p1.font.size = Pt(19)
    p1.font.bold = True
    p1.font.color.rgb = AMBER
    p1.space_after = Pt(8)

    items1 = [
        "Kênh S1 (Cam B - Ngang): Phát hiện vật thể nhấc cao hơn mặt bàn > +20 mm.",
        "Vạch bàn: SIDE_TABLE_Y_RATIO = 0.54, ngưỡng nâng: SIDE_LIFT_RATIO = 0.065.",
        "LOẠI TRỪ MÃ ID 6: Tuyệt đối không tính mã đầu kẹp (chỉ tính ID 10–29 / YOLO).",
        "Kênh S2 (Cam A - Trên xuống): Kiểm tra vị trí cũ (locked_grasp_cm) có trống không.",
        "Bán kính r = 3.0 cm: Quét dọn chỗ cũ hoàn toàn sạch bóng vật thể."
    ]
    for item in items1:
        p = tf1.add_paragraph()
        p.text = f"• {item}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(14.5)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(5)

    # Cột 2: Cửa sổ 30 khung hình & Đồng thuận >= 80%
    add_card(slide, cols_x[1], Inches(1.60), col_w, col_h)
    box2 = slide.shapes.add_textbox(cols_x[1] + Inches(0.2), Inches(1.75), col_w - Inches(0.4), col_h - Inches(0.3))
    tf2 = box2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_right = tf2.margin_top = tf2.margin_bottom = 0
    p2 = tf2.paragraphs[0]
    p2.text = "CỬA SỔ ĐỒNG THUẬN 80%"
    p2.font.name = FONT_MAIN
    p2.font.size = Pt(19)
    p2.font.bold = True
    p2.font.color.rgb = GREEN
    p2.space_after = Pt(8)

    items2 = [
        "Cửa sổ trượt: deque(maxlen=30) lưu kết quả từng khung hình của S1 và S2.",
        "Tỉ lệ đồng thuận: s1_ratio = sum(s1)/30, s2_ratio = sum(s2)/30.",
        "Điều kiện THÀNH CÔNG: Số khung >= 15 và đồng thời s1_ratio >= 0.80 VÀ s2_ratio >= 0.80.",
        "Thời gian Timeout: Giới hạn tối đa 3.0 giây ở Bước 5.",
        "Biểu ngữ: 'GAP THANH CONG: Cam A + Cam B deu thay vat da roi ban!'"
    ]
    for item in items2:
        p = tf2.add_paragraph()
        p.text = f"• {item}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(14.5)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(5)

    # Cột 3: Cây quyết định phân loại lỗi & Log CSV
    add_card(slide, cols_x[2], Inches(1.60), col_w, col_h)
    box3 = slide.shapes.add_textbox(cols_x[2] + Inches(0.2), Inches(1.75), col_w - Inches(0.4), col_h - Inches(0.3))
    tf3 = box3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_right = tf3.margin_top = tf3.margin_bottom = 0
    p3 = tf3.paragraphs[0]
    p3.text = "PHÂN LOẠI LỖI & NHẬT KÝ"
    p3.font.name = FONT_MAIN
    p3.font.size = Pt(19)
    p3.font.bold = True
    p3.font.color.rgb = RED
    p3.space_after = Pt(8)

    items3 = [
        "Phân loại lỗi khi hết 3.0s Timeout:",
        "1. Kẹp trượt (s2 < 0.40): Vật vẫn ở vị trí cũ (kep_truot_vat_van_o_cho_cu).",
        "2. Rơi khi nâng (s1 < 0.40): Cam B không thấy vật (roi_khi_nang_hoac_chua_nhac_len).",
        "3. Không xác định: Bị che khuất tầm nhìn (khong_xac_dinh_bi_che).",
        "Ghi nhật ký attempts.csv: Timestamp, tên vật, tọa độ, sai số align_error_mm, S1/S2."
    ]
    for item in items3:
        p = tf3.add_paragraph()
        p.text = f"• {item}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(14.5)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(5)

    set_speaker_notes(slide,
        "Điểm sáng tạo cốt lõi của đề tài là cơ chế tự động xác nhận kết quả gắp độc lập bằng 2 camera mà không cần gắn thêm cảm biến áp lực phức tạp. "
        "Camera ngang kiểm tra tín hiệu S1 xem vật đã nâng cao hơn mặt bàn 20mm hay chưa, trong đó thuật toán đặc biệt loại trừ mã ID 6 của đầu kẹp "
        "để tránh trường hợp kẹp rỗng nâng lên bị báo nhầm là thành công. Cùng lúc đó, camera trên kiểm tra tín hiệu S2 xem vị trí cũ trong bán kính 3 centimet "
        "đã hoàn toàn trống hay chưa. Nếu cả hai camera đồng thuận đạt từ 80% trên tổng số 30 khung hình, hệ thống sẽ công nhận thành công và tự động ghi log sai số vào CSV."
    )


# ==============================================================================
# SLIDE 11: GIAO THỨC TRUYỀN THÔNG VÀ ĐỒNG BỘ ARDUINO
# ==============================================================================
def build_slide_11(prs):
    slide = add_slide_with_bg(prs)
    add_header(slide, "TRUYỀN THÔNG & ĐỒNG BỘ", "GIAO THỨC TRUYỀN THÔNG VÀ ĐỒNG BỘ ARDUINO")
    add_footer(slide, 11)

    # Sơ đồ truyền thông 3 khối ngang phía trên
    box_l = add_card(slide, Inches(0.8), Inches(1.65), Inches(3.4), Inches(1.5), bg_color=RGBColor(32, 35, 40), border_color=AMBER)
    b_l = slide.shapes.add_textbox(Inches(0.8), Inches(1.65), Inches(3.4), Inches(1.5))
    tf_l = b_l.text_frame
    tf_l.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_l.margin_left = tf_l.margin_right = tf_l.margin_top = tf_l.margin_bottom = 0
    p = tf_l.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "MÁY TÍNH (PYTHON)\nArduinoSerialLink\nGửi ký tự phím 'a','w','s'...\nĐọc gói JSON trạng thái"
    p.font.name = FONT_MAIN
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_TEXT

    # Mũi tên 2 chiều
    add_arrow(slide, Inches(4.3), Inches(2.2), Inches(0.6), Inches(0.3), color=AMBER)

    box_m = add_card(slide, Inches(5.0), Inches(1.65), Inches(3.4), Inches(1.5), bg_color=RGBColor(32, 35, 40), border_color=GREEN)
    b_m = slide.shapes.add_textbox(Inches(5.0), Inches(1.65), Inches(3.4), Inches(1.5))
    tf_m = b_m.text_frame
    tf_m.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_m.margin_left = tf_m.margin_right = tf_m.margin_top = tf_m.margin_bottom = 0
    p = tf_m.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "ARDUINO [...]\nFirmware robot_arm_4dof.ino\nUSB 9600 & Bluetooth HC-05\nPhát JSON mỗi 200ms (5Hz)"
    p.font.name = FONT_MAIN
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_TEXT

    add_arrow(slide, Inches(8.5), Inches(2.2), Inches(0.6), Inches(0.3), color=GREEN)

    box_r = add_card(slide, Inches(9.2), Inches(1.65), Inches(3.333), Inches(1.5), bg_color=RGBColor(32, 35, 40), border_color=AMBER)
    b_r = slide.shapes.add_textbox(Inches(9.2), Inches(1.65), Inches(3.333), Inches(1.5))
    tf_r = b_r.text_frame
    tf_r.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf_r.margin_left = tf_r.margin_right = tf_r.margin_top = tf_r.margin_bottom = 0
    p = tf_r.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    p.text = "MẠCH PCA9685 & SERVO\nI2C Địa chỉ 0x40, Tần số 50Hz\nXung 12-bit (125 - 575)\n4x Servo MG996R"
    p.font.name = FONT_MAIN
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = PRIMARY_TEXT

    # 3 Thẻ chi tiết phía dưới
    card_w = Inches(3.7)
    card_h = Inches(3.3)
    card_y = Inches(3.35)

    # Thẻ 1: Cấu trúc gói tin JSON
    add_card(slide, cols_x_0 := Inches(0.8), card_y, card_w, card_h)
    b1 = slide.shapes.add_textbox(cols_x_0 + Inches(0.15), card_y + Inches(0.15), card_w - Inches(0.3), card_h - Inches(0.3))
    tf1 = b1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_right = tf1.margin_top = tf1.margin_bottom = 0
    p1 = tf1.paragraphs[0]
    p1.text = "GÓI TIN JSON ĐỒNG BỘ"
    p1.font.name = FONT_MAIN
    p1.font.size = Pt(17)
    p1.font.bold = True
    p1.font.color.rgb = AMBER
    p1.space_after = Pt(8)

    items1 = [
        "Định dạng JSON gửi từ Arduino:",
        "{\"t\":12450,\"servo\":[90,85,110,165]}",
        "Tần số gửi:",
        "1. Gửi tức thời sau mỗi lệnh phím.",
        "2. Gửi định kỳ mỗi 200 ms (5 Hz) qua ngắt timer millis().",
        "Đồng bộ góc thực tế với giao diện laptop không bị giật."
    ]
    for item in items1:
        p = tf1.add_paragraph()
        p.text = item if item.startswith("{\"") else f"• {item}"
        p.font.name = FONT_CODE if item.startswith("{\"") else FONT_MAIN
        p.font.size = Pt(14)
        p.font.color.rgb = GREEN if item.startswith("{\"") else PRIMARY_TEXT
        p.space_after = Pt(4)

    # Thẻ 2: Cơ chế Watchdog & Fallback
    add_card(slide, cols_x_1 := Inches(4.816), card_y, card_w, card_h)
    b2 = slide.shapes.add_textbox(cols_x_1 + Inches(0.15), card_y + Inches(0.15), card_w - Inches(0.3), card_h - Inches(0.3))
    tf2 = b2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_right = tf2.margin_top = tf2.margin_bottom = 0
    p2 = tf2.paragraphs[0]
    p2.text = "WATCHDOG & FALLBACK"
    p2.font.name = FONT_MAIN
    p2.font.size = Pt(17)
    p2.font.bold = True
    p2.font.color.rgb = GREEN
    p2.space_after = Pt(8)

    items2 = [
        "Tự động tìm Bluetooth HC-05: Tìm MAC 98D351F6AF14 trên Windows hoặc /dev/cu.HC-05 trên macOS.",
        "Tự động Fallback: Đang gửi Bluetooth nếu đứt kết nối sẽ lập tức chuyển sang cáp USB.",
        "Phát hiện mất phản hồi (Timeout 2s): Cảnh báo 'BOARD KHONG PHAN HOI' nếu vi điều khiển im lặng > 2.0s."
    ]
    for item in items2:
        p = tf2.add_paragraph()
        p.text = f"• {item}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(14)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(6)

    # Thẻ 3: Chế độ Mô phỏng & Khẩn cấp
    add_card(slide, cols_x_2 := Inches(8.833), card_y, card_w, card_h)
    b3 = slide.shapes.add_textbox(cols_x_2 + Inches(0.15), card_y + Inches(0.15), card_w - Inches(0.3), card_h - Inches(0.3))
    tf3 = b3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_right = tf3.margin_top = tf3.margin_bottom = 0
    p3 = tf3.paragraphs[0]
    p3.text = "MÔ PHỎNG & KHẨN CẤP"
    p3.font.name = FONT_MAIN
    p3.font.size = Pt(17)
    p3.font.bold = True
    p3.font.color.rgb = AMBER
    p3.space_after = Pt(8)

    items3 = [
        "Chế độ Mô phỏng (Simulation Mode): Tự động kích hoạt khi không cắm board thật, cập nhật góc ảo bằng phím.",
        "Kiểm thử độc lập: Cho phép kiểm tra toàn bộ thị giác và giải thuật IK mà không sợ reset board.",
        "Phím khẩn cấp [H] (Home): Đưa lập tức 4 servo về tư thế an toàn: [90°, 90°, 90°, 95°]."
    ]
    for item in items3:
        p = tf3.add_paragraph()
        p.text = f"• {item}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(14)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(6)

    set_speaker_notes(slide,
        "Giao thức truyền thông giữa máy tính và vi điều khiển được thiết kế vô cùng tin cậy với tốc độ 9600 baud. "
        "Bo mạch Arduino định kỳ phát gói JSON chứa mảng 4 góc servo với tần số 5Hz để đồng bộ thời gian thực với mô hình 3D trên máy tính. "
        "Hệ thống hỗ trợ truyền nhận song song qua cả USB và Bluetooth HC-05, có khả năng tự động fallback về cáp USB nếu đường truyền Bluetooth bị gián đoạn. "
        "Đặc biệt, nếu không có phần cứng kết nối, phần mềm sẽ tự động chuyển sang chế độ mô phỏng giúp nhóm có thể kiểm thử toàn bộ thuật toán mọi lúc mọi nơi."
    )


# ==============================================================================
# SLIDE 12: GIAO DIỆN NGƯỜI DÙNG TRỰC QUAN (HUD & CỬA SỔ HƯỚNG DẪN)
# ==============================================================================
def build_slide_12(prs):
    slide = add_slide_with_bg(prs)
    add_header(slide, "GIAO DIỆN NGƯỜI DÙNG", "THIẾT KẾ GIAO DIỆN NGƯỜI DÙNG VÀ BẢNG PHÍM TẮT")
    add_footer(slide, 12)

    # Chèn ảnh giao diện thật được sinh từ code
    img_path = os.path.join(ASSETS_DIR, "guide_screen_sample.png")
    if os.path.exists(img_path):
        # Kích thước ảnh 1280 x 800 (tỉ lệ 1.6)
        slide.shapes.add_picture(img_path, Inches(0.8), Inches(1.60), width=Inches(7.4), height=Inches(4.625))
    else:
        # Fallback card nếu ảnh chưa tồn tại
        add_card(slide, Inches(0.8), Inches(1.60), Inches(7.4), Inches(4.625))

    # Cột phải: Bảng phân tích giao diện và danh mục phím tắt
    card_r = add_card(slide, Inches(8.4), Inches(1.60), Inches(4.133), Inches(5.18))
    box_r = slide.shapes.add_textbox(Inches(8.55), Inches(1.75), Inches(3.833), Inches(4.88))
    tf_r = box_r.text_frame
    tf_r.word_wrap = True
    tf_r.margin_left = tf_r.margin_right = tf_r.margin_top = tf_r.margin_bottom = 0

    p = tf_r.paragraphs[0]
    p.text = "CÁC VÙNG CHỨC NĂNG CHÍNH"
    p.font.name = FONT_MAIN
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = AMBER
    p.space_after = Pt(6)

    features = [
        "1. Khung 2 Camera (1280x400): Cam ngang kiểm tra vạch nâng; Cam trên quan sát bàn.",
        "2. Thanh Stepper 5 bước: Viên thuốc bo tròn thể hiện tiến độ quy trình gắp.",
        "3. Chỉ dẫn phím Keycap: Nút cam chỉ rõ phím cần bấm và số lần lặp xN.",
        "4. Thanh trượt servo: Vạch trắng góc hiện tại, vòng tròn mục tiêu cần đạt.",
        "5. Thẻ kết quả & Đồng hồ 80%: Hiển thị trạng thái thành công hoặc lý do lỗi."
    ]
    for feat in features:
        p = tf_r.add_paragraph()
        p.text = feat
        p.font.name = FONT_MAIN
        p.font.size = Pt(13.5)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(3)

    p_sub = tf_r.add_paragraph()
    p_sub.text = "DANH MỤC PHÍM TẮT HỆ THỐNG"
    p_sub.font.name = FONT_MAIN
    p_sub.font.size = Pt(15)
    p_sub.font.bold = True
    p_sub.font.color.rgb = GREEN
    p_sub.space_before = Pt(6)
    p_sub.space_after = Pt(4)

    shortcuts = [
        "• SPACE / N: Sang bước tiếp   • TAB / V: Đổi mục tiêu",
        "• P: Bật/Tắt Auto-Step        • H: Về vị trí Home",
        "• R: Reset về Bước 1         • G: Ẩn/Hiện Guide HUD",
        "• Q: Thoát an toàn khỏi chương trình."
    ]
    for sc in shortcuts:
        p = tf_r.add_paragraph()
        p.text = sc
        p.font.name = FONT_MAIN
        p.font.size = Pt(13)
        p.font.color.rgb = MUTED_TEXT
        p.space_after = Pt(2)

    set_speaker_notes(slide,
        "Đây là hình ảnh thực tế của cửa sổ 'HƯỚNG DẪN GẮP' với độ phân giải 1280 nhân 800 do nhóm tự động sinh từ mã nguồn. "
        "Nửa trên hiển thị song song hai góc camera giúp người quan sát nắm bắt trọn vẹn hiện trường, trong khi nửa dưới là bảng hướng dẫn "
        "thao tác được thiết kế tương phản cao trên nền tối. Mỗi khớp servo đều có ô keycap màu cam chỉ rõ phím cần bấm, số lần lặp và thanh trượt "
        "trực quan hóa góc xoay. Người vận hành chỉ cần làm theo hướng dẫn từng bước mà không cần phải ghi nhớ bất kỳ thông số kỹ thuật phức tạp nào."
    )


# ==============================================================================
# SLIDE 13: KẾT QUẢ KIỂM THỬ GIẢI THUẬT VÀ THỰC NGHIỆM
# ==============================================================================
def build_slide_13(prs):
    slide = add_slide_with_bg(prs)
    add_header(slide, "KIỂM THỬ & THỰC NGHIỆM", "KẾT QUẢ KIỂM THỬ GIẢI THUẬT VÀ THỰC NGHIỆM")
    add_footer(slide, 13)

    # Cột trái: Kết quả test_ik.py thật (Dữ liệu thật 100%)
    card_l = add_card(slide, Inches(0.8), Inches(1.60), Inches(5.7), Inches(5.18), border_color=GREEN, border_width=1.5)
    box_lh = slide.shapes.add_textbox(Inches(1.1), Inches(1.75), Inches(5.1), Inches(0.45))
    tf_lh = box_lh.text_frame
    tf_lh.margin_left = tf_lh.margin_top = tf_lh.margin_right = tf_lh.margin_bottom = 0
    p_lh = tf_lh.paragraphs[0]
    p_lh.text = "KIỂM THỬ ĐỘNG HỌC (test_ik.py)"
    p_lh.font.name = FONT_MAIN
    p_lh.font.size = Pt(20)
    p_lh.font.bold = True
    p_lh.font.color.rgb = GREEN

    box_lc = slide.shapes.add_textbox(Inches(1.1), Inches(2.25), Inches(5.1), Inches(4.4))
    tf_lc = box_lc.text_frame
    tf_lc.word_wrap = True
    tf_lc.margin_left = tf_lc.margin_top = tf_lc.margin_right = tf_lc.margin_bottom = 0

    items_l = [
        "10/10 Bài kiểm thử PASS 100% (Exit code 0).",
        "Kiểm thử lưới 455 điểm 3D trong tầm với: Sai số cực đại FK(IK(p)) = 0.000000 mm (< 0.1 mm).",
        "Toàn bộ góc servo tuân thủ SERVO_LIMITS và chia hết cho SERVO_STEP_DEG = 5°.",
        "Gợi ý phím WASD + IK + JL: Tính toán số xung phím chính xác tuyệt đối.",
        "Ánh xạ tờ A4 ↔ Robot: Đúng 100% cho cả 2 hướng up và down.",
        "Xử lý ngắt kết nối: Tự động fallback từ Bluetooth về cáp USB khi đứt kết nối.",
        "Loại trừ mã ID 6: Kẹp rỗng nâng lên không bị báo nhầm là đã gắp vật."
    ]
    for item in items_l:
        p = tf_lc.add_paragraph()
        p.text = f"✅ {item}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(14)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(4)

    # Cột phải: Thực nghiệm phần cứng (Giữ nguyên dạng placeholder [...])
    card_r = add_card(slide, Inches(6.833), Inches(1.60), Inches(5.7), Inches(5.18), border_color=AMBER, border_width=1.5)
    box_rh = slide.shapes.add_textbox(Inches(7.133), Inches(1.75), Inches(5.1), Inches(0.45))
    tf_rh = box_rh.text_frame
    tf_rh.margin_left = tf_rh.margin_top = tf_rh.margin_right = tf_rh.margin_bottom = 0
    p_rh = tf_rh.paragraphs[0]
    p_rh.text = "THỰC NGHIỆM TRÊN PHẦN CỨNG THẬT"
    p_rh.font.name = FONT_MAIN
    p_rh.font.size = Pt(20)
    p_rh.font.bold = True
    p_rh.font.color.rgb = AMBER

    box_rc = slide.shapes.add_textbox(Inches(7.133), Inches(2.25), Inches(5.1), Inches(4.4))
    tf_rc = box_rc.text_frame
    tf_rc.word_wrap = True
    tf_rc.margin_left = tf_rc.margin_top = tf_rc.margin_right = tf_rc.margin_bottom = 0

    items_r = [
        "Tổng số lượt thử nghiệm gắp: [...] lượt.",
        "Tỉ lệ gắp thành công: [...]% (Thành công [...] lượt, Thất bại [...] lượt).",
        "Phân bố nguyên nhân thất bại thực nghiệm:",
        "  • Lỗi kẹp trượt (vật vẫn ở chỗ cũ): [...]%",
        "  • Lỗi rơi khi nâng (vật rơi lúc nhấc cao): [...]%",
        "  • Lỗi bị che khuất tầm nhìn: [...]%",
        "Sai số căn chỉnh đầu kẹp thực tế: align_error_mm = [...] mm.",
        "Thời gian trung bình hoàn thành 5 bước: [...] giây/lượt.",
        "Ghi chú: Số liệu thực nghiệm do nhóm cập nhật sau khi chạy chuỗi đo trên cánh tay vật lý."
    ]
    for item in items_r:
        p = tf_rc.add_paragraph()
        p.text = item if item.startswith("  •") else f"• {item}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(14)
        p.font.color.rgb = AMBER if "[...]" in item else MUTED_TEXT
        p.space_after = Pt(4)

    set_speaker_notes(slide,
        "Về mặt kiểm thử giải thuật, bộ test tự động test_ik.py đã thực thi thành công toàn bộ 10 bài kiểm tra nghiêm ngặt. "
        "Trong đó, giải thuật động học ngược được thử nghiệm trên lưới 455 điểm không gian 3 chiều trong tầm với, cho sai số giữa động học thuận "
        "và ngược đạt 0.000000 milimet, chứng minh công thức giải tích hoàn toàn chính xác. Đối với phần thực nghiệm trên mô hình thực tế, "
        "do hệ thống nhật ký đang tiếp tục ghi nhận, nhóm xin phép thể hiện các chỉ số về số lượt gắp và tỉ lệ thành công dưới dạng số liệu đang hoàn thiện "
        "và sẽ cập nhật chi tiết trong buổi báo cáo trực tiếp."
    )


# ==============================================================================
# SLIDE 14: ĐÁNH GIÁ HẠN CHẾ VÀ HƯỚNG PHÁT TRIỂN
# ==============================================================================
def build_slide_14(prs):
    slide = add_slide_with_bg(prs)
    add_header(slide, "ĐÁNH GIÁ & ĐỊNH HƯỚNG", "ĐÁNH GIÁ HẠN CHẾ VÀ HƯỚNG PHÁT TRIỂN MỞ RỘNG")
    add_footer(slide, 14)

    # Bố cục 2 cột: Hạn chế vs Hướng phát triển
    card_l = add_card(slide, Inches(0.8), Inches(1.60), Inches(5.7), Inches(5.18), border_color=AMBER, border_width=1.5)
    box_lh = slide.shapes.add_textbox(Inches(1.1), Inches(1.75), Inches(5.1), Inches(0.45))
    tf_lh = box_lh.text_frame
    tf_lh.margin_left = tf_lh.margin_top = tf_lh.margin_right = tf_lh.margin_bottom = 0
    p_lh = tf_lh.paragraphs[0]
    p_lh.text = "HẠN CHẾ KỸ THUẬT HIỆN TẠI"
    p_lh.font.name = FONT_MAIN
    p_lh.font.size = Pt(20)
    p_lh.font.bold = True
    p_lh.font.color.rgb = AMBER

    box_lc = slide.shapes.add_textbox(Inches(1.1), Inches(2.25), Inches(5.1), Inches(4.4))
    tf_lc = box_lc.text_frame
    tf_lc.word_wrap = True
    tf_lc.margin_left = tf_lc.margin_top = tf_lc.margin_right = tf_lc.margin_bottom = 0

    items_l = [
        "Vạch bàn Cam ngang cố định: Tỉ lệ SIDE_TABLE_Y_RATIO = 0.54 cần đo đạc lại bằng tay nếu di chuyển vị trí webcam laptop.",
        "Ước lượng vị trí đế: Tọa độ base_x, base_y ước lượng từ ảnh vẫn còn sai số ±1–2 cm nếu tờ A4 bị xê dịch.",
        "Điều khiển servo vòng hở: Servo RC MG996R bước 5° chưa có encoder đọc phản hồi góc thực tế nên có thể bị trễ dưới tải nặng.",
        "Phụ thuộc ánh sáng môi trường: Phân đoạn màu LAB tìm 4 góc giấy dễ bị ảnh hưởng khi phòng quá tối hoặc bị bóng sẫm che khuất.",
        "Tốc độ khung hình: Mô hình YOLO11s trên CPU thông thường chỉ đạt 10–15 FPS nếu không có bộ tăng tốc GPU/NPU."
    ]
    for item in items_l:
        p = tf_lc.add_paragraph()
        p.text = f"• {item}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(14.5)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(4)

    card_r = add_card(slide, Inches(6.833), Inches(1.60), Inches(5.7), Inches(5.18), border_color=GREEN, border_width=1.5)
    box_rh = slide.shapes.add_textbox(Inches(7.133), Inches(1.75), Inches(5.1), Inches(0.45))
    tf_rh = box_rh.text_frame
    tf_rh.margin_left = tf_rh.margin_top = tf_rh.margin_right = tf_rh.margin_bottom = 0
    p_rh = tf_rh.paragraphs[0]
    p_rh.text = "HƯỚNG PHÁT TRIỂN & NÂNG CẤP"
    p_rh.font.name = FONT_MAIN
    p_rh.font.size = Pt(20)
    p_rh.font.bold = True
    p_rh.font.color.rgb = GREEN

    box_rc = slide.shapes.add_textbox(Inches(7.133), Inches(2.25), Inches(5.1), Inches(4.4))
    tf_rc = box_rc.text_frame
    tf_rc.word_wrap = True
    tf_rc.margin_left = tf_rc.margin_top = tf_rc.margin_right = tf_rc.margin_bottom = 0

    items_r = [
        "Tự động định chuẩn 3D với solvePnP: Sử dụng ma trận camera nội quy (Intrinsic Matrix) để tự động tính tư thế 6-DOF không cần vạch bàn thủ công.",
        "Điều khiển vòng lặp kín (Closed-loop): Bám vết trực tiếp mã ArUco ID 5 trên đầu kẹp để bù sai số cơ khí thời gian thực.",
        "Tự động hóa toàn phần (Full-Autonomous): Tích hợp thuật toán quy hoạch quỹ đạo mượt (Trajectory Planning) gắp vật hoàn toàn tự động.",
        "Cảm biến áp lực đầu kẹp: Gắn thêm cảm biến FSR ở ngón kẹp để điều khiển lực kẹp thích ứng với các vật mềm dễ vỡ.",
        "Tích hợp ROS2 & IoT Cloud: Đưa trạng thái gắp lên MQTT Dashboard quản lý từ xa qua Internet."
    ]
    for item in items_r:
        p = tf_rc.add_paragraph()
        p.text = f"• {item}"
        p.font.name = FONT_MAIN
        p.font.size = Pt(14.5)
        p.font.color.rgb = PRIMARY_TEXT
        p.space_after = Pt(4)

    set_speaker_notes(slide,
        "Nhìn nhận một cách khách quan, hệ thống vẫn tồn tại một số hạn chế nhất định: vị trí vạch mặt bàn của webcam ngang "
        "hiện vẫn phụ thuộc vào tỉ lệ đặt trước là 0.54 nên cần canh chỉnh lại nếu dời vị trí laptop, và góc servo bước 5 độ vẫn là điều khiển vòng hở "
        "chưa có encoder phản hồi. Trong giai đoạn phát triển tiếp theo, nhóm định hướng tích hợp thuật toán solvePnP để tự động hiệu chuẩn không gian camera 3 chiều, "
        "kích hoạt vòng điều khiển kín dựa trên mã ArUco ID 5 gắn ở đầu kẹp, và tiến tới tự động hóa toàn phần quỹ đạo chuyển động của robot."
    )


# ==============================================================================
# SLIDE 15: TỔNG KẾT ĐỀ TÀI VÀ HỎI ĐÁP (Q&A)
# ==============================================================================
def build_slide_15(prs):
    slide = add_slide_with_bg(prs)
    add_header(slide, "TỔNG KẾT & HỎI ĐÁP", "TỔNG KẾT DỰ ÁN VÀ PHIÊN HỎI ĐÁP (Q&A)")
    add_footer(slide, 15)

    # 3 Khối trụ cột thành công phía trên
    col_w = Inches(3.7)
    col_h = Inches(3.2)
    cols_x = [Inches(0.8), Inches(4.816), Inches(8.833)]

    # Trụ cột 1
    add_card(slide, cols_x[0], Inches(1.65), col_w, col_h, border_color=AMBER)
    b1 = slide.shapes.add_textbox(cols_x[0] + Inches(0.15), Inches(1.8), col_w - Inches(0.3), col_h - Inches(0.3))
    tf1 = b1.text_frame
    tf1.word_wrap = True
    p1 = tf1.paragraphs[0]
    p1.alignment = PP_ALIGN.CENTER
    p1.text = "ĐỘNG HỌC CHÍNH XÁC"
    p1.font.name = FONT_MAIN
    p1.font.size = Pt(18)
    p1.font.bold = True
    p1.font.color.rgb = AMBER
    p1.space_after = Pt(8)

    t1 = tf1.add_paragraph()
    t1.text = "Làm chủ trọn vẹn giải thuật giải tích Động học thuận và Động học ngược 4-DOF nghiệm khuỷu lên. Sai số 0.000000 mm trên 455 điểm kiểm thử không gian."
    t1.font.name = FONT_MAIN
    t1.font.size = Pt(15)
    t1.font.color.rgb = PRIMARY_TEXT

    # Trụ cột 2
    add_card(slide, cols_x[1], Inches(1.65), col_w, col_h, border_color=GREEN)
    b2 = slide.shapes.add_textbox(cols_x[1] + Inches(0.15), Inches(1.8), col_w - Inches(0.3), col_h - Inches(0.3))
    tf2 = b2.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.alignment = PP_ALIGN.CENTER
    p2.text = "THỊ GIÁC KÉP THÔNG MINH"
    p2.font.name = FONT_MAIN
    p2.font.size = Pt(18)
    p2.font.bold = True
    p2.font.color.rgb = GREEN
    p2.space_after = Pt(8)

    t2 = tf2.add_paragraph()
    t2.text = "Hợp nhất ArUco định vị không gian và YOLO11s nhận diện linh hoạt. Tự động xác nhận gắp bằng 2 camera độc lập với ngưỡng đồng thuận 80%."
    t2.font.name = FONT_MAIN
    t2.font.size = Pt(15)
    t2.font.color.rgb = PRIMARY_TEXT

    # Trụ cột 3
    add_card(slide, cols_x[2], Inches(1.65), col_w, col_h, border_color=AMBER)
    b3 = slide.shapes.add_textbox(cols_x[2] + Inches(0.15), Inches(1.8), col_w - Inches(0.3), col_h - Inches(0.3))
    tf3 = b3.text_frame
    tf3.word_wrap = True
    p3 = tf3.paragraphs[0]
    p3.alignment = PP_ALIGN.CENTER
    p3.text = "TRẢI NGHIỆM TRỰC QUAN"
    p3.font.name = FONT_MAIN
    p3.font.size = Pt(18)
    p3.font.bold = True
    p3.font.color.rgb = AMBER
    p3.space_after = Pt(8)

    t3 = tf3.add_paragraph()
    t3.text = "Giao diện HƯỚNG DẪN GẮP chuẩn Dark Theme hiện đại, nút Keycap cam trực quan hóa từng phím bấm. Hỗ trợ tự động bước Auto-Step và chế độ mô phỏng."
    t3.font.name = FONT_MAIN
    t3.font.size = Pt(15)
    t3.font.color.rgb = PRIMARY_TEXT

    # Khung Q&A lớn phía dưới
    qa_card = add_card(slide, Inches(0.8), Inches(5.05), Inches(11.733), Inches(1.65),
                       bg_color=RGBColor(32, 35, 40), border_color=AMBER, border_width=1.5)
    qa_box = slide.shapes.add_textbox(Inches(1.0), Inches(5.15), Inches(11.333), Inches(1.45))
    tf_qa = qa_box.text_frame
    tf_qa.vertical_anchor = MSO_ANCHOR.MIDDLE

    p_qa1 = tf_qa.paragraphs[0]
    p_qa1.alignment = PP_ALIGN.CENTER
    p_qa1.text = "XIN CHÂN THÀNH CẢM ƠN QUÝ THẦY CÔ VÀ CÁC BẠN ĐÃ LẮNG NGHE!"
    p_qa1.font.name = FONT_MAIN
    p_qa1.font.size = Pt(22)
    p_qa1.font.bold = True
    p_qa1.font.color.rgb = AMBER

    p_qa2 = tf_qa.add_paragraph()
    p_qa2.alignment = PP_ALIGN.CENTER
    p_qa2.text = "PHIÊN HỎI ĐÁP & ĐÓNG GÓP Ý KIẾN (Q&A)"
    p_qa2.font.name = FONT_MAIN
    p_qa2.font.size = Pt(18)
    p_qa2.font.bold = True
    p_qa2.font.color.rgb = PRIMARY_TEXT

    set_speaker_notes(slide,
        "Tóm lại, đề tài đã xây dựng thành công một hệ thống hỗ trợ gắp vật hoàn chỉnh cho cánh tay robot 4-DOF, "
        "làm chủ từ bài toán giải tích động học ngược, xử lý ảnh thị giác máy tính với ArUco và YOLO11s, "
        "cho đến thiết kế giao diện hướng dẫn người dùng trực quan. Hệ thống chứng minh tính khả thi cao và mở ra tiềm năng ứng dụng lớn "
        "trong các dây chuyền phân loại sản phẩm mini. Nhóm chúng em xin chân thành cảm ơn quý thầy cô và các bạn đã chú ý lắng nghe, "
        "và chúng em rất mong nhận được những câu hỏi và ý kiến đóng góp quý báu."
    )


# ==============================================================================
# HÀM ĐIỀU PHỐI CHÍNH
# ==============================================================================
def main():
    print("=" * 70)
    print("KHỞI TẠO BỘ SLIDE THUYẾT TRÌNH: Project_IoT_ThuyetTrinh.pptx")
    print("=" * 70)

    # 1. Sinh ảnh giao diện mẫu từ code nếu chưa có
    generate_guide_screen_asset()

    # 2. Khởi tạo đối tượng Presentation
    prs = create_deck()

    # 3. Dựng tuần tự 15 slide kỹ thuật
    print("Đang dựng Slide 1: Tiêu đề đề tài...")
    build_slide_1(prs)

    print("Đang dựng Slide 2: Bài toán và mục tiêu giải pháp...")
    build_slide_2(prs)

    print("Đang dựng Slide 3: Kiến trúc và thiết bị phần cứng...")
    build_slide_3(prs)

    print("Đang dựng Slide 4: Kiến trúc phần mềm và luồng dữ liệu...")
    build_slide_4(prs)

    print("Đang dựng Slide 5: Hệ tọa độ bàn và lưới ArUco...")
    build_slide_5(prs)

    print("Đang dựng Slide 6: Nhận diện vật thể YOLO11s và ArUco...")
    build_slide_6(prs)

    print("Đang dựng Slide 7: Động học 4-DOF và quy đổi servo...")
    build_slide_7(prs)

    print("Đang dựng Slide 8: Chuyển đổi tọa độ A4 sang Robot...")
    build_slide_8(prs)

    print("Đang dựng Slide 9: Quy trình gắp 5 bước và thứ tự an toàn...")
    build_slide_9(prs)

    print("Đang dựng Slide 10: Tự động xác nhận gắp 2 camera...")
    build_slide_10(prs)

    print("Đang dựng Slide 11: Giao thức truyền thông Arduino...")
    build_slide_11(prs)

    print("Đang dựng Slide 12: Thiết kế giao diện người dùng (HUD & Guide)...")
    build_slide_12(prs)

    print("Đang dựng Slide 13: Kết quả kiểm thử động học và thực nghiệm...")
    build_slide_13(prs)

    print("Đang dựng Slide 14: Đánh giá hạn chế và hướng phát triển...")
    build_slide_14(prs)

    print("Đang dựng Slide 15: Tổng kết dự án và phiên hỏi đáp (Q&A)...")
    build_slide_15(prs)

    # 4. Xuất file PPTX
    out_dir = os.path.join(PROJECT_ROOT, "slides")
    os.makedirs(out_dir, exist_ok=True)
    out_pptx = os.path.join(out_dir, "Project_IoT_ThuyetTrinh.pptx")
    prs.save(out_pptx)

    # 5. Xác minh file xuất ra
    file_size = os.path.getsize(out_pptx)
    num_slides = len(prs.slides)
    print("=" * 70)
    print(f"XUẤT THÀNH CÔNG: {out_pptx}")
    print(f"Tổng số slide: {num_slides} slide (Yêu cầu: 15 slide)")
    print(f"Kích thước file: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
    print("=" * 70)

    assert num_slides == 15, f"Lỗi: Số lượng slide không đúng: {num_slides} != 15"
    assert file_size > 50000, f"Lỗi: File PPTX quá nhỏ: {file_size} bytes"


if __name__ == "__main__":
    main()
