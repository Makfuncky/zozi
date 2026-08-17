"""API versioning implementation for Zozi backend.

Provides consistent versioned API routing and versioning utilities.
"""
from __future__ import annotations

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# API version configuration
VERSION_PREFIX = "/api/v1"

# Route mappings by version
VERSIONED_ROUTES: Dict[str, Dict[str, Any]] = {
    "v1": {
        "base_path": f"{VERSION_PREFIX}",
        "default_prefix": "",
        "enabled": True,
        "swagger": {
            "title": "Zozi API v1",
            "description": "Version 1 of the Zozi E-commerce API",
            "version": "1.0.0",
        },
    },
}

# Version-specific settings
VERSION_SETTINGS: Dict[str, Dict[str, Any]] = {
    "v1": {
        "maintenance_mode": False,
        "rate_limit": "100 per minute",
        "cors_origins": ["*"],
        "supported_formats": ["application/json"],
        "authentication": "jwt",
    },
}


def get_version_path(version: str = "v1") -> str:
    """Get the path prefix for a specific API version.

    Args:
        version: API version (e.g., "v1", "v2""

    Returns:
        Full path prefix for the version

    Raises:
        ValueError: If version is not supported
    """
    if version not in VERSIONED_ROUTES:
        raise ValueError(f"Unsupported API version: {version}")

    route_config = VERSIONED_ROUTES[version]
    return route_config["base_path"] + route_config["default_prefix"]


def get_version_swagger_config(version: str = "v1") -> Dict[str, Any]:
    """Get Swagger configuration for a specific API version.

    Args:
        version: API version (e.g., "v1", "v2")

    Returns:
        Swagger configuration dictionary

    Raises:
        ValueError: If version is not supported
    """
    if version not in VERSIONED_ROUTES:
        raise ValueError(f"Unsupported API version: {version}")

    return VERSIONED_ROUTES[version]["swagger"].copy()


def get_version_settings(version: str = "v1") -> Dict[str, Any]:
    """Get settings for a specific API version.

    Args:
        version: API version (e.g., "v1", "v2")

    Returns:
        Version settings dictionary

    Raises:
        ValueError: If version is not supported
    """
    if version not in VERSION_SETTINGS:
        raise ValueError(f"Unsupported API version: {version}")

    return VERSION_SETTINGS[version].copy()


def is_version_enabled(version: str = "v1") -> bool:
    """Check if a specific API version is enabled.

    Args:
        version: API version (e.g., "v1", "v2")

    Returns:
        True if version is enabled, False otherwise
    """
    return VERSIONED_ROUTES.get(version, {}).get("enabled", True)


def get_active_versions() -> list[str]:
    """Get list of all active API versions.

    Returns:
        List of active version strings
    """
    return [
        version for version, config in VERSIONED_ROUTES.items()
        if config.get("enabled", True)
    ]


def versioned_prefix(path: str, version: str = "v1") -> str:
    """Build a versioned API path.

    Example::

        versioned_prefix("/users")  # => "/api/v1/users"
    """
    base = get_version_path(version)
    if path.startswith("/"):
        return f"{base}{path}"
    return f"{base}/{path}"


def versioned_route(version: str = "v1") -> str:
    """Get just the version base path for use as a FastAPI prefix.

    Example::

        router = APIRouter(prefix=versioned_route())
    """
    return get_version_path(version)


def migrate_to_version(
    from_version: str,
    to_version: str,
    settings: Optional[Dict[str, Any]] = None,
) -> bool:
    """Transition API from one version to another.

    Args:
        from_version: Current version
        to_version: Target version
        settings: Optional settings for the target version

    Returns:
        True if migration successful, False otherwise

    Note:
        This is a placeholder for actual migration logic
    """
    logger.warning(
        "API version migration from %s to %s is not yet implemented",
        from_version,
        to_version,
    )
    return False


def add_version(
    version: str,
    config: Optional[Dict[str, Any]] = None,
    settings: Optional[Dict[str, Any]] = None,
) -> bool:
    """Add a new API version.

    Args:
        version: Version to add (e.g., "v2")
        config: Route configuration for the version
        settings: Settings for the version

    Returns:
        True if version added successfully, False otherwise
    """
    if version in VERSIONED_ROUTES:
        logger.warning("Version %s already exists", version)
        return False

    VERSIONED_ROUTES[version] = config or {
        "base_path": f"{VERSION_PREFIX}/{version}",
        "default_prefix": "",
        "enabled": True,
        "swagger": {
            "title": f"Zozi API {version.upper()}",
            "description": f"Version {version} of the Zozi E-commerce API",
            "version": version,
        },
    }

    VERSION_SETTINGS[version] = settings or {
        "maintenance_mode": False,
        "rate_limit": "100 per minute",
        "cors_origins": ["*"],
        "supported_formats": ["application/json"],
        "authentication": "jwt",
    }

    logger.info("Added API version: %s", version)
    return True


def remove_version(version: str) -> bool:
    """Remove an API version.

    Args:
        version: Version to remove (e.g., "v2")

    Returns:
        True if version removed successfully, False otherwise
    """
    if version not in VERSIONED_ROUTES:
        logger.warning("Version %s does not exist", version)
        return False

    del VERSIONED_ROUTES[version]
    del VERSION_SETTINGS[version]

    logger.info("Removed API version: %s", version)
    return True