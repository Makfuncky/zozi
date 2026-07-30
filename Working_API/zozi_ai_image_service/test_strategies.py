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
OUTPUT_FOLDER = WORKSPACE / "Working_API" / "zozi_ai_image_service" / "bg_all_results"
BACKEND = WORKSPACE / "backend"

sys.path.insert(0, str(BACKEND))

ALL_IMAGES = sorted([p for p in INPUT_FOLDER.iterdir() if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}])


def make_fake_rgba_png(width, height):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    arr = np.array(img)
    margin_x = max(1, int(width * 0.04))
    margin_y = max(1, int(height * 0.04))
    arr[margin_y:-margin_y, margin_x:-margin_x, 3] = 255
    arr[margin_y:-margin_y, margin_x:-margin_x, 0] = 200
    arr[margin_y:-margin_y, margin_x:-margin_x, 1] = 180
    arr[margin_y:-margin_y, margin_x:-margin_x, 2] = 160
    return Image.fromarray(arr, mode="RGBA")


def mock_remove(image, session=None):
    if hasattr(image, "width") and hasattr(image, "height"):
        width, height = image.width, image.height
    else:
        img = Image.open(io.BytesIO(image)).convert("RGBA")
        width, height = img.width, img.height
    return make_fake_rgba_png(width, height)


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


def run_strategy(image_bytes, strategy_name):
    start = time.perf_counter()
    try:
        from providers.bg_remover import remove_background_strategy
        result = remove_background_strategy(image_bytes, strategy_name)
        elapsed = time.perf_counter() - start
        return result, elapsed, None
    except Exception as e:
        elapsed = time.perf_counter() - start
        return None, elapsed, str(e)


def main():
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    strategies = [
        "clean_commercial",
        "precision_geometry",
        "production_birefnet",
        "ultimate_v11",
        "ultimate_v12",
        "variant_testing",
    ]

    summaries = []
    for image_path in ALL_IMAGES:
        image_bytes = image_path.read_bytes()
        for strategy in strategies:
            out_path = OUTPUT_FOLDER / f"{image_path.stem}_{strategy}.png"
            with patch("providers.bg_remover.remove", side_effect=mock_remove):
                with patch("providers.bg_remover.new_session", side_effect=mock_new_session):
                    result, elapsed, error = run_strategy(image_bytes, strategy)

            success = False
            if result is not None:
                try:
                    out_path.write_bytes(result)
                    success = True
                except Exception as e:
                    error = str(e)

            stats = analyze_output(out_path) if success else {"error": error or "missing"}
            summaries.append({
                "image": image_path.name,
                "strategy": strategy,
                "success": success,
                "time": round(elapsed, 3),
                "coverage": stats.get("coverage", "-") if success else "-",
                "mode": stats.get("mode", "-") if success else "-",
                "error": error or "",
            })

    print("\n" + "=" * 100)
    print(f"{'Image':<18} {'Strategy':<22} {'Status':<8} {'Time':<8} {'Coverage':<10} {'Mode':<8}")
    print("-" * 100)
    for s in summaries:
        status = "OK" if s["success"] else "FAIL"
        cov = f"{s['coverage']:.2%}" if isinstance(s['coverage'], float) else str(s['coverage'])
        print(f"{s['image']:<18} {s['strategy']:<22} {status:<8} {s['time']:<8} {cov:<10} {s['mode']:<8}")
    print("=" * 100)

    total = len(summaries)
    ok = sum(1 for s in summaries if s["success"])
    print(f"\nTotal: {ok}/{total} passed across {len(ALL_IMAGES)} images x {len(strategies)} strategies")
    return summaries


if __name__ == "__main__":
    main()