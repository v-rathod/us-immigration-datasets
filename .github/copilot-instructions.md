# GitHub Copilot Instructions - Immigration Data Repository

## Project Overview
**Repository:** US Immigration Datasets (fetch-immigration-data)  
**Location:** `/Users/vrathod1/dev/NorthStar/fetch-immigration-data/`  
**GitHub:** https://github.com/v-rathod/us-immigration-datasets  
**Purpose:** Automated collection & management of 1,230+ US immigration datasets (3-5 GB)

## ⚠️ CRITICAL ACTIVE RULES

### 1. AUTO-COMMIT EVERYTHING ✅
**Always commit ALL changes immediately with descriptive messages after any modification to:**
- Code (fetch_latest.py, handlers)
- Docs (README, FOLDER_STRUCTURE.md, data-dictionary.md)
- Config (sources.yaml, requirements.txt)
- Any tracked files

**Format:** `git add [files] && git commit -m "Summary\n\n- Details..." && git push`

### 2. AUTO-UPDATE DATA_DICTIONARY.md ✅
**Automatically update data-dictionary.md when triggered by:**
- "new data added"
- "update dictionary"
- "refresh schema notes"
- "reflect latest downloads"

**Actions:**
- Scan downloads/ for changes
- Add/update dataset sections
- Generate field inventory (Appendix A)
- Update dates and commit

## Project Status (Feb 25, 2026)
- ✅ 15/15 active data sources operational
- ✅ 1,226 files across 207 folders
- ✅ 5 new sources added (DOL Record Layouts, BLS OEWS, H-1B Employer Hub, DOS Numerical Limits, Codebooks, DOS Waiting List)
- ✅ Incremental downloads working (manifest-based)

## Key Files
- **fetch_latest.py** (3,309 lines) - Main downloader with 15 source handlers
- **sources.yaml** - 15 data source configurations
- **data-dictionary.md** - Functional contract for downstream projects (14 datasets)
- **FOLDER_STRUCTURE.md** - Current repo state (1,226 files, 207 folders)
- **.ai-instructions.md** - Detailed context for AI agents
- **downloads/** - 3-5 GB data (gitignored)

## Technical Context

### Dependencies
```
requests==2.32.3
beautifulsoup4==4.12.3
pyyaml==6.0.2
selenium==4.27.1          # Cloudflare bypass for USCIS
webdriver-manager==4.0.2
PyPDF2==3.0.1             # DOS PDF parsing
```

### Path Convention
**Always use:** `/Users/vrathod1/dev/NorthStar/fetch-immigration-data/`  
**Never use:** `/Users/vrathod1/dev/fetch-immigration-data/` (old location)

### Virtual Environment
```bash
cd /Users/vrathod1/dev/NorthStar/fetch-immigration-data
source .venv/bin/activate
```

## Important Conventions

### Incremental Downloads
- Check manifest before download: `is_file_in_manifest(url, path, manifest)`
- Skip if exists: "Already have {file}, skipping"
- Only download delta/new data

### File Organization
- Raw: `downloads/{SOURCE}/{YEAR}/` or `downloads/{SOURCE}/raw/{YEAR}/`
- Parsed: `downloads/{SOURCE}/parsed/{YEAR}/`
- Manifest: `downloads/_manifest.json`

### DO NOT
- ❌ Modify existing code without explicit request
- ❌ Re-download existing data
- ❌ Use absolute paths (always relative)
- ❌ Commit .venv/ or downloads/ (gitignored)

## Data Sources (15 active)

### Original 10
1. Visa Bulletin (monthly PDFs, 2011-2026)
2. Visa Statistics (monthly IV, 2017-2025)
3. Visa Annual Reports (FY2015-2024)
4. USCIS Immigration (I-140/I-485/I-765)
5. LCA (H-1B, FY2008-2026)
6. PERM (FY2008-2026)
7. NIV Statistics
8. BLS, ACS, WARN

### New 5 (Feb 2026)
9. ✅ DOL Record Layouts
10. ✅ BLS OEWS Wages
11. ✅ USCIS H-1B Employer Hub
12. ✅ DOS Numerical Limits
13. ✅ Codebooks (SOC, country, EB)
14. ✅ DOS Waiting List (PDF + PyPDF2)

### Removed
- ❌ USCIS Processing Times (Cloudflare-protected SPA, not extractable)
- ❌ TRAC Immigration Data (requires paid subscription)

## Special Handlers

### DOS Waiting List (lines 2523-2770)
- Multi-pattern URL testing
- PyPDF2 parsing: fiscal_year, category, country, count
- Yearly reports, 2023 confirmed working

## Quick Commands
```bash
# Run downloader (incremental)
python fetch_latest.py sources.yaml

# Check manifest
python -c "from fetch_latest import load_manifest; from pathlib import Path; m = load_manifest(Path('downloads')); print(f'{len(m.get(\"files_by_url\", {}))} files')"

# Status
git status
```

## User Preferences
- Brief responses (1-3 sentences for simple questions)
- No emojis unless requested
- Direct action, minimal framing
- Use markdown file links: [file.ts](file.ts#L10)

## Related Projects
- **Project 2:** `/Users/vrathod1/dev/NorthStar/immigration-model-builder/` (ML models)
- **Project 3:** Public app (planned)

---

**For detailed context:** See `.ai-instructions.md` (265 lines)  
**For data schemas:** See `data-dictionary.md` (15+ datasets documented)  
**For current state:** See `FOLDER_STRUCTURE.md` (1,230 files mapped)
