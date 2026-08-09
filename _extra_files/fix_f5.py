import os

repo = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
src = os.path.join(repo, "backend", ".env")
dst = os.path.join(repo, "backend", ".env.local")
if os.path.exists(src):
    os.rename(src, dst)
    print("renamed .env -> .env.local")
else:
    print("source .env not found; dst exists?", os.path.exists(dst))

cfg = os.path.join(repo, "backend", "utils", "config.py")
s = open(cfg, encoding="utf-8").read()
old = '''try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass
    logger.exception("Handled ImportError")'''
new = '''# Load local secrets from .env.local (gitignored). Fall back to .env only if
# present for backward compatibility. Production MUST inject secrets via the
# environment / a secrets manager -- no plaintext secret file should ship in VCS.
for _ENV_FILENAME in (".env.local", ".env"):
    _ENV_PATH = BASE_DIR / _ENV_FILENAME
    if _ENV_PATH.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(_ENV_PATH)
        except ImportError:
            logger.exception("Handled ImportError")
        break'''
assert old in s, "old load_dotenv block not found"
s = s.replace(old, new)
open(cfg, "w", encoding="utf-8").write(s)
print("config.py updated")
