#!/usr/bin/env python3
"""
Interactive Visa Bulletin downloader.

Opens a VISIBLE Chrome window so a human can solve the Cloudflare challenge
on travel.state.gov. Once the challenge is cleared (cf_clearance cookie issued),
it captures the session cookies and downloads all pending Visa Bulletin PDFs,
then registers them in the manifest.

Usage:
    python interactive_visa_bulletin.py
"""

import base64
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import undetected_chromedriver as uc

HUB_URL = "https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html"
PDF_BASE = "https://travel.state.gov/content/dam/visas/Bulletins/"
YEAR_DIR = Path("downloads/Visa_Bulletin/2026")
MANIFEST_PATH = Path("downloads/_manifest.json")
# Keep this None so undetected_chromedriver auto-matches installed Chrome.
CHROME_VERSION_MAIN = None
MAX_WAIT_SECONDS = 240  # up to 4 minutes for human to solve

# Months to attempt (already-present files are skipped automatically)
TARGET_MONTHS = ["September2026", "October2026"]


def _wait_for_pdf_file(path: Path, timeout_seconds: int = 45) -> bool:
    """Wait for a downloaded PDF file to appear and stabilize on disk."""
    deadline = time.time() + timeout_seconds
    last_size = -1
    stable_count = 0

    while time.time() < deadline:
        if path.exists():
            size = path.stat().st_size
            if size > 0 and size == last_size:
                stable_count += 1
                if stable_count >= 2:
                    return True
            else:
                stable_count = 0
                last_size = size
        time.sleep(1)
    return path.exists() and path.stat().st_size > 0


def _download_via_navigation(driver, url: str, dest: Path) -> bool:
    """Fallback: open PDF URL in a new tab and let Chrome download it normally."""
    original_handle = driver.current_window_handle
    before_handles = set(driver.window_handles)

    try:
        driver.execute_script("window.open(arguments[0], '_blank');", url)

        deadline = time.time() + 10
        while time.time() < deadline:
            after_handles = set(driver.window_handles)
            diff = list(after_handles - before_handles)
            if diff:
                driver.switch_to.window(diff[0])
                break
            time.sleep(0.3)

        # Give navigation a moment to trigger download before polling file.
        time.sleep(2)
        ok = _wait_for_pdf_file(dest, timeout_seconds=45)
        if not ok:
            return False

        return dest.read_bytes()[:4] == b"%PDF"
    finally:
        # Close any extra tab(s) and restore the original tab.
        for handle in list(driver.window_handles):
            if handle != original_handle:
                try:
                    driver.switch_to.window(handle)
                    driver.close()
                except Exception:
                    pass
        try:
            driver.switch_to.window(original_handle)
        except Exception:
            pass


def wait_for_clearance(driver) -> bool:
    """Poll until Cloudflare clearance is obtained or timeout."""
    print(f"\n{'='*60}")
    print("  ACTION REQUIRED: Solve the Cloudflare challenge in the")
    print("  Chrome window that just opened (click the checkbox if shown).")
    print(f"  Waiting up to {MAX_WAIT_SECONDS}s for clearance...")
    print(f"{'='*60}\n")

    deadline = time.time() + MAX_WAIT_SECONDS
    while time.time() < deadline:
        time.sleep(3)
        try:
            cookies = driver.get_cookies()
            title = driver.title or ""
        except Exception:
            continue
        names = [c["name"] for c in cookies]
        elapsed = int(MAX_WAIT_SECONDS - (deadline - time.time()))
        print(f"  [{elapsed:3}s] title='{title[:35]}' cookies={names}")

        if any(c["name"] == "cf_clearance" for c in cookies):
            print("\n  \u2713 cf_clearance obtained \u2014 challenge solved!\n")
            return True
        if title and "just a moment" not in title.lower() and "attention required" not in title.lower():
            # Title changed to real page content
            if "visa bulletin" in title.lower():
                print("\n  \u2713 Real page loaded \u2014 challenge cleared!\n")
                return True
    print("\n  \u2717 Timed out waiting for challenge to clear.\n")
    return False


# JavaScript that fetches a URL from within the browser context (correct TLS
# fingerprint + session cookies) and returns the body as base64.
FETCH_JS = """
const url = arguments[0];
const done = arguments[arguments.length - 1];
fetch(url, {credentials: 'include'})
  .then(resp => {
    if (!resp.ok) { done({ok: false, status: resp.status}); return; }
    return resp.arrayBuffer().then(buf => {
      let binary = '';
      const bytes = new Uint8Array(buf);
      const chunk = 0x8000;
      for (let i = 0; i < bytes.length; i += chunk) {
        binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
      }
      done({ok: true, status: resp.status, b64: btoa(binary)});
    });
  })
  .catch(err => done({ok: false, error: String(err)}));
"""


