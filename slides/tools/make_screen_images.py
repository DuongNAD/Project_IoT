#!/usr/bin/env python3
"""Tạo ảnh GIAO DIỆN MỚI cho slide: màn hình hai phần (điều khiển -> success), khung camera có chú thích, ảnh trước / sau hiệu chỉnh.

Dùng CHÍNH app (main.App) ở chế độ mô phỏng trên ảnh camera thật đã lưu, nên ảnh là kết quả thật của mã nguồn hiện tại. Không mở camera,
không mở cổng USB / Serial, không đụng Arduino, không ghi calibration.json (kiểm bằng băm trước và sau khi chạy).

Ảnh ghi vào slides/assets/real/ (đồng thời thêm hoặc thay mục trong assets/manifest.json và tạo lại _preview.jpg):
  ui_screen_before.png      màn hình lúc còn phải bấm phím: ảnh camera 20:27 (cánh tay chưa tới cốc), servo mô phỏng ở Home 90/90/90/95
  ui_screen_done.png        màn hình sau khi MÔ PHỎNG bấm đủ phím theo lệnh và giữ góc > 1 s: XONG! + Thanh cong: 1 lan (ảnh camera 20:32:52, hai ngón kẹp ôm cốc)
  sw_annot_top.jpg, sw_annot_side.jpg   khung camera do phần mềm vẽ (viền giấy, lưới 5 cm, mã ArUco, vị trí cốc) lúc chưa bấm (ảnh 20:27)
  calib_before_after_side.jpg, calib_before_after_top.jpg   hai dấu 'KEP' (mô hình mặc định và mô hình đã hiệu chỉnh) trên ảnh 21:03:35 lúc hai ngón kẹp ôm cốc

Chạy lại, từ thư mục dự án:   .venv/bin/python -B slides/tools/make_screen_images.py
Cần: demo_00_before_* và demo_06_grip_* trong slides/assets/real/ (tạo bằng prepare_real_assets.py), ảnh gốc 20261102_210335_* trong captures/
(thư mục này không nằm trong git), và calibration.json (không có thì không có hiệu chỉnh để minh họa).

Hai điều cần biết khi đọc ảnh:
  * Ảnh camera chụp lúc tờ giấy còn ĐÚNG HƯỚNG ban đầu (đế robot gần mép Y = 0), còn calibration.json ghi đế theo tờ giấy đã xoay 180° ("to_giay" trong
    mục arm_fit). Script đổi đế về hệ lúc chụp bằng phép xoay 180° quanh tâm tờ giấy (photo_frame_config) rồi tự kiểm: dấu 'KEP' đã hiệu chỉnh phải
    cách cốc đo từ chính ảnh không quá CALIB_MAX_CM, không thì dừng thay vì vẽ ảnh sai.
  * Ảnh 21:03:35 là MỘT trong các lần ôm cốc dùng để khớp hiệu chỉnh, nên ảnh trước / sau chỉ cho thấy mô hình khớp với dữ liệu đã dùng để khớp,
    không phải kiểm tra độc lập.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True  # đừng để lại __pycache__ trong repo

TOOLS = Path(__file__).resolve().parent
SLIDES = TOOLS.parent
PROJECT = SLIDES.parent
sys.path[:0] = [str(PROJECT), str(TOOLS)]

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import control as C  # noqa: E402
import main as M  # noqa: E402
import prepare_real_assets as P  # noqa: E402  (blur_regions, upsert_entries)
import vision as V  # noqa: E402
from calibration import CALIBRATION_PATH, apply_calibration  # noqa: E402
from success import check  # noqa: E402

REAL = SLIDES / "assets" / "real"
CAPTURES = PROJECT / "captures"

BEFORE = ("demo_00_before_top.jpg", "demo_00_before_side.jpg", "20:27")      # cánh tay chưa tới cốc
DONE = ("demo_06_grip_top.jpg", "demo_06_grip_side.jpg", "20:32:52")        # hai ngón kẹp ôm cốc
CALIB_STAMP, CALIB_CLOCK = "20261102_210335", "21:03:35"                    # lần ôm cốc có góc servo ghi lại
CALIB_SERVO = (75, 85, 50)                                                   # đế, vai, khuỷu (kẹp 150)
CALIB_GRIP = 150
CALIB_MAX_CM = 2.0            # dấu 'KEP' đã hiệu chỉnh cách cốc quá ngần này thì ảnh sai hệ tọa độ: không vẽ
CUP_BASE_RADIUS_CM = 1.5      # bán kính đáy cốc đỏ (thân ~3,4 cm, nắp ~4 cm), để suy tâm đáy từ mép dưới của khối cam trong ảnh
SETTLE_S = 3.5                # chạy vòng lặp app ngần này giây cho luồng tìm vật và trung bình trượt ổn định

# Màn hình laptop lọt vào mép khung ở ảnh 21:xx (đọc được chữ): làm mờ trước khi vẽ. Tọa độ trong khung 1920x1080.
SIDE_SCREEN_21 = [(0, 0), (520, 0), (520, 150), (500, 300), (450, 450), (400, 580), (330, 720), (250, 860), (150, 990), (0, 1080)]
TOP_SCREEN_21 = [(480, 1080), (880, 880), (1330, 882), (1500, 918), (1700, 958), (1800, 1080)]

ORANGE, GREEN, BLUE, WHITE = (0, 128, 255), (0, 230, 0), (255, 110, 0), (255, 255, 255)  # BGR


def vn(value: float, digits: int = 1) -> str:
    """Số thập phân kiểu Việt (dấu phẩy) cho mô tả tiếng Việt."""
    return f"{value:.{digits}f}".replace(".", ",")


def md5(path) -> str | None:
    path = Path(path)
    return hashlib.md5(path.read_bytes()).hexdigest() if path.exists() else None


def need(path: Path) -> Path:
    if not path.exists():
        raise SystemExit(f"Thiếu {path}. Chạy slides/tools/prepare_real_assets.py trước (ảnh demo_*), hoặc kiểm tra thư mục captures/.")
    return path


# ==============================================================================
# 1. Hiệu chỉnh đổi về hệ tờ giấy lúc chụp
# ==============================================================================
def rotate_sheet_180(cfg: dict) -> None:
    """Đổi vị trí và hướng đế sang hệ của tờ giấy xoay 180° quanh tâm (mã ID 0 <-> 2, 1 <-> 3). Phép này là phép nghịch đảo của chính nó."""
    cfg["base_x_cm"] = V.SHEET_W_CM - cfg["base_x_cm"]
    cfg["base_y_cm"] = V.SHEET_H_CM - cfg["base_y_cm"]
    cfg["base_heading_deg"] = (cfg["base_heading_deg"] + 180.0 + 180.0) % 360.0 - 180.0


def photo_frame_config() -> dict:
    """ARM_CONFIG của calibration.json, đổi sang hệ tờ giấy lúc chụp ảnh 20:27-21:16 (xem docstring đầu file). Hai góc chuẩn vai / khuỷu và hình học càng kẹp không đổi."""
    cfg = dict(C.ARM_CONFIG_DEFAULTS)
    if not apply_calibration(cfg):
        raise SystemExit("Không có calibration.json (hoặc rỗng): không có hiệu chỉnh để minh họa.")
    rotate_sheet_180(cfg)
    return cfg


# ==============================================================================
# 2. Chạy app mô phỏng trên một cặp ảnh (màn hình, khung chú thích)
# ==============================================================================
def make_app(top: Path, side: Path, clock: str, cfg: dict) -> "M.App":
    """App thật (main.App) với hai ảnh tĩnh thay camera, không mở cổng USB; nhãn camera ghi rõ là ảnh đã lưu."""
    args = M.parse_args(["--top", str(top), "--side", str(side), "--no-serial", "--headless"])
    app = M.App(args)
    C.ARM_CONFIG.update(cfg)  # App nạp calibration.json thô vào ARM_CONFIG; ghi đè bằng bản đã đổi về hệ lúc chụp
    app.cam_top.label = f"anh da luu {clock}"
    app.cam_side.label = f"anh da luu {clock}"
    return app


def settle(app, seconds: float):
    """Chạy vòng dựng khung của app (như --headless) trong ngần này giây; trả về (màn hình, Plan, Result) cuối cùng."""
    end, out = time.time() + seconds, None
    while time.time() < end:
        out = app.render()
        time.sleep(0.04)
    return out


def wait_for_target(app, timeout: float = 30.0):
    """Chạy tới khi app thấy cốc, rồi thêm SETTLE_S giây cho trung bình trượt vị trí vật (control.py) ổn định."""
    end = time.time() + timeout
    while time.time() < end:
        screen, plan, result = app.render()
        if plan.found and app.control.objects:
            return settle(app, SETTLE_S)
        time.sleep(0.04)
    raise SystemExit("App không thấy cốc trong ảnh: kiểm tra ảnh đầu vào và lưới ArUco.")


def press_until_done(app) -> int:
    """MÔ PHỎNG người bấm phím đúng như màn hình chỉ: lặp 'bấm phím của lệnh đầu tiên' cho tới khi success.check báo xong. Trả về số lần bấm."""
    presses = 0
    for _ in range(400):
        result = check(app.control.update(app.vision.objects))
        if result.done:
            return presses
        app.control.press(result.next_move.key)
        presses += 1
    raise SystemExit("Mô phỏng bấm phím không tới được góc đích (kiểm tra hiệu chỉnh hoặc tầm với).")


def view_info(app, mode: str) -> dict:
    sheet = app.vision.sheets[mode]
    return {"ma_dang_dung": len(sheet.markers), "ma_thay": sheet.n_seen}


def run_screen(top_name: str, side_name: str, clock: str, cfg: dict, press: bool) -> dict:
    """Một lần chạy app trên cặp ảnh demo_*: màn hình, hai khung chú thích sạch (chưa vẽ DICH / KEP), kế hoạch và kết quả."""
    app = make_app(need(REAL / top_name), need(REAL / side_name), clock, cfg)
    try:
        screen, plan, result = wait_for_target(app)
        annotated = {"top": app._frame(app.cam_top, "topdown").copy(), "side": app._frame(app.cam_side, "side").copy()}
        facts = {
            "anh": [top_name, side_name], "gio": clock, "vat_cm": [round(v, 1) for v in plan.target_cm], "servo_hien_tai": plan.now[:3],
            "goc_dich": plan.goal, "lenh": [(m.key, m.steps, m.words, m.degrees) for m in plan.moves], "con_lai": result.remaining,
            "trang_thai": result.state, "cam_tren": view_info(app, "topdown"), "cam_ngang": view_info(app, "side"),
            "next": result.next_move and (result.next_move.key, result.next_move.steps, result.next_move.words, result.next_move.degrees),
        }
        if press:
            facts["so_lan_bam_mo_phong"] = press_until_done(app)
            screen, plan, result = settle(app, 1.8)  # giữ đủ góc > HOLD_S (1 s) để success đếm 1 lần
            if not (result.done and result.count == 1):
                raise SystemExit(f"Success không đếm được 1 lần (state={result.state}, count={result.count}).")
            facts.update(servo_sau=plan.now[:3], trang_thai_sau=result.state, thanh_cong=result.count)
        assert screen is not None and not plan.usb_ok  # chân trang phải ghi 'USB Arduino: MO PHONG'
        return {"screen": screen.copy(), "annotated": annotated, "facts": facts}
    finally:
        app.close()


# ==============================================================================
# 3. Ảnh trước / sau hiệu chỉnh trên khung 21:03:35 (hai ngón kẹp ôm cốc)
# ==============================================================================
def cup_ground_from_side(frame, view) -> tuple[tuple[float, float], tuple]:
    """Tâm đáy cốc (cm trên giấy) đo từ khung cam NGANG, nơi cốc nhìn rõ và không bị che.

    Tách khối cam đỏ lớn nhất (phép mở bỏ dây servo mảnh), lấy giữa theo chiều ngang và mép dưới của khối. Mép dưới ấy là điểm thấp nhất của đường tròn
    đáy nằm trên mặt giấy, nên tâm được dịch trong ảnh cho tới khi đường tròn bán kính CUP_BASE_RADIUS_CM quanh nó (chiếu bằng homography) chạm đúng mép dưới.
    Sai số khoảng ±1 cm (lưới cam NGANG nhìn xiên, 3 mã thấy được).
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (0, 150, 150), (20, 255, 255))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25)))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        raise SystemExit("Không thấy cốc cam đỏ trong khung cam NGANG của ảnh hiệu chỉnh.")
    box = cv2.boundingRect(max(cnts, key=cv2.contourArea))
    cx, bottom = box[0] + box[2] / 2.0, box[1] + box[3]
    center = np.array(V.px_to_cm(view.H_px2cm, cx, bottom - 30.0), dtype=float)
    angles = np.linspace(0.0, 2.0 * np.pi, 90, endpoint=False)
    for _ in range(8):
        ring = (center + CUP_BASE_RADIUS_CM * np.stack([np.cos(angles), np.sin(angles)], axis=1)).reshape(1, -1, 2).astype(np.float32)
        low = cv2.perspectiveTransform(ring, view.H_cm2px)[0][:, 1].max()
        p = np.array(V.cm_to_px(view.H_cm2px, *center), dtype=float)
        p[1] += bottom - low
        center = np.array(V.px_to_cm(view.H_px2cm, p[0], p[1]), dtype=float)
    return (float(center[0]), float(center[1])), box


