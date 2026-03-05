# Horizon (P1) — Technical Architecture

> **Project:** fetch-immigration-data  
> **Role:** Data collection layer — automated download of U.S. immigration datasets  
> **Last Updated:** March 5, 2026

---

## Prerequisite Reading

Before working on this project, read these documents in order:

1. **`/Users/vrathod1/dev/NorthStar/NORTHSTAR_VISION.md`** — Program vision, 3-project architecture, guardrails
2. **`.github/copilot-instructions.md`** — P1-specific context: data sources, conventions, commands
3. **`.ai-instructions.md`** — Detailed AI agent instructions (263 lines)
4. **`data-dictionary.md`** — Functional data contract for downstream P2

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                    GOVERNMENT DATA SOURCES (15 active)               │
│                                                                      │
│  DOL           DOS              USCIS            BLS       DHS      │
│  ┌─────┐      ┌──────────┐     ┌──────────┐    ┌─────┐  ┌─────┐   │
│  │PERM │      │Visa      │     │I-140/485/│    │OEWS │  │Admis│   │
│  │LCA  │      │Bulletin  │     │765 forms │    │CES  │  │sions│   │
│  │Rec. │      │Issuances │     │H-1B Hub  │    │     │  │     │   │
│  │Lyout│      │Wait List │     │          │    │     │  │     │   │
│  └──┬──┘      └────┬─────┘     └────┬─────┘    └──┬──┘  └──┬──┘   │
│     │              │                │              │        │       │
└─────┼──────────────┼────────────────┼──────────────┼────────┼───────┘
      │              │                │              │        │
      ▼              ▼                ▼              ▼        ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     fetch_latest.py (3,309 lines)                    │
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐   │
│  │ sources.yaml │───▶│ 15 Source    │───▶│ Incremental Download │   │
│  │ (configs)    │    │ Handlers     │    │ Engine               │   │
│  └──────────────┘    └──────────────┘    │                      │   │
│                                          │ • Check manifest     │   │
│                                          │ • Skip if exists     │   │
│                                          │ • Download delta     │   │
│                                          │ • Compute hash       │   │
│                                          │ • Update manifest    │   │
│                                          └──────────┬───────────┘   │
│                                                     │               │
│                                                     ▼               │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    downloads/ (~3-5 GB)                       │   │
│  │                                                              │   │
│  │  ├── visa_bulletin/          (monthly PDFs, 2011-2026)       │   │
│  │  ├── PERM/                   (Excel, FY2008-2026)            │   │
│  │  ├── LCA/                    (Excel/CSV, FY2008-2026)        │   │
│  │  ├── USCIS_Immigration/      (I-140/485/765, 1991-2026)      │   │
│  │  ├── BLS_OEWS/               (wage percentiles, 2023-2024)   │   │
│  │  ├── Visa_Statistics/        (monthly IV issuances)          │   │
│  │  ├── Visa_Annual_Reports/    (FY2015-2024)                   │   │
│  │  ├── DOS_Waiting_List/       (backlog PDFs)                  │   │
│  │  ├── codebooks/              (SOC, country, EB categories)   │   │
│  │  ├── WARN_Layoffs/           (state WARN notices)            │   │
│  │  └── _manifest.json          (URL+path+hash tracking)        │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                          │                          │
└──────────────────────────────────────────┼──────────────────────────┘
                                           │
                              P2 Meridian reads directly
                              (never copies, never modifies)
                                           │
                                           ▼
                              immigration-model-builder/
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Single Python file (3,309 lines) | All 15 handlers share common utilities; monolith avoids import complexity |
| Manifest-based incremental downloads | Only downloads new/changed files; saves bandwidth and time |
| `downloads/` is gitignored | 3-5 GB of data files; too large for version control |
| Selenium for Cloudflare bypass | USCIS website uses Cloudflare protection; headless Chrome bypasses it |
| PyPDF2 for DOS PDFs | Lightweight PDF parsing for Visa Bulletin and Waiting List documents |
| No virtual env activated by default | System Python 3.12 with pip packages; `.venv/` available if needed |

---

## Data Source Inventory

| # | Source | Handler | Files | Format | Years |
|---|--------|---------|-------|--------|-------|
| 1 | Visa Bulletin | `fetch_visa_bulletin()` | ~180 | PDF | 2011-2026 |
| 2 | Visa Statistics | `fetch_visa_statistics()` | ~100 | CSV | 2017-2025 |
| 3 | Visa Annual Reports | `fetch_visa_annual()` | ~40 | CSV | FY2015-2024 |
| 4 | USCIS Immigration | `fetch_uscis()` | ~50 | Excel/CSV | 1991-2026 |
| 5 | LCA (H-1B) | `fetch_lca()` | ~80 | Excel/CSV | FY2008-2026 |
| 6 | PERM | `fetch_perm()` | ~40 | Excel | FY2008-2026 |
| 7 | NIV Statistics | `fetch_niv()` | ~30 | CSV | Various |
| 8 | BLS OEWS | `fetch_bls_oews()` | ~20 | Excel | 2023-2024 |
| 9 | BLS CES | `fetch_bls_ces()` | ~10 | CSV | Various |
| 10 | ACS (Census) | `fetch_acs()` | ~5 | CSV | 2022-2024 |
| 11 | WARN Layoffs | `fetch_warn()` | ~100 | CSV/HTML | 2020-2026 |
| 12 | DOL Record Layouts | `fetch_record_layouts()` | ~30 | PDF | FY2011+ |
| 13 | H-1B Employer Hub | `fetch_h1b_hub()` | ~15 | Excel | FY2010-2023 |
| 14 | DOS Numerical Limits | `fetch_dos_limits()` | ~5 | CSV | FY2025 |
| 15 | Codebooks | `fetch_codebooks()` | ~10 | CSV | Various |

**Removed sources:**
- USCIS Processing Times (Cloudflare-protected SPA, not extractable)
- TRAC Immigration Data (requires paid subscription)

---

## Extension Points

To add a new data source:
1. Add configuration entry to `sources.yaml`
2. Add handler function to `fetch_latest.py` following existing patterns
3. Update `data-dictionary.md` with schema, fields, and notes
4. Update `FOLDER_STRUCTURE.md` with new directory
5. Run the handler and verify downloads land in `downloads/`
6. Notify P2 team to add corresponding builder script

---

## Commands

```bash
# Run incremental download (all sources)
python fetch_latest.py sources.yaml

# Check what's been downloaded
python -c "from fetch_latest import load_manifest; from pathlib import Path; \
  m = load_manifest(Path('downloads')); \
  print(f'{len(m.get(\"files_by_url\", {}))} files tracked')"

# Git status
git status && git log --oneline -5
```

---

## Guardrails

1. **Never modify downloaded files** — P1 downloads are read-only for P2
2. **Always use manifest** — Check before downloading to avoid duplicates
3. **Never commit downloads/** — Data files are gitignored
4. **Handle failures gracefully** — 404s and timeouts should log warnings, not crash
5. **Maintain data-dictionary.md** — This is the functional contract for P2
