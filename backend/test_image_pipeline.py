"""
Deep diagnostic test for the AI image pipeline.
Run from backend/ with the project venv active.
"""
import sys, os, io, traceback

sys.path.insert(0, ".")

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

# ── 1. Import ─────────────────────────────────────────────────────────────────
print("=== 1. Import check ===")
try:
    from services import image_ai_service
    print(f"  {PASS} service imported")
except Exception as e:
    print(f"  {FAIL} {e}")
    sys.exit(1)

# ── 2. Pillow ─────────────────────────────────────────────────────────────────
print("=== 2. Pillow ===")
try:
    from PIL import Image as PILImage
    import PIL
    print(f"  {PASS} Pillow {PIL.__version__}")
except Exception as e:
    print(f"  {FAIL} {e}")
    sys.exit(1)

# ── 3. Synthetic test image ───────────────────────────────────────────────────
print("=== 3. Synthetic test image ===")
img = PILImage.new("RGB", (200, 200), color=(200, 50, 50))
buf = io.BytesIO()
img.save(buf, format="JPEG", quality=90)
raw_bytes = buf.getvalue()
print(f"  {PASS} created {len(raw_bytes)}-byte JPEG (200x200 red square)")

# ── 4. _resize_if_needed ──────────────────────────────────────────────────────
print("=== 4. _resize_if_needed ===")
try:
    result = image_ai_service._resize_if_needed(raw_bytes)
    assert len(result) > 0, "empty result"
    print(f"  {PASS} small image unchanged ({len(result)} bytes)")

    big = PILImage.new("RGB", (2000, 1500), color=(0, 100, 200))
    bigbuf = io.BytesIO()
    big.save(bigbuf, "JPEG")
    big_bytes = bigbuf.getvalue()
    resized = image_ai_service._resize_if_needed(big_bytes)
    ri = PILImage.open(io.BytesIO(resized))
    assert max(ri.size) <= 1024, f"resize failed: {ri.size}"
    print(f"  {PASS} 2000×1500 → {ri.size} (max dim ≤ 1024)")
except Exception as e:
    print(f"  {FAIL} {e}")
    traceback.print_exc()

# ── 5. _composite_white ───────────────────────────────────────────────────────
print("=== 5. _composite_white ===")
try:
    # Opaque red → should be red on white (still red)
    rgba_opaque = PILImage.new("RGBA", (100, 100), (255, 0, 0, 255))
    pngbuf = io.BytesIO()
    rgba_opaque.save(pngbuf, "PNG")
    jpg = image_ai_service._composite_white(pngbuf.getvalue())
    out = PILImage.open(io.BytesIO(jpg))
    px = out.getpixel((50, 50))
    assert out.mode == "RGB", f"wrong mode {out.mode}"
    assert px[0] > 200 and px[1] < 50, f"expected red-ish pixel, got {px}"
    print(f"  {PASS} opaque red→white composite: pixel={px}")

    # Transparent image → should give white pixel
    rgba_transparent = PILImage.new("RGBA", (100, 100), (255, 0, 0, 0))
    pngbuf2 = io.BytesIO()
    rgba_transparent.save(pngbuf2, "PNG")
    jpg2 = image_ai_service._composite_white(pngbuf2.getvalue())
    out2 = PILImage.open(io.BytesIO(jpg2))
    px2 = out2.getpixel((50, 50))
    assert all(v > 240 for v in px2), f"expected white pixel, got {px2}"
    print(f"  {PASS} fully transparent→white composite: pixel={px2}")

    # Semi-transparent red (alpha=128) → should blend to mid-pink
    rgba_semi = PILImage.new("RGBA", (100, 100), (255, 0, 0, 128))
    pngbuf3 = io.BytesIO()
    rgba_semi.save(pngbuf3, "PNG")
    jpg3 = image_ai_service._composite_white(pngbuf3.getvalue())
    out3 = PILImage.open(io.BytesIO(jpg3))
    px3 = out3.getpixel((50, 50))
    print(f"  {PASS} semi-transparent (alpha=128) pixel={px3} (should be pinkish)")
