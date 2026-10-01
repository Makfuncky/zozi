# ========================== REMOVAL STRATEGY RUNNERS ==========================
from PIL import Image


from typing import Optional, Dict, Any
import numpy as np
from .configuration import ProcessingConfig
from .image_helpers import Image


def _run_general(
    image_bytes: bytes,
    config: ProcessingConfig,
    img: Image.Image,
    input_np: np.ndarray,
) -> bytes:
    _ensure_rembg()
    result_image = None
    used_model = None

    for model_name in config.models_to_try:
        session = _SessionManager.get_session(model_name)
        if session is None:
            continue
        try:
            result_image = _run_model_with_dimension(
                img, session, model_name, config.max_rembg_dimension
            )
            used_model = model_name
            break
        except Exception as exc:
            logger.warning("Model %s failed: %s", model_name, exc)
        finally:
            _SessionManager.release_session(model_name)
            MemoryManager.cleanup()

    if result_image is None:
        logger.error("No model available for general")
        return image_bytes

    try:
        alpha_float = result_image[:, :, 3].astype(np.float32) / 255.0
        final_rgba = _compose_pure_alpha(input_np, alpha_float)
        return _image_to_bytes(Image.fromarray(final_rgba, mode="RGBA"))
    except Exception as exc:
        logger.error("general failed: %s", exc)
        return image_bytes
    finally:
        if used_model:
            _SessionManager.release_session(used_model)
        del result_image
        MemoryManager.cleanup()


def _run_clean_commercial(
    image_bytes: bytes,
    config: ProcessingConfig,
    img: Image.Image,
    input_np: np.ndarray,
) -> bytes:
    """br_05: Gentle edge refinement, pure high-fidelity extraction."""
    _ensure_rembg()
    result_image = None
    used_model = None

    for model_name in config.models_to_try:
        session = _SessionManager.get_session(model_name)
        if session is None:
            continue
        try:
            result_image = _run_model_with_dimension(
                img, session, model_name, config.max_rembg_dimension
            )
            used_model = model_name
            break
        except Exception as exc:
            logger.warning("Model %s failed: %s", model_name, exc)
        finally:
            _SessionManager.release_session(model_name)
            MemoryManager.cleanup()

    if result_image is None:
        logger.error("No model available for clean_commercial")
        return image_bytes

    try:
        raw_alpha_float = result_image[:, :, 3].astype(np.float32) / 255.0
        final_alpha = CleanEdgeRefiner.refine(input_np, raw_alpha_float)
        final_alpha[final_alpha < 0.02] = 0.0
        final_alpha[final_alpha > 0.98] = 1.0
        final_rgba = _compose_pure_alpha(input_np, final_alpha)
        return _image_to_bytes(Image.fromarray(final_rgba, mode="RGBA"))
    except Exception as exc:
        logger.error("clean_commercial failed: %s", exc)
        return image_bytes
    finally:
        if used_model:
            _SessionManager.release_session(used_model)
        del result_image
        MemoryManager.cleanup()


def _run_precision_geometry(
    image_bytes: bytes,
    config: ProcessingConfig,
    img: Image.Image,
    input_np: np.ndarray,
) -> bytes:
    """br_06: Scene-aware geometry (human bypass, hand removal, hole fill, thin reconnect)."""
    _ensure_rembg()
    result_image = None
    used_model = None

    for model_name in config.models_to_try:
        session = _SessionManager.get_session(model_name)
        if session is None:
            continue
        try:
            result_image = _run_model_with_dimension(
                img, session, model_name, config.max_rembg_dimension
            )
            used_model = model_name
            break
        except Exception as exc:
            logger.warning("Model %s failed: %s", model_name, exc)
        finally:
            _SessionManager.release_session(model_name)
            MemoryManager.cleanup()

    if result_image is None:
        logger.error("No model available for precision_geometry")
        return image_bytes

    try:
        raw_alpha_f = result_image[:, :, 3].astype(np.float32) / 255.0
        alpha_mask = (raw_alpha_f > 0.5).astype(np.uint8) * 255

        is_human = SceneAnalyzer.is_human_photo(raw_alpha_f)

        if is_human:
            alpha_f = HumanPreserver.fix_hollows(raw_alpha_f)
        else:
            alpha_mask = HandRemover.remove_if_isolated(alpha_mask)
            alpha_mask = HoleFiller.fill_mask(alpha_mask, min_hole_area=50)
            alpha_mask = ThinPartHandler.handle(alpha_mask, raw_alpha_f)
            alpha_f = alpha_mask.astype(np.float32) / 255.0

        alpha_f = EdgeRefiner.refine(input_np, alpha_f)
        alpha_f[alpha_f < 0.02] = 0.0
        alpha_f[alpha_f > 0.98] = 1.0
        final_rgba = _compose_pure_alpha(input_np, alpha_f)
        return _image_to_bytes(Image.fromarray(final_rgba, mode="RGBA"))
    except Exception as exc:
        logger.error("precision_geometry failed: %s", exc)
        return image_bytes
    finally:
        if used_model:
            _SessionManager.release_session(used_model)
        del result_image
        MemoryManager.cleanup()


