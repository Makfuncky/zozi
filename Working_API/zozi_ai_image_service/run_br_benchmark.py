import io
import os
import sys
import time
import shutil
from pathlib import Path
from PIL import Image
import numpy as np
from unittest.mock import patch, MagicMock

WORKSPACE = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi")
INPUT_FOLDER = WORKSPACE / "image"
LOCAL_SERVICE = WORKSPACE / "Working_API" / "zozi_ai_image_service"
LOCAL_IMAGE = LOCAL_SERVICE / "image"
OUTPUT_BASE = LOCAL_SERVICE

ALL_IMAGES = sorted([p for p in INPUT_FOLDER.iterdir() if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}])


def ensure_local_images():
    LOCAL_IMAGE.mkdir(parents=True, exist_ok=True)
    copied = []
    for src in ALL_IMAGES:
        dst = LOCAL_IMAGE / src.name
        shutil.copy2(src, dst)
        copied.append(dst)
    return copied


def cleanup_local_images(copied):
    for p in copied:
        try:
            p.unlink()
        except Exception:
            pass


def make_fake_rgba_png(width, height):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    arr = np.array(img)
    y, x = np.ogrid[:height, :width]
    cx, cy = width // 2, height // 2
    rx, ry = int(width * 0.35), int(height * 0.35)
    mask = ((x - cx) ** 2 / rx**2 + (y - cy) ** 2 / ry**2) <= 1
    arr[mask, 3] = 255
    arr[mask, 0] = 200
    arr[mask, 1] = 180
    arr[mask, 2] = 160
    buf = io.BytesIO()
    Image.fromarray(arr, mode="RGBA").save(buf, "PNG")
    return buf.getvalue()


def mock_remove(*args, **kwargs):
    image_bytes = args[0] if args else kwargs.get("image_bytes")
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    return make_fake_rgba_png(img.width, img.height)


def mock_new_session(model_name: str):
    return MagicMock()


def analyze_output(path):
    try:
        with Image.open(path) as img:
            arr = np.array(img)
            has_alpha = img.mode in ("RGBA", "P") or img.mode.endswith("A")
            alpha = arr[:, :, 3] if has_alpha and arr.shape[2] == 4 else None
            if alpha is not None:
                opaque = int(np.sum(alpha > 128))
                total = alpha.size
                coverage = opaque / total if total else 0
            else:
                coverage = 1.0
            return {
                "size": img.size,
                "mode": img.mode,
                "coverage": coverage,
            }
    except Exception as e:
        return {"error": str(e)}


def test_br_05(image_path):
    sys.path.insert(0, str(LOCAL_SERVICE))
    import br_05
    out_path = str(OUTPUT_BASE / "output_br_05" / f"{Path(image_path).stem}_05.png")
    (OUTPUT_BASE / "output_br_05").mkdir(parents=True, exist_ok=True)
    with patch.object(br_05.Deps, "remove", side_effect=mock_remove):
        with patch.object(br_05.Deps, "new_session", side_effect=mock_new_session):
            processor = br_05.BackgroundRemover()
            result = processor.process_file(image_path, out_path)
    return result


def test_br_06(image_path):
    sys.path.insert(0, str(LOCAL_SERVICE))
    import br_06
    out_path = str(OUTPUT_BASE / "output_br_06" / f"{Path(image_path).stem}_06.png")
    (OUTPUT_BASE / "output_br_06").mkdir(parents=True, exist_ok=True)
    with patch.object(br_06.Deps, "remove", side_effect=mock_remove):
        with patch.object(br_06.Deps, "new_session", side_effect=mock_new_session):
            processor = br_06.BackgroundRemover()
            result = processor.process_file(image_path, out_path)
    return result


def test_br_08(image_path):
    sys.path.insert(0, str(LOCAL_SERVICE))
    import br_08
    out_path = str(OUTPUT_BASE / "output_br_08" / f"{Path(image_path).stem}_08.png")
    (OUTPUT_BASE / "output_br_08").mkdir(parents=True, exist_ok=True)
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    with patch("br_08.remove", side_effect=mock_remove):
        with patch("br_08.new_session", side_effect=mock_new_session):
            result = br_08.process_product_image(image_bytes, "transparent", "PNG")
    if "base64" in result:
        import base64
        Path(out_path).write_bytes(base64.b64decode(result["base64"]))
    return {"success": "error" not in result}


