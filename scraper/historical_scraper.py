import json
import os
import time
import random
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.gomotionapp.com"
CALENDAR_URL = "https://www.gomotionapp.com/team/md/page/calendar#/team-events/past"
HISTORICAL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw", "historical")
MANIFEST_FILE = os.path.join(HISTORICAL_DIR, "historical_manifest.json")

def setup_directories():
    os.makedirs(HISTORICAL_DIR, exist_ok=True)

def scrape_historical_events():
    setup_directories()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()
        
        print(f"Navigating to {CALENDAR_URL}")
        page.goto(CALENDAR_URL, wait_until="networkidle")
        page.wait_for_timeout(5000)

        print("Locating Date Picker...")
        date_input_selector = "date-time-picker input"
        
        try:
            page.wait_for_selector(date_input_selector, state="visible", timeout=15000)
            
            box = page.locator(date_input_selector).first.bounding_box()
            if box:
                page.mouse.click(box['x'] + 10, box['y'] + 10)
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                page.keyboard.type("01/01/2010", delay=50)
                print("Typed date 01/01/2010.")
                
                # Click Search button
                for btn in page.locator("button").all():
                    if "search" in btn.inner_text().lower():
                        btn.click()
                        break
                print("Clicked search.")
            else:
                print("Could not find date input box.")
        except Exception as e:
            print(f"Date picker error: {e}")
            
        page.wait_for_timeout(8000)
        
        print("Scrolling down to load events...")
        previous_count = 0
        scroll_attempts = 0
        
        while scroll_attempts < 15: # Arbitrary limit for now
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)
            
            try:
                # Click Load More if present
                for btn in page.locator("button").all():
                    if "load more" in btn.inner_text().lower():
                        btn.click()
                        page.wait_for_timeout(2000)
            except:
                pass
                
            # Extract rowids from .team-event elements
            rowids = page.eval_on_selector_all(".team-event", "elements => elements.map(e => e.getAttribute('rowid')).filter(r => r)")
            event_links = list(set([f"{CALENDAR_URL}/{rid}" for rid in rowids]))
            
            if len(event_links) == previous_count:
                scroll_attempts += 1
                time.sleep(2) # Give it an extra moment
            else:
                scroll_attempts = 0
                print(f"  Found {len(event_links)} events...")
                previous_count = len(event_links)

        print(f"\nFinal count: Found {len(event_links)} historical event URLs.")
        
        with open(MANIFEST_FILE, "w") as f:
            json.dump({"urls": event_links}, f, indent=2)
            
        if event_links:
            download_events(context, event_links)
        
        browser.close()

def download_events(context, event_links):
    print(f"\nStarting download phase...")
    page = context.new_page()
    
    progress_file = os.path.join(HISTORICAL_DIR, "historical_progress.json")
    processed = []
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            processed = json.load(f)
            
    for i, url in enumerate(event_links, 1):
        if url in processed:
            print(f"[{i}/{len(event_links)}] Already processed: {url}")
            continue
            
        try:
            print(f"[{i}/{len(event_links)}] Processing: {url}")
            page.goto(url, wait_until="networkidle")
            page.wait_for_timeout(3000)
            
            links = page.locator("a").all()
            downloaded = 0
            
            for link in links:
                href = (link.get_attribute("href") or "").lower()
                text = link.inner_text().lower()
                
                # Explicitly skip PDFs
                if ".pdf" in href:
                    continue
                    
                if ".zip" in href or "result" in text and ("zip" in text or "cl2" in text or "hy3" in text):
                    print(f"    -> Found result link: {text[:30]}")
                    try:
                        with page.expect_download(timeout=10000) as download_info:
                            link.click(force=True)
                        
                        download = download_info.value
                        filename = download.suggested_filename
                        
                        save_dir = os.path.join(HISTORICAL_DIR, "downloads")
                        os.makedirs(save_dir, exist_ok=True)
                        
                        save_path = os.path.join(save_dir, filename)
                        download.save_as(save_path)
                        print(f"    -> Downloaded: {filename}")
                        downloaded += 1
                        page.wait_for_timeout(500)
                    except Exception as de:
                        print(f"    -> Download timeout/error (likely not a zip): {de}")
            
            if downloaded == 0:
                print("    -> No result ZIPs found on this page.")
                
            processed.append(url)
            with open(progress_file, "w") as f:
                json.dump(processed, f)
                
            # Random delay before next event to prevent blocking
            delay = random.uniform(1.0, 2.0)
            time.sleep(delay)
                
        except Exception as e:
            print(f"    -> ERROR processing event: {e}")

if __name__ == "__main__":
    # If manifest exists, skip scraping the list and go straight to download
    if os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE, "r") as f:
            data = json.load(f)
            links = data.get("urls", [])
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            download_events(context, links)
            browser.close()
    else:
        scrape_historical_events()

