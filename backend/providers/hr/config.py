"""Flat shim: re-export from providers.hr.bg_remover."""

from providers.hr.bg_remover import *


try:
    from utils.config import settings
except ImportError:
    settings = None
