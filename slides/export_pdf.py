"""Export PPTX to PDF using PowerPoint COM."""
import os
import sys
import win32com.client

def convert_pptx_to_pdf(pptx_path, pdf_path):
    pptx_path = os.path.abspath(pptx_path)
    pdf_path = os.path.abspath(pdf_path)
    print(f"Converting: {pptx_path}")
    print(f"Target PDF: {pdf_path}")
    
    ppSaveAsPDF = 32
    ppt = win32com.client.DispatchEx("PowerPoint.Application")
    try:
        presentation = ppt.Presentations.Open(pptx_path, ReadOnly=True, Untitled=False, WithWindow=False)
        presentation.SaveAs(pdf_path, ppSaveAsPDF)
        presentation.Close()
        print("Export successful!")
    finally:
        try:
            ppt.Quit()
        except Exception:
            pass

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pptx_path = os.path.join(current_dir, "Project_IoT_ThuyetTrinh.pptx")
    pdf_path = os.path.join(current_dir, "Project_IoT_ThuyetTrinh.pdf")
    convert_pptx_to_pdf(pptx_path, pdf_path)
