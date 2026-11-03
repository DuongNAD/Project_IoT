"""Dò tờ A4 qua mã ArUco, tách vật theo màu, đổi phát hiện thành vật có vị trí cm (phối cảnh, vật có màu) và bộ theo dõi tổng hợp, trên cảnh tổng hợp có đáp án."""

import time

import cv2
import numpy as np
import pytest
from synth import (
    FRAME_H,
    FRAME_W,
    PPC,
    cm_to_texture_px,
    corner_error_px,
    draw_disc,
    occlude_markers,
    render,
    sheet_texture,
    side_camera,
    top_camera,
)

import vision as V

DISC_CM = (20.0, 12.0)  # Vị trí tâm vật màu trên tờ giấy (cm)


@pytest.fixture(scope="module")
def scene():
    top, side = top_camera(), side_camera()
    plain = sheet_texture()
    with_object = sheet_texture(lambda img: draw_disc(img, *DISC_CM, 2.2))
    return {
        "top": top,
        "side": side,
        "top_frame": render(top, plain),
        "side_frame": render(side, plain),
        "top_object_frame": render(top, with_object),
    }


def settle(tracker, frame, times=3):
    view = None
    for _ in range(times):
        view = tracker.update(frame)
    return view


def test_sheet_tracker_recovers_homography_for_both_views(scene):
    for tag in ("top", "side"):
        view = settle(V.SheetTracker(), scene[f"{tag}_frame"])
        assert view.source == "aruco" and view.n_seen == 4 and view.n_known == 4
        assert view.rms_px < 1.5
        assert corner_error_px(view, scene[tag]) < 1.5, f"cam {tag} lệch lưới"
        # Pixel -> cm cho tâm tờ giấy phải ra (14.85, 10.5)
        cx, cy = V.px_to_cm(view.H_px2cm, *scene[tag].project(14.85, 10.5))
        assert abs(cx - 14.85) < 0.1 and abs(cy - 10.5) < 0.1


def test_sheet_tracker_remembers_markers_hidden_by_the_arm(scene):
    tracker = V.SheetTracker()
    settle(tracker, scene["side_frame"])
    # Cánh tay che 2 mã: vẫn đủ mã trong khung -> lưới chính xác
    view = tracker.update(occlude_markers(scene["side_frame"], scene["side"], (1, 2)))
    assert view.n_seen == 2 and view.n_known == 4 and view.source == "aruco"
    assert corner_error_px(view, scene["side"]) < 1.5
    # Che 3 mã: chỉ thấy 1 mã nhưng vẫn dùng mã đã nhớ
    view = tracker.update(occlude_markers(scene["side_frame"], scene["side"], (0, 1, 2)))
    assert view.n_seen == 1 and view.source == "memory" and view.n_known == 4
    assert corner_error_px(view, scene["side"]) < 1.5
    # Chưa từng thấy gì mà chỉ thấy 1 mã thì không đủ để tính lưới
    fresh = V.SheetTracker().update(occlude_markers(scene["side_frame"], scene["side"], (0, 1, 2)))
    assert fresh.source == "none" and fresh.H_px2cm is None


def test_sheet_tracker_forgets_memory_when_the_camera_is_bumped(scene):
    tracker = V.SheetTracker()
    settle(tracker, scene["top_frame"])
    bumped = cv2.warpAffine(scene["top_frame"], np.float32([[1, 0, 45], [0, 1, 30]]), (FRAME_W, FRAME_H))
    for _ in range(2):  # Hai khung nhiễu đầu chưa đủ để kết luận xô lệch
        tracker.update(bumped)
    assert tracker.memory
    view = tracker.update(bumped)
    assert view.n_known == 4
    u, v = V.cm_to_px(view.H_cm2px, 0, 0)
    tu, tv = scene["top"].project(0, 0)
    assert abs(u - (tu + 45)) < 3 and abs(v - (tv + 30)) < 3, "phải bám theo vị trí mới sau khi bị xô"


def test_sheet_tracker_fallback_estimates_the_page_without_markers(scene):
    blank = scene["top_frame"].copy()
    blank = occlude_markers(blank, scene["top"], (0, 1, 2, 3))
    view = V.SheetTracker(allow_fallback=True).update(blank)
    assert view.source == "fallback" and view.H_px2cm is not None
    quad = V.sheet_quad_px(view.H_cm2px)
    truth = np.float32([scene["top"].project(x, y) for x, y in ((0, 0), (29.7, 0), (29.7, 21), (0, 21))])
    # Thứ tự góc chỉ là ước đoán nhưng 4 góc phải trùng tờ giấy thật (sai số vài pixel)
    for corner in truth:
        assert np.min(np.linalg.norm(quad - corner, axis=1)) < 12


