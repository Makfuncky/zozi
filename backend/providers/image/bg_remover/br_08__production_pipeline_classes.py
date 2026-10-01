from typing import List, Tuple, Optional, Dict, Any
# ========================== br_08: PRODUCTION PIPELINE CLASSES ==========================
from PIL import Image

import numpy as np

from .configuration import ProcessingConfig


class ColorSpaceUtils:
    """Utility class for color space conversions (br_08)."""

    @staticmethod
    def rgb_to_gray(image: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return np.mean(image[:, :, :3], axis=2)
        return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    @staticmethod
    def rgb_to_hsv(image: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

    @staticmethod
    def rgb_to_lab(image: np.ndarray) -> np.ndarray:
        if not _HAS_CV2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_RGB2LAB)

    @staticmethod
    def detect_skin_regions(image: np.ndarray) -> np.ndarray:
        hsv = ColorSpaceUtils.rgb_to_hsv(image)
        lower1 = np.array([0, 20, 70], dtype=np.uint8)
        upper1 = np.array([20, 255, 255], dtype=np.uint8)
        lower2 = np.array([160, 20, 70], dtype=np.uint8)
        upper2 = np.array([180, 255, 255], dtype=np.uint8)
        mask1 = cv2.inRange(hsv, lower1, upper1) if _HAS_CV2 else np.zeros(image.shape[:2], dtype=np.uint8)
        mask2 = cv2.inRange(hsv, lower2, upper2) if _HAS_CV2 else np.zeros(image.shape[:2], dtype=np.uint8)
        skin_mask = cv2.bitwise_or(mask1, mask2) if _HAS_CV2 else np.zeros(image.shape[:2], dtype=np.uint8)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)) if _HAS_CV2 else np.ones((5, 5), np.uint8)
        return cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel, iterations=2) if _HAS_CV2 else skin_mask


class ImageLoader:
    """Load and preprocess images for background removal (br_08)."""

    @staticmethod
    def load_from_bytes(image_bytes: bytes) -> Tuple[Image.Image, np.ndarray]:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.load()
        return img, np.array(img)

    @staticmethod
    def preprocess_for_segmentation(image_np: np.ndarray) -> np.ndarray:
        lab = cv2.cvtColor(image_np, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l)
        lab_enhanced = cv2.merge([l_enhanced, a, b])
        return cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2RGB)


class QualityAnalyzer:
    """Analyze image quality for optimal processing (br_08)."""

    @staticmethod
    def analyze(image_np: np.ndarray) -> Dict[str, float]:
        gray = ColorSpaceUtils.rgb_to_gray(image_np)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        return {
            "texture_complexity": float(np.var(laplacian)),
            "brightness": float(np.mean(gray)),
        }


class SubjectDetector:
    """Detect subject type (product, human, clothing, food) from initial mask (br_08)."""

    @staticmethod
    def detect(image_np: np.ndarray, initial_mask: np.ndarray) -> Tuple[str, Dict[str, float]]:
        metrics = {}

        try:
            skin_mask = ColorSpaceUtils.detect_skin_regions(image_np)
            metrics["skin_ratio"] = float(np.sum(skin_mask > 0)) / skin_mask.size

            mask_binary = (initial_mask > 127).astype(np.uint8)
            metrics["coverage"] = float(np.sum(mask_binary > 0)) / mask_binary.size

            gray_full = ColorSpaceUtils.rgb_to_gray(image_np)
            full_edges = cv2.Canny(gray_full, 50, 150)
            metrics["edge_density"] = float(np.sum(full_edges > 0)) / full_edges.size

            if metrics.get("skin_ratio", 0) < 0.05:
                subject_type = SubjectCategory.CLOTHING.value if metrics.get("edge_density", 0) > 0.1 else SubjectCategory.PRODUCT.value
            elif metrics.get("skin_ratio", 0) > 0.15:
                if metrics.get("edge_density", 0) < 0.15:
                    subject_type = SubjectCategory.HUMAN.value
                else:
                    subject_type = SubjectCategory.CLOTHING.value
            else:
                subject_type = SubjectCategory.PRODUCT.value

        except Exception as exc:
            logger.warning("Subject detection failed: %s, using default", exc)
            subject_type = SubjectCategory.PRODUCT.value

        return subject_type, metrics