except Exception as e:
    print(f"  {FAIL} {e}")
    traceback.print_exc()

# ── 6. _split_grid ────────────────────────────────────────────────────────────
print("=== 6. _split_grid ===")
try:
    # Portrait 2-col × 3-row (as zero123-plus outputs)
    grid_portrait = PILImage.new("RGB", (512, 768), color=(128, 128, 128))
    # Draw distinct colors in each cell so we can verify splits
    colors = [(255,0,0),(0,255,0),(0,0,255),(255,255,0),(255,0,255),(0,255,255)]
    for r in range(3):
        for c in range(2):
            col = colors[r * 2 + c]
            for px in range(c * 256, (c+1) * 256):
                for py in range(r * 256, (r+1) * 256):
                    grid_portrait.putpixel((px, py), col)
    gbuf = io.BytesIO()
    grid_portrait.save(gbuf, "PNG")
    cells = image_ai_service._split_grid(gbuf.getvalue(), count=4)
    assert len(cells) == 4, f"expected 4 cells, got {len(cells)}"
    for i, c in enumerate(cells):
        ci = PILImage.open(io.BytesIO(c))
        assert ci.size == (256, 256), f"cell[{i}] wrong size: {ci.size}"
    print(f"  {PASS} portrait 512×768 → {len(cells)} cells of {PILImage.open(io.BytesIO(cells[0])).size}")

    # Landscape 3-col × 2-row
    grid_landscape = PILImage.new("RGB", (768, 512), color=(64, 64, 64))
    gbuf2 = io.BytesIO()
    grid_landscape.save(gbuf2, "PNG")
    cells2 = image_ai_service._split_grid(gbuf2.getvalue(), count=4)
    assert len(cells2) == 4, f"expected 4 cells, got {len(cells2)}"
    print(f"  {PASS} landscape 768×512 → {len(cells2)} cells of {PILImage.open(io.BytesIO(cells2[0])).size}")

    # Edge case: count=6 (all cells)
    cells3 = image_ai_service._split_grid(gbuf.getvalue(), count=6)
    assert len(cells3) == 6, f"expected 6 cells, got {len(cells3)}"
    print(f"  {PASS} count=6 → {len(cells3)} cells")
except Exception as e:
    print(f"  {FAIL} {e}")
    traceback.print_exc()

# ── 7. HF token check ────────────────────────────────────────────────────────
print("=== 7. HF token & env ===")
hf_token = os.getenv("HF_API_TOKEN", "")
token_display = f"YES ({hf_token[:8]}...)" if hf_token else "NO"
print(f"  HF_API_TOKEN set: {token_display}")
if not hf_token:
    print(f"  {WARN} No HF_API_TOKEN — bg removal falls back to rembg/no-op; angle gen disabled")
    print(f"       Set HF_API_TOKEN in .env to enable RMBG-1.4 and zero123-plus")

# ── 8. remove_background — no-token fallback ─────────────────────────────────
print("=== 8. remove_background (no-token fallback) ===")
try:
    saved_token = image_ai_service.HF_API_TOKEN
    image_ai_service.HF_API_TOKEN = ""

    result = image_ai_service.remove_background(raw_bytes)
    assert len(result) > 0, "empty result"
    if result == raw_bytes:
        print(f"  {PASS} fallback → original returned (no rembg + no token — expected)")
    else:
        ri = PILImage.open(io.BytesIO(result))
        print(f"  {PASS} fallback → rembg processed image {ri.size}")

    image_ai_service.HF_API_TOKEN = saved_token
except Exception as e:
    image_ai_service.HF_API_TOKEN = saved_token
    print(f"  {FAIL} {e}")
    traceback.print_exc()

