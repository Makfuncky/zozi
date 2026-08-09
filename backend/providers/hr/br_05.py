from __future__ import annotations
import structlog
logger = structlog.get_logger(__name__)
'\nZozi AI Background Remover - Clean Commercial Pipeline v05.0\n============================================================\nPHILOSOPHY: Less is More. \nThe AI model does 99% of the work perfectly. We only do 1% cleanup.\n- No destructive text/ground slicing\n- No aggressive geometric hardening\n- Pure, high-fidelity edge refinement\n- Respects the original model mask\n\nUsage: python bg_remover.py\nInput: ./image/\nOutput: ./output/\n'
import io
import os
import sys
import time
import logging
import gc
from typing import Tuple, Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, field
from utils.lazy_imports import np, Image
import structlog
logger = structlog.get_logger(__name__)

class _Br05ColoredFormatter(logging.Formatter):
    COLORS = {'DEBUG': '\x1b[36m', 'INFO': '\x1b[32m', 'WARNING': '\x1b[33m', 'ERROR': '\x1b[31m', 'CRITICAL': '\x1b[41m'}
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
        handler.setFormatter(_Br05ColoredFormatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S'))
        logger.addHandler(handler)
    return logger
logger = setup_logger()

class _Br05Deps:
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
_Br05Deps.check()
if _Br05Deps.cv2:
    import cv2

@dataclass
class _Config:
    models: List[str] = field(default_factory=lambda : ['isnet-general-use', 'u2net'])
    max_dimension: int = 2048
    png_compression: int = 6
CONFIG = _Config()

class _Br05CleanEdgeRefiner:
    """Applies a VERY gentle touch to the raw AI mask."""

    @staticmethod
    def refine(image_np: np.ndarray, alpha: np.ndarray) -> np.ndarray:
        if not _Br05Deps.cv2:
            return alpha
        binary_fg = (alpha > 0.95).astype(np.uint8) * 255
        if np.sum(binary_fg) > 0:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            safe_zone = cv2.dilate(binary_fg, kernel, iterations=2)
            semi_inside = (alpha > 0.3) & (alpha < 0.95) & (safe_zone > 0)
            alpha[semi_inside] = 1.0
        if _Br05Deps.guided_filter:
            try:
                guide = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR).astype(np.float32) / 255.0
                alpha_f = alpha.astype(np.float32)
                refined = cv2.ximgproc.guidedFilter(guide, alpha_f, radius=4, eps=0.0001)
                alpha = np.clip(refined, 0, 1)
            except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
                logger.debug('Guided filter unavailable, falling back to raw mask: %s', e)
        binary_final = (alpha > 0.5).astype(np.uint8) * 255
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        near_edge = cv2.dilate(binary_final, kernel, iterations=5)
        ghost_mask = (near_edge == 0) & (alpha < 0.1)
        alpha[ghost_mask] = 0.0
        return alpha

class _Br05BackgroundRemover:

    def __init__(self, config: _Config=None):
        self.config = config or CONFIG
        self.session = None
        self.model_name = None
        self.stats = {'total_processed': 0, 'total_time': 0, 'errors': 0}

    def _load_best_model(self):
        """Load the single best available model."""
        for model_name in self.config.models:
            try:
                logger.info(f'Loading model: {model_name}...')
                self.session = _Br05Deps.new_session(model_name)
                self.model_name = model_name
                logger.info(f'✓ Using {model_name}')
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
            output_bytes = _Br05Deps.remove(input_bytes, session=self.session, alpha_matting=False)
            out_img = Image.open(io.BytesIO(output_bytes)).convert('RGBA')
            if ratio < 1.0:
                out_img = out_img.resize((w, h), Image.Resampling.LANCZOS)
            raw_alpha = np.array(out_img.split()[-1]).astype(np.float32) / 255.0
            final_alpha = _Br05CleanEdgeRefiner.refine(img_np, raw_alpha)
            final_alpha[final_alpha < 0.02] = 0.0
            final_alpha[final_alpha > 0.98] = 1.0
            alpha_uint8 = np.clip(final_alpha * 255, 0, 255).astype(np.uint8)
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
        logger.info(f'\nFound {len(image_files)} images to process')
        logger.info(f'Input:  {input_folder}')
        logger.info(f'Output: {output_folder}\n')
        output_path.mkdir(parents=True, exist_ok=True)
        if not self._load_best_model():
            logger.error('No models could be loaded!')
            return []
        results = []
        for img_file in sorted(image_files):
            out_file = output_path / f'{img_file.stem}.png'
            results.append(self.process_file(str(img_file), str(out_file)))
            gc.collect()
        self._print_summary(results)
        return results

    def _print_summary(self, results: List[Dict[str, Any]]):
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        avg_time = np.mean([r['time_seconds'] for r in successful]) if successful else 0
        logger.info(f"{'=' * 60}")
        logger.info(f'SUMMARY: {len(successful)} Success, {len(failed)} Failed')
        logger.info(f"Avg Time: {avg_time:.2f}s | Total Time: {self.stats['total_time']:.2f}s")
        logger.info(f"{'=' * 60}\n")

def main():
    INPUT_FOLDER = './image'
    OUTPUT_FOLDER = './output_br_05'
    if not os.path.exists(INPUT_FOLDER):
        logger.info(f'\n❌ Input folder not found: {INPUT_FOLDER}\n')
        return
    supported_ext = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
    image_count = len([f for f in os.listdir(INPUT_FOLDER) if Path(f).suffix.lower() in supported_ext])
    if image_count == 0:
        logger.info(f'\n❌ No images found in: {INPUT_FOLDER}\n')
        return
    logger.info(f"\n{'=' * 60}")
    logger.info('  ZOZI AI BACKGROUND REMOVER 05.0')
    logger.info('  Clean & Pure Pipeline')
    logger.info(f"{'=' * 60}")
    logger.info(f'  Input:  {INPUT_FOLDER} ({image_count} images)')
    logger.info(f'  Output: {OUTPUT_FOLDER}')
    logger.info(f"{'=' * 60}\n")
    processor = _Br05BackgroundRemover()
    results = processor.process_folder(INPUT_FOLDER, OUTPUT_FOLDER)
    if results:
        success_count = sum((1 for r in results if r['success']))
        logger.info(f'✅ All {success_count} images processed successfully!\n' if success_count == len(results) else f'⚠️  {success_count}/{len(results)} images processed successfully\n')
if __name__ == '__main__':
    main()