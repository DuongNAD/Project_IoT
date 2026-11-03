"""Verify generated PPTX meets all criteria."""
import os
import sys

from pptx import Presentation

pptx_path = os.path.join(os.path.dirname(__file__), "Project_IoT_ThuyetTrinh.pptx")
assert os.path.exists(pptx_path), f"File {pptx_path} does not exist!"

prs = Presentation(pptx_path)
print("=" * 60)
print(f"VERIFYING: {pptx_path}")
print(f"File size: {os.path.getsize(pptx_path):,} bytes")
print(f"Slide width: {prs.slide_width.inches:.3f} in (expected ~13.333)")
print(f"Slide height: {prs.slide_height.inches:.3f} in (expected ~7.500)")
assert abs(prs.slide_width.inches - 13.333) < 0.01, "Width not 16:9 widescreen!"
assert abs(prs.slide_height.inches - 7.5) < 0.01, "Height not 16:9 widescreen!"

num_slides = len(prs.slides)
print(f"Total slides: {num_slides} (expected 15)")
assert num_slides == 15, f"Expected 15 slides, got {num_slides}"

for idx, slide in enumerate(prs.slides, start=1):
    notes = slide.notes_slide.notes_text_frame.text.strip()
    shapes = list(slide.shapes)
    has_image = any(s.shape_type == 13 for s in shapes) # 13 is MSO_SHAPE_TYPE.PICTURE
    
    # Check footers on slides 2 to 15
    footer_text = ""
    for s in shapes:
        if s.has_text_frame:
            for p in s.text_frame.paragraphs:
                if f"Trang {idx} / 15" in p.text:
                    footer_text = p.text
    
    print(f"Slide {idx:02d}: shapes={len(shapes):02d}, img={has_image}, footer={'YES' if (idx==1 or footer_text) else 'NO'}, notes_len={len(notes)}")
    assert len(notes) > 50, f"Slide {idx} notes too short: {notes}"
    if idx >= 2:
        assert footer_text != "", f"Slide {idx} missing footer 'Trang {idx} / 15'!"
    if idx == 12:
        assert has_image, "Slide 12 missing embedded image!"

print("=" * 60)
print("ALL PRESENTATION VERIFICATION CHECKS PASSED SUCCESSFULLY!")
print("=" * 60)