def test_color_object_detection_finds_the_disc_and_rejects_the_arm(scene):
    view = settle(V.SheetTracker(), scene["top_object_frame"])
    found = V.detect_color_objects(scene["top_object_frame"], view.H_px2cm, view.H_cm2px)
    assert len(found) == 1 and found[0]["cls"] == "vat mau"
    cx, cy = V.px_to_cm(view.H_px2cm, *found[0]["ref_pt"])
    assert abs(cx - DISC_CM[0]) < 0.4 and abs(cy - DISC_CM[1]) < 0.4
    assert 38 < found[0]["size_mm"][0] < 50  # Đĩa bán kính 2.2 cm -> đường kính ~44 mm

    def arm_and_wires(img):
        # Dây điện cam mảnh (bị loại) và nhãn servo xanh nằm lọt giữa phần đen của cánh tay (bị loại)
        cv2.line(img, (300, 300), (700, 340), (40, 90, 235), 3, cv2.LINE_AA)
        cv2.rectangle(img, (800, 440), (1120, 660), (15, 15, 15), -1)
        cv2.rectangle(img, (900, 500), (1000, 600), (235, 120, 40), -1)

    frame = render(scene["top"], sheet_texture(arm_and_wires))
    view = settle(V.SheetTracker(), frame)
    assert V.detect_color_objects(frame, view.H_px2cm, view.H_cm2px) == []

    def object_between_the_jaws(img):
        # Vật chỉ chạm một cạnh vào phần đen (như cốc nằm giữa hai ngón kẹp) thì vẫn phải được nhận
        cv2.rectangle(img, (800, 500), (900, 600), (235, 120, 40), -1)
        cv2.rectangle(img, (900, 480), (1100, 620), (15, 15, 15), -1)

    frame = render(scene["top"], sheet_texture(object_between_the_jaws))
    view = settle(V.SheetTracker(), frame)
    assert len(V.detect_color_objects(frame, view.H_px2cm, view.H_cm2px)) == 1


def test_color_object_detection_ignores_hands_and_blobs_too_big_to_grasp(scene):
    """Bàn tay đưa vào tờ giấy (khối da to, dính mép giấy) hay khối rộng hơn miệng kẹp không phải vật cần gắp (ảnh chụp thật)."""
    skin = (110, 140, 225)  # BGR: màu da người, đủ bão hòa để lọt ngưỡng tách màu

    def detect(draw):
        frame = render(scene["top"], sheet_texture(draw))
        view = settle(V.SheetTracker(), frame)
        return V.detect_color_objects(frame, view.H_px2cm, view.H_cm2px)

    def hand_from_the_right_edge(img):
        cv2.rectangle(img, cm_to_texture_px(22, 8), cm_to_texture_px(29.7, 15), skin, -1)  # cẳng tay từ ngoài mép giấy
        cv2.ellipse(img, cm_to_texture_px(18, 11.5), (int(5 * PPC), int(4.5 * PPC)), 0, 0, 360, skin, -1)  # bàn tay

    def palm_inside_the_sheet(img):
        cv2.ellipse(img, cm_to_texture_px(14.85, 10.5), (int(7 * PPC), int(5 * PPC)), 0, 0, 360, skin, -1)  # 14 x 10 cm

    def fingertip_on_the_edge(img):
        cv2.rectangle(img, cm_to_texture_px(26.5, 9), cm_to_texture_px(29.7, 11), skin, -1)

    assert detect(hand_from_the_right_edge) == []
    assert detect(palm_inside_the_sheet) == []
    assert detect(fingertip_on_the_edge) == []

    def cup_and_box(img):
        draw_disc(img, 8.0, 5.0, 3.2)  # Cốc rộng 64 mm, đặt cách mép giấy ~ 2 cm
        cv2.rectangle(img, cm_to_texture_px(20, 14), cm_to_texture_px(26, 17), (40, 90, 235), -1)  # Hộp 6 x 3 cm

    found = detect(cup_and_box)
    assert len(found) == 2, "vật vừa miệng kẹp phải còn được nhận"
    narrow = sorted(round(f["size_mm"][0]) for f in found)
    assert 28 <= narrow[0] <= 36 and 58 <= narrow[1] <= 70, narrow


