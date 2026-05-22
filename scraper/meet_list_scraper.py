from __future__ import annotations

"""
Meet List Scraper for Maryland Swimming GoMotion pages.

Parses the HTML meet schedule page and extracts:
- Meet name, dates
- Links to: Result PDF, Result ZIP, Backup ZIP, Event files, etc.
- Organizes into a structured manifest JSON file.
"""
import json
import os
import re
import time
from dataclasses import dataclass, field, asdict
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from scraper.config import (
    GOMOTION_BASE_URL,
    SEASON_PAGES,
    MANIFEST_DIR,
    USER_AGENT,
    REQUEST_DELAY_SECONDS,
    REQUEST_TIMEOUT_SECONDS,
)


@dataclass
class MeetFile:
    """Represents a downloadable file associated with a meet."""
    label: str          # e.g., "Result PDF", "Result ZIP", "Backup"
    url: str
    file_type: str      # "pdf", "zip", "doc", "xlsx", etc.


@dataclass
class MeetEntry:
    """Represents a single swim meet with its associated files."""
    name: str
    date_range: str                     # e.g., "Sept 9-10, 2023"
    season: str                         # e.g., "2023-2024"
    result_pdf_url: Optional[str] = None
    result_zip_url: Optional[str] = None
    backup_zip_url: Optional[str] = None
    event_file_url: Optional[str] = None
    meet_notice_pdf_url: Optional[str] = None
    all_files: list = field(default_factory=list)


def fetch_page(url: str) -> str:
    """Fetch HTML content from URL with proper headers."""
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.text


def _classify_link(href: str, link_text: str) -> tuple[str, str]:
    """
    Classify a link by its type and role based on URL and link text.
    Returns (file_type, role) where role is one of:
        'result_pdf', 'result_zip', 'backup_zip', 'event_file',
        'meet_notice_pdf', 'signup', 'warmup', 'timeline',
        'psych_sheet', 'other'
    """
    href_lower = href.lower()
    text_lower = link_text.strip().lower()

    # Determine file type from extension
    if href_lower.endswith(".pdf"):
        file_type = "pdf"
    elif href_lower.endswith(".zip"):
        file_type = "zip"
    elif href_lower.endswith(".doc") or href_lower.endswith(".docx"):
        file_type = "doc"
    elif href_lower.endswith(".xlsx") or href_lower.endswith(".xls"):
        file_type = "xlsx"
    else:
        file_type = "other"

    # Classify role based on URL patterns and link text
    if "meet-results-" in href_lower and file_type == "zip":
        return file_type, "result_zip"
    elif "meet-results" in href_lower and file_type == "pdf":
        return file_type, "result_pdf"
    elif "swmm" in href_lower and "bkup" in href_lower:
        return file_type, "backup_zip"
    elif "meet-events-" in href_lower:
        return file_type, "event_file"
    elif "results" in href_lower and file_type == "pdf":
        return file_type, "result_pdf"
    elif "results" in text_lower and file_type == "pdf":
        return file_type, "result_pdf"
    elif text_lower in ("backup",):
        return file_type, "backup_zip"
    elif "signup" in text_lower or "google.com/forms" in href_lower:
        return file_type, "signup"
    elif "warmup" in text_lower or "warm-up" in href_lower or "warmup" in href_lower:
        return file_type, "warmup"
    elif "timeline" in text_lower or "timeline" in href_lower or "session" in href_lower:
        return file_type, "timeline"
    elif "psych" in text_lower or "psych" in href_lower:
        return file_type, "psych_sheet"
    elif text_lower in ("pdf",) and file_type == "pdf":
        # Generic PDF — could be meet notice or results; need context
        return file_type, "generic_pdf"
    elif text_lower in ("file",) and file_type == "zip":
        return file_type, "event_file"
    elif text_lower in ("zip",) and file_type == "zip":
        return file_type, "result_zip"
    else:
        return file_type, "other"


