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