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


class _LazyPIL:
    """Lazy proxy for PIL.Image to avoid top-level import."""
    def __getattr__(self, name):
        from PIL import Image
        return getattr(Image, name)


class _LazyNumpy:
    """Lazy proxy for numpy to avoid top-level import."""
    def __getattr__(self, name):
        import numpy as np
        return getattr(np, name)


Image = _LazyPIL()
np = _LazyNumpy()

try:
    import cv2
except ImportError:
    cv2 = None

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