class ModelSelector:
    """Select optimal model list per subject type (br_08)."""

    def __init__(self):
        self.model_configs = {
            SubjectCategory.PRODUCT: {
                "primary": ["birefnet-general", "isnet-general-use"],
                "fallback": ["u2net", "silueta"],
            },
            SubjectCategory.HUMAN: {
                "primary": ["birefnet-general", "isnet-general-use"],
                "fallback": ["silueta"],
            },
            SubjectCategory.CLOTHING: {
                "primary": ["birefnet-general", "isnet-general-use"],
                "fallback": ["silueta"],
            },
            SubjectCategory.UNKNOWN: {
                "primary": ["isnet-general-use", "birefnet-general"],
                "fallback": ["u2net", "silueta"],
            },
        }

    def select(self, subject_type: str) -> Dict[str, Any]:
        return self.model_configs.get(subject_type, self.model_configs[SubjectCategory.UNKNOWN])


class MultiModelSegmenter:
    """Multi-model segmentation with memory-safe fallbacks (br_08)."""

    _global_birefnet_disabled = False

    def __init__(self):
        self.sessions: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self.available_models: List[str] = []
        self._availability_cache: Dict[str, bool] = {}

        if not MultiModelSegmenter._global_birefnet_disabled:
            total_mem = MemoryManager.get_total_memory_mb()
            if total_mem < 8192:
                logger.warning("Low total RAM (%.0fMB). Disabling BiRefNet globally.", total_mem)
                MultiModelSegmenter._global_birefnet_disabled = True

    def _check_model_availability(self, model_name: str) -> bool:
        if model_name in self._availability_cache:
            return self._availability_cache[model_name]

        if "birefnet" in model_name:
            if MultiModelSegmenter._global_birefnet_disabled:
                self._availability_cache[model_name] = False
                return False
            available_mem = MemoryManager.get_available_memory_mb()
            if available_mem < 2048:
                logger.warning("Low memory (%.0fMB). Disabling %s", available_mem, model_name)
                MultiModelSegmenter._global_birefnet_disabled = True
                self._availability_cache[model_name] = False
                return False

        try:
            session = new_session(model_name)
            self._availability_cache[model_name] = session is not None
            return self._availability_cache[model_name]
        except Exception as exc:
            logger.debug("Model %s not available: %s", model_name, exc)
            self._availability_cache[model_name] = False
            return False

    def _get_session(self, model_name: str):
        with self._lock:
            if model_name not in self.sessions:
                if not self._check_model_availability(model_name):
                    return None
                try:
                    self.sessions[model_name] = new_session(model_name)
                    if model_name not in self.available_models:
                        self.available_models.append(model_name)
                except Exception as exc:
                    logger.warning("Model %s failed: %s", model_name, exc)
                    if "birefnet" in model_name:
                        MultiModelSegmenter._global_birefnet_disabled = True
                    return None
            return self.sessions[model_name]

    def _generate_probability_map(
        self,
        image_bytes: bytes,
        model_name: str,
        orig_size: Tuple[int, int],
        config: ProcessingConfig,
    ) -> Optional[np.ndarray]:
        _ensure_rembg()
        session = self._get_session(model_name)
        if session is None:
            return None

        try:
            img = Image.open(io.BytesIO(image_bytes))
            w, h = img.size
            max_dim = config.max_rembg_dimension
            if "birefnet" in model_name:
                max_dim = min(max_dim, 768)
                logger.debug("Using reduced resolution (%dpx) for %s", max_dim, model_name)

            if max(w, h) > max_dim:
                ratio = max_dim / max(w, h)
                img = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=85)
                input_bytes = buf.getvalue()
            else:
                input_bytes = image_bytes

            output_bytes = remove(input_bytes, session=session, alpha_matting=False)
            output_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")

            if max(w, h) > max_dim:
                output_img = output_img.resize(orig_size, Image.Resampling.LANCZOS)

            alpha = np.array(output_img.split()[-1], dtype=np.uint8)
            prob_map = alpha.astype(np.float32) / 255.0

            del output_img, alpha, output_bytes
            return prob_map

        except MemoryError as exc:
            logger.error("Model %s OOM: %s", model_name, exc)
            if "birefnet" in model_name:
                MultiModelSegmenter._global_birefnet_disabled = True
                self._availability_cache[model_name] = False
            return None

        except Exception as exc:
            error_msg = str(exc)
            if "bad allocation" in error_msg or "Failed to allocate" in error_msg or "RUNTIME_EXCEPTION" in error_msg:
                logger.error("Model %s memory allocation failed", model_name)
                if "birefnet" in model_name:
                    MultiModelSegmenter._global_birefnet_disabled = True
                    self._availability_cache[model_name] = False
            else:
                logger.error("Model %s failed: %s", model_name, exc)
            return None

    def segment_with_comparison(
        self,
        image_bytes: bytes,
        model_config: Dict[str, Any],
        orig_size: Tuple[int, int],
        config: ProcessingConfig,
    ) -> Tuple[np.ndarray, str]:
        models_to_try = model_config["primary"] + model_config["fallback"]
        available_models = [m for m in models_to_try if self._check_model_availability(m)]

        if not available_models:
            logger.error("No models available!")
            return None, ""

        best_prob_map = None
        best_model = ""
        best_score = -1
        models_tried = 0

        for model_name in available_models[: config.max_models_to_try]:
            logger.info("Testing %s...", model_name)

            mem_usage = MemoryManager.get_available_memory_mb()
            if mem_usage < 1024:
                logger.warning("Low memory (%.0fMB), stopping model tests", mem_usage)
                break

            prob_map = self._generate_probability_map(image_bytes, model_name, orig_size, config)

            if prob_map is not None:
                models_tried += 1
                coverage = float(np.count_nonzero(prob_map > 0.3)) / prob_map.size
                confidence = float(np.mean(prob_map[prob_map > 0.3])) if np.any(prob_map > 0.3) else 0.0
                score = (coverage * 0.4) + (confidence * 0.6)

                logger.info(
                    "  %s - Coverage: %.1f%%, Confidence: %.1f%%, Score: %.3f",
                    model_name, coverage * 100, confidence * 100, score,
                )

                if score > best_score:
                    best_score = score
                    best_prob_map = prob_map
                    best_model = model_name

                    if score > 0.85:
                        logger.info("  Excellent score (%.3f), stopping model tests", score)
                        break
            else:
                logger.warning("  %s failed, trying next model...", model_name)

            gc.collect()

        if best_prob_map is not None:
            logger.info("Selected best model: %s (score: %.3f, tested %d models)", best_model, best_score, models_tried)
            return best_prob_map, best_model

        return None, ""


