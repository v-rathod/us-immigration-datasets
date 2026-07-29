# Horizon (P1) Progress Tracker

> **PURPOSE**: Chronological record of data collection runs, new sources, and pipeline changes.
> **UPDATE**: Add entries after significant data refreshes or source additions.

---

## 2026-07-29 - Milestone 2: Comprehensive Q2/Q3 Data Refresh

### Why
Three-month data gap since April 2026. Multiple high-priority sources now have fresh data published:
1. **LCA & PERM** - FY2026 Q2 disclosure data released (July 2026)
2. **USCIS Employment-Based** - FY2026 Q1 data + 4 monthly EB inventories (Feb-Apr 2026)
3. **DHS Yearbook** - FY2024 complete yearbook released (June 2026)
4. **DOL Record Layouts** - FY2026 record layouts for LCA/PERM published

### New Files Downloaded

| Group | Count | Files/Details |
|-------|-------|---------------|
| **LCA** | 6 | FY2026 Q2 Disclosure Data + Appendix A + Worksites + all record layouts |
| **PERM** | 3 | FY2026 Q2 Disclosure Data + Record Layout + Selected Statistics |
| **USCIS Immigration** | 24 | FY2026 Q1 (10 forms) + FY2025 Q4 (8 forms) + EB Inventory (Feb-Apr 2026, 4 files) |
| **DHS Yearbook** | 4 | FY2024 Lawful Permanent Residents, Naturalizations, Nonimmigrants, Tables 8-11 |
| **DOL Record Layouts** | 4 | FY2026 layouts for PERM (1) + LCA (3) |
| **WARN (CA)** | 1 | Current California WARN report |
| **Other** | 3 | BLS OEWS, Codebooks, ACS (already present) |

**Total New Files: ~41 files** (65 files transferred to manifest in batch processing)

### Inventory After Update

| Source | Coverage | Status |
|--------|----------|--------|
| **LCA** | FY2008-2026 Q2 | ✅ UP-TO-DATE (Q2 just published) |
| **PERM** | FY2008-2026 Q2 | ✅ UP-TO-DATE (Q2 just published) |
| **USCIS EB** | 1991-2026 Q1 + Monthly EB Inv | ✅ UP-TO-DATE |
| **DHS Yearbook** | FY2024 | ✅ UP-TO-DATE (annual) |
| **DOL Record Layouts** | Through FY2026 | ✅ UP-TO-DATE |
| **Visa Bulletin** | May 2026 | ⏳ STALE (Jun-Jul 2026 expected) |
| **Visa Statistics** | Sep 2025 | ⏳ STALE (Oct 2025-Jul 2026 expected) |
| **BLS CES** | Mar 2026 | ⏳ STALE (Jul 2026 expected) |
| **ACS** | 2025 (stub) | ⏳ MISSING (Sep 2026 expected) |

### Downstream Impact for P2/P3
- **`fact_lca_applications`** - 6 new quarters of H-1B data (FY2025 Q4 onward)
- **`fact_perm_applications`** - 6 new quarters of PERM data (FY2025 Q4 onward)
- **`fact_uscis_approvals`** - 10+ new EB form types for FY2026 Q1
- **`fact_eb_inventory`** - 4 new monthly snapshots (Feb, Mar, Apr 2026)
- **`fact_dhs_lpr`**, **`fact_dhs_naturalization`**, **`fact_dhs_nonimmigrant`** - FY2024 complete data
- All downstream tables depending on LCA/PERM (wage metrics, PD trends, demand forecasts) will refresh

### Archive Generated
- **File:** `exports/latest_datasets_2026-07-29.zip`
- **Size:** ~468 files bundled
- **Purpose:** Full backup of all downloaded data for P2/P3 consumption

---

## 2026-04-19 - Data Freshness Audit + Waiting List Fix + New Data Fetch

