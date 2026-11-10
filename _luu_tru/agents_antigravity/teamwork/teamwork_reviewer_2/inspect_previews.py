"""Inspect PNG preview files for resolution, aspect ratio, file size."""
import os
import sys
from PIL import Image

preview_dir = r"e:\03_Development_Projects\project\Project_IoT\slides\preview"

print("=" * 80)
print("PNG PREVIEW FILES INSPECTION")
print("=" * 80)

for i in range(1, 16):
    fname = f"slide_{i:02d}.png"
    fpath = os.path.join(preview_dir, fname)
    if not os.path.exists(fpath):
        print(f"ERROR: {fname} MISSING!")
        continue
    sz_bytes = os.path.getsize(fpath)
    with Image.open(fpath) as im:
        w, h = im.size
        aspect = w / h
        mode = im.mode
    print(f"{fname}: {w}x{h} px ({sz_bytes:,} bytes, mode={mode}, aspect={aspect:.4f} vs 16/9={16/9:.4f})")
    assert abs(aspect - 16/9) < 0.01, f"{fname} aspect ratio mismatch!"
    assert w >= 1920, f"{fname} resolution too low!"
