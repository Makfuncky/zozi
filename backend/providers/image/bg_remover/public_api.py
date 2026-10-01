from typing import List, Optional, Dict, Any
import logging
import numpy as np
# ========================== PUBLIC API ==========================
from .configuration import ProcessingConfig

from PIL import Image

from .rembg_lazy_load import _ensure_rembg, _HAS_REMBG, remove, new_session
from .core_i_o import _bytes_to_image, _image_to_bytes, bytes_to_image, create_rembg_session, create_frugal_rembg_session, rembg_remove_bytes
from .session_management import _SessionManager

logger = logging.getLogger(__name__)



def remove_background(
    image_bytes: bytes,
    model: Optional[str] = None,
    strategy: Optional[str] = None,
) -> bytes:
    """Core background-removal entry point.

    Args:
        image_bytes: Raw image bytes.
        model: Optional specific rembg model name.
        strategy: Optional processing strategy (ProcessingStrategy values).

    Returns:
        PNG bytes with transparent background.
    """
    _ensure_rembg()
    if not _HAS_REMBG or remove is None:
        logger.error("rembg is not installed")
        return image_bytes

    config = ProcessingConfig()
    if strategy:
        config = _get_strategy_config(strategy)

    config.max_rembg_dimension = _adaptive_max_rembg_dimension(config.max_rembg_dimension)

    img = _bytes_to_image(image_bytes)
    img = _resize_image(img, config.max_rembg_dimension)
    input_np = np.array(img.convert("RGB"))

    if strategy:
        try:
            return _run_strategy(image_bytes, strategy, config, img, input_np)
        except Exception as exc:
            logger.error("Strategy %s failed: %s", strategy, exc)

    def _try_model(model_name: str) -> Optional[np.ndarray]:
        session = _SessionManager.get_session(model_name)
        if session is None:
            return None
        try:
            return _run_model_with_dimension(
                img, session, model_name, config.max_rembg_dimension
            )
        except Exception as exc:
            logger.warning("Model %s failed: %s", model_name, exc)
            return None
        finally:
            _SessionManager.release_session(model_name)
            MemoryManager.cleanup()

    selected_models = [model] if model else config.models_to_try
    result_image = None
    used_model = None

    if config.enable_model_comparison:
        best_score = -1.0
        best_result = None

        for model_name in selected_models[: config.max_models_to_try]:
            session = _SessionManager.get_session(model_name)
            if session is None:
                continue

            try:
                raw_output = _try_model(model_name)
                if raw_output is None:
                    continue

                prob_map = raw_output[:, :, 3].astype(np.float32) / 255.0
                coverage = float(np.count_nonzero(prob_map > 0.3)) / prob_map.size
                confidence = float(np.mean(prob_map[prob_map > 0.3])) if np.any(prob_map > 0.3) else 0.0
                score = (coverage * 0.4) + (confidence * 0.6)

                if score > best_score:
                    best_score = score
                    best_result = raw_output
                    used_model = model_name

                if score > 0.85:
                    break
            except Exception as exc:
                logger.warning("Model comparison failed for %s: %s", model_name, exc)
            finally:
                _SessionManager.release_session(model_name)
                MemoryManager.cleanup()

        if best_result is not None:
            result_image = best_result

    if result_image is None:
        for model_name in selected_models:
            result_image = _try_model(model_name)
            used_model = model_name if result_image is not None else None
            if result_image is not None:
                break

    if result_image is None:
        logger.error("No rembg model session available")
        return image_bytes

    try:
        alpha_float = result_image[:, :, 3].astype(np.float32) / 255.0
        final_rgba = _compose_pure_alpha(input_np, alpha_float)
        final_img = Image.fromarray(final_rgba, mode="RGBA")

        if config.background.lower() != "transparent":
            final_img = _create_canvas(final_img, config.background, config.max_output_dimension)

        return _image_to_bytes(final_img)
    except Exception as exc:
        logger.error("Background removal failed with model %s: %s", used_model, exc)
        return image_bytes
    finally:
        if used_model:
            _SessionManager.release_session(used_model)
        del result_image
        MemoryManager.cleanup()


