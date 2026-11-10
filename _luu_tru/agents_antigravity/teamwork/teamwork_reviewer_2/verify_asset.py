import hashlib
import os
import sys

# Add project root to sys.path
PROJECT_ROOT = r"e:\03_Development_Projects\project\Project_IoT"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from slides.generate_asset import generate_guide_screen_asset

tmp_path = os.path.join(r"e:\03_Development_Projects\project\Project_IoT\.agents\teamwork\teamwork_reviewer_2", "temp_asset.png")
generate_guide_screen_asset(tmp_path)
with open(tmp_path, "rb") as f:
    h = hashlib.sha256(f.read()).hexdigest()
print("Regenerated asset SHA256:", h)

orig_path = os.path.join(PROJECT_ROOT, "slides", "assets", "guide_screen_sample.png")
with open(orig_path, "rb") as f:
    orig = hashlib.sha256(f.read()).hexdigest()
print("Original asset SHA256:    ", orig)
print("Matches exactly:", h == orig)
if os.path.exists(tmp_path):
    os.remove(tmp_path)
