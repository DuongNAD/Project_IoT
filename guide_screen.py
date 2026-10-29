#!/usr/bin/env python3
"""
Cửa sổ "HƯỚNG DẪN GẮP": 2 camera ở trên + bảng thao tác ở dưới, chữ to để vừa nhìn vừa làm theo.

Bảng thao tác gồm:
  - Thanh 5 bước gắp (bước nào xong thì hiện dấu tick, bước hiện tại sáng màu cam)
  - 4 dòng việc cần làm theo thứ tự an toàn Đế -> Kẹp -> Vai -> Khuỷu: phím nào, bấm mấy lần, thanh góc servo
  - Khung KẾT QUẢ GẮP: đang kiểm tra / THÀNH CÔNG / THẤT BẠI + lý do + số lần thành công/thất bại
Dữ liệu lấy từ GraspAssist4DOF.compute_current_suggestion(); chữ viết ASCII không dấu vì font OpenCV không vẽ được dấu.
"""

import cv2
import numpy as np

from grasp_assist_4dof import SERVO_LIMITS

GUIDE_WINDOW = "HUONG DAN GAP: 2 Cam + Thao tac (bam G de an/hien)"
GUIDE_W = 1280
CAM_H = 400
PANEL_H = 400

FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_BIG = cv2.FONT_HERSHEY_DUPLEX
AA = cv2.LINE_AA

# Màu (BGR)
BG = (30, 27, 25)
CARD = (46, 42, 39)
CARD_EDGE = (82, 76, 70)
WHITE = (245, 245, 245)
MUTED = (165, 160, 155)
GREEN = (110, 215, 90)
GREEN_DK = (50, 88, 42)
RED = (85, 85, 245)
AMBER = (40, 185, 255)
AMBER_DK = (28, 62, 98)
DARK_TXT = (30, 27, 25)

# 5 bước gắp: (tên ngắn trên thanh bước, việc cần làm)
STAGES = [
    ("DIEM CHO", "Dua dau kep len TREN vat, kep van MO"),
    ("HA XUONG", "Ha dau kep xuong sat vat, giu kep MO"),
    ("DONG KEP", "DONG kep cho chat vat (bam L)"),
    ("NANG LEN", "NANG vat len khoi mat ban, giu kep DONG"),
    ("KIEM TRA", "Giu yen, 2 camera dang kiem tra gap thanh cong chua"),
]
# Khi 4 servo đã đạt góc gợi ý thì bấm SPACE để làm gì
STAGE_DONE_MSG = [
    "DA TOI DIEM CHO! Bam SPACE de HA XUONG (buoc 2)",
    "DA SAT VAT! Bam SPACE sang buoc 3, roi DONG KEP",
    "KEP DA DONG! Bam SPACE de NANG VAT LEN (buoc 4)",
    "DA NANG LEN! Bam SPACE de bat dau KIEM TRA (buoc 5)",
]

# Kênh servo: (tên, mô tả khi tăng góc, mô tả khi giảm góc, khóa trong SERVO_LIMITS, hướng mũi tên khi tăng, khi giảm)
CHANNELS = {
    0: ("DE", "Quay TRAI", "Quay PHAI", "base", "left", "right"),
    1: ("VAI", "Nang LEN", "Ha XUONG", "shoulder", "up", "down"),
    2: ("KHUYU", "Gap LEN", "Ha XUONG", "elbow", "up", "down"),
    3: ("KEP", "KEP VAO", "MO RA", "grip", "close", "open"),
}
# Thứ tự an toàn, giống chế độ Tự động (phím P): Đế -> Kẹp -> Vai -> Khuỷu
ROW_ORDER = (0, 3, 1, 2)

JOINT_NAMES = {"base": "de", "shoulder": "vai", "elbow": "khuyu"}
VERIFY_TIMEOUT_S = 3.0
RESULT_FRESH_S = 12.0  # Kết quả gắp mới nhất hiện to trong ngần này giây, sau đó thu nhỏ thành dòng "Lần trước"

LEGEND = (
    "[SPACE] buoc tiep   [TAB] doi vat   [P] tu dong   [R] lam lai   [H] ve Home   "
    "[C] chup anh   [M] ArUco   [G] an/hien man nay   [Q] thoat"
)


