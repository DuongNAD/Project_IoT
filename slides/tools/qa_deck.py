#!/usr/bin/env python3
"""Kiểm tra bản PPTX của bộ slide Project IoT.

Chạy:  python3 -I slides/tools/qa_deck.py slides/build/IoT_RobotArm_Presentation.pptx [--expected-slides 25]
Cần:   python-pptx (pip install python-pptx)

Bộ slide hiện tại: 25 slide (14 chính + phụ lục A-K = slide 15-25), viết cho mã SAU khi đơn giản hóa (control.py -> success.py).

ERROR làm lệnh thoát với mã 1; WARN và INFO chỉ để người xem xét.
  ERROR: sai số slide, khổ giấy, thiếu hoặc quá ngắn ghi chú diễn giả, thiếu dòng "Nguồn:", khung vượt mép slide, ảnh bị kéo méo > 3%,
         ảnh AI thiếu nhãn "Minh họa (AI)", ảnh AI đặt ở slide kết quả / bằng chứng,
         slide 8 / 9 (ảnh màn hình chạy trên ảnh đã lưu) thiếu chú thích "mô phỏng".
  WARN:  ảnh không có alt text, ảnh không thuộc assets/, chữ nhỏ hơn 10 pt, phông lạ, ước lượng chữ tràn khung, ô "THIẾU ẢNH", thiếu "Nếu được hỏi",
         nhắc thiết kế đã bỏ (S1/S2, 5 bước, Auto-Step, attempts.csv, phím Y/E, cửa sổ HƯỚNG DẪN GẮP) ngoài phụ lục I.
  INFO:  các chỗ trống [...] còn lại, các cụm từ rủi ro cần đọc lại (xem 05_SO_LIEU_VA_NGUON.md mục 14 CẤM NÓI).
"""
from __future__ import annotations

import argparse
import hashlib
import math
import re
import sys
from pathlib import Path

from pptx import Presentation
from pptx.util import Emu

EMU_IN = 914400
SLIDES_DIR = Path(__file__).resolve().parents[1]
EVIDENCE_SLIDES = {5, 6, 8, 9, 10, 11, 12, 13}                 # slide kết quả / bằng chứng: không được có ảnh AI
SIMULATED_SCREEN_SLIDES = {8, 9}                               # ảnh màn hình chạy trên ảnh đã lưu, cánh tay mô phỏng: bắt buộc ghi chữ "mô phỏng"
APPENDIX_FROM = 15
QA_SLIDE = 25                                                  # phụ lục K · Hỏi đáp: không bắt buộc đoạn "Nếu được hỏi"
ALLOWED_FONTS = {"Arial", "Courier New", "Segoe UI", "Segoe UI Semibold", "Consolas"}
PLAN_WORDS = ("ESP32", "MQTT", "FSR", "dashboard", "Dashboard", "YOLO26")          # chỉ nên xuất hiện ở slide kế hoạch / chưa làm
PLAN_OK_SLIDES = {13, 14, 24, 25}
# Thiết kế đã bỏ khi đơn giản hóa (02/11): chỉ được nhắc ở phụ lục I (slide 23) và vài chỗ nói rõ "đã bỏ"
REMOVED_DESIGN = [
    (re.compile(r"\bS[12]\b"), "S1/S2", {23}),
    (re.compile(r"Auto-?Step", re.I), "Auto-Step", {23}),
    (re.compile(r"attempts\.csv"), "attempts.csv", {23}),
    (re.compile(r"quy trình (gắp )?(5|năm) bước|5 bước", re.I), "quy trình 5 bước", {23}),
    (re.compile(r"phím\s+Y\b|\bY\s*/\s*E\b"), "phím Y/E trong ứng dụng", {20, 23}),
    (re.compile(r"HƯỚNG DẪN GẮP"), "cửa sổ HƯỚNG DẪN GẮP", {23}),
]
RISKY = [
    (re.compile(r"A\s*[=:]\s*(sang\s+)?trái|phím\s+A[^.\n]{0,25}trái", re.I), "hướng A/D ngược (A sang phải, D sang trái nhìn theo cam NGANG)"),
    (re.compile(r"\b110\s*(test|/\s*110)", re.I), "số test cũ 110 (hiện 103)"),
    (re.compile(r"mô hình (đã )?chính xác (dưới|< ?)\s*1\s*cm", re.I), "nói mô hình chính xác dưới 1 cm"),
    (re.compile(r"tự động hoàn toàn|robot tự (động )?gắp", re.I), "nói robot tự động"),
    (re.compile(r"tỉ lệ (gắp )?thành công[^.\n]{0,20}\d"), "con số tỉ lệ thành công"),
    (re.compile(r"\b\d{1,3}\s*/\s*\d{1,3}\s*lần\b"), "kiểu '9/10 lần'"),
    (re.compile(r"hết nóng|nguội (đi )?\d|giảm \d+\s*°C", re.I), "nói đã hết nóng / nhiệt độ"),
    (re.compile(r"23\s*mm"), "con số 23 mm (chỉ là mô phỏng)"),
    (re.compile(r"155\s*[–-]\s*165"), "ngoại suy 155–165° đã rút lại"),
    (re.compile(r"gần đế (hơn )?3\s*cm|mép tầm với", re.I), "kết luận 'mép tầm với' đã đính chính"),
]


