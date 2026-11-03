import pptx
from pptx import Presentation
import os

pptx_path = r"slides/Project_IoT_ThuyetTrinh.pptx"
prs = Presentation(pptx_path)

print(f"Total slides: {len(prs.slides)}")
print(f"Dimensions: {prs.slide_width.inches:.3f} x {prs.slide_height.inches:.3f} in (16:9 widescreen = 13.333 x 7.500)")

assert len(prs.slides) == 15, f"Expected 15 slides, got {len(prs.slides)}"
assert abs(prs.slide_width.inches - 13.333) < 0.01, "Width not 16:9 widescreen"
assert abs(prs.slide_height.inches - 7.500) < 0.01, "Height not 16:9 widescreen"

placeholders_found = []

for idx, slide in enumerate(prs.slides, start=1):
    notes = slide.notes_slide.notes_text_frame.text if slide.has_notes_slide else ""
    shapes = list(slide.shapes)
    texts = []
    has_image = False
    for s in shapes:
        if s.has_text_frame:
            texts.append(s.text_frame.text.strip())
        if s.shape_type == pptx.enum.shapes.MSO_SHAPE_TYPE.PICTURE:
            has_image = True
    full_text = " \n ".join(texts)
    
    # Check footers for slides 2-15
    if idx > 1:
        has_page_num = any(f"Trang {idx} / 15" in t for t in texts)
        has_title = any("Hệ thống hỗ trợ gắp vật 4-DOF" in t for t in texts)
        assert has_page_num, f"Slide {idx} missing page number 'Trang {idx} / 15'"
        assert has_title, f"Slide {idx} missing footer title"
    
    # Check speaker notes
    assert len(notes.strip()) > 50, f"Slide {idx} speaker notes too short or missing: '{notes}'"
    
    # Check placeholders
    if "[...]" in full_text:
        placeholders_found.append((idx, [line for line in full_text.splitlines() if "[...]" in line]))
    
    # Check Slide 12 has image
    if idx == 12:
        assert has_image, "Slide 12 missing embedded picture"
    else:
        # Check no other slides have raster images (native shapes only)
        assert not has_image, f"Slide {idx} has raster image; expected native shapes only"

    print(f"Slide {idx:02d}: shapes={len(shapes):2d}, footer={'OK' if idx > 1 else 'None (Title)'}, notes_chars={len(notes):3d}, has_image={has_image}")

print(f"\nPlaceholders found on {len(placeholders_found)} slides:")
for s_idx, lines in placeholders_found:
    print(f"Slide {s_idx}: {len(lines)} placeholder lines:")
    for l in lines:
        print(f"  - {l.strip()}")