def parse_meet_schedule(html: str, season: str) -> list[MeetEntry]:
    """
    Parse the Maryland Swimming meet schedule HTML and extract meet entries.

    The page structure is a series of date headers followed by meet blocks,
    each containing links to various files (PDFs, ZIPs, signups, etc.).
    """
    soup = BeautifulSoup(html, "html.parser")
    meets = []

    # The page content is inside the main content area
    # We need to parse the raw text/link structure since the page uses
    # a somewhat unstructured HTML layout.

    # Strategy: Find all links and group them by proximity to meet names
    # The page has date ranges as section headers and meet names as text blocks

    # First, extract all text content and links in order
    content_area = soup.body if soup.body else soup

    # Find all links on the page
    all_links = content_area.find_all("a", href=True)

    # Filter to only file/resource links (not navigation)
    resource_links = []
    for link in all_links:
        href = link.get("href", "")
        if any(pattern in href.lower() for pattern in [
            "userfiles", "quickupload", "google.com/forms",
            ".pdf", ".zip", ".doc", ".xlsx"
        ]):
            # Make absolute URL
            if href.startswith("/"):
                href = urljoin(GOMOTION_BASE_URL, href)
            resource_links.append((link, href))

    # Now parse meets from the structured content
    # We'll look for patterns: meet names followed by groups of links
    text_content = content_area.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text_content.split("\n") if line.strip()]

    # Find date range headers (e.g., "Sept 9-10, 2023", "Oct 6-8, 2023")
    date_pattern = re.compile(
        r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
        r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|"
        r"Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:-\d{1,2})?,?\s*\d{4}",
        re.IGNORECASE
    )

    # Process the resource links in sequence to group them into meets
    # Each "meet block" on the page has: meet name text, then a series of links

    # Build a list of link groups based on URL proximity and patterns
    # A new "meet block" typically starts with a meet notice PDF or an event file

    current_meet_name = None
    current_date = None
    current_links = []
    meet_blocks = []

    # Parse the raw HTML line by line for better structure detection
    # Get all text nodes and links in order
    elements = []
    for elem in content_area.descendants:
        if isinstance(elem, str):
            text = elem.strip()
            if text and len(text) > 3:
                elements.append(("text", text, None))
        elif elem.name == "a" and elem.get("href"):
            href = elem.get("href", "")
            if any(p in href.lower() for p in ["userfiles", "quickupload", "forms"]):
                if href.startswith("/"):
                    href = urljoin(GOMOTION_BASE_URL, href)
                elements.append(("link", elem.get_text(strip=True), href))

    # Now group elements into meet blocks
    # Heuristic: A meet block starts when we see a meet name (text that's not
    # just "PDF", "ZIP", "Signup", etc.) followed by links
    skip_labels = {
        "pdf", "zip", "file", "signup", "warmup", "timeline",
        "psych sheet", "backup", "meet info", "officials needed",
        "online apparel store"
    }

    for elem_type, text, href in elements:
        if elem_type == "text":
            # Check if this is a date range
            date_match = date_pattern.search(text)
            if date_match:
                current_date = date_match.group(0)
                continue

            # Check if this is a meet name (not a label or short text)
            text_lower = text.lower()
            if (len(text) > 10
                    and text_lower not in skip_labels
                    and not text.startswith("Session")
                    and not text.startswith("Warm")
                    and not text.startswith("FOLLOW")
                    and not text.startswith("CANCELLED")
                    and not text.startswith("MEET")
                    and not text.startswith("Entry")
                    and not text.startswith("Format")
                    and not text.startswith("Updated")
                    and not text.startswith("Friday")
                    and not text.startswith("Saturday")
                    and not text.startswith("Sunday")
                    and not text.startswith("Teams")
                    and "(" in text and ")" in text  # Usually "Meet Name (SCY/LCM)"
                    ):
                # Save previous meet block
                if current_meet_name and current_links:
                    meet_blocks.append((current_meet_name, current_date, current_links))
                current_meet_name = text
                current_links = []

        elif elem_type == "link" and href:
            current_links.append((text, href))

    # Don't forget the last block
    if current_meet_name and current_links:
        meet_blocks.append((current_meet_name, current_date, current_links))

    # If the heuristic above finds too few meets, fall back to a simpler approach:
    # Group all links by their URL patterns (result ZIP files as anchors)
    if len(meet_blocks) < 40:
        print(f"  Heuristic found only {len(meet_blocks)} meets, trying fallback parser...")
        meets = _fallback_parse_links(resource_links, season)
        return meets

    # Convert meet blocks to MeetEntry objects
    for meet_name, date_range, links in meet_blocks:
        entry = MeetEntry(
            name=meet_name,
            date_range=date_range or "Unknown",
            season=season,
        )

        # Track which PDFs we've seen to distinguish meet notice vs results
        pdf_count = 0

        for link_text, link_href in links:
            file_type, role = _classify_link(link_href, link_text)

            entry.all_files.append(asdict(MeetFile(
                label=f"{role} ({link_text})",
                url=link_href,
                file_type=file_type,
            )))

            if role == "result_zip" and not entry.result_zip_url:
                entry.result_zip_url = link_href
            elif role == "backup_zip" and not entry.backup_zip_url:
                entry.backup_zip_url = link_href
            elif role == "event_file" and not entry.event_file_url:
                entry.event_file_url = link_href
            elif role == "result_pdf" and not entry.result_pdf_url:
                entry.result_pdf_url = link_href
            elif role == "generic_pdf":
                pdf_count += 1
                if pdf_count == 1:
                    # First generic PDF is usually the meet notice
                    entry.meet_notice_pdf_url = link_href
                elif pdf_count >= 2 and not entry.result_pdf_url:
                    # Second+ generic PDF is usually results
                    entry.result_pdf_url = link_href

        meets.append(entry)

    return meets


