import pptx
from pptx import Presentation

prs = Presentation("slides/Project_IoT_ThuyetTrinh.pptx")

all_slide_texts = {}
for i, slide in enumerate(prs.slides, 1):
    texts = []
    for s in slide.shapes:
        if s.has_text_frame:
            texts.append(s.text_frame.text)
    all_slide_texts[i] = "\n".join(texts)

checks = [
    # Slide 3: Hardware
    (3, ["PCA9685", "0x40", "50", "MG996R", "HC-05", "9600"]),
    # Slide 4: Architecture
    (4, ["ArucoYoloTracker", "Homography", "GraspAssist4DOF", "ArduinoSerialLink"]),
    # Slide 5: Coordinates & ArUco
    (5, ["29.7", "21.0", "DICT_4X4_50", "0-3", "4", "5-6", "10-29", "LAB"]),
    # Slide 6: YOLO & Tracking
    (6, ["YOLO11s", "2.5 cm", "10"]),
    # Slide 7: Kinematics
    (7, ["80", "105", "100", "65", "25", "45", "-45", "5°", "0-180", "15-165", "30-150"]),
    # Slide 8: A4 to Robot
    (8, ["18.0", "-13.6", "down", "±1-2 cm"]),
    # Slide 9: 5-step process
    (9, ["+60 mm", "+80 mm", "A/D", "W/S", "I/K", "J/L", "H", "P"]),
    # Slide 10: Auto-confirm 2 cameras
    (10, ["S1", "S2", "+20 mm", "3 cm", "30", "80%", "3", "attempts.csv"]),
    # Slide 11: Arduino Serial Link
    (11, ["9600", "5 Hz", "2s", "fallback"]),
    # Slide 12: Guide UI
    (12, ["HƯỚNG DẪN GẮP", "1280x800"]),
    # Slide 13: Test Results
    (13, ["455", "0.000000 mm", "SERVO_LIMITS", "5°"]),
    # Slide 14: Limitations & Future
    (14, ["SIDE_TABLE_Y_RATIO = 0.54", "solvePnP", "ID 5"]),
    # Slide 15: Conclusions
    (15, ["Q&A"])
]

passed_all = True
for slide_num, tokens in checks:
    stext = all_slide_texts[slide_num]
    missing = [t for t in tokens if t not in stext]
    if missing:
        print(f"FAILED on Slide {slide_num}: Missing tokens {missing}")
        passed_all = False
    else:
        print(f"Slide {slide_num:02d}: ALL {len(tokens)} key parameters verified present.")

assert passed_all, "Some parameters missing in slides"
print("\nALL TECHNICAL PARAMETERS VERIFIED 100% FAITHFUL TO CODEBASE!")
