# br_08.py

"""
Zozi AI Image Processor - Production Pipeline v08.0 (BiRefNet Local)
=====================================================================
FEATURES:
1. ✅ BiRefNet via rembg (local, no API)
2. ✅ Memory-safe with automatic fallback
3. ✅ Smart model switching (BiRefNet → ISNet → Silueta)
4. ✅ Advanced post-processing (wood removal, hole filling)
5. ✅ Resolution switcher (1024/1536/2048px)
"""

import io
import os
import sys
import base64
import logging
import time
import threading
import gc
from typing import Tuple, Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from PIL import Image
import numpy as np

# ========================== MEMORY MANAGER ==========================
class MemoryManager:
    @staticmethod
    def cleanup():
        gc.collect()
    
    @staticmethod
    def get_available_memory_mb() -> float:
        try:
            import psutil
            return psutil.virtual_memory().available / 1024 / 1024
        except ImportError:
            return 4096  # Assume 4GB if psutil missing
    
    @staticmethod
    def get_total_memory_mb() -> float:
        try:
            import psutil
            return psutil.virtual_memory().total / 1024 / 1024
        except ImportError:
            return 8192  # Assume 8GB

# ========================== LOGGING ==========================
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ZoziAI")

# ========================== DEPENDENCY CHECK ==========================
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    logger.error("OpenCV not installed. Run: pip install opencv-python")
    sys.exit(1)

try:
    from rembg import remove, new_session
    REMBG_AVAILABLE = True
except ImportError:
    logger.error("rembg not installed. Run: pip install rembg[cpu]")
    sys.exit(1)

# ========================== CONFIGURATION ==========================
@dataclass
class ProcessingConfig:
    max_rembg_dimension: int = 1024
    max_output_dimension: int = 2048
    min_dimension: int = 128
    max_file_size_mb: int = 50
    default_background: str = "transparent"
    default_format: str = "PNG"
    jpeg_quality: int = 95
    png_compression: int = 6
    enable_model_comparison: bool = True
    memory_limit_mb: int = 2048
    max_models_to_try: int = 3

CONFIG = ProcessingConfig()

# ========================== ENUMS ==========================
class SubjectCategory(str, Enum):
    PRODUCT = "product"
    HUMAN = "human"
    CLOTHING = "clothing"
    FOOD = "food"
    UNKNOWN = "unknown"

class FusionStrategy(str, Enum):
    UNION = "union"

