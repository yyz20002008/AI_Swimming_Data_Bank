from backend.ingest import ingest_data
import os

parsed_dir = "data/parsed"

files = [
    "all_meets_2023_2024.json",
    "all_meets_2024_2025.json",
    "all_meets_historical_extracted.json",
    "all_meets_2025_2026.json"
]

for fname in files:
    path = os.path.join(parsed_dir, fname)
    if not os.path.exists(path):
        print(f"File not found: {path}")
        continue
    print(f"\n==================================================")
    print(f"STARTING INGESTION OF: {fname}")
    print(f"==================================================")
    ingest_data(data_file=path, batch_size=500, season=None)
