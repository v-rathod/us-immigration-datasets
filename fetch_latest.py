#!/usr/bin/env python3
"""
Immigration & Labor Data Fetcher
Automates download of public datasets from official sources for the past 12 months.
"""

import hashlib
import json
import os
import random
import re
import shutil
import sys
import time
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
import yaml
from bs4 import BeautifulSoup

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
ACCEPT_LANGUAGE = "en-US,en;q=0.9"
REQUEST_TIMEOUT = 60
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds
REQUEST_JITTER_MIN = 0.2  # 200ms
REQUEST_JITTER_MAX = 0.8  # 800ms


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def log(msg: str, level: str = "info") -> None:
    """Print formatted log message to console."""
    prefix = {
        "info": "→",
        "success": "✓",
        "warning": "⚠",
        "error": "✗",
    }.get(level, "•")
    print(f"{prefix} {msg}")


def load_manifest(downloads_dir: Path) -> Dict[str, Any]:
    """
    Load download manifest from previous runs.
    
    The manifest tracks all downloaded files and their metadata,
    allowing incremental downloads on subsequent runs.
    
    Returns:
        Dictionary with 'entries' list and metadata, or empty if not found
    """
    manifest_path = downloads_dir / '_manifest.json'
    
    if not manifest_path.exists():
        log("No previous manifest found - will download all files")
        return {"entries": [], "files_by_url": {}}
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        # Build index by URL for fast lookups
        files_by_url = {}
        for entry in manifest.get('entries', []):
            url = entry.get('source_url')
            if url and entry.get('status') == 'success':
                files_by_url[url] = entry
        
        manifest['files_by_url'] = files_by_url
        
        log(f"Loaded manifest: {len(files_by_url)} files previously downloaded")
        return manifest
        
    except Exception as e:
        log(f"Failed to load manifest: {e}", "warning")
        return {"entries": [], "files_by_url": {}}


def is_file_in_manifest(file_url: str, local_path: Path, manifest: Dict[str, Any]) -> bool:
    """
    Check if a file has already been downloaded.
    
    Args:
        file_url: The source URL of the file
        local_path: Expected local file path
        manifest: Loaded manifest dictionary
    
    Returns:
        True if file exists both in manifest and on disk
    """
    # Check manifest first
    files_by_url = manifest.get('files_by_url', {})
    if file_url not in files_by_url:
        return False
    
    # Verify file still exists on disk
    if not local_path.exists():
        log(f"File in manifest but missing on disk: {local_path.name}", "warning")
        return False
    
    return True


def save_manifest_incremental(downloads_dir: Path, manifest: Dict[str, Any]) -> None:
    """
    Save manifest incrementally during run.
    
    This allows progress to be preserved even if the run is interrupted.
    """
    manifest_path = downloads_dir / '_manifest.json'
    
    try:
        # Update run metadata
        manifest['last_updated'] = datetime.now().isoformat()
        
        # Write atomically using temporary file
        temp_path = manifest_path.with_suffix('.json.tmp')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        temp_path.replace(manifest_path)
        
    except Exception as e:
        log(f"Failed to save manifest: {e}", "warning")


def http_get(url: str, stream: bool = False) -> requests.Response:
    """
    HTTP GET with retries and exponential backoff.
    Includes User-Agent and Accept-Language headers to avoid 403/bot blocking.
    
    Args:
        url: URL to fetch
        stream: Whether to stream the response (for large files)
    
    Returns:
        Response object
    
    Raises:
        requests.RequestException: If all retries fail
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": ACCEPT_LANGUAGE
    }
    
    # Add small random jitter to avoid rate limiting
    jitter = random.uniform(REQUEST_JITTER_MIN, REQUEST_JITTER_MAX)
    time.sleep(jitter)
    
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(
                url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                stream=stream,
                allow_redirects=True
            )
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                wait_time = RETRY_BACKOFF ** attempt
                log(f"Retry {attempt + 1}/{MAX_RETRIES} for {url} in {wait_time}s: {e}", "warning")
                time.sleep(wait_time)
            else:
                raise
    
    raise requests.RequestException(f"Failed after {MAX_RETRIES} retries")


def find_links(page_url: str, css_selector: Optional[str] = None) -> List[Tuple[str, str]]:
    """
    Find links on a page matching optional CSS selector.
    
    Args:
        page_url: URL of page to scrape
        css_selector: Optional CSS selector to filter links
    
    Returns:
        List of (absolute_url, link_text) tuples
    """
    try:
        resp = http_get(page_url)
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        links = []
        if css_selector:
            elements = soup.select(css_selector)
        else:
            elements = soup.find_all('a', href=True)
        
        for elem in elements:
            href = elem.get('href', '')
            if not href:
                continue
            absolute_url = urljoin(page_url, href)
            text = elem.get_text(strip=True)
            links.append((absolute_url, text))
        
        return links
    except Exception as e:
        log(f"Error finding links on {page_url}: {e}", "error")
        return []


def extract_date_from_text(text: str) -> Optional[datetime]:
    """
    Extract date from text using common patterns.
    Supports: "February 2026", "2026-02", "FY2025_Q3", "Q3 FY2025", etc.
    
    Args:
        text: Text to parse
    
    Returns:
        Datetime object or None
    """
    text = text.lower()
    
    # Pattern: "February 2026", "Feb 2026"
    month_names = {
        'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
        'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6,
        'july': 7, 'jul': 7, 'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
        'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
    }
    
    # Pattern: "February 2026", "february-2026", "February2026" (various separators)
    for month_name, month_num in month_names.items():
        pattern = rf'\b{month_name}[-\s]?(\d{{4}})\b'
        match = re.search(pattern, text)
        if match:
            year = int(match.group(1))
            return datetime(year, month_num, 1)
    
    # Pattern: "2026-02", "2026_02"
    match = re.search(r'\b(\d{4})[-_](\d{1,2})\b', text)
    if match:
        year, month = int(match.group(1)), int(match.group(2))
        if 1 <= month <= 12 and 2000 <= year <= 2100:
            return datetime(year, month, 1)
    
    # Pattern: "FY2025_Q3", "Q3_FY2025" - map to QUARTER END dates
    match = re.search(r'(?:fy|fiscal\s*year)\s*(\d{4}).*?q(\d)', text)
    if not match:
        match = re.search(r'q(\d).*?(?:fy|fiscal\s*year)\s*(\d{4})', text)
        if match:
            quarter = int(match.group(1))
            year = int(match.group(2))
        else:
            quarter = None
            year = None
    else:
        year = int(match.group(1))
        quarter = int(match.group(2))
    
    if quarter and year:
        # Federal Fiscal Year: Q1 ends Dec 31, Q2 ends Mar 31, Q3 ends Jun 30, Q4 ends Sep 30
        if 1 <= quarter <= 4:
            quarter_end_months = {1: 12, 2: 3, 3: 6, 4: 9}
            month = quarter_end_months[quarter]
            # Q1 of FY2025 ends Dec 31, 2024; Q2-Q4 end in calendar year matching FY year
            if quarter == 1:
                actual_year = year - 1
                day = 31
            elif month == 3:
                actual_year = year
                day = 31
            elif month == 6:
                actual_year = year
                day = 30
            else:  # Sep 30
                actual_year = year
                day = 30
            return datetime(actual_year, month, day)
    
    # Pattern: "2026Q2", "2026-Q2"
    match = re.search(r'\b(\d{4})[-_]?q(\d)\b', text)
    if match:
        year = int(match.group(1))
        quarter = int(match.group(2))
        if 1 <= quarter <= 4:
            month = (quarter - 1) * 3 + 1  # Calendar quarters
            return datetime(year, month, 1)
    
    # Pattern: just year "2026"
    match = re.search(r'\b(20\d{2})\b', text)
    if match:
        year = int(match.group(1))
        return datetime(year, 1, 1)
    
    return None


def download_file(url: str, dest_path: Path) -> bool:
    """
    Download file to destination path.
    
    Args:
        url: URL to download
        dest_path: Destination file path
    
    Returns:
        True if successful, False otherwise
    """
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        resp = http_get(url, stream=True)
        
        # Write file
        with open(dest_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
    except Exception as e:
        log(f"Error downloading {url}: {e}", "error")
        return False


def hash_file(path: Path) -> str:
    """
    Calculate SHA256 hash of file.
    
    Args:
        path: File path
    
    Returns:
        Hex string of SHA256 hash
    """
    sha256 = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def guess_file_extension(url: str, content_type: Optional[str] = None) -> str:
    """
    Guess file extension from URL or Content-Type.
    
    Args:
        url: URL of file
        content_type: HTTP Content-Type header
    
    Returns:
        File extension (with dot) or .bin if unknown
    """
    # Try URL path first
    path = urlparse(url).path
    if '.' in path:
        ext = Path(path).suffix.lower()
        if ext:
            return ext
    
    # Try Content-Type
    if content_type:
        content_type = content_type.lower()
        mapping = {
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/vnd.ms-excel': '.xls',
            'application/pdf': '.pdf',
            'text/html': '.html',
            'text/csv': '.csv',
            'application/json': '.json',
            'application/zip': '.zip',
        }
        for mime, ext in mapping.items():
            if mime in content_type:
                return ext
    
    return '.bin'


def is_downloadable_file(url: str) -> bool:
    """
    Check if URL points to a downloadable file (not HTML).
    
    Args:
        url: URL to check
    
    Returns:
        True if file is PDF, Excel, CSV, JSON, etc.
    """
    ext = Path(urlparse(url).path).suffix.lower()
    downloadable_exts = {'.pdf', '.xls', '.xlsx', '.csv', '.json', '.zip'}
    return ext in downloadable_exts


def apply_regex_filters(
    links: List[Tuple[str, str]],
    regex_filters: List[str]
) -> List[Tuple[str, str]]:
    """
    Filter links by regex patterns.
    
    Args:
        links: List of (url, text) tuples
        regex_filters: List of regex patterns to match
    
    Returns:
        Filtered list of (url, text) tuples matching at least one pattern
    """
    if not regex_filters:
        return links
    
    filtered = []
    for url, text in links:
        combined = url + " " + text
        for pattern in regex_filters:
            try:
                if re.search(pattern, combined, re.IGNORECASE):
                    filtered.append((url, text))
                    break  # Match found, no need to check other patterns
            except re.error as e:
                log(f"Invalid regex pattern '{pattern}': {e}", "warning")
    
    return filtered


def is_within_months(dt: datetime, reference: datetime, months: int) -> bool:
    """
    Check if date is within N months of reference date.
    
    Args:
        dt: Date to check
        reference: Reference date
        months: Number of months
    
    Returns:
        True if within range
    """
    cutoff = reference - timedelta(days=months * 30)
    return dt >= cutoff


def pick_recent_links(
    links: List[Tuple[str, str]],
    reference_date: datetime,
    within_months: int = 12
) -> List[Tuple[str, str, Optional[datetime]]]:
    """
    Filter links to those within date range, extract dates.
    
    Args:
        links: List of (url, text) tuples
        reference_date: Reference date
        within_months: Number of months to look back
    
    Returns:
        List of (url, text, extracted_date) tuples for recent links
    """
    recent = []
    for url, text in links:
        # Try to extract date from text and URL
        date_from_text = extract_date_from_text(text)
        date_from_url = extract_date_from_text(url)
        
        detected_date = date_from_text or date_from_url
        
        if detected_date and is_within_months(detected_date, reference_date, within_months):
            recent.append((url, text, detected_date))
    
    return recent


# ============================================================================
# API FUNCTIONS
# ============================================================================

def bls_fetch(
    series_ids: List[str],
    start_year: int,
    end_year: int,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch BLS time series data via API v2.
    
    Args:
        series_ids: List of BLS series IDs
        start_year: Start year
        end_year: End year
        api_key: Optional API key for higher quota
    
    Returns:
        JSON response as dict
    """
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    
    payload = {
        "seriesid": series_ids,
        "startyear": str(start_year),
        "endyear": str(end_year),
    }
    
    if api_key:
        payload["registrationkey"] = api_key
    
    headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json"
    }
    
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        log(f"BLS API error: {e}", "error")
        return {"status": "error", "message": str(e)}


