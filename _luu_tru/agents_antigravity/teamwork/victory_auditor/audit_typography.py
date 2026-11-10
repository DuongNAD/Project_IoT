import pptx
from pptx import Presentation
from pptx.util import Inches, Pt

prs = Presentation("slides/Project_IoT_ThuyetTrinh.pptx")

for idx, slide in enumerate(prs.slides, 1):
    title = ""
    min_size = 999
    max_size = 0
    font_names = set()
    keycap_count = 0
    
    for shape in slide.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                if p.font.size:
                    sz = p.font.size.pt
                    min_size = min(min_size, sz)
                    max_size = max(max_size, sz)
                if p.font.name:
                    font_names.add(p.font.name)
                for run in p.runs:
                    if run.font.size:
                        sz = run.font.size.pt
                        min_size = min(min_size, sz)
                        max_size = max(max_size, sz)
                    if run.font.name:
                        font_names.add(run.font.name)
        # Check for keycap
        if shape.shape_type == pptx.enum.shapes.MSO_SHAPE_TYPE.AUTO_SHAPE:
            if shape.width < Inches(0.8) and shape.height < Inches(0.8):
                if shape.has_text_frame and shape.text_frame.text.strip() in ['A', 'D', 'W', 'S', 'I', 'K', 'J', 'L', 'P', 'H', 'R', 'G', 'Q', 'TAB', 'SPACE']:
                    keycap_count += 1

    print(f"Slide {idx:02d}: fonts={font_names}, font_size_range=[{min_size}pt - {max_size}pt], keycaps={keycap_count}")
