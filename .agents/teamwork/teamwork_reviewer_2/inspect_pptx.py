import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE_TYPE

pptx_path = r"e:\03_Development_Projects\project\Project_IoT\slides\Project_IoT_ThuyetTrinh.pptx"
prs = Presentation(pptx_path)

print(f"Presentation Path: {pptx_path}")
print(f"Slide Width: {prs.slide_width.inches:.4f} in (target: 13.3333 in)")
print(f"Slide Height: {prs.slide_height.inches:.4f} in (target: 7.5000 in)")
print(f"Aspect Ratio: {prs.slide_width.inches / prs.slide_height.inches:.4f} (target: {16/9:.4f})")
print(f"Total Slides: {len(prs.slides)}")

expected_colors = {
    "BG": (25, 27, 30),
    "CARD": (39, 42, 46),
    "BORDER": (70, 76, 82),
    "PRIMARY_TEXT": (245, 245, 245),
    "MUTED_TEXT": (155, 160, 165),
    "AMBER": (255, 185, 40),
    "GREEN": (90, 215, 110),
    "RED": (245, 85, 85),
    "DARK_TEXT": (25, 27, 30),
}

for i, slide in enumerate(prs.slides, 1):
    print(f"\n--- SLIDE {i:02d} ---")
    notes = slide.notes_slide.notes_text_frame.text.strip() if slide.has_notes_slide else ""
    sentences = [s.strip() for s in notes.replace("\n", " ").split(".") if s.strip()]
    print(f"Notes length: {len(notes)} chars, ~{len(sentences)} sentences")
    print(f"Notes preview: {notes[:100]}...")

    shapes = list(slide.shapes)
    shape_types = {}
    for s in shapes:
        st = s.shape_type
        shape_types[st] = shape_types.get(st, 0) + 1
    print(f"Total shapes: {len(shapes)}, Shape types: {shape_types}")

    # Check footer for slides 2-15
    footer_found = False
    title_text = ""
    font_sizes = []
    fonts_used = set()
    keycaps = []
    has_image = False
    image_names = []

    for s in shapes:
        if s.shape_type == MSO_SHAPE_TYPE.PICTURE:
            has_image = True
            try:
                image_names.append(f"{s.name} ({s.image.content_type})")
            except Exception:
                image_names.append(s.name)

        if s.has_text_frame:
            tf = s.text_frame
            for p in tf.paragraphs:
                p_text = p.text.strip()
                if f"Trang {i} / 15" in p_text or f"Trang {i:02d} / 15" in p_text:
                    footer_found = True
                
                # Check font size & name
                for r in p.runs:
                    if r.font.name:
                        fonts_used.add(r.font.name)
                    if r.font.size:
                        font_sizes.append((r.font.size.pt, r.text[:20]))
                if p.font.name:
                    fonts_used.add(p.font.name)
                if p.font.size:
                    font_sizes.append((p.font.size.pt, p.text[:20]))

        # Check keycaps
        if s.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE and s.has_text_frame:
            # check if width < 1.0 inch, height < 0.6 inch, text is short (1-4 chars)
            if s.width.inches <= 1.2 and s.height.inches <= 0.6:
                txt = s.text_frame.text.strip()
                if txt and len(txt) <= 5:
                    keycaps.append(txt)

    if i > 1:
        print(f"Footer check: {'PASS' if footer_found else 'FAIL'}")
    else:
        print("Slide 1 Title Slide (no footer expected)")

    print(f"Fonts used: {fonts_used}")
    if font_sizes:
        min_sz = min(s[0] for s in font_sizes)
        max_sz = max(s[0] for s in font_sizes)
        print(f"Font sizes range: {min_sz:.1f}pt - {max_sz:.1f}pt")
    if keycaps:
        print(f"Keycaps detected: {keycaps}")
    if has_image:
        print(f"Images detected: {image_names}")
