"""
Kiểm bộ slide 15 trang (slides/Project_IoT_ThuyetTrinh.pptx) trước khi chiếu.

    python3 slides/verify_slides.py

LỖI (thoát mã 1): sai số trang hoặc khổ 16:9, ghi chú diễn giả thiếu / quá ngắn / thiếu dòng "Nguồn:", thiếu chân trang "Trang n / 15",
     hình vượt mép slide, ảnh bị kéo méo, slide 8 / 9 (màn hình chạy trên ảnh đã lưu) thiếu chữ "mô phỏng",
     nhắc tên tệp đã xóa hay thiết kế đã bỏ (S1/S2, 5 bước, Auto-Step, attempts.csv, phím Y/E, cửa sổ HƯỚNG DẪN GẮP).
CẢNH BÁO: phông lạ, chữ nhỏ hơn 10 pt, khung "[Ảnh: ...]" (thiếu ảnh), cụm từ rủi ro ở mục CẤM NÓI (05_SO_LIEU_VA_NGUON.md mục 14).
Cuối cùng in các chỗ "[...]" còn phải điền.
"""
import os
import re
import sys

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "tools"))
from qa_deck import REMOVED_DESIGN, RISKY  # noqa: E402  (cùng danh sách với công cụ kiểm bộ 25 slide)

PPTX = os.path.join(HERE, "Project_IoT_ThuyetTrinh.pptx")
TOTAL = 15
SIMULATED_SCREEN_SLIDES = {8, 9}
DELETED_NAMES = ("grasp_assist_4dof", "guide_screen", "test_ik", "GraspAssist4DOF", "STAGE_NAMES", "fake_assist")
FONTS = {"Arial", "Courier New"}
EMU_IN = 914400


def walk(shapes):
    for sh in shapes:
        yield sh
        if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from walk(sh.shapes)


def placeholders(s):
    """Chỗ còn phải điền: [...], [...ghi chú], hoặc [CHỮ HOA] không có số (bỏ qua [Ảnh: ...] và mảng góc như [85, 60, 90])."""
    out = []
    for m in re.findall(r"\[[^\]]*\]", s):
        if m.startswith(("[...", "[…")) or (not m.startswith("[Ảnh:") and not re.search(r"\d", m) and re.search(r"[A-ZĐ]", m)):
            out.append(m)
    return out


def visible_text(slide):
    text = "\n".join(p.text for sh in walk(slide.shapes) if sh.has_text_frame for p in sh.text_frame.paragraphs)
    return text.replace(" ", " ")  # build_slides.py dùng khoảng trắng không ngắt giữa số và đơn vị


def main():
    prs = Presentation(PPTX)
    errors, warns, todo = [], [], []
    w_in, h_in = prs.slide_width / EMU_IN, prs.slide_height / EMU_IN
    if abs(w_in - 13.333) > 0.01 or abs(h_in - 7.5) > 0.01:
        errors.append(f"khổ {w_in:.3f} x {h_in:.3f} in, không phải 16:9 (13,333 x 7,5)")
    if len(prs.slides) != TOTAL:
        errors.append(f"{len(prs.slides)} slide, cần {TOTAL}")

    for n, slide in enumerate(prs.slides, 1):
        body = visible_text(slide)
        note = slide.notes_slide.notes_text_frame.text if slide.has_notes_slide else ""
        both = body + "\n" + note
        if len(note) < 300:
            errors.append(f"slide {n}: ghi chú diễn giả quá ngắn ({len(note)} ký tự)")
        if "Nguồn:" not in note:
            errors.append(f"slide {n}: ghi chú thiếu dòng 'Nguồn:'")
        if n > 1 and f"Trang {n} / {TOTAL}" not in body:
            errors.append(f"slide {n}: thiếu chân trang 'Trang {n} / {TOTAL}'")
        if n in SIMULATED_SCREEN_SLIDES and "mô phỏng" not in body.lower():
            errors.append(f"slide {n}: ảnh màn hình chạy trên ảnh đã lưu nhưng không ghi 'mô phỏng'")
        for pat, label, _allowed in REMOVED_DESIGN:
            if pat.search(both):
                errors.append(f"slide {n}: nhắc thiết kế đã bỏ ({label})")
        for name in DELETED_NAMES:
            if name in both:
                errors.append(f"slide {n}: nhắc tên trong mã cũ đã xóa ({name})")
        for pat, label in RISKY:
            if pat.search(both):
                warns.append(f"slide {n}: cụm từ rủi ro: {label}")
        on_slide = placeholders(body)
        if on_slide:
            todo.append(f"slide {n}: " + ", ".join(f"{m} ×{on_slide.count(m)}" if on_slide.count(m) > 1 else m
                                                   for m in dict.fromkeys(on_slide)))
        todo += [f"slide {n} (ghi chú): {m}" for m in placeholders(note)]

        for sh in walk(slide.shapes):
            if sh.left is not None and (sh.left < 0 or sh.top < 0 or sh.left + sh.width > prs.slide_width + 9525
                                        or sh.top + sh.height > prs.slide_height + 9525):
                errors.append(f"slide {n}: '{sh.name}' vượt mép slide")
            if sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
                iw, ih = sh.image.size
                vis_w = iw * (1 - sh.crop_left - sh.crop_right)
                vis_h = ih * (1 - sh.crop_top - sh.crop_bottom)
                stretch = (sh.width / sh.height) / (vis_w / vis_h)
                if abs(stretch - 1) > 0.03:
                    errors.append(f"slide {n}: ảnh '{sh.name}' bị kéo méo {100 * (stretch - 1):+.1f}%")
            if sh.has_text_frame:
                if "[Ảnh:" in sh.text_frame.text:
                    warns.append(f"slide {n}: thiếu ảnh: {sh.text_frame.text}")
                for p in sh.text_frame.paragraphs:
                    for r in p.runs:
                        if r.font.name and r.font.name not in FONTS:
                            warns.append(f"slide {n}: phông lạ '{r.font.name}'")
                        if r.font.size is not None and r.font.size.pt < 10 and r.text.strip():
                            warns.append(f"slide {n}: chữ {r.font.size.pt:.1f} pt: '{r.text[:40]}'")

    for title, items in (("LỖI", errors), ("CẢNH BÁO", warns), ("CẦN ĐIỀN", todo)):
        items = list(dict.fromkeys(items))
        print(f"== {title}: {len(items)}")
        for it in items:
            print("  " + it)
    print("KẾT QUẢ:", "ĐẠT" if not errors else "CHƯA ĐẠT")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
