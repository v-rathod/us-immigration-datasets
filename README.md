# Immigration & Labor Data Fetcher

🚀 **Comprehensive historical data collection tool** for immigration and labor datasets from official U.S. government sources.

This automated system fetches and organizes **1,033+ files** spanning **decades of immigration data** (1991-2026), with intelligent incremental updates to avoid duplicate downloads.

> **📋 For AI Assistants** — start here before writing any code:
> 1. [`/Users/vrathod1/dev/NorthStar/NORTHSTAR_VISION.md`](../NORTHSTAR_VISION.md) — Program vision, architecture, guardrails
> 2. [`/Users/vrathod1/dev/NorthStar/BEST_PRACTICES.md`](../BEST_PRACTICES.md) — Engineering conventions, testing strategy, agent checklist
> 3. [`ARCHITECTURE.md`](ARCHITECTURE.md) — P1 technical design
> 4. [`.github/copilot-instructions.md`](.github/copilot-instructions.md) — P1 detailed context (auto-loaded by Copilot)
> 5. [`PROGRESS.md`](PROGRESS.md) — Chronological milestone history

## ✨ Key Features

- **📊 Historical Coverage**: Complete data archives going back 10-35 years depending on source
- **🔄 Incremental Downloads**: Smart manifest-based tracking downloads only new files
- **📁 Organized Storage**: Files automatically organized by fiscal year and data type
- **⚙️ Config-Driven**: Easy customization via `sources.yaml`
- **🛡️ Robust**: Built-in retry logic, bot detection bypass, error handling
- **🎯 Specialized Handlers**: 15 custom handlers for different government data formats
- **📝 Manifest Tracking**: JSON-based download history with file hashes and timestamps

## 📦 Data Sources & Coverage

### ✅ Fully Operational Sources

| Source | Files | Years | Description |
|--------|-------|-------|-------------|
| **Visa Bulletin** | 167 PDFs | FY2011-2026 | Monthly priority date bulletins organized by year |
| **Visa Statistics** | 184 PDFs | Mar 2017-May 2025 | Monthly immigrant visa issuance statistics |
| **Visa Annual Reports** | 273 PDFs | FY2015-FY2024 | Detailed annual visa statistics reports |
| **NIV Statistics** | 32 files | Dec 2021-Jul 2024 | Non-immigrant visa statistics |
| **LCA (H-1B)** | 85 files | FY2008-2026 | H-1B Labor Condition Application disclosure data |
| **PERM** | 47 files | FY2008-2026 | Permanent labor certification disclosure data |
| **USCIS Employment** | 245 files | 1991-2026 | I-140, I-485, I-765, I-360, I-526/I-829 statistics |

**Total: 1,033+ files** covering multiple decades of immigration and labor data.

### 🎯 Data Organization

```
downloads/
├── Visa_Bulletin/
│   ├── FY2011/ ... FY2026/
│   └── [167 monthly bulletins organized by fiscal year]
├── Visa_Statistics/
│   ├── 2017/ ... 2025/
│   └── [184 monthly reports organized by calendar year]
├── Visa_Annual_Reports/
│   ├── FY2015/ ... FY2024/
│   └── [273 detailed annual reports]
├── NIV_Statistics/
│   └── [32 non-immigrant visa statistics files]
├── LCA/
│   ├── H1B/
│   │   └── FY2008/ ... FY2026/
│   │       └── [85 quarterly H-1B disclosure files]
│   └── PERM/
│       └── FY2008/ ... FY2026/
│           └── [47 quarterly PERM disclosure files]
├── USCIS/
│   ├── I-140/ I-485/ I-765/ I-360/ I-526/ I-829/
│   └── [245 employment-based immigration files, 1991-2026]
└── _manifest.json
    └── [Download tracking with 160+ entries]
```

## 🔧 Requirements

- **Python 3.10+** (tested with Python 3.12.3)
- **Internet connection**
- **~5GB disk space** for complete dataset

## 📥 Installation

### 1. Clone this repository

```bash
git clone <repository-url>
cd fetch-immigration-data
```