def census_fetch_acs1(
    year: int,
    variables: List[str],
    geo_params: str,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch Census ACS 1-year data via API.
    
    Args:
        year: ACS year
        variables: List of variable codes (e.g., B01001_001E)
        geo_params: Geography parameter (e.g., "state:*")
        api_key: Optional API key
    
    Returns:
        JSON response as dict
    """
    url = f"https://api.census.gov/data/{year}/acs/acs1"
    
    params = {
        "get": ",".join(variables),
        "for": geo_params,
    }
    
    if api_key:
        params["key"] = api_key
    
    headers = {"User-Agent": USER_AGENT}
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        log(f"Census ACS API error: {e}", "error")
        return {"error": str(e)}


# ============================================================================
# DATA SOURCE HANDLERS
# ============================================================================

def handle_scrape_or_pattern(
    source: Dict[str, Any],
    run_date: datetime,
    group_dir: Path,
    manifest_entries: List[Dict[str, Any]],
    manifest: Dict[str, Any] = None
) -> None:
    """Handle scrape_or_pattern method (OFLC LCA/PERM)."""
    log(f"Processing {source['name']} via scrape_or_pattern")
    
    page_url = source.get('page_url', '')
    selector = source.get('selector', 'a')
    pattern = source.get('pattern', '')
    regex_filters = source.get('regex_filters', [])
    
    if not page_url:
        log(f"Missing page_url for {source['name']}", "warning")
        return
    
    try:
        links = find_links(page_url, selector)
        
        # Filter by downloadable file extensions only
        links = [(url, text) for url, text in links if is_downloadable_file(url)]
        
        # Apply regex filters if specified
        if regex_filters:
            links = apply_regex_filters(links, regex_filters)
        
        # Filter by pattern if specified (legacy support)
        if pattern:
            pattern_lower = pattern.lower()
            filtered_links = []
            for url, text in links:
                combined = (url + " " + text).lower()
                if pattern_lower in combined:
                    filtered_links.append((url, text))
            links = filtered_links
        
        recent = pick_recent_links(links, run_date, within_months=12)
        
        if not recent:
            log(f"No recent files found for {source['name']}", "warning")
            manifest_entries.append({
                "group": source["group"],
                "name": source["name"],
                "source_url": page_url,
                "local_path": None,
                "detected_date": None,
                "method": source["method"],
                "status": "no_files_found",
                "notes": "No files within 12-month window",
                "hash": None
            })
            return
        
        # Download up to 8 most recent (avoid downloading too many)
        for url, text, detected_date in sorted(recent, key=lambda x: x[2] or datetime.min, reverse=True)[:8]:
            filename = Path(urlparse(url).path).name
            if not filename or filename == '/':
                filename = f"{source['group']}_{detected_date.strftime('%Y%m') if detected_date else 'unknown'}{guess_file_extension(url)}"
            
            dest_path = group_dir / filename
            
            if download_file(url, dest_path):
                log(f"Downloaded {filename}", "success")
                
                manifest_entries.append({
                    "group": source["group"],
                    "name": source["name"],
                    "source_url": url,
                    "local_path": str(dest_path.relative_to(dest_path.parents[1])),
                    "detected_date": detected_date.isoformat() if detected_date else None,
                    "method": source["method"],
                    "status": "success",
                    "notes": text,
                    "hash": hash_file(dest_path)
                })
            else:
                manifest_entries.append({
                    "group": source["group"],
                    "name": source["name"],
                    "source_url": url,
                    "local_path": None,
                    "detected_date": detected_date.isoformat() if detected_date else None,
                    "method": source["method"],
                    "status": "download_failed",
                    "notes": text,
                    "hash": None
                })
    
    except Exception as e:
        log(f"Error handling {source['name']}: {e}", "error")
        manifest_entries.append({
            "group": source["group"],
            "name": source["name"],
            "source_url": page_url,
            "local_path": None,
            "detected_date": None,
            "method": source["method"],
            "status": "error",
            "notes": str(e),
            "hash": None
        })


def handle_scrape(
    source: Dict[str, Any],
    run_date: datetime,
    group_dir: Path,
    manifest_entries: List[Dict[str, Any]],
    manifest: Dict[str, Any] = None
) -> None:
    """Handle scrape method (USCIS Forms, Visa Bulletin, etc.)."""
    log(f"Processing {source['name']} via scrape")
    
    page_url = source.get('page_url', '')
    selector = source.get('selector', 'a')
    pattern = source.get('pattern', '')
    regex_filters = source.get('regex_filters', [])
    
    if not page_url:
        log(f"Missing page_url for {source['name']}", "warning")
        return
    
    try:
        links = find_links(page_url, selector)
        
        # Filter by downloadable file extensions only
        links = [(url, text) for url, text in links if is_downloadable_file(url)]
        
        # Apply regex filters if specified
        if regex_filters:
            links = apply_regex_filters(links, regex_filters)
        
        # Filter by pattern if specified (legacy support)
        if pattern:
            pattern_lower = pattern.lower()
            filtered_links = []
            for url, text in links:
                combined = (url + " " + text).lower()
                if pattern_lower in combined:
                    filtered_links.append((url, text))
            links = filtered_links
        
        recent = pick_recent_links(links, run_date, within_months=12)
        
        if not recent:
            log(f"No recent files found for {source['name']}", "warning")
            manifest_entries.append({
                "group": source["group"],
                "name": source["name"],
                "source_url": page_url,
                "local_path": None,
                "detected_date": None,
                "method": source["method"],
                "status": "no_files_found",
                "notes": "No files within 12-month window",
                "hash": None
            })
            return
        
        # Download recent files
        downloaded = 0
        for url, text, detected_date in sorted(recent, key=lambda x: x[2] or datetime.min, reverse=True):
            # Limit downloads per source
            if downloaded >= 15:
                break
            
            filename = Path(urlparse(url).path).name
            if not filename or filename == '/':
                filename = f"{source['group']}_{detected_date.strftime('%Y%m') if detected_date else 'unknown'}{guess_file_extension(url)}"
            
            dest_path = group_dir / filename
            
            # Skip if already exists (dedupe)
            if dest_path.exists():
                continue
            
            if download_file(url, dest_path):
                log(f"Downloaded {filename}", "success")
                downloaded += 1
                
                manifest_entries.append({
                    "group": source["group"],
                    "name": source["name"],
                    "source_url": url,
                    "local_path": str(dest_path.relative_to(dest_path.parents[1])),
                    "detected_date": detected_date.isoformat() if detected_date else None,
                    "method": source["method"],
                    "status": "success",
                    "notes": text,
                    "hash": hash_file(dest_path)
                })
    
    except Exception as e:
        log(f"Error handling {source['name']}: {e}", "error")
        manifest_entries.append({
            "group": source["group"],
            "name": source["name"],
            "source_url": page_url,
            "local_path": None,
            "detected_date": None,
            "method": source["method"],
            "status": "error",
            "notes": str(e),
            "hash": None
        })


def handle_scrape_if_available(
    source: Dict[str, Any],
    run_date: datetime,
    group_dir: Path,
    manifest_entries: List[Dict[str, Any]],
    manifest: Dict[str, Any] = None
) -> None:
    """Handle scrape_if_available method (DHS Yearbook)."""
    log(f"Processing {source['name']} via scrape_if_available")
    
    page_url = source.get('page_url', '')
    selector = source.get('selector', 'a')
    
    if not page_url:
        log(f"Missing page_url for {source['name']}", "warning")
        return
    
    try:
        links = find_links(page_url, selector)
        
        if not links:
            log(f"No files available for {source['name']}", "warning")
            manifest_entries.append({
                "group": source["group"],
                "name": source["name"],
                "source_url": page_url,
                "local_path": None,
                "detected_date": None,
                "method": source["method"],
                "status": "no_new_release",
                "notes": "No new yearbook release within 12 months",
                "hash": None
            })
            return
        
        # Download all available files (yearbooks tend to be table-by-table)
        for url, text in links[:20]:  # Limit to 20 files
            filename = Path(urlparse(url).path).name
            if not filename or filename == '/':
                filename = f"{source['group']}_table{guess_file_extension(url)}"
            
            dest_path = group_dir / filename
            
            if dest_path.exists():
                continue
            
            if download_file(url, dest_path):
                log(f"Downloaded {filename}", "success")
                
                manifest_entries.append({
                    "group": source["group"],
                    "name": source["name"],
                    "source_url": url,
                    "local_path": str(dest_path.relative_to(dest_path.parents[1])),
                    "detected_date": run_date.isoformat(),
                    "method": source["method"],
                    "status": "success",
                    "notes": text,
                    "hash": hash_file(dest_path)
                })
    
    except Exception as e:
        log(f"Error handling {source['name']}: {e}", "error")
        manifest_entries.append({
            "group": source["group"],
            "name": source["name"],
            "source_url": page_url,
            "local_path": None,
            "detected_date": None,
            "method": source["method"],
            "status": "error",
            "notes": str(e),
            "hash": None
        })


def handle_visa_bulletin_multilevel(
    source: Dict[str, Any],
    run_date: datetime,
    group_dir: Path,
    manifest_entries: List[Dict[str, Any]],
    manifest: Dict[str, Any] = None
) -> None:
    """
    Handle Visa Bulletin multi-level scraping: hub → monthly pages → PDFs.
    
    The State Department structures Visa Bulletins as:
    1. Hub page contains direct links to monthly bulletin pages (e.g., "visa-bulletin-for-february-2026.html")
    2. Each monthly page contains a "printer-friendly PDF" link
    
    We only download the PDFs, not the HTML pages.
    """
    log(f"Processing {source['name']} via multilevel scrape")
    
    hub_url = source.get('page_url', '')
    regex_filters = source.get('regex_filters', [])
    
    if not hub_url:
        log(f"Missing page_url for {source['name']}", "warning")
        return
    
    all_pdfs = []  # List of (url, text, detected_date)
    
    try:
        # Step 1: Get monthly page links from hub
        log(f"Visiting hub: {hub_url}")
        hub_links = find_links(hub_url, "a[href]")
        
        # Find monthly bulletin page links (e.g., "visa-bulletin-for-february-2026.html")
        monthly_page_links = []
        for url, text in hub_links:
            # Look for monthly bulletin page URLs
            if 'visa-bulletin-for-' in url.lower():
                monthly_page_links.append((url, text))
        
        if not monthly_page_links:
            log(f"No monthly bulletin page links found on hub", "warning")
            manifest_entries.append({
                "group": source["group"],
                "name": source["name"],
                "source_url": hub_url,
                "local_path": None,
                "detected_date": None,
                "method": source["method"],
                "status": "no_files_found",
                "notes": "No monthly bulletin page links found on hub",
                "hash": None
            })
            return
        
        log(f"Found {len(monthly_page_links)} monthly bulletin page(s) on hub")
        
        # Extract dates from all monthly page links (no filtering - get all available)
        all_monthly_pages = []
        
        for url, text in monthly_page_links:
            # Extract date from URL or link text
            detected_date = extract_date_from_text(url)
            if not detected_date:
                detected_date = extract_date_from_text(text)
            
            if detected_date:
                all_monthly_pages.append((url, text, detected_date))
            else:
                log(f"Could not extract date from: {text[:50]}", "warning")
        
        if not all_monthly_pages:
            log(f"No dated monthly pages found", "warning")
            manifest_entries.append({
                "group": source["group"],
                "name": source["name"],
                "source_url": hub_url,
                "local_path": None,
                "detected_date": None,
                "method": source["method"],
                "status": "no_files_found",
                "notes": f"Found {len(monthly_page_links)} monthly pages but could not extract dates",
                "hash": None
            })
            return
        
        log(f"Processing {len(all_monthly_pages)} monthly page(s) (all available)")
        
        # Step 2: For each monthly page, find the printer-friendly PDF
        for monthly_url, monthly_text, page_date in sorted(all_monthly_pages, key=lambda x: x[2], reverse=True):
            try:
                log(f"Visiting: {monthly_text[:50]}")
                monthly_page_links_inner = find_links(monthly_url, "a[href]")
                
                # Filter for PDF links only
                pdf_links = [(url, text) for url, text in monthly_page_links_inner 
                            if url.lower().endswith('.pdf')]
                
                # Apply regex filters if specified
                if regex_filters:
                    pdf_links = apply_regex_filters(pdf_links, regex_filters)
                
                # Extract date from each PDF
                for pdf_url, pdf_text in pdf_links:
                    # Try to extract date from PDF filename
                    filename = Path(urlparse(pdf_url).path).name
                    detected_date = extract_date_from_text(filename)
                    
                    # Fallback to page date
                    if not detected_date:
                        detected_date = page_date
                    
                    if detected_date:
                        all_pdfs.append((pdf_url, pdf_text or filename, detected_date))
                        log(f"Found PDF: {filename} (date: {detected_date.strftime('%Y-%m-%d')})")
            
            except Exception as e:
                log(f"Error processing monthly page {monthly_url}: {e}", "warning")
                continue
        
        if not all_pdfs:
            log(f"No PDFs found on monthly pages", "warning")
            manifest_entries.append({
                "group": source["group"],
                "name": source["name"],
                "source_url": hub_url,
                "local_path": None,
                "detected_date": None,
                "method": source["method"],
                "status": "no_files_found",
                "notes": f"Visited {len(all_monthly_pages)} monthly pages but found no matching PDFs",
                "hash": None
            })
            return
        
        log(f"Found {len(all_pdfs)} PDF(s) total")
        
        # Download PDFs organized by year (sorted by date, newest first)
        downloaded = 0
        for pdf_url, pdf_text, detected_date in sorted(all_pdfs, key=lambda x: x[2], reverse=True):
            filename = Path(urlparse(pdf_url).path).name
            
            # Create year subdirectory
            year = detected_date.year
            year_dir = group_dir / str(year)
            year_dir.mkdir(parents=True, exist_ok=True)
            
            dest_path = year_dir / filename
            
            # Skip if already exists
            if dest_path.exists():
                log(f"Already have {year}/{filename}, skipping")
                continue
            
            if download_file(pdf_url, dest_path):
                log(f"Downloaded {year}/{filename}", "success")
                downloaded += 1
                
                manifest_entries.append({
                    "group": source["group"],
                    "name": source["name"],
                    "source_url": pdf_url,
                    "local_path": str(dest_path.relative_to(dest_path.parents[2])),
                    "detected_date": detected_date.isoformat() if detected_date else None,
                    "method": source["method"],
                    "status": "success",
                    "notes": pdf_text,
                    "hash": hash_file(dest_path)
                })
        
        log(f"Downloaded {downloaded} new Visa Bulletin PDF(s)")
    
    except Exception as e:
        log(f"Error handling {source['name']}: {e}", "error")
        manifest_entries.append({
            "group": source["group"],
            "name": source["name"],
            "source_url": hub_url,
            "local_path": None,
            "detected_date": None,
            "method": source["method"],
            "status": "error",
            "notes": str(e),
            "hash": None
        })


def handle_visa_annual_reports(
    source: Dict[str, Any],
    run_date: datetime,
    group_dir: Path,
    manifest_entries: List[Dict[str, Any]],
    manifest: Dict[str, Any] = None
) -> None:
    """
    Handle visa_annual_reports method for State Dept annual reports.
    
    Multi-level scraping:
    1. Hub page → Find year links (2015-2024)
    2. Each year page → Find all table PDFs
    3. Download into year-specific subfolders
    """
    hub_url = source.get('page_url')
    if not hub_url:
        log(f"No page_url configured for {source['name']}", "error")
        return
    
    regex_filters = source.get("regex_filters", [])
    target_years = list(range(2015, 2025))  # 2015-2024 (10 years)
    
    log(f"Handling {source['name']} with visa_annual_reports method")
    log(f"Hub URL: {hub_url}")
    log(f"Target years: {target_years[0]}-{target_years[-1]}")
    
    try:
        # Step 1: Find year links on hub page
        log(f"Fetching hub page...")
        year_links = find_links(hub_url, "a[href]")
        
        # Filter for year links matching our target years
        year_pages = []
        for link_url, link_text in year_links:
            # Look for patterns like "report-of-the-visa-office-2024.html"
            for year in target_years:
                if f"-{year}.html" in link_url or f"-{year}" in link_url:
                    year_pages.append((link_url, link_text, year))
                    log(f"Found year {year}: {link_text[:60]}")
                    break
        
        if not year_pages:
            log(f"No year pages found for target years", "warning")
            manifest_entries.append({
                "group": source["group"],
                "name": source["name"],
                "source_url": hub_url,
                "local_path": None,
                "detected_date": None,
                "method": source["method"],
                "status": "no_files_found",
                "notes": f"No year pages found for {target_years[0]}-{target_years[-1]}",
                "hash": None
            })
            return
        
        log(f"Found {len(year_pages)} year page(s)")
        
        # Step 2: For each year page, find all table PDFs
        all_pdfs = []
        for year_url, year_text, year in sorted(year_pages, key=lambda x: x[2], reverse=True):
            try:
                log(f"Visiting year {year}: {year_text[:50]}")
                year_page_links = find_links(year_url, "a[href]")
                
                # Filter for PDF links only
                pdf_links = [(url, text) for url, text in year_page_links 
                            if url.lower().endswith('.pdf')]
                
                # Apply regex filters if specified
                if regex_filters:
                    pdf_links = apply_regex_filters(pdf_links, regex_filters)
                
                log(f"Found {len(pdf_links)} PDF(s) for year {year}")
                
                # Add year and PDF info to collection
                for pdf_url, pdf_text in pdf_links:
                    filename = Path(urlparse(pdf_url).path).name
                    all_pdfs.append((pdf_url, pdf_text or filename, year))
            
            except Exception as e:
                log(f"Error processing year {year} page {year_url}: {e}", "warning")
                continue
        
        if not all_pdfs:
            log(f"No PDFs found on year pages", "warning")
            manifest_entries.append({
                "group": source["group"],
                "name": source["name"],
                "source_url": hub_url,
                "local_path": None,
                "detected_date": None,
                "method": source["method"],
                "status": "no_files_found",
                "notes": f"Visited {len(year_pages)} year pages but found no matching PDFs",
                "hash": None
            })
            return
        
        log(f"Found {len(all_pdfs)} PDF(s) total across all years")
        
        # Download PDFs organized by year
        downloaded = 0
        for pdf_url, pdf_text, year in sorted(all_pdfs, key=lambda x: x[2], reverse=True):
            filename = Path(urlparse(pdf_url).path).name
            
            # Create year subfolder
            year_dir = group_dir / str(year)
            year_dir.mkdir(parents=True, exist_ok=True)
            
            dest_path = year_dir / filename
            
            # Skip if already exists
            if dest_path.exists():
                log(f"Already have {year}/{filename}, skipping")
                continue
            
            if download_file(pdf_url, dest_path):
                log(f"Downloaded {year}/{filename}", "success")
                downloaded += 1
                
                manifest_entries.append({
                    "group": source["group"],
                    "name": source["name"],
                    "source_url": pdf_url,
                    "local_path": str(dest_path.relative_to(dest_path.parents[2])),
                    "detected_date": f"{year}-12-31",  # Fiscal year end
                    "method": source["method"],
                    "status": "success",
                    "notes": pdf_text,
                    "hash": hash_file(dest_path)
                })
        
        log(f"Downloaded {downloaded} new file(s)")
    
    except Exception as e:
        log(f"Error handling {source['name']}: {e}", "error")
        manifest_entries.append({
            "group": source["group"],
            "name": source["name"],
            "source_url": hub_url,
            "local_path": None,
            "detected_date": None,
            "method": source["method"],
            "status": "error",
            "notes": str(e),
            "hash": None
        })


def handle_visa_statistics_monthly(
    source: Dict[str, Any],
    run_date: datetime,
    group_dir: Path,
    manifest_entries: List[Dict[str, Any]],
    manifest: Dict[str, Any] = None
) -> None:
    """
    Handle visa_statistics_monthly method for Monthly Immigrant Visa Issuances.
    
    Downloads all available monthly IV statistics files and organizes them by year.
    Each month has 2 files:
    - IV Issuances by FSC or Place of Birth and Visa Class
    - IV Issuances by Post and Visa Class
    """
    page_url = source.get('page_url')
    if not page_url:
        log(f"No page_url configured for {source['name']}", "error")
        return
    
    selector = source.get('selector', "a[href*='.xls'], a[href*='.pdf']")
    
    log(f"Handling {source['name']} with visa_statistics_monthly method")
    log(f"Page URL: {page_url}")
    
    try:
        # Step 1: Find all file links on the page
        log(f"Fetching page...")
        links = find_links(page_url, selector)
        
        # Filter for downloadable files only (PDF, XLS, XLSX)
        file_links = [(url, text) for url, text in links if is_downloadable_file(url)]
        
        # Filter out generic "Excel" text links that are duplicates
        filtered_links = []
        for url, text in file_links:
            # Skip links with just "Excel" or "click here" as text
            if text.strip().lower() in ['excel', 'click here', 'pdf']:
                continue
            # Must contain month and year pattern (e.g., "March 2017")
            if not extract_date_from_text(text):
                continue
            filtered_links.append((url, text))
        
        log(f"Found {len(filtered_links)} file link(s)")
        
        if not filtered_links:
            log(f"No files found", "warning")
            manifest_entries.append({
                "group": source["group"],
                "name": source["name"],
                "source_url": page_url,
                "local_path": None,
                "detected_date": None,
                "method": source["method"],
                "status": "no_files_found",
                "notes": "No matching files found on page",
                "hash": None
            })
            return
        
        # Step 2: Extract dates and prepare for download
        files_with_dates = []
        for url, text in filtered_links:
            detected_date = extract_date_from_text(text)
            if detected_date:
                files_with_dates.append((url, text, detected_date))
                log(f"Found: {text[:70]} (date: {detected_date.strftime('%Y-%m')})")
        
        if not files_with_dates:
            log(f"No files with detectable dates found", "warning")
            manifest_entries.append({
                "group": source["group"],
                "name": source["name"],
                "source_url": page_url,
                "local_path": None,
                "detected_date": None,
                "method": source["method"],
                "status": "no_files_found",
                "notes": "No files with detectable dates",
                "hash": None
            })
            return
        
        log(f"Found {len(files_with_dates)} file(s) with dates")
        
        # Step 3: Download files organized by year (sorted by date, newest first)
        downloaded = 0
        for file_url, file_text, detected_date in sorted(files_with_dates, key=lambda x: x[2], reverse=True):
            filename = Path(urlparse(file_url).path).name
            
            # URL-decode the filename if needed
            try:
                from urllib.parse import unquote
                filename = unquote(filename)
            except:
                pass
            
            # Create year subdirectory
            year = detected_date.year
            year_dir = group_dir / str(year)
            year_dir.mkdir(parents=True, exist_ok=True)
            
            dest_path = year_dir / filename
            
            # Skip if already exists
            if dest_path.exists():
                log(f"Already have {year}/{filename}, skipping")
                continue
            
            if download_file(file_url, dest_path):
                log(f"Downloaded {year}/{filename}", "success")
                downloaded += 1
                
                manifest_entries.append({
                    "group": source["group"],
                    "name": source["name"],
                    "source_url": file_url,
                    "local_path": str(dest_path.relative_to(dest_path.parents[2])),
                    "detected_date": detected_date.isoformat(),
                    "method": source["method"],
                    "status": "success",
                    "notes": file_text,
                    "hash": hash_file(dest_path)
                })
        
        log(f"Downloaded {downloaded} new file(s)")
    
    except Exception as e:
        log(f"Error handling {source['name']}: {e}", "error")
        manifest_entries.append({
            "group": source["group"],
            "name": source["name"],
            "source_url": page_url,
            "local_path": None,
            "detected_date": None,
            "method": source["method"],
            "status": "error",
            "notes": str(e),
            "hash": None
        })


def handle_lca_disclosure_data(
    source: Dict[str, Any],
    run_date: datetime,
    group_dir: Path,
    manifest_entries: List[Dict[str, Any]],
    manifest: Dict[str, Any] = None
) -> None:
    """
    Handle LCA (Labor Condition Application) disclosure data download.
    
    Downloads quarterly LCA disclosure data files and their record layout PDFs,
    organized by fiscal year. Focuses on:
    - LCA_Disclosure_Data_FY{YEAR}_Q{Quarter}.xlsx (main data)
    - LCA_Record_Layout_FY{YEAR}_Q{Quarter}.pdf (explains data structure)
    """
    page_url = source.get('page_url')
    if not page_url:
        log(f"No page_url configured for {source['name']}", "error")
        return
    
    log(f"Handling {source['name']} with lca_disclosure_data method")
    log(f"Page URL: {page_url}")
    
    try:
        # Step 1: Find all LCA disclosure data files
        log(f"Fetching page...")
        links = find_links(page_url, "a[href]")
        
        # Filter for LCA disclosure data and record layout files
        lca_files = []
        for link_url, link_text in links:
            # Check if it's an LCA file (XLSX, XLS, PDF, DOC, DOCX)
            if any(ext in link_url.lower() for ext in ['.xlsx', '.xls', '.pdf', '.doc', '.docx']):
                combined = (link_url + " " + link_text).lower()
                # Look for LCA-related or H-1B files
                if 'lca' in combined or 'h-1b' in combined or 'h1b' in combined:
                    # Focus on disclosure data and record layout files (exclude statistics reports)
                    # Patterns: 
                    # - FY2020+: LCA_Disclosure_Data, LCA_Record_Layout, LCA_Appendix_A, LCA_Worksites
                    # - FY2014-2019: H-1B FY20XX.xlsx, H1B Record Layout FY1X.pdf
                    # - FY2010-2013: LCA FY20XX.xlsx, LCA Record Layout FY1X.doc
                    if ('disclosure' in combined or 'record' in combined or 
                        'layout' in combined or 'appendix' in combined or 
                        'worksite' in combined or 
                        # Match any fiscal year pattern (FY followed by 2-4 digits)
                        (re.search(r'fy\d{2,4}', combined) and ('lca' in combined or 'h-1b' in combined or 'h1b' in combined))):
                        # Exclude selected statistics files
                        if 'selected' not in link_text.lower() and 'statistics' not in link_text.lower():
                            lca_files.append((link_url, link_text))
        
        log(f"Found {len(lca_files)} LCA disclosure data/layout file(s)")
        
        if not lca_files:
            log(f"No LCA files found", "warning")
            manifest_entries.append({
                "group": source["group"],
                "name": source["name"],
                "source_url": page_url,
                "local_path": None,
                "detected_date": None,
                "method": source["method"],
                "status": "no_files_found",
                "notes": "No LCA disclosure data files found on page",
                "hash": None
            })
            return
        
        # Step 2: Extract fiscal year and organize
        files_by_year = {}
        
        for file_url, file_text in lca_files:
            # Extract fiscal year from URL (matches both FY2020 and FY20 formats)
            fy_match = re.search(r'FY(\d{2,4})', file_url, re.IGNORECASE)
            if fy_match:
                fiscal_year = fy_match.group(1)
                # Convert 2-digit year to 4-digit (FY14 → 2014)
                if len(fiscal_year) == 2:
                    fiscal_year = "20" + fiscal_year
                
                # Extract quarter if available
                q_match = re.search(r'Q(\d)', file_url, re.IGNORECASE)
                quarter = q_match.group(1) if q_match else None
                
                if fiscal_year not in files_by_year:
                    files_by_year[fiscal_year] = []
                
                files_by_year[fiscal_year].append((file_url, file_text, quarter))
        
        if not files_by_year:
            log(f"No files with recognizable fiscal year patterns", "warning")
            manifest_entries.append({
                "group": source["group"],
                "name": source["name"],
                "source_url": page_url,
                "local_path": None,
                "detected_date": None,
                "method": source["method"],
                "status": "no_files_found",
                "notes": "No files with FY pattern found",
                "hash": None
            })
            return
        
        log(f"Found files for {len(files_by_year)} fiscal year(s): {', '.join(sorted(files_by_year.keys()))}")
        
        # Step 3: Download files organized by fiscal year
        downloaded = 0
        for fiscal_year in sorted(files_by_year.keys(), reverse=True):
            year_files = files_by_year[fiscal_year]
            
            # Create fiscal year subdirectory
            fy_dir = group_dir / f"FY{fiscal_year}"
            fy_dir.mkdir(parents=True, exist_ok=True)
            
            log(f"Processing FY{fiscal_year} ({len(year_files)} file(s))")
            
            for file_url, file_text, quarter in sorted(year_files, key=lambda x: x[2] or "", reverse=True):
                filename = Path(urlparse(file_url).path).name
                
                dest_path = fy_dir / filename
                
                # Skip if already exists
                if dest_path.exists():
                    log(f"Already have FY{fiscal_year}/{filename}, skipping")
                    continue
                
                if download_file(file_url, dest_path):
                    q_info = f" Q{quarter}" if quarter else ""
                    log(f"Downloaded FY{fiscal_year}{q_info}/{filename}", "success")
                    downloaded += 1
                    
                    manifest_entries.append({
                        "group": source["group"],
                        "name": source["name"],
                        "source_url": file_url,
                        "local_path": str(dest_path.relative_to(dest_path.parents[2])),
                        "detected_date": f"{fiscal_year}-09-30",  # FY end date
                        "method": source["method"],
                        "status": "success",
                        "notes": file_text or filename,
                        "hash": hash_file(dest_path)
                    })
        
        log(f"Downloaded {downloaded} new file(s)")
    
    except Exception as e:
        log(f"Error handling {source['name']}: {e}", "error")
        manifest_entries.append({
            "group": source["group"],
            "name": source["name"],
            "source_url": page_url,
            "local_path": None,
            "detected_date": None,
            "method": source["method"],
            "status": "error",
            "notes": str(e),
            "hash": None
        })


def handle_perm_disclosure_data(
    source: Dict[str, Any],
    run_date: datetime,
    group_dir: Path,
    manifest_entries: List[Dict[str, Any]],
    manifest: Dict[str, Any] = None
) -> None:
    """
    Handle PERM (Permanent Labor Certification) disclosure data download.
    
    Downloads yearly PERM disclosure data files and their record layout PDFs,
    organized by fiscal year under PERM subdirectory. Includes:
    - PERM_Disclosure_Data_FY{YEAR}.xlsx (main data)
    - PERM_Record_Layout_FY{YEAR}.pdf (explains data structure)
    - PERM_Selected_Statistics (optional statistics reports)
    """
    page_url = source.get('page_url')
    if not page_url:
        log(f"No page_url configured for {source['name']}", "error")
        return
    
    log(f"Handling {source['name']} with perm_disclosure_data method")
    log(f"Page URL: {page_url}")
    
    try:
        # Step 1: Find all PERM disclosure data files
        log(f"Fetching page...")
        links = find_links(page_url, "a[href]")
        
        # Filter for PERM disclosure data and record layout files
        perm_files = []
        for link_url, link_text in links:
            # Check if it's a PERM file (XLSX, XLS, PDF, DOC, DOCX)
            if any(ext in link_url.lower() for ext in ['.xlsx', '.xls', '.pdf', '.doc', '.docx']):
                combined = (link_url + " " + link_text).lower()
                # Look for PERM files
                if 'perm' in combined:
                    # Match any fiscal year pattern (FY followed by 2-4 digits)
                    if ('disclosure' in combined or 'record' in combined or 
                        'layout' in combined or 'statistics' in combined or 'selected' in combined or
                        re.search(r'fy\d{2,4}', combined)):
                        perm_files.append((link_url, link_text))
        
        log(f"Found {len(perm_files)} PERM disclosure data/layout file(s)")
        
        if not perm_files:
            log(f"No PERM files found", "warning")
            manifest_entries.append({
                "group": source["group"],
                "name": source["name"],
                "source_url": page_url,
                "local_path": None,
                "detected_date": None,
                "method": source["method"],
                "status": "no_files_found",
                "notes": "No PERM disclosure data files found on page",
                "hash": None
            })
            return
        
        # Step 2: Extract fiscal year and organize
        files_by_year = {}
        
        for file_url, file_text in perm_files:
            # Extract fiscal year from URL (matches both FY2020 and FY20 formats)
            fy_match = re.search(r'FY(\d{2,4})', file_url, re.IGNORECASE)
            if fy_match:
                fiscal_year = fy_match.group(1)
                # Convert 2-digit year to 4-digit (FY14 → 2014)
                if len(fiscal_year) == 2:
                    fiscal_year = "20" + fiscal_year
                
                # Extract quarter if available
                q_match = re.search(r'Q(\d)', file_url, re.IGNORECASE)
                quarter = q_match.group(1) if q_match else None
                
                if fiscal_year not in files_by_year:
                    files_by_year[fiscal_year] = []
                
                files_by_year[fiscal_year].append((file_url, file_text, quarter))
        
        if not files_by_year:
            log(f"No files with recognizable fiscal year patterns", "warning")
            manifest_entries.append({
                "group": source["group"],
                "name": source["name"],
                "source_url": page_url,
                "local_path": None,
                "detected_date": None,
                "method": source["method"],
                "status": "no_files_found",
                "notes": "No files with FY pattern found",
                "hash": None
            })
            return
        
        log(f"Found files for {len(files_by_year)} fiscal year(s): {', '.join(sorted(files_by_year.keys()))}")
        
        # Step 3: Download files organized by fiscal year under PERM subdirectory
        downloaded = 0
        perm_dir = group_dir / "PERM"
        perm_dir.mkdir(parents=True, exist_ok=True)
        
        for fiscal_year in sorted(files_by_year.keys(), reverse=True):
            year_files = files_by_year[fiscal_year]
            
            # Create fiscal year subdirectory under PERM
            fy_dir = perm_dir / f"FY{fiscal_year}"
            fy_dir.mkdir(parents=True, exist_ok=True)
            
            log(f"Processing FY{fiscal_year} ({len(year_files)} file(s))")
            
            for file_url, file_text, quarter in sorted(year_files, key=lambda x: x[2] or "", reverse=True):
                filename = Path(urlparse(file_url).path).name
                
                dest_path = fy_dir / filename
                
                # Skip if already exists
                if dest_path.exists():
                    log(f"Already have FY{fiscal_year}/{filename}, skipping")
                    continue
                
                if download_file(file_url, dest_path):
                    q_info = f" Q{quarter}" if quarter else ""
                    log(f"Downloaded FY{fiscal_year}{q_info}/{filename}", "success")
                    downloaded += 1
                    
                    manifest_entries.append({
                        "group": source["group"],
                        "name": source["name"],
                        "source_url": file_url,
                        "local_path": str(dest_path.relative_to(dest_path.parents[2])),
                        "detected_date": f"{fiscal_year}-09-30",  # FY end date
                        "method": source["method"],
                        "status": "success",
                        "notes": file_text or filename,
                        "hash": hash_file(dest_path)
                    })
        
        log(f"Downloaded {downloaded} new file(s)")
    
    except Exception as e:
        log(f"Error handling {source['name']}: {e}", "error")
        manifest_entries.append({
            "group": source["group"],
            "name": source["name"],
            "source_url": page_url,
            "local_path": None,
            "detected_date": None,
            "method": source["method"],
            "status": "error",
            "notes": str(e),
            "hash": None
        })


def handle_uscis_employment_data(
    source: Dict[str, Any],
    run_date: datetime,
    group_dir: Path,
    manifest_entries: List[Dict[str, Any]],
    manifest: Dict[str, Any] = None
) -> None:
    """
    Handle USCIS employment-based immigration data download.
    
    Downloads employment-based immigration forms from USCIS:
    - I-140 (Immigrant Worker Petitions)
    - I-485 (Adjustment of Status)  
    - I-765 (Employment Authorization)
    - I-360 (Special Immigrant Petitions)
    - I-526/I-526E (EB-5 Investor Petitions)
    - EB inventory files
    
    Organized by fiscal year under employment_based subdirectory.
    Historical coverage: 1991-present with pagination support.
    """
    page_url = source.get('page_url')
    if not page_url:
        log(f"No page_url configured for {source['name']}", "error")
        return
    
    log(f"Handling {source['name']} with uscis_employment_data method")
    log(f"Base URL: {page_url}")
    
    # Initialize manifest if not provided
    if manifest is None:
        manifest = {"entries": [], "files_by_url": {}}
    
    try:
        # Step 1: Fetch all pages with pagination
        all_employment_files = []
        page = 0
        max_pages = 20  # Safety limit
        
        # Use filtered URL with employment topics if not already present
        if 'topic_id' not in page_url:
            # Add employment topic filters and pagination support
            base_url = page_url.split('?')[0]
            base_url = f"{base_url}?topic_id%5B0%5D=33682&topic_id%5B1%5D=33599&topic_id%5B2%5D=33631&topic_id%5B3%5D=33674&topic_id%5B4%5D=33737&topic_id%5B5%5D=33628&topic_id%5B6%5D=33614&topic_id%5B7%5D=33685&topic_id%5B8%5D=33615&topic_id%5B9%5D=33686&topic_id%5B10%5D=33687&topic_id%5B11%5D=33690&topic_id%5B12%5D=33691&topic_id%5B13%5D=33701&ddt_mon=&ddt_yr=&query=&items_per_page=100"
        else:
            # Use provided filtered URL, ensure items_per_page=100
            base_url = page_url
            if 'items_per_page' not in base_url:
                base_url += '&items_per_page=100'
        
        log(f"Fetching pages with pagination...")
        
        while page < max_pages:
            paginated_url = f"{base_url}&page={page}"
            log(f"Fetching page {page}...")
            
            links = find_links(paginated_url, "a[href]")
            
            # Filter for employment-based files on this page
            page_files = []
            for link_url, link_text in links:
                # Check if it's a data file (XLSX, XLS, CSV)
                if any(ext in link_url.lower() for ext in ['.xlsx', '.xls', '.csv']):
                    combined = (link_url + " " + link_text).lower()
                    # Look for employment-based keywords
                    if any(keyword in combined for keyword in ['i-140', 'i140', 'i-485', 'i485', 
                                                                'i-765', 'i765', 'i-360', 'i360',
                                                                'i-526', 'i526', 'eb_', 'employment']):
                        page_files.append((link_url, link_text))
            
            if not page_files:
                log(f"No files found on page {page} - end of pagination")
                break
            
            log(f"Found {len(page_files)} employment files on page {page}")
            all_employment_files.extend(page_files)
            
            # Check for "next" pagination link to see if there are more pages
            has_next = False
            for link_url, link_text in links:
                if 'next' in link_text.lower() or '›' in link_text or '»' in link_text:
                    has_next = True
                    break
            
            if not has_next:
                log(f"No 'next' link found - reached last page")
                break
            
            page += 1
        
        log(f"Found {len(all_employment_files)} total employment-based file(s) across {page + 1} page(s)")
        
        if not all_employment_files:
            log(f"No employment-based files found", "warning")
            manifest_entries.append({
                "group": source["group"],
                "name": source["name"],
                "source_url": base_url,
                "local_path": None,
                "detected_date": None,
                "method": source["method"],
                "status": "no_files_found",
                "notes": "No employment-based files found on any page",
                "hash": None
            })
            return
        
        # Step 2: Extract fiscal year and organize
        files_by_year = {}
        monthly_files = []  # For EB inventory files without FY
        
        for file_url, file_text in all_employment_files:
            # Extract fiscal year from URL (matches both FY2025 and FY25 formats)
            fy_match = re.search(r'fy(\d{2,4})', file_url.lower())
            
            if fy_match:
                fiscal_year = fy_match.group(1)
                # Convert 2-digit year to 4-digit (FY25 → 2025)
                if len(fiscal_year) == 2:
                    fiscal_year = "20" + fiscal_year
                
                # Extract quarter if available
                q_match = re.search(r'q(\d)', file_url.lower())
                quarter = q_match.group(1) if q_match else None
                
                if fiscal_year not in files_by_year:
                    files_by_year[fiscal_year] = []
                
                files_by_year[fiscal_year].append((file_url, file_text, quarter))
            else:
                # Files without FY (like monthly EB inventory)
                # Try to extract year/month from filename or text
                date_match = re.search(r'(january|february|march|april|may|june|july|august|september|october|november|december)[\s_]+(\d{4})', 
                                       file_url.lower() + " " + file_text.lower())
                if date_match:
                    year = date_match.group(2)
                    monthly_files.append((file_url, file_text, year))
                else:
                    # Default to current year if no date found
                    current_year = str(run_date.year)
                    monthly_files.append((file_url, file_text, current_year))
        
        # Combine monthly files into files_by_year
        for file_url, file_text, year in monthly_files:
            if year not in files_by_year:
                files_by_year[year] = []
            files_by_year[year].append((file_url, file_text, None))
        
        if not files_by_year:
            log(f"No files with recognizable year patterns", "warning")
            manifest_entries.append({
                "group": source["group"],
                "name": source["name"],
                "source_url": page_url,
                "local_path": None,
                "detected_date": None,
                "method": source["method"],
                "status": "no_files_found",
                "notes": "No files with year pattern found",
                "hash": None
            })
            return
        
        log(f"Found files for {len(files_by_year)} year(s): {', '.join(sorted(files_by_year.keys()))}")
        
        # Step 3: Download files organized by year under employment_based subdirectory
        downloaded = 0
        employment_dir = group_dir / "employment_based"
        employment_dir.mkdir(parents=True, exist_ok=True)
        
        for year in sorted(files_by_year.keys(), reverse=True):
            year_files = files_by_year[year]
            
            # Create year subdirectory under employment_based
            year_dir = employment_dir / year
            year_dir.mkdir(parents=True, exist_ok=True)
            
            log(f"Processing {year} ({len(year_files)} file(s))")
            
            for file_url, file_text, quarter in sorted(year_files, key=lambda x: x[2] or "", reverse=True):
                filename = Path(urlparse(file_url).path).name
                
                dest_path = year_dir / filename
                
                # Skip if already in manifest and file exists
                if manifest and is_file_in_manifest(file_url, dest_path, manifest):
                    # File already downloaded previously
                    continue
                
                if download_file(file_url, dest_path):
                    q_info = f" Q{quarter}" if quarter else ""
                    log(f"Downloaded {year}{q_info}/{filename}", "success")
                    downloaded += 1
                    
                    entry = {
                        "group": source["group"],
                        "name": source["name"],
                        "source_url": file_url,
                        "local_path": str(dest_path.relative_to(dest_path.parents[2])),
                        "detected_date": f"{year}-09-30" if quarter else f"{year}-12-31",
                        "downloaded_at": datetime.now().isoformat(),
                        "method": source["method"],
                        "status": "success",
                        "notes": file_text or filename,
                        "hash": hash_file(dest_path)
                    }
                    manifest_entries.append(entry)
                    
                    # Update manifest index for future lookups in this run
                    if manifest:
                        manifest['files_by_url'][file_url] = entry
        
        log(f"Downloaded {downloaded} new file(s)")
    
    except Exception as e:
        log(f"Error handling {source['name']}: {e}", "error")
        manifest_entries.append({
            "group": source["group"],
            "name": source["name"],
            "source_url": page_url,
            "local_path": None,
            "detected_date": None,
            "method": source["method"],
            "status": "error",
            "notes": str(e),
            "hash": None
        })


def handle_manual_or_auth(
    source: Dict[str, Any],
    run_date: datetime,
    group_dir: Path,
    manifest_entries: List[Dict[str, Any]],
    manifest: Dict[str, Any] = None
) -> None:
    """Handle manual_or_auth method (TRAC - skip and log)."""
    log(f"Skipping {source['name']} - requires authentication", "warning")
    
    manifest_entries.append({
        "group": source["group"],
        "name": source["name"],
        "source_url": source.get('page_url', ''),
        "local_path": None,
        "detected_date": None,
        "method": source["method"],
        "status": "skipped",
        "notes": "Requires authentication/subscription - manual download needed",
        "hash": None
    })


def handle_api_bls(
    source: Dict[str, Any],
    run_date: datetime,
    group_dir: Path,
    manifest_entries: List[Dict[str, Any]],
    manifest: Dict[str, Any] = None
) -> None:
    """Handle BLS API method."""
    log(f"Processing {source['name']} via BLS API")
    
    series_ids = source.get('bls_series_ids', [])
    if not series_ids:
        log(f"No BLS series IDs configured for {source['name']}", "warning")
        return
    
    api_key = os.environ.get('BLS_API_KEY')
    
    # Fetch last 12 months (use past 2 years to ensure coverage)
    start_year = run_date.year - 1
    end_year = run_date.year
    
    try:
        data = bls_fetch(series_ids, start_year, end_year, api_key)
        
        filename = f"ces_{run_date.strftime('%Y%m%d')}.json"
        dest_path = group_dir / filename
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
        
        log(f"Saved BLS data: {filename}", "success")
        
        manifest_entries.append({
            "group": source["group"],
            "name": source["name"],
            "source_url": source.get('api_endpoint', ''),
            "local_path": str(dest_path.relative_to(dest_path.parents[1])),
            "detected_date": run_date.isoformat(),
            "method": source["method"],
            "status": "success",
            "notes": f"Series: {', '.join(series_ids)}",
            "hash": hash_file(dest_path)
        })
    
    except Exception as e:
        log(f"Error fetching BLS data: {e}", "error")
        manifest_entries.append({
            "group": source["group"],
            "name": source["name"],
            "source_url": source.get('api_endpoint', ''),
            "local_path": None,
            "detected_date": None,
            "method": source["method"],
            "status": "error",
            "notes": str(e),
            "hash": None
        })


def handle_api_census(
    source: Dict[str, Any],
    run_date: datetime,
    group_dir: Path,
    manifest_entries: List[Dict[str, Any]],
    manifest: Dict[str, Any] = None
) -> None:
    """Handle Census ACS API method."""
    log(f"Processing {source['name']} via Census ACS API")
    
    variables = source.get('acs_variables', [])
    geography = source.get('acs_geography', 'state:*')
    
    if not variables:
        log(f"No ACS variables configured for {source['name']}", "warning")
        return
    
    api_key = os.environ.get('CENSUS_API_KEY')
    
    # Use latest available year (typically run_date.year - 1)
    year = run_date.year - 1
    
    try:
        data = census_fetch_acs1(year, variables, geography, api_key)
        
        filename = f"acs1_{year}_nativity.json"
        dest_path = group_dir / filename
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
        
        log(f"Saved ACS data: {filename}", "success")
        
        manifest_entries.append({
            "group": source["group"],
            "name": source["name"],
            "source_url": source.get('api_endpoint', ''),
            "local_path": str(dest_path.relative_to(dest_path.parents[1])),
            "detected_date": run_date.isoformat(),
            "method": source["method"],
            "status": "success",
            "notes": f"Year: {year}, Variables: {', '.join(variables)}",
            "hash": hash_file(dest_path)
        })
    
    except Exception as e:
        log(f"Error fetching ACS data: {e}", "error")
        manifest_entries.append({
            "group": source["group"],
            "name": source["name"],
            "source_url": source.get('api_endpoint', ''),
            "local_path": None,
            "detected_date": None,
            "method": source["method"],
            "status": "error",
            "notes": str(e),
            "hash": None
        })


def handle_direct_file(
    source: Dict[str, Any],
    run_date: datetime,
    group_dir: Path,
    manifest_entries: List[Dict[str, Any]],
    manifest: Dict[str, Any] = None
) -> None:
    """Handle direct_file method (California WARN)."""
    log(f"Processing {source['name']} via direct_file")
    
    url = source.get('url', '')
    
    if not url:
        log(f"Missing URL for {source['name']}", "warning")
        return
    
    try:
        filename = Path(urlparse(url).path).name or 'WARN_Report.xlsx'
        dest_path = group_dir / filename
        
        if download_file(url, dest_path):
            log(f"Downloaded {filename}", "success")
            
            manifest_entries.append({
                "group": source["group"],
                "name": source["name"],
                "source_url": url,
                "local_path": str(dest_path.relative_to(dest_path.parents[1])),
                "detected_date": run_date.isoformat(),
                "method": source["method"],
                "status": "success",
                "notes": "Full WARN report - requires date filtering",
                "hash": hash_file(dest_path)
            })
        else:
            manifest_entries.append({
                "group": source["group"],
                "name": source["name"],
                "source_url": url,
                "local_path": None,
                "detected_date": None,
                "method": source["method"],
                "status": "download_failed",
                "notes": "Failed to download",
                "hash": None
            })
    
    except Exception as e:
        log(f"Error downloading {source['name']}: {e}", "error")
        manifest_entries.append({
            "group": source["group"],
            "name": source["name"],
            "source_url": url,
            "local_path": None,
            "detected_date": None,
            "method": source["method"],
            "status": "error",
            "notes": str(e),
            "hash": None
        })


def handle_warn_state(
    source: Dict[str, Any],
    run_date: datetime,
    base_downloads_dir: Path,
    manifest_entries: List[Dict[str, Any]],
    manifest: Dict[str, Any] = None
) -> None:
    """Handle WARN data for a specific state."""
    state = source.get('state', 'UNKNOWN')
    method = source.get('method', 'scrape')
    
    log(f"Processing WARN data for {state} via {method}")
    
    # Create WARN/<STATE> directory
    group_dir = base_downloads_dir / 'WARN' / state
    group_dir.mkdir(parents=True, exist_ok=True)
    
    # Group name for manifest
    manifest_group = f"WARN/{state}"
    
    if method == 'direct_file':
        # Direct download (e.g., CA)
        handle_warn_direct_file(source, state, manifest_group, run_date, group_dir, manifest_entries, manifest)
    else:
        # Scraping (TX, FL, etc.)
        handle_warn_scrape(source, state, manifest_group, run_date, group_dir, manifest_entries, manifest)


def handle_warn_direct_file(
    source: Dict[str, Any],
    state: str,
    manifest_group: str,
    run_date: datetime,
    group_dir: Path,
    manifest_entries: List[Dict[str, Any]],
    manifest: Dict[str, Any] = None
) -> None:
    """Handle direct file download for WARN (e.g., California)."""
    # Support both file_url (new) and url (legacy)
    url = source.get('file_url', source.get('url', ''))
    
    if not url:
        log(f"Missing file_url for WARN {state}", "warning")
        return
    
    try:
        filename = Path(urlparse(url).path).name or f'WARN_{state}.xlsx'
        dest_path = group_dir / filename
        
        if download_file(url, dest_path):
            log(f"Downloaded {state}: {filename}", "success")
            
            manifest_entries.append({
                "group": manifest_group,
                "name": source["name"],
                "source_url": url,
                "local_path": str(dest_path.relative_to(dest_path.parents[2])),
                "detected_date": run_date.isoformat(),
                "method": source["method"],
                "status": "success",
                "notes": f"{state} WARN report - full dataset requiring date filtering",
                "hash": hash_file(dest_path)
            })
        else:
            manifest_entries.append({
                "group": manifest_group,
                "name": source["name"],
                "source_url": url,
                "local_path": None,
                "detected_date": None,
                "method": source["method"],
                "status": "download_failed",
                "notes": "Failed to download",
                "hash": None
            })
    
    except Exception as e:
        log(f"Error downloading WARN {state}: {e}", "error")
        manifest_entries.append({
            "group": manifest_group,
            "name": source["name"],
            "source_url": url,
            "local_path": None,
            "detected_date": None,
            "method": source["method"],
            "status": "error",
            "notes": str(e),
            "hash": None
        })


def handle_warn_scrape(
    source: Dict[str, Any],
    state: str,
    manifest_group: str,
    run_date: datetime,
    group_dir: Path,
    manifest_entries: List[Dict[str, Any]],
    manifest: Dict[str, Any] = None
) -> None:
    """Handle scraping WARN data for a state."""
    page_urls = source.get('page_urls', [source.get('page_url', '')])
    selector = source.get('selector', 'a[href]')
    pattern = source.get('pattern', '')
    regex_filters = source.get('regex_filters', [])
    
    if not any(page_urls):
        log(f"Missing page_url for WARN {state}", "warning")
        return
    
    all_links = []
    
    # Scrape all provided URLs
    for page_url in page_urls:
        if not page_url:
            continue
        try:
            links = find_links(page_url, selector)
            
            # Filter to only downloadable files (no HTML)
            downloadable_links = [(url, text) for url, text in links if is_downloadable_file(url)]
            
            # Apply regex filters if specified
            if regex_filters:
                downloadable_links = apply_regex_filters(downloadable_links, regex_filters)
            
            # Apply pattern filter if specified (legacy support)
            if pattern:
                pattern_lower = pattern.lower()
                filtered = []
                for url, text in downloadable_links:
                    combined = (url + " " + text).lower()
                    if pattern_lower in combined:
                        filtered.append((url, text))
                downloadable_links = filtered
            
            all_links.extend(downloadable_links)
        except Exception as e:
            log(f"Error scraping {page_url}: {e}", "warning")
    
    # Filter by date
    recent = pick_recent_links(all_links, run_date, within_months=12)
    
    if not recent:
        log(f"No recent downloadable files found for WARN {state}", "warning")
        manifest_entries.append({
            "group": manifest_group,
            "name": source["name"],
            "source_url": page_urls[0] if page_urls else '',
            "local_path": None,
            "detected_date": None,
            "method": source["method"],
            "status": "no_files_found",
            "notes": "No downloadable files within 12-month window",
            "hash": None
        })
        return
    
    # Download files
    for url, text, detected_date in sorted(recent, key=lambda x: x[2] or datetime.min, reverse=True):
        filename = Path(urlparse(url).path).name
        if not filename or filename == '/':
            filename = f"WARN_{state}_{detected_date.strftime('%Y%m') if detected_date else 'unknown'}{guess_file_extension(url)}"
        
        dest_path = group_dir / filename
        
        # Skip if already exists (dedupe)
        if dest_path.exists():
            continue
        
        if download_file(url, dest_path):
            log(f"Downloaded {state}: {filename}", "success")
            
            manifest_entries.append({
                "group": manifest_group,
                "name": source["name"],
                "source_url": url,
                "local_path": str(dest_path.relative_to(dest_path.parents[2])),
                "detected_date": detected_date.isoformat() if detected_date else None,
                "method": source["method"],
                "status": "success",
                "notes": text,
                "hash": hash_file(dest_path)
            })


# ============================================================================
# MAIN PROCESSING
# ============================================================================

def create_zip_archive(downloads_dir: Path, run_date: datetime, exports_dir: Path) -> Path:
    """
    Create zip archive of downloads.
    
    Args:
        downloads_dir: Downloads directory to zip
        run_date: Run date for naming
        exports_dir: Exports directory
    
    Returns:
        Path to created zip file
    """
    log("Creating zip archive")
    
    exports_dir.mkdir(parents=True, exist_ok=True)
    zip_name = f"latest_datasets_{run_date.strftime('%Y-%m-%d')}.zip"
    zip_path = exports_dir / zip_name
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in downloads_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(downloads_dir)
                zf.write(file_path, arcname)
    
    log(f"Created archive: {zip_path}", "success")
    return zip_path


def print_summary(manifest_entries: List[Dict[str, Any]], zip_path: Path) -> None:
    """
    Print run summary.
    
    Args:
        manifest_entries: List of all manifest entries
        zip_path: Path to created zip archive
    """
    print("\n" + "=" * 60)
    print("RUN SUMMARY")
    print("=" * 60)
    
    # Count by group
    from collections import Counter
    group_counts = Counter(e['group'] for e in manifest_entries if e['status'] == 'success')
    
    print("\nFiles downloaded by group:")
    for group, count in sorted(group_counts.items()):
        print(f"  {group:40s} {count:3d} files")
    
    # Failures
    failures = [e for e in manifest_entries if e['status'] in ('error', 'download_failed')]
    if failures:
        print(f"\nFailures: {len(failures)}")
        for f in failures[:5]:  # Show first 5
            print(f"  ✗ {f['name']}: {f['notes']}")
    
    # Skipped
    skipped = [e for e in manifest_entries if e['status'] == 'skipped']
    if skipped:
        print(f"\nSkipped (requires auth): {len(skipped)}")
        for s in skipped:
            print(f"  ⊘ {s['name']}")
    
    print(f"\nTotal successful downloads: {len([e for e in manifest_entries if e['status'] == 'success'])}")
    print(f"Archive created: {zip_path}")
    print("=" * 60 + "\n")


def main(config_path: str) -> int:
    """
    Main entry point.
    
    Args:
        config_path: Path to sources.yaml
    
    Returns:
        Exit code
    """
    # Load configuration
    log(f"Loading configuration from {config_path}")
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        log(f"Failed to load config: {e}", "error")
        return 1
    
    sources = config.get('sources', [])
    if not sources:
        log("No sources configured", "error")
        return 1
    
    # Setup directories
    run_date = datetime.now()
    date_str = run_date.strftime('%Y-%m-%d')
    
    base_dir = Path.cwd()
    downloads_dir = base_dir / 'downloads'
    exports_dir = base_dir / 'exports'
    
    downloads_dir.mkdir(parents=True, exist_ok=True)
    
    # Calculate time windows
    window_12m_start = run_date - timedelta(days=365)
    
    log(f"Run Date: {date_str}")
    log(f"12-month window: {window_12m_start.strftime('%Y-%m-%d')} to {date_str}")
    
    # Load previous manifest for incremental downloads
    manifest = load_manifest(downloads_dir)
    manifest_entries = manifest.get('entries', [])
    new_downloads = 0
    skipped_existing = 0
    
    log(f"Starting incremental download (tracking delta only)...\n")
    
    for source in sources:
        name = source.get('name', 'Unknown')
        group = source.get('group', 'Other')
        method = source.get('method', 'unknown')
        
        print(f"\n{'=' * 60}")
        
        # Special handling for WARN (multi-state with subfolders)
        if group == 'WARN':
            state = source.get('state', 'UNKNOWN')
            log(f"Group: WARN/{state}")
            handle_warn_state(source, run_date, downloads_dir, manifest_entries, manifest)
            time.sleep(1)
            continue
        
        log(f"Group: {group}")
        
        group_dir = downloads_dir / group
        group_dir.mkdir(parents=True, exist_ok=True)
        
        # Route to appropriate handler (with manifest for incremental downloads)
        if method == 'scrape_or_pattern':
            handle_scrape_or_pattern(source, run_date, group_dir, manifest_entries, manifest)
        elif method == 'scrape':
            handle_scrape(source, run_date, group_dir, manifest_entries, manifest)
        elif method == 'scrape_if_available':
            handle_scrape_if_available(source, run_date, group_dir, manifest_entries, manifest)
        elif method == 'visa_bulletin_multilevel':
            handle_visa_bulletin_multilevel(source, run_date, group_dir, manifest_entries, manifest)
        elif method == 'visa_annual_reports':
            handle_visa_annual_reports(source, run_date, group_dir, manifest_entries, manifest)
        elif method == 'visa_statistics_monthly':
            handle_visa_statistics_monthly(source, run_date, group_dir, manifest_entries, manifest)
        elif method == 'lca_disclosure_data':
            handle_lca_disclosure_data(source, run_date, group_dir, manifest_entries, manifest)
        elif method == 'perm_disclosure_data':
            handle_perm_disclosure_data(source, run_date, group_dir, manifest_entries, manifest)
        elif method == 'uscis_employment_data':
            handle_uscis_employment_data(source, run_date, group_dir, manifest_entries, manifest)
        elif method == 'manual_or_auth':
            handle_manual_or_auth(source, run_date, group_dir, manifest_entries, manifest)
        elif method == 'api':
            # Determine API type from source name/group
            if 'BLS' in group:
                handle_api_bls(source, run_date, group_dir, manifest_entries, manifest)
            elif 'ACS' in group:
                handle_api_census(source, run_date, group_dir, manifest_entries, manifest)
        elif method == 'direct_file':
            handle_direct_file(source, run_date, group_dir, manifest_entries, manifest)
        else:
            log(f"Unknown method '{method}' for {name}", "warning")
        
        # Small delay between sources to be polite
        time.sleep(1)
    
    # Write final manifest
    manifest_path = downloads_dir / '_manifest.json'
    final_manifest = {
        "run_date": run_date.isoformat(),
        "window_12m_start": window_12m_start.isoformat(),
        "window_12m_end": run_date.isoformat(),
        "total_files": len([e for e in manifest_entries if e.get('status') == 'success']),
        "entries": manifest_entries
    }
    
    manifest_path.write_text(json.dumps(final_manifest, indent=2), encoding='utf-8')
    log(f"\nWrote manifest: {manifest_path}", "success")
    log(f"Total tracked files: {final_manifest['total_files']}")
    
    # Create zip archive
    zip_path = create_zip_archive(downloads_dir, run_date, exports_dir)
    
    # Print summary
    print_summary(manifest_entries, zip_path)
    
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python fetch_latest.py <sources.yaml>")
        sys.exit(1)
    
    config_path = sys.argv[1]
    sys.exit(main(config_path))
