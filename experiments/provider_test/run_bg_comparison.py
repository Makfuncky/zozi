"""
Side-by-Side BG Strategy Comparison
=====================================
Runs all 6 background-removal strategies on representative product images
(Clothing, Electronics, Beauty), computes quality metrics, generates
side-by-side composite comparison PNGs, and writes an HTML report.

Usage:
    cd backend && python ../provider_test/run_bg_comparison.py

Output:
    provider_test/bg_comparison/
        ├── index.html          ← main report
        ├── strategy_grid_*.png ← one grid per category with all 6 strategies
        ├── individual/         ← each (image × strategy) result as PNG
        └── metrics.json        ← all quality metrics as JSON
"""

import sys, os, json, io, gc, time, base64
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict

# Windows terminal encoding fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ── Add backend to path ─────────────────────────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

os.environ["BG_SKIP_HEAVY_MODELS"] = "true"
os.environ["BG_ALLOW_HEAVY_MODELS"] = "false"

# ── Import provider ─────────────────────────────────────────────────
from providers.bg_remover import (
    remove_background_strategy,
    ProcessingStrategy,
    _SessionManager,
    MemoryManager,
)

# ── Categories + images ─────────────────────────────────────────────
# Representative images for each category based on visual inspection:
#   Clothing:   bright, varied colors, textured fabric
#   Electronics: neutral, dark, smooth surfaces
#   Beauty:     pastel, colorful, small containers

CATEGORIES = {
    "Clothing": [
        ("image_05.jpg", "Casual Wear (Light)"),
        ("image_07.jpg", "Warm-toned Garment"),
        ("image_08.webp", "Fashion Product"),
        ("image_12.jpg", "Textile Close-up"),
    ],
    "Electronics": [
        ("image_04.jpg", "Gadget (Neutral)"),
        ("image_15.jpeg", "Dark Device"),
        ("image_17.jpeg", "Electronic Component"),
        ("image_23.jpg", "Tech Product"),
    ],
    "Beauty & Personal Care": [
        ("image_14.jpeg", "Blue-tone Product"),
        ("image_16.jpeg", "Red/Orange Cosmetic"),
        ("image_29.webp", "Pink Beauty Item"),
        ("image_30.jpg", "Personal Care"),
    ],
}

STRATEGIES = [
    ("clean_commercial",    "br_05 · Clean Edge"),
    ("precision_geometry",  "br_06 · Precision Geo"),
    ("production_birefnet", "br_08 · Production"),
    ("ultimate_v11",        "br_11 · Ultimate Gap"),
    ("ultimate_v12",        "br_12 · Marketing"),
    ("variant_testing",     "br_13 · Lite Variant"),
]

IMG_DIR = BACKEND_DIR.parent / "image"
OUTPUT_DIR = Path(__file__).resolve().parent / "bg_comparison"
INDIVIDUAL_DIR = OUTPUT_DIR / "individual"

MAX_DIM = 1024  # max dimension for processing


@dataclass
class MetricResult:
    strategy: str = ""
    strategy_label: str = ""
    image_name: str = ""
    category: str = ""
    timing_s: float = 0.0
    output_size_bytes: int = 0
    coverage_pct: float = 0.0          # foreground pixel ratio
    alpha_confidence: float = 0.0      # mean alpha in foreground
    edge_clarity: float = 0.0          # Laplacian variance on alpha edge band
    edge_smoothness: float = 0.0       # variance of gradient magnitude on edge
    artifact_count: int = 0            # connected components outside main subject
    main_foreground_ratio: float = 0.0 # ratio of largest CC to total fg
    error: str = ""
    final_dimensions: str = ""
    model_used: str = ""


def load_image(fname: str) -> bytes:
    path = IMG_DIR / fname
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    return path.read_bytes()