### Why
Comprehensive audit of all P1 data sources against P2 (Meridian) requirements revealed:
1. **DOS Waiting List** had only FY2023 data (125 rows in P2). FY2020-2024 data exists as Table XIII in Annual Reports but P1 was not fetching it.
2. **Visa Statistics** was missing Sep 2025 (FY2025 Q4 final month) - now available on travel.state.gov.
3. **USCIS employment data** had FY2025 Q4 and Jan 2026 EB inventory newly published but not fetched.
4. **BLS CES** was 5+ weeks stale (last: Mar 11, 2026).

### Code Changes
- **`fetch_latest.py`**: Rewrote `handle_dos_waiting_list()` with 3-tier strategy:
  1. Try standalone `WaitingListItem_YYYY_vF.pdf` (works for 2023+)
  2. Copy Table XIII from already-downloaded Annual Reports (FY2020-2024)
  3. Download Table XIII directly from DOS Annual Report URLs
  - Changed `start_year` from 2015 to 2020 (Table XIII not published pre-FY2020)
- **`sources.yaml`**: Updated DOS_Waiting_List notes and start_year to reflect reality

### New Files Downloaded/Copied

| Source | File | Method |
|--------|------|--------|
| DOS Waiting List | `DOS_Waiting_List/2020/waiting_list_2020.pdf` | Copied from Annual Report FY2020 Table XIII |
| DOS Waiting List | `DOS_Waiting_List/2021/waiting_list_2021.pdf` | Copied from Annual Report FY2021 Table XIII |
| DOS Waiting List | `DOS_Waiting_List/2022/waiting_list_2022.pdf` | Copied from Annual Report FY2022 Table XIII |
| DOS Waiting List | `DOS_Waiting_List/2024/waiting_list_2024.pdf` | Copied from Annual Report FY2024 Table XIII |
| Visa Statistics | `Visa_Statistics/2025/SEPTEMBER 2025 - IV Issuances by FSC...pdf` | Downloaded from travel.state.gov |
| Visa Statistics | `Visa_Statistics/2025/SEPTEMBER 2025 - IV Issuances by Post...pdf` | Downloaded from travel.state.gov |
| USCIS Immigration | `USCIS_IMMIGRATION/employment_based/2025/eb_i140_i360_i526_performance_data_fy2025_q4_v1.xlsx` | Downloaded from uscis.gov |
| USCIS Immigration | `USCIS_IMMIGRATION/employment_based/2025/i485_performance_data_fy2025_q4_v1.xlsx` | Downloaded from uscis.gov |
| USCIS Immigration | `USCIS_IMMIGRATION/employment_based/2025/i140_fy2025_q4_v1.xlsx` | Downloaded from uscis.gov |
| USCIS Immigration | `USCIS_IMMIGRATION/employment_based/2025/i140_rec_by_class_country_fy2025_q4_v1.xlsx` | Downloaded from uscis.gov |
| USCIS Immigration | `USCIS_IMMIGRATION/employment_based/2025/i485_lrif_performance_data_fy2025_q4_v1.xlsx` | Downloaded from uscis.gov |
| USCIS Immigration | `USCIS_IMMIGRATION/employment_based/2025/eb_inventory_january_2026.xlsx` | Downloaded from uscis.gov |
| BLS CES | `BLS/bls_ces_20260419.json` | BLS API (latest: 2026-M03) |

### Inventory After Update

