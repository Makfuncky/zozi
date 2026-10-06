import sys
import os

def test_debug_rbac_import():
    sys.path.insert(0, 'D:/Projects/10_E_COMMERCE_WEBSITE/zozi/backend')
    os.environ.setdefault("APP_ENV", "test")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only-do-not-use-in-production")
    os.environ.setdefault("DATABASE_URL", "sqlite://")
    os.environ.setdefault("VALKEY_URL", "valkey://localhost:6379")
    
    import config
    config.settings.database_url = "sqlite://"
    config.settings.valkey_url = "valkey://localhost:6379"
    
    for key in ("rbac", "rbac.models"):
        sys.modules.pop(key, None)
    
    from rbac.models.permission_entities import PermissionCategory
    print("PermissionCategory imported OK")
    assert PermissionCategory is not None
