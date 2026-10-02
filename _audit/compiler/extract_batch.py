import json

with open(r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\_audit\compiler\batches_small.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total batches: {len(data)}")
print(f"Batch 49 files: {len(data[49])}")

for i, file_entry in enumerate(data[49]):
    print(f"File {i}: {file_entry[1]}")

# Write batch 49 to file
with open(r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\_audit\compiler\batch_49_extract.json', 'w', encoding='utf-8') as f:
    json.dump(data[49], f, indent=2)
