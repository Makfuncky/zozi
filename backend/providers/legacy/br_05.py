# br_05.py

"""
Zozi AI Background Remover - Clean Commercial Pipeline v05.0
============================================================
PHILOSOPHY: Less is More. 
The AI model does 99% of the work perfectly. We only do 1% cleanup.
- No destructive text/ground slicing
- No aggressive geometric hardening
- Pure, high-fidelity edge refinement
- Respects the original model mask

Usage: python bg_remover.py
Input: ./image/
Output: ./output/
"""

import io
import os
import sys
import time
import logging
import gc
from typing import Tuple, Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, field


class _LazyNumpy:
    """Lazy proxy for numpy to avoid top-level import."""
    def __getattr__(self, name):
        import numpy as np
        return getattr(np, name)


class _LazyPIL:
    """Lazy proxy for PIL.Image to avoid top-level import."""
    def __getattr__(self, name):
        from PIL import Image
        return getattr(Image, name)


np = _LazyNumpy()
Image = _LazyPIL()

# ========================== LOGGING ==========================
class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m', 'INFO': '\033[32m',
        'WARNING': '\033[33m', 'ERROR': '\033[31m', 'CRITICAL': '\033[41m',
    }
    RESET = '\033[0m'
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)

def setup_logger(name: str = "ZoziAI", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(ColoredFormatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S'))
        logger.addHandler(handler)
    return logger

logger = setup_logger()

# ========================== DEPENDENCY CHECK ==========================
class Deps:
    cv2 = False
    guided_filter = False
    remove = None
    new_session = None
    
    @classmethod
    def check(cls):
        try: import numpy; logger.info("✓ NumPy available")
        except ImportError: logger.error("✗ NumPy required"); sys.exit(1)
        
        try: from PIL import Image; logger.info("✓ Pillow available")
        except ImportError: logger.error("✗ Pillow required"); sys.exit(1)
        
        try:
            import cv2
            cls.cv2 = True
            logger.info(f"✓ OpenCV {cv2.__version__} available")
            try:
                from cv2 import ximgproc
                cls.guided_filter = True
                logger.info("✓ Guided Filter available")
            except: pass
        except ImportError: logger.warning("✗ OpenCV not available")
        
        try:
            from rembg import remove, new_session
            cls.rembg = True
            cls.remove = remove
            cls.new_session = new_session
            logger.info("✓ rembg available")
        except ImportError: logger.error("✗ rembg required"); sys.exit(1)

Deps.check()

if Deps.cv2:
    import cv2

# ========================== CONFIGURATION ==========================
@dataclass
class Config:
    # Prioritize isnet-general-use, it's the best for products
    models: List[str] = field(default_factory=lambda: ['isnet-general-use', 'u2net'])
    max_dimension: int = 2048 # Higher resolution = better edges
    png_compression: int = 6

CONFIG = Config()

# ========================== CLEAN EDGE REFINER ==========================
class CleanEdgeRefiner:
    """Applies a VERY gentle touch to the raw AI mask."""
    
    @staticmethod
    def refine(image_np: np.ndarray, alpha: np.ndarray) -> np.ndarray:
        if not Deps.cv2:
            return alpha
            
        # 1. Fix light product edge fringing (white edges on white backgrounds)
        # If the AI left a 1-2px gap of semi-transparent pixels, push them to opaque
        # ONLY do this if they are directly adjacent to the opaque foreground
        binary_fg = (alpha > 0.95).astype(np.uint8) * 255
        if np.sum(binary_fg) > 0:
            # Dilate foreground by 2px to find the "safe zone"
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            safe_zone = cv2.dilate(binary_fg, kernel, iterations=2)
            
            # If a pixel is semi-transparent (0.3 to 0.9) AND inside the safe zone, make it opaque
            # This fixes the "white halo" on light products without destroying soft outer edges
            semi_inside = (alpha > 0.3) & (alpha < 0.95) & (safe_zone > 0)
            alpha[semi_inside] = 1.0
            
        # 2. Gentle Edge Smoothing (Guided Filter)
        # This smooths out the 1px staircase jitters without destroying the shape
        if Deps.guided_filter:
            try:
                guide = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR).astype(np.float32) / 255.0
                alpha_f = alpha.astype(np.float32)
                # Very small radius and low eps preserves exact edges
                refined = cv2.ximgproc.guidedFilter(guide, alpha_f, radius=4, eps=0.0001)
                alpha = np.clip(refined, 0, 1)
            except Exception:
                pass # Fallback to raw if guided filter fails
                
        # 3. Pure background cleanup (remove ghosting)
        # Any pixel far from the subject that is slightly transparent should be 100% transparent
        # Find edge pixels
        binary_final = (alpha > 0.5).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        near_edge = cv2.dilate(binary_final, kernel, iterations=5)
        
        # If a pixel is outside the 5px edge zone and is less than 10% opaque, zero it out
        ghost_mask = (near_edge == 0) & (alpha < 0.1)
        alpha[ghost_mask] = 0.0
        
        return alpha

# ========================== MAIN PROCESSOR ==========================
class BackgroundRemover:
    def __init__(self, config: Config = None):
        self.config = config or CONFIG
        self.session = None
        self.model_name = None
        self.stats = {'total_processed': 0, 'total_time': 0, 'errors': 0}
    
    def _load_best_model(self):
        """Load the single best available model."""
        for model_name in self.config.models:
            try:
                logger.info(f"Loading model: {model_name}...")
                self.session = Deps.new_session(model_name)
                self.model_name = model_name
                logger.info(f"✓ Using {model_name}")
                return True
            except Exception as e:
                logger.warning(f"✗ {model_name} unavailable")
        return False

    def process_file(self, input_path: str, output_path: str) -> Dict[str, Any]:
        start_time = time.time()
        result = {'input': input_path, 'output': output_path, 'success': False, 'time_seconds': 0}
        
        try:
            logger.info(f"Processing: {Path(input_path).name}")
            
            # 1. Load
            img = Image.open(input_path).convert('RGB')
            img_np = np.array(img)
            h, w = img_np.shape[:2]
            
            # 2. Resize for model (keep high res if possible)
            img_resized, ratio = img, 1.0
            if max(w, h) > self.config.max_dimension:
                ratio = self.config.max_dimension / max(w, h)
                new_w, new_h = int(w * ratio), int(h * ratio)
                img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
            buf = io.BytesIO()
            img_resized.save(buf, format="PNG")
            input_bytes = buf.getvalue()
            
            # 3. Run AI Model (Pure extraction)
            output_bytes = Deps.remove(input_bytes, session=self.session, alpha_matting=False)
            out_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
            
            if ratio < 1.0:
                out_img = out_img.resize((w, h), Image.Resampling.LANCZOS)
                
            raw_alpha = np.array(out_img.split()[-1]).astype(np.float32) / 255.0
            
            # 4. Clean Refinement (No destruction)
            final_alpha = CleanEdgeRefiner.refine(img_np, raw_alpha)
            
            # 5. Final strict cleanup for pure transparent background
            final_alpha[final_alpha < 0.02] = 0.0
            final_alpha[final_alpha > 0.98] = 1.0
            
            # 6. Compose & Save
            alpha_uint8 = np.clip(final_alpha * 255, 0, 255).astype(np.uint8)
            result_img = Image.fromarray(np.dstack([img_np, alpha_uint8]), mode='RGBA')
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            result_img.save(output_path, "PNG", compress_level=self.config.png_compression)
            
            elapsed = time.time() - start_time
            result.update({'success': True, 'time_seconds': round(elapsed, 2)})
            self.stats['total_processed'] += 1
            self.stats['total_time'] += elapsed
            
            logger.info(f"  ✅ Done ({elapsed:.2f}s)\n")
            
        except Exception as e:
            logger.error(f"  ❌ Failed: {e}\n")
            result['error'] = str(e)
            self.stats['errors'] += 1
            
        return result
    
    def process_folder(self, input_folder: str, output_folder: str) -> List[Dict[str, Any]]:
        input_path = Path(input_folder)
        output_path = Path(output_folder)
        
        if not input_path.exists():
            logger.error(f"Input folder not found: {input_folder}"); return []
            
        supported_ext = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
        image_files = [f for f in input_path.iterdir() if f.is_file() and f.suffix.lower() in supported_ext]
        
        if not image_files:
            logger.warning(f"No images found in {input_folder}"); return []
            
        logger.info(f"\nFound {len(image_files)} images to process")
        logger.info(f"Input:  {input_folder}")
        logger.info(f"Output: {output_folder}\n")
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        if not self._load_best_model():
            logger.error("No models could be loaded!"); return []
            
        results = []
        for img_file in sorted(image_files):
            out_file = output_path / f"{img_file.stem}.png"
            results.append(self.process_file(str(img_file), str(out_file)))
            gc.collect()
            
        self._print_summary(results)
        return results
    
    def _print_summary(self, results: List[Dict[str, Any]]):
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        avg_time = np.mean([r['time_seconds'] for r in successful]) if successful else 0
        
        logger.info(f"{'='*60}")
        logger.info(f"SUMMARY: {len(successful)} Success, {len(failed)} Failed")
        logger.info(f"Avg Time: {avg_time:.2f}s | Total Time: {self.stats['total_time']:.2f}s")
        logger.info(f"{'='*60}\n")

# ========================== SIMPLE TEST CODE ==========================
def main():
    INPUT_FOLDER = "./image"
    OUTPUT_FOLDER = "./output_br_05"
    
    if not os.path.exists(INPUT_FOLDER):
        print(f"\n❌ Input folder not found: {INPUT_FOLDER}\n"); return
        
    supported_ext = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
    image_count = len([f for f in os.listdir(INPUT_FOLDER) if Path(f).suffix.lower() in supported_ext])
    
    if image_count == 0:
        print(f"\n❌ No images found in: {INPUT_FOLDER}\n"); return
        
    print(f"\n{'='*60}")
    print("  ZOZI AI BACKGROUND REMOVER 05.0")
    print("  Clean & Pure Pipeline")
    print(f"{'='*60}")
    print(f"  Input:  {INPUT_FOLDER} ({image_count} images)")
    print(f"  Output: {OUTPUT_FOLDER}")
    print(f"{'='*60}\n")
    
    processor = BackgroundRemover()
    results = processor.process_folder(INPUT_FOLDER, OUTPUT_FOLDER)
    
    if results:
        success_count = sum(1 for r in results if r['success'])
        print(f"✅ All {success_count} images processed successfully!\n" if success_count == len(results) else f"⚠️  {success_count}/{len(results)} images processed successfully\n")

if __name__ == "__main__":
    main()