from typing import Any, List, Dict
# ========================== br_05 / br_06: BACKGROUND REMOVER LEGACY ==========================
from PIL import Image

import numpy as np


from typing import Optional


class BackgroundRemover:
    """Legacy clean-commercial and precision-geometry background remover (br_05/br_06)."""

    def __init__(self, config=None):
        self.config = config
        self.session = None
        self.model_name = None
        self.stats = {"total_processed": 0, "total_time": 0, "errors": 0}

    def _load_best_model(self):
        if self.config is None:
            models = ["isnet-general-use", "u2net"]
        else:
            models = self.config.models
        for model_name in models:
            try:
                self.session = _SessionManager.get_session(model_name)
                self.model_name = model_name
                return True
            except Exception:
                pass
        return False

    def process_file(self, input_path: str, output_path: str) -> Dict[str, Any]:
        start_time = time.time()
        result = {"input": input_path, "output": output_path, "success": False, "time_seconds": 0}

        try:
            img = Image.open(input_path).convert("RGB")
            img_np = np.array(img)
            h, w = img_np.shape[:2]

            ratio = 1.0
            img_resized = img
            if max(w, h) > 2048:
                ratio = 2048 / max(w, h)
                new_w, new_h = int(w * ratio), int(h * ratio)
                img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            buf = io.BytesIO()
            img_resized.save(buf, format="PNG")
            input_bytes = buf.getvalue()

            session = self.session
            if session is None:
                return result

            output_bytes = _safe_remove(img_resized, session)
            out_img = Image.open(io.BytesIO(output_bytes.tobytes() if hasattr(output_bytes, 'tobytes') else output_bytes)).convert("RGBA") if isinstance(output_bytes, Image.Image) else Image.open(io.BytesIO(output_bytes)).convert("RGBA")

            if ratio < 1.0:
                out_img = out_img.resize((w, h), Image.Resampling.LANCZOS)

            raw_alpha = np.array(out_img.split()[-1]).astype(np.float32) / 255.0
            final_alpha = CleanEdgeRefiner.refine(img_np, raw_alpha)
            final_alpha[final_alpha < 0.02] = 0.0
            final_alpha[final_alpha > 0.98] = 1.0

            alpha_uint8 = np.clip(final_alpha * 255, 0, 255).astype(np.uint8)
            result_img = Image.fromarray(np.dstack([img_np, alpha_uint8]), mode="RGBA")

            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            result_img.save(output_path, "PNG", compress_level=6)

            elapsed = time.time() - start_time
            result.update({"success": True, "time_seconds": round(elapsed, 2)})
            self.stats["total_processed"] += 1
            self.stats["total_time"] += elapsed
        except Exception as exc:
            logger.error("BackgroundRemover failed: %s", exc)
            result["error"] = str(exc)
            self.stats["errors"] += 1

        return result

    def process_folder(self, input_folder: str, output_folder: str) -> List[Dict[str, Any]]:
        input_path = Path(input_folder)
        output_path = Path(output_folder)

        if not input_path.exists():
            logger.error("Input folder not found: %s", input_folder)
            return []

        supported_ext = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
        image_files = [f for f in input_path.iterdir() if f.is_file() and f.suffix.lower() in supported_ext]

        if not image_files:
            logger.warning("No images found in %s", input_folder)
            return []

        if not self._load_best_model():
            logger.error("No models could be loaded!")
            return []

        output_path.mkdir(parents=True, exist_ok=True)
        results = []
        for img_file in sorted(image_files):
            out_file = output_path / f"{img_file.stem}.png"
            results.append(self.process_file(str(img_file), str(out_file)))
            gc.collect()

        successful = [r for r in results if r["success"]]
        logger.info("BR05 legacy: %d/%d processed", len(successful), len(results))
        return results

