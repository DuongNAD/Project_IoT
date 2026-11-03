#!/usr/bin/env python3
"""
MÀN HÌNH: 2 camera ở trên, bên dưới là 2 phần nối nhau giống hai nhóm làm hai việc.

  [ cam NGANG | cam TREN ]
  [ 1. ĐIỀU KHIỂN (control.py): bấm phím gì, mấy lần ]  ->  [ 2. SUCCESS (success.py): đã tới chưa? ]

Phần 1 vẽ từ Plan của control.py:   BAM  [D]  x8     sang TRAI 16 do     (trái / phải nhìn theo cam NGANG = MacBook)
Phần 2 vẽ từ Result của success.py: XONG!  khi cả 3 servo đế / vai / khuỷu tới góc gợi ý, không thì "CHUA XONG, con N lan bam"
Chữ viết ASCII không dấu vì font OpenCV không vẽ được dấu.
"""

import cv2
import numpy as np

from control import SERVO_LIMITS

SCREEN_WINDOW = "GAP DON GIAN: bam phim theo lenh (Q = thoat)"
SCREEN_W = 1280
CAM_W, CAM_H = 640, 360            # Mỗi camera một ô 16:9
PANEL_Y, PANEL_H = CAM_H + 10, 290  # Hai phần nằm ngang nhau dưới 2 camera
CTRL_X0, CTRL_X1 = 12, 826          # Phần 1: điều khiển
SUCC_X0, SUCC_X1 = 858, SCREEN_W - 12  # Phần 2: success (giữa hai phần có mũi tên nối)
FOOT_Y = PANEL_Y + PANEL_H + 8
SCREEN_H = FOOT_Y + 60
SIDE_NOTE = "(trai / phai nhin theo cam NGANG = MacBook)"

# Màu (BGR)
BG, CARD, CARD_EDGE = (30, 27, 25), (46, 42, 39), (82, 76, 70)
WHITE, MUTED = (245, 245, 245), (165, 160, 155)
GREEN, GREEN_DK = (110, 215, 90), (50, 88, 42)
RED, RED_DK = (85, 85, 245), (40, 40, 110)
AMBER, AMBER_DK = (40, 185, 255), (28, 62, 98)
DARK_TXT = (30, 27, 25)
FONT, FONT_BIG, AA = cv2.FONT_HERSHEY_SIMPLEX, cv2.FONT_HERSHEY_DUPLEX, cv2.LINE_AA


# ==============================================================================
# Hàm vẽ nhỏ
# ==============================================================================
def text_w(text, scale, thick=1, font=FONT):
    return cv2.getTextSize(text, font, scale, thick)[0][0]


def put(img, text, x, y, scale=0.6, color=WHITE, thick=1, font=FONT, align="l"):
    """Vẽ chữ tại đường cơ sở y; align l / c / r là căn trái / giữa / phải quanh x."""
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


def arrow(img, cx, cy, kind, color, s=9):
    """Mũi tên chỉ hướng: left / right (xoay đế), up / down (vai, khuỷu)."""
    tri = {
        "left": [(cx - s, cy), (cx + s * 0.7, cy - s), (cx + s * 0.7, cy + s)],
        "right": [(cx + s, cy), (cx - s * 0.7, cy - s), (cx - s * 0.7, cy + s)],
        "up": [(cx, cy - s), (cx - s, cy + s * 0.7), (cx + s, cy + s * 0.7)],
        "down": [(cx, cy + s), (cx - s, cy - s * 0.7), (cx + s, cy - s * 0.7)],
    }
    if kind in tri:
        cv2.fillConvexPoly(img, np.array(tri[kind], np.int32), color, AA)


