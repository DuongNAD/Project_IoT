"""Generate guide screen sample image using real code from test_ik and guide_screen."""
import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import cv2
import numpy as np

# Ensure slides/assets directory exists
ASSETS_DIR = os.path.join(PROJECT_ROOT, "slides", "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

from test_ik import fake_assist
from guide_screen import build_guide_screen
import grasp_assist_4dof as ga


def generate_guide_screen_asset(output_path=None):
    if output_path is None:
        output_path = os.path.join(ASSETS_DIR, "guide_screen_sample.png")

    print(f"Generating guide screen sample image: {output_path}...")
    with fake_assist() as assist:
        # 1. Thêm vật thể mẫu trên tờ A4 (tọa độ cm)
        assist.objects = [{
            "name": "Hop_Xanh_ID11",
            "x_cm": 15.0,
            "y_cm": 8.0,
            "w_mm": 35.0,
            "h_mm": 35.0,
            "px": (640, 480),
            "source": "aruco",
        }]
        assist.target_history_cm.append((15.0, 8.0))
        assist.stage = 1  # Bước 2: Hạ xuống điểm kẹp
        info = assist.compute_current_suggestion()

        # 2. Tạo hình ảnh 2 camera
        # Cam phải (Top-down): Dùng ảnh lưới ArUco A4 thật có sẵn trong workspace
        grid_path = os.path.join(PROJECT_ROOT, "aruco_A4_grid.png")
        grid_img = cv2.imread(grid_path)
        if grid_img is None:
            grid_img = np.full((400, 640, 3), (240, 240, 240), dtype=np.uint8)

        # Cam trái (Side): Khung nền tối mô phỏng webcam nhìn ngang với vạch bàn và vạch nâng S1
        side_img = np.zeros((400, 640, 3), dtype=np.uint8)
        # Vạch bàn: SIDE_TABLE_Y_RATIO = 0.54 -> y = 400 * 0.54 = 216
        y_table = int(round(400 * ga.SIDE_TABLE_Y_RATIO))
        cv2.line(side_img, (0, y_table), (640, y_table), (40, 185, 255), 2)
        cv2.putText(side_img, "MAT BAN (SIDE_TABLE_Y_RATIO = 0.54)", (20, y_table + 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (165, 160, 155), 1)

        # Vạch nâng: SIDE_LIFT_RATIO = 0.065 -> y = 216 - 400 * 0.065 = 190
        y_lift = int(round(y_table - 400 * ga.SIDE_LIFT_RATIO))
        cv2.line(side_img, (0, y_lift), (640, y_lift), (110, 215, 90), 1)
        cv2.putText(side_img, "NGUONG NANG +20mm (S1)", (20, y_lift - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (110, 215, 90), 1)
        cv2.putText(side_img, "WEBCAM LAPTOP (NHIN NGANG)", (20, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (245, 245, 245), 1)

        # 3. Tạo màn hình hướng dẫn và lưu vào slides/assets/
        screen = build_guide_screen(side_img, grid_img, info)
        cv2.imwrite(output_path, screen)
        print(f"Generated {output_path} ({screen.shape[1]}x{screen.shape[0]}) successfully.")
        return output_path


if __name__ == "__main__":
    generate_guide_screen_asset()
