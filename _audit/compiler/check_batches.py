import json
from pathlib import Path

d = json.load(open('_audit/compiler/batches_small.json'))
print('Total batches:', len(d))

# Show structure of first batch
b0 = d[0]
print('\nBatch 0 (first batch):')
for i, item in enumerate(b0):
    item_type = type(item).__name__
    item_len = len(item) if isinstance(item, list) else 'N/A'
    print(f'  Item {i}: type={item_type}, len={item_len}')
    if isinstance(item, list) and len(item) > 1:
        item1 = str(item[1])[:80] if len(item) > 1 else 'none'
        print(f'    [0]={item[0]}, [1]={item1}')

# List all batch files (first entry of each batch item)
print('\nAll batches overview:')
for batch_idx, batch in enumerate(d):
    files = []
    for item in batch:
        if isinstance(item, list) and len(item) > 1:
            files.append(str(item[1])[:60])
    print(f'Batch {batch_idx}: {files}')
