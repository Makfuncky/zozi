#!/usr/bin/env python3
"""Add `import logging` + `logger = logging.getLogger(__name__)` at top level
of files that reference `logger.` but have no logger definition.

Safe insertion: after module docstring / `from __future__` block, before the
first non-import statement, at column 0.
"""
import os
import re
import sys
import py_compile

sys.stdout.reconfigure(encoding='utf-8')

FILES = [
    'controllers/core/admin_database_controller.py',
    'data/services_auto_payout_scheduler.py',
    'routers/api_commerce_routes_2.py',
    'routers/api_comms_messaging_2.py',
    'routers/api_comms_messaging_3.py',
    'routers/supplier_supplier_routes.py',
    'services/comms/command_center_query_service.py',
    'services/comms/communication_read_service.py',
    'services/comms/notification_engine.py',
    'services/comms/websocket_manager.py',
    'services/core/db_health_service.py',
    'services/finance/finance_transfer_service.py',
    'services/hr/employee_write_service.py',
    'services/logistics/logistics_partner_pricing.py',
]


def add_logger(fpath):
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    if re.search(r'\blogger\s*=\s*logging\.getLogger', content):
        return 'already-has-logger'

    lines = content.split('\n')
    insert_idx = 0
    in_docstring = False

    for idx, ln in enumerate(lines):
        s = ln.strip()
        if idx == 0 and (s.startswith('"""') or s.startswith("'''")):
            in_docstring = True
            if s.count('"""') >= 2 or s.count("'''") >= 2:
                in_docstring = False
            insert_idx = idx + 1
            continue
        if in_docstring:
            if '"""' in s or "'''" in s:
                in_docstring = False
            insert_idx = idx + 1
            continue
        if s.startswith('from __future__'):
            insert_idx = idx + 1
            continue
        if s.startswith('import ') or s.startswith('from '):
            insert_idx = idx + 1
            continue
        if s == '' or s.startswith('#'):
            continue
        break

    has_logging_import = bool(re.search(r'^import logging', content, re.M))
    block = []
    if not has_logging_import:
        block.append('import logging')
    block.append('logger = logging.getLogger(__name__)')
    block.append('')

    new_lines = lines[:insert_idx] + block + lines[insert_idx:]
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

    try:
        py_compile.compile(fpath, doraise=True)
    except py_compile.PyCompileError as e:
        print('  !! COMPILE ERROR: %s' % e)
        return 'compile-error'
    return 'ok'


for f in FILES:
    fpath = os.path.normpath(f)
    if not os.path.exists(fpath):
        print('SKIP %s (missing)' % f)
        continue
    result = add_logger(fpath)
    print('%s -> %s' % (f, result))