class WoodBackgroundRemover:
    """Specialized remover for wood texture backgrounds inside product gaps (br_08)."""

    @staticmethod
    def remove(image_rgba: np.ndarray, fused_prob_map: np.ndarray = None) -> np.ndarray:
        """Remove wood texture background from inside product gaps."""
        if not _HAS_CV2:
            return image_rgba
        gray = cv2.cvtColor(image_rgba[:, :, :3], cv2.COLOR_RGB2GRAY)
        texture_variance = float(np.var(cv2.Laplacian(gray, cv2.CV_64F)))
        if texture_variance < 150:
            return image_rgba

        h, w = image_rgba.shape[:2]
        if h * w > 300000:
            corner_size = min(h, w) // 8
        else:
            corner_size = min(h, w) // 6

        corner_samples = np.concatenate([
            image_rgba[:corner_size, :corner_size, :3].reshape(-1, 3),
            image_rgba[:corner_size, -corner_size:, :3].reshape(-1, 3),
            image_rgba[-corner_size:, :corner_size, :3].reshape(-1, 3),
            image_rgba[-corner_size:, -corner_size:, :3].reshape(-1, 3),
        ])
        bg_color = np.median(corner_samples, axis=0)
        all_pixels = image_rgba[:, :, :3].reshape(-1, 3)
        distances = np.linalg.norm(all_pixels - bg_color, axis=1)
        bg_mask_flat = distances < 70
        bg_mask = bg_mask_flat.reshape(h, w).astype(np.uint8)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        bg_mask = cv2.morphologyEx(bg_mask, cv2.MORPH_OPEN, kernel, iterations=1)
        bg_mask = cv2.morphologyEx(bg_mask, cv2.MORPH_CLOSE, kernel, iterations=1)

        if fused_prob_map is not None and h * w <= 300000:
            product_mask = (fused_prob_map > 0.25).astype(np.uint8) * 255
            num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(product_mask, connectivity=8)
            if num_labels > 1:
                areas = [(i, stats[i, cv2.CC_STAT_AREA]) for i in range(1, num_labels)]
                areas.sort(key=lambda x: x[1], reverse=True)
                if areas:
                    largest_label = areas[0][0]
                    if areas[0][1] > (h * w * 0.05):
                        product_region = (labels == largest_label).astype(np.uint8)
                        product_region = cv2.dilate(product_region, kernel, iterations=1)
                        bg_mask = cv2.bitwise_and(bg_mask, 255 - product_region)

        image_rgba[bg_mask > 0, 3] = 0
        logger.info("    Removed %d wood background pixels", int(np.sum(bg_mask > 0)))
        return image_rgba