def sheet_view(frame, side: bool):
    """Lưới tờ giấy của một khung (cùng bộ dò mã như app)."""
    view = V.Sheet()
    view.update(frame)
    if view.H_px2cm is None or len(view.markers) < 3:
        raise SystemExit(f"Khung {'cam NGANG' if side else 'cam TREN'} của ảnh hiệu chỉnh chưa thấy đủ 3 mã ArUco.")
    return view


def outlined(img, text, org, scale, color, thick, k):
    """Chữ có viền đen cho dễ đọc trên mọi nền (cỡ chữ và nét phóng theo k)."""
    for col, th in (((0, 0, 0), thick + 2), (color, thick)):
        cv2.putText(img, text, (int(org[0]), int(org[1])), cv2.FONT_HERSHEY_SIMPLEX, scale * k, col, max(1, int(th * k)), cv2.LINE_AA)


def draw_marker(img, p_px, color, label, k):
    """Dấu '+' có viền đen (đọc được trên nền đen của thân kẹp) và nhãn có viền."""
    p = (int(p_px[0]), int(p_px[1]))
    size, thick = int(38 * k), max(2, int(3 * k))
    cv2.drawMarker(img, p, (0, 0, 0), cv2.MARKER_CROSS, size, thick + 3, cv2.LINE_AA)
    cv2.drawMarker(img, p, color, cv2.MARKER_CROSS, size, thick, cv2.LINE_AA)
    outlined(img, label, (p[0] + 26 * k, p[1] - 16 * k), 0.62, color, 2, k)