def test_br_11(image_path):
    sys.path.insert(0, str(LOCAL_SERVICE))
    import br_11
    out_path = str(OUTPUT_BASE / "output_br_11" / f"{Path(image_path).stem}_11.png")
    (OUTPUT_BASE / "output_br_11").mkdir(parents=True, exist_ok=True)
    with patch("rembg.remove", side_effect=mock_remove):
        with patch("rembg.new_session", side_effect=mock_new_session):
            br_11.Exporter.process_and_save(Path(image_path).read_bytes(), out_path, br_11.CONFIG)
    return {"success": Path(out_path).exists()}


def test_br_12(image_path):
    sys.path.insert(0, str(LOCAL_SERVICE))
    import br_12
    out_path = str(OUTPUT_BASE / "output_br_12" / f"{Path(image_path).stem}_12.png")
    (OUTPUT_BASE / "output_br_12").mkdir(parents=True, exist_ok=True)
    with patch("rembg.remove", side_effect=mock_remove):
        with patch("rembg.new_session", side_effect=mock_new_session):
            br_12.Exporter.process_and_save(Path(image_path).read_bytes(), out_path, br_12.CONFIG)
    return {"success": Path(out_path).exists()}


def test_br_13(image_path):
    sys.path.insert(0, str(LOCAL_SERVICE))
    import br_13
    out_path = str(OUTPUT_BASE / "output_br_13" / f"{Path(image_path).stem}_13.png")
    (OUTPUT_BASE / "output_br_13").mkdir(parents=True, exist_ok=True)
    with patch("rembg.remove", side_effect=mock_remove):
        with patch("rembg.new_session", side_effect=mock_new_session):
            br_13.Exporter.process_and_save(Path(image_path).read_bytes(), out_path, br_13.CONFIG)
    return {"success": Path(out_path).exists()}


def main():
    copied = ensure_local_images()
    if not copied:
        print("No test images found.")
        return

    tests = [
        ("br_05 Clean", test_br_05),
        ("br_06 Precision", test_br_06),
        ("br_08 Production", test_br_08),
        ("br_11 Ultimate", test_br_11),
        ("br_12 Variant", test_br_12),
        ("br_13 Testing", test_br_13),
    ]

    summaries = []
    for image_path in copied:
        img = Image.open(image_path)
        for label, fn in tests:
            start = time.perf_counter()
            error = ""
            out_path = ""
            try:
                res = fn(str(image_path))
                success = res.get("success", False)
            except Exception as e:
                success = False
                error = str(e)
            elapsed = time.perf_counter() - start

            out_path = str(OUTPUT_BASE / f"output_{label.split()[0][2:]}" / f"{image_path.stem}_{label.split()[0][2:]}.png")
            stats = analyze_output(out_path) if Path(out_path).exists() else {"error": "missing"}
            summaries.append({
                "image": image_path.name,
                "size": img.size,
                "model": label,
                "success": success,
                "time": round(elapsed, 3),
                "coverage": stats.get("coverage", "-") if success else "-",
                "output_mode": stats.get("mode", "-") if success else "-",
                "error": error,
            })

    print("\n" + "=" * 90)
    print(f"{'Image':<16} {'Model':<18} {'Status':<8} {'Time':<8} {'Coverage':<10} {'Mode':<8}")
    print("-" * 90)
    for s in summaries:
        status = "OK" if s["success"] else "FAIL"
        cov = f"{s['coverage']:.2%}" if isinstance(s['coverage'], float) else str(s['coverage'])
        print(f"{s['image']:<16} {s['model']:<18} {status:<8} {s['time']:<8} {cov:<10} {s['output_mode']:<8}")
    print("=" * 90)

    total = len(summaries)
    ok = sum(1 for s in summaries if s["success"])
    print(f"\nTotal: {ok}/{total} passed across {len(copied)} images x 6 models")
    cleanup_local_images(copied)
    return summaries


if __name__ == "__main__":
    main()
