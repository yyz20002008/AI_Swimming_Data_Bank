import os
import json

parsed_dir = "data/parsed"
for f in os.listdir(parsed_dir):
    if f.endswith(".json"):
        path = os.path.join(parsed_dir, f)
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
                print(f"{f}: {len(data)} meets")
        except Exception as e:
            print(f"Error reading {f}: {e}")
