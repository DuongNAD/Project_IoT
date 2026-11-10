"""Dò tờ A4 qua mã ArUco, tìm vật có màu (và loại tay người, dây điện, thân robot), bù thị sai: trên cảnh tổng hợp có đáp án."""

import cv2
import pytest
from synth import PPC, cm_to_texture_px, corner_error_px, draw_disc, occlude_markers, render, sheet_texture, side_camera, top_camera

import vision as V

DISC_CM = (20.0, 12.0)  # Tâm vật màu trên tờ giấy (cm)


@pytest.fixture(scope="module")
def scene():
    top, side = top_camera(), side_camera()
    return {
        "top": top,
        "side": side,
        "top_frame": render(top, sheet_texture()),
        "side_frame": render(side, sheet_texture()),
        "top_object_frame": render(top, sheet_texture(lambda img: draw_disc(img, *DISC_CM, 2.2))),
    }


def sheet_of(frame):
    sheet = V.Sheet()
    sheet.update(frame)
    return sheet


def objects_in(scene, draw):
    frame = render(scene["top"], sheet_texture(draw))
    return V.find_objects(frame, sheet_of(frame))


def test_marker_corners_match_the_printed_sheet():
    assert V.marker_corners_cm(0)[0].tolist() == pytest.approx([0.25, 0.25])  # Góc ngoài mã ID 0
    assert V.marker_corners_cm(2)[2].tolist() == pytest.approx([29.45, 20.75])  # Góc ngoài mã ID 2


def test_homography_for_both_cameras(scene):
    for tag in ("top", "side"):
        sheet = sheet_of(scene[f"{tag}_frame"])
        assert sheet.n_seen == 4 and corner_error_px(sheet, scene[tag]) < 1.5, f"cam {tag} lệch lưới"
        cx, cy = V.px_to_cm(sheet.H_px2cm, *scene[tag].project(14.85, 10.5))  # Tâm tờ giấy
        assert abs(cx - 14.85) < 0.1 and abs(cy - 10.5) < 0.1


def test_markers_hidden_by_the_arm_are_remembered(scene):
    sheet = sheet_of(scene["side_frame"])
    sheet.update(occlude_markers(scene["side_frame"], scene["side"], (0, 1, 2)))  # Cánh tay che 3 mã
    assert sheet.n_seen == 1 and len(sheet.markers) == 4
    assert corner_error_px(sheet, scene["side"]) < 1.5
    fresh = sheet_of(occlude_markers(scene["side_frame"], scene["side"], (0, 1, 2)))  # Chưa từng thấy đủ: 1 mã không tính được lưới
    assert fresh.H_px2cm is None


def test_the_coloured_disc_is_found_at_its_position(scene, monkeypatch):
    monkeypatch.setattr(V, "CAM_HEIGHT_CM", 0.0)  # Đĩa vẽ phẳng trên giấy: không có thị sai để bù
    found = V.find_objects(scene["top_object_frame"], sheet_of(scene["top_object_frame"]))
    assert len(found) == 1
    assert abs(found[0]["x_cm"] - DISC_CM[0]) < 0.4 and abs(found[0]["y_cm"] - DISC_CM[1]) < 0.4


def test_parallax_correction_pulls_the_object_towards_the_image_centre(scene):
    frame = scene["top_object_frame"]
    sheet = sheet_of(frame)
    obj = V.find_objects(frame, sheet)[0]
    nadir = V.px_to_cm(sheet.H_px2cm, frame.shape[1] / 2, frame.shape[0] / 2)
    k = (V.CAM_HEIGHT_CM - V.OBJECT_HEIGHT_CM) / V.CAM_HEIGHT_CM  # 46 cm, cốc 5 cm: kéo vào 11%
    for j in (0, 1):
        assert obj[("x_cm", "y_cm")[j]] == pytest.approx(nadir[j] + (DISC_CM[j] - nadir[j]) * k, abs=0.4)


def test_wires_and_parts_of_the_black_arm_are_not_objects(scene):
    def arm_and_wires(img):
        cv2.line(img, (300, 300), (700, 340), (40, 90, 235), 3, cv2.LINE_AA)   # Dây điện cam mảnh
        cv2.rectangle(img, (800, 440), (1120, 660), (15, 15, 15), -1)         # Thân robot đen
        cv2.rectangle(img, (900, 500), (1000, 600), (235, 120, 40), -1)       # Nhãn servo nằm giữa phần đen

    assert objects_in(scene, arm_and_wires) == []

    def object_between_the_jaws(img):  # Vật chỉ chạm một cạnh vào phần đen (cốc giữa hai ngón kẹp) vẫn được nhận
        cv2.rectangle(img, (800, 500), (900, 600), (235, 120, 40), -1)
        cv2.rectangle(img, (900, 480), (1100, 620), (15, 15, 15), -1)

    assert len(objects_in(scene, object_between_the_jaws)) == 1


def test_hands_and_blobs_too_big_to_grasp_are_not_objects(scene):
    skin = (110, 140, 225)  # BGR màu da: đủ bão hòa để lọt ngưỡng tách màu

    def hand_from_the_right_edge(img):
        cv2.rectangle(img, cm_to_texture_px(22, 8), cm_to_texture_px(29.7, 15), skin, -1)
        cv2.ellipse(img, cm_to_texture_px(18, 11.5), (int(5 * PPC), int(4.5 * PPC)), 0, 0, 360, skin, -1)

    def palm_inside_the_sheet(img):  # 14 x 10 cm
        cv2.ellipse(img, cm_to_texture_px(14.85, 10.5), (int(7 * PPC), int(5 * PPC)), 0, 0, 360, skin, -1)

    def cup_and_box(img):
        draw_disc(img, 8.0, 5.0, 3.2)  # Cốc rộng 64 mm
        cv2.rectangle(img, cm_to_texture_px(20, 14), cm_to_texture_px(26, 17), (40, 90, 235), -1)  # Hộp 6 x 3 cm

    assert objects_in(scene, hand_from_the_right_edge) == []
    assert objects_in(scene, palm_inside_the_sheet) == []
    assert len(objects_in(scene, cup_and_box)) == 2, "vật vừa miệng kẹp vẫn phải được nhận"


def test_vision_draws_both_views_and_keeps_the_top_objects(scene):
    vision = V.Vision()
    out = vision.process_frame(scene["top_object_frame"], "topdown")
    assert out.shape == scene["top_object_frame"].shape and len(vision.objects) == 1
    side = vision.process_frame(scene["side_frame"], "side")
    assert side.shape == scene["side_frame"].shape and vision.sheets["side"].H_px2cm is not None
    assert len(vision.objects) == 1  # Khung cam NGANG không xóa danh sách vật của cam TREN
    vision.reset_sheet()  # Phím U
    assert not vision.sheets["side"].markers and vision.sheets["side"].H_px2cm is None
    assert vision.process_frame(None, "side") is None
    blank = vision.process_frame(occlude_markers(scene["top_object_frame"], scene["top"], (0, 1, 2, 3)), "topdown")
    assert blank is not None and vision.objects == []  # Không thấy tờ giấy: không đoán vị trí vật
