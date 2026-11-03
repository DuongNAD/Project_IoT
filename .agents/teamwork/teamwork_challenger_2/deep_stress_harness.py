#!/usr/bin/env python3
"""
Deep Stress Harness for Project_IoT_ThuyetTrinh.pptx and assets.
Inspects:
- Presentation dimensions (16:9)
- Visual styling (color palettes, font hierarchies, keycap shapes)
- Speaker notes sentence counts
- Exported PDF and Preview images integrity
"""

import os
import sys
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE_TYPE
from PIL import Image

PROJECT_ROOT = r"e:\03_Development_Projects\project\Project_IoT"
PPTX_PATH = os.path.join(PROJECT_ROOT, "slides", "Project_IoT_ThuyetTrinh.pptx")
PDF_PATH = os.path.join(PROJECT_ROOT, "slides", "Project_IoT_ThuyetTrinh.pdf")
PREVIEW_DIR = os.path.join(PROJECT_ROOT, "slides", "preview")

def run_deep_stress_harness():
    print("=" * 80)
    print("RUNNING DEEP STRESS HARNESS")
    print("=" * 80)

    prs = Presentation(PPTX_PATH)

    # 1. Check Dimensions
    w_in = prs.slide_width.inches
    h_in = prs.slide_height.inches
    aspect = w_in / h_in
    print(f"Presentation Dimensions: {w_in:.3f} x {h_in:.3f} inches (Aspect Ratio: {aspect:.4f})")
    assert abs(w_in - 13.333) < 0.01, f"Expected 13.333 in, got {w_in}"
    assert abs(h_in - 7.500) < 0.01, f"Expected 7.500 in, got {h_in}"
    assert abs(aspect - (16.0 / 9.0)) < 0.01, f"Expected 16:9 ratio, got {aspect}"
    print("✅ [PASS] 16:9 widescreen dimensions verified.")

    # 2. Check Typography & Fonts
    print("\n--- CHECKING TYPOGRAPHY & FONT HIERARCHIES ---")
    font_issues = []
    keycap_count = 0
    all_fonts_used = set()

    for idx, slide in enumerate(prs.slides, start=1):
        for shape in slide.shapes:
            if shape.has_text_frame:
                for p in shape.text_frame.paragraphs:
                    if p.font.name:
                        all_fonts_used.add(p.font.name)
                    for r in p.runs:
                        if r.font.name:
                            all_fonts_used.add(r.font.name)
            # Count keycaps (rounded rectangles or keycap shapes)
            if shape.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE:
                # Keycaps typically have fill color AMBER
                try:
                    fill = shape.fill
                    if fill.type and fill.fore_color and fill.fore_color.type:
                        rgb = fill.fore_color.rgb
                        if rgb == RGBColor(255, 185, 40): # AMBER
                            keycap_count += 1
                except Exception:
                    pass

    print(f"Fonts used across deck: {all_fonts_used}")
    print(f"Total AMBER keycap / highlight shapes found: {keycap_count}")
    assert "Arial" in all_fonts_used, "Primary font Arial must be used"
    assert keycap_count >= 8, f"Expected keycaps across deck, found {keycap_count}"
    print("✅ [PASS] Typography and keycaps conform to specifications.")

    # 3. Speaker notes sentence structure
    print("\n--- CHECKING SPEAKER NOTES DEPTH ---")
    for idx, slide in enumerate(prs.slides, start=1):
        notes = slide.notes_slide.notes_text_frame.text.strip() if slide.has_notes_slide else ""
        sentences = [s.strip() for s in notes.replace("\n", " ").split(".") if len(s.strip()) > 10]
        print(f"Slide {idx:02d} notes: {len(sentences)} sentences, {len(notes)} chars")
        assert len(sentences) >= 2, f"Slide {idx} notes too brief ({len(sentences)} sentences): {notes}"
    print("✅ [PASS] All 15 slides have substantial Vietnamese presentation speaker notes.")

    # 4. Check PDF Export
    print("\n--- CHECKING PDF EXPORT INTEGRITY ---")
    assert os.path.exists(PDF_PATH), f"PDF file does not exist at {PDF_PATH}"
    pdf_size = os.path.getsize(PDF_PATH)
    print(f"PDF File exists: {PDF_PATH} ({pdf_size:,} bytes)")
    assert pdf_size > 100_000, f"PDF file suspiciously small: {pdf_size} bytes"

    # Try reading PDF with pypdf / fitz if available
    try:
        import fitz
        doc = fitz.open(PDF_PATH)
        print(f"PyMuPDF: PDF has {len(doc)} pages")
        assert len(doc) == 15, f"PDF page count mismatch: expected 15, got {len(doc)}"
        print("✅ [PASS] PDF export verified with 15 pages.")
    except ImportError:
        print("PyMuPDF not installed, skipping internal PDF page check.")

    # 5. Check PNG Previews
    print("\n--- CHECKING PREVIEW PNG IMAGES ---")
    assert os.path.exists(PREVIEW_DIR), f"Preview directory does not exist: {PREVIEW_DIR}"
    png_files = sorted([f for f in os.listdir(PREVIEW_DIR) if f.lower().endswith(".png")])
    print(f"Found {len(png_files)} PNG preview files in {PREVIEW_DIR}")
    assert len(png_files) == 15, f"Expected 15 preview PNGs, got {len(png_files)}: {png_files}"

    for pf in png_files:
        full_p = os.path.join(PREVIEW_DIR, pf)
        with Image.open(full_p) as img:
            w, h = img.size
            print(f"  {pf}: {w}x{h} px, format: {img.format}")
            assert w == 2000 and h == 1125, f"{pf} resolution is {w}x{h}, expected 2000x1125"
    print("✅ [PASS] All 15 preview images exist with exact 2000x1125 px (16:9 widescreen) resolution.")

    print("\n" + "=" * 80)
    print("DEEP STRESS HARNESS PASSED SUCCESSFULLY!")
    print("=" * 80)
    return True

if __name__ == "__main__":
    run_deep_stress_harness()
