# P1 Horizon — Project Guardrails

> **Horizon** is the data collection layer for NorthStar. These guardrails protect data integrity, manifest reliability, and downstream compatibility with P2 Meridian.
>
> **Read the program-wide Ten Commandments first**: `/Users/vrathod1/dev/NorthStar/northstar-docs/GUARDRAILS.md`

---

## P1 Commandments (Non-Negotiable)

### 1. The Manifest is Sacred

`downloads/_manifest.json` is the single source of truth for what has been downloaded. Every download must be recorded in the manifest with URL, file path, hash, status, and timestamp. Never manually add files to `downloads/` without updating the manifest.

**Why**: P2 Meridian relies on the manifest to know what data is available. An unrecorded file is invisible to the pipeline.

### 2. Never Re-Download What Already Exists

The manifest-based incremental system exists for a reason. Before downloading any file:
1. Check if the URL exists in `files_by_url` (O(1) lookup)
2. Check if the file exists on disk
3. Only download if both checks fail

Never bypass this with `--force` unless explicitly requested by the user.

**Why**: Government servers rate-limit. Re-downloading 3-5 GB wastes bandwidth, time, and risks being blocked.

### 3. Downloads Are Gitignored, Always

The `downloads/` directory (3-5 GB) must never be committed to git. Only code, configuration, and the manifest are version-controlled. The `.gitignore` must include `downloads/`.

**Why**: Git is not designed for multi-gigabyte binary files. The manifest + code can regenerate the downloads.

### 4. One Handler Per Source Pattern

Each government data source has its own handler function in `fetch_latest.py`. Handlers are specialized, not generalized. Don't try to create a "universal handler" that works for all sources.

**Why**: Government websites change formats, require different authentication, and have different pagination patterns. Specialized handlers are easier to debug and maintain than a generic one.

### 5. Update data-dictionary.md With Every Schema Change

`data-dictionary.md` is P2's contract for understanding P1 data. When adding a new source, changing a schema, or discovering new fields: update the data dictionary and commit it alongside the code change.

**Why**: P2 reads P1 data by convention. If the dictionary is stale, P2 builds incorrectly.

### 6. sources.yaml is the Configuration, Not Code

All data source metadata (URLs, groups, methods, file types, notes) lives in `sources.yaml`. Adding a new source means adding a YAML entry + writing a handler function. Don't hardcode URLs in handler functions.

**Why**: YAML configuration is readable, diffable, and auditable. Hardcoded URLs in Python are invisible to quick review.

### 7. Respect HTTP Etiquette

All HTTP requests must:
- Include a realistic User-Agent header
- Add jitter between requests (0.2-0.8s)
- Retry with exponential backoff (max 3 retries)
- Log clearly: what was found, what was skipped, what failed
- Never parallelize requests to the same government domain

**Why**: Government servers are not CDNs. Aggressive scraping gets IP-blocked and harms other researchers.

### 8. Atomic Manifest Saves

`save_manifest_incremental()` must be called after each successful download batch, not at the end of the entire run. This prevents losing progress if the script is interrupted mid-execution.

**Why**: A 2-hour fetch run that crashes at minute 119 should not lose 118 minutes of progress.

---

## Operational Guardrails

| # | Guardrail | Enforcement |
|---|-----------|-------------|
| O1 | Run `python fetch_latest.py sources.yaml` from the project root | README instructions |
| O2 | Check manifest integrity after every run: `python -c "from fetch_latest import load_manifest; ..."` | Post-run verification |
| O3 | Verify file counts after adding a new source: `find downloads/{GROUP} -type f \| wc -l` | Manual check |
| O4 | Commit manifest changes alongside code changes | Git workflow |
| O5 | Update PROGRESS.md after every successful fetch run | Documentation discipline |
| O6 | No Selenium usage unless source is Cloudflare-protected | Minimize browser automation |
| O7 | PyPDF2 for text extraction, pdfplumber for table extraction | Library conventions |

## Data Quality Guardrails

| # | Guardrail | Enforcement |
|---|-----------|-------------|
| Q1 | Every downloaded file gets SHA256 hash in manifest | `hash_file()` in handler |
| Q2 | Duplicate URL detection before download | `is_file_in_manifest()` dual check |
| Q3 | File size validation (reject zero-byte downloads) | Handler logic |
| Q4 | Date extraction from filenames/URLs for temporal ordering | `extract_date_from_text()` |
| Q5 | Group directory structure: `downloads/{SOURCE}/{FY}/` | Convention |

## Cross-Project Impact

When P1 adds a new data source, the following downstream actions are required:

1. **P1**: Add source in `sources.yaml` + write handler + update `data-dictionary.md` + update `FOLDER_STRUCTURE.md`
2. **P2**: Add parser in `src/curate/` + add build script in `scripts/` + add test + update `configs/schemas.yml`
3. **P3**: Add type in `src/types/p2-artifacts.ts` + add loader in `src/lib/data/` + update sync script (if needed)

This chain must be documented in commit messages when a cross-project change is initiated.

---

## Cross-References

- **Program-wide guardrails (Ten Commandments)**: `/Users/vrathod1/dev/NorthStar/northstar-docs/GUARDRAILS.md`
- **P2 Meridian guardrails**: `/Users/vrathod1/dev/NorthStar/immigration-model-builder/.github/GUARDRAILS.md`
- **P3 Compass guardrails**: `/Users/vrathod1/dev/NorthStar/immigration-insights-app/.github/GUARDRAILS.md`
- **Data contract**: `data-dictionary.md` (this repo)
- **Architecture**: `ARCHITECTURE.md` (this repo)
