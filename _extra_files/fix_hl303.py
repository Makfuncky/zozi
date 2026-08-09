#!/usr/bin/env python3
"""Fix HL303: add `logger.exception(...)` to broad `except Exception` handlers
that neither log nor re-raise.  Uses line-number insertion (safe, AST-guided),
then verifies each file compiles.

IMPORTANT: For handlers whose body is ONLY `pass`, HL302 handles them; here we
skip pure-pass handlers and handlers that already re-raise.
"""
import ast
import os
import re
import sys
import py_compile

sys.stdout.reconfigure(encoding='utf-8')

SKIP_DIRS = {'__pycache__', 'venv', '.git', '_extra_files', 'tests', 'scripts', 'node_modules', '.mypy_cache'}
SKIP_FILES = set()  # add files to skip if needed


def _handler_is_flagable(node):
    """Broad except Exception that does NOT log and does NOT re-raise."""
    if node.type is None:
        return False  # bare except -> HL301, not our scope here
    types = []
    if isinstance(node.type, ast.Name) and node.type.id == 'Exception':
        types = ['Exception']
    elif isinstance(node.type, ast.Tuple):
        for elt in node.type.elts:
            if isinstance(elt, ast.Name) and elt.id == 'Exception':
                types.append('Exception')
    if not types:
        return False

    body = node.body
    # skip pure-pass handlers (HL302 scope)
    if len(body) == 1 and isinstance(body[0], ast.Pass):
        return False

    logs = False
    re_raises = False
    for stmt in body:
        if isinstance(stmt, ast.Raise):
            re_raises = True
        for sub in ast.walk(stmt):
            if isinstance(sub, ast.Call):
                func = sub.func
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                    if func.value.id == 'logger' and func.attr in ('exception', 'error', 'warning', 'critical', 'info', 'debug'):
                        logs = True
                    if func.value.id in ('log',) and func.attr in ('exception', 'error', 'warning', 'critical'):
                        logs = True
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Attribute):
                    if getattr(func.value, 'attr', '') == 'logger' and func.attr in ('exception', 'error', 'warning'):
                        logs = True
    return (not logs) and (not re_raises)


def _find_handler_start(line, lines):
    """Find the indentation of the handler body from the except line."""
    # except line is `    except Exception:` -> indent is its leading spaces + 4
    m = re.match(r'^(\s*)', line)
    return len(m.group(1)) + 4


def fix_file(fpath):
    with open(fpath, 'r', encoding='utf-8') as f:
        source = f.read()
    tree = ast.parse(source)
    lines = source.split('\n')

    flagged = [n for n in ast.walk(tree) if isinstance(n, ast.ExceptHandler) and _handler_is_flagable(n)]
    if not flagged:
        return 0

    has_logger = bool(re.search(r'\blogger\b', source))
    if not has_logger:
        return -1  # needs logger bootstrap - handled separately

    # Insert logger.exception as first statement of each handler.
    # Process handlers in REVERSE line order so insertions don't shift later lines.
    flagged.sort(key=lambda n: n.body[0].lineno, reverse=True)
    for node in flagged:
        first_stmt = node.body[0]
        insert_at = first_stmt.lineno - 1  # 0-indexed line of first body statement
        indent = ' ' * _find_handler_start(lines[node.lineno - 1], lines)
        # Build a descriptive message from the except line context
        msg = 'Handled Exception in %s:%d' % (os.path.basename(fpath), node.lineno)
        new_line = '%slogger.exception("%s")\n' % (indent, msg)
        lines.insert(insert_at, new_line.rstrip('\n'))

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    # verify
    try:
        py_compile.compile(fpath, doraise=True)
    except py_compile.PyCompileError as e:
        print('  !! COMPILE ERROR after fix: %s' % e)
        return -2
    return len(flagged)


def main():
    fixed = 0
    errors = []
    need_logger = []
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            if not fname.endswith('.py'):
                continue
            fpath = os.path.normpath(os.path.join(root, fname))
            if fpath in SKIP_FILES:
                continue
            relpath = os.path.relpath(fpath, '.')
            try:
                result = fix_file(fpath)
                if result > 0:
                    fixed += result
                    print('FIXED %s (%d handlers)' % (relpath, result))
                elif result == -1:
                    need_logger.append(relpath)
            except (SyntaxError, UnicodeDecodeError) as e:
                errors.append('%s: %s' % (relpath, e))

    print('\nTotal handlers fixed: %d' % fixed)
    if need_logger:
        print('\nFiles needing logger bootstrap (%d):' % len(need_logger))
        for f in need_logger:
            print('  %s' % f)
    if errors:
        print('\nErrors (%d):' % len(errors))
        for e in errors[:10]:
            print('  %s' % e)


if __name__ == '__main__':
    main()
