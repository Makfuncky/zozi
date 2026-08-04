"""Tests for API versioning utilities."""
import pytest

from utils.versioning import (
    VERSION_PREFIX,
    VERSIONED_ROUTES,
    VERSION_SETTINGS,
    get_version_path,
    get_version_swagger_config,
    get_version_settings,
    is_version_enabled,
    get_active_versions,
    migrate_to_version,
    add_version,
    remove_version,
    versioned_prefix,
    versioned_route,
)


class TestConstants:
    def test_version_prefix(self):
        assert VERSION_PREFIX == "/api/v1"

    def test_v1_route_config(self):
        assert "v1" in VERSIONED_ROUTES
        v1 = VERSIONED_ROUTES["v1"]
        assert v1["base_path"] == "/api/v1"
        assert v1["enabled"] is True

    def test_v1_settings(self):
        assert "v1" in VERSION_SETTINGS
        v1 = VERSION_SETTINGS["v1"]
        assert v1["authentication"] == "jwt"
        assert v1["maintenance_mode"] is False


class TestGetVersionPath:
    def test_v1_path(self):
        path = get_version_path("v1")
        assert path == "/api/v1"

    def test_invalid_version(self):
        with pytest.raises(ValueError, match="Unsupported API version"):
            get_version_path("v99")


class TestVersionedHelpers:
    def test_versioned_prefix(self):
        result = versioned_prefix("/users")
        assert result == "/api/v1/users"

    def test_versioned_prefix_no_leading_slash(self):
        result = versioned_prefix("users")
        assert result == "/api/v1/users"

    def test_versioned_prefix_custom_version(self):
        result = versioned_prefix("/products", version="v1")
        assert result == "/api/v1/products"

    def test_versioned_route(self):
        result = versioned_route()
        assert result == "/api/v1"

    def test_versioned_route_explicit(self):
        result = versioned_route(version="v1")
        assert result == "/api/v1"


class TestSwaggerConfig:
    def test_get_swagger_config(self):
        config = get_version_swagger_config("v1")
        assert config["title"] == "Zozi API v1"
        assert "version" in config

    def test_swagger_config_copy(self):
        config = get_version_swagger_config("v1")
        config["title"] = "modified"
        original = get_version_swagger_config("v1")
        assert original["title"] == "Zozi API v1"


class TestVersionSettings:
    def test_get_version_settings(self):
        settings = get_version_settings("v1")
        assert settings["rate_limit"] == "100 per minute"
        assert settings["cors_origins"] == ["*"]

    def test_version_settings_copy(self):
        settings = get_version_settings("v1")
        settings["rate_limit"] = "changed"
        original = get_version_settings("v1")
        assert original["rate_limit"] == "100 per minute"


class TestVersionManagement:
    def test_is_version_enabled(self):
        assert is_version_enabled("v1") is True

    def test_is_version_enabled_missing(self):
        enabled = is_version_enabled("v99")
        assert enabled is True  # returns default True for unknown versions

    def test_get_active_versions(self):
        active = get_active_versions()
        assert "v1" in active

    def test_add_and_remove_version(self):
        result = add_version("v2")
        assert result is True
        assert "v2" in VERSIONED_ROUTES
        assert is_version_enabled("v2") is True

        result = remove_version("v2")
        assert result is True
        assert "v2" not in VERSIONED_ROUTES

    def test_add_duplicate_version(self):
        result = add_version("v1")
        assert result is False  # already exists

    def test_remove_nonexistent_version(self):
        result = remove_version("v99")
        assert result is False

    def test_migrate_to_version_not_implemented(self):
        result = migrate_to_version("v1", "v2")
        assert result is False

    def test_add_version_with_custom_config(self):
        custom_config = {
            "base_path": "/api/v2",
            "default_prefix": "",
            "enabled": True,
            "swagger": {"title": "Zozi API v2", "version": "2.0.0"},
        }
        custom_settings = {
            "rate_limit": "200 per minute",
            "authentication": "jwt",
        }
        result = add_version("v2-test", config=custom_config, settings=custom_settings)
        assert result is True
        assert get_version_settings("v2-test")["rate_limit"] == "200 per minute"
        remove_version("v2-test")


class TestEdgeCases:
    def test_versioned_prefix_with_version_parameter(self):
        result = versioned_prefix("/admin/users", version="v1")
        assert result.startswith("/api/v1")

    def test_versioned_route_consistent_with_prefix(self):
        route = versioned_route()
        prefix = versioned_prefix("/test")
        assert prefix.startswith(route)

    def test_empty_path_versioned_prefix(self):
        result = versioned_prefix("", version="v1")
        assert result == "/api/v1/"
