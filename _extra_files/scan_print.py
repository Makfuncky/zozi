#!/usr/bin/env python3
"""Scan for print() statements in application code (HL201 / QUAL4).

Skips: __pycache__, venv, .git, _extra_files, tests, scripts, alembic, data/,
migrations, and files whose primary purpose is CLI/scripting (tools/, tasks/,
dependencies/ seed files).
"""
import ast
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

SKIP_DIRS = {'__pycache__', 'venv', '.git', '_extra_files', 'tests', 'scripts',
             'node_modules', '.mypy_cache', 'alembic', 'out', 'docs'}
SKIP_FILE_PREFIXES = ('_triage',)


def main():
    violations = []
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            if not fname.endswith('.py'):
                continue
            fpath = os.path.normpath(os.path.join(root, fname))
            relpath = os.path.relpath(fpath, '.')
            if relpath.startswith(SKIP_FILE_PREFIXES):
                continue
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    source = f.read()
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        func = node.func
                        # print(...) direct call
                        if isinstance(func, ast.Name) and func.id == 'print':
                            violations.append('%s:%d: print(...) %s' % (relpath, node.lineno, (ast.get_source_segment(source, node) or '')[:60]))
                        # sys.stdout.write / sys.stderr.write
                        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Attribute):
                            if func.value.attr in ('stdout', 'stderr') and func.attr == 'write':
                                violations.append('%s:%d: sys.%s.write(...)' % (relpath, node.lineno, func.value.attr))
            except (SyntaxError, UnicodeDecodeError):
                pass

    print('Total print()/write() statements in app code: %d' % len(violations))
    # group by file
    by_file = {}
    for v in violations:
        f = v.split(':')[0]
        by_file.setdefault(f, []).append(v)
    print('Files with print(): %d' % len(by_file))
    for f, vs in sorted(by_file.items()):
        print('  %s (%d)' % (f, len(vs)))
    print('\n--- First 40 details ---')
    for v in violations[:40]:
        print('  ' + v)


if __name__ == '__main__':
    main()
