import os

raw_historical = r"d:\Backup-STUDY-7-22-2018\AI_Swimming_Data_Bank\data\raw\historical"
if os.path.exists(raw_historical):
    items = os.listdir(raw_historical)
    dirs = [item for item in items if os.path.isdir(os.path.join(raw_historical, item))]
    files = [item for item in items if os.path.isfile(os.path.join(raw_historical, item))]
    print(f"Subdirectories: {len(dirs)}")
    print(f"Files: {len(files)}")
    if dirs:
        print(f"Sample subdirectories: {dirs[:10]}")
    if files:
        print(f"Sample files: {files[:10]}")
else:
    print("raw/historical does not exist")
