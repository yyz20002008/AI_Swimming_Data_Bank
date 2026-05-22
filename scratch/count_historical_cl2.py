import os
import glob

raw_dir = r"d:\Backup-STUDY-7-22-2018\AI_Swimming_Data_Bank\data\raw"

seasons = ["2023_2024", "2024_2025", "2025_2026", "historical", "historical/extracted"]

for season in seasons:
    path = os.path.join(raw_dir, season)
    cl2_files = glob.glob(os.path.join(path, "**", "*.cl2"), recursive=True)
    print(f"Season '{season}': found {len(cl2_files)} CL2 files in {path}")