| Source | Files | Coverage | Status |
|--------|-------|----------|--------|
| PERM | 47 | FY2008-FY2026 Q1 | UP-TO-DATE |
| LCA | 217 | FY2008-FY2026 Q1 | UP-TO-DATE |
| BLS OEWS | 3 | 2023-2024 | UP-TO-DATE (annual) |
| Visa Bulletin | 170 | FY2011-May 2026 | UP-TO-DATE |
| Visa Statistics | 208 | Jan 2017-Sep 2025 | UPDATED (+2 files) |
| NIV Statistics | 32 | FY2016-FY2024 | UP-TO-DATE (annual) |
| Visa Annual Reports | 274 | 2015-2024 (FY2025 not published) | UP-TO-DATE |
| USCIS Immigration | 251 | 1991-FY2025 Q4 + Jan 2026 | UPDATED (+6 files) |
| H1B Employer Hub | 15 | FY2010-FY2023 | DISCONTINUED |
| DHS Yearbook | 1 | FY2024 | UP-TO-DATE (annual) |
| DOS Waiting List | 10 | FY2020-FY2023 | UPDATED (+4 years) |
| DOS Numerical Limits | 1 | FY2025 only | STALE (no historical PDFs on DOS site) |
| BLS CES | 8 | Through Mar 2026 | UPDATED |
| ACS | 1 | 2025 (stub/error) | MISSING (expected ~Sep 2026) |
| WARN | 2 | CA + TX only | SPARSE |

### What Is Still Unavailable (Confirmed)
- **DOS Waiting List pre-FY2020**: Table XIII was not published before FY2020. No public source exists.
- **DOS Waiting List FY2025+**: FY2025 Annual Report not yet published. No standalone PDF exists.
- **DOS Numerical Limits pre-FY2025**: Only FY2025 PDF exists at the known URL pattern. Historical limits not available via direct download.
- **Visa Statistics Oct-Dec 2025**: Not yet published on travel.state.gov (typically 2-4 month lag).
- **ACS wage data**: Census 2025 ACS1 not published until ~Sep 2026.
- **USCIS Processing Times**: Vue.js SPA, no static data available.
- **Spillover data**: Not a separate data source. Calculable from dim_visa_ceiling + fact_visa_issuance in P2.

### Downstream Impact
- P2 should rebuild:
  - `fact_waiting_list` (will go from 125 rows to ~500+ rows with FY2020-2024 data)
  - `fact_visa_applications` and `fact_iv_post` (added Sep 2025)
  - `fact_uscis_approvals` (FY2025 Q4 data)
  - `fact_bls_ces` (new March 2026 snapshot)
  - `visa_demand_metrics` (downstream of visa stats update)
  - `backlog_estimates` (waiting list data can now anchor queue depth)

---

## 2026-03-10 - Milestone 1: Full Pipeline Data Refresh

### What Was Done
Ran `python3 fetch_latest.py sources.yaml` against all 15 configured data sources. Incremental manifest-based download found 9 new/updated files.

### New Files Downloaded
| Source | File | Notes |
|--------|------|-------|
| BLS CES | `BLS/ces_20260310.json` | Latest employment situation snapshot |
| ACS | `ACS/acs1_2025_nativity.json` | 2025 American Community Survey nativity demographics |
| Visa Statistics (DOS) | `Visa_Statistics/2025/iv_jun25.pdf` | June 2025 immigrant visa issuance |
| Visa Statistics (DOS) | `Visa_Statistics/2025/iv_jul25.pdf` | July 2025 immigrant visa issuance |
| Visa Statistics (DOS) | `Visa_Statistics/2025/iv_aug25.pdf` | August 2025 immigrant visa issuance |
| Visa Statistics (DOS) | `Visa_Statistics/2025/niv_jun25.pdf` | June 2025 non-immigrant visa issuance |
| Visa Statistics (DOS) | `Visa_Statistics/2025/niv_jul25.pdf` | July 2025 non-immigrant visa issuance |
| Visa Statistics (DOS) | `Visa_Statistics/2025/niv_aug25.pdf` | August 2025 non-immigrant visa issuance |
| WARN (CA) | `WARN/CA/warn_ca.csv` | Latest California WARN report |

### Manifest Summary
| Metric | Value |
|--------|-------|
| Total entries | 434 |
| Successful | 402 |
| No files found | 30 |
| Skipped | 2 |
| Errors | 0 |

### Downstream Impact
- P2 Meridian full rebuild triggered (Stages 1–4)
- P3 Compass full sync triggered (94K+ employer shards refreshed)

---