def _run_production_birefnet(
    image_bytes: bytes,
    config: ProcessingConfig,
    img: Image.Image,
    input_np: np.ndarray,
) -> bytes:
    """br_08: Multi-model comparison + wood removal + hole filling."""
    _ensure_rembg()
    best_score = -1.0
    best_result = None
    best_model = None

    for model_name in config.models_to_try[: config.max_models_to_try]:
        session = _SessionManager.get_session(model_name)
        if session is None:
            continue
        try:
            raw_output = _run_model_with_dimension(
                img, session, model_name, config.max_rembg_dimension
            )

            prob_map = raw_output[:, :, 3].astype(np.float32) / 255.0
            coverage = float(np.count_nonzero(prob_map > 0.3)) / prob_map.size
            confidence = (
                float(np.mean(prob_map[prob_map > 0.3]))
                if np.any(prob_map > 0.3)
                else 0.0
            )
            score = (coverage * 0.4) + (confidence * 0.6)

            if score > best_score:
                best_score = score
                best_result = raw_output
                best_model = model_name

            if score > 0.85:
                break
        except Exception as exc:
            logger.warning("Model %s failed: %s", model_name, exc)
        finally:
            _SessionManager.release_session(model_name)
            MemoryManager.cleanup()

    if best_result is None:
        logger.error("All models failed for production_birefnet")
        return image_bytes

    try:
        alpha_float = best_result[:, :, 3].astype(np.float32) / 255.0
        image_rgba = _compose_pure_alpha(input_np, alpha_float)
        image_rgba = WoodBackgroundRemover.remove(image_rgba, alpha_float)
        image_rgba = HoleFiller.fill(image_rgba.astype(np.uint8))
        return _image_to_bytes(Image.fromarray(image_rgba.astype(np.uint8), mode="RGBA"))
    except Exception as exc:
        logger.error("production_birefnet failed: %s", exc)
        return image_bytes
    finally:
        del best_result
        MemoryManager.cleanup()


def _run_ultimate_v11(
    image_bytes: bytes,
    config: ProcessingConfig,
    img: Image.Image,
    input_np: np.ndarray,
) -> bytes:
    """br_11: Edge shave + color bleed + artifact isolation."""
    _ensure_rembg()
    result_image = None
    used_model = None

    for model_name in config.models_to_try:
        session = _SessionManager.get_session(model_name)
        if session is None:
            continue
        try:
            result_image = _run_model_with_dimension(
                img, session, model_name, config.max_rembg_dimension
            )
            used_model = model_name
            break
        except Exception as exc:
            logger.warning("Model %s failed: %s", model_name, exc)
        finally:
            _SessionManager.release_session(model_name)
            MemoryManager.cleanup()

    if result_image is None:
        logger.error("No model available for ultimate_v11")
        return image_bytes

    try:
        alpha_map = result_image[:, :, 3].astype(np.float32) / 255.0
        alpha_map = EdgeShaver.shave_trailing_edges(alpha_map)
        alpha_map = GlobalBackgroundBleeder.remove_background_in_gaps(input_np, alpha_map)
        alpha_map = ArtifactIsolator.remove_floating_dust(alpha_map)
        final_rgba = np.zeros((input_np.shape[0], input_np.shape[1], 4), dtype=np.uint8)
        final_rgba[:, :, :3] = input_np
        final_rgba[:, :, 3] = (alpha_map * 255).astype(np.uint8)
        final_rgba[final_rgba[:, :, 3] == 0, :3] = 0
        return _image_to_bytes(Image.fromarray(final_rgba, mode="RGBA"))
    except Exception as exc:
        logger.error("ultimate_v11 failed: %s", exc)
        return image_bytes
    finally:
        if used_model:
            _SessionManager.release_session(used_model)
        del result_image
        MemoryManager.cleanup()