def test_bbox_size_mm_measures_real_size_on_the_sheet(scene):
    view = settle(V.SheetTracker(), scene["top_frame"])
    # Hộp 4 x 3 cm trên mặt giấy, nhìn từ trên xuống
    corners = np.float32([scene["top"].project(x, y) for x, y in ((10, 5), (14, 5), (14, 8), (10, 8))])
    bbox = (corners[:, 0].min(), corners[:, 1].min(), corners[:, 0].max(), corners[:, 1].max())
    ref = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
    narrow, long = V.bbox_size_mm(view.H_px2cm, bbox, ref)
    assert abs(narrow - 30) < 2 and abs(long - 40) < 2


def test_tracker_end_to_end_finds_the_object_and_its_position(scene, monkeypatch):
    monkeypatch.setattr(V, "PARALLAX_CAM_HEIGHT_CM", 0.0)  # Vật giả lập vẽ phẳng trên giấy, không có phối cảnh theo độ cao
    tracker = V.ArucoYoloTracker(use_yolo=False)
    try:
        deadline = time.time() + 5
        while time.time() < deadline and not tracker.objects:
            out = tracker.process_frame(scene["top_object_frame"], "topdown")
            time.sleep(0.05)
        assert out.shape == scene["top_object_frame"].shape
        assert tracker.latest_view["topdown"].source == "aruco"
        assert tracker.objects, "bộ tách màu phải tìm thấy vật"
        obj = tracker.objects[0]
        assert abs(obj["x_cm"] - DISC_CM[0]) < 0.5 and abs(obj["y_cm"] - DISC_CM[1]) < 0.5 and obj["source"] == "color"
        # Cam ngang: chỉ ra khung có lớp phủ, không tìm vật
        for _ in range(3):
            side_out = tracker.process_frame(scene["side_frame"], "side")
        assert side_out.shape == scene["side_frame"].shape and tracker.latest_view["side"].source == "aruco"
        assert tracker.objects  # Khung cam NGANG không làm mất danh sách vật của cam TREN
        # Quên vật khi cam TREN mất tín hiệu, reset_sheet quên hết mã đã nhớ
        tracker.forget_objects()
        assert tracker.objects == []
        tracker.reset_sheet()
        assert not tracker.sheets["side"].memory
        assert tracker.process_frame(None, "side") is None
    finally:
        tracker.stop()


def test_perspective_strength_tells_overhead_from_oblique_views(scene):
    top = settle(V.SheetTracker(), scene["top_frame"])
    side = settle(V.SheetTracker(), scene["side_frame"])
    assert V.perspective_strength(top.H_cm2px) < 0.05
    assert V.perspective_strength(side.H_cm2px) > 0.25


# ----------------------------------------------------------------------------- từ phát hiện tới vật có vị trí
def top_view(scene):
    return settle(V.SheetTracker(), scene["top_object_frame"])


def test_find_objects_turns_a_colour_detection_into_a_position(scene, monkeypatch):
    monkeypatch.setattr(V, "PARALLAX_CAM_HEIGHT_CM", 0.0)
    view = top_view(scene)
    dets = V.detect_color_objects(scene["top_object_frame"], view.H_px2cm, view.H_cm2px)
    objects = V.find_objects(view.corners, view.ids, dets, view.H_px2cm, scene["top_object_frame"].shape, raw_img=scene["top_object_frame"])
    assert len(objects) == 1
    obj = objects[0]
    assert (obj["name"], obj["source"]) == ("Vat mau", "color")
    assert abs(obj["x_cm"] - DISC_CM[0]) < 0.5 and abs(obj["y_cm"] - DISC_CM[1]) < 0.5


