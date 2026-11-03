"""Deep slide inspection script for teamwork_reviewer_2."""
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

STANDARD_COLORS = {
    (25, 27, 30): "#191B1E (BG / DARK_TEXT)",
    (39, 42, 46): "#272A2E (CARD)",
    (70, 76, 82): "#464C52 (BORDER)",
    (245, 245, 245): "#F5F5F5 (PRIMARY_TEXT)",
    (155, 160, 165): "#9BA0A5 (MUTED_TEXT)",
    (255, 185, 40): "#FFB928 (AMBER)",
    (90, 215, 110): "#5AD76E (GREEN)",
    (245, 85, 85): "#F55555 (RED)",
    (98, 62, 28): "#623E1C (AMBER_DK)",
    (42, 88, 50): "#2A5832 (GREEN_DK)",
    (28, 30, 34): "#1C1E22 (PILL_BG)",
}

print(f"Total Slides: {len(prs.slides)}")
print(f"Dimensions: {prs.slide_width.inches:.3f} x {prs.slide_height.inches:.3f} in")

all_colors_found = {}
font_issues = []
bullet_counts = {}
words_per_line_issues = []
titles_info = []

for idx, slide in enumerate(prs.slides, 1):
    slide_title = ""
    slide_tag = ""
    bullets = 0
    paragraphs_count = 0
    slide_fonts = set()
    slide_colors = set()
    
    # Check shapes
    for s in slide.shapes:
        # Check fill color
        try:
            if s.fill.type is not None:
                if hasattr(s.fill, 'fore_color') and hasattr(s.fill.fore_color, 'rgb'):
                    rgb = tuple(s.fill.fore_color.rgb)
                    all_colors_found[rgb] = all_colors_found.get(rgb, 0) + 1
                    slide_colors.add(rgb)
        except Exception:
            pass

        # Check line color
        try:
            if hasattr(s, 'line') and s.line.color and hasattr(s.line.color, 'rgb'):
                rgb = tuple(s.line.color.rgb)
                all_colors_found[rgb] = all_colors_found.get(rgb, 0) + 1
                slide_colors.add(rgb)
        except Exception:
            pass

        if s.has_text_frame:
            tf = s.text_frame
            for p in tf.paragraphs:
                paragraphs_count += 1
                txt = p.text.strip()
                if not txt:
                    continue
                
                # Check if bullet
                if p.level > 0 or txt.startswith("•") or txt.startswith("-") or (hasattr(p, '_p') and p._p.xpath('.//a:buChar')):
                    bullets += 1
                elif any(txt.startswith(f"{n}.") for n in range(1, 10)):
                    bullets += 1

                # Check words per line
                words = txt.split()
                if len(words) > 20: # significantly longer than 12 words
                    words_per_line_issues.append((idx, len(words), txt[:40]))

                # Check runs
                for r in p.runs:
                    if r.font.name:
                        slide_fonts.add(r.font.name)
                    if hasattr(r.font, 'color') and hasattr(r.font.color, 'rgb'):
                        try:
                            rgb = tuple(r.font.color.rgb)
                            all_colors_found[rgb] = all_colors_found.get(rgb, 0) + 1
                            slide_colors.add(rgb)
                        except Exception:
                            pass
                    if r.font.size:
                        pt_sz = r.font.size.pt
                        # check if title
                        if idx > 1 and pt_sz >= 26:
                            slide_title = r.text
                        elif idx == 1 and pt_sz >= 30:
                            slide_title = r.text

    bullet_counts[idx] = bullets
    titles_info.append((idx, slide_title))

print("\n--- SLIDE TITLES ---")
for idx, title in titles_info:
    print(f"Slide {idx:02d}: {title}")

print("\n--- BULLET COUNTS PER SLIDE ---")
for idx, count in bullet_counts.items():
    print(f"Slide {idx:02d}: {count} bullets/cards")

print("\n--- COLORS DETECTED IN DECK ---")
for rgb, count in sorted(all_colors_found.items(), key=lambda x: -x[1]):
    desc = STANDARD_COLORS.get(rgb, "CUSTOM/OTHER")
    hex_str = f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"
    print(f"RGB {rgb} -> Hex {hex_str}: {count} times ({desc})")

print("\n--- WORDS PER LINE CHECK (>20 words) ---")
if not words_per_line_issues:
    print("None found! All lines are concise.")
else:
    for item in words_per_line_issues:
        print(f"Slide {item[0]:02d} ({item[1]} words): {item[2]}...")
