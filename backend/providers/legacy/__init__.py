"""
Legacy Background Removal Scripts
==================================
Reference implementations of the 6 background removal pipelines (br_05–br_13).
These are the original standalone scripts from ``Working_API/zozi_ai_image_service/``,
preserved here for reference and side-by-side comparison.

The production implementations live in ``providers.bg_remover``, with each
strategy mapping to its br_* counterpart:

    clean_commercial   → br_05  CleanEdgeRefiner
    precision_geometry → br_06  SceneAware + HoleFiller + HandRemover
    production_birefnet→ br_08  MultiModelSegmenter + WoodBackgroundRemover
    ultimate_v11       → br_11  EdgeShaver + GlobalBackgroundBleeder
    ultimate_v12       → br_12  + FloatingArtifactRemover + BottomTextEraser
    variant_testing    → br_13  Lite variant pipeline

To run any script standalone:
    python -m providers.legacy.br_05
    python -m providers.legacy.br_08
"""
