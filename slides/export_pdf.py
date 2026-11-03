"""
Xuất slides/Project_IoT_ThuyetTrinh.pptx sang PDF cùng thư mục.
Dùng LibreOffice (macOS / Linux / Windows có cài); không có LibreOffice thì dùng PowerPoint qua COM trên Windows.
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PPTX = os.path.join(HERE, "Project_IoT_ThuyetTrinh.pptx")
PDF = os.path.join(HERE, "Project_IoT_ThuyetTrinh.pdf")


def find_soffice():
    candidates = [shutil.which("soffice"), shutil.which("libreoffice"),
                  "/Applications/LibreOffice.app/Contents/MacOS/soffice",
                  r"C:\Program Files\LibreOffice\program\soffice.exe"]
    return next((c for c in candidates if c and os.path.exists(c)), None)


def export_libreoffice(soffice):
    # Hồ sơ người dùng tạm: không đụng (và không bị khóa bởi) LibreOffice đang mở
    with tempfile.TemporaryDirectory() as profile:
        profile_url = "file:///" + profile.replace("\\", "/").lstrip("/")
        subprocess.run([soffice, f"-env:UserInstallation={profile_url}", "--headless", "--convert-to", "pdf",
                        "--outdir", HERE, PPTX], check=True, timeout=300)


def export_powerpoint():
    import win32com.client

    pp_save_as_pdf = 32
    ppt = win32com.client.DispatchEx("PowerPoint.Application")
    try:
        deck = ppt.Presentations.Open(PPTX, ReadOnly=True, Untitled=False, WithWindow=False)
        deck.SaveAs(PDF, pp_save_as_pdf)
        deck.Close()
    finally:
        try:
            ppt.Quit()
        except Exception:
            pass


if __name__ == "__main__":
    soffice = find_soffice()
    if soffice:
        export_libreoffice(soffice)
    elif sys.platform == "win32":
        export_powerpoint()
    else:
        sys.exit("Không tìm thấy LibreOffice (soffice): cài LibreOffice hoặc mở file .pptx rồi tự xuất PDF")
    print(f"Đã xuất {PDF}")