def resize_to_max(data: bytes, max_dim: int) -> bytes:
    """Downscale to max_dim while preserving aspect ratio."""
    img = Image.open(io.BytesIO(data)).convert("RGB")
    w, h = img.size
    if max(w, h) <= max_dim:
        return data
    ratio = max_dim / max(w, h)
    new_w, new_h = int(w * ratio), int(h * ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def compute_metrics(result_bytes: bytes, timing_s: float, strategy_label: str) -> MetricResult:
    m = MetricResult(strategy_label=strategy_label, timing_s=timing_s)

    if not result_bytes or len(result_bytes) < 100:
        m.error = "Empty or invalid result"
        return m

    m.output_size_bytes = len(result_bytes)

    try:
        img = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
        m.final_dimensions = f"{img.size[0]}x{img.size[1]}"
        arr = np.array(img)
        alpha = arr[:, :, 3].astype(np.float32) / 255.0
        rgb = arr[:, :, :3].astype(np.float32)

        h, w = alpha.shape
        total_px = h * w

        # Coverage: foreground pixel ratio (alpha > 0.02)
        fg_mask = alpha > 0.02
        fg_count = int(np.sum(fg_mask))
        m.coverage_pct = round(fg_count / total_px * 100, 2)

        # Alpha confidence: mean alpha value in foreground
        if fg_count > 0:
            m.alpha_confidence = round(float(np.mean(alpha[fg_mask])), 4)

        # Edge clarity: Laplacian variance on the alpha edge transition band
        try:
            import cv2
            alpha_u8 = (alpha * 255).astype(np.uint8)
            # Edge band: alpha between 0.02 and 0.98
            edge_band = (alpha > 0.02) & (alpha < 0.98)
            if np.sum(edge_band) > 100:
                # Laplacian on the alpha channel
                lap = cv2.Laplacian(alpha_u8, cv2.CV_32F)
                m.edge_clarity = float(np.var(lap[edge_band]))
                # Edge smoothness: variance of gradient magnitude
                grad_x = cv2.Sobel(alpha_u8, cv2.CV_32F, 1, 0)
                grad_y = cv2.Sobel(alpha_u8, cv2.CV_32F, 0, 1)
                grad_mag = np.sqrt(grad_x**2 + grad_y**2)
                m.edge_smoothness = float(np.std(grad_mag[edge_band]))
            else:
                # Very sharp cut — not much edge band to measure
                m.edge_clarity = 999.0
                m.edge_smoothness = 0.0
        except ImportError:
            m.edge_clarity = -1.0
            m.edge_smoothness = -1.0

        # Artifact detection via connected components
        try:
            import cv2
            binary = (alpha > 0.5).astype(np.uint8) * 255
            num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
            if num_labels > 1:
                # Find the largest component
                areas = [(i, stats[i, cv2.CC_STAT_AREA]) for i in range(1, num_labels)]
                areas.sort(key=lambda x: x[1], reverse=True)
                largest_idx, largest_area = areas[0]
                main_ratio = largest_area / max(fg_count, 1)
                m.main_foreground_ratio = round(main_ratio, 4)
                # Artifacts = components < 5% of largest
                m.artifact_count = sum(1 for _, a in areas[1:] if a < largest_area * 0.05)
            else:
                m.main_foreground_ratio = 1.0
                m.artifact_count = 0
        except ImportError:
            m.artifact_count = -1
            m.main_foreground_ratio = -1.0

    except Exception as exc:
        m.error = f"Metric computation failed: {exc}"

    return m


def create_side_by_side_grid(
    results: list[tuple[str, str, bytes, MetricResult]],
    image_name: str,
    category: str,
    output_path: Path,
):
    """Create a grid image showing original + all 6 strategies side by side."""
    try:
        import cv2
    except ImportError:
        return  # No OpenCV, can't make composites

    original_path = IMG_DIR / image_name
    orig_img = cv2.imread(str(original_path))
    if orig_img is None:
        return
    orig_h, orig_w = orig_img.shape[:2]

    # Resize all to uniform height for the grid
    cell_h = 400
    cell_w = int(orig_w * cell_h / orig_h)

    # Grid: 1 row original + 2 rows × 3 cols strategies
    cols = 3
    rows = 3   # 1 original + 2 strategy rows
    label_h = 36
    total_cell_h = cell_h + label_h
    total_w = cols * cell_w
    total_h = rows * total_cell_h

    grid = np.ones((total_h, total_w, 3), dtype=np.uint8) * 245  # light gray bg

    def put_label(img, text, y_offset, font_scale=0.5, color=(0, 0, 0)):
        try:
            # Try PIL for better text rendering
            pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_img)
            try:
                font = ImageFont.truetype("arial.ttf", 14)
            except:
                font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            tx = (img.shape[1] - tw) // 2
            ty = y_offset + (label_h - th) // 2
            # Background pill
            draw.rectangle([tx-4, ty-2, tx+tw+4, ty+th+2], fill=(245, 245, 245))
            draw.text((tx, ty), text, fill=color, font=font)
            return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        except:
            cv2.putText(img, text, (10, y_offset + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 1)
            return img

    # Row 0: Original image
    orig_resized = cv2.resize(orig_img, (cell_w, cell_h))
    x0 = 0
    y0 = 0
    grid[y0:y0+cell_h, x0:x0+cell_w] = orig_resized
    grid = put_label(grid, f"📷 ORIGINAL — {image_name}", y0 + cell_h)

    # Fill other cells with blank
    for c in range(1, cols):
        x = c * cell_w
        grid[y0:y0+cell_h, x:x+cell_w] = 200

    # Strategy grid: row 1 = cols 0-2, row 2 = cols 3-5
    for idx, (strat_key, strat_label, result_bytes, metrics) in enumerate(results):
        row = idx // cols
        col = idx % cols
        cell_y = (row + 1) * total_cell_h  # +1 for original row
        cell_x = col * cell_w

        # Decode result
        try:
            result_rgba = cv2.imdecode(
                np.frombuffer(result_bytes, np.uint8),
                cv2.IMREAD_UNCHANGED
            )
            if result_rgba is None:
                raise ValueError("decode failed")
            # Composite over white for display
            if result_rgba.shape[2] == 4:
                alpha = result_rgba[:, :, 3:4].astype(float) / 255.0
                result_rgb = (result_rgba[:, :, :3].astype(float) * alpha +
                             255.0 * (1.0 - alpha)).astype(np.uint8)
            else:
                result_rgb = result_rgba[:, :, :3]
        except:
            result_rgb = np.ones((cell_h, cell_w, 3), dtype=np.uint8) * 128
            cv2.putText(result_rgb, "FAIL", (cell_w//2-30, cell_h//2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        result_resized = cv2.resize(result_rgb, (cell_w, cell_h))
        grid[cell_y:cell_y+cell_h, cell_x:cell_x+cell_w] = result_resized

        # Label with short name + metrics
        label = f"{strat_label}"
        grid = put_label(grid, label, cell_y + cell_h)
        metrics_text = f" cov={metrics.coverage_pct:.0f}%  conf={metrics.alpha_confidence:.2f}  edge={metrics.edge_clarity:.1f}  artf={metrics.artifact_count}  t={metrics.timing_s:.1f}s"
        grid = put_label(grid, metrics_text, cell_y + cell_h + 16, font_scale=0.4, color=(80, 80, 80))

    cv2.imwrite(str(output_path), grid)
    return grid


def generate_html_report(
    all_metrics: list[MetricResult],
    category_grids: list[tuple[str, str, Path]],  # (category, image_name, grid_path)
    strategy_averages: dict[str, dict[str, dict[str, float]]],
) -> str:
    """Generate a self-contained HTML report with all results."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── Build per-strategy-per-category recommendation table ──
    rows_html = ""
    for m in all_metrics:
        if m.error:
            rows_html += f"""<tr class="error">
                <td>{m.category}</td><td>{m.image_name}</td>
                <td>{m.strategy_label}</td>
                <td colspan="7">{m.error}</td></tr>\n"""
            continue
        badge = "✅" if m.artifact_count == 0 else f"⚠️{'' if m.artifact_count < 5 else '🔴'}"
        rows_html += f"""<tr>
            <td>{m.category}</td>
            <td title="{m.final_dimensions}">{m.image_name.split('.')[0]}</td>
            <td><strong>{m.strategy_label.replace('·','<br>')}</strong></td>
            <td>{m.timing_s:.1f}s</td>
            <td>{m.coverage_pct:.1f}%</td>
            <td>{m.alpha_confidence:.2f}</td>
            <td>{m.edge_clarity:.1f}</td>
            <td>{m.edge_smoothness:.1f}</td>
            <td>{badge} {m.artifact_count}</td>
            <td>{m.main_foreground_ratio:.2f}</td>
        </tr>\n"""

    # ── Build average table & winner matrix ──
    avg_rows = ""
    winner_matrix: dict[str, dict[str, list[tuple[str, float]]]] = {}
    METRIC_NAMES = {
        "alpha_confidence": "Alpha Confidence",
        "coverage_pct": "Coverage %",
        "edge_clarity": "Edge Clarity",
        "edge_smoothness": "Edge Smoothness",
    }
    for cat_key, cat_data in strategy_averages.items():
        winner_matrix[cat_key] = {}
        for metric_key, metric_label in METRIC_NAMES.items():
            sorted_strats = sorted(cat_data.items(), key=lambda x: x[1][metric_key], reverse=True)
            winner_matrix[cat_key][metric_label] = [(s, v[metric_key]) for s, v in sorted_strats]

    # Create winner matrix as markdown table
    winner_html = ""
    for cat_key in strategy_averages:
        # Best all-around strategy by summing z-scores
        cat_best = {}
        for strat_key in strategy_averages[cat_key]:
            with_strat = strategy_averages[cat_key][strat_key]
            z_scores = []
            for mk in ["edge_clarity", "alpha_confidence", "coverage_pct"]:
                vals = [strategy_averages[cat_key][s][mk] for s in strategy_averages[cat_key]]
                mean_v = np.mean(vals) if vals else 0
                std_v = np.std(vals) if vals and np.std(vals) > 0 else 1
                z_scores.append((with_strat[mk] - mean_v) / std_v)
            cat_best[strat_key] = np.mean(z_scores)

        best_strat = max(cat_best, key=cat_best.get) if cat_best else ""
        ranked = sorted(cat_best.items(), key=lambda x: x[1], reverse=True)

        winner_html += f"""<h3>🏆 {cat_key}</h3>
        <table class="winner"><tr><th>Rank</th><th>Strategy</th><th>Composite Score</th></tr>\n"""
        for rank, (strat, score) in enumerate(ranked, 1):
            highlight = " class='best'" if rank == 1 else ""
            winner_html += f"<tr{highlight}><td>{rank}</td><td>{strat}</td><td>{score:.2f}</td></tr>\n"
        winner_html += "</table>\n"

    # Make relative paths for images
    grid_images_html = ""
    for cat, img_name, grid_path in category_grids:
        rel = grid_path.name
        grid_images_html += f"""<div class="grid-section">
            <h2>{cat} — <em>{img_name}</em></h2>
            <a href="{rel}" target="_blank">
                <img src="{rel}" alt="{cat} {img_name}" style="max-width:100%;border:1px solid #ddd;">
            </a>
        </div>\n"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>BG Strategy Comparison — Zozi</title>
<style>
    body {{ font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
           margin: 20px; background: #f8f9fa; color: #333; }}
    h1 {{ color: #1a1a2e; }}
    h2 {{ color: #16213e; border-bottom: 2px solid #0f3460; padding-bottom: 4px; margin-top: 30px; }}
    .summary {{ background: #fff; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    table {{ border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 13px; }}
    th, td {{ padding: 6px 8px; text-align: left; border-bottom: 1px solid #dee2e6; }}
    th {{ background: #1a1a2e; color: #fff; position: sticky; top: 0; }}
    tr:hover {{ background: #f0f4ff; }}
    .error td {{ background: #fff5f5; color: #c53030; }}
    .best {{ background: #f0fff4 !important; font-weight: bold; }}
    .winner {{ width: auto; }}
    .grid-section {{ margin: 20px 0; background: #fff; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    .grid-section img {{ cursor: zoom-in; }}
    .winner h3 {{ margin-top: 15px; color: #2d3748; }}
    .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; }}
    .badge-ok {{ background: #c6f6d5; color: #22543d; }}
    .badge-warn {{ background: #fefcbf; color: #744210; }}
    .badge-bad {{ background: #fed7d7; color: #9b2c2c; }}
    @media (max-width: 768px) {{ table {{ font-size: 11px; }} th,td {{ padding: 4px; }} }}
</style>
</head>
<body>
<h1>🧪 BG Strategy Comparison Report</h1>
<p class="summary">
    Generated: {now}<br>
    <strong>6 strategies</strong> × <strong>{len(CATEGORIES)} categories</strong> = <strong>{len(all_metrics)} total tests</strong><br>
    Max dimension: {MAX_DIM}px · Heavy models: <span class="badge badge-ok">SKIPPED</span><br>
    Errors: <span class="badge badge-ok">{sum(1 for m in all_metrics if not m.error)} OK</span>
    <span class="badge badge-bad">{sum(1 for m in all_metrics if m.error)} FAIL</span>
</p>

<h2>🏆 Per-Category Winners</h2>
{winner_html}

<h2>📊 Detailed Metrics Table</h2>
<div style="overflow-x:auto">
<table>
<thead><tr>
    <th>Category</th><th>Image</th><th>Strategy</th>
    <th>⏱ Time</th><th>📐 Coverage</th><th>🎯 Alpha Conf</th>
    <th>🔪 Edge Clarity</th><th>✨ Edge Smooth</th>
    <th>🧹 Artifacts</th><th>📏 Main Ratio</th>
</tr></thead>
<tbody>
{rows_html}
</tbody>
</table>
</div>

<h2>🖼️ Side-by-Side Grid Comparison</h2>
{grid_images_html}

<p class="summary" style="text-align:center;color:#718096;margin-top:30px">
    <em>Higher edge clarity = sharper transitions. Higher alpha confidence = more solid foreground.
    Fewer artifacts = cleaner result. Composite Z-score averages all metrics for overall ranking.</em>
</p>
</body>
</html>"""
    return html


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    INDIVIDUAL_DIR.mkdir(parents=True, exist_ok=True)

    all_metrics: list[MetricResult] = []
    category_grids: list[tuple[str, str, Path]] = []
    strategy_averages: dict[str, dict[str, dict[str, float]]] = {}
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    total_tests = sum(len(imgs) for imgs in CATEGORIES.values()) * len(STRATEGIES)
    test_idx = 0

    print(f"🧪 BG Strategy Comparison — {total_tests} total tests")
    print("=" * 70)

    for category, images in CATEGORIES.items():
        print(f"\n📁 Category: {category}")
        strategy_averages[category] = {}

        for image_name, image_label in images:
            print(f"  📷 {image_label} ({image_name})")

            try:
                raw_bytes = load_image(image_name)
                raw_bytes = resize_to_max(raw_bytes, MAX_DIM)
            except FileNotFoundError as e:
                print(f"    ❌ {e}")
                continue

            results: list[tuple[str, str, bytes, MetricResult]] = []

            for strat_key, strat_label in STRATEGIES:
                test_idx += 1
                print(f"    [{test_idx}/{total_tests}] {strat_label}...", end=" ", flush=True)

                try:
                    _SessionManager.reset()
                    MemoryManager.cleanup()
                    gc.collect()

                    t0 = time.perf_counter()
                    result = remove_background_strategy(raw_bytes, strat_key)
                    elapsed = time.perf_counter() - t0

                    metrics = compute_metrics(result, elapsed, strat_label)
                    metrics.strategy = strat_key
                    metrics.strategy_label = strat_label
                    metrics.image_name = image_name
                    metrics.category = category

                    # Save individual result
                    ind_path = INDIVIDUAL_DIR / f"{category}_{image_name.split('.')[0]}_{strat_key}.png"
                    with open(ind_path, "wb") as f:
                        f.write(result)

                    results.append((strat_key, strat_label, result, metrics))
                    all_metrics.append(metrics)

                    if metrics.error:
                        print(f"⚠️ {metrics.error}")
                    else:
                        print(f"✅ {metrics.timing_s:.1f}s cov={metrics.coverage_pct:.0f}% conf={metrics.alpha_confidence:.2f}")
                except Exception as exc:
                    print(f"❌ {exc}")
                    m = MetricResult(
                        strategy=strat_key, strategy_label=strat_label,
                        image_name=image_name, category=category,
                        error=str(exc),
                    )
                    results.append((strat_key, strat_label, b"", m))
                    all_metrics.append(m)

            # Generate side-by-side grid
            try:
                grid_filename = f"strategy_grid_{category}_{image_name.split('.')[0]}.png"
                grid_path = OUTPUT_DIR / grid_filename
                create_side_by_side_grid(results, image_name, category, grid_path)
                category_grids.append((category, image_label, grid_path))
                print(f"    📊 Grid saved: {grid_filename}")
            except Exception as exc:
                print(f"    ❌ Grid failed: {exc}")

            # Update averages for this category
            for strat_key, strat_label, result, m in results:
                if m.error:
                    continue
                if strat_label not in strategy_averages[category]:
                    strategy_averages[category][strat_label] = {
                        "alpha_confidence": [], "coverage_pct": [], "edge_clarity": [],
                        "edge_smoothness": [], "timing_s": [], "artifact_count": [],
                    }
                sa = strategy_averages[category][strat_label]
                sa["alpha_confidence"].append(m.alpha_confidence)
                sa["coverage_pct"].append(m.coverage_pct)
                sa["edge_clarity"].append(m.edge_clarity)
                sa["edge_smoothness"].append(m.edge_smoothness)
                sa["timing_s"].append(m.timing_s)
                sa["artifact_count"].append(m.artifact_count)

            _SessionManager.reset()
            MemoryManager.cleanup()
            gc.collect()

    # Compute final averages
    for cat in strategy_averages:
        for strat in strategy_averages[cat]:
            for k in list(strategy_averages[cat][strat].keys()):
                vals = strategy_averages[cat][strat][k]
                strategy_averages[cat][strat][k] = round(float(np.mean(vals)), 3) if vals else 0.0

    # Generate HTML report
    html = generate_html_report(all_metrics, category_grids, strategy_averages)
    report_path = OUTPUT_DIR / "index.html"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)

    # Save raw metrics as JSON
    metrics_json = []
    for m in all_metrics:
        d = asdict(m)
        # Skip binary/bytes fields
        metrics_json.append(d)
    metrics_path = OUTPUT_DIR / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_json, f, indent=2, default=str)

    # Summary
    ok = sum(1 for m in all_metrics if not m.error)
    fail = sum(1 for m in all_metrics if m.error)
    print("\n" + "=" * 70)
    print(f"✅ Complete: {ok} passed, {fail} failed")
    print(f"📊 Report: {report_path}")
    print(f"📁 Output: {OUTPUT_DIR}")
    print(f"📐 Max dimension: {MAX_DIM}px")

    # Print per-category winner
    print("\n🏆 Per-Category Winners (by composite Z-score):")
    for cat in CATEGORIES:
        if cat not in strategy_averages or not strategy_averages[cat]:
            continue
        best = max(strategy_averages[cat].items(),
                   key=lambda x: (
                       x[1]["edge_clarity"] + x[1]["alpha_confidence"]*100 + x[1]["coverage_pct"]
                   ) / 3)
        print(f"  {cat:25s} → {best[0]}")


if __name__ == "__main__":
    main()
