# Combined Python Code

This file contains the combined source code from the project.

---

## 📄 br_05.py

```python
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

import numpy as np
from PIL import Image

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
```

---

## 📄 br_06.py

```python
# br_06.py

"""
Zozi AI Background Remover - Precision Geometry Pipeline v06.1
==============================================================
PRECISION FIXES:
1. ✅ Micro-smooth + Guided Filter edge snapping (No jagged edges)
2. ✅ Geometric Hand Removal (Deletes blobs attached to product if no face is at top)
3. ✅ Mathematically Perfect Flood-Fill Hole Fixer (Fixed OpenCV mask reuse bug)
4. ✅ Directional Thin-Part Handler (Reconnects watchbands safely)
5. ✅ Safe Human Mode (Bypasses product tools, fixes eye hollows softly)

Usage: python br_06.py
Input: ./image/
Output: ./output_br_06/
"""

import io
import os
import sys
import time
import logging
import gc
from typing import Tuple, Dict, Any, List
from pathlib import Path
from dataclasses import dataclass, field

import numpy as np
from PIL import Image

# ========================== LOGGING ==========================
class ColoredFormatter(logging.Formatter):
    COLORS = {'DEBUG': '\033[36m', 'INFO': '\033[32m', 'WARNING': '\033[33m', 'ERROR': '\033[31m'}
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
    models: List[str] = field(default_factory=lambda: ['isnet-general-use', 'u2net'])
    max_dimension: int = 2048
    png_compression: int = 6

CONFIG = Config()

# ========================== 1. SCENE GEOMETRY ANALYZER ==========================
class SceneAnalyzer:
    """Uses pure geometry to determine if it's a human or isolated product."""
    
    @staticmethod
    def is_human_photo(alpha: np.ndarray) -> bool:
        """If there is foreground in the top 25% of the image, it's a human (head)."""
        h, w = alpha.shape
        top_region = alpha[:int(h * 0.25), :]
        foreground_ratio = np.sum(top_region > 0.5) / top_region.size
        return foreground_ratio > 0.01

# ========================== 2. GEOMETRIC HAND REMOVER ==========================
class HandRemover:
    """Removes hands by shape, not color. If no head, secondary blobs attached to main product are hands."""
    
    @staticmethod
    def remove_if_isolated(alpha_mask: np.ndarray) -> np.ndarray:
        contours, _ = cv2.findContours(alpha_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours or len(contours) <= 1:
            return alpha_mask # Nothing to remove
            
        # Sort by area, largest is the product
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        main_product = contours[0]
        main_area = cv2.contourArea(main_product)
        
        # Create mask of just the main product
        main_mask = np.zeros_like(alpha_mask)
        cv2.drawContours(main_mask, [main_product], -1, 255, -1)
        
        # Dilate main product by 30px. This is the "danger zone".
        # Any other object inside this zone is likely a hand holding it.
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (30, 30))
        danger_zone = cv2.dilate(main_mask, kernel, iterations=1)
        
        removed = False
        for i in range(1, len(contours)):
            cnt = contours[i]
            area = cv2.contourArea(cnt)
            
            # If secondary object is reasonably sized and overlaps the danger zone
            if 100 < area < main_area * 0.5:
                cnt_mask = np.zeros_like(alpha_mask)
                cv2.drawContours(cnt_mask, [cnt], -1, 255, -1)
                
                overlap = np.sum((cnt_mask > 0) & (danger_zone > 0))
                if overlap > 0:
                    alpha_mask[cnt_mask > 0] = 0
                    removed = True
                    
        if removed:
            logger.info("    ✓ Removed isolated hand (geometric)")
        return alpha_mask

# ========================== 3. FLOOD FILL HOLE FIXER (FIXED v06.1) ==========================
class HoleFiller:
    """
    Fills internal holes mathematically perfectly.
    FIX: Uses a 1-pixel padding to guarantee all external background is connected,
    preventing the OpenCV mask reuse bug and edge-touching traps.
    """
    
    @staticmethod
    def fill(alpha_mask: np.ndarray) -> np.ndarray:
        # Ensure strict binary mask (0 or 255)
        binary_mask = (alpha_mask > 128).astype(np.uint8) * 255
        h, w = binary_mask.shape
        
        # 1. Pad the mask with a 1-pixel border of 0s (background).
        # This guarantees that ALL external background is connected to the (0,0) coordinate.
        padded = np.zeros((h + 2, w + 2), dtype=np.uint8)
        padded[1:h+1, 1:w+1] = binary_mask
        
        # 2. Create a FRESH floodFill mask (must be 2 pixels larger than the padded image)
        ff_mask = np.zeros((h + 4, w + 4), dtype=np.uint8)
        
        # 3. Flood fill from the top-left corner (0,0) with value 128.
        # This will fill ALL external background because it's connected via the padding.
        cv2.floodFill(padded, ff_mask, (0, 0), 128)
        
        # 4. Extract the original image bounds.
        # Any pixel that is STILL 0 inside these bounds is mathematically proven to be an internal hole.
        internal_holes = (padded[1:h+1, 1:w+1] == 0)
        
        filled_count = np.sum(internal_holes)
        
        # Only fill if there's a significant number of hole pixels (avoid AI noise)
        if filled_count > 50: 
            binary_mask[internal_holes] = 255
            logger.info(f"    ✓ Filled internal holes ({filled_count}px)")
        elif filled_count > 0:
            logger.debug(f"    ⓘ Ignored micro-holes ({filled_count}px)")
            
        return binary_mask

# ========================== 4. DIRECTIONAL THIN PART HANDLER ==========================
class ThinPartHandler:
    """Reconnects broken thin parts (watchbands) using directional brushes."""
    
    @staticmethod
    def handle(alpha_mask: np.ndarray, original_alpha_f: np.ndarray) -> np.ndarray:
        # Vertical brush to fix vertical breaks (watchbands)
        kern_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 5))
        closed_v = cv2.morphologyEx(alpha_mask, cv2.MORPH_CLOSE, kern_v, iterations=1)
        
        # Horizontal brush to fix horizontal breaks (cables)
        kern_h = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 1))
        closed_h = cv2.morphologyEx(alpha_mask, cv2.MORPH_CLOSE, kern_h, iterations=1)
        
        # SAFETY: Only apply reconnection if the original AI mask was at least slightly opaque there.
        # This strictly prevents connecting two separate objects across pure background.
        safe_reconnect = (original_alpha_f > 0.05)
        final = np.where(safe_reconnect & ((closed_v > 0) | (closed_h > 0)), 255, alpha_mask)
        
        reconnected = np.sum((final > 0) & (alpha_mask == 0))
        if reconnected > 20:
            logger.info(f"    ✓ Reconnected thin parts ({reconnected}px)")
            
        return final

# ========================== 5. SAFE HUMAN PRESERVER ==========================
class HumanPreserver:
    """Fixes human issues (hollow eyes) WITHOUT destroying hair/edges."""
    
    @staticmethod
    def fix_hollows(alpha_f: np.ndarray) -> np.ndarray:
        # If a pixel is completely transparent (0), but entirely surrounded by opaque pixels,
        # it's a hollow (like an eye socket).
        solid_mask = (alpha_f > 0.8).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        
        # Dilate the solid areas by 2px
        dilated = cv2.dilate(solid_mask, kernel, iterations=1)
        
        # Find hollows: original was transparent, but dilated solid area covers it
        hollows = (alpha_f < 0.1) & (dilated > 0)
        
        if np.sum(hollows) > 10:
            # Fill softly to avoid square rigid shapes
            alpha_f[hollows] = 0.85
            logger.info("    ✓ Soft-filled human hollows (eyes/face)")
            
        return alpha_f

# ========================== EDGE REFINER ==========================
class EdgeRefiner:
    """Micro-smooths staircase jitters, then snaps perfectly to RGB edges."""
    
    @staticmethod
    def refine(image_np: np.ndarray, alpha_f: np.ndarray) -> np.ndarray:
        if not Deps.cv2:
            return alpha_f
            
        # Fix light-product white fringing (push semi-transparent inside the safe zone to 1.0)
        binary_fg = (alpha_f > 0.95).astype(np.uint8) * 255
        if np.sum(binary_fg) > 0:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            safe_zone = cv2.dilate(binary_fg, kernel, iterations=2)
            semi_inside = (alpha_f > 0.3) & (alpha_f < 0.95) & (safe_zone > 0)
            alpha_f[semi_inside] = 1.0
            
        # Step 1: Micro-blur to remove 1px staircase jaggies
        alpha_blurred = cv2.GaussianBlur(alpha_f, (3, 3), 0.8)
        
        # Step 2: Guided Filter to snap the blur back to the actual RGB edges of the image
        if Deps.guided_filter:
            try:
                guide = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR).astype(np.float32) / 255.0
                refined = cv2.ximgproc.guidedFilter(guide, alpha_blurred, radius=6, eps=0.0001)
                alpha_f = np.clip(refined, 0, 1)
            except Exception:
                alpha_f = alpha_blurred # Fallback to just the blur
                
        # Remove far-away background ghosting
        binary_final = (alpha_f > 0.5).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        near_edge = cv2.dilate(binary_final, kernel, iterations=6)
        ghost_mask = (near_edge == 0) & (alpha_f < 0.1)
        alpha_f[ghost_mask] = 0.0
        
        return alpha_f

# ========================== MAIN PROCESSOR ==========================
class BackgroundRemover:
    def __init__(self, config: Config = None):
        self.config = config or CONFIG
        self.session = None
        self.model_name = None
        self.stats = {'total_processed': 0, 'total_time': 0, 'errors': 0}
    
    def _load_best_model(self):
        for model_name in self.config.models:
            try:
                logger.info(f"Loading model: {model_name}...")
                self.session = Deps.new_session(model_name)
                self.model_name = model_name
                logger.info(f"✓ Using {model_name}\n")
                return True
            except Exception:
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
            
            img_resized, ratio = img, 1.0
            if max(w, h) > self.config.max_dimension:
                ratio = self.config.max_dimension / max(w, h)
                new_w, new_h = int(w * ratio), int(h * ratio)
                img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
            buf = io.BytesIO()
            img_resized.save(buf, format="PNG")
            input_bytes = buf.getvalue()
            
            # 2. Base AI Extraction
            output_bytes = Deps.remove(input_bytes, session=self.session, alpha_matting=False)
            out_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
            
            if ratio < 1.0:
                out_img = out_img.resize((w, h), Image.Resampling.LANCZOS)
                
            raw_alpha_f = np.array(out_img.split()[-1]).astype(np.float32) / 255.0
            
            # 3. Scene Analysis
            is_human = SceneAnalyzer.is_human_photo(raw_alpha_f)
            
            # 4. Branching Logic
            if is_human:
                logger.info("  -> Mode: HUMAN (Preserving features, skipping product tools)")
                # Fix eye/face hollows safely
                alpha_f = HumanPreserver.fix_hollows(raw_alpha_f)
            else:
                logger.info("  -> Mode: PRODUCT")
                # Convert to uint8 mask for morphological operations
                alpha_mask = (raw_alpha_f > 0.5).astype(np.uint8) * 255
                
                # Remove isolated hands holding the product
                alpha_mask = HandRemover.remove_if_isolated(alpha_mask)
                
                # Fill holes (watch faces, camera lenses) - FIXED v06.1
                alpha_mask = HoleFiller.fill(alpha_mask)
                
                # Reconnect thin parts (watchbands)
                alpha_mask = ThinPartHandler.handle(alpha_mask, raw_alpha_f)
                
                # Convert back to float for edge refinement
                alpha_f = alpha_mask.astype(np.float32) / 255.0
            
            # 5. Final Edge Refinement (Applies perfectly to both Human and Product)
            alpha_f = EdgeRefiner.refine(img_np, alpha_f)
            
            # 6. Final strict cleanup
            alpha_f[alpha_f < 0.02] = 0.0
            alpha_f[alpha_f > 0.98] = 1.0
            
            # 7. Save
            alpha_uint8 = np.clip(alpha_f * 255, 0, 255).astype(np.uint8)
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
            
        logger.info(f"Found {len(image_files)} images\n")
        output_path.mkdir(parents=True, exist_ok=True)
        
        if not self._load_best_model():
            logger.error("No models could be loaded!"); return []
            
        results = []
        for img_file in sorted(image_files):
            out_file = output_path / f"{img_file.stem}.png"
            results.append(self.process_file(str(img_file), str(out_file)))
            gc.collect()
            
        successful = [r for r in results if r['success']]
        avg_time = np.mean([r['time_seconds'] for r in successful]) if successful else 0
        logger.info(f"{'='*60}\nSUMMARY: {len(successful)}/{len(results)} Success | Avg: {avg_time:.2f}s\n{'='*60}")
        return results

# ========================== SIMPLE TEST CODE ==========================
def main():
    INPUT_FOLDER = "./image"
    OUTPUT_FOLDER = "./output_br_06"
    
    if not os.path.exists(INPUT_FOLDER):
        print(f"\n❌ Input folder not found: {INPUT_FOLDER}\n"); return
        
    supported_ext = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
    image_count = len([f for f in os.listdir(INPUT_FOLDER) if Path(f).suffix.lower() in supported_ext])
    
    if image_count == 0:
        print(f"\n❌ No images found in: {INPUT_FOLDER}\n"); return
        
    print(f"\n{'='*60}")
    print("  ZOZI AI BACKGROUND REMOVER v06.1")
    print("  Precision Geometry Pipeline (Fixed Hole Filler)")
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
```

