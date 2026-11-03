"""Inspect block diagrams and native shapes in slides 4, 7, 9, 10, 11."""
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import pptx
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

pptx_path = r"e:\03_Development_Projects\project\Project_IoT\slides\Project_IoT_ThuyetTrinh.pptx"
prs = Presentation(pptx_path)

diagram_slides = [4, 7, 9, 10, 11]

for slide_num in diagram_slides:
    slide = prs.slides[slide_num - 1]
    print(f"\n==========================================")
    print(f"SLIDE {slide_num:02d} BLOCK DIAGRAM INSPECTION")
    print(f"==========================================")
    
    shapes_summary = []
    arrows = []
    blocks = []
    has_image = False
    
    for s in slide.shapes:
        if s.shape_type == MSO_SHAPE_TYPE.PICTURE:
            has_image = True
        elif s.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE:
            shape_name = s.auto_shape_type
            txt = s.text_frame.text.replace("\n", " ").strip() if s.has_text_frame else ""
            if "ARROW" in str(shape_name):
                arrows.append((str(shape_name), round(s.left.inches, 2), round(s.top.inches, 2), round(s.width.inches, 2), round(s.height.inches, 2)))
            else:
                blocks.append((str(shape_name), round(s.left.inches, 2), round(s.top.inches, 2), round(s.width.inches, 2), round(s.height.inches, 2), txt[:40]))
        elif s.shape_type == MSO_SHAPE_TYPE.TEXT_BOX:
            txt = s.text_frame.text.replace("\n", " ").strip()
            shapes_summary.append(("TEXT_BOX", txt[:40]))
            
    print(f"Contains Image (bitmap): {has_image}")
    print(f"Total Native AutoShapes: {len(blocks)}")
    print(f"Total Native Arrows: {len(arrows)}")
    print("Sample Blocks:")
    for b in blocks[:5]:
        print(f"  Shape: {b[0]} at ({b[1]}, {b[2]}) size {b[3]}x{b[4]} in | Text: {b[5]}")
    if arrows:
        print("Arrows:")
        for a in arrows:
            print(f"  Arrow: {a[0]} at ({a[1]}, {a[2]}) size {a[3]}x{a[4]} in")