def calib_image(frame, blur_poly, view, tips, cup_cm, crop, cup_ring: bool, caption: list[str]):
    """Khung camera đã làm mờ màn hình, vẽ lưới 5 cm và hai dấu 'KEP' của hai mô hình (hình chiếu xuống mặt giấy, giống app), rồi cắt."""
    img = P.blur_regions(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)), [blur_poly])
    out = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
    k = max(1.0, out.shape[1] / 1280)
    V.draw_grid(out, view.H_cm2px, k)
    if cup_ring:
        c = V.cm_to_px(view.H_cm2px, *cup_cm)
        cv2.circle(out, (int(c[0]), int(c[1])), int(30 * k), (0, 0, 0), max(2, int(3 * k)) + 3, cv2.LINE_AA)
        cv2.circle(out, (int(c[0]), int(c[1])), int(30 * k), BLUE, max(2, int(3 * k)), cv2.LINE_AA)
        outlined(out, "COC (do tu cam ngang)", (c[0] - 120 * k, c[1] + 66 * k), 0.62, BLUE, 2, k)  # dưới vòng: tránh đè nhãn hai dấu '+'
    for name, color, label in (("default", ORANGE, "MAC DINH"), ("calibrated", GREEN, "SAU HIEU CHINH")):
        draw_marker(out, V.cm_to_px(view.H_cm2px, *tips[name][:2]), color, label, k)
    x0, y0, x1, y1 = crop
    out = out[y0:y1, x0:x1].copy()
    for i, line in enumerate(caption):
        outlined(out, line, (14 * k, out.shape[0] - (14 + 24 * (len(caption) - 1 - i)) * k), 0.55, WHITE, 1, k)
    return out