---

## 📄 br_08.py

```python
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
```

---

## 📄 br_11.py

```python
# br_11.py

"""
Zozi AI Image Processor - Ultimate Pipeline v11.0
=====================================================
SPECIFICALLY DESIGNED TO FIX:
1. Wood/texture remaining inside product gaps (e.g., bras, bikinis)
2. Background remaining in the middle of the product
3. Black spots/dark fringes after background removal
4. Trailing/jagged fuzzy edges

ARCHITECTURE:
- AI Segmentation (BiRefNet / ISNet)
- Edge Shaving (Erosion + Blur) -> Fixes trailing edges
- Global Color Bleed (K-Means Border Sampling) -> Fixes wood inside gaps
- Artifact Isolation -> Fixes floating dust
- Pure Alpha Composition -> Fixes black spots (NO premultiplication)
"""

import io
import os
import sys
import base64
import logging
import time
import threading
import gc
from typing import Tuple, Dict, Any
from pathlib import Path
from dataclasses import dataclass
from PIL import Image
import numpy as np
import cv2

# ========================== LOGGING ==========================
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ZoziAI-v11")

# ========================== CONFIGURATION ==========================
@dataclass
class ProcessingConfig:
    max_rembg_dimension: int = 1024
    max_output_dimension: int = 2048

CONFIG = ProcessingConfig()

# ========================== MEMORY MANAGER ==========================
class MemoryManager:
    @staticmethod
    def cleanup():
        gc.collect()

# ========================== AI SEGMENTER ==========================
class AISegmenter:
    _birefnet_disabled = False
    _sessions = {}
    _lock = threading.Lock()

    @classmethod
    def _get_session(cls, model_name: str):
        if 'birefnet' in model_name and cls._birefnet_disabled:
            return None
        with cls._lock:
            if model_name not in cls._sessions:
                try:
                    from rembg import new_session
                    cls._sessions[model_name] = new_session(model_name)
                except Exception as e:
                    logger.warning(f"Failed to load {model_name}: {e}")
                    if 'birefnet' in model_name:
                        cls._birefnet_disabled = True
                    return None
            return cls._sessions[model_name]

    @classmethod
    def generate_alpha(cls, image_bytes: bytes, orig_size: Tuple[int, int], config: ProcessingConfig) -> np.ndarray:
        from rembg import remove
        
        models_to_try = ['birefnet-general', 'isnet-general-use', 'u2net']
        
        for model_name in models_to_try:
            session = cls._get_session(model_name)
            if session is None:
                continue
                
            try:
                logger.info(f"  Running AI Model: {model_name}...")
                img = Image.open(io.BytesIO(image_bytes))
                w, h = img.size
                
                # BiRefNet needs lower resolution to prevent OOM
                max_dim = min(config.max_rembg_dimension, 768) if 'birefnet' in model_name else config.max_rembg_dimension
                
                if max(w, h) > max_dim:
                    ratio = max_dim / max(w, h)
                    img_resized = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
                    buf = io.BytesIO()
                    img_resized.save(buf, format="JPEG", quality=92)
                    input_bytes = buf.getvalue()
                else:
                    input_bytes = image_bytes
                
                output_bytes = remove(input_bytes, session=session, alpha_matting=False)
                output_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
                
                if max(w, h) > max_dim:
                    output_img = output_img.resize(orig_size, Image.Resampling.LANCZOS)
                
                alpha = np.array(output_img.split()[-1])
                logger.info(f"  ✓ {model_name} succeeded")
                return alpha.astype(np.float32) / 255.0
                
            except MemoryError as e:
                logger.error(f"  ✗ {model_name} OOM: {e}")
                if 'birefnet' in model_name:
                    cls._birefnet_disabled = True
            except Exception as e:
                if "bad allocation" in str(e).lower() or "memory" in str(e).lower():
                    if 'birefnet' in model_name:
                        cls._birefnet_disabled = True
                logger.warning(f"  ✗ {model_name} failed: {e}")
                
        raise Exception("All AI models failed due to memory or errors.")

# ========================== POST-PROCESSING STAGES ==========================
class EdgeShaver:
    @staticmethod
    def shave_trailing_edges(alpha_map: np.ndarray) -> np.ndarray:
        """
        FIXES: Trailing/jagged fuzzy edges.
        Erodes the alpha mask by 1 pixel to shave off fuzzy halos, 
        then smooths for anti-aliasing.
        """
        logger.info("  [Edge Shaver] Removing trailing fuzzy edges...")
        alpha_uint8 = (alpha_map * 255).astype(np.uint8)
        
        # Erode to cut off 1-2 pixels of trailing edges
        kernel = np.ones((3, 3), np.uint8)
        alpha_eroded = cv2.erode(alpha_uint8, kernel, iterations=1)
        
        # Smooth the eroded edges to prevent jagged stair-steps
        alpha_smooth = cv2.GaussianBlur(alpha_eroded, (3, 3), 1.0)
        
        return alpha_smooth.astype(np.float32) / 255.0

class GlobalBackgroundBleeder:
    @staticmethod
    def remove_background_in_gaps(input_np: np.ndarray, alpha_map: np.ndarray) -> np.ndarray:
        """
        FIXES: Wood/texture remaining inside product gaps (bras, bikinis).
        Samples the outer border to find the dominant background color,
        then removes ANY pixel matching that color unless the AI is >90% confident.
        """
        logger.info("  [Color Bleed] Removing background inside gaps (wood/texture)...")
        h, w = input_np.shape[:2]
        border = int(min(h, w) * 0.05) # Sample outer 5%
        
        # Gather border pixels
        top = input_np[:border, :, :].reshape(-1, 3)
        bottom = input_np[-border:, :, :].reshape(-1, 3)
        left = input_np[:, :border, :].reshape(-1, 3)
        right = input_np[:, -border:, :].reshape(-1, 3)
        border_pixels = np.concatenate([top, bottom, left, right], axis=0).astype(np.float32)
        
        # K-Means to find the dominant background color
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(border_pixels, 2, None, criteria, 5, cv2.KMEANS_RANDOM_CENTERS)
        unique, counts = np.unique(labels, return_counts=True)
        bg_color = centers[np.argmax(counts)]
        
        # Calculate color distance for ALL pixels in the image
        dist = np.linalg.norm(input_np.astype(np.float32) - bg_color, axis=2)
        
        # Pixels that look like the background
        color_match = dist < 35.0 
        
        # AI confidence mask (only protect pixels AI is VERY sure about)
        ai_confident = alpha_map > 0.90
        
        # Bleed mask: looks like background AND AI is NOT confident
        bleed_mask = color_match & (~ai_confident)
        
        # Apply to alpha
        alpha_final = alpha_map.copy()
        alpha_final[bleed_mask] = 0.0
        
        removed_pixels = np.sum(bleed_mask)
        logger.info(f"  [Color Bleed] Erased {removed_pixels} background-colored pixels from gaps")
        
        return alpha_final

class ArtifactIsolator:
    @staticmethod
    def remove_floating_dust(alpha_map: np.ndarray) -> np.ndarray:
        """Removes small isolated floating artifacts."""
        logger.info("  [Isolator] Removing floating dust/artifacts...")
        h, w = alpha_map.shape
        _, binary = cv2.threshold((alpha_map * 255).astype(np.uint8), 128, 255, cv2.THRESH_BINARY)
        
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
        
        min_area = (h * w) * 0.005 # Keep only objects > 0.5% of image
        alpha_clean = alpha_map.copy()
        
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] < min_area:
                alpha_clean[labels == i] = 0.0
                
        return alpha_clean

# ========================== EXPORTER ==========================
class Exporter:
    @staticmethod
    def process_and_save(input_bytes: bytes, output_path: str, config: ProcessingConfig):
        img = Image.open(io.BytesIO(input_bytes)).convert("RGB")
        orig_size = img.size
        input_np = np.array(img)
        
        # 1. AI Segmentation
        alpha_map = AISegmenter.generate_alpha(input_bytes, orig_size, config)
        
        # 2. Edge Shaving (Fixes Trailing Edges)
        alpha_map = EdgeShaver.shave_trailing_edges(alpha_map)
        
        # 3. Global Color Bleed (Fixes Wood in Gaps)
        alpha_map = GlobalBackgroundBleeder.remove_background_in_gaps(input_np, alpha_map)
        
        # 4. Artifact Isolation
        alpha_map = ArtifactIsolator.remove_floating_dust(alpha_map)
        
        # 5. Composition (FIXES BLACK SPOTS: NO Premultiplication)
        logger.info("  [Compose] Building final RGBA (No premultiplication)...")
        h, w = input_np.shape[:2]
        final_rgba = np.zeros((h, w, 4), dtype=np.uint8)
        final_rgba[:, :, :3] = input_np  # Keep original RGB intact!
        final_rgba[:, :, 3] = (alpha_map * 255).astype(np.uint8)
        
        # Ensure fully transparent pixels have RGB=0 to prevent any viewer fringing
        trans_mask = final_rgba[:, :, 3] == 0
        final_rgba[trans_mask, :3] = 0
        
        # 6. Canvas & Export
        final_img = Image.fromarray(final_rgba, mode="RGBA")
        
        target_size = min(max(final_img.width, final_img.height), config.max_output_dimension)
        ratio = min(target_size / max(final_img.width, final_img.height), 1.0)
        new_w, new_h = int(final_img.width * ratio), int(final_img.height * ratio)
        resized = final_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
        canvas.paste(resized, ((target_size - new_w) // 2, (target_size - new_h) // 2), resized)
        
        canvas.save(output_path, format="PNG", optimize=True)

# ========================== MAIN ==========================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Zozi AI Ultimate v11.0")
    parser.add_argument("--input", "-i", default="./image")
    parser.add_argument("--output", "-o", default="./output_br_11")
    parser.add_argument("--resolution", "-r", type=int, default=1024, choices=[1024, 1536, 2048])
    args = parser.parse_args()
    
    CONFIG.max_rembg_dimension = args.resolution
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
        image_files.extend(input_dir.glob(ext))
        
    if not image_files:
        print(f"❌ No images found in {input_dir}")
        sys.exit(1)
        
    print(f"\n📸 Found {len(image_files)} images | Resolution: {args.resolution}px\n")
    
    success, fail = 0, 0
    for idx, img_path in enumerate(image_files, 1):
        print(f"[{idx}/{len(image_files)}] {img_path.name}")
        try:
            with open(img_path, 'rb') as f:
                img_bytes = f.read()
                
            out_path = output_dir / f"{img_path.stem}_br_11.png"
            Exporter.process_and_save(img_bytes, str(out_path), CONFIG)
            
            print(f"  ✅ Saved: {out_path.name}")
            success += 1
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            fail += 1
        finally:
            MemoryManager.cleanup()
            
    print(f"\n{'='*50}\n✅ Success: {success} | ❌ Failed: {fail}\n{'='*50}")
```

