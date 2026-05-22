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
        print(f"{fname}: File not found")
        continue
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"{fname}: len={len(data)}")
            if len(data) > 0:
                first = data[0]
                print(f"  type(first)={type(first)}")
                if isinstance(first, dict):
                    print(f"  keys in first: {list(first.keys())}")
                    meet = first.get("meet", {})
                    print(f"  meet keys: {list(meet.keys()) if isinstance(meet, dict) else type(meet)}")
                    print(f"  meet name: {meet.get('name') if isinstance(meet, dict) else 'N/A'}")
                    print(f"  meet start_date: {meet.get('start_date') if isinstance(meet, dict) else 'N/A'}")
    except Exception as e:
        print(f"{fname}: error: {e}")