def big_key(img, x, y, letter, size=96, bg=AMBER, fg=DARK_TXT):
    rrect(img, (x, y + 5), (x + size, y + size + 5), (20, 18, 16), r=14)
    rrect(img, (x, y), (x + size, y + size), bg, r=14)
    put(img, letter, x + size // 2, y + size // 2 + 24, 2.6, fg, 5, FONT_BIG, "c")


def servo_track(img, x, y, w, cur, tgt, lo, hi, color):
    """Thanh vị trí servo: chấm trắng = góc hiện tại, vòng màu = góc cần tới."""

    def px(a):
        return int(x + (min(hi, max(lo, a)) - lo) / float(hi - lo) * w)

    cv2.line(img, (x, y), (x + w, y), (92, 88, 84), 6, AA)
    cv2.line(img, (px(cur), y), (px(tgt), y), color, 6, AA)
    cv2.circle(img, (px(tgt), y), 9, color, 3, AA)
    cv2.circle(img, (px(cur), y), 6, WHITE, -1, AA)


def fit_cell(frame, w, h):
    """Thu phóng giữ nguyên tỉ lệ rồi chèn viền đen cho vừa ô w x h."""
    fh, fw = frame.shape[:2]
    scale = min(w / fw, h / fh)
    nw, nh = max(1, round(fw * scale)), max(1, round(fh * scale))
    canvas = np.zeros((h, w, 3), np.uint8)
    x, y = (w - nw) // 2, (h - nh) // 2
    canvas[y:y + nh, x:x + nw] = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_AREA)
    return canvas


def cam_cell(frame, title):
    cell = fit_cell(frame, CAM_W, CAM_H)
    cv2.rectangle(cell, (0, 0), (text_w(title, 0.6, 2) + 22, 32), (0, 0, 0), -1)
    put(cell, title, 11, 23, 0.6, (120, 255, 120), 2)
    return cell


# ==============================================================================
# Hai phần của màn hình
# ==============================================================================
def part_title(img, x0, x1, number, title, col):
    """Thanh tiêu đề của một phần: số thứ tự to + tên phần."""
    cv2.circle(img, (x0 + 16, PANEL_Y + 16), 15, col, -1, AA)
    put(img, str(number), x0 + 16, PANEL_Y + 24, 0.75, DARK_TXT, 2, FONT_BIG, "c")
    put(img, title, x0 + 42, PANEL_Y + 24, 0.8, col, 2, FONT_BIG)
    cv2.line(img, (x0, PANEL_Y + 36), (x1, PANEL_Y + 36), CARD_EDGE, 1, AA)


