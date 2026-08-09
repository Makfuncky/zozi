import pathlib
import re

data_dir = pathlib.Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\data")

pattern = re.compile(
    r"try:\n"
    r"    _m = sys\.modules\[_target\]\n"
    r"except KeyError as e:\n"
    r"    logger\.exception\([^\n]*\)\n"
    r"    _m = importlib\.import_module\(_target\)\n",
    re.MULTILINE,
)

replacement = (
    "_m = sys.modules.get(_target)\n"
    "if _m is None:\n"
    "    _m = importlib.import_module(_target)\n"
)

fixed = 0
for p in sorted(data_dir.glob("*.py")):
    text = p.read_text(encoding="utf-8")
    if "sys.modules[_target]" in text and "logger.exception" in text:
        new_text, n = pattern.subn(replacement, text)
        if n:
            p.write_text(new_text, encoding="utf-8")
            fixed += 1

print(f"FIXED_SHIMS={fixed}")