def run_calibration(cfg_photo: dict) -> dict:
    """Ảnh trước / sau hiệu chỉnh (cam NGANG nhìn rõ cốc; cam TREN bị thân kẹp che cốc) + số đo. Dừng nếu dấu đã hiệu chỉnh không khớp ảnh."""
    raw_side = cv2.imread(str(need(CAPTURES / f"{CALIB_STAMP}_cam_ngang_macbook.jpg")))
    raw_top = cv2.imread(str(need(CAPTURES / f"{CALIB_STAMP}_cam_tren_obsbot.jpg")))
    view_side, view_top = sheet_view(raw_side, side=True), sheet_view(raw_top, side=False)
    cup_cm, cup_box = cup_ground_from_side(raw_side, view_side)

    raw_cfg = dict(C.ARM_CONFIG_DEFAULTS)
    apply_calibration(raw_cfg)
    configs = {"default": dict(C.ARM_CONFIG_DEFAULTS), "calibrated": cfg_photo, "calibration_json_chua_xoay": raw_cfg}
    tips = {name: C.predict_tip(CALIB_SERVO, cfg) for name, cfg in configs.items()}
    dist = {name: float(np.hypot(t[0] - cup_cm[0], t[1] - cup_cm[1])) for name, t in tips.items()}
    if dist["calibrated"] > CALIB_MAX_CM:
        raise SystemExit(f"Dấu 'KEP' đã hiệu chỉnh cách cốc {dist['calibrated']:.1f} cm (> {CALIB_MAX_CM} cm): calibration.json không còn khớp hệ tờ giấy của ảnh "
                         f"{CALIB_CLOCK} (đã khớp lại với tờ giấy khác?). Không vẽ ảnh sai; xem photo_frame_config().")
    if dist["default"] < 3.0:
        raise SystemExit(f"Mô hình mặc định chỉ lệch {dist['default']:.1f} cm: ảnh trước / sau sẽ không cho thấy khác biệt.")

    caption = [f"ANH THAT {CALIB_CLOCK}  servo {CALIB_SERVO[0]}/{CALIB_SERVO[1]}/{CALIB_SERVO[2]}, kep {CALIB_GRIP}",
               "+ = dau kep theo mo hinh (chieu xuong mat giay)"]
    side = calib_image(raw_side, SIDE_SCREEN_21, view_side, tips, cup_cm, (100, 60, 1500, 848), False, caption)
    top = calib_image(raw_top, TOP_SCREEN_21, view_top, tips, cup_cm, (330, 130, 1530, 805), True, caption)
    return {"side": side, "top": top, "facts": {
        "servo": list(CALIB_SERVO), "coc_cm_do_tu_cam_ngang": [round(v, 2) for v in cup_cm], "khoi_cam_cam_ngang_px": list(cup_box),
        "dau_kep_cm": {n: [round(float(v), 2) for v in t] for n, t in tips.items()},
        "cach_coc_cm": {n: round(d, 2) for n, d in dist.items()},
        "luoi": {"cam_ngang": len(view_side.markers), "cam_tren": len(view_top.markers)},
        "de_sau_xoay": [round(cfg_photo[k], 2) for k in ("base_x_cm", "base_y_cm", "base_heading_deg")],
    }}