# ========================== UTILITY CLASSES ==========================
class ColorSpaceUtils:
    @staticmethod
    def rgb_to_gray(image: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    
    @staticmethod
    def rgb_to_hsv(image: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    
    @staticmethod
    def rgb_to_lab(image: np.ndarray) -> np.ndarray:
        return cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    
    @staticmethod
    def detect_skin_regions(image: np.ndarray) -> np.ndarray:
        hsv = ColorSpaceUtils.rgb_to_hsv(image)
        lower1 = np.array([0, 20, 70], dtype=np.uint8)
        upper1 = np.array([20, 255, 255], dtype=np.uint8)
        lower2 = np.array([160, 20, 70], dtype=np.uint8)
        upper2 = np.array([180, 255, 255], dtype=np.uint8)
        mask1 = cv2.inRange(hsv, lower1, upper1)
        mask2 = cv2.inRange(hsv, lower2, upper2)
        skin_mask = cv2.bitwise_or(mask1, mask2)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        return cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel, iterations=2)

# ========================== STAGE 1 & 2: LOADER & QUALITY ==========================
class ImageLoader:
    @staticmethod
    def load_from_bytes(image_bytes: bytes) -> Tuple[Image.Image, np.ndarray]:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode != 'RGB':
            img = img.convert('RGB')
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
    @staticmethod
    def analyze(image_np: np.ndarray) -> Dict[str, float]:
        gray = ColorSpaceUtils.rgb_to_gray(image_np)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        return {
            'texture_complexity': float(np.var(laplacian)),
            'brightness': float(np.mean(gray)),
        }

# ========================== STAGE 3: SUBJECT DETECTOR ==========================
class SubjectDetector:
    @staticmethod
    def detect(image_np: np.ndarray, initial_mask: np.ndarray) -> Tuple[str, Dict[str, float]]:
        metrics = {}
        
        try:
            skin_mask = ColorSpaceUtils.detect_skin_regions(image_np)
            metrics['skin_ratio'] = np.sum(skin_mask > 0) / skin_mask.size
            
            mask_binary = (initial_mask > 127).astype(np.uint8)
            metrics['coverage'] = np.sum(mask_binary > 0) / mask_binary.size
            
            gray_full = ColorSpaceUtils.rgb_to_gray(image_np)
            full_edges = cv2.Canny(gray_full, 50, 150)
            metrics['edge_density'] = np.sum(full_edges > 0) / full_edges.size
            
            # Classification
            if metrics.get('skin_ratio', 0) < 0.05:
                subject_type = SubjectCategory.CLOTHING if metrics.get('edge_density', 0) > 0.1 else SubjectCategory.PRODUCT
            elif metrics.get('skin_ratio', 0) > 0.15:
                if metrics.get('edge_density', 0) < 0.15:
                    subject_type = SubjectCategory.HUMAN
                else:
                    subject_type = SubjectCategory.CLOTHING
            else:
                subject_type = SubjectCategory.PRODUCT
                
        except Exception as e:
            logger.warning(f"Subject detection failed: {e}, using default")
            subject_type = SubjectCategory.PRODUCT
        
        return subject_type, metrics

# ========================== STAGE 4 & 5: MODEL SELECTOR & SEGMENTER ==========================
class ModelSelector:
    def __init__(self):
        self.model_configs = {
            SubjectCategory.PRODUCT: {
                'primary': ['birefnet-general', 'isnet-general-use'],
                'fallback': ['u2net', 'silueta'],
            },
            SubjectCategory.HUMAN: {
                'primary': ['birefnet-general', 'isnet-general-use'],
                'fallback': ['silueta'],
            },
            SubjectCategory.CLOTHING: {
                'primary': ['birefnet-general', 'isnet-general-use'],
                'fallback': ['silueta'],
            },
            SubjectCategory.UNKNOWN: {
                'primary': ['isnet-general-use', 'birefnet-general'],
                'fallback': ['u2net', 'silueta'],
            }
        }
    
    def select(self, subject_type: str) -> Dict[str, Any]:
        return self.model_configs.get(subject_type, self.model_configs[SubjectCategory.UNKNOWN])

class MultiModelSegmenter:
    # ✅ CRITICAL: Class-level variable persists across ALL pipeline instances
    _global_birefnet_disabled = False
    
    def __init__(self):
        self.sessions = {}
        self._lock = threading.Lock()
        self.available_models = []
        self._availability_cache = {}
        
        # ✅ PREVENTATIVE CHECK: Disable BiRefNet if system RAM is too low
        if not MultiModelSegmenter._global_birefnet_disabled:
            total_mem = MemoryManager.get_total_memory_mb()
            if total_mem < 8192:  # Less than 8GB total RAM
                logger.warning(f"⚠ System has low total RAM ({total_mem:.0f}MB). Disabling BiRefNet globally.")
                MultiModelSegmenter._global_birefnet_disabled = True
    
    def _check_model_availability(self, model_name: str) -> bool:
        if model_name in self._availability_cache:
            return self._availability_cache[model_name]
        
        # ✅ Skip BiRefNet if globally disabled
        if 'birefnet' in model_name:
            if MultiModelSegmenter._global_birefnet_disabled:
                logger.debug(f"Skipping {model_name} (GLOBALLY disabled)")
                self._availability_cache[model_name] = False
                return False
            
            available_mem = MemoryManager.get_available_memory_mb()
            if available_mem < 2048:
                logger.warning(f"⚠ Low memory ({available_mem:.0f}MB). Disabling {model_name}")
                MultiModelSegmenter._global_birefnet_disabled = True
                self._availability_cache[model_name] = False
                return False
        
        try:
            session = new_session(model_name)
            self._availability_cache[model_name] = session is not None
            return self._availability_cache[model_name]
        except Exception as e:
            logger.debug(f"Model {model_name} not available: {e}")
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
                except Exception as e:
                    logger.warning(f"Model {model_name} failed: {e}")
                    if 'birefnet' in model_name:
                        MultiModelSegmenter._global_birefnet_disabled = True
                    return None
            return self.sessions[model_name]
    
    def _generate_probability_map(self, image_bytes: bytes, model_name: str, 
                                  orig_size: Tuple[int, int], config: ProcessingConfig) -> Optional[np.ndarray]:
        session = self._get_session(model_name)
        if session is None:
            return None
        
        try:
            img = Image.open(io.BytesIO(image_bytes))
            w, h = img.size
            
            # ✅ Use lower resolution for BiRefNet
            max_dim = config.max_rembg_dimension
            if 'birefnet' in model_name:
                max_dim = min(max_dim, 768)
                logger.debug(f"Using reduced resolution ({max_dim}px) for {model_name}")
            
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
            
        except MemoryError as e:
            logger.error(f"    ✗ {model_name} ran out of memory: {e}")
            if 'birefnet' in model_name:
                MultiModelSegmenter._global_birefnet_disabled = True
                self._availability_cache[model_name] = False
                logger.critical(f"    🚨 {model_name} disabled GLOBALLY!")
            return None
            
        except Exception as e:
            error_msg = str(e)
            if "bad allocation" in error_msg or "Failed to allocate" in error_msg or "RUNTIME_EXCEPTION" in error_msg:
                logger.error(f"    ✗ {model_name} memory allocation failed")
                if 'birefnet' in model_name:
                    MultiModelSegmenter._global_birefnet_disabled = True
                    self._availability_cache[model_name] = False
                    logger.critical(f"    🚨 {model_name} disabled GLOBALLY!")
            else:
                logger.error(f"    ✗ {model_name} failed: {e}")
            return None
    
    def segment_with_comparison(self, image_bytes: bytes, model_config: Dict[str, Any],
                                orig_size: Tuple[int, int], config: ProcessingConfig) -> Tuple[np.ndarray, str]:
        models_to_try = model_config['primary'] + model_config['fallback']
        available_models = [m for m in models_to_try if self._check_model_availability(m)]
        
        if not available_models:
            logger.error("No models available!")
            return None, ""
        
        best_prob_map = None
        best_model = ""
        best_score = -1
        models_tried = 0
        
        for model_name in available_models[:config.max_models_to_try]:
            logger.info(f"Testing {model_name}...")
            
            mem_usage = MemoryManager.get_available_memory_mb()
            if mem_usage < 1024:
                logger.warning(f"⚠ Low memory ({mem_usage:.0f}MB), stopping model tests")
                break
            
            prob_map = self._generate_probability_map(image_bytes, model_name, orig_size, config)
            
            if prob_map is not None:
                models_tried += 1
                coverage = np.count_nonzero(prob_map > 0.3) / prob_map.size
                confidence = np.mean(prob_map[prob_map > 0.3]) if np.any(prob_map > 0.3) else 0
                score = (coverage * 0.4) + (confidence * 0.6)
                
                logger.info(f"  {model_name} - Coverage: {coverage*100:.1f}%, Confidence: {confidence*100:.1f}%, Score: {score:.3f}")
                
                if score > best_score:
                    best_score = score
                    best_prob_map = prob_map
                    best_model = model_name
                    
                    if score > 0.85:
                        logger.info(f"  ✓ Excellent score ({score:.3f}), stopping model tests")
                        break
            else:
                logger.warning(f"  ✗ {model_name} failed, trying next model...")
            
            gc.collect()
        
        if best_prob_map is not None:
            logger.info(f"✓ Selected best model: {best_model} (score: {best_score:.3f}, tested {models_tried} models)")
            return best_prob_map, best_model
        
        return None, ""

# ========================== STAGE 6-15: POST-PROCESSING ==========================
class HoleFiller:
    @staticmethod
    def fill(image_rgba: np.ndarray, subject_type: str = None) -> np.ndarray:
        alpha = image_rgba[:, :, 3]
        visible_mask = (alpha > 128).astype(np.uint8) * 255
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        filled_mask = cv2.morphologyEx(visible_mask, cv2.MORPH_CLOSE, kernel, iterations=1)
        holes_filled = cv2.bitwise_and(filled_mask, 255 - visible_mask)
        
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(holes_filled, connectivity=8)
        holes_to_fill = np.zeros_like(holes_filled)
        
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area < 500:
                holes_to_fill[labels == i] = 255
        
        if np.sum(holes_to_fill > 0) > 0:
            image_rgba[holes_to_fill > 0, 3] = 255
            logger.info(f"✓ Filled {np.sum(holes_to_fill > 0)} small holes")
        
        return image_rgba

class WoodBackgroundRemover:
    @staticmethod
    def remove(image_rgba: np.ndarray, prob_map: np.ndarray) -> np.ndarray:
        gray = ColorSpaceUtils.rgb_to_gray(image_rgba[:, :, :3])
        texture_variance = np.var(cv2.Laplacian(gray, cv2.CV_64F))
        
        if texture_variance < 150:
            logger.info("    No wood texture detected - skipping")
            return image_rgba
        
        logger.info("    Wood texture detected - applying smart removal...")
        h, w = image_rgba.shape[:2]
        corner_size = min(h, w) // 6
        
        corner_samples = np.concatenate([
            image_rgba[:corner_size, :corner_size, :3].reshape(-1, 3),
            image_rgba[:corner_size, -corner_size:, :3].reshape(-1, 3),
            image_rgba[-corner_size:, :corner_size, :3].reshape(-1, 3),
            image_rgba[-corner_size:, -corner_size:, :3].reshape(-1, 3)
        ])
        
        bg_color = np.median(corner_samples, axis=0)
        all_pixels = image_rgba[:, :, :3].reshape(-1, 3)
        distances = np.linalg.norm(all_pixels - bg_color, axis=1)
        
        bg_mask_flat = distances < 70
        bg_mask = bg_mask_flat.reshape(h, w).astype(np.uint8)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        bg_mask = cv2.morphologyEx(bg_mask, cv2.MORPH_OPEN, kernel, iterations=2)
        bg_mask = cv2.morphologyEx(bg_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # Protect product area
        product_mask = (prob_map > 0.25).astype(np.uint8) * 255
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(product_mask, connectivity=8)
        
        if num_labels > 1:
            areas = [(i, stats[i, cv2.CC_STAT_AREA]) for i in range(1, num_labels)]
            areas.sort(key=lambda x: x[1], reverse=True)
            
            if areas:
                largest_label = areas[0][0]
                largest_area = areas[0][1]
                
                if largest_area > (h * w * 0.05):
                    product_region = (labels == largest_label).astype(np.uint8)
                    product_region = cv2.dilate(product_region, kernel, iterations=3)
                    bg_mask = cv2.bitwise_and(bg_mask, 255 - product_region)
        
        image_rgba[bg_mask > 0, 3] = 0
        logger.info(f"    ✓ Removed {np.sum(bg_mask > 0)} wood background pixels")
        
        return image_rgba

# ========================== STAGE 16: EXPORTER ==========================
class Exporter:
    @staticmethod
    def create_canvas(final_img: Image.Image, background: str, config: ProcessingConfig) -> Image.Image:
        bg_colors = {"transparent": (0, 0, 0, 0), "white": (255, 255, 255, 255), "black": (0, 0, 0, 255)}
        bg = bg_colors.get(background.lower(), (0, 0, 0, 0))
        
        target_size = min(max(final_img.width, final_img.height), config.max_output_dimension)
        ratio = min(target_size / max(final_img.width, final_img.height), 1.0)
        new_w, new_h = int(final_img.width * ratio), int(final_img.height * ratio)
        resized = final_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        canvas = Image.new("RGBA", (target_size, target_size), bg)
        canvas.paste(resized, ((target_size - new_w) // 2, (target_size - new_h) // 2), resized)
        return canvas
    
    @staticmethod
    def encode(canvas: Image.Image, output_format: str, config: ProcessingConfig) -> Tuple[bytes, str]:
        if output_format.upper() in ("JPEG", "JPG"):
            canvas = canvas.convert("RGB")
            output_format = "JPEG"
            save_kwargs = {"quality": config.jpeg_quality, "optimize": True}
        else:
            output_format = "PNG"
            save_kwargs = {"optimize": True, "compress_level": config.png_compression}
        
        buf = io.BytesIO()
        canvas.save(buf, format=output_format, **save_kwargs)
        return buf.getvalue(), output_format

# ========================== MAIN PIPELINE ==========================
class ZoziBackgroundRemover:
    def __init__(self, config: ProcessingConfig = None):
        self.config = config or CONFIG
        self.segmenter = MultiModelSegmenter()
        self.model_selector = ModelSelector()
        logger.info(f"Zozi AI v20.0 - Pipeline Initialized (Resolution: {self.config.max_rembg_dimension}px)")
    
    def process(self, image_bytes: bytes, background: str = "transparent", output_format: str = "PNG") -> Dict[str, Any]:
        try:
            logger.info("=" * 70)
            logger.info("=== Starting Zozi AI v20.0 ===")
            logger.info("=" * 70)
            
            start_time = time.time()
            
            # STAGE 1: Load
            logger.info("\n[STAGE 1] Loading image...")
            input_img, input_np = ImageLoader.load_from_bytes(image_bytes)
            orig_size = input_img.size
            logger.info(f"✓ Image: {orig_size[0]}x{orig_size[1]}")
            
            # STAGE 2: Pre-process
            logger.info("\n[STAGE 2] Pre-processing (CLAHE)...")
            input_np_enhanced = ImageLoader.preprocess_for_segmentation(input_np)
            quality_metrics = QualityAnalyzer.analyze(input_np)
            
            # STAGE 3: Subject Detection
            logger.info("\n[STAGE 3] Subject detection...")
            initial_prob_map = self.segmenter._generate_probability_map(
                image_bytes, 'isnet-general-use', orig_size, self.config
            )
            if initial_prob_map is None:
                return {"error": "Initial segmentation failed"}
            
            initial_mask = (initial_prob_map > 0.3).astype(np.uint8) * 255
            subject_type, subject_metrics = SubjectDetector.detect(input_np_enhanced, initial_mask)
            logger.info(f"✓ Detected: {subject_type}")
            
            # STAGE 4: Model Selection
            logger.info("\n[STAGE 4] Model selection...")
            model_config = self.model_selector.select(subject_type)
            
            # STAGE 5: Multi-Model Segmentation
            logger.info("\n[STAGE 5] Multi-model segmentation...")
            fused_prob_map, best_model = self.segmenter.segment_with_comparison(
                image_bytes, model_config, orig_size, self.config
            )
            if fused_prob_map is None:
                return {"error": "Segmentation failed - all models failed"}
            logger.info(f"✓ Best model: {best_model}")
            
            # STAGE 6: Composition
            logger.info("\n[STAGE 6] Composition...")
            h, w = input_np.shape[:2]
            final_rgba = np.zeros((h, w, 4), dtype=np.uint8)
            
            for i in range(3):
                final_rgba[:, :, i] = (input_np[:, :, i].astype(np.float32) * fused_prob_map).astype(np.uint8)
            
            final_rgba[:, :, 3] = (fused_prob_map * 255).astype(np.uint8)
            
            # STAGE 7: Wood Background Removal
            logger.info("\n[STAGE 7] Wood background removal...")
            final_rgba = WoodBackgroundRemover.remove(final_rgba, fused_prob_map)
            
            # STAGE 8: Hole Filling
            logger.info("\n[STAGE 8] Hole filling...")
            final_rgba = HoleFiller.fill(final_rgba, subject_type)
            
            # STAGE 9: Export
            logger.info("\n[STAGE 9] Exporting...")
            final_img = Image.fromarray(final_rgba, mode="RGBA")
            canvas = Exporter.create_canvas(final_img, background, self.config)
            
            if background.lower() == "transparent":
                output_format = "PNG"
            
            encoded, final_format = Exporter.encode(canvas, output_format, self.config)
            elapsed = round(time.time() - start_time, 2)
            
            logger.info("\n" + "=" * 70)
            logger.info(f"✅ COMPLETED in {elapsed}s")
            logger.info(f"Subject: {subject_type} | Model: {best_model}")
            logger.info(f"Resolution: {self.config.max_rembg_dimension}px")
            logger.info("=" * 70)
            
            return {
                "base64": base64.b64encode(encoded).decode("utf-8"),
                "format": final_format,
                "width": canvas.width,
                "height": canvas.height,
                "processing_time_seconds": elapsed,
                "subject_type": subject_type,
                "best_model": best_model,
                "file_size_kb": round(len(encoded) / 1024, 1)
            }
        finally:
            MemoryManager.cleanup()

# ========================== CONVENIENCE FUNCTIONS ==========================
def process_product_image(image_bytes: bytes, background: str = "transparent", output_format: str = "PNG") -> Dict[str, Any]:
    remover = ZoziBackgroundRemover()
    return remover.process(image_bytes, background, output_format)

# ========================== MAIN ==========================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Zozi AI Background Remover v20.0")
    parser.add_argument("--input", "-i", help="Input folder", default="./image")
    parser.add_argument("--output", "-o", help="Output folder", default="./output_br_08")
    parser.add_argument("--background", "-b", help="Background color", default="transparent")
    parser.add_argument("--format", "-f", help="Output format", default="PNG")
    parser.add_argument("--resolution", "-r", help="Max dimension (1024, 1536, or 2048)", type=int, default=1024, choices=[1024, 1536, 2048])
    parser.add_argument("--no-comparison", action="store_true", help="Disable model comparison (faster)")
    args = parser.parse_args()
    
    CONFIG.max_rembg_dimension = args.resolution
    CONFIG.enable_model_comparison = not args.no_comparison
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
        image_files.extend(input_dir.glob(ext))
    
    if not image_files:
        print(f"\n❌ No images found in '{input_dir}' folder")
        sys.exit(1)
    
    print(f"\n📸 Found {len(image_files)} image(s) to process")
    print(f"📐 Resolution: {args.resolution}px")
    print(f"🔄 Model comparison: {'Enabled' if CONFIG.enable_model_comparison else 'Disabled'}\n")
    
    successful = 0
    failed = 0
    
    for idx, img_path in enumerate(image_files, 1):
        print(f"\n[{idx}/{len(image_files)}] Processing: {img_path.name}")
        print("-" * 70)
        
        try:
            with open(img_path, 'rb') as f:
                image_bytes = f.read()
            
            result = process_product_image(image_bytes, args.background, args.format)
            
            if 'error' in result:
                print(f"❌ Error: {result['error']}")
                failed += 1
                continue
            
            ext = 'jpg' if args.format.lower() == 'jpeg' else args.format.lower()
            output_path = output_dir / f"{img_path.stem}_br_08.{ext}"
            
            with open(output_path, 'wb') as f:
                f.write(base64.b64decode(result['base64']))
            
            print(f"✅ Success! Subject: {result.get('subject_type')} | Model: {result.get('best_model')}")
            print(f"Saved: {output_path.name}")
            successful += 1
            
        except Exception as e:
            print(f"❌ Failed: {str(e)}")
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"✅ Successful: {successful} | ❌ Failed: {failed}")
    print(f"{'='*70}")