# ==============================================================================
# Hàm vẽ nhỏ
# ==============================================================================
def text_w(text, scale, thick=1, font=FONT):
    return cv2.getTextSize(text, font, scale, thick)[0][0]


def put(img, text, x, y, scale=0.6, color=WHITE, thick=1, font=FONT, align="l"):
    """Vẽ chữ tại đường cơ sở y; align l/c/r là căn trái/giữa/phải quanh x."""
    if align != "l":
        w = text_w(text, scale, thick, font)
        x = x - w // 2 if align == "c" else x - w
    cv2.putText(img, text, (int(x), int(y)), font, scale, color, thick, AA)


def wrap_text(text, max_w, scale=0.55, thick=1, font=FONT):
    """Ngắt dòng theo độ rộng pixel."""
    lines, line = [], ""
    for word in text.split():
        cand = f"{line} {word}".strip()
        if line and text_w(cand, scale, thick, font) > max_w:
            lines.append(line)
            line = word
        else:
            line = cand
    if line:
        lines.append(line)
    return lines


def rrect(img, p1, p2, color, r=10, edge=None, edge_w=2):
    """Hình chữ nhật bo góc, có thể kèm viền."""

    def fill(a, b, c, rad):
        (ax, ay), (bx, by) = a, b
        rad = int(max(0, min(rad, (bx - ax) // 2, (by - ay) // 2)))
        cv2.rectangle(img, (ax + rad, ay), (bx - rad, by), c, -1)
        cv2.rectangle(img, (ax, ay + rad), (bx, by - rad), c, -1)
        for cx, cy in ((ax + rad, ay + rad), (bx - rad, ay + rad), (ax + rad, by - rad), (bx - rad, by - rad)):
            cv2.circle(img, (cx, cy), rad, c, -1, AA)

    (x1, y1), (x2, y2) = p1, p2
    if edge is not None:
        fill((x1, y1), (x2, y2), edge, r)
        fill((x1 + edge_w, y1 + edge_w), (x2 - edge_w, y2 - edge_w), color, r - edge_w)
    else:
        fill((x1, y1), (x2, y2), color, r)


def check_icon(img, cx, cy, s, color, thick=3):
    pts = np.array([[cx - s * 0.55, cy + s * 0.02], [cx - s * 0.15, cy + s * 0.42], [cx + s * 0.6, cy - s * 0.4]], np.int32)
    cv2.polylines(img, [pts], False, color, thick, AA)


def cross_icon(img, cx, cy, s, color, thick=3):
    d = int(s * 0.45)
    cv2.line(img, (cx - d, cy - d), (cx + d, cy + d), color, thick, AA)
    cv2.line(img, (cx - d, cy + d), (cx + d, cy - d), color, thick, AA)


def direction_glyph(img, cx, cy, kind, color, s=9):
    """Mũi tên chỉ hướng: left/right (quay đế), up/down (vai, khuỷu), close/open (kẹp)."""
    tri = {
        "left": [(cx - s, cy), (cx + s * 0.7, cy - s), (cx + s * 0.7, cy + s)],
        "right": [(cx + s, cy), (cx - s * 0.7, cy - s), (cx - s * 0.7, cy + s)],
        "up": [(cx, cy - s), (cx - s, cy + s * 0.7), (cx + s, cy + s * 0.7)],
        "down": [(cx, cy + s), (cx - s, cy - s * 0.7), (cx + s, cy - s * 0.7)],
    }
    if kind in tri:
        cv2.fillConvexPoly(img, np.array(tri[kind], np.int32), color, AA)
        return
    # Kẹp: hai tam giác quay vào nhau (đóng) hoặc quay ra ngoài (mở) quanh một vạch giữa
    sign = 1 if kind == "close" else -1
    for side in (-1, 1):
        base_x = cx + side * s * 1.1
        tip_x = base_x - side * sign * s * 0.9
        cv2.fillConvexPoly(img, np.array([(tip_x, cy), (base_x, cy - s * 0.8), (base_x, cy + s * 0.8)], np.int32), color, AA)
    cv2.line(img, (cx, cy - s), (cx, cy + s), color, 2, AA)


def keycap(img, x, y, letter, size=44, bg=AMBER, fg=DARK_TXT):
    rrect(img, (x, y + 3), (x + size, y + size + 3), (20, 18, 16), r=9)
    rrect(img, (x, y), (x + size, y + size), bg, r=9)
    put(img, letter, x + size // 2, y + size // 2 + 11, 1.1, fg, 2, FONT_BIG, "c")


def servo_track(img, x, y, w, cur, tgt, lo, hi, color):
    """Thanh vị trí servo: chấm trắng = góc hiện tại, vòng màu = góc cần tới."""

    def px(a):
        return int(x + (min(hi, max(lo, a)) - lo) / float(hi - lo) * w)

    cv2.line(img, (x, y), (x + w, y), (92, 88, 84), 6, AA)
    cv2.line(img, (px(cur), y), (px(tgt), y), color, 6, AA)
    cv2.circle(img, (px(tgt), y), 9, color, 3, AA)
    cv2.circle(img, (px(cur), y), 6, WHITE, -1, AA)


def meter(img, x, y, w, h, ratio, color):
    """Thanh tiến độ 0..1 kèm vạch ngưỡng 80% (mức cần đạt để kết luận thành công)."""
    rrect(img, (x, y), (x + w, y + h), (74, 70, 66), r=h // 2)
    fw = int(w * max(0.0, min(1.0, ratio)))
    if fw >= h:
        rrect(img, (x, y), (x + fw, y + h), color, r=h // 2)
    tx = x + int(w * 0.8)
    cv2.line(img, (tx, y - 3), (tx, y + h + 3), WHITE, 1, AA)


def fit_cell(frame, w, h):
    """Thu phóng giữ nguyên tỉ lệ rồi chèn viền đen cho vừa ô w x h."""
    fh, fw = frame.shape[:2]
    scale = min(w / fw, h / fh)
    nw, nh = max(1, round(fw * scale)), max(1, round(fh * scale))
    canvas = np.zeros((h, w, 3), np.uint8)
    x, y = (w - nw) // 2, (h - nh) // 2
    canvas[y:y + nh, x:x + nw] = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_AREA)
    return canvas


# ==============================================================================
# Các khối của bảng thao tác
# ==============================================================================
def draw_stepper(img, stage, y=8, h=40):
    n, gap, x0 = len(STAGES), 8, 12
    w = (GUIDE_W - 2 * x0 - gap * (n - 1)) // n
    for i, (short, _) in enumerate(STAGES):
        x = x0 + i * (w + gap)
        if i < stage:
            rrect(img, (x, y), (x + w, y + h), GREEN_DK, r=h // 2, edge=GREEN, edge_w=2)
            check_icon(img, x + 30, y + h // 2, 15, GREEN, 3)
            put(img, f"{i + 1}  {short}", x + w // 2 + 14, y + 27, 0.68, GREEN, 2, FONT, "c")
        elif i == stage:
            rrect(img, (x, y), (x + w, y + h), AMBER, r=h // 2)
            put(img, f"{i + 1}  {short}", x + w // 2, y + 28, 0.78, DARK_TXT, 2, FONT, "c")
        else:
            rrect(img, (x, y), (x + w, y + h), CARD, r=h // 2, edge=CARD_EDGE, edge_w=1)
            put(img, f"{i + 1}  {short}", x + w // 2, y + 27, 0.66, MUTED, 1, FONT, "c")


def draw_instruction(img, info, y=54):
    """Dòng lệnh to nhất: việc cần làm ngay bây giờ."""
    stage = info["stage"]
    remaining = sum(h[1] for h in info["hints"] if not h[4])
    if stage == 4:
        msg, col = "GIU YEN! 2 camera dang kiem tra vat da duoc gap len chua...", AMBER
    elif info["all_aligned"]:
        msg, col = STAGE_DONE_MSG[stage], GREEN
    else:
        msg, col = f"BUOC {stage + 1}/5:  {STAGES[stage][1]}", WHITE
    put(img, msg, 14, y + 28, 0.95, col, 2, FONT_BIG)
    if stage < 4 and not info["all_aligned"]:
        put(img, f"Con {remaining} lan bam", GUIDE_W - 14, y + 28, 0.95, AMBER, 2, FONT_BIG, "r")


def draw_target_line(img, info, y=94):
    """Vật mục tiêu, tọa độ robot và trạng thái tầm với (ẩn ở bước 5 vì vật đã rời bàn)."""
    if info["stage"] == 4:
        return
    rx, ry, rz = info["rob_mm"]
    ik = info["ik"]
    if not info["has_obj"]:
        # Chưa có vật thật: mục tiêu chỉ là tâm tờ giấy mặc định nên không báo tầm với
        put(img, "Chua thay vat tren to A4 (dan ma ArUco ID 10-29 vao vat)", 14, y + 12, 0.55, AMBER, 1)
        return
    left, left_col = f"Muc tieu: {info['obj_name']}   X={rx:.0f}  Y={ry:.0f}  Z={rz:.0f} mm (he toa do robot)", MUTED
    if not ik["reachable"]:
        right, rcol = f"NGOAI TAM VOI! Doi vat gan them {ik['move_closer_mm']:.0f}mm", RED
    elif info.get("clamped"):
        joints = ", ".join(JOINT_NAMES[k] for k in info["clamped"])
        right, rcol = f"CANH BAO: {joints} cham gioi han servo (dau kep se lech)", AMBER
    else:
        right, rcol = "TRONG TAM VOI", GREEN
    # Bên trái nhường chỗ cho bên phải, quá dài thì cắt bớt để hai dòng không đè nhau
    room = GUIDE_W - 28 - text_w(right, 0.55, 2) - 24
    while text_w(left, 0.55) > room and len(left) > 12:
        left = left[:-4].rstrip() + "..."
    put(img, left, 14, y + 12, 0.55, left_col, 1)
    put(img, right, GUIDE_W - 14, y + 12, 0.55, rcol, 2, FONT, "r")


def draw_action_rows(img, info, x0=12, y0=118, w=800, row_h=54, gap=4):
    stage = info["stage"]
    hints, now, tgt = info["hints"], info["servo_now"], info["servo_target"]
    if stage == 4:
        rrect(img, (x0, y0), (x0 + w, y0 + 4 * row_h + 3 * gap), CARD, r=12, edge=CARD_EDGE, edge_w=1)
        put(img, "GIU YEN - KHONG BAM PHIM", x0 + w // 2, y0 + 92, 1.15, AMBER, 2, FONT_BIG, "c")
        v = info.get("verify") or {}
        elapsed = min(VERIFY_TIMEOUT_S, v.get("elapsed", 0.0))
        meter(img, x0 + 150, y0 + 118, w - 300, 14, elapsed / VERIFY_TIMEOUT_S, AMBER)
        put(img, f"Dang kiem tra... {elapsed:.1f}/{VERIFY_TIMEOUT_S:.0f}s", x0 + w // 2, y0 + 164, 0.65, MUTED, 1, FONT, "c")
        if v.get("n1", 0) == 0 and v.get("elapsed", 0.0) > 2.0:
            put(img, "Cam ngang chua co hinh nen khong kiem tra duoc. Bam R de lam lai.", x0 + w // 2, y0 + 196, 0.6, RED, 2, FONT, "c")
        return

    current = next((i for i in ROW_ORDER if not hints[i][4]), None)
    for k, ch in enumerate(ROW_ORDER):
        y = y0 + k * (row_h + gap)
        delta, steps, key, _, ok = hints[ch]
        name, pos_txt, neg_txt, lim_key, pos_dir, neg_dir = CHANNELS[ch]
        lo, hi, _ = SERVO_LIMITS[lim_key]
        is_now = ch == current
        if ok:
            rrect(img, (x0, y), (x0 + w, y + row_h), CARD, r=10, edge=GREEN_DK, edge_w=2)
        elif is_now:
            rrect(img, (x0, y), (x0 + w, y + row_h), AMBER_DK, r=10, edge=AMBER, edge_w=2)
        else:
            rrect(img, (x0, y), (x0 + w, y + row_h), CARD, r=10, edge=CARD_EDGE, edge_w=1)

        cy = y + row_h // 2
        if ok:
            cv2.circle(img, (x0 + 32, cy), 17, GREEN, -1, AA)
            check_icon(img, x0 + 32, cy, 15, DARK_TXT, 3)
            put(img, f"{name}  - DA DUNG", x0 + 68, cy + 7, 0.8, GREEN, 2, FONT_BIG)
            put(img, f"{now[ch]} deg", x0 + w - 24, cy + 6, 0.65, MUTED, 1, FONT, "r")
            continue

        main_col = AMBER if is_now else MUTED
        cv2.circle(img, (x0 + 32, cy), 17, main_col, -1 if is_now else 2, AA)
        put(img, str(k + 1), x0 + 32, cy + 7, 0.65, DARK_TXT if is_now else MUTED, 2, FONT, "c")
        keycap(img, x0 + 66, y + (row_h - 44) // 2, key.upper(), 44, bg=AMBER if is_now else (120, 116, 112))
        put(img, f"x{steps}", x0 + 122, cy + 10, 1.15, WHITE if is_now else MUTED, 2, FONT_BIG)
        direction_glyph(img, x0 + 224, cy, pos_dir if delta > 0 else neg_dir, main_col)
        put(img, name, x0 + 248, y + 20, 0.5, MUTED, 1)
        put(img, pos_txt if delta > 0 else neg_txt, x0 + 248, y + 43, 0.78, WHITE if is_now else (205, 200, 195), 2, FONT_BIG)
        put(img, f"{now[ch]} -> {tgt[ch]} deg", x0 + 478, y + 20, 0.5, MUTED, 1)
        servo_track(img, x0 + 478, y + 38, 290, now[ch], tgt[ch], lo, hi, main_col)


def draw_result_card(img, info, x0=824, y0=118, w=444, h=228):
    rrect(img, (x0, y0), (x0 + w, y0 + h), CARD, r=12, edge=CARD_EDGE, edge_w=1)
    ok_n, bad_n = info["success_count"], info["fail_count"]
    total = ok_n + bad_n
    put(img, "KET QUA GAP", x0 + 16, y0 + 28, 0.62, MUTED, 2)
    cx = x0 + w // 2
    verify, result = info.get("verify"), info.get("result")

    if info["stage"] == 4 and verify is not None:
        put(img, "DANG KIEM TRA...", cx, y0 + 76, 1.05, AMBER, 2, FONT_BIG, "c")
        for j, (label, got, n) in enumerate((
            ("Cam NGANG thay vat da nang len", verify["s1"], verify["n1"]),
            ("Cam TREN thay cho cu da TRONG", verify["s2"], verify["n2"]),
        )):
            yy = y0 + 112 + j * 44
            ratio = got / n if n else 0.0
            col = GREEN if ratio >= 0.8 else AMBER
            put(img, label, x0 + 18, yy, 0.55, WHITE, 1)
            put(img, f"{got}/{n}", x0 + w - 18, yy, 0.55, col, 2, FONT, "r")
            meter(img, x0 + 18, yy + 9, w - 36, 12, ratio, col)
    elif result is not None and result["age"] <= RESULT_FRESH_S:
        icon_c = (x0 + 50, y0 + 66)
        if result["ok"]:
            cv2.circle(img, icon_c, 28, GREEN, -1, AA)
            check_icon(img, icon_c[0], icon_c[1], 28, DARK_TXT, 6)
            put(img, "GAP THANH CONG", x0 + 94, y0 + 78, 1.0, GREEN, 2, FONT_BIG)
            detail = "Cam ngang thay vat da nang len va cam tren thay cho cu da trong."
            extra, extra_col = f"Vat: {result['obj']}", MUTED
        else:
            cv2.circle(img, icon_c, 28, RED, -1, AA)
            cross_icon(img, icon_c[0], icon_c[1], 28, WHITE, 6)
            put(img, "GAP THAT BAI", x0 + 94, y0 + 78, 1.0, RED, 2, FONT_BIG)
            detail = result["detail"].replace("THAT BAI: ", "")
            extra, extra_col = "Bam R de lam lai tu buoc 1.", AMBER
        for j, ln in enumerate(wrap_text(detail, w - 36)[:2]):
            put(img, ln, x0 + 18, y0 + 122 + j * 22, 0.55, WHITE, 1)
        put(img, extra, x0 + 18, y0 + 170, 0.5, extra_col, 1)
    else:
        if result is not None:
            col = GREEN if result["ok"] else RED
            put(img, "Lan truoc: " + ("THANH CONG" if result["ok"] else "THAT BAI"), cx, y0 + 76, 0.9, col, 2, FONT_BIG, "c")
        else:
            put(img, "CHUA GAP LAN NAO", cx, y0 + 76, 0.95, MUTED, 2, FONT_BIG, "c")
        put(img, "Lam du 5 buoc, he thong tu kiem tra", cx, y0 + 114, 0.55, MUTED, 1, FONT, "c")
        put(img, "bang 2 camera roi bao ket qua o day.", cx, y0 + 136, 0.55, MUTED, 1, FONT, "c")
        if info.get("banner"):
            put(img, info["banner"], cx, y0 + 168, 0.5, AMBER, 1, FONT, "c")

    # Số lần thành công / thất bại của lần chạy này
    cv2.line(img, (x0 + 14, y0 + h - 40), (x0 + w - 14, y0 + h - 40), CARD_EDGE, 1, AA)
    put(img, f"Thanh cong: {ok_n}", x0 + 18, y0 + h - 14, 0.62, GREEN, 2)
    put(img, f"That bai: {bad_n}", x0 + 190, y0 + h - 14, 0.62, RED, 2)
    rate = f"{100 * ok_n // total}%" if total else "--"
    put(img, rate, x0 + w - 18, y0 + h - 14, 0.62, WHITE, 2, FONT, "r")


def draw_footer(img, info, y=352):
    cv2.line(img, (12, y), (GUIDE_W - 12, y), CARD_EDGE, 1, AA)
    if info["usb_ok"]:
        usb, ucol = f"USB Arduino: DA KET NOI ({info['port_name']})", GREEN
    else:
        usb, ucol = "USB Arduino: MO PHONG (bam phim tren ban phim de thu)", AMBER
    cv2.circle(img, (22, y + 15), 6, ucol, -1, AA)
    put(img, usb, 36, y + 20, 0.55, ucol, 1)
    auto = "BAT" if info["auto_step"] else "TAT"
    put(img, f"Tu dong (P): {auto}", 560, y + 20, 0.55, AMBER if info["auto_step"] else MUTED, 2 if info["auto_step"] else 1)
    if info["n_objects"] > 0:
        put(img, f"Vat {info['selected_idx'] + 1}/{info['n_objects']} (TAB doi vat)", 790, y + 20, 0.55, MUTED, 1)
    put(img, f"Sai so dau kep: {info['align_err_mm']:.0f} mm", GUIDE_W - 14, y + 20, 0.55, MUTED, 1, FONT, "r")
    put(img, LEGEND, 14, y + 40, 0.5, (190, 186, 182), 1)


# ==============================================================================
# Ghép màn hình
# ==============================================================================
def render_guide_panel(info, width=GUIDE_W, height=PANEL_H):
    """Bảng thao tác (1280 x 400) từ kết quả GraspAssist4DOF.compute_current_suggestion()."""
    img = np.full((height, width, 3), BG, dtype=np.uint8)
    draw_stepper(img, info["stage"])
    draw_instruction(img, info)
    draw_target_line(img, info)
    draw_action_rows(img, info)
    draw_result_card(img, info)
    draw_footer(img, info)
    return img


def _cam_cell(frame, title, w, h):
    cell = fit_cell(frame, w, h)
    cv2.rectangle(cell, (0, 0), (text_w(title, 0.62, 2) + 24, 34), (0, 0, 0), -1)
    put(cell, title, 12, 24, 0.62, (120, 255, 120), 2)
    return cell


def build_guide_screen(view_left, view_right, info,
                       titles=("CAM 1: DIEN THOAI (nhin ngang)", "CAM 2: OBSBOT (nhin tu tren)")):
    """Cửa sổ hướng dẫn 1280 x 800: 2 camera ở trên, bảng thao tác ở dưới."""
    half = GUIDE_W // 2
    cams = cv2.hconcat([_cam_cell(view_left, titles[0], half, CAM_H), _cam_cell(view_right, titles[1], half, CAM_H)])
    cv2.line(cams, (half, 0), (half, CAM_H), (255, 255, 255), 2)
    return cv2.vconcat([cams, render_guide_panel(info)])