def remove_background_preset(image_bytes: bytes, preset_name: str) -> bytes:
    """Remove background using a named preset model list.

    Args:
        image_bytes: Raw image bytes.
        preset_name: Key from settings.bg_preset_models.

    Returns:
        PNG bytes with transparent background.
    """
    preset_models = settings.bg_preset_models.get(preset_name)
    if not preset_models:
        logger.warning("Unknown preset %s, falling back to general", preset_name)
        preset_models = settings.bg_preset_models["general"]

    config = ProcessingConfig(
        max_rembg_dimension=settings.max_image_dim,
        models_to_try=preset_models,
        background="transparent",
    )

    img = _bytes_to_image(image_bytes)
    img = _resize_image(img, config.max_rembg_dimension)
    input_np = np.array(img.convert("RGB"))

    for model_name in preset_models:
        session = _SessionManager.get_session(model_name)
        if session is None:
            continue
        try:
            result_image = np.array(_safe_remove(img, session).convert("RGBA"))
            alpha_float = result_image[:, :, 3].astype(np.float32) / 255.0
            final_rgba = _compose_pure_alpha(input_np, alpha_float)
            final_img = Image.fromarray(final_rgba, mode="RGBA")
            return _image_to_bytes(final_img)
        except Exception as exc:
            logger.warning("Model %s failed: %s, trying next", model_name, exc)
            continue
        finally:
            _SessionManager.release_session(model_name)
            MemoryManager.cleanup()

    logger.error("All preset models failed for preset %s", preset_name)
    return image_bytes


def remove_background_model(image_bytes: bytes, model_name: str) -> bytes:
    """Remove background using a specific model by name.

    Args:
        image_bytes: Raw image bytes.
        model_name: Exact rembg model name (e.g. 'isnet-general-use').

    Returns:
        Processed image bytes with transparent background.
    """
    if model_name not in AVAILABLE_MODELS:
        logger.warning("Model %s not in AVAILABLE_MODELS, using anyway", model_name)
    return remove_background(image_bytes, model=model_name)


def remove_background_strategy(image_bytes: bytes, strategy: str) -> bytes:
    """Remove background using a specific processing strategy.

    Args:
        image_bytes: Raw image bytes.
        strategy: Strategy name (e.g. 'clean_commercial', 'precision_geometry').

    Returns:
        Processed image bytes with transparent background.
    """
    return remove_background(image_bytes, strategy=strategy)


def magic_erase(image_bytes: bytes, mask: np.ndarray) -> bytes:
    """Erase specific regions from an image using a mask.

    Args:
        image_bytes: Raw image bytes.
        mask: NumPy array (H, W) with 255 for regions to erase, 0 for keep.

    Returns:
        Processed image bytes with erased regions made transparent.
    """
    img = _bytes_to_image(image_bytes)
    img_array = np.array(img)

    if mask.shape[:2] != img_array.shape[:2]:
        mask = np.array(Image.fromarray(mask).resize(
            (img_array.shape[1], img_array.shape[0]),
            Image.NEAREST,
        ))

    alpha = img_array[:, :, 3] if img_array.shape[2] == 4 else np.ones(img_array.shape[:2], dtype=np.uint8) * 255
    mask_bool = mask > 128
    alpha[mask_bool] = 0

    result = np.zeros_like(img_array)
    result[:, :, :3] = img_array[:, :, :3]
    result[:, :, 3] = alpha

    return _image_to_bytes(Image.fromarray(result, "RGBA"))


