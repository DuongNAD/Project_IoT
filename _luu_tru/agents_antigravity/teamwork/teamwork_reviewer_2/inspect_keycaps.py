"""Inspect keycap implementation and appearance in PPTX."""
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

print("=" * 80)
print("KEYCAP INSPECTION")
print("=" * 80)

for idx, slide in enumerate(prs.slides, 1):
    slide_keycaps = []
    for s in slide.shapes:
        if s.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE and s.has_text_frame:
            # Keycap characteristics: rounded rectangle, width <= 1.2 in, height <= 0.6 in
            txt = s.text_frame.text.strip()
            if 0 < len(txt) <= 5 and s.width.inches <= 1.2 and s.height.inches <= 0.6:
                fill_rgb = None
                text_rgb = None
                try:
                    if s.fill.type is not None and hasattr(s.fill, 'fore_color') and hasattr(s.fill.fore_color, 'rgb'):
                        fill_rgb = tuple(s.fill.fore_color.rgb)
                except Exception:
                    pass
                try:
                    p = s.text_frame.paragraphs[0]
                    if p.font.color and p.font.color.rgb:
                        text_rgb = tuple(p.font.color.rgb)
                    elif p.runs and p.runs[0].font.color and p.runs[0].font.color.rgb:
                        text_rgb = tuple(p.runs[0].font.color.rgb)
                except Exception:
                    pass
                slide_keycaps.append({
                    "text": txt,
                    "pos": (round(s.left.inches, 2), round(s.top.inches, 2)),
                    "size": (round(s.width.inches, 2), round(s.height.inches, 2)),
                    "fill": f"#{fill_rgb[0]:02X}{fill_rgb[1]:02X}{fill_rgb[2]:02X}" if fill_rgb else "None",
                    "text_color": f"#{text_rgb[0]:02X}{text_rgb[1]:02X}{text_rgb[2]:02X}" if text_rgb else "None"
                })
    if slide_keycaps:
        print(f"\nSlide {idx:02d}: Found {len(slide_keycaps)} keycaps:")
        for kc in slide_keycaps:
            print(f"  Keycap '{kc['text']}': pos={kc['pos']}, size={kc['size']}, fill={kc['fill']}, text_color={kc['text_color']}")