def draw_control(img, plan, result):
    """PHẦN 1 - ĐIỀU KHIỂN (từ Plan): lệnh to (phím nào, mấy lần, hướng nào) và 3 dòng servo đế / vai / khuỷu."""
    x0, x1 = CTRL_X0, CTRL_X1
    part_title(img, x0, x1, 1, "DIEU KHIEN: bam phim theo lenh", AMBER)
    top, card_h, nxt = PANEL_Y + 46, 118, result.next_move
    if result.state == "moving":
        rrect(img, (x0, top), (x1, top + card_h), AMBER_DK, r=14, edge=AMBER, edge_w=3)
        big_key(img, x0 + 18, top + 11, nxt.key.upper())
        put(img, f"BAM  {nxt.key.upper()}   x {nxt.steps}", x0 + 140, top + 52, 1.7, WHITE, 3, FONT_BIG)
        put(img, f"{nxt.words}  {nxt.degrees} DO", x0 + 140, top + 92, 1.15, AMBER, 3, FONT_BIG)
        if nxt.joint == "base":
            put(img, SIDE_NOTE, x0 + 140, top + 111, 0.45, MUTED, 1)
        arrow(img, x1 - 54, top + 48, nxt.arrow, AMBER, s=28)
        put(img, f"Con {result.remaining} lan bam", x1 - 16, top + 108, 0.6, MUTED, 2, FONT, "r")
    else:
        messages = {
            "done": ("KHONG CAN BAM THEM", "Ca 3 servo da dung goc", GREEN, GREEN_DK),
            "no_target": ("CHUA THAY VAT", "Dat vat co mau len to giay A4 (bam TAB de chon vat khac)", AMBER, AMBER_DK),
            "unreachable": ("VAT NGOAI TAM VOI", f"Dat vat gan de them {plan.move_closer_mm:.0f} mm", RED, RED_DK),
            "relaxed": ("CANH TAY DANG NGHI", "Bam W A S D I K H de cap xung lai cho cac servo", AMBER, AMBER_DK),
        }
        title, sub, col, bg = messages[result.state]
        rrect(img, (x0, top), (x1, top + card_h), bg, r=14, edge=col, edge_w=3)
        put(img, title, x0 + 24, top + 56, 1.6, col, 3, FONT_BIG)
        for i, line in enumerate(wrap_text(sub, x1 - x0 - 60, 0.75, 2)[:2]):
            put(img, line, x0 + 24, top + 92 + i * 24, 0.75, WHITE, 2, FONT)

    row_h, gap, rows_y = 38, 5, top + card_h + 10
    for k, m in enumerate(plan.moves):
        y = rows_y + k * (row_h + gap)
        ok, is_now = result.joints_ok[k], m is nxt and result.state == "moving"
        if ok:
            rrect(img, (x0, y), (x1, y + row_h), CARD, r=10, edge=GREEN_DK, edge_w=2)
        elif is_now:
            rrect(img, (x0, y), (x1, y + row_h), AMBER_DK, r=10, edge=AMBER, edge_w=2)
        else:
            rrect(img, (x0, y), (x1, y + row_h), CARD, r=10, edge=CARD_EDGE, edge_w=1)
        cy = y + row_h // 2
        col = GREEN if ok else (AMBER if is_now else MUTED)
        put(img, m.label, x0 + 16, cy + 7, 0.7, WHITE if (ok or is_now) else MUTED, 2, FONT_BIG)
        put(img, f"{m.now} -> {m.goal} do", x0 + 156, cy + 6, 0.55, MUTED, 1)
        lo, hi, _ = SERVO_LIMITS[m.joint]
        servo_track(img, x0 + 300, cy, 220, m.now, m.goal, lo, hi, col)
        if ok:
            put(img, "DA DUNG", x1 - 14, cy + 7, 0.7, GREEN, 2, FONT_BIG, "r")
        else:
            put(img, f"{m.key.upper()} x{m.steps}  {m.words} {m.degrees} do", x1 - 14, cy + 7, 0.7, AMBER if is_now else MUTED, 2, FONT_BIG, "r")


def draw_success(img, plan, result):
    """PHẦN 2 - SUCCESS (từ Result): đã tới chưa? XONG khi cả 3 servo tới góc gợi ý, kèm dấu tích từng servo và số lần thành công."""
    x0, x1 = SUCC_X0, SUCC_X1
    state, done = result.state, result.done
    col = GREEN if done else (RED if state == "unreachable" else AMBER)
    part_title(img, x0, x1, 2, "SUCCESS: da toi chua?", col)
    top, card_h = PANEL_Y + 46, 150
    cx, cy = (x0 + x1) // 2, top + card_h // 2
    if done:
        rrect(img, (x0, top), (x1, top + card_h), GREEN_DK, r=14, edge=GREEN, edge_w=3)
        cv2.circle(img, (x0 + 66, cy), 42, GREEN, -1, AA)
        check_icon(img, x0 + 66, cy, 42, DARK_TXT, 9)
        put(img, "XONG!", x0 + 130, cy + 22, 2.2, GREEN, 4, FONT_BIG)
    else:
        rrect(img, (x0, top), (x1, top + card_h), CARD, r=14, edge=col, edge_w=3)
        title = {"moving": "CHUA XONG", "no_target": "CHUA THAY VAT", "unreachable": "NGOAI TAM VOI", "relaxed": "TAY DANG NGHI"}[state]
        put(img, title, cx, top + 62, 1.25, col, 3, FONT_BIG, "c")
        if state == "moving":
            put(img, f"con {result.remaining} lan bam", cx, top + 106, 1.0, WHITE, 2, FONT_BIG, "c")
        else:
            put(img, "chua tinh duoc thanh cong", cx, top + 106, 0.65, MUTED, 1, FONT, "c")
    # Từng servo: tích xanh = đã tới góc gợi ý, dấu x = chưa
    chip_y, chip_w = top + card_h + 12, (x1 - x0 - 2 * 8) // 3
    for k, m in enumerate(plan.moves):
        cx0 = x0 + k * (chip_w + 8)
        ok = result.joints_ok[k] and state not in ("no_target", "relaxed", "unreachable")
        rrect(img, (cx0, chip_y), (cx0 + chip_w, chip_y + 40), GREEN_DK if ok else CARD, r=10, edge=GREEN if ok else CARD_EDGE, edge_w=2 if ok else 1)
        if ok:
            check_icon(img, cx0 + 22, chip_y + 20, 12, GREEN, 3)
        else:
            cross_icon(img, cx0 + 22, chip_y + 20, 24, MUTED, 3)
        put(img, m.label.split(" ")[0], cx0 + 42, chip_y + 27, 0.6, WHITE if ok else MUTED, 2, FONT_BIG)
    put(img, f"Thanh cong: {result.count} lan", cx, chip_y + 64, 0.7, GREEN if result.count else MUTED, 2, FONT, "c")
    put(img, "= ca 3 servo toi goc goi y (lech khong qua 2 do, kep khong tinh)", cx, chip_y + 86, 0.45, MUTED, 1, FONT, "c")


