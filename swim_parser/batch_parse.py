from __future__ import annotations

"""
Batch parser: processes all CL2 files from downloaded meets
and outputs combined JSON + summary statistics.
"""
import json
import os
import glob
from swim_parser.cl2_parser import parse_cl2_file

RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")
PARSED_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "parsed")


def batch_parse(season: str = "2023_2024"):
    """Parse all CL2 files for a season and output combined results."""
    season_dir = os.path.join(RAW_DIR, season)
    if not os.path.isdir(season_dir):
        print(f"Season dir not found: {season_dir}")
        return

    cl2_files = glob.glob(os.path.join(season_dir, "**", "*.cl2"), recursive=True)
    print(f"Found {len(cl2_files)} CL2 files in {season}")

    all_meets = []
    total_swimmers = 0
    total_results = 0
    errors = []

    for i, fp in enumerate(sorted(cl2_files), 1):
        meet_name = os.path.basename(os.path.dirname(fp))
        try:
            data = parse_cl2_file(fp)
            n_swim = len(data["swimmers"])
            n_res = data["total_results"]
            total_swimmers += n_swim
            total_results += n_res
            all_meets.append(data)
            print(f"  [{i:2d}/{len(cl2_files)}] {data['meet'].get('name', meet_name)[:50]:50s}  "
                  f"swimmers={n_swim:4d}  results={n_res:5d}")
        except Exception as e:
            errors.append((fp, str(e)))
            print(f"  [{i:2d}/{len(cl2_files)}] ERROR {meet_name}: {e}")

    # Save combined output
    os.makedirs(PARSED_DIR, exist_ok=True)
    safe_season = season.replace("/", "_").replace("\\", "_")
    out_path = os.path.join(PARSED_DIR, f"all_meets_{safe_season}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_meets, f, indent=2, default=str)

    print(f"\n{'='*60}")
    print(f"BATCH PARSE SUMMARY — {season}")
    print(f"  Meets parsed:  {len(all_meets)}")
    print(f"  Errors:        {len(errors)}")
    print(f"  Total swimmers (with dups): {total_swimmers:,}")
    print(f"  Total results: {total_results:,}")
    print(f"  Output: {out_path}")

    if errors:
        print(f"\n  ERRORS:")
        for fp, err in errors:
            print(f"    {os.path.basename(fp)}: {err}")

    return all_meets


if __name__ == "__main__":
    batch_parse()