def download_pdfs(driver) -> list:
    """Download target-month PDFs via in-browser fetch (passes Cloudflare TLS check)."""
    YEAR_DIR.mkdir(parents=True, exist_ok=True)
    downloaded = []
    driver.set_script_timeout(90)

    for month in TARGET_MONTHS:
        filename = f"visabulletin_{month}.pdf"
        dest = YEAR_DIR / filename
        if dest.exists():
            print(f"  \u2713 Already have {filename}, skipping")
            continue

        url = PDF_BASE + filename
        print(f"  \u2192 Downloading {filename} (in-browser fetch) ...")
        try:
            result = driver.execute_async_script(FETCH_JS, url)
        except Exception as e:
            print(f"    \u2717 Error: {e}")
            continue

        if not result or not result.get("ok"):
            status = (result or {}).get("status", "?")
            if status == 404:
                print(f"    \u26a0 Not published yet (404): {filename}")
            else:
                print(f"    \u26a0 Fetch blocked (status={status}). Trying browser-download fallback...")
                if _download_via_navigation(driver, url, dest):
                    size = dest.stat().st_size
                    print(f"    \u2713 Saved {filename} ({size // 1024} KB) via navigation fallback")
                    downloaded.append((month, filename, url, size))
                    continue
                print(f"    \u2717 Failed: status={status} {(result or {}).get('error', '')}")
            continue

        content = base64.b64decode(result["b64"])
        if content[:4] == b"%PDF":
            dest.write_bytes(content)
            print(f"    \u2713 Saved {filename} ({len(content) // 1024} KB)")
            downloaded.append((month, filename, url, len(content)))
        else:
            print(f"    \u2717 Not a PDF ({len(content)} bytes): {content[:40]!r}")

    return downloaded


def update_manifest(downloaded: list) -> None:
    """Register newly downloaded files in the manifest."""
    if not downloaded:
        return
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    else:
        manifest = {"entries": []}

    existing_paths = {e.get("local_path") for e in manifest.get("entries", [])}

    for month, filename, url, _size in downloaded:
        # Parse month name -> date
        month_name = month[:-4]
        detected = datetime.strptime(f"{month_name} 2026", "%B %Y")
        local_path = f"Visa_Bulletin/2026/{filename}"
        if local_path in existing_paths:
            continue
        manifest["entries"].append({
            "group": "Visa_Bulletin",
            "name": "Visa Bulletin PDFs (Monthly)",
            "source_url": url,
            "local_path": local_path,
            "detected_date": detected.isoformat(),
            "method": "visa_bulletin_multilevel",
            "status": "success",
            "notes": f"Visa Bulletin For {month_name} 2026 (interactive Cloudflare bypass)",
            "hash": None,
        })

    manifest["last_updated"] = datetime.now().isoformat()
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\n  \u2713 Manifest updated (+{len(downloaded)} entries)")


def main() -> int:
    driver = None
    try:
        print("Starting visible Chrome window...")
        opts = uc.ChromeOptions()
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        YEAR_DIR.mkdir(parents=True, exist_ok=True)
        prefs = {
            "download.default_directory": str(YEAR_DIR.resolve()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
        }
        opts.add_experimental_option("prefs", prefs)
        chrome_kwargs = {
            "options": opts,
            "headless": False,
            "use_subprocess": True,
        }
        if CHROME_VERSION_MAIN is not None:
            chrome_kwargs["version_main"] = CHROME_VERSION_MAIN
        driver = uc.Chrome(**chrome_kwargs)
        driver.set_page_load_timeout(90)
        driver.get(HUB_URL)

        if not wait_for_clearance(driver):
            print("Could not obtain Cloudflare clearance. Aborting.")
            return 1

        print("Downloading pending Visa Bulletin PDFs...\n")
        downloaded = download_pdfs(driver)
        update_manifest(downloaded)

        print(f"\n{'='*60}")
        print(f"  DONE \u2014 {len(downloaded)} new bulletin(s) downloaded")
        for month, filename, _url, size in downloaded:
            print(f"    \u2022 {filename} ({size // 1024} KB)")
        print(f"{'='*60}")
        return 0
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    sys.exit(main())