def draw_link(img):
    """Mũi tên nối phần 1 -> phần 2: kết quả của điều khiển được chuyển sang success."""
    cy = PANEL_Y + PANEL_H // 2
    pts = np.array([(CTRL_X1 + 6, cy - 22), (CTRL_X1 + 6, cy + 22), (SUCC_X0 - 6, cy)], np.int32)
    cv2.fillConvexPoly(img, pts, AMBER, AA)


def draw_footer(img, plan):
    cv2.line(img, (12, FOOT_Y), (SCREEN_W - 12, FOOT_Y), CARD_EDGE, 1, AA)
    ucol = GREEN if plan.usb_ok else AMBER
    usb = f"USB Arduino: DA KET NOI ({plan.port})" if plan.usb_ok else "USB Arduino: MO PHONG (chua cam / chua ket noi)"
    cv2.circle(img, (22, FOOT_Y + 17), 6, ucol, -1, AA)
    put(img, usb, 36, FOOT_Y + 22, 0.55, ucol, 1)
    if plan.n_objects > 0:
        put(img, f"Vat {plan.selected_idx + 1}/{plan.n_objects}  {plan.target_name[:28]}", 520, FOOT_Y + 22, 0.55, MUTED, 1)
    put(img, "[TAB] doi vat  [H] ve Home  [U] do lai ma  [C] chup anh  [Q] thoat", SCREEN_W - 14, FOOT_Y + 22, 0.55, (190, 186, 182), 1, FONT, "r")
    if plan.banner:  # Cảnh báo quan trọng: Arduino vừa reset, firmware cũ không có phím Z...
        put(img, plan.banner[:100], 14, FOOT_Y + 48, 0.6, AMBER, 2)


def build_screen(view_left, view_right, plan, result, titles=("CAM NGANG (MacBook)", "CAM TREN (OBSBOT)")):
    """Màn hình 1280 x SCREEN_H: 2 camera + phần 1 ĐIỀU KHIỂN + phần 2 SUCCESS nối nhau + chân trang."""
    img = np.full((SCREEN_H, SCREEN_W, 3), BG, dtype=np.uint8)
    img[:CAM_H] = cv2.hconcat([cam_cell(view_left, titles[0]), cam_cell(view_right, titles[1])])
    cv2.line(img, (CAM_W, 0), (CAM_W, CAM_H), (255, 255, 255), 2)
    draw_control(img, plan, result)
    draw_link(img)
    draw_success(img, plan, result)
    draw_footer(img, plan)
    return img