def _fallback_parse_links(resource_links: list, season: str) -> list[MeetEntry]:
    """
    Fallback parser: group links by result ZIP files.
    Each result ZIP URL contains a descriptive meet name that we can extract.
    """
    meets = []
    seen_result_zips = set()

    for link, href in resource_links:
        href_lower = href.lower()

        # Find result ZIP files as "anchor" points for meet identification
        if "meet-results-" in href_lower and href_lower.endswith(".zip"):
            if href in seen_result_zips:
                continue
            seen_result_zips.add(href)

            # Extract meet name from the URL
            # Pattern: meet-results-{meet-name}-{date}-{version}_{hash}.zip
            filename = href.split("/")[-1]
            match = re.match(
                r"(?:\d+-)?meet-results-(.+?)-(\d{2}\w{3}\d{4})-\d+",
                filename, re.IGNORECASE
            )
            if match:
                raw_name = match.group(1).replace("-", " ").title()
                date_str = match.group(2)
            else:
                raw_name = filename.replace("meet-results-", "").split("_")[0]
                raw_name = raw_name.replace("-", " ").title()
                date_str = "Unknown"

            entry = MeetEntry(
                name=raw_name,
                date_range=date_str,
                season=season,
                result_zip_url=href,
            )

            # Try to find associated backup ZIP and result PDF nearby
            # (within ±5 links in the list)
            idx = next(
                (i for i, (_, h) in enumerate(resource_links) if h == href),
                -1
            )
            if idx >= 0:
                # Look in a window around this link
                window = resource_links[max(0, idx - 5):idx + 5]
                for _, nearby_href in window:
                    nearby_lower = nearby_href.lower()
                    if "swmm" in nearby_lower and "bkup" in nearby_lower:
                        entry.backup_zip_url = nearby_href
                    elif nearby_lower.endswith(".pdf") and "results" in nearby_lower:
                        entry.result_pdf_url = nearby_href

            meets.append(entry)

    return meets


def scrape_season(season: str) -> list[dict]:
    """Scrape all meet data for a given season and save to manifest."""
    url = SEASON_PAGES.get(season)
    if not url:
        raise ValueError(f"No URL configured for season: {season}")

    print(f"Fetching meet schedule for {season}...")
    print(f"  URL: {url}")

    html = fetch_page(url)
    print(f"  Page fetched ({len(html):,} bytes)")

    meets = parse_meet_schedule(html, season)
    print(f"  Found {len(meets)} meets")

    # Count meets with result files
    with_zip = sum(1 for m in meets if m.result_zip_url)
    with_pdf = sum(1 for m in meets if m.result_pdf_url)
    with_backup = sum(1 for m in meets if m.backup_zip_url)
    print(f"  With result ZIP: {with_zip}")
    print(f"  With result PDF: {with_pdf}")
    print(f"  With backup ZIP: {with_backup}")

    # Convert to dicts for JSON serialization
    meets_data = [asdict(m) for m in meets]

    # Save manifest
    manifest_path = os.path.join(MANIFEST_DIR, f"meet_manifest_{season}.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(meets_data, f, indent=2, ensure_ascii=False)
    print(f"  Manifest saved to: {manifest_path}")

    return meets_data


def scrape_all_seasons() -> dict:
    """Scrape all configured seasons."""
    all_data = {}
    for season in SEASON_PAGES:
        data = scrape_season(season)
        all_data[season] = data
        time.sleep(REQUEST_DELAY_SECONDS)
    return all_data


if __name__ == "__main__":
    print("=" * 60)
    print("Maryland Swimming Meet Scraper")
    print("=" * 60)
    result = scrape_all_seasons()
    for season, meets in result.items():
        print(f"\n{season}: {len(meets)} meets scraped")
