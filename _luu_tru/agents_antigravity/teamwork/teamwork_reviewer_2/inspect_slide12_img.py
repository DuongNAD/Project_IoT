"""Verify Slide 12 image embedding and asset authenticity."""
import os
import sys
import hashlib
from PIL import Image

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import pptx
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

pptx_path = r"e:\03_Development_Projects\project\Project_IoT\slides\Project_IoT_ThuyetTrinh.pptx"
prs = Presentation(pptx_path)

slide12 = prs.slides[11] # 0-indexed
img_shape = None
for s in slide12.shapes:
    if s.shape_type == MSO_SHAPE_TYPE.PICTURE:
        img_shape = s
        break

print(f"Slide 12 has picture shape: {img_shape is not None}")
if img_shape:
    print(f"Picture shape name: {img_shape.name}")
    print(f"Picture position: left={img_shape.left.inches:.3f}in, top={img_shape.top.inches:.3f}in")
    print(f"Picture size in slide: width={img_shape.width.inches:.3f}in, height={img_shape.height.inches:.3f}in")
    img_bytes = img_shape.image.blob
    img_hash = hashlib.sha256(img_bytes).hexdigest()
    print(f"Embedded image SHA256: {img_hash}")
    print(f"Embedded image format: {img_shape.image.ext}")

asset_path = r"e:\03_Development_Projects\project\Project_IoT\slides\assets\guide_screen_sample.png"
if os.path.exists(asset_path):
    with open(asset_path, "rb") as f:
        disk_bytes = f.read()
    disk_hash = hashlib.sha256(disk_bytes).hexdigest()
    print(f"Disk asset SHA256:     {disk_hash}")
    print(f"Hashes match: {img_hash == disk_hash}")
    
    with Image.open(asset_path) as im:
        print(f"Disk image resolution: {im.size} (width x height)")
        print(f"Disk image format: {im.format}")
