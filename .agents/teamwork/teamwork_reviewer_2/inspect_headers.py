"""Inspect titles, paragraphs, and font sizes across all 15 slides."""
import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

import pptx
from pptx import Presentation

pptx_path = r"e:\03_Development_Projects\project\Project_IoT\slides\Project_IoT_ThuyetTrinh.pptx"
prs = Presentation(pptx_path)

for idx, slide in enumerate(prs.slides, 1):
    print(f"\n==========================================")
    print(f"SLIDE {idx:02d}")
    print(f"==========================================")
    headers = []
    text_blocks = []
    for s in slide.shapes:
        if s.has_text_frame:
            for p in s.text_frame.paragraphs:
                txt = p.text.strip()
                if not txt:
                    continue
                size = p.font.size.pt if p.font.size else (p.runs[0].font.size.pt if p.runs and p.runs[0].font.size else None)
                font_name = p.font.name if p.font.name else (p.runs[0].font.name if p.runs and p.runs[0].font.name else None)
                bold = p.font.bold if p.font.bold is not None else (p.runs[0].font.bold if p.runs and p.runs[0].font.bold is not None else None)
                color = None
                try:
                    if p.font.color and p.font.color.rgb:
                        color = str(p.font.color.rgb)
                    elif p.runs and p.runs[0].font.color and p.runs[0].font.color.rgb:
                        color = str(p.runs[0].font.color.rgb)
                except Exception:
                    pass
                if size and size >= 24:
                    headers.append((txt, size, font_name, bold, color))
                else:
                    text_blocks.append((txt, size, font_name, bold, color))

    print(f"HEADER(S): {headers}")
    print(f"Sample body texts (count={len(text_blocks)}):")
    for tb in text_blocks[:6]:
        print(f"  [{tb[1]}pt, {tb[2]}, b={tb[3]}, col={tb[4]}]: {tb[0][:60]}")
