"""Live end-to-end test: remove background and generate 4 angle views with rembg installed."""
import sys, os, io
sys.path.insert(0, ".")
os.environ.setdefault("HF_API_TOKEN", "")

from PIL import Image as PILImage
from services import image_ai_service

# Build a minimal test JPEG - gradient so it has real content
img = PILImage.new("RGB", (300, 300))
for x in range(300):
    for y in range(300):
        img.putpixel((x, y), (x * 255 // 300, y * 255 // 300, 100))
# Draw a colored rectangle in center (simulates a product)
for x in range(80, 220):
    for y in range(60, 240):
        img.putpixel((x, y), (200, 80, 40))

buf = io.BytesIO()
img.save(buf, "JPEG", quality=90)
original = buf.getvalue()
print(f"Input: {len(original)} bytes, 300x300 JPEG")

# Step 1: Background removal
print("\n--- Step 1: remove_background ---")
result_bg = image_ai_service.remove_background(original)
print(f"Output: {len(result_bg)} bytes")
ri = PILImage.open(io.BytesIO(result_bg))
print(f"  mode={ri.mode}, size={ri.size}, format={ri.format}")
same = result_bg == original
print(f"  Changed from original: {not same}")
if not same:
    print(f"  SUCCESS: background removal modified the image")
else:
    print(f"  WARN: image unchanged (rembg may not have run)")

# Save outputs for visual inspection
os.makedirs("test_outputs", exist_ok=True)
with open("test_outputs/bg_removed.jpg", "wb") as f:
    f.write(result_bg)
print(f"  Saved: test_outputs/bg_removed.jpg")

# Step 2: Generate 4 angle views
print("\n--- Step 2: generate_angles ---")
angles = image_ai_service.generate_angles(result_bg)
print(f"Generated {len(angles)} angles")
for i, a in enumerate(angles):
    ai_img = PILImage.open(io.BytesIO(a))
    print(f"  angle[{i}]: {ai_img.size}, mode={ai_img.mode}, {len(a)} bytes")
    with open(f"test_outputs/angle_{i}.jpg", "wb") as f:
        f.write(a)
    print(f"  Saved: test_outputs/angle_{i}.jpg")

print(f"\nAll outputs in backend/test_outputs/")
print("RESULT: Pipeline WORKS" if len(angles) == 4 else "RESULT: FAIL - expected 4 angles")

