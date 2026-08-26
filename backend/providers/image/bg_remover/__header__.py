"""
Background Removal Provider
===========================
Consolidates 6 bg removal models (br_05-br_13) into a unified provider.

Classes preserved from reference files:
  br_05: CleanEdgeRefiner, BackgroundRemover
  br_06: SceneAnalyzer, HandRemover, HoleFiller, ThinPartHandler, HumanPreserver, EdgeRefiner, BackgroundRemover
  br_08: MemoryManager, ColorSpaceUtils, ImageLoader, QualityAnalyzer, SubjectDetector, ModelSelector,
          MultiModelSegmenter, WoodBackgroundRemover, Exporter, ZoziBackgroundRemover
  br_11: AISegmenter, EdgeShaver, GlobalBackgroundBleeder, ArtifactIsolator, Exporter
  br_12: AISegmenter (variants), FloatingArtifactRemover, BottomTextEraser, EdgeShaver, GlobalBackgroundBleeder, Exporter
  br_13: AISegmenter (lite variants), EdgeShaver, GlobalBackgroundBleeder, FloatingArtifactRemover, BottomTextEraser, Exporter

All rembg remove() calls use alpha_matting=False.

Test file: backend/tests/_test_provider/test_bg_remover.py
"""
from __future__ import annotations

import io
import logging
import threading
import base64
import gc
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

import numpy as np
from PIL import Image

try:
    import cv2
    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False
    cv2 = None

from infrastructure.utils.config import settings

logger = logging.getLogger(__name__)

_HEAVY_MODELS = {"birefnet-massive", "birefnet-hrsod", "birefnet-general", "u2net_cloth_seg"}
