#!/usr/bin/env python3
"""Scan for HL303: broad `except Exception` handlers that neither log nor re-raise."""
import ast
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

SKIP_DIRS = {'__pycache__', 'venv', '.git', '_extra_files', 'tests', 'scripts', 'node_modules', '.mypy_cache'}


def _handler_logs(node):
    """Return True if the handler body contains a logger.* call or re-raise."""
    for stmt in node.body:
        # re-raise
        if isinstance(stmt, ast.Raise):
            return True
        # bare `return` is not logging
        if isinstance(stmt, ast.Return):
            continue
        for sub in ast.walk(stmt):
            if isinstance(sub, ast.Call):
                func = sub.func
                # logger.exception(...) / logger.error(...) / logger.warning(...)
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                    if func.value.id == 'logger' and func.attr in ('exception', 'error', 'warning', 'critical', 'info', 'debug'):
                        return True
                # structlog: log.exception / log.error
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                    if func.value.id in ('log', 'structlog_logger') and func.attr in ('exception', 'error', 'warning', 'critical', 'info'):
                        return True
                # self.logger.exception
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Attribute):
                    if getattr(func.value, 'attr', '') == 'logger' and func.attr in ('exception', 'error', 'warning'):
                        return True
    return False


def main():
    violations = []
    total_handlers = 0
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            if not fname.endswith('.py'):
                continue
            fpath = os.path.join(root, fname)
            relpath = os.path.relpath(fpath, '.')
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    source = f.read()
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ExceptHandler):
                        # broad except Exception (or except (SomeError, Exception))
                        types = []
                        if node.type is None:
                            continue  # bare except -> HL301
                        if isinstance(node.type, ast.Name) and node.type.id == 'Exception':
                            types = ['Exception']
                        elif isinstance(node.type, ast.Tuple):
                            for elt in node.type.elts:
                                if isinstance(elt, ast.Name) and elt.id == 'Exception':
                                    types.append('Exception')
                        if not types:
                            continue
                        total_handlers += 1
                        if not _handler_logs(node):
                            violations.append('%s:%d: except Exception without logging/re-raise' % (relpath, node.lineno))
            except (SyntaxError, UnicodeDecodeError):
                pass

    print('Total broad except Exception handlers: %d' % total_handlers)
    print('HL303 violations (no logging, no re-raise): %d' % len(violations))
    for v in violations[:60]:
        print('  ' + v)


if __name__ == '__main__':
    main()
