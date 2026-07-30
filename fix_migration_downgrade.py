with open('backend/alembic/versions/2026_07_28_19_30-e8efae30fc29_add_missing_indexes_and_constraints.py', 'r') as f:
    lines = f.readlines()

# Remove lines 249-257 (0-indexed: 248-256) which are the email_delivery_events DROP COLUMN statements in downgrade
new_lines = lines[:248] + lines[257:]

with open('backend/alembic/versions/2026_07_28_19_30-e8efae30fc29_add_missing_indexes_and_constraints.py', 'w') as f:
    f.writelines(new_lines)

print('Removed email_delivery_events DROP COLUMN from downgrade')
