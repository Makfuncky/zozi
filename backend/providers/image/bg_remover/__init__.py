"""Split provider package — originally bg_remover.py."""
from __future__ import annotations

from typing import List
from typing import List

from .__header__ import *  # noqa: F401,F403
from .rembg_lazy_load import *  # noqa: F401,F403
from .rembg_lazy_load import _HAS_REMBG, _ensure_rembg, remove, new_session  # noqa: F401
from .core_i_o import *  # noqa: F401,F403
from .core_i_o import _safe_remove, _bytes_to_image, _image_to_bytes  # noqa: F401
from .enums___constants import *  # noqa: F401,F403
from .configuration import *  # noqa: F401,F403
from .memory_management__br_08_ import *  # noqa: F401,F403
from .session_management import *  # noqa: F401,F403
from .image_helpers import _resize_image, _adaptive_max_rembg_dimension, _get_model_max_dimension, _run_model_with_dimension, _apply_alpha_composite, _compose_pure_alpha, _create_canvas
from .core_i_o import _bytes_to_image, _image_to_bytes
from .strategy_config import *  # noqa: F401,F403
from .removal_strategy_runners import *  # noqa: F401,F403
from .public_api import *  # noqa: F401,F403
from .br_05__clean_edge_refiner import *  # noqa: F401,F403
from .br_05___br_06__background_remover_legacy import *  # noqa: F401,F403
from .br_06__precision_geometry_classes import *  # noqa: F401,F403
from .br_08__production_pipeline_classes import *  # noqa: F401,F403
from .br_11_12_13__ultimate_pipeline_classes import *  # noqa: F401,F403
from .br_08___br_11___br_12___br_13__exporters import *  # noqa: F401,F403

__all__: list[str] = []