def _run_ultimate_v12(
    image_bytes: bytes,
    config: ProcessingConfig,
    img: Image.Image,
    input_np: np.ndarray,
) -> bytes:
    """br_12: Floating artifact removal + bottom text + edge shave + color bleed."""
    _ensure_rembg()
    result_image = None
    used_model = None

    for model_name in config.models_to_try:
        session = _SessionManager.get_session(model_name)
        if session is None:
            continue
        try:
            result_image = _run_model_with_dimension(
                img, session, model_name, config.max_rembg_dimension
            )
            used_model = model_name
            break
        except Exception as exc:
            logger.warning("Model %s failed: %s", model_name, exc)
        finally:
            _SessionManager.release_session(model_name)
            MemoryManager.cleanup()

    if result_image is None:
        logger.error("No model available for ultimate_v12")
        return image_bytes

    try:
        alpha_map = result_image[:, :, 3].astype(np.float32) / 255.0
        alpha_map = FloatingArtifactRemover.remove_floating_objects(alpha_map)
        alpha_map = BottomTextEraser.erase_bottom_text(alpha_map, input_np)
        alpha_map = EdgeShaver.shave_trailing_edges(alpha_map)
        alpha_map = GlobalBackgroundBleeder.remove_background_in_gaps(input_np, alpha_map)
        final_rgba = np.zeros((input_np.shape[0], input_np.shape[1], 4), dtype=np.uint8)
        final_rgba[:, :, :3] = input_np
        final_rgba[:, :, 3] = (alpha_map * 255).astype(np.uint8)
        final_rgba[final_rgba[:, :, 3] == 0, :3] = 0
        return _image_to_bytes(Image.fromarray(final_rgba, mode="RGBA"))
    except Exception as exc:
        logger.error("ultimate_v12 failed: %s", exc)
        return image_bytes
    finally:
        if used_model:
            _SessionManager.release_session(used_model)
        del result_image
        MemoryManager.cleanup()


def _run_variant_testing(
    image_bytes: bytes,
    config: ProcessingConfig,
    img: Image.Image,
    input_np: np.ndarray,
) -> bytes:
    """br_13: Lite variant pipeline (same post-processing as v12)."""
    _ensure_rembg()
    result_image = None
    used_model = None

    for model_name in config.models_to_try:
        session = _SessionManager.get_session(model_name)
        if session is None:
            continue
        try:
            result_image = _run_model_with_dimension(
                img, session, model_name, config.max_rembg_dimension
            )
            used_model = model_name
            break
        except Exception as exc:
            logger.warning("Model %s failed: %s", model_name, exc)
        finally:
            _SessionManager.release_session(model_name)
            MemoryManager.cleanup()

    if result_image is None:
        logger.error("No model available for variant_testing")
        return image_bytes

    try:
        alpha_map = result_image[:, :, 3].astype(np.float32) / 255.0
        alpha_map = FloatingArtifactRemover.remove_floating_objects(alpha_map)
        alpha_map = BottomTextEraser.erase_bottom_text(alpha_map, input_np)
        alpha_map = EdgeShaver.shave_trailing_edges(alpha_map)
        alpha_map = GlobalBackgroundBleeder.remove_background_in_gaps(input_np, alpha_map)
        final_rgba = np.zeros((input_np.shape[0], input_np.shape[1], 4), dtype=np.uint8)
        final_rgba[:, :, :3] = input_np
        final_rgba[:, :, 3] = (alpha_map * 255).astype(np.uint8)
        final_rgba[final_rgba[:, :, 3] == 0, :3] = 0
        return _image_to_bytes(Image.fromarray(final_rgba, mode="RGBA"))
    except Exception as exc:
        logger.error("variant_testing failed: %s", exc)
        return image_bytes
    finally:
        if used_model:
            _SessionManager.release_session(used_model)
        del result_image
        MemoryManager.cleanup()


def _run_strategy(
    image_bytes: bytes,
    strategy: str,
    config: ProcessingConfig,
    img: Image.Image,
    input_np: np.ndarray,
) -> bytes:
    strategy_lower = strategy.lower()
    if strategy_lower == ProcessingStrategy.CLEAN_COMMERCIAL.value:
        return _run_clean_commercial(image_bytes, config, img, input_np)
    elif strategy_lower == ProcessingStrategy.PRECISION_GEOMETRY.value:
        return _run_precision_geometry(image_bytes, config, img, input_np)
    elif strategy_lower == ProcessingStrategy.PRODUCTION_BIREFNET.value:
        return _run_production_birefnet(image_bytes, config, img, input_np)
    elif strategy_lower == ProcessingStrategy.ULTIMATE_V11.value:
        return _run_ultimate_v11(image_bytes, config, img, input_np)
    elif strategy_lower == ProcessingStrategy.ULTIMATE_V12.value:
        return _run_ultimate_v12(image_bytes, config, img, input_np)
    elif strategy_lower == ProcessingStrategy.VARIANT_TESTING.value:
        return _run_variant_testing(image_bytes, config, img, input_np)
    elif strategy_lower == ProcessingStrategy.GENERAL.value:
        return _run_general(image_bytes, config, img, input_np)
    return image_bytes