class ZoziBackgroundRemover:
    """Full production pipeline orchestrator (br_08 Zozi v20 style)."""

    def __init__(self, config: ProcessingConfig = None):
        self.config = config or ProcessingConfig()
        self.segmenter = MultiModelSegmenter()
        self.model_selector = ModelSelector()
        logger.info("Zozi AI - Pipeline Initialized (Resolution: %dpx)", self.config.max_rembg_dimension)

    def process(self, image_bytes: bytes, background: str = "transparent", output_format: str = "PNG") -> Dict[str, Any]:
        try:
            start_time = time.time()

            input_img, input_np = ImageLoader.load_from_bytes(image_bytes)
            orig_size = input_img.size
            logger.info("Image: %dx%d", orig_size[0], orig_size[1])

            input_np_enhanced = ImageLoader.preprocess_for_segmentation(input_np)
            quality_metrics = QualityAnalyzer.analyze(input_np)

            initial_prob_map = self.segmenter._generate_probability_map(
                image_bytes, "isnet-general-use", orig_size, self.config
            )
            if initial_prob_map is None:
                return {"error": "Initial segmentation failed"}

            initial_mask = (initial_prob_map > 0.3).astype(np.uint8) * 255
            subject_type, subject_metrics = SubjectDetector.detect(input_np_enhanced, initial_mask)
            logger.info("Detected: %s", subject_type)

            model_config = self.model_selector.select(subject_type)
            fused_prob_map, best_model = self.segmenter.segment_with_comparison(
                image_bytes, model_config, orig_size, self.config
            )
            if fused_prob_map is None:
                return {"error": "Segmentation failed - all models failed"}
            logger.info("Best model: %s", best_model)

            h, w = input_np.shape[:2]
            final_rgba = np.zeros((h, w, 4), dtype=np.uint8)
            for i in range(3):
                final_rgba[:, :, i] = (input_np[:, :, i].astype(np.float32) * fused_prob_map).astype(np.uint8)
            final_rgba[:, :, 3] = (fused_prob_map * 255).astype(np.uint8)

            logger.info("Wood background removal...")
            final_rgba = WoodBackgroundRemover.remove(final_rgba, fused_prob_map)

            logger.info("Hole filling...")
            final_rgba = HoleFiller.fill(final_rgba)

            final_img = Image.fromarray(final_rgba, mode="RGBA")
            canvas = Exporter.create_canvas(final_img, background, self.config)
            if background.lower() == "transparent":
                output_format = "PNG"
            encoded, final_format = Exporter.encode(canvas, output_format, self.config)
            elapsed = round(time.time() - start_time, 2)

            logger.info("Completed in %ds | Subject: %s | Model: %s", elapsed, subject_type, best_model)

            return {
                "base64": base64.b64encode(encoded).decode("utf-8"),
                "format": final_format,
                "width": canvas.width,
                "height": canvas.height,
                "processing_time_seconds": elapsed,
                "subject_type": subject_type,
                "best_model": best_model,
                "file_size_kb": round(len(encoded) / 1024, 1),
            }
        finally:
            MemoryManager.cleanup()

