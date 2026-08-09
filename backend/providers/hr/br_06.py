from __future__ import annotations
import structlog
logger = structlog.get_logger(__name__)
'\nZozi AI Background Remover - Precision Geometry Pipeline v06.1\n==============================================================\nPRECISION FIXES:\n1. ✅ Micro-smooth + Guided Filter edge snapping (No jagged edges)\n2. ✅ Geometric Hand Removal (Deletes blobs attached to product if no face is at top)\n3. ✅ Mathematically Perfect Flood-Fill Hole Fixer (Fixed OpenCV mask reuse bug)\n4. ✅ Directional Thin-Part Handler (Reconnects watchbands safely)\n5. ✅ Safe Human Mode (Bypasses product tools, fixes eye hollows softly)\n\nUsage: python br_06.py\nInput: ./image/\nOutput: ./output_br_06/\n'
import io
import os
import sys
import time
import logging
import gc
from typing import Tuple, Dict, Any, List
from pathlib import Path
from dataclasses import dataclass, field
from utils.lazy_imports import np, Image
import structlog
logger = structlog.get_logger(__name__)

class _Br06ColoredFormatter(logging.Formatter):
    COLORS = {'DEBUG': '\x1b[36m', 'INFO': '\x1b[32m', 'WARNING': '\x1b[33m', 'ERROR': '\x1b[31m'}
    RESET = '\x1b[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f'{color}{record.levelname}{self.RESET}'
        return super().format(record)

def setup_logger(name: str='ZoziAI', level: int=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(_Br06ColoredFormatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S'))
        logger.addHandler(handler)
    return logger
logger = setup_logger()

class _Br06Deps:
    cv2 = False
    guided_filter = False
    remove = None
    new_session = None

    @classmethod
    def check(cls):
        try:
            import numpy
            logger.info('✓ NumPy available')
        except ImportError:
            logger.error('✗ NumPy required')
            sys.exit(1)
        try:
            from PIL import Image
            logger.info('✓ Pillow available')
        except ImportError:
            logger.error('✗ Pillow required')
            sys.exit(1)
        try:
            import cv2
            cls.cv2 = True
            logger.info(f'✓ OpenCV {cv2.__version__} available')
            try:
                from cv2 import ximgproc
                cls.guided_filter = True
                logger.info('✓ Guided Filter available')
            except ImportError:
                logger.exception("unhandled exception", error=str(None))
        except ImportError:
            logger.warning('✗ OpenCV not available')
        try:
            from rembg import remove, new_session
            cls.rembg = True
            cls.remove = remove
            cls.new_session = new_session
            logger.info('✓ rembg available')
        except ImportError:
            logger.error('✗ rembg required')
            sys.exit(1)
_Br06Deps.check()
if _Br06Deps.cv2:
    import cv2

@dataclass
class _Config:
    models: List[str] = field(default_factory=lambda : ['isnet-general-use', 'u2net'])
    max_dimension: int = 2048
    png_compression: int = 6
CONFIG = _Config()

class _Br06SceneAnalyzer:
    """Uses pure geometry to determine if it's a human or isolated product."""

    @staticmethod
    def is_human_photo(alpha: np.ndarray) -> bool:
        """If there is foreground in the top 25% of the image, it's a human (head)."""
        (h, w) = alpha.shape
        top_region = alpha[:int(h * 0.25), :]
        foreground_ratio = np.sum(top_region > 0.5) / top_region.size
        return foreground_ratio > 0.01

class _Br06HandRemover:
    """Removes hands by shape, not color. If no head, secondary blobs attached to main product are hands."""

    @staticmethod
    def remove_if_isolated(alpha_mask: np.ndarray) -> np.ndarray:
        (contours, _) = cv2.findContours(alpha_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours or len(contours) <= 1:
            return alpha_mask
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        main_product = contours[0]
        main_area = cv2.contourArea(main_product)
        main_mask = np.zeros_like(alpha_mask)
        cv2.drawContours(main_mask, [main_product], -1, 255, -1)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (30, 30))
        danger_zone = cv2.dilate(main_mask, kernel, iterations=1)
        removed = False
        for i in range(1, len(contours)):
            cnt = contours[i]
            area = cv2.contourArea(cnt)
            if 100 < area < main_area * 0.5:
                cnt_mask = np.zeros_like(alpha_mask)
                cv2.drawContours(cnt_mask, [cnt], -1, 255, -1)
                overlap = np.sum((cnt_mask > 0) & (danger_zone > 0))
                if overlap > 0:
                    alpha_mask[cnt_mask > 0] = 0
                    removed = True
        if removed:
            logger.info('    ✓ Removed isolated hand (geometric)')
        return alpha_mask

class _Br06HoleFiller:
    """
    Fills internal holes mathematically perfectly.
    FIX: Uses a 1-pixel padding to guarantee all external background is connected,
    preventing the OpenCV mask reuse bug and edge-touching traps.
    """

    @staticmethod
    def fill(alpha_mask: np.ndarray) -> np.ndarray:
        binary_mask = (alpha_mask > 128).astype(np.uint8) * 255
        (h, w) = binary_mask.shape
        padded = np.zeros((h + 2, w + 2), dtype=np.uint8)
        padded[1:h + 1, 1:w + 1] = binary_mask
        ff_mask = np.zeros((h + 4, w + 4), dtype=np.uint8)
        cv2.floodFill(padded, ff_mask, (0, 0), 128)
        internal_holes = padded[1:h + 1, 1:w + 1] == 0
        filled_count = np.sum(internal_holes)
        if filled_count > 50:
            binary_mask[internal_holes] = 255
            logger.info(f'    ✓ Filled internal holes ({filled_count}px)')
        elif filled_count > 0:
            logger.debug(f'    ⓘ Ignored micro-holes ({filled_count}px)')
        return binary_mask

class _Br06ThinPartHandler:
    """Reconnects broken thin parts (watchbands) using directional brushes."""

    @staticmethod
    def handle(alpha_mask: np.ndarray, original_alpha_f: np.ndarray) -> np.ndarray:
        kern_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 5))
        closed_v = cv2.morphologyEx(alpha_mask, cv2.MORPH_CLOSE, kern_v, iterations=1)
        kern_h = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 1))
        closed_h = cv2.morphologyEx(alpha_mask, cv2.MORPH_CLOSE, kern_h, iterations=1)
        safe_reconnect = original_alpha_f > 0.05
        final = np.where(safe_reconnect & ((closed_v > 0) | (closed_h > 0)), 255, alpha_mask)
        reconnected = np.sum((final > 0) & (alpha_mask == 0))
        if reconnected > 20:
            logger.info(f'    ✓ Reconnected thin parts ({reconnected}px)')
        return final

