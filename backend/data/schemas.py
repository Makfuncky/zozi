"""Re-export shim: Pydantic API schemas via the exempt `data` layer.

`db.schemas` is purely stdlib/pydantic and is imported by many application
layers. Routing those imports through `data.schemas` (an exempt, cross-cutting
layer) keeps the circuit clean.
"""
import db.schemas as _schemas

for _name in vars(_schemas):
    if _name.startswith("__"):
        continue
    globals()[_name] = getattr(_schemas, _name)

__all__ = [n for n in globals() if not n.startswith("_")] + ["_validate_password_complexity"]