def process_folder(
    input_folder: str,
    output_folder: str,
    strategy: Optional[str] = None,
    model: Optional[str] = None,
    background: str = "transparent",
) -> List[Dict[str, Any]]:
    """Batch-process a folder of images with aggressive memory cleanup.

    This is the batch-safe entry point for processing thousands of images.
    It loads one model at a time, processes each image, then releases the
    session and runs ``gc.collect()`` before the next image.
    """
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    supported_ext = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
    image_files = sorted(
        f for f in input_path.iterdir()
        if f.is_file() and f.suffix.lower() in supported_ext
    )

    if not image_files:
        logger.warning("No images found in %s", input_folder)
        return []

    logger.info("Batch processing %d images -> %s", len(image_files), output_folder)
    results: List[Dict[str, Any]] = []

    for idx, img_file in enumerate(image_files, 1):
        logger.info("[%d/%d] %s", idx, len(image_files), img_file.name)
        result: Dict[str, Any] = {
            "input": str(img_file),
            "success": False,
            "time_seconds": 0.0,
        }

        try:
            image_bytes = img_file.read_bytes()
            start = time.perf_counter()

            if strategy:
                output_bytes = remove_background(image_bytes, strategy=strategy)
            elif model:
                output_bytes = remove_background(image_bytes, model=model)
            else:
                output_bytes = remove_background(image_bytes)

            elapsed = time.perf_counter() - start
            result["time_seconds"] = round(elapsed, 2)
            result["output_size_bytes"] = len(output_bytes)

            if isinstance(output_bytes, bytes) and len(output_bytes) > 0:
                out_file = output_path / f"{img_file.stem}.png"
                out_file.write_bytes(output_bytes)
                result["success"] = True
                result["output"] = str(out_file)
            else:
                result["error"] = "empty output"

        except Exception as exc:
            result["error"] = str(exc)
        finally:
            _SessionManager.reset()
            gc.collect()
            results.append(result)

    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    avg_time = (
        sum(r["time_seconds"] for r in successful) / len(successful)
        if successful
        else 0.0
    )
    logger.info(
        "Batch complete: %d success, %d failed | avg %.2fs",
        len(successful),
        len(failed),
        avg_time,
    )
    return results


def process_product_image(
    image_bytes: bytes,
    background: str = "transparent",
    output_format: str = "PNG",
) -> Dict[str, Any]:
    """Process a product image using the ultimate pipeline.

    Args:
        image_bytes: Raw image bytes.
        background: Background color for output.
        output_format: Output image format.

    Returns:
        Dict with processing results including base64 encoded image.
    """
    config = ProcessingConfig()
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    orig_size = img.size
    input_np = np.array(img)

    alpha_map = AISegmenter.generate_alpha(image_bytes, orig_size, config)
    alpha_map = EdgeShaver.shave_trailing_edges(alpha_map)
    alpha_map = GlobalBackgroundBleeder.remove_background_in_gaps(input_np, alpha_map)
    alpha_map = FloatingArtifactRemover.remove_floating_objects(alpha_map)

    alpha_uint8 = (alpha_map * 255).astype(np.uint8)
    final_rgba = np.zeros((input_np.shape[0], input_np.shape[1], 4), dtype=np.uint8)
    final_rgba[:, :, :3] = input_np
    final_rgba[:, :, 3] = alpha_uint8

    final_img = Image.fromarray(final_rgba, mode="RGBA")
    buf = io.BytesIO()
    final_img.save(buf, format="PNG")
    output_bytes = buf.getvalue()

    return {
        "base64": base64.b64encode(output_bytes).decode("utf-8"),
        "format": "PNG",
        "width": final_img.width,
        "height": final_img.height,
        "background": background,
    }


def generate_angles(image_bytes: bytes, product_name: str = "", category: str = "") -> List[Dict[str, str]]:
    """Generate AI-suggested descriptions for multiple product photo angles."""
    _ANGLE_PROMPTS = [
        ("Front View", "front view of the product, showing the main face"),
        ("Back View", "rear view of the product, showing the reverse side"),
        ("Side View", "side profile of the product, showing dimensions"),
        ("Detail Shot", "close-up detail showing material texture and quality"),
        ("In Use", "product in use, demonstrating its practical application"),
    ]

    results = []
    for angle_name, angle_context in _ANGLE_PROMPTS:
        description = (
            f"Photograph the {angle_name.lower()} of '{product_name}' to highlight {angle_context}. "
            f"Ensure good lighting and a clean background."
        )
        results.append({
            "angle": angle_name,
            "description": description,
        })

    return results