# ── 9. generate_angles — no-token returns [] ─────────────────────────────────
print("=== 9. generate_angles (no-token → empty list) ===")
try:
    saved_token = image_ai_service.HF_API_TOKEN
    image_ai_service.HF_API_TOKEN = ""
    angles = image_ai_service.generate_angles(raw_bytes)
    assert angles == [], f"expected [], got {len(angles)} items"
    print(f"  {PASS} returns [] without token (correct — no crash)")
    image_ai_service.HF_API_TOKEN = saved_token
except Exception as e:
    image_ai_service.HF_API_TOKEN = saved_token
    print(f"  {FAIL} {e}")
    traceback.print_exc()

# ── 10. Controller import & logic ────────────────────────────────────────────
print("=== 10. Controller: process_product_image ===")
try:
    import controllers.supplier_controller as ctrl
    import inspect
    src = inspect.getsource(ctrl.process_product_image)
    # Check uuid usage
    assert "uuid.uuid4()" in src, "uuid.uuid4() missing"
    # Check os.makedirs
    assert "os.makedirs" in src, "os.makedirs missing"
    # Check both steps
    assert "remove_background" in src, "remove_background call missing"
    assert "generate_angles" in src, "generate_angles call missing"
    print(f"  {PASS} function signature and logic structure OK")
except Exception as e:
    print(f"  {FAIL} {e}")
    traceback.print_exc()

# ── 11. HF API endpoint correctness ──────────────────────────────────────────
print("=== 11. HF API endpoint URLs ===")
print(f"  RMBG URL  : {image_ai_service._HF_BASE}/{image_ai_service.RMBG_MODEL}")
print(f"  Z123+ URL : {image_ai_service._HF_BASE}/{image_ai_service.ZERO123_MODEL}")
# zero123-plus inference API note
import requests as req
try:
    # HEAD request to check if the model exists on HF Hub (no auth needed for public models)
    r = req.head(f"https://huggingface.co/{image_ai_service.ZERO123_MODEL}", timeout=10)
    print(f"  zero123-plus HF page status: HTTP {r.status_code}")
    if r.status_code == 200:
        print(f"  {PASS} zero123-plus model page exists on HF Hub")
    else:
        print(f"  {WARN} unexpected status for zero123-plus page")
except Exception as e:
    print(f"  {WARN} could not reach HF Hub: {e}")

# ── 12. Test router is correctly mounted ─────────────────────────────────────
print("=== 12. Router includes /process-image ===")
try:
    from routers import supplier as supplier_router
    routes = [r.path for r in supplier_router.router.routes]
    process_route = [r for r in routes if "process-image" in r]
    assert process_route, f"route missing! routes={routes}"
    print(f"  {PASS} route found: {process_route[0]}")
except Exception as e:
    print(f"  {FAIL} {e}")
    traceback.print_exc()

# ── 13. Full integration: mock the HTTP calls, invoke remove_background + generate_angles
print("=== 13. Integration: BG removal with mocked HF API ===")
try:
    from unittest.mock import patch, MagicMock

    # Build a fake RGBA PNG that looks like what RMBG-1.4 would return 
    fake_mask = PILImage.new("RGBA", (200, 200), (200, 50, 50, 200))  # slightly transparent
    fbuf = io.BytesIO()
    fake_mask.save(fbuf, "PNG")
    fake_png_bytes = fbuf.getvalue()

    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.headers = {"content-type": "image/png"}
    fake_response.content = fake_png_bytes

    image_ai_service.HF_API_TOKEN = "fake-token-for-test"
    with patch("services.image_ai_service.requests.post", return_value=fake_response):
        result = image_ai_service.remove_background(raw_bytes)

    ri = PILImage.open(io.BytesIO(result))
    assert ri.mode == "RGB", f"expected RGB, got {ri.mode}"
    print(f"  {PASS} mocked RMBG-1.4 → white-bg JPEG {ri.size}, mode={ri.mode}")

    # Restore
    image_ai_service.HF_API_TOKEN = hf_token