### 2. Create and activate virtual environment

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```cmd
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

**Dependencies:**
- `requests` - HTTP library with retry logic
- `beautifulsoup4` - HTML parsing for web scraping
- `pyyaml` - YAML configuration file parsing

## ⚙️ Configuration

### Customizing Data Sources

Edit `sources.yaml` to configure data collection:

```yaml
sources:
  - name: "Visa Bulletin"
    group: "Visa_Bulletin"
    method: "visa_bulletin_multilevel"  # Custom handler
    base_url: "https://travel.state.gov/..."
    start_year: 2011  # Fetch from FY2011 onwards
    notes: "Monthly visa priority date bulletins"
```

**Available Methods:**
- `visa_bulletin_multilevel` - Multi-level page traversal for visa bulletins
- `scrape` - Generic web scraping with CSS selectors
- `direct_file` - Direct file downloads
- `lca_disclosure_data` - H-1B/PERM quarterly data from DOL
- `perm_disclosure_data` - PERM certification data
- `uscis_employment_data` - USCIS forms with pagination support

**Key Configuration Options:**
- `start_year` / `end_year` - Define year range for historical collection
- `selector` - CSS selector for finding download links
- `pattern` - Regex pattern to filter specific files
- `filetype` - Expected file extension (pdf, xlsx, csv, etc.)

## 🚀 Usage

### First Run (Historical Data Collection)

```bash
python fetch_latest.py sources.yaml
```

This will:
1. **Load configuration** from `sources.yaml`
2. **Create downloads directory** structure
3. **Fetch historical data** for all configured sources
4. **Download 900+ files** (takes 15-30 minutes)
5. **Generate manifest** tracking all downloads
6. **Print summary** with file counts and status

### Subsequent Runs (Incremental Updates)

```bash
python fetch_latest.py sources.yaml
```

The system automatically:
- ✅ **Loads existing manifest** (160+ tracked files)
- ✅ **Discovers available files** from each source
- ✅ **Skips existing files** (no duplicate downloads)
- ✅ **Downloads only new files** (delta-only updates)
- ✅ **Updates manifest** with new entries

**Example Output:**
```
→ Loaded manifest: 160 files previously downloaded
→ Starting incremental download (tracking delta only)...

→ Group: LCA (H-1B Data)
→ Found 85 files across 19 fiscal years (2008-2026)
→ Already have FY2026/LCA_Disclosure_Data_FY2026_Q1.xlsx, skipping
...
→ Downloaded 0 new file(s)  # No new files available

