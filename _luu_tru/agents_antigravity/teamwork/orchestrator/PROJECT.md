# Project: 4-DOF Robot Arm Grasp Assist Technical Slides

## Architecture
- Modules investigated:
  - `main.py`: Camera feeds, ArUco detection (DICT_4X4_50 ID 0-3, 4, 5-6, 10-29), Homography, `ArucoYoloTracker`, background YOLO thread, keyboard shortcuts.
  - `grasp_assist_4dof.py`: `ARM_CONFIG`, `SERVO_LIMITS`, FK/IK analytical solver (elbow-up), coordinate transformations (table A4 cm -> robot mm), `ArduinoSerialLink`, stage machine (5 steps), logging.
  - `guide_screen.py`: "HƯỚNG DẪN GẮP" HUD & side-by-side guide window, color palette, keycaps, instruction rendering.
  - `robot_arm_4dof/robot_arm_4dof.ino`: Arduino firmware, PCA9685 I2C 0x40 50Hz, HC-05 9600, key controls, state JSON.
  - `test_ik.py`: IK/FK test suite & `fake_assist()`.
  - `generate_aruco_a4.py`, `aruco_A4_grid.png`: A4 ArUco pattern.
- Target Output:
  - `slides/build_slides.py`: `python-pptx` automated presentation generator.
  - `slides/assets/`: Generated UI screenshots and diagram assets (NO AI images).
  - `slides/Project_IoT_ThuyetTrinh.pptx`: 15-slide technical presentation (16:9, dark theme).
  - `slides/Project_IoT_ThuyetTrinh.pdf`: Headless PowerPoint COM PDF export.
  - `slides/preview/`: 15 PNG preview exports (2000x1125 px) for visual QA.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Slide 1: Tiêu đề | Project title, group, advisor, course, date | M1, M2 | R1.1 |
| 2 | Slide 2: Bài toán & Mục tiêu | Vision-based assistance, joint angle calc, key guide, auto-confirm | M1, M2 | R1.2 |
| 3 | Slide 3: Phần cứng | Arduino, PCA9685 0x40 50Hz, 4x MG996R, HC-05 D2/D3 9600, 5-6V, Mac M5 MPS, 2 cameras | M1, M2 | R1.3 |
| 4 | Slide 4: Kiến trúc phần mềm | Block diagram: 2 cameras -> Tracker -> Homography -> GraspAssist -> Arduino -> Firmware -> Servos | M1, M2 | R1.4 |
| 5 | Slide 5: Hệ tọa độ & ArUco | A4 grid 29.7x21cm, DICT_4X4_50 ID 0-3, 4, 5-6, 10-29, homography px->cm, LAB fallback | M1, M2 | R1.5 |
| 6 | Slide 6: Nhận diện vật | YOLO11s background thread, ArUco fusion (<2.5cm dedup), proximity sorting, 10-frame SMA | M1, M2 | R1.6 |
| 7 | Slide 7: Động học thuận/ngược | ARM_CONFIG d1, L2, L3, L4_r, L4_z, elbow-up analytical IK, servo mapping (90°->45°,-45°), 5° step, limits | M1, M2 | R1.7 |
| 8 | Slide 8: Chuyển đổi tọa độ A4->Robot | base_x_cm, base_y_cm, robot_faces, axis inversions, reachability warning | M1, M2 | R1.8 |
| 9 | Slide 9: Quy trình gắp 5 bước | Hover +60mm -> Lower -> Grasp -> Lift +80mm -> Verify; Keys A/D, W/S, I/K, J/L, H; Base->Grip->Shoulder->Elbow; P auto | M1, M2 | R1.9 |
| 10 | Slide 10: Tự xác nhận 2 camera | S1 side cam >+20mm (excl ID 6); S2 top cam empty r=3cm; 30 frames >=80%; 3s timeout slips/drops; attempts.csv | M1, M2 | R1.10 |
| 11 | Slide 11: Giao tiếp Arduino | USB 9600 baud, JSON {"servo":[...]} 5Hz, HC-05 fallback, timeout 2s, simulation mode | M1, M2 | R1.11 |
| 12 | Slide 12: Giao diện người dùng | Real screenshot from code (fake_assist + build_guide_screen), shortcut cheat sheet | M1, M2 | R1.12 |
| 13 | Slide 13: Kết quả kiểm thử | Real test_ik.py execution results, attempts.csv stats (or [...] if none) | M1, M2 | R1.13 |
| 14 | Slide 14: Hạn chế & Hướng phát triển | Manual calibration SIDE_TABLE_Y_RATIO, base estimation ±1-2cm, 5° open-loop; solvePnP, ID 5 closed-loop | M1, M2 | R1.14 |
| 15 | Slide 15: Demo & Kết luận | 3 key takeaways, Q&A | M1, M2 | R1.15 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Survey & Implementation Plan | Full codebase inspection, running test_ik.py, extracting all exact constants/formulas/keys, detailed 15-slide plan | none | DONE |
| M2 | Python Slide Generator & Assets | slides/build_slides.py using python-pptx, dark theme styling, keycaps, native PowerPoint shapes, real UI asset generation | M1 | DONE |
| M3 | Visual QA & Preview Generation | PowerPoint COM PDF conversion, PyMuPDF PNG rendering, visual defect fixes | M2 | DONE |
| M4 | Final Review & Walkthrough | Review, adversarial verification, forensic audit, final walkthrough report | M3 | DONE |

## Code Layout
- Only write/modify in `slides/` and `.agents/teamwork/`
- Target outputs:
  - `slides/build_slides.py`
  - `slides/assets/`
  - `slides/Project_IoT_ThuyetTrinh.pptx`
  - `slides/Project_IoT_ThuyetTrinh.pdf`
  - `slides/preview/`
