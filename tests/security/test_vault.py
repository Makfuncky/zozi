import ast
import pathlib

VAULT_PATH = pathlib.Path(__file__).resolve().parents[2] / "backend" / "infrastructure" / "security" / "vault.py"


def test_no_raw_os_getenv_for_vault_master_key():
    source = VAULT_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if node.func.value.id == "os" and node.func.attr == "getenv":
                    args = [ast.unparse(arg) for arg in node.args]
                    if any('ZOZI_VAULT_MASTER_KEY' in arg for arg in args):
                        raise AssertionError(
                            "raw os.getenv for ZOZI_VAULT_MASTER_KEY found in vault.py"
                        )
