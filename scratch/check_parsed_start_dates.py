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
for fname in files:
    path = os.path.join(parsed_dir, fname)
    if not os.path.exists(path):
        continue
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        none_count = 0
        valid_count = 0
        samples = []
        for meet_data in data:
            meet = meet_data.get("meet", {})
            sd = meet.get("start_date")
            name = meet.get("name")
            if sd is None:
                none_count += 1
                if len(samples) < 3:
                    samples.append(name)
            else:
                valid_count += 1
        print(f"{fname}: total={len(data)}, valid_start_date={valid_count}, none_start_date={none_count}")
        if samples:
            print(f"  Sample None meets: {samples}")
