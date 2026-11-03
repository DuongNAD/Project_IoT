"""Render PDF slides to high-resolution PNG previews using PyMuPDF (fitz)."""
import os
import fitz  # PyMuPDF

def render_pdf_to_images(pdf_path, output_dir, dpi=150):
    pdf_path = os.path.abspath(pdf_path)
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    doc = fitz.open(pdf_path)
    num_pages = len(doc)
    print(f"Rendering {num_pages} pages from {pdf_path} to {output_dir} at {dpi} DPI...")
    
    for page_idx in range(num_pages):
        page = doc.load_page(page_idx)
        pix = page.get_pixmap(dpi=dpi)
        slide_num = page_idx + 1
        output_path = os.path.join(output_dir, f"slide_{slide_num:02d}.png")
        pix.save(output_path)
        print(f"Saved: {output_path} ({pix.width}x{pix.height})")
    
    print("All slides successfully rendered!")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.join(current_dir, "Project_IoT_ThuyetTrinh.pdf")
    output_dir = os.path.join(current_dir, "preview")
    render_pdf_to_images(pdf_path, output_dir, dpi=150)
