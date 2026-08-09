#!/usr/bin/env python3
"""Add logger definitions to files that use logger.exception() but have no logger."""
import os, sys

sys.stdout.reconfigure(encoding='utf-8')

files_needing_logger = [
    'alembic/versions/2026_07_31_0011_add_composite_indexes.py',
    'controllers/catalog/search_controller.py',
    'controllers/commerce/admin_coupons_controller.py',
    'controllers/core/admin_users_controller.py',
    'controllers/orders/admin_orders_controller.py',
    'routers/admin_core_routes_3.py',
    'routers/api_comms_inbound.py',
    'routers/api_security_detection.py',
    'services/catalog/advanced_filter_service.py',
    'services/core/misc_write_service.py',
    'services/geography/country_maps_service.py',
    'services/geography/cross_border_service.py',
    'services/security/security_router_service.py',
    'services/supplier/supplier_read_service.py',
]

fixed = []
for fpath in files_needing_logger:
    if not os.path.exists(fpath):
        continue
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if it already has logger
    if 'logger = ' in content or 'logger= ' in content:
        continue

    # Find the right place to insert logger (after last import)
    lines = content.split('\n')
    insert_idx = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('import ') or stripped.startswith('from '):
            insert_idx = i + 1

    # Check if logging is already imported
    has_logging = 'import logging' in content

    # Insert logger after imports
    if has_logging:
        logger_line = 'logger = logging.getLogger(__name__)'
    else:
        logger_line = 'import logging\nlogger = logging.getLogger(__name__)'

    lines.insert(insert_idx, logger_line)
    lines.insert(insert_idx + 1, '')

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    fixed.append(fpath)

print(f'Added logger to {len(fixed)} files')
for f in fixed:
    print(f'  {f}')