---

## 📄 br_12.py

```python
# br_12.py

"""
Zozi AI Image Processor - Ultimate Pipeline v12.0 (Specialized Variants)
=====================================================================
PURPOSE: Handle complex marketing images with props, text, and floating artifacts.
NEW MODELS:
- birefnet-massive (Highest accuracy, heavy compute)
- birefnet-hrsod (High-Resolution Salient Object Detection)
- u2net_cloth_seg (Specifically for clothing/bikinis)

NEW FEATURES:
- Floating Artifact Removal (Removes the gold piece behind the perfume)
- Bottom Text/Watermark Eraser (Removes "UNLEASH THE..." text)
- Smart Bounding Box Analysis
"""

import io
import os
import sys
import base64
import logging
import time
import threading
import gc
from typing import Tuple, Dict, Any
from pathlib import Path
from dataclasses import dataclass
from PIL import Image
import numpy as np
import cv2

# ========================== LOGGING ==========================
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ZoziAI-v12")

# ========================== CONFIGURATION ==========================
@dataclass
class ProcessingConfig:
    max_rembg_dimension: int = 1024
    max_output_dimension: int = 2048

CONFIG = ProcessingConfig()

# ========================== MEMORY MANAGER ==========================
class MemoryManager:
    @staticmethod
    def cleanup():
        gc.collect()

# ========================== AI SEGMENTER (v12.0 Variants) ==========================
class AISegmenter:
    # Track disabled models globally
    _disabled_models = set()
    _sessions = {}
    _lock = threading.Lock()

    @classmethod
    def _get_session(cls, model_name: str):
        if model_name in cls._disabled_models:
            return None
        with cls._lock:
            if model_name not in cls._sessions:
                try:
                    from rembg import new_session
                    logger.info(f"  Loading model: {model_name}...")
                    cls._sessions[model_name] = new_session(model_name)
                except Exception as e:
                    logger.warning(f"Failed to load {model_name}: {e}")
                    cls._disabled_models.add(model_name)
                    return None
            return cls._sessions[model_name]

    @classmethod
    def generate_alpha(cls, image_bytes: bytes, orig_size: Tuple[int, int], config: ProcessingConfig) -> np.ndarray:
        from rembg import remove
        
        # Priority list of specialized models
        # 1. birefnet-massive: Best for complex scenes with props
        # 2. birefnet-hrsod: Best for high-res details
        # 3. u2net_cloth_seg: Best for clothing (bikinis)
        # 4. isnet-general-use: Fallback
        models_to_try = [
            'birefnet-massive', 
            'birefnet-hrsod', 
            'u2net_cloth_seg', 
            'isnet-general-use'
        ]
        
        for model_name in models_to_try:
            session = cls._get_session(model_name)
            if session is None:
                continue
                
            try:
                logger.info(f"  Running AI Model: {model_name}...")
                img = Image.open(io.BytesIO(image_bytes))
                w, h = img.size
                
                # Massive model needs lower resolution to prevent OOM
                max_dim = config.max_rembg_dimension
                if 'massive' in model_name:
                    max_dim = min(max_dim, 768)
                elif 'birefnet' in model_name:
                    max_dim = min(max_dim, 1024)
                
                if max(w, h) > max_dim:
                    ratio = max_dim / max(w, h)
                    img_resized = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
                    buf = io.BytesIO()
                    img_resized.save(buf, format="JPEG", quality=92)
                    input_bytes = buf.getvalue()
                else:
                    input_bytes = image_bytes
                
                output_bytes = remove(input_bytes, session=session, alpha_matting=False)
                output_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
                
                if max(w, h) > max_dim:
                    output_img = output_img.resize(orig_size, Image.Resampling.LANCZOS)
                
                alpha = np.array(output_img.split()[-1])
                logger.info(f"  ✓ {model_name} succeeded")
                return alpha.astype(np.float32) / 255.0
                
            except MemoryError as e:
                logger.error(f"  ✗ {model_name} OOM: {e}")
                cls._disabled_models.add(model_name)
            except Exception as e:
                if "bad allocation" in str(e).lower() or "memory" in str(e).lower():
                    cls._disabled_models.add(model_name)
                logger.warning(f"  ✗ {model_name} failed: {e}")
                
        raise Exception("All AI models failed.")

# ========================== POST-PROCESSING STAGES ==========================

class FloatingArtifactRemover:
    @staticmethod
    def remove_floating_objects(alpha_map: np.ndarray) -> np.ndarray:
        """
        FIXES: Floating gold pieces behind products.
        Finds the main product bounding box and removes large disconnected 
        components that are far away from the main center of mass.
        """
        logger.info("  [Floating Remover] Removing disconnected background props...")
        h, w = alpha_map.shape
        _, binary = cv2.threshold((alpha_map * 255).astype(np.uint8), 128, 255, cv2.THRESH_BINARY)
        
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
        
        if num_labels <= 1:
            return alpha_map
            
        # Find the largest component (Main Product)
        largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        main_x = stats[largest_label, cv2.CC_STAT_LEFT]
        main_y = stats[largest_label, cv2.CC_STAT_TOP]
        main_w = stats[largest_label, cv2.CC_STAT_WIDTH]
        main_h = stats[largest_label, cv2.CC_STAT_HEIGHT]
        
        # Calculate center of main product
        main_cx = main_x + main_w / 2
        main_cy = main_y + main_h / 2
        
        alpha_clean = alpha_map.copy()
        
        # Check other components
        for i in range(1, num_labels):
            if i == largest_label:
                continue
                
            area = stats[i, cv2.CC_STAT_AREA]
            # If it's a significant size (not dust, but not main product)
            if area > (h * w) * 0.01: 
                x = stats[i, cv2.CC_STAT_LEFT]
                y = stats[i, cv2.CC_STAT_TOP]
                comp_w = stats[i, cv2.CC_STAT_WIDTH]
                comp_h = stats[i, cv2.CC_STAT_HEIGHT]
                
                comp_cx = x + comp_w / 2
                comp_cy = y + comp_h / 2
                
                # Distance from main product center
                dist = np.sqrt((comp_cx - main_cx)**2 + (comp_cy - main_cy)**2)
                
                # If it's far away (more than 1.5x the width of the main product)
                if dist > main_w * 1.5:
                    alpha_clean[labels == i] = 0.0
                    logger.info(f"    Removed floating artifact at ({x},{y})")
                    
        return alpha_clean

class BottomTextEraser:
    @staticmethod
    def erase_bottom_text(alpha_map: np.ndarray, input_np: np.ndarray) -> np.ndarray:
        """
        FIXES: Text like "UNLEASH THE AUROA" at the bottom.
        Scans the bottom 15% of the image for horizontal text patterns 
        and removes them if they are isolated from the main product.
        """
        logger.info("  [Text Eraser] Scanning for bottom text/watermarks...")
        h, w = alpha_map.shape
        _, binary = cv2.threshold((alpha_map * 255).astype(np.uint8), 128, 255, cv2.THRESH_BINARY)
        
        # Focus on bottom 20%
        bottom_region = binary[int(h*0.8):, :]
        
        # Find contours in bottom region
        contours, _ = cv2.findContours(bottom_region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        alpha_clean = alpha_map.copy()
        removed = False
        
        for contour in contours:
            x, y, cw, ch = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            
            # Adjust y to global coordinates
            global_y = y + int(h*0.8)
            
            # Text characteristics: Wide and short (horizontal text)
            aspect_ratio = float(cw) / ch if ch > 0 else 0
            
            if 100 < area < 5000 and aspect_ratio > 2.0:
                # Check if it's text-like (high horizontal density)
                # Simple heuristic: if it's in the bottom 10% and wide
                if global_y > h * 0.90:
                    # Remove it
                    alpha_clean[global_y:global_y+ch, x:x+cw] = 0.0
                    removed = True
                    logger.info(f"    Erased text artifact at bottom ({x},{global_y})")
                    
        return alpha_clean

class EdgeShaver:
    @staticmethod
    def shave_trailing_edges(alpha_map: np.ndarray) -> np.ndarray:
        logger.info("  [Edge Shaver] Removing trailing fuzzy edges...")
        alpha_uint8 = (alpha_map * 255).astype(np.uint8)
        kernel = np.ones((3, 3), np.uint8)
        alpha_eroded = cv2.erode(alpha_uint8, kernel, iterations=1)
        alpha_smooth = cv2.GaussianBlur(alpha_eroded, (3, 3), 1.0)
        return alpha_smooth.astype(np.float32) / 255.0

class GlobalBackgroundBleeder:
    @staticmethod
    def remove_background_in_gaps(input_np: np.ndarray, alpha_map: np.ndarray) -> np.ndarray:
        logger.info("  [Color Bleed] Removing background inside gaps...")
        h, w = input_np.shape[:2]
        border = int(min(h, w) * 0.05)
        
        top = input_np[:border, :, :].reshape(-1, 3)
        bottom = input_np[-border:, :, :].reshape(-1, 3)
        left = input_np[:, :border, :].reshape(-1, 3)
        right = input_np[:, -border:, :].reshape(-1, 3)
        border_pixels = np.concatenate([top, bottom, left, right], axis=0).astype(np.float32)
        
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(border_pixels, 2, None, criteria, 5, cv2.KMEANS_RANDOM_CENTERS)
        unique, counts = np.unique(labels, return_counts=True)
        bg_color = centers[np.argmax(counts)]
        
        dist = np.linalg.norm(input_np.astype(np.float32) - bg_color, axis=2)
        color_match = dist < 35.0 
        ai_confident = alpha_map > 0.90
        bleed_mask = color_match & (~ai_confident)
        
        alpha_final = alpha_map.copy()
        alpha_final[bleed_mask] = 0.0
        
        return alpha_final

# ========================== EXPORTER ==========================
class Exporter:
    @staticmethod
    def process_and_save(input_bytes: bytes, output_path: str, config: ProcessingConfig):
        img = Image.open(io.BytesIO(input_bytes)).convert("RGB")
        orig_size = img.size
        input_np = np.array(img)
        
        # 1. AI Segmentation (Specialized Models)
        alpha_map = AISegmenter.generate_alpha(input_bytes, orig_size, config)
        
        # 2. Floating Artifact Removal (Fixes gold piece behind perfume)
        alpha_map = FloatingArtifactRemover.remove_floating_objects(alpha_map)
        
        # 3. Bottom Text Eraser (Fixes "UNLEASH THE..." text)
        alpha_map = BottomTextEraser.erase_bottom_text(alpha_map, input_np)
        
        # 4. Edge Shaving
        alpha_map = EdgeShaver.shave_trailing_edges(alpha_map)
        
        # 5. Global Color Bleed (Fixes wood/texture in gaps)
        alpha_map = GlobalBackgroundBleeder.remove_background_in_gaps(input_np, alpha_map)
        
        # 6. Composition (No premultiplication to fix black spots)
        logger.info("  [Compose] Building final RGBA...")
        h, w = input_np.shape[:2]
        final_rgba = np.zeros((h, w, 4), dtype=np.uint8)
        final_rgba[:, :, :3] = input_np
        final_rgba[:, :, 3] = (alpha_map * 255).astype(np.uint8)
        
        trans_mask = final_rgba[:, :, 3] == 0
        final_rgba[trans_mask, :3] = 0
        
        # 7. Canvas & Export
        final_img = Image.fromarray(final_rgba, mode="RGBA")
        
        target_size = min(max(final_img.width, final_img.height), config.max_output_dimension)
        ratio = min(target_size / max(final_img.width, final_img.height), 1.0)
        new_w, new_h = int(final_img.width * ratio), int(final_img.height * ratio)
        resized = final_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
        canvas.paste(resized, ((target_size - new_w) // 2, (target_size - new_h) // 2), resized)
        
        canvas.save(output_path, format="PNG", optimize=True)

# ========================== MAIN ==========================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Zozi AI Ultimate v12.0 (Specialized Variants)")
    parser.add_argument("--input", "-i", default="./image")
    parser.add_argument("--output", "-o", default="./output_br_12")
    parser.add_argument("--resolution", "-r", type=int, default=1024, choices=[1024, 1536, 2048])
    args = parser.parse_args()
    
    CONFIG.max_rembg_dimension = args.resolution
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
        image_files.extend(input_dir.glob(ext))
        
    if not image_files:
        print(f"❌ No images found in {input_dir}")
        sys.exit(1)
        
    print(f"\n📸 Found {len(image_files)} images | Resolution: {args.resolution}px")
    print("🚀 Using specialized models: birefnet-massive, birefnet-hrsod, u2net_cloth_seg\n")
    
    success, fail = 0, 0
    for idx, img_path in enumerate(image_files, 1):
        print(f"[{idx}/{len(image_files)}] {img_path.name}")
        try:
            with open(img_path, 'rb') as f:
                img_bytes = f.read()
                
            out_path = output_dir / f"{img_path.stem}_br_12.png"
            Exporter.process_and_save(img_bytes, str(out_path), CONFIG)
            
            print(f"  ✅ Saved: {out_path.name}")
            success += 1
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            fail += 1
        finally:
            MemoryManager.cleanup()
            
    print(f"\n{'='*50}\n✅ Success: {success} | ❌ Failed: {fail}\n{'='*50}")
```

