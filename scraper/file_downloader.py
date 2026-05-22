from __future__ import annotations

"""
File Downloader for swimming meet result archives.

Downloads ZIP files from the meet manifest, extracts them,
and organizes CL2/HY3/SD3 files into a structured directory.
"""
import json
import os
import re
import time
import zipfile
from pathlib import Path
from typing import Optional

import requests

from scraper.config import (
    RAW_DIR, MANIFEST_DIR, USER_AGENT, REQUEST_DELAY_SECONDS,
    REQUEST_TIMEOUT_SECONDS, MAX_RETRIES, RETRY_BACKOFF_FACTOR,
    RESULT_FILE_EXTENSIONS,
)


def _sanitize_dirname(name: str) -> str:
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name[:80]


def download_file(url: str, dest_path: str, retries: int = MAX_RETRIES) -> bool:
    headers = {"User-Agent": USER_AGENT}
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS, stream=True)
            resp.raise_for_status()
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            size = os.path.getsize(dest_path)
            print(f"    OK ({size:,}B): {os.path.basename(dest_path)}")
            return True
        except requests.RequestException as e:
            wait = RETRY_BACKOFF_FACTOR ** attempt
            print(f"    FAIL {attempt+1}/{retries}: {e}")
            if attempt < retries - 1:
                time.sleep(wait)
    return False


def extract_zip(zip_path: str, extract_dir: str) -> list[str]:
    data_files = []
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
            for name in zf.namelist():
                ext = os.path.splitext(name)[1].lower()
                if ext in RESULT_FILE_EXTENSIONS:
                    full_path = os.path.join(extract_dir, name)
                    data_files.append(full_path)
                    print(f"    Found: {name} ({ext})")
    except zipfile.BadZipFile:
        print(f"    Bad ZIP: {zip_path}")
    except Exception as e:
        print(f"    Error: {e}")
    return data_files


def download_meet_results(season: str, limit: Optional[int] = None, skip_existing: bool = True) -> dict:
    manifest_path = os.path.join(MANIFEST_DIR, f"meet_manifest_{season}.json")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest not found: {manifest_path}. Run meet_list_scraper.py first.")

    with open(manifest_path, "r", encoding="utf-8") as f:
        meets = json.load(f)

    print(f"\nDownloading {season} ({len(meets)} meets)")
    season_dir = os.path.join(RAW_DIR, season.replace("-", "_"))
    os.makedirs(season_dir, exist_ok=True)

    stats = {"total": len(meets), "downloaded": 0, "skipped": 0, "no_zip": 0, "failed": 0, "files": []}
    to_process = meets[:limit] if limit else meets

    for i, meet in enumerate(to_process, 1):
        name = meet.get("name", "Unknown").replace('\xa0', ' ').encode('ascii', 'replace').decode()
        zip_url = meet.get("result_zip_url")
        print(f"\n[{i}/{len(to_process)}] {name}")

        if not zip_url:
            print("    No result ZIP")
            stats["no_zip"] += 1
            continue

        meet_dir = os.path.join(season_dir, _sanitize_dirname(name))
        os.makedirs(meet_dir, exist_ok=True)
        zip_filename = zip_url.split("/")[-1].split("?")[0]
        zip_path = os.path.join(meet_dir, zip_filename)

        if skip_existing and os.path.exists(zip_path):
            print(f"    Exists: {zip_filename}")
            stats["skipped"] += 1
            # Check for already-extracted data files
            for fn in os.listdir(meet_dir):
                ext = os.path.splitext(fn)[1].lower()
                if ext in RESULT_FILE_EXTENSIONS:
                    stats["files"].append(os.path.join(meet_dir, fn))
            continue

        if download_file(zip_url, zip_path):
            stats["downloaded"] += 1
            data_files = extract_zip(zip_path, meet_dir)
            stats["files"].extend(data_files)
        else:
            stats["failed"] += 1

        time.sleep(REQUEST_DELAY_SECONDS)

    print(f"\nSummary: {stats['downloaded']} downloaded, {stats['skipped']} skipped, "
          f"{stats['no_zip']} no ZIP, {stats['failed']} failed, {len(stats['files'])} data files")

    report_path = os.path.join(season_dir, "download_report.json")
    report = {**stats, "files": [os.path.relpath(f, season_dir) for f in stats["files"]]}
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    return stats


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--season", default="2023-2024")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--no-skip", action="store_true")
    args = p.parse_args()
    download_meet_results(args.season, args.limit, not args.no_skip)