→ Group: PERM
→ Found 47 files across 19 fiscal years (2008-2026)
→ Downloaded 2 new file(s)  # FY2026 Q2 just released!
```

### 🔄 How Incremental Downloads Work

1. **Manifest Loading**: Reads `downloads/_manifest.json` with download history
2. **URL Indexing**: Builds in-memory index for O(1) lookups
3. **File Discovery**: Scrapes each source to find available files
4. **Dual Verification**: Checks both manifest entry AND physical file existence
5. **Smart Skipping**: Bypasses files that already exist
6. **Delta Downloads**: Only fetches truly new files
7. **Manifest Update**: Adds new downloads with timestamp and hash

**Benefits:**
- ⚡ **Fast execution** - Only network calls for discovery, no file transfers
- 💾 **Bandwidth efficient** - Downloads only what's needed
- 🔍 **Transparent** - Clear logging shows what's skipped vs downloaded
- 🛡️ **Resilient** - Verifies both manifest and disk to handle manual deletions

## 📂 Output Structure

```
fetch-immigration-data/
├── downloads/
│   ├── Visa_Bulletin/
│   │   ├── FY2011/ ... FY2026/
│   │   └── [167 monthly PDF bulletins]
│   ├── Visa_Statistics/
│   │   ├── 2017/ ... 2025/
│   │   └── [184 monthly PDF reports]
│   ├── Visa_Annual_Reports/
│   │   ├── FY2015/ ... FY2024/
│   │   └── [273 detailed annual PDFs]
│   ├── NIV_Statistics/
│   │   └── [32 non-immigrant visa statistics]
│   ├── LCA/
│   │   ├── H1B/
│   │   │   ├── FY2008/ ... FY2026/
│   │   │   └── [85 quarterly Excel files]
│   │   └── PERM/
│   │       ├── FY2008/ ... FY2026/
│   │       └── [47 quarterly Excel files]
│   ├── USCIS/
│   │   ├── I-140/, I-485/, I-765/
│   │   ├── I-360/, I-526/, I-829/
│   │   └── [245 employment immigration files, 1991-2026]
│   └── _manifest.json  # Download tracking database
└── exports/  # (Reserved for future ZIP exports)
```

**File Organization Patterns:**
- **Visa data**: Organized by fiscal year (FY) or calendar year
- **LCA/PERM**: Separated into H1B/ and PERM/ subdirectories, then by FY
- **USCIS**: Organized by form type (I-140, I-485, etc.)
- **Manifest**: Single JSON file tracking all downloads

## 📝 Manifest Format

The `downloads/_manifest.json` tracks all downloaded files:

```json
{
  "run_date": "2026-02-19T22:03:38.682725",
  "total_files": 160,
  "entries": [
    {
      "source_url": "https://www.dol.gov/.../LCA_Disclosure_Data_FY2026_Q1.xlsx",
      "local_path": "downloads/LCA/H1B/FY2026/LCA_Disclosure_Data_FY2026_Q1.xlsx",
      "downloaded_at": "2026-02-19T21:58:42.123456",
      "hash": "b81ef0197a395c8a2c91d7f42b8b9c7e",
      "status": "success"
    },
    ...
  ],
  "files_by_url": {
    "https://www.dol.gov/.../LCA_Disclosure_Data_FY2026_Q1.xlsx": {
      "local_path": "downloads/LCA/H1B/FY2026/LCA_Disclosure_Data_FY2026_Q1.xlsx",
      "downloaded_at": "2026-02-19T21:58:42.123456",
      "hash": "b81ef0197a395c8a2c91d7f42b8b9c7e"
    },
    ...
  }
}
```

**Manifest Fields:**
- `source_url` - Original download URL
- `local_path` - Path to downloaded file (relative to workspace)
- `downloaded_at` - ISO 8601 timestamp
- `hash` - MD5 hash of file contents
- `status` - Download status (success, error, skipped)
- `files_by_url` - Indexed dictionary for fast O(1) URL lookups

## ⏰ Scheduling (Optional)

Automate monthly runs to keep data up-to-date:

### macOS/Linux (cron)

Run monthly on the 1st at 2 AM:

```bash
crontab -e
```

Add:
```bash
0 2 1 * * cd /Users/youruser/fetch-immigration-data && /Users/youruser/fetch-immigration-data/.venv/bin/python fetch_latest.py sources.yaml >> /tmp/fetch_immigration.log 2>&1
```

### Windows (Task Scheduler)

1. Open **Task Scheduler**
2. Create **Basic Task**
3. Set trigger: **Monthly** (1st of month, 2:00 AM)
4. Action: **Start a program**
   - Program: `C:\path\to\fetch-immigration-data\.venv\Scripts\python.exe`
   - Arguments: `fetch_latest.py sources.yaml`
   - Start in: `C:\path\to\fetch-immigration-data`

## 🔧 Troubleshooting

### No files downloaded for a source

**Common causes:**
- Government website structure changed
- URL patterns updated
- New pagination or access restrictions

**Solutions:**
1. Check the source URL in browser
2. Verify files are still available
3. Update `sources.yaml` with new URLs or selectors
4. Check console output for specific error messages

### "Already have..." messages but files missing

**Cause:** Manifest entry exists but physical file was deleted.

**Solution:**
```bash
# Delete manifest to force fresh download
rm downloads/_manifest.json
python fetch_latest.py sources.yaml
```

### USCIS pagination issues

**Symptoms:** Only getting recent USCIS files, missing historical data.

**Cause:** Pagination parameters need adjustment.

**Solution:** Edit `sources.yaml` USCIS section:
```yaml
page_url: "https://www.uscis.gov/tools/reports-and-studies/..."
items_per_page: 100  # Increase if more files exist
```

### DOL website blocking requests

**Symptoms:** 403 errors for LCA/PERM downloads.

**Cause:** DOL has bot detection.

**Solution:** The script uses Macintosh User-Agent to bypass this. If still blocked:
- Add delays between requests (already implemented with retries)
- Check if DOL changed their bot detection

### Rate limiting / Timeouts

**Symptoms:** Connection timeouts or 429 errors.

**Solution:** The script includes:
- 60-second timeout per request
- 3 automatic retries with exponential backoff
- Delays between requests

If issues persist, reduce concurrent downloads in `fetch_latest.py`.

## 🛠️ Development

### Code Structure

**`fetch_latest.py`** (2475 lines) - Main orchestrator:
- **Lines 1-39**: Imports and HTTP utilities
- **Lines 40-124**: Manifest management (load, check, save)
- **Lines 125-2300**: 16 specialized handler methods:
  - `handle_visa_bulletin_multilevel()` - Multi-level page traversal
  - `handle_lca_disclosure_data()` - H-1B quarterly data
  - `handle_perm_disclosure_data()` - PERM quarterly data
  - `handle_uscis_employment_data()` - I-140/I-485 with pagination
  - `handle_scrape()` - Generic web scraping
  - `handle_direct_file()` - Direct downloads
  - And 10 more specialized handlers
- **Lines 2301-2475**: `main()` orchestration and routing

**`sources.yaml`** (324 lines) - Data source definitions:
- 20+ configured government data sources
- Custom handler mappings
- URL patterns and selectors
- Year ranges and file type preferences

**`requirements.txt`** - Three core dependencies:
- `requests==2.32.3` - HTTP with retry logic
- `beautifulsoup4==4.12.3` - HTML parsing
- `pyyaml==6.0.2` - YAML configuration

### Technical Architecture

**Handler Pattern:**
```python
def handle_<method_name>(source: Dict[str, Any], 
                          group_dir: Path,
                          manifest: Dict[str, Any] = None) -> int:
    """Process a data source and return count of new downloads."""
    
    # 1. Discover available files from source
    files = discover_files(source)
    
    # 2. Check against manifest
    for file_url, dest_path in files:
        if manifest and is_file_in_manifest(file_url, dest_path, manifest):
            continue  # Skip existing
    
    # 3. Download new files only
    download_file(file_url, dest_path)
    
    # 4. Update manifest
    update_manifest_entry(file_url, dest_path)
    
    return download_count