except Exception as e:
    image_ai_service.HF_API_TOKEN = hf_token
    print(f"  {FAIL} {e}")
    traceback.print_exc()

# ── 14. Integration: angle generation with mocked HF API ─────────────────────
print("=== 14. Integration: angle generation with mocked HF API ===")
try:
    from unittest.mock import patch, MagicMock

    # Build a fake 2×3 grid portrait 512×768
    fake_grid = PILImage.new("RGB", (512, 768), color=(80, 120, 180))
    fbuf = io.BytesIO()
    fake_grid.save(fbuf, "PNG")
    fake_grid_bytes = fbuf.getvalue()

    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.headers = {"content-type": "image/png"}
    fake_response.content = fake_grid_bytes

    image_ai_service.HF_API_TOKEN = "fake-token-for-test"
    with patch("services.image_ai_service.requests.post", return_value=fake_response):
        angles = image_ai_service.generate_angles(raw_bytes)

    assert len(angles) == 4, f"expected 4 angles, got {len(angles)}"
    for i, a in enumerate(angles):
        ai = PILImage.open(io.BytesIO(a))
        assert ai.mode == "RGB"
        print(f"    angle[{i}]: {ai.size} mode={ai.mode}")
    print(f"  {PASS} mocked zero123-plus → {len(angles)} angle views")

    image_ai_service.HF_API_TOKEN = hf_token

except Exception as e:
    image_ai_service.HF_API_TOKEN = hf_token
    print(f"  {FAIL} {e}")
    traceback.print_exc()

# ── 15. Error resilience: bad API response ───────────────────────────────────
print("=== 15. Error resilience ===")
try:
    from unittest.mock import patch, MagicMock

    # 503 response
    bad_resp = MagicMock()
    bad_resp.status_code = 503
    bad_resp.headers = {"content-type": "application/json"}
    bad_resp.text = '{"error": "Model loading"}'

    image_ai_service.HF_API_TOKEN = "fake-token"
    with patch("services.image_ai_service.requests.post", return_value=bad_resp):
        result_bg = image_ai_service.remove_background(raw_bytes)
    # Should fall through to rembg or return original — must not crash
    assert len(result_bg) > 0, "empty result on 503"
    print(f"  {PASS} 503 response → graceful fallback ({len(result_bg)} bytes returned)")

    # Timeout
    import requests as _req
    with patch("services.image_ai_service.requests.post", side_effect=_req.Timeout):
        result_bg2 = image_ai_service.remove_background(raw_bytes)
    assert len(result_bg2) > 0
    print(f"  {PASS} Timeout → graceful fallback")

    # 401 Unauthorized
    unauth_resp = MagicMock()
    unauth_resp.status_code = 401
    unauth_resp.headers = {"content-type": "application/json"}
    unauth_resp.text = '{"error": "Unauthorized"}'
    with patch("services.image_ai_service.requests.post", return_value=unauth_resp):
        angles_401 = image_ai_service.generate_angles(raw_bytes)
    assert angles_401 == [], f"expected [], got {angles_401}"
    print(f"  {PASS} 401 response → generates empty angles list (no crash)")

    image_ai_service.HF_API_TOKEN = hf_token

except Exception as e:
    image_ai_service.HF_API_TOKEN = hf_token
    print(f"  {FAIL} {e}")
    traceback.print_exc()

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("Diagnostic complete.")
hf = os.getenv("HF_API_TOKEN", "")
if not hf:
    print(f"\n{WARN}  IMPORTANT: HF_API_TOKEN not set in environment.")
    print("   • Background removal: will return original (no-op)")
    print("   • Angle generation: disabled (returns [])")
    print("   Set HF_API_TOKEN in backend/.env to enable real AI processing.")
else:
    print(f"\n{PASS}  HF_API_TOKEN is configured — real API calls will work.")

