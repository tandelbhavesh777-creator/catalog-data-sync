import json
import os
import sys

# Usage: python split_json.py <input_json_path> <output_dir> <max_mb>
input_path = sys.argv[1]
output_dir = sys.argv[2]
max_bytes = int(float(sys.argv[3]) * 1024 * 1024)

os.makedirs(output_dir, exist_ok=True)

with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Automatically detect top-level list keys (e.g., "items", "movies", "series")
list_keys = [k for k, v in data.items() if isinstance(v, list)]
meta = {k: v for k, v in data.items() if not isinstance(v, list)}

tagged_items = []
for k in list_keys:
    for item in data[k]:
        tagged_items.append((k, item))

def build_chunk(buckets, part_num, total_parts=0):
    obj = dict(meta)
    obj["part"] = part_num
    if total_parts > 0:
        obj["total_parts"] = total_parts
    for k in list_keys:
        obj[k] = buckets[k]
    return json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")

chunks = []
curr_buckets = {k: [] for k in list_keys}
curr_size = len(build_chunk(curr_buckets, 999, 999)) + 100

for key, item in tagged_items:
    item_bytes = len(json.dumps(item, ensure_ascii=False, indent=2).encode("utf-8")) + 6
    if curr_size + item_bytes > max_bytes and any(curr_buckets[k] for k in list_keys):
        chunks.append(curr_buckets)
        curr_buckets = {k: [] for k in list_keys}
        curr_size = len(build_chunk(curr_buckets, 999, 999)) + 100
    curr_buckets[key].append(item)
    curr_size += item_bytes

if any(curr_buckets[k] for k in list_keys):
    chunks.append(curr_buckets)

total = len(chunks)
for idx, buckets in enumerate(chunks, 1):
    raw = build_chunk(buckets, idx, total)
    out_file = os.path.join(output_dir, f"catalog_part{idx}.json")
    with open(out_file, "wb") as out:
        out.write(raw)
    print(f"Saved {out_file} ({len(raw) / (1024 * 1024):.2f} MB)")