```

**Manifest System:**
- **O(1) lookups** via `files_by_url` dictionary index
- **Dual verification**: Checks manifest entry AND physical file
- **Atomic updates**: Incremental saves preserve existing data
- **File hashing**: MD5 hashes for integrity verification

### Adding a New Data Source

**1. Define in `sources.yaml`:**
```yaml
- name: "New Immigration Data"
  group: "NewGroup"
  method: "scrape"  # or direct_file, custom handler
  page_url: "https://example.gov/data"
  selector: "a[href$='.xlsx']"  # CSS selector for files
  pattern: "disclosure"  # Optional: filter by filename pattern
  filetype: "xlsx"
  notes: "Quarterly disclosure data"
```

**2. Use existing handler or create new one:**

For simple scraping, `method: "scrape"` works out of the box.

For custom logic, add handler in `fetch_latest.py`:
```python
def handle_new_source(source: Dict[str, Any], 
                      group_dir: Path,
                      manifest: Dict[str, Any] = None) -> int:
    """Custom handler for new data source."""
    page_url = source['page_url']
    resp = http_get(page_url)
    soup = BeautifulSoup(resp.content, 'html.parser')
    
    # Custom scraping logic here
    download_count = 0
    for link in soup.find_all('a', href=True):
        file_url = link['href']
        if manifest and is_file_in_manifest(file_url, dest_path, manifest):
            continue
        # Download and track
        download_file(file_url, dest_path)
        download_count += 1
    
    return download_count
```

**3. Route in `main()` function:**
```python
if method == 'new_source':
    count = handle_new_source(source, group_dir, manifest)
