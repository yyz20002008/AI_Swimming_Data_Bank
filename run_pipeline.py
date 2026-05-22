from __future__ import annotations

"""
Master pipeline runner for Maryland Swimming Data.
Ties together:
1. Scraping meet schedule (manifest)
2. Downloading new meet results zip files
3. Parsing downloaded meet CL2 files
4. Ingestion of the parsed data into Supabase
"""

import argparse
import os
import sys
from scraper.config import SEASON_PAGES
from scraper.meet_list_scraper import scrape_season
from scraper.file_downloader import download_meet_results
from swim_parser.batch_parse import batch_parse
from backend.ingest import ingest_data


def get_latest_season() -> str:
    """Gets the latest configured season from scraper config."""
    seasons = sorted(SEASON_PAGES.keys())
    if not seasons:
        raise ValueError("No seasons configured in scraper/config.py")
    return seasons[-1]


def main():
    parser = argparse.ArgumentParser(
        description="Run the complete Maryland Swimming ingestion pipeline."
    )
    parser.add_argument(
        "--season",
        default=None,
        help="Season to process (e.g. 2025-2026). Defaults to the latest configured season.",
    )
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Skip scraping the meet list manifest from GoMotion.",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip downloading and extracting new meet ZIP files.",
    )
    parser.add_argument(
        "--skip-parse",
        action="store_true",
        help="Skip parsing raw meet files to JSON.",
    )
    parser.add_argument(
        "--skip-ingest",
        action="store_true",
        help="Skip ingesting parsed JSON into Supabase database.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of meets to download (useful for testing).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Batch size for Supabase database inserts.",
    )

    args = parser.parse_args()

    # Determine season
    season = args.season
    if not season:
        season = get_latest_season()

    # Normalize season name for parser/folders
    # e.g., "2025-2026" -> "2025_2026"
    normalized_season = season.replace("-", "_")

    print("=" * 60)
    print(f"Maryland Swimming Pipeline Runner - Season: {season}")
    print("=" * 60)

    # Step 1: Scrape meet schedule manifest
    if not args.skip_scrape:
        print("\n--- [STEP 1/4] Scraping Meet Manifest ---")
        try:
            scrape_season(season)
            print("✓ Scraping completed successfully.")
        except Exception as e:
            print(f"✗ Scraping failed: {e}")
            sys.exit(1)
    else:
        print("\n--- [STEP 1/4] Scraping Meet Manifest (SKIPPED) ---")

    # Step 2: Download files
    if not args.skip_download:
        print("\n--- [STEP 2/4] Downloading Meet Results ZIPs ---")
        try:
            download_meet_results(season, limit=args.limit, skip_existing=True)
            print("✓ Downloading/extraction completed successfully.")
        except Exception as e:
            print(f"✗ Downloading/extraction failed: {e}")
            sys.exit(1)
    else:
        print("\n--- [STEP 2/4] Downloading Meet Results ZIPs (SKIPPED) ---")

    # Step 3: Parse downloaded CL2 files
    if not args.skip_parse:
        print("\n--- [STEP 3/4] Parsing CL2 Files ---")
        try:
            batch_parse(normalized_season)
            print("✓ Parsing completed successfully.")
        except Exception as e:
            print(f"✗ Parsing failed: {e}")
            sys.exit(1)
    else:
        print("\n--- [STEP 3/4] Parsing CL2 Files (SKIPPED) ---")

    # Step 4: Ingest into Supabase
    if not args.skip_ingest:
        print("\n--- [STEP 4/4] Ingesting parsed JSON into Supabase ---")
        parsed_file = os.path.join("data", "parsed", f"all_meets_{normalized_season}.json")
        if not os.path.exists(parsed_file):
            print(f"✗ Ingestion failed: Parsed JSON file not found: {parsed_file}")
            sys.exit(1)
        try:
            stats = ingest_data(data_file=parsed_file, batch_size=args.batch_size, season=None)
            print("\n✓ Ingestion completed successfully!")
            print(f"  Inserted {stats.get('meets_inserted', 0)} meets, "
                  f"{stats.get('results_inserted', 0)} results.")
        except Exception as e:
            print(f"✗ Ingestion failed: {e}")
            sys.exit(1)
    else:
        print("\n--- [STEP 4/4] Ingesting parsed JSON into Supabase (SKIPPED) ---")

    print("\n" + "=" * 60)
    print("PIPELINE RUN COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nReminder: Materialized views in Supabase should be refreshed manually if needed:")
    print("  Run in SQL Editor: SELECT refresh_all_views();")


if __name__ == "__main__":
    main()