def walk(shapes):
    for sh in shapes:
        yield sh
        if sh.shape_type == 6:                                   # nhóm
            yield from walk(sh.shapes)


def all_text(slide) -> str:
    out = []
    for sh in walk(slide.shapes):
        if sh.has_text_frame:
            out.append(sh.text_frame.text)
        if getattr(sh, "has_table", False) and sh.has_table:
            out.extend(c.text for row in sh.table.rows for c in row.cells)
    return "\n".join(out)


def sha1(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()


def load_asset_hashes(assets: Path):
    real, ai = {}, {}
    for folder, table in (("real", real), ("ai", ai)):
        for p in sorted((assets / folder).glob("*")):
            if p.suffix.lower() in (".png", ".jpg", ".jpeg"):
                table[sha1(p.read_bytes())] = p.name
    return real, ai


def est_overflow(sh):
    tf = sh.text_frame
    w_in, h_in = sh.width / EMU_IN, sh.height / EMU_IN
    if w_in < 0.3 or h_in < 0.1:
        return None
    need = 0.0
    for p in tf.paragraphs:
        txt = "".join(r.text for r in p.runs)
        if not txt.strip():
            continue
        size = max((r.font.size.pt for r in p.runs if r.font.size), default=18.0)
        per_line = max(1, int(w_in * 72 / (size * 0.52)))
        need += math.ceil(len(txt) / per_line) * size * 1.2 / 72
    return need, h_in


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx")
    ap.add_argument("--expected-slides", type=int, default=25)
    ap.add_argument("--assets", default=str(SLIDES_DIR / "assets"))
    args = ap.parse_args()

    prs = Presentation(args.pptx)
    errors, warns, infos = [], [], []
    real_hash, ai_hash = load_asset_hashes(Path(args.assets))
    W, H = prs.slide_width / EMU_IN, prs.slide_height / EMU_IN

    if abs(W - 13.333) > 0.02 or abs(H - 7.5) > 0.02:
        errors.append(f"khổ slide {W:.3f} x {H:.3f} in, cần 13,333 x 7,5")
    if len(prs.slides) != args.expected_slides:
        errors.append(f"có {len(prs.slides)} slide, cần {args.expected_slides}")

    placeholders, missing_imgs, ai_used = {}, [], {}
    for n, slide in enumerate(prs.slides, 1):
        text = all_text(slide)
        notes = slide.notes_slide.notes_text_frame.text.strip() if slide.has_notes_slide else ""
        words = len(notes.split())
        floor_words = 60 if n < APPENDIX_FROM else 25
        if words < 15:
            errors.append(f"slide {n}: ghi chú diễn giả trống hoặc quá ngắn ({words} từ)")
        elif words < floor_words:
            warns.append(f"slide {n}: ghi chú diễn giả ngắn ({words} từ, nên ≥ {floor_words})")
        if n > 1 and "Nguồn:" not in notes:
            errors.append(f"slide {n}: ghi chú thiếu dòng 'Nguồn:'")
        if n > 1 and "Nếu được hỏi" not in notes and n != QA_SLIDE:
            warns.append(f"slide {n}: ghi chú thiếu đoạn 'Nếu được hỏi:'")
        if n in SIMULATED_SCREEN_SLIDES and "mô phỏng" not in text.lower():
            errors.append(f"slide {n}: ảnh màn hình chạy trên ảnh đã lưu nhưng slide thiếu chữ 'mô phỏng' (dễ bị hiểu là chạy trực tiếp)")

        has_ai, tagged = False, "Minh họa (AI)" in text
        for sh in walk(slide.shapes):
            l, t = sh.left / EMU_IN, sh.top / EMU_IN
            r, b = l + sh.width / EMU_IN, t + sh.height / EMU_IN
            if l < -0.02 or t < -0.02 or r > W + 0.02 or b > H + 0.02:
                errors.append(f"slide {n}: '{sh.name}' vượt mép slide ({l:.2f},{t:.2f})-({r:.2f},{b:.2f})")
            if sh.shape_type == 13:                                  # ảnh
                blob = sh.image.blob
                h = sha1(blob)
                nat_w, nat_h = sh.image.size
                shown = sh.width / max(1, sh.height)
                if abs(shown / (nat_w / nat_h) - 1) > 0.03 and not (sh.crop_left or sh.crop_right or sh.crop_top or sh.crop_bottom):
                    errors.append(f"slide {n}: ảnh '{sh.name}' bị kéo méo ({shown:.2f} so với {nat_w / nat_h:.2f})")
                descr = sh._element.nvPicPr.cNvPr.get("descr", "")
                if not descr.strip():
                    warns.append(f"slide {n}: ảnh '{sh.name}' không có alt text")
                if h in ai_hash:
                    has_ai = True
                    ai_used.setdefault(ai_hash[h], []).append(n)
                elif h not in real_hash:
                    warns.append(f"slide {n}: ảnh '{sh.name}' không thuộc assets/real hay assets/ai")
            if sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    for run in p.runs:
                        if run.font.size and run.font.size.pt < 10 and run.text.strip():
                            warns.append(f"slide {n}: chữ {run.font.size.pt:.1f} pt < 10 pt: '{run.text.strip()[:30]}'")
                        if run.font.name and run.font.name not in ALLOWED_FONTS:
                            warns.append(f"slide {n}: phông lạ '{run.font.name}'")
                res = est_overflow(sh)
                if res and res[0] > res[1] * 1.25 + 0.1:
                    warns.append(f"slide {n}: có thể tràn khung ({res[0]:.2f} in cần, {res[1]:.2f} in có): '{sh.text_frame.text.strip()[:36]}'")
        if has_ai and not tagged:
            errors.append(f"slide {n}: có ảnh AI nhưng thiếu nhãn 'Minh họa (AI)'")
        if has_ai and n in EVIDENCE_SLIDES:
            errors.append(f"slide {n}: ảnh AI đặt ở slide kết quả / bằng chứng")
        for m in re.finditer(r"THIẾU ẢNH\s*\n?\s*([\w/.\-]+)", text):
            missing_imgs.append((n, m.group(1)))
        for m in re.finditer(r"\[[^\]\n]{2,60}\]", text + "\n" + notes):
            placeholders.setdefault(m.group(0), set()).add(n)
        for rx, why in RISKY:
            if rx.search(text) or rx.search(notes):
                infos.append(f"slide {n}: đọc lại, có thể {why}")
        for rx, what, ok_slides in REMOVED_DESIGN:
            if n not in ok_slides and (rx.search(text) or rx.search(notes)):
                warns.append(f"slide {n}: nhắc '{what}' (thiết kế đã bỏ, chỉ nên ở slide {sorted(ok_slides)})")
        for w in PLAN_WORDS:
            if w in text and n not in PLAN_OK_SLIDES:
                warns.append(f"slide {n}: nhắc '{w}' (chỉ nên ở slide {sorted(PLAN_OK_SLIDES)})")

    for n, rel in missing_imgs:
        warns.append(f"slide {n}: ô THIẾU ẢNH ({rel})")

    print(f"{args.pptx}: {len(prs.slides)} slide, khổ {W:.3f} x {H:.3f} in")
    if ai_used:
        print("ảnh AI đã dùng:", {k: v for k, v in ai_used.items()})
    if placeholders:
        print(f"chỗ trống còn lại ({len(placeholders)}): " + "; ".join(f"{k} (slide {','.join(map(str, sorted(v)))})" for k, v in placeholders.items()))
    for tag, items in (("ERROR", errors), ("WARN ", warns), ("INFO ", infos)):
        for msg in items:
            print(f"{tag} {msg}")
    print("QA OK" if not errors else f"QA FAIL: {len(errors)} lỗi, {len(warns)} cảnh báo")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