```

### Specialized Handlers Reference

| Handler | Purpose | Key Features |
|---------|---------|-------------|
| `visa_bulletin_multilevel` | Visa Bulletin PDFs | Year page → bulletin list → PDF download |
| `lca_disclosure_data` | H-1B LCA data | Quarterly Excel, FY2008-2026 |
| `perm_disclosure_data` | PERM certification | Quarterly Excel, FY2008-2026 |
| `uscis_employment_data` | USCIS forms | Pagination, 7 pages, topic filtering |
| `visa_statistics_scrape` | Monthly visa stats | Monthly PDFs, year-based organization |
| `annual_visa_reports` | Annual reports | Multi-level scraping, detailed PDFs |
| `niv_statistics` | Non-immigrant visas | Excel files with date extraction |
| `scrape` | Generic scraping | CSS selectors, pattern matching |
| `direct_file` | Direct downloads | Single file, no scraping needed |

### HTTP Configuration

**User-Agent**: Uses Macintosh Chrome to bypass bot detection:
```python
user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...'
```

**Retry Logic**:
- 3 attempts per request
- Exponential backoff (2s, 4s, 8s)
- 60-second timeout per request

**Error Handling**:
- Graceful degradation (continues on individual source failures)
- Detailed error logging
- Status tracking in manifest

## 📊 Data Statistics

Current collection as of February 2026:

| Category | File Count | Size (approx) | Years Covered |
|----------|------------|---------------|---------------|
| Visa Bulletin | 167 | ~350 MB | FY2011-2026 |
| Visa Statistics | 184 | ~920 MB | 2017-2025 |
| Visa Annual Reports | 273 | ~1.8 GB | FY2015-2024 |
| NIV Statistics | 32 | ~45 MB | 2021-2024 |
| LCA (H-1B) | 85 | ~850 MB | FY2008-2026 |
| PERM | 47 | ~280 MB | FY2008-2026 |
| USCIS Employment | 245 | ~620 MB | 1991-2026 |
| **Total** | **1,033+** | **~4.9 GB** | **1991-2026** |

## 🔑 Key Benefits

✅ **Complete Historical Archives** - No need to manually hunt down old reports  
✅ **Automated Updates** - Run monthly to stay current  
✅ **Efficient** - Only downloads new files  
✅ **Organized** - Clear directory structure by year and type  
✅ **Reliable** - Built-in retry logic and error handling  
✅ **Transparent** - Full manifest tracking with hashes  
✅ **Maintainable** - Simple YAML configuration  

## 🚦 Roadmap

- [x] Historical data collection (1991-2026)
- [x] Incremental download system
- [x] Manifest-based tracking
- [x] Year-based file organization
- [x] LCA/PERM separation (H1B vs PERM)
- [x] USCIS pagination support (7 pages, 474 files)
- [ ] ZIP export functionality
- [ ] Data analysis notebooks
- [ ] API wrapper for common queries
- [ ] Docker container for easy deployment
- [ ] GitHub Actions for automated monthly runs

## 📝 License

Public domain / CC0. Use freely for any purpose.

## 🤝 Contributing

This is a utility project for automated data collection. Feel free to:
- Fork and customize for your needs
- Submit issues for bugs or enhancement requests
- Share improvements via pull requests

## ⚠️ Disclaimer

This tool fetches **publicly available data** from U.S. government websites. 

**User Responsibilities:**
- Comply with terms of service for each source website
- Respect rate limits and server resources
- Provide proper attribution when using the data
- Verify data accuracy against official sources for critical decisions

**Not Responsible For:**
- Changes to source websites breaking the scraper
- Data accuracy, completeness, or timeliness
- Usage or misuse of downloaded data
- Storage costs or bandwidth usage

**Always verify critical information against official government sources.**

---

## 📧 Support

For issues or questions:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review `sources.yaml` configuration
3. Check console output for specific error messages
4. Open an issue with details about the problem

---

**Last Updated**: February 2026  
**Current Version**: 1.0.0  
**Python Version**: 3.12.3  
**Total Files Collected**: 1,033+
