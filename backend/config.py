"""Compatibility re-export for legacy imports."""
from utils.config import settings


Settings = type(settings)


def get_settings() -> Settings:
    return settings

