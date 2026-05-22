import os
import json

files = [
    "all_meets_2023_2024.json",
    "all_meets_2024_2025.json",
    "all_meets_2025_2026.json",
    "all_meets_historical.json",
    "all_meets_historical_extracted.json"
]

parsed_dir = "data/parsed"
unique_meets = {}

for fname in files:
    path = os.path.join(parsed_dir, fname)
    if not os.path.exists(path):
        print(f"File not found: {fname}")
        continue
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        for idx, meet_data in enumerate(data):
            meet = meet_data.get("meet", {})
            name = meet.get("name")
            start_date = meet.get("start_date")
            course = meet.get("course", "SCY")
            if not name or not start_date:
                continue
            key = (name, start_date, course)
            if key not in unique_meets:
                unique_meets[key] = []
            unique_meets[key].append(fname)

print(f"Total unique meets across files: {len(unique_meets)}")

# Analyze overlaps
overlap_counts = {}
for key, file_list in unique_meets.items():
    l = len(file_list)
    overlap_counts[l] = overlap_counts.get(l, 0) + 1

print("\nOverlap counts:")
for l, count in sorted(overlap_counts.items()):
    print(f"  Meets appearing in {l} files: {count}")

# Print sample overlap
print("\nSample overlaps (appearing in multiple files):")
printed = 0
for key, file_list in unique_meets.items():
    if len(file_list) > 1:
        print(f"  {key}: {file_list}")
        printed += 1
        if printed >= 5:
            break