class _Br06HumanPreserver:
    """Fixes human issues (hollow eyes) WITHOUT destroying hair/edges."""

    @staticmethod
    def fix_hollows(alpha_f: np.ndarray) -> np.ndarray:
        solid_mask = (alpha_f > 0.8).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        dilated = cv2.dilate(solid_mask, kernel, iterations=1)
        hollows = (alpha_f < 0.1) & (dilated > 0)
        if np.sum(hollows) > 10:
            alpha_f[hollows] = 0.85
            logger.info('    ✓ Soft-filled human hollows (eyes/face)')
        return alpha_f

class _Br06EdgeRefiner:
    """Micro-smooths staircase jitters, then snaps perfectly to RGB edges."""

    @staticmethod
    def refine(image_np: np.ndarray, alpha_f: np.ndarray) -> np.ndarray:
        if not _Br06Deps.cv2:
            return alpha_f
        binary_fg = (alpha_f > 0.95).astype(np.uint8) * 255
        if np.sum(binary_fg) > 0:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            safe_zone = cv2.dilate(binary_fg, kernel, iterations=2)
            semi_inside = (alpha_f > 0.3) & (alpha_f < 0.95) & (safe_zone > 0)
            alpha_f[semi_inside] = 1.0
        alpha_blurred = cv2.GaussianBlur(alpha_f, (3, 3), 0.8)
        if _Br06Deps.guided_filter:
            try:
                guide = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR).astype(np.float32) / 255.0
                refined = cv2.ximgproc.guidedFilter(guide, alpha_blurred, radius=6, eps=0.0001)
                alpha_f = np.clip(refined, 0, 1)
            except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
                logger.exception("Handled Exception in br_06.py:199")
                alpha_f = alpha_blurred
        binary_final = (alpha_f > 0.5).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        near_edge = cv2.dilate(binary_final, kernel, iterations=6)
        ghost_mask = (near_edge == 0) & (alpha_f < 0.1)
        alpha_f[ghost_mask] = 0.0
        return alpha_f

