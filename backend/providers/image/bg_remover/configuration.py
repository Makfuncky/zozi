# ========================== CONFIGURATION ==========================


from dataclasses import dataclass, field
from typing import Optional, Dict, List
from .enums___constants import SubjectCategory


@dataclass
class ProcessingConfig:
    max_rembg_dimension: int = 512
    max_output_dimension: int = 768
    min_dimension: int = 128
    max_file_size_mb: int = 50
    default_background: str = "transparent"
    default_format: str = "PNG"
    jpeg_quality: int = 95
    png_compression: int = 6
    enable_model_comparison: bool = False
    memory_limit_mb: int = 2048
    max_models_to_try: int = 1
    models_to_try: List[str] = field(default_factory=lambda: [
        "isnet-general-use",
        "u2net",
        "u2netp",
    ])
    preserve_text: bool = False
    preserve_ground: bool = False
    background: str = "transparent"
    subject_type: str = SubjectCategory.UNKNOWN

