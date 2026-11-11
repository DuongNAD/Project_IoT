#!/usr/bin/env python3
"""Chuẩn bị ảnh THẬT cho slide thuyết trình.

Việc script làm (không bao giờ sửa file gốc, chỉ đọc):
  * chép ảnh thật từ nơi lưu gốc vào slides/assets/real/ với tên gọn, không dấu;
  * cắt bỏ thanh chú thích tiếng Việt đã được dựng sẵn trong vài ảnh (chữ trên slide sẽ do PPTX tự vẽ);
  * làm mờ màn hình laptop lọt vào khung hình (chữ trên đó là nội dung riêng tư, không liên quan);
  * ghi slides/assets/manifest.json (mô tả, alt text, slide dùng, ghi chú cẩn thận) và ảnh xem nhanh _preview.jpg.

Chạy lại: python3 -I slides/tools/prepare_real_assets.py        (cần Pillow và numpy)
Nguồn nào không còn tồn tại (VD thư mục tạm đã bị dọn) thì bị bỏ qua và in cảnh báo, file đã tạo trước đó giữ nguyên.

Ảnh GIAO DIỆN MỚI (ui_screen_*, sw_annot_*, calib_before_after_*) do slides/tools/make_screen_images.py tạo, không phải script này.
Script này giữ nguyên mục manifest của chúng (và của mọi ảnh còn trong assets/real/ mà nó không dựng lại), nên chạy hai script
theo thứ tự nào cũng không làm mất mục. Bảng slide dùng ảnh theo kịch bản mới (25 slide: 14 chính + phụ lục A-K ở slide 15-25).
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

SLIDES = Path(__file__).resolve().parents[1]
PROJECT = SLIDES.parent
OUT = SLIDES / "assets" / "real"



def _find_drive():
    """Thư mục ảnh phần cứng trên Google Drive đồng bộ cục bộ. Tên thư mục gốc có địa chỉ tài khoản nên tìm bằng glob, không ghi cứng vào mã."""
    base = Path.home() / "Library/CloudStorage"
    for root in sorted(base.glob("GoogleDrive-*/Drive của tôi")):
        folder = root / "Project_IoT_Thu_gap_2026-11-02" / "anh_slide"
        if folder.exists():
            return folder
    return base / "GoogleDrive" / "Drive của tôi" / "Project_IoT_Thu_gap_2026-11-02" / "anh_slide"   # không thấy: các ảnh lấy từ Drive sẽ báo thiếu


DRIVE = _find_drive()
TMP = Path("/private/tmp/claude-501/-Users-duongnad-Documents-project-Project-IoT")
RUN4 = TMP / "2b984ba7-f079-5e9a-b65f-9a90f8099ed3/scratchpad/run4"      # khung hình buổi gắp 20:27-20:45
LIVE_UI = TMP / "2b984ba7-f079-5e9a-b65f-9a90f8099ed3/scratchpad/guide_win.png"
RELAXED_UI = TMP / "38b211b4-3f79-47e3-b280-c55517c4d15f/scratchpad/relaxed_ui.png"

# Vùng làm mờ, tọa độ trong khung 1920x1080 (tự co theo kích thước ảnh).
SIDE_SCREEN = [(0, 0), (450, 0), (455, 150), (430, 300), (360, 450), (290, 580), (220, 720), (150, 860), (80, 990), (0, 1080)]
TOP_SCREEN = [(360, 1080), (540, 928), (1000, 936), (1500, 950), (1700, 976), (1780, 1080)]
# Điện thoại đặt góc trên trái ở buổi 20:xx; mép phải màn hình (chữ nghiêng đọc được) kéo tới x ≈ 660 nên vùng làm mờ rộng thêm ở nửa trên
TOP_PHONE = [(380, 0), (672, 0), (672, 100), (630, 100), (630, 190), (380, 190)]
# Buổi 20:xx cốc hay nằm sát mép trái khung ngang nên đường mép màn hình được thu vào ~40 px để không làm mềm cốc
SIDE_SCREEN_TIGHT = [(0, 0), (400, 0), (385, 150), (340, 260), (270, 380), (215, 500), (160, 640), (105, 780), (50, 920), (0, 1030), (0, 1080)]
# Điện thoại nằm phía sau tờ giấy ở mép trên khung ngang (20:27 màn hình sáng, thấy các dòng chữ nghiêng): làm mờ ở mọi khung 20:xx
SIDE_PHONE = [(1200, 55), (1735, 55), (1735, 250), (1200, 250)]
BLUR = {"side": [SIDE_SCREEN], "side20": [SIDE_SCREEN_TIGHT, SIDE_PHONE], "top18": [TOP_SCREEN], "top20": [TOP_SCREEN, TOP_PHONE]}
# Nhãn do phần mềm vẽ đè lên vùng bị mờ: dán lại điểm ảnh gốc ở các hình chữ nhật này (x0, y0, x1, y1 trong khung 1920x1080)
KEEP = {"sw_grid_side.jpg": [(40, 476, 400, 518)]}     # nhãn "Nguong nhac vat S1 (+20mm)"


# Ảnh chụp cửa sổ bản cũ (ui_guide_cameras.png, 2560x765): màn hình laptop lọt vào hai ô camera, chữ nhỏ nhưng vẫn thấy từng dòng.
# Đa giác trong tọa độ của chính ảnh 2560x765 (truyền ref=UI_CAMS_REF cho blur_regions); chừa nhãn 'ID:0' và 'ID:3' của phần mềm.
UI_CAMS_REF = (2560, 765)
UI_CAMS_BLUR = [
    [(0, 72), (290, 72), (285, 150), (262, 205), (225, 245), (222, 285), (200, 370), (170, 470), (140, 570), (105, 640), (70, 700), (40, 716), (0, 716)],  # laptop mép trái ô cam NGANG (chừa thanh tiêu đề và dòng 'Luoi A4')
    [(1590, 765), (1640, 690), (2260, 678), (2300, 765)],                                                                                    # laptop đáy ô cam TREN
]


def blur_regions(img: Image.Image, polys, radius: int = 26, feather: int = 8, keep=(), ref=(1920, 1080)) -> Image.Image:
    """Làm mờ các đa giác; tọa độ tính trong khung ref (mặc định 1920x1080) và tự co theo kích thước ảnh."""
    w, h = img.size
    sx, sy = w / float(ref[0]), h / float(ref[1])
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    for poly in polys:
        d.polygon([(x * sx, y * sy) for x, y in poly], fill=255)
    for x0, y0, x1, y1 in keep:
        d.rectangle([x0 * sx, y0 * sy, x1 * sx, y1 * sy], fill=0)
    mask = mask.filter(ImageFilter.GaussianBlur(feather))
    return Image.composite(img.filter(ImageFilter.GaussianBlur(radius)), img, mask)


def caption_bar_top(img: Image.Image) -> int:
    """Hàng đầu tiên của thanh chú thích đen dựng sẵn ở đáy ảnh (10 hàng liên tiếp gần như đen hoàn toàn)."""
    a = np.asarray(ImageOps.grayscale(img), dtype=float)
    dark = (a < 70).mean(axis=1)
    h = a.shape[0]
    for y in range(int(h * 0.5), h - 12):
        if dark[y:y + 10].min() >= 0.97:
            return y
    return h


def load(path: Path) -> Image.Image:
    return ImageOps.exif_transpose(Image.open(path)).convert("RGB")


def stamp(path: Path) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(path)))


MANIFEST: list[dict] = []


def save(img: Image.Image, name: str, meta: dict, quality: int = 90) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    if name.endswith(".png"):
        img.save(path, optimize=True)
    else:
        img.save(path, quality=quality, optimize=True)
    entry = {"file": f"assets/real/{name}", "size_px": list(img.size), "kb": round(path.stat().st_size / 1024)}
    entry.update(meta)
    MANIFEST.append(entry)
    print(f"  ghi {name:34s} {img.size[0]}x{img.size[1]}  {entry['kb']} KB")


def need(path: Path) -> bool:
    if not path.exists():
        print(f"  BO QUA (không thấy nguồn): {path}")
        return False
    return True


MANIFEST_PATH = SLIDES / "assets" / "manifest.json"
OLD_UI_NOTE = "Giao diện CŨ đã bỏ (bản trước khi đơn giản hóa thành hai khối điều khiển / success): KHÔNG dùng trong slide."
DEMO_NOTE = "Khung cắt từ video, người điều khiển bằng bàn phím theo gợi ý trên màn hình bản cũ (trước khi đơn giản hóa), chưa tự động."


def load_manifest() -> list[dict]:
    """Manifest đang có trên đĩa ([] nếu chưa có hoặc hỏng)."""
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def refresh_entry(entry: dict, path: Path) -> dict:
    """Mục manifest với kích thước và dung lượng đọc lại từ file thật."""
    with Image.open(path) as im:
        size = list(im.size)
    return {**entry, "size_px": size, "kb": round(path.stat().st_size / 1024)}


def write_manifest_and_preview(entries: list[dict]) -> None:
    """Ghi manifest.json (xếp theo tên file) và ảnh xem nhanh _preview.jpg của mọi ảnh trong đó."""
    entries = sorted(entries, key=lambda e: e["file"])
    MANIFEST_PATH.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nmanifest.json: {len(entries)} ảnh")

    # ảnh xem nhanh toàn bộ (để người và Antigravity lướt qua)
    files = [OUT / Path(e["file"]).name for e in entries]
    cols, tw = 6, 300
    thumbs = []
    for f in files:
        im = Image.open(f).convert("RGB")
        im = im.resize((tw, max(1, int(im.size[1] * tw / im.size[0]))))
        thumbs.append((f.name, im))
    rows = (len(thumbs) + cols - 1) // cols
    cell_h = max(t[1].size[1] for t in thumbs) + 16
    sheet = Image.new("RGB", (cols * (tw + 6) + 6, rows * cell_h + 6), (40, 40, 40))
    d = ImageDraw.Draw(sheet)
    for i, (name, im) in enumerate(thumbs):
        x, y = 6 + (i % cols) * (tw + 6), 6 + (i // cols) * cell_h
        d.text((x, y), name[:44], fill=(255, 255, 0))
        sheet.paste(im, (x, y + 14))
    sheet.save(OUT / "_preview.jpg", quality=85)
    print("ghi _preview.jpg", sheet.size)


def upsert_entries(new_entries: list[dict]) -> None:
    """Thêm hoặc thay các mục (theo tên file) trong manifest hiện có, rồi ghi lại manifest và _preview.jpg (dùng bởi make_screen_images.py)."""
    by_file = {e["file"]: e for e in load_manifest()}
    by_file.update({e["file"]: e for e in new_entries})
    write_manifest_and_preview(list(by_file.values()))


def keep_other_entries() -> None:
    """Giữ mục manifest của ảnh mà lần chạy này không dựng lại nhưng file vẫn còn trong assets/real/ (ảnh do make_screen_images.py tạo, hoặc ảnh có nguồn đã bị dọn)."""
    done = {e["file"] for e in MANIFEST}
    for e in load_manifest():
        path = SLIDES / e["file"]
        if e["file"] not in done and path.exists():
            MANIFEST.append(refresh_entry(e, path))
            print(f"  giữ mục cũ {path.name} (không dựng lại ở lần chạy này)")


def main() -> None:
    print("== Ảnh phần cứng (Drive, 02/11 18:xx, cam trên + cam ngang + ảnh cận cảnh) ==")
    p = DRIVE / "01_tong_quan_cam_tren.jpg"
    if need(p):
        save(blur_regions(load(p), BLUR["top18"]), "hw_overview_top.jpg", dict(
            group="hw", source=str(p), blurred="màn hình laptop ở đáy ảnh",
            desc_vi="Toàn cảnh từ camera TRÊN (OBSBOT): mạch điều khiển bên trái, cánh tay robot, tờ A4 với 4 mã ArUco, cốc đỏ số 3. Ảnh thô, không lớp phủ.",
            alt_vi="Ảnh chụp từ camera trên: cánh tay robot đen đặt cạnh tờ giấy A4 có bốn mã ArUco ở bốn góc, một cốc đỏ trên giấy",
            slides=[4], note_vi="Cánh tay ở tư thế 90/90/90/95 (Home của bản trước 11/11)."))
    p = DRIVE / "02_tong_quan_cam_ngang.jpg"
    if need(p):
        save(blur_regions(load(p), BLUR["side"]), "hw_overview_side.jpg", dict(
            group="hw", source=str(p), blurred="màn hình laptop ở mép trái",
            desc_vi="Toàn cảnh từ camera NGANG (MacBook) đặt thấp trước tờ A4: bệ robot ở phía xa, bốn mã ArUco rõ nét ở bốn góc giấy, cốc đỏ số 3 và bóng cánh tay trên giấy.",
            alt_vi="Ảnh chụp từ camera ngang: tờ A4 với bốn mã ArUco, cốc đỏ ở giữa, bệ robot ở phía sau",
            slides=[4], note_vi="Ảnh nét nhất để chỉ cho khán giả thấy bốn mã ArUco."))
    p = DRIVE / "03_mach_dieu_khien_va_de_robot.jpg"
    if need(p):
        im = load(p)
        y = caption_bar_top(im) - 2
        save(im.crop((0, 0, im.size[0], y)), "hw_electronics.jpg", dict(
            group="hw", source=str(p), cropped="bỏ thanh chú thích dựng sẵn ở đáy",
            desc_vi="Cận cảnh mạch điều khiển: Arduino Uno, mạch PCA9685, nguồn tổ ong và đế cánh tay, dây servo ba màu.",
            alt_vi="Cận cảnh bo mạch Arduino Uno, mạch PCA9685 và nguồn tổ ong trên đế của cánh tay robot",
            slides=[4], note_vi="Ảnh nhỏ (800 px): đặt ở thẻ vừa phải, đừng phóng to quá nửa slide."))
    p = DRIVE / "04_canh_tay_va_tay_kep.jpg"
    if need(p):
        im = load(p)
        y = caption_bar_top(im) - 2
        save(im.crop((0, 0, im.size[0], y)), "hw_arm_gripper.jpg", dict(
            group="hw", source=str(p), cropped="bỏ thanh chú thích dựng sẵn ở đáy",
            desc_vi="Cánh tay 4 bậc tự do (servo MG996R) và tay kẹp song song ở tư thế gốc 90/90/90, nhìn từ trên xuống, cốc đỏ ở gần ngón kẹp.",
            alt_vi="Cận cảnh cánh tay robot bốn servo và tay kẹp hai ngón nhìn từ trên xuống, cốc đỏ nằm cạnh",
            slides=[4], note_vi="Ảnh 960 px."))
    p = DRIVE / "07_tay_kep_95_vs_125_do.jpg"
    if need(p):
        im = load(p)
        y = caption_bar_top(im) - 2
        im = im.crop((0, 0, im.size[0], y))
        save(im, "hw_gripper_95_vs_125.jpg", dict(
            group="hw", source=str(p), cropped="bỏ thanh chú thích dựng sẵn ở đáy",
            desc_vi="Tay kẹp ở 95° (mở hết) bên trái và 125° bên phải, cùng một góc nhìn từ trên xuống. Từ 95° lên 125° ngón kẹp vươn ra khoảng 1,7 cm nhưng khe kẹp chỉ hẹp khoảng 0,5 cm.",
            alt_vi="Hai ảnh cạnh nhau của tay kẹp: bên trái mở hết cỡ 95 độ, bên phải 125 độ, khe kẹp gần như không hẹp lại",
            slides=[21], note_vi="Phụ lục G (slide 21). Tự ghi nhãn 95° / 125° bằng chữ của slide vì đã bỏ chú thích dựng sẵn."))
        a = np.asarray(ImageOps.grayscale(im), dtype=float)
        w = a.shape[1]
        lo, hi = int(w * 0.40), int(w * 0.60)
        cut = lo + int(np.argmax(a[:, lo:hi].mean(axis=0)))               # cột trắng ngăn hai nửa
        save(im.crop((0, 0, cut - 3, im.size[1])), "hw_gripper_95.jpg", dict(
            group="hw", source=str(p), cropped="nửa trái của ảnh 95 vs 125",
            desc_vi="Tay kẹp mở hết cỡ ở 95°.", alt_vi="Tay kẹp mở hết cỡ 95 độ nhìn từ trên xuống", slides=[], note_vi="Dự phòng cho slide 21 (phụ lục G) khi cần hai ảnh rời."))
        save(im.crop((cut + 3, 0, w, im.size[1])), "hw_gripper_125.jpg", dict(
            group="hw", source=str(p), cropped="nửa phải của ảnh 95 vs 125",
            desc_vi="Tay kẹp ở 125°.", alt_vi="Tay kẹp ở 125 độ nhìn từ trên xuống", slides=[], note_vi="Dự phòng cho slide 21 (phụ lục G) khi cần hai ảnh rời."))

    print("== Ảnh phần mềm có lớp phủ (Drive, 18:xx) ==")
    p = DRIVE / "08_cam_tren_luoi_aruco.jpg"
    if need(p):
        save(blur_regions(load(p), BLUR["top18"]), "sw_grid_top.jpg", dict(
            group="sw", source=str(p), blurred="màn hình laptop ở đáy ảnh",
            desc_vi="Camera TRÊN với lưới tọa độ cm dựng từ 4 mã ArUco: ID 0 ở gốc (0,0 cm), ID 1 ở X = 29,7 cm, ID 3 ở Y = 21,0 cm; chấm cam 'DE ROBOT' là trục xoay đế.",
            alt_vi="Ảnh camera trên có lưới tọa độ xanh và nhãn ID các mã ArUco, trục X và Y vẽ bằng mũi tên",
            slides=[], note_vi="Dự phòng. Ảnh chụp từ bản cũ (có nhãn 'DE ROBOT' của giao diện đã bỏ); slide 5 dùng sw_annot_top do phần mềm hiện tại vẽ."))
    p = DRIVE / "08_cam_ngang_luoi_aruco.jpg"
    if need(p):
        save(blur_regions(load(p), BLUR["side"], keep=KEEP["sw_grid_side.jpg"]), "sw_grid_side.jpg", dict(
            group="sw", source=str(p), blurred="màn hình laptop ở mép trái",
            desc_vi="Camera NGANG với cùng lưới cm nhìn nghiêng; vạch xanh là ngưỡng nhấc vật S1 (+20 mm).",
            alt_vi="Ảnh camera ngang có lưới cm nhìn nghiêng và vạch ngang xanh đánh dấu ngưỡng nhấc vật 20 mm",
            slides=[], note_vi="Dự phòng, KHÔNG dùng: có vạch 'Nguong nhac vat S1 (+20mm)' của kiểm tra S1 đã bỏ khỏi phần mềm. Slide 5 dùng sw_annot_side."))

    print("== Giao diện phần mềm đang chạy thật (02/11 20:32, USB Arduino ĐÃ KẾT NỐI) ==")
    if need(LIVE_UI):
        ui = load(LIVE_UI)
        W, H = ui.size                                                      # 2560 x 1656
        save(ui, "ui_guide_live.png", dict(
            group="ui", source=str(LIVE_UI), captured_at=stamp(LIVE_UI),
            desc_vi="Cửa sổ HƯỚNG DẪN GẮP lúc đang chạy với Arduino thật (dòng 'USB Arduino: DA KET NOI'): hai camera có lưới ArUco và khung vật, thanh 5 bước, bốn thẻ servo (phím, số lần bấm, góc hiện tại → đích), ô KET QUA GAP.",
            alt_vi="Ảnh chụp màn hình phần mềm: hai khung camera phía trên, thanh năm bước và bốn thẻ servo phía dưới",
            slides=[], note_vi=OLD_UI_NOTE + " Slide 8 dùng ui_screen_before. Chữ không dấu vì OpenCV putText không vẽ được dấu. Có vài nhãn YOLO nhận nhầm (bottle, airplane, frisbee)."))
        save(blur_regions(ui.crop((0, 56, W, int(H * 0.496))), UI_CAMS_BLUR, ref=UI_CAMS_REF), "ui_guide_cameras.png", dict(
            group="ui", source=str(LIVE_UI), cropped="hai khung camera phía trên của cửa sổ", blurred="màn hình laptop ở mép trái ô cam NGANG và đáy ô cam TREN",
            desc_vi="Hai khung camera của phần mềm: NGANG (MacBook) và TREN (OBSBOT) với lưới, vị trí cm của cốc (X=16,5 cm, Y=13,9 cm) và các khung nhận diện.",
            alt_vi="Hai khung camera có lưới tọa độ và các hộp nhận diện vật kèm tọa độ cm", slides=[6],
            note_vi="Ảnh chụp từ BẢN TRƯỚC khi đơn giản hóa (YOLO đang bật mặc định; phần mềm hiện tại chỉ tách màu, YOLO là tùy chọn --yolo). Chỉ dùng làm bằng chứng trung thực cho giới hạn của YOLO: nhãn nhận nhầm bottle, airplane, frisbee."))
        save(ui.crop((0, int(H * 0.517), W, H)), "ui_guide_steps.png", dict(
            group="ui", source=str(LIVE_UI), cropped="phần điều khiển phía dưới của cửa sổ",
            desc_vi="Thanh năm bước (1 DIEM CHO ... 5 KIEM TRA), dòng BUOC 1/5, bốn thẻ servo và ô KET QUA GAP (Thanh cong: 0, That bai: 0), cùng hàng phím tắt.",
            alt_vi="Phần dưới cửa sổ hướng dẫn gắp: thanh năm bước, bốn thẻ servo và bảng kết quả gắp", slides=[],
            note_vi=OLD_UI_NOTE + " (Thanh năm bước và ô KET QUA GAP S1/S2 đã bỏ khỏi phần mềm.)"))
        save(ui.crop((1500, 200, 2440, 590)), "ui_fk_vs_real.png", dict(
            group="ui", source=str(LIVE_UI), cropped="khung camera TREN quanh đầu kẹp",
            desc_vi="Khung camera TREN: dấu '+' xanh 'Dau kep FK (Z=22mm)' là đầu kẹp mà MÔ HÌNH tính; nhãn 'So voi tam vo: (+2.4, +4.3) cm' cho biết cốc cách điểm đó 2,4 và 4,3 cm trong khi hai ngón kẹp thật đang ở sát cốc.",
            alt_vi="Ảnh phóng to khung camera trên: dấu đầu kẹp theo mô hình nằm lệch khỏi vị trí hai ngón kẹp thật quanh cốc", slides=[],
            note_vi=OLD_UI_NOTE + " Dự phòng cho slide 11 chỉ khi thiếu calib_before_after_*: một lần chụp (20:32:05) với mô hình MẶC ĐỊNH, 'Sai so dau kep: 56 mm' trên màn hình bản cũ."))
        save(ui.crop((0, int(H * 0.944), W, H)), "ui_status_bar.png", dict(
            group="ui", source=str(LIVE_UI), cropped="thanh trạng thái dưới cùng của cửa sổ",
            desc_vi="Thanh trạng thái: 'USB Arduino: DA KET NOI (/dev/cu.usbmodemFX2348N1)', 'Tu dong (P): TAT', 'Vat 2/2 (TAB doi vat)', 'Sai so dau kep: 56 mm', và hàng phím tắt.",
            alt_vi="Thanh trạng thái phần mềm: Arduino đã kết nối, tự động tắt, sai số đầu kẹp 56 mm, hàng phím tắt", slides=[],
            note_vi=OLD_UI_NOTE + " (Auto-Step phím P và phím Y/E đã bỏ khỏi phần mềm; 56 mm là sai số của mô hình MẶC ĐỊNH lúc cốc nằm giữa hai ngón kẹp.)"))
    if need(RELAXED_UI):
        save(load(RELAXED_UI), "ui_guide_relaxed.png", dict(
            group="ui", source=str(RELAXED_UI), captured_at=stamp(RELAXED_UI), mode="mô phỏng (không nối Arduino)",
            desc_vi="Giao diện khi cánh tay đang NGHỈ: dòng cam 'CANH TAY DANG NGHI (ngat xung): bam W A S D I K H de cap xung lai' và thẻ KEP ghi 'NGHI - servo dang nguoi'.",
            alt_vi="Ảnh chụp màn hình phần mềm báo cánh tay đang nghỉ, ngắt xung",
            slides=[], note_vi=OLD_UI_NOTE + " Chụp ở chế độ mô phỏng (không nối Arduino)."))
    hud = RUN4 / "hud_07.jpg"
    if need(hud):
        im = load(hud)
        crop = im.crop((16, 63, 836, 122))
        save(crop.resize((crop.size[0] * 2, crop.size[1] * 2), Image.LANCZOS), "ui_hud_grip_warning.png", dict(
            group="ui", source=str(hud), captured_at=stamp(hud), cropped="hàng KEP của thanh HUD, phóng 2 lần",
            desc_vi="Cảnh báo thật trên màn hình: 'GIU 31s! J nha/X nghi' (chữ đỏ) trên thẻ KEP khi kẹp đã khép quá 30 giây.",
            alt_vi="Hàng thẻ servo kẹp có dòng cảnh báo đỏ giữ kẹp 31 giây, bấm J nhả hoặc X nghỉ", slides=[],
            note_vi=OLD_UI_NOTE + " (Cảnh báo 'GIU Ns' của bản cũ lúc thử thật 20:34; phần mềm hiện tại không còn cảnh báo này, chỉ firmware tự ngắt xung.)"))

    print("== Khung hình buổi gắp thành công 02/11 20:27-20:36 (cam NGANG | cam TREN, đã làm mờ màn hình) ==")
    frames = [
        ("anh_00_batdau", "demo_00_before", "20:27 ban đầu", "Trước khi gắp: cốc đứng giữa tờ giấy, cánh tay giơ cao ở phía trên.", []),
        ("anh_t02", "demo_02_approach", "20:32:12", "Tiếp cận: kẹp mở rộng, hai ngón kẹp đưa tới sát cốc.", []),
        ("anh_t05", "demo_05_knocked", "20:32:42", "Cốc bị đổ nằm nghiêng trước hai ngón kẹp (một trong khoảng 3 lần cốc đổ).", [21]),
        ("anh_t06", "demo_06_grip", "20:32:52", "Cốc nằm giữa hai ngón kẹp (đã kẹp).", [1, 10]),
        ("anh_t07", "demo_07_carry", "20:33:02", "Cốc đang được kẹp và chuyển sang bên trái tờ giấy.", [10]),
        ("anh_t08", "demo_08_place", "20:33:12", "Cốc đã đặt xuống bên trái, cánh tay rút về.", [10]),
        ("anh_t15", "demo_15_tilted", "20:34:22", "Lần kẹp thứ hai: cốc bị nghiêng trong tay kẹp.", [21]),
        ("anh_t16", "demo_16_regrip", "20:34:32", "Lần kẹp thứ hai: cốc đứng lại giữa hai ngón kẹp ở bên trái.", []),
    ]
    for src_stem, dst_stem, when, what, slides in frames:
        for cam, key in (("ngang", "side"), ("tren", "top")):
            p = RUN4 / f"{src_stem}_{cam}.jpg"
            if not need(p):
                continue
            polys = BLUR["side20"] if cam == "ngang" else BLUR["top20"]
            save(blur_regions(load(p), polys), f"{dst_stem}_{key}.jpg", dict(
                group="demo", source=str(p), captured_at=stamp(p), clock=when,
                blurred="màn hình laptop và điện thoại",
                desc_vi=f"{'Cam NGANG (MacBook)' if cam == 'ngang' else 'Cam TRÊN (OBSBOT)'} lúc {when}: {what}",
                alt_vi=f"Khung hình {'camera ngang' if cam == 'ngang' else 'camera trên'}: {what}",
                slides=slides, note_vi=DEMO_NOTE))

    print("== Ảnh gốc trong repo ==")
    for name, nid in (("aruco_A4_clean.png", "repo_aruco_a4_clean.png"),):
        p = PROJECT / name
        if need(p):
            save(load(p), nid, dict(
                group="repo", source=str(p),
                desc_vi="Tờ A4 in 4 mã ArUco (DICT_4X4_50, ID 0-3, cạnh 2,8 cm)" + (" kèm lưới và thước cm ở viền." if "grid" in name else ", bản sạch không lưới."),
                alt_vi="Tờ giấy A4 nằm ngang với bốn mã ArUco ở bốn góc", slides=[], note_vi="Tùy chọn (không dùng mặc định). File sinh bởi generate_aruco_a4.py."))

    print("== Mục cũ giữ lại ==")
    keep_other_entries()
    write_manifest_and_preview(MANIFEST)


if __name__ == "__main__":
    main()