class _Br06BackgroundRemover:

    def __init__(self, config: _Config=None):
        self.config = config or CONFIG
        self.session = None
        self.model_name = None
        self.stats = {'total_processed': 0, 'total_time': 0, 'errors': 0}

    def _load_best_model(self):
        for model_name in self.config.models:
            try:
                logger.info(f'Loading model: {model_name}...')
                self.session = _Br06Deps.new_session(model_name)
                self.model_name = model_name
                logger.info(f'✓ Using {model_name}\n')
                return True
            except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
                logger.warning(f'✗ {model_name} unavailable')
        return False

    def process_file(self, input_path: str, output_path: str) -> Dict[str, Any]:
        start_time = time.time()
        result = {'input': input_path, 'output': output_path, 'success': False, 'time_seconds': 0}
        try:
            logger.info(f'Processing: {Path(input_path).name}')
            img = Image.open(input_path).convert('RGB')
            img_np = np.array(img)
            (h, w) = img_np.shape[:2]
            (img_resized, ratio) = (img, 1.0)
            if max(w, h) > self.config.max_dimension:
                ratio = self.config.max_dimension / max(w, h)
                (new_w, new_h) = (int(w * ratio), int(h * ratio))
                img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            img_resized.save(buf, format='PNG')
            input_bytes = buf.getvalue()
            output_bytes = _Br06Deps.remove(input_bytes, session=self.session, alpha_matting=False)
            out_img = Image.open(io.BytesIO(output_bytes)).convert('RGBA')
            if ratio < 1.0:
                out_img = out_img.resize((w, h), Image.Resampling.LANCZOS)
            raw_alpha_f = np.array(out_img.split()[-1]).astype(np.float32) / 255.0
            is_human = _Br06SceneAnalyzer.is_human_photo(raw_alpha_f)
            if is_human:
                logger.info('  -> Mode: HUMAN (Preserving features, skipping product tools)')
                alpha_f = _Br06HumanPreserver.fix_hollows(raw_alpha_f)
            else:
                logger.info('  -> Mode: PRODUCT')
                alpha_mask = (raw_alpha_f > 0.5).astype(np.uint8) * 255
                alpha_mask = _Br06HandRemover.remove_if_isolated(alpha_mask)
                alpha_mask = _Br06HoleFiller.fill(alpha_mask)
                alpha_mask = _Br06ThinPartHandler.handle(alpha_mask, raw_alpha_f)
                alpha_f = alpha_mask.astype(np.float32) / 255.0
            alpha_f = _Br06EdgeRefiner.refine(img_np, alpha_f)
            alpha_f[alpha_f < 0.02] = 0.0
            alpha_f[alpha_f > 0.98] = 1.0
            alpha_uint8 = np.clip(alpha_f * 255, 0, 255).astype(np.uint8)
            result_img = Image.fromarray(np.dstack([img_np, alpha_uint8]), mode='RGBA')
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            result_img.save(output_path, 'PNG', compress_level=self.config.png_compression)
            elapsed = time.time() - start_time
            result.update({'success': True, 'time_seconds': round(elapsed, 2)})
            self.stats['total_processed'] += 1
            self.stats['total_time'] += elapsed
            logger.info(f'  ✅ Done ({elapsed:.2f}s)\n')
        except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
            logger.error(f'  ❌ Failed: {e}\n')
            result['error'] = str(e)
            self.stats['errors'] += 1
        return result

    def process_folder(self, input_folder: str, output_folder: str) -> List[Dict[str, Any]]:
        input_path = Path(input_folder)
        output_path = Path(output_folder)
        if not input_path.exists():
            logger.error(f'Input folder not found: {input_folder}')
            return []
        supported_ext = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
        image_files = [f for f in input_path.iterdir() if f.is_file() and f.suffix.lower() in supported_ext]
        if not image_files:
            logger.warning(f'No images found in {input_folder}')
            return []
        logger.info(f'Found {len(image_files)} images\n')
        output_path.mkdir(parents=True, exist_ok=True)
        if not self._load_best_model():
            logger.error('No models could be loaded!')
            return []
        results = []
        for img_file in sorted(image_files):
            out_file = output_path / f'{img_file.stem}.png'
            results.append(self.process_file(str(img_file), str(out_file)))
            gc.collect()
        successful = [r for r in results if r['success']]
        avg_time = np.mean([r['time_seconds'] for r in successful]) if successful else 0
        logger.info(f"{'=' * 60}\nSUMMARY: {len(successful)}/{len(results)} Success | Avg: {avg_time:.2f}s\n{'=' * 60}")
        return results

def main():
    INPUT_FOLDER = './image'
    OUTPUT_FOLDER = './output_br_06'
    if not os.path.exists(INPUT_FOLDER):
        logger.info(f'\n❌ Input folder not found: {INPUT_FOLDER}\n')
        return
    supported_ext = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
    image_count = len([f for f in os.listdir(INPUT_FOLDER) if Path(f).suffix.lower() in supported_ext])
    if image_count == 0:
        logger.info(f'\n❌ No images found in: {INPUT_FOLDER}\n')
        return
    logger.info(f"\n{'=' * 60}")
    logger.info('  ZOZI AI BACKGROUND REMOVER v06.1')
    logger.info('  Precision Geometry Pipeline (Fixed Hole Filler)')
    logger.info(f"{'=' * 60}")
    logger.info(f'  Input:  {INPUT_FOLDER} ({image_count} images)')
    logger.info(f'  Output: {OUTPUT_FOLDER}')
    logger.info(f"{'=' * 60}\n")
    processor = _Br06BackgroundRemover()
    results = processor.process_folder(INPUT_FOLDER, OUTPUT_FOLDER)
    if results:
        success_count = sum((1 for r in results if r['success']))
        logger.info(f'✅ All {success_count} images processed successfully!\n' if success_count == len(results) else f'⚠️  {success_count}/{len(results)} images processed successfully\n')
if __name__ == '__main__':
    main()