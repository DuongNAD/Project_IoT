"""Check footers on all slides."""
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
import pptx
from pptx import Presentation

pptx_path = r"e:\03_Development_Projects\project\Project_IoT\slides\Project_IoT_ThuyetTrinh.pptx"
prs = Presentation(pptx_path)

for idx, slide in enumerate(prs.slides, 1):
    left_footer = None
    right_footer = None
    for s in slide.shapes:
        if s.has_text_frame:
            for p in s.text_frame.paragraphs:
                txt = p.text.strip()
                if "Hệ thống hỗ trợ gắp vật 4-DOF" in txt:
                    left_footer = txt
                if f"Trang {idx} / 15" in txt:
                    right_footer = txt
    print(f"Slide {idx:02d}: Left Footer = '{left_footer}', Right Footer = '{right_footer}'")