# ==============================================================================
# 4. Ghi ảnh và manifest
# ==============================================================================
def write_image(name: str, img) -> None:
    path = REAL / name
    if name.endswith(".png"):
        cv2.imwrite(str(path), img, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    else:
        cv2.imwrite(str(path), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(f"  ghi {name:28s} {img.shape[1]}x{img.shape[0]}  {round(path.stat().st_size / 1024)} KB")


def entry(name: str, meta: dict) -> dict:
    path = REAL / name
    with Image.open(path) as im:
        size = list(im.size)
    return {"file": f"assets/real/{name}", "size_px": size, "kb": round(path.stat().st_size / 1024), **meta}


INHERITED_BLUR = "màn hình laptop và điện thoại (đã làm mờ sẵn trong ảnh demo_* dùng làm đầu vào)"


def move_text(m) -> str:
    key, steps, words, degrees = m
    return f"BAM {key.upper()} x {steps} · {words} {degrees} DO"


def manifest_entries(before: dict, done: dict, calib: dict | None) -> list[dict]:
    bf, df = before["facts"], done["facts"]
    nxt = bf["next"]
    src_before = f"slides/assets/real/{BEFORE[0]} + {BEFORE[1]} (ảnh thật {BEFORE[2]}, đã làm mờ màn hình)"
    src_done = f"slides/assets/real/{DONE[0]} + {DONE[1]} (ảnh thật {DONE[2]}, đã làm mờ màn hình)"
    sim = "Chạy MÔ PHỎNG trên ảnh đã lưu (chân trang 'USB Arduino: MO PHONG'), KHÔNG phải chạy trực tiếp."
    top_n = bf["cam_tren"]["ma_dang_dung"]
    entries = [
        entry("ui_screen_before.png", dict(
            group="screen", source=src_before, clock=BEFORE[2], mode="mô phỏng trên ảnh đã lưu", blurred=INHERITED_BLUR,
            desc_vi=(f"Màn hình hai phần của phần mềm hiện tại, chạy mô phỏng trên ảnh camera thật lúc {BEFORE[2]} (cánh tay chưa tới cốc; servo mô phỏng ở Home 90/90/90/95, "
                     f"không nối Arduino). Trên cùng là hai camera (NGANG | TRÊN) có lưới 5 cm, vòng DICH quanh cốc ở ({vn(bf['vat_cm'][0])}; {vn(bf['vat_cm'][1])}) cm và dấu KEP. "
                     f"Ô 1 ĐIỀU KHIỂN ghi to '{move_text(nxt)}' và ba dòng servo đế / vai / khuỷu (góc hiện tại → góc đích); "
                     f"ô 2 SUCCESS ghi 'CHUA XONG' và 'con {bf['con_lai']} lan bam'; chân trang ghi 'USB Arduino: MO PHONG'."),
            alt_vi=(f"Ảnh chụp màn hình phần mềm: hai khung camera phía trên; bên trái lệnh lớn '{move_text(nxt)}'; bên phải 'CHUA XONG', 'con {bf['con_lai']} lan bam'"),
            slides=[8],
            note_vi=(sim + " Nhãn camera ghi 'anh da luu'. Chữ không dấu vì OpenCV putText không vẽ được dấu: giữ nguyên, nói rõ khi thuyết trình. "
                     f"Góc đích {bf['goc_dich']} tính bằng calibration.json (đã đổi về hệ tờ giấy lúc chụp); cốc đo ở ({vn(bf['vat_cm'][0])}; {vn(bf['vat_cm'][1])}) cm.")),
        ),
        entry("ui_screen_done.png", dict(
            group="screen", source=src_done, clock=DONE[2], mode="mô phỏng trên ảnh đã lưu", blurred=INHERITED_BLUR,
            desc_vi=(f"Cùng màn hình sau khi MÔ PHỎNG bấm đủ {df['so_lan_bam_mo_phong']} lần theo lệnh và giữ đúng góc hơn 1 giây: phần 1 ghi 'Khong can bam them', ba dòng servo 'DA DUNG'; "
                     f"phần 2 ghi 'XONG!' màu xanh và 'Thanh cong: 1 lan'. Ảnh camera là ảnh thật lúc {DONE[2]} khi hai ngón kẹp đang ôm cốc; "
                     f"phần mềm đo cốc ở ({vn(df['vat_cm'][0])}; {vn(df['vat_cm'][1])}) cm trên ảnh này."),
            alt_vi=("Ảnh chụp màn hình phần mềm: hai khung camera phía trên thấy hai ngón kẹp ôm cốc; bên trái 'Khong can bam them'; bên phải 'XONG!' màu xanh "
                    "và dòng 'Thanh cong: 1 lan'"),
            slides=[9],
            note_vi=(sim + " Phím do script bấm giả lập, nên 'Thanh cong: 1 lan' KHÔNG phải số lần gắp thật và góc servo trên màn hình KHÔNG phải góc thật lúc chụp ảnh. "
                     f"Góc đích app tính từ ảnh này: {df['goc_dich']}. Lệnh ban đầu còn {df['con_lai']} lần bấm; mô phỏng dừng sau {df['so_lan_bam_mo_phong']} lần vì lệch không quá 1 bước (2°) đã tính là tới. Cốc đo ở ({vn(df['vat_cm'][0])}; {vn(df['vat_cm'][1])}) cm, khác ảnh {BEFORE[2]} "
                     f"({vn(bf['vat_cm'][0])}; {vn(bf['vat_cm'][1])}) cm vì hai ngón kẹp che một phần cốc: đừng ghép số của hai ảnh làm một câu chuyện.")),
        ),
        entry("sw_annot_top.jpg", dict(
            group="annot", source=src_before, clock=BEFORE[2], mode="mô phỏng trên ảnh đã lưu", blurred=INHERITED_BLUR,
            desc_vi=(f"Khung camera TRÊN (ảnh thật {BEFORE[2]}) do chính phần mềm vẽ: viền tờ A4, lưới 5 cm dựng từ mã ArUco ({top_n} mã thấy được, mã thứ tư bị cánh tay che nhưng lưới vẫn đủ), "
                     f"vòng xanh quanh cốc kèm nhãn 'X=... Y=... cm' và dòng 'Luoi A4: thay .../4 ma ArUco'."),
            alt_vi=(f"Ảnh camera trên có lưới 5 cm phủ lên tờ A4, bốn góc có mã ArUco (một mã bị cánh tay che), vòng xanh quanh cốc đỏ kèm tọa độ X, Y tính bằng cm"),
            slides=[5],
            note_vi="Khung sạch do app vẽ (chưa có vòng DICH và dấu KEP). Cánh tay trong ảnh giơ cao chưa tới cốc. Chữ trên ảnh không dấu."),
        ),
        entry("sw_annot_side.jpg", dict(
            group="annot", source=src_before, clock=BEFORE[2], mode="mô phỏng trên ảnh đã lưu", blurred=INHERITED_BLUR,
            desc_vi=(f"Khung camera NGANG (ảnh thật {BEFORE[2]}) với cùng lưới 5 cm nhìn nghiêng, bốn mã ArUco thấy rõ và dòng 'Luoi A4: thay .../4 ma ArUco'; "
                     f"cốc đứng giữa tờ giấy, cánh tay ở ngoài khung phía trên."),
            alt_vi="Ảnh camera ngang nhìn nghiêng: lưới 5 cm phủ lên tờ A4 có bốn mã ArUco ở bốn góc, cốc đỏ đứng giữa giấy",
            slides=[5],
            note_vi="Khung sạch do app vẽ (cam NGANG không vẽ nhãn vật, chỉ lưới và mã). Chữ trên ảnh không dấu."),
        ),
    ]
    if calib is not None:
        cf = calib["facts"]
        d_def, d_cal = cf["cach_coc_cm"]["default"], cf["cach_coc_cm"]["calibrated"]
        src = f"captures/{CALIB_STAMP}_cam_ngang_macbook.jpg, captures/{CALIB_STAMP}_cam_tren_obsbot.jpg (ảnh thật {CALIB_CLOCK}, đã làm mờ màn hình laptop)"
        common = (f"Hai dấu '+' là đầu kẹp mà phần mềm tính từ góc servo {CALIB_SERVO[0]}/{CALIB_SERVO[1]}/{CALIB_SERVO[2]}: dấu cam 'MAC DINH' (mô hình mặc định) rơi ra giấy trống, "
                  f"cách cốc khoảng {round(d_def)} cm; dấu xanh 'SAU HIEU CHINH' (mô hình đã hiệu chỉnh trong calibration.json) nằm sát cốc, cách khoảng {round(d_cal)} cm "
                  f"(đo trên ảnh, sai số khoảng ±1 cm).")
        note = (f"Ảnh thật {CALIB_CLOCK}; góc servo ghi lại lúc đó (kẹp {CALIB_GRIP}°). Đây là MỘT trong các lần ôm cốc dùng để khớp hiệu chỉnh (n = 10, sai số khớp RMS 8,5 mm, bỏ-một-mẫu 11,6 mm), "
                f"nên ảnh chỉ cho thấy mô hình khớp dữ liệu đã dùng, không phải kiểm tra độc lập. calibration.json ghi đế theo tờ giấy xoay 180° so với lúc chụp; script đã xoay lại "
                f"đế thành ({vn(cf['de_sau_xoay'][0], 2)}; {vn(cf['de_sau_xoay'][1], 2)}) cm, hướng {vn(cf['de_sau_xoay'][2])}°. Dấu là hình chiếu xuống mặt giấy (như dấu KEP của app).")
        entries += [
            entry("calib_before_after_side.jpg", dict(
                group="calib", source=src, clock=CALIB_CLOCK, mode="ảnh thật, dấu do mã nguồn tính", blurred="màn hình laptop ở mép trái khung",
                desc_vi=f"Ảnh thật camera NGANG lúc {CALIB_CLOCK}: hai ngón kẹp đang ôm cốc đỏ (kẹp {CALIB_GRIP}°). " + common,
                alt_vi="Ảnh camera ngang: hai ngón kẹp đen ôm cốc đỏ trên tờ giấy có lưới; dấu cam 'MAC DINH' nằm trên giấy trống phía trước cốc, dấu xanh 'SAU HIEU CHINH' nằm ngay tại cốc",
                slides=[11], note_vi="Ảnh ƯU TIÊN cho slide 11: cốc nhìn rõ giữa hai ngón kẹp. " + note),
            ),
            entry("calib_before_after_top.jpg", dict(
                group="calib", source=src, clock=CALIB_CLOCK, mode="ảnh thật, dấu do mã nguồn tính", blurred="màn hình laptop ở đáy khung (đã cắt bỏ khỏi ảnh)",
                desc_vi=(f"Ảnh thật camera TRÊN lúc {CALIB_CLOCK}: thân tay kẹp che gần hết cốc (chỉ thấy mép nắp cam). Vòng xanh dương 'COC' là vị trí cốc đo từ ảnh camera NGANG cùng lúc. " + common),
                alt_vi="Ảnh camera trên nhìn xuống: thân tay kẹp đen che cốc; dấu xanh 'SAU HIEU CHINH' nằm trên thân tay kẹp sát vòng 'COC', dấu cam 'MAC DINH' nằm cách xa trên giấy trống",
                slides=[], note_vi="DỰ PHÒNG, không dùng mặc định: phụ cho calib_before_after_side (cốc bị thân kẹp che nên bằng chứng yếu hơn). " + note),
            ),
        ]
    return entries


def main() -> None:
    calibration_before = md5(CALIBRATION_PATH)
    cfg = photo_frame_config()
    print(f"calibration.json đổi về hệ ảnh: đế ({cfg['base_x_cm']:.2f}; {cfg['base_y_cm']:.2f}) cm, hướng {cfg['base_heading_deg']:.1f}°")

    print("== Màn hình trước khi bấm (ảnh 20:27) ==")
    before = run_screen(*BEFORE[:2], BEFORE[2], cfg, press=False)
    print("== Màn hình sau khi mô phỏng bấm xong (ảnh 20:32:52) ==")
    done = run_screen(*DONE[:2], DONE[2], cfg, press=True)
    print("== Ảnh trước / sau hiệu chỉnh (ảnh 21:03:35) ==")
    calib = run_calibration(cfg)

    REAL.mkdir(parents=True, exist_ok=True)
    write_image("ui_screen_before.png", before["screen"])
    write_image("ui_screen_done.png", done["screen"])
    write_image("sw_annot_top.jpg", before["annotated"]["top"])
    write_image("sw_annot_side.jpg", before["annotated"]["side"])
    write_image("calib_before_after_side.jpg", calib["side"])
    write_image("calib_before_after_top.jpg", calib["top"])
    P.upsert_entries(manifest_entries(before, done, calib))

    if md5(CALIBRATION_PATH) != calibration_before:
        raise SystemExit("calibration.json đã bị đổi trong lúc chạy (không được xảy ra)!")
    print("\ncalibration.json không đổi (băm trước = băm sau).")
    facts = {"truoc": before["facts"], "xong": done["facts"], "hieu_chinh": calib["facts"]}
    print(json.dumps(facts, ensure_ascii=False, indent=2, default=lambda o: o.item() if hasattr(o, "item") else list(o)))


if __name__ == "__main__":
    main()