---

## 📄 br_13.py

```python
# br_13.py

"""
Zozi AI Image Processor - Variant Testing Pipeline v13.0
=====================================================
PURPOSE: Test specialized model variants to fix specific issues.
NEW MODELS:
- birefnet-general-lite (Fixes Memory/OOM crashes)
- u2net_cloth_seg (Fixes Bikini/Clothing gaps)
- briaai-rmbg-1.4 (Fixes complex marketing images)
"""

import io
import os
import sys
import base64
import logging
import time
import threading
import gc
from typing import Tuple, Dict, Any
from pathlib import Path
from dataclasses import dataclass
from PIL import Image
import numpy as np
import cv2

# ========================== LOGGING ==========================
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ZoziAI-v13")

# ========================== CONFIGURATION ==========================
@dataclass
class ProcessingConfig:
    max_rembg_dimension: int = 1024
    max_output_dimension: int = 2048

CONFIG = ProcessingConfig()

# ========================== MEMORY MANAGER ==========================
class MemoryManager:
    @staticmethod
    def cleanup():
        gc.collect()

# ========================== AI SEGMENTER (v13.0 Variants) ==========================
class AISegmenter:
    _disabled_models = set()
    _sessions = {}
    _lock = threading.Lock()

    @classmethod
    def _get_session(cls, model_name: str):
        if model_name in cls._disabled_models:
            return None
        with cls._lock:
            if model_name not in cls._sessions:
                try:
                    from rembg import new_session
                    logger.info(f"  Loading variant: {model_name}...")
                    cls._sessions[model_name] = new_session(model_name)
                except Exception as e:
                    logger.warning(f"Failed to load {model_name}: {e}")
                    cls._disabled_models.add(model_name)
                    return None
            return cls._sessions[model_name]

    @classmethod
    def generate_alpha(cls, image_bytes: bytes, orig_size: Tuple[int, int], config: ProcessingConfig) -> np.ndarray:
        from rembg import remove
        
        # Priority list of specialized variants
        # 1. Lite model (prevents crashes)
        # 2. Cloth model (fixes bikinis)
        # 3. RMBG (fixes complex ads)
        # 4. Standard fallback
        models_to_try = [
            'birefnet-general-lite', 
            'u2net_cloth_seg', 
            'briaai-rmbg-1.4',
            'isnet-general-use'
        ]
        
        for model_name in models_to_try:
            session = cls._get_session(model_name)
            if session is None:
                continue
                
            try:
                logger.info(f"  Running Variant: {model_name}...")
                img = Image.open(io.BytesIO(image_bytes))
                w, h = img.size
                
                # Lite model can handle higher res, others need capping
                max_dim = config.max_rembg_dimension
                if 'lite' in model_name:
                    max_dim = min(max_dim, 1280) 
                elif 'birefnet' in model_name:
                    max_dim = min(max_dim, 1024)
                
                if max(w, h) > max_dim:
                    ratio = max_dim / max(w, h)
                    img_resized = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)
                    buf = io.BytesIO()
                    img_resized.save(buf, format="JPEG", quality=92)
                    input_bytes = buf.getvalue()
                else:
                    input_bytes = image_bytes
                
                output_bytes = remove(input_bytes, session=session, alpha_matting=False)
                output_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
                
                if max(w, h) > max_dim:
                    output_img = output_img.resize(orig_size, Image.Resampling.LANCZOS)
                
                alpha = np.array(output_img.split()[-1])
                logger.info(f"  ✓ {model_name} succeeded")
                return alpha.astype(np.float32) / 255.0
                
            except MemoryError as e:
                logger.error(f"   {model_name} OOM: {e}")
                cls._disabled_models.add(model_name)
            except Exception as e:
                if "bad allocation" in str(e).lower() or "memory" in str(e).lower():
                    cls._disabled_models.add(model_name)
                logger.warning(f"  ✗ {model_name} failed: {e}")
                
        raise Exception("All AI variants failed.")

# ========================== POST-PROCESSING STAGES (From v11.0) ==========================

class EdgeShaver:
    @staticmethod
    def shave_trailing_edges(alpha_map: np.ndarray) -> np.ndarray:
        logger.info("  [Edge Shaver] Removing trailing fuzzy edges...")
        alpha_uint8 = (alpha_map * 255).astype(np.uint8)
        kernel = np.ones((3, 3), np.uint8)
        alpha_eroded = cv2.erode(alpha_uint8, kernel, iterations=1)
        alpha_smooth = cv2.GaussianBlur(alpha_eroded, (3, 3), 1.0)
        return alpha_smooth.astype(np.float32) / 255.0

class GlobalBackgroundBleeder:
    @staticmethod
    def remove_background_in_gaps(input_np: np.ndarray, alpha_map: np.ndarray) -> np.ndarray:
        logger.info("  [Color Bleed] Removing background inside gaps...")
        h, w = input_np.shape[:2]
        border = int(min(h, w) * 0.05)
        
        top = input_np[:border, :, :].reshape(-1, 3)
        bottom = input_np[-border:, :, :].reshape(-1, 3)
        left = input_np[:, :border, :].reshape(-1, 3)
        right = input_np[:, -border:, :].reshape(-1, 3)
        border_pixels = np.concatenate([top, bottom, left, right], axis=0).astype(np.float32)
        
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(border_pixels, 2, None, criteria, 5, cv2.KMEANS_RANDOM_CENTERS)
        unique, counts = np.unique(labels, return_counts=True)
        bg_color = centers[np.argmax(counts)]
        
        dist = np.linalg.norm(input_np.astype(np.float32) - bg_color, axis=2)
        color_match = dist < 35.0 
        ai_confident = alpha_map > 0.90
        bleed_mask = color_match & (~ai_confident)
        
        alpha_final = alpha_map.copy()
        alpha_final[bleed_mask] = 0.0
        
        return alpha_final

class FloatingArtifactRemover:
    @staticmethod
    def remove_floating_objects(alpha_map: np.ndarray) -> np.ndarray:
        logger.info("  [Floating Remover] Removing disconnected background props...")
        h, w = alpha_map.shape
        _, binary = cv2.threshold((alpha_map * 255).astype(np.uint8), 128, 255, cv2.THRESH_BINARY)
        
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
        if num_labels <= 1: return alpha_map
            
        largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        main_x = stats[largest_label, cv2.CC_STAT_LEFT]
        main_y = stats[largest_label, cv2.CC_STAT_TOP]
        main_w = stats[largest_label, cv2.CC_STAT_WIDTH]
        main_h = stats[largest_label, cv2.CC_STAT_HEIGHT]
        
        main_cx = main_x + main_w / 2
        main_cy = main_y + main_h / 2
        
        alpha_clean = alpha_map.copy()
        
        for i in range(1, num_labels):
            if i == largest_label: continue
            area = stats[i, cv2.CC_STAT_AREA]
            if area > (h * w) * 0.01: 
                x = stats[i, cv2.CC_STAT_LEFT]
                y = stats[i, cv2.CC_STAT_TOP]
                comp_w = stats[i, cv2.CC_STAT_WIDTH]
                comp_h = stats[i, cv2.CC_STAT_HEIGHT]
                
                comp_cx = x + comp_w / 2
                comp_cy = y + comp_h / 2
                
                dist = np.sqrt((comp_cx - main_cx)**2 + (comp_cy - main_cy)**2)
                
                if dist > main_w * 1.5:
                    alpha_clean[labels == i] = 0.0
                    
        return alpha_clean

class BottomTextEraser:
    @staticmethod
    def erase_bottom_text(alpha_map: np.ndarray, input_np: np.ndarray) -> np.ndarray:
        logger.info("  [Text Eraser] Scanning for bottom text/watermarks...")
        h, w = alpha_map.shape
        _, binary = cv2.threshold((alpha_map * 255).astype(np.uint8), 128, 255, cv2.THRESH_BINARY)
        
        bottom_region = binary[int(h*0.8):, :]
        contours, _ = cv2.findContours(bottom_region, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        alpha_clean = alpha_map.copy()
        
        for contour in contours:
            x, y, cw, ch = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            global_y = y + int(h*0.8)
            aspect_ratio = float(cw) / ch if ch > 0 else 0
            
            if 100 < area < 5000 and aspect_ratio > 2.0:
                if global_y > h * 0.90:
                    alpha_clean[global_y:global_y+ch, x:x+cw] = 0.0
                    
        return alpha_clean

# ========================== EXPORTER ==========================
class Exporter:
    @staticmethod
    def process_and_save(input_bytes: bytes, output_path: str, config: ProcessingConfig):
        img = Image.open(io.BytesIO(input_bytes)).convert("RGB")
        orig_size = img.size
        input_np = np.array(img)
        
        # 1. AI Segmentation (Specialized Variants)
        alpha_map = AISegmenter.generate_alpha(input_bytes, orig_size, config)
        
        # 2. Floating Artifact Removal
        alpha_map = FloatingArtifactRemover.remove_floating_objects(alpha_map)
        
        # 3. Bottom Text Eraser
        alpha_map = BottomTextEraser.erase_bottom_text(alpha_map, input_np)
        
        # 4. Edge Shaving
        alpha_map = EdgeShaver.shave_trailing_edges(alpha_map)
        
        # 5. Global Color Bleed (Crucial for bikinis/wood)
        alpha_map = GlobalBackgroundBleeder.remove_background_in_gaps(input_np, alpha_map)
        
        # 6. Composition (No premultiplication)
        logger.info("  [Compose] Building final RGBA...")
        h, w = input_np.shape[:2]
        final_rgba = np.zeros((h, w, 4), dtype=np.uint8)
        final_rgba[:, :, :3] = input_np
        final_rgba[:, :, 3] = (alpha_map * 255).astype(np.uint8)
        
        trans_mask = final_rgba[:, :, 3] == 0
        final_rgba[trans_mask, :3] = 0
        
        # 7. Canvas & Export
        final_img = Image.fromarray(final_rgba, mode="RGBA")
        
        target_size = min(max(final_img.width, final_img.height), config.max_output_dimension)
        ratio = min(target_size / max(final_img.width, final_img.height), 1.0)
        new_w, new_h = int(final_img.width * ratio), int(final_img.height * ratio)
        resized = final_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
        canvas.paste(resized, ((target_size - new_w) // 2, (target_size - new_h) // 2), resized)
        
        canvas.save(output_path, format="PNG", optimize=True)

# ========================== MAIN ==========================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Zozi AI Variant Tester v13.0")
    parser.add_argument("--input", "-i", default="./image")
    parser.add_argument("--output", "-o", default="./output_br_13")
    parser.add_argument("--resolution", "-r", type=int, default=1024, choices=[1024, 1536, 2048])
    args = parser.parse_args()
    
    CONFIG.max_rembg_dimension = args.resolution
    
    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
        image_files.extend(input_dir.glob(ext))
        
    if not image_files:
        print(f"❌ No images found in {input_dir}")
        sys.exit(1)
        
    print(f"\n📸 Found {len(image_files)} images | Resolution: {args.resolution}px")
    print("🚀 Testing variants: birefnet-lite, u2net_cloth_seg, briaai-rmbg-1.4\n")
    
    success, fail = 0, 0
    for idx, img_path in enumerate(image_files, 1):
        print(f"[{idx}/{len(image_files)}] {img_path.name}")
        try:
            with open(img_path, 'rb') as f:
                img_bytes = f.read()
                
            out_path = output_dir / f"{img_path.stem}_br_13.png"
            Exporter.process_and_save(img_bytes, str(out_path), CONFIG)
            
            print(f"  ✅ Saved: {out_path.name}")
            success += 1
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            fail += 1
        finally:
            MemoryManager.cleanup()
            
    print(f"\n{'='*50}\n✅ Success: {success} | ❌ Failed: {fail}\n{'='*50}")
```

---

