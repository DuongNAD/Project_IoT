import fitz  # PyMuPDF
import os
import glob

pdf_path = r"slides/Project_IoT_ThuyetTrinh.pdf"
preview_dir = r"slides/preview"

print(f"Checking PDF: {pdf_path}")
assert os.path.exists(pdf_path), "PDF file does not exist!"
pdf_doc = fitz.open(pdf_path)
print(f"PDF page count: {len(pdf_doc)}")
assert len(pdf_doc) == 15, f"Expected 15 pages in PDF, got {len(pdf_doc)}"

for pno, page in enumerate(pdf_doc, start=1):
    rect = page.rect
    aspect = rect.width / rect.height
    print(f"Page {pno:02d}: {rect.width:.1f} x {rect.height:.1f} (ratio={aspect:.3f})")
    assert abs(aspect - (16.0 / 9.0)) < 0.05, f"Page {pno} aspect ratio {aspect:.3f} is not 16:9"

print(f"\nChecking PNG previews in: {preview_dir}")
png_files = sorted(glob.glob(os.path.join(preview_dir, "slide_*.png")))
print(f"Total PNG files: {len(png_files)}")
assert len(png_files) == 15, f"Expected 15 preview PNGs, got {len(png_files)}"

import cv2
for idx, png_file in enumerate(png_files, start=1):
    expected_name = f"slide_{idx:02d}.png"
    assert os.path.basename(png_file) == expected_name, f"Expected {expected_name}, got {os.path.basename(png_file)}"
    img = cv2.imread(png_file)
    assert img is not None, f"Failed to read image {png_file}"
    h, w, c = img.shape
    aspect = w / h
    print(f"{expected_name}: {w}x{h} px, size={os.path.getsize(png_file):,} bytes, ratio={aspect:.3f}")
    assert abs(aspect - (16.0 / 9.0)) < 0.05, f"{expected_name} aspect ratio not 16:9"

print("\nALL PDF AND PREVIEW CHECKS PASSED!")