def test_parallax_correction_pulls_the_measured_point_towards_the_camera_axis():
    # Đo thật 2026-11-02: cam TREN thấy tâm nắp cốc (cao 5 cm) ở (20.6, 6.8), nadir (14.82, 14.56), đáy cốc thật ở khoảng (20.0, 7.8)
    x, y = V.correct_parallax((20.6, 6.8), (14.82, 14.56), 5.0, cam_height_cm=46.0)
    assert (x, y) == pytest.approx((19.97, 7.64), abs=0.02) and np.hypot(x - 20.0, y - 7.84) < 0.3
    # Vật nằm đúng dưới camera, hoặc thấp sát giấy, hoặc không hiệu chỉnh (H = 0): giữ nguyên
    assert V.correct_parallax((14.82, 14.56), (14.82, 14.56), 5.0, 46.0) == pytest.approx((14.82, 14.56))
    assert V.correct_parallax((20.6, 6.8), (14.82, 14.56), 0.0, 46.0) == (20.6, 6.8)
    assert V.correct_parallax((20.6, 6.8), (14.82, 14.56), 5.0, 0.0) == (20.6, 6.8)
    # Vật càng cao thì kéo càng nhiều
    near, far = V.correct_parallax((20.0, 5.0), (15.0, 15.0), 2.0, 46.0), V.correct_parallax((20.0, 5.0), (15.0, 15.0), 8.0, 46.0)
    assert np.hypot(near[0] - 20.0, near[1] - 5.0) < np.hypot(far[0] - 20.0, far[1] - 5.0)


def test_find_objects_applies_the_parallax_correction_about_the_image_centre():
    raw = np.zeros((200, 400, 3), np.uint8)
    cv2.circle(raw, (300, 50), 14, (40, 90, 235), -1)
    ident = np.eye(3, dtype=np.float64)  # 1 px = 1 cm: nadir = tâm ảnh = (200, 100)
    det = {"ref_pt": (300, 50), "cls": "vat mau", "source": "color", "conf": 0.6, "size_mm": (30.0, 30.0)}
    obj = V.find_objects([], None, [det], ident, raw.shape, raw_img=raw)[0]
    k = (V.PARALLAX_CAM_HEIGHT_CM - obj["h_mm"] / 10.0) / V.PARALLAX_CAM_HEIGHT_CM
    assert (obj["x_cm"], obj["y_cm"]) == pytest.approx((200 + 100 * k, 100 - 50 * k), abs=1e-3)


def test_colorful_check_separates_the_cup_from_black_servo_parts_and_paper():
    img = np.zeros((120, 120, 3), np.uint8)
    cv2.circle(img, (30, 30), 12, (40, 90, 235), -1)            # Cốc đỏ cam
    cv2.rectangle(img, (60, 20), (100, 50), (25, 25, 25), -1)    # Thân servo đen
    cv2.rectangle(img, (10, 70), (50, 110), (235, 235, 235), -1)  # Giấy trắng
    cv2.rectangle(img, (70, 70), (110, 110), (130, 130, 130), -1)  # Kim loại xám
    assert V.is_colorful(img, (30, 30)) and not V.is_colorful(img, (80, 35)) and not V.is_colorful(img, (30, 90)) and not V.is_colorful(img, (90, 90))
    assert not V.is_colorful(img, (-5, 10)) and not V.is_colorful(img, (500, 10))


def test_yolo_objects_must_be_coloured_but_colour_blobs_always_pass():
    raw = np.zeros((200, 200, 3), np.uint8)
    cv2.circle(raw, (150, 50), 14, (40, 90, 235), -1)  # Nắp cốc
    ident = np.eye(3, dtype=np.float64)
    dets = [
        {"ref_pt": (50, 50), "cls": "traffic light", "source": "yolo", "conf": 0.5},  # Thân servo kẹp (đen): YOLO hay gọi sai như vậy
        {"ref_pt": (150, 50), "cls": "frisbee", "source": "yolo", "conf": 0.5},
        {"ref_pt": (100, 150), "cls": "vat mau", "source": "color", "conf": 0.6, "size_mm": (30.0, 30.0)},
    ]
    names = sorted(o["name"] for o in V.find_objects([], None, dets, ident, raw.shape, raw_img=raw))
    assert names == ["Vat mau", "YOLO:frisbee"]


def test_object_with_an_aruco_tag_is_found_and_not_duplicated(scene):
    ident = np.eye(3, dtype=np.float64)
    corners = [np.float32([[[90, 90], [110, 90], [110, 110], [90, 110]]])]
    ids = np.array([[12]])
    det = {"ref_pt": (100, 100), "cls": "vat mau", "source": "color", "conf": 0.6, "size_mm": (30.0, 30.0)}  # Cùng vật: không lặp lại
    objects = V.find_objects(corners, ids, [det], ident, (200, 200, 3))
    assert len(objects) == 1 and objects[0]["source"] == "aruco" and "Hop_Do_ID12" in objects[0]["name"]
    assert objects[0]["w_mm"] == V.OBJECT_SPECS[12]["w_mm"]
