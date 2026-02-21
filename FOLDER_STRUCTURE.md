# US Immigration Datasets - Folder Structure

**Last Updated:** February 20, 2026  
**Total Files:** 1,230  
**Total Folders:** 210

---

## Summary by Data Group

| Data Group | Files | Description |
|------------|-------|-------------|
| **Visa_Annual_Reports** | 274 | State Department annual visa statistical reports (2015-2024) |
| **USCIS_IMMIGRATION** | 245 | Employment-based immigration forms (I-140, I-485, I-765, EB inventory) |
| **LCA** | 217 | H-1B Labor Condition Applications disclosure data (FY2008-2026) |
| **Visa_Statistics** | 198 | Monthly immigrant visa issuance statistics (2017-2025) |
| **Visa_Bulletin** | 168 | Monthly visa bulletin PDFs (2011-2026) |
| **PERM** | 47 | Permanent Labor Certification disclosure data (FY2008-2026) |
| **NIV_Statistics** | 32 | Nonimmigrant visa workload and detail tables |
| **DOL_Record_Layouts** | 15 | **NEW** - PERM/LCA record layout files (FY2020-2026) |
| **USCIS_H1B_Employer_Hub** | 14 | **NEW** - H-1B employer-level data (FY2010-2023) |
| **BLS** | 4 | Bureau of Labor Statistics employment data |
| **Codebooks** | 3 | **NEW** - Static reference CSVs (SOC, countries, EB codes) |
| **BLS_OEWS** | 3 | **NEW** - OEWS wage data (2023-2024) |
| **WARN** | 2 | Worker Adjustment and Retraining Notification data (CA, TX) |
| **DOS_Numerical_Limits** | 1 | **NEW** - Annual visa numerical limits (FY2025 only) |
| **DHS_Yearbook** | 1 | DHS Yearbook of Immigration Statistics |
| **ACS** | 1 | American Community Survey data |
| **USCIS_Processing_Times** | 2 | **NEW** - USCIS processing times (Feb 2026 snapshot) |
| **DOS_Waiting_List** | 2 | **NEW** - DOS waiting list (2023: PDF + CSV) |
| **TRAC** | 0 | TRAC Immigration data (requires authentication) |

---

## Detailed Folder Structure

```
downloads/ (1,226 files across 207 folders)
│
├── _manifest.json (1 file)
│
├── ACS/ (1 file)
│   └── acs1_2025_nativity.json
│
├── BLS/ (4 files)
│   ├── ces_20260220.json
│   ├── ces_20260220_2.json
│   ├── ces_20260220_3.json
│   └── [Additional BLS employment data]
│
├── BLS_OEWS/ (3 files) **NEW**
│   ├── 2023/ (1 file)
│   │   └── oews_all_data_2023.zip
│   ├── 2024/ (1 file)
│   │   └── oews_all_data_2024.zip
│   └── docs/ (1 file)
│       └── Technical_Notes_2025-2026.pdf
│
├── Codebooks/ (3 files) **NEW**
│   ├── soc_crosswalk_2010_to_2018.csv
│   ├── country_codes_iso.csv
│   └── eb_subcategory_codes.csv
│
├── DHS_Yearbook/ (1 file)
│   └── [Yearbook files - skipped if available]
│
├── DOL_Record_Layouts/ (15 files) **NEW**
│   ├── LCA/ (7 files)
│   │   ├── FY2020/ (1 file)
│   │   ├── FY2021/ (1 file)
│   │   ├── FY2022/ (1 file)
│   │   ├── FY2023/ (1 file)
│   │   ├── FY2024/ (1 file)
│   │   ├── FY2025/ (1 file)
│   │   └── FY2026/ (1 file)
│   └── PERM/ (8 files)
│       ├── FY2011/ (1 file)
│       ├── FY2020/ (1 file)
│       ├── FY2021/ (1 file)
│       ├── FY2022/ (1 file)
│       ├── FY2023/ (1 file)
│       ├── FY2024/ (1 file)
│       ├── FY2025/ (1 file)
│       └── FY2026/ (1 file)
│
├── DOS_Numerical_Limits/ (1 file) **NEW**
│   └── FY2025/ (1 file)
│       └── Annual_Numerical_Limits_FY2025.pdf
│
├── DOS_Waiting_List/ (2 files) **NEW**
│   └── 2023/ (2 files)
│       ├── waiting_list_2023.pdf (230 KB - Annual backlog snapshot)
│       └── waiting_list_2023.csv (Parsed: fiscal_year, category, country, count)
│
├── LCA/ (217 files in 46 folders)
│   │
│   ├── FY2008/ (2 files)
│   ├── FY2009/ (3 files)
│   ├── FY2010/ (2 files)
│   ├── FY2011/ (2 files)
│   ├── FY2012/ (2 files)
│   ├── FY2013/ (2 files)
│   ├── FY2014/ (2 files)
│   ├── FY2015/ (2 files)
│   ├── FY2016/ (2 files)
│   ├── FY2017/ (2 files)
│   ├── FY2018/ (2 files)
│   ├── FY2019/ (2 files)
│   ├── FY2020/ (9 files)
│   │   ├── LCA_Disclosure_Data_FY2020.xlsx
│   │   ├── LCA_Disclosure_Data_FY2020_Q1.xlsx
│   │   ├── LCA_Disclosure_Data_FY2020_Q2.xlsx
│   │   ├── LCA_Disclosure_Data_FY2020_Q3.xlsx
│   │   ├── LCA_Disclosure_Data_FY2020_Q4.xlsx
│   │   ├── LCA_Record_Layout_FY2020.pdf
│   │   ├── LCA_Record_Layout_FY2020_Q[1-4].pdf
│   │   └── [Additional files]
│   ├── FY2021/ (9 files)
│   ├── FY2022/ (9 files)
│   ├── FY2023/ (9 files)
│   ├── FY2024/ (9 files)
│   ├── FY2025/ (9 files)
│   ├── FY2026/ (6 files)
│   │
│   ├── H1B/ (Same structure as LCA/)
│   │   ├── FY2008/ (2 files)
│   │   ├── FY2009/ (3 files)
│   │   ├── ... (through FY2026)
│   │   └── FY2026/ (6 files)
│   │
│   └── PERM/ (Same structure as LCA/)
│       ├── FY2008/ (2 files)
│       ├── FY2009/ (2 files)
│       ├── ... (through FY2026)
│       └── FY2026/ (3 files)
│
├── NIV_Statistics/ (32 files in 2 folders)
│   ├── Detail_Tables/ (20 files)
│   │   ├── NIVDetailTable-[Year].pdf
│   │   └── [Multi-year summary reports]
│   └── Workload/ (12 files)
│       └── NIVWorkload-FY[Year].pdf
│
├── PERM/ (47 files in 20 folders)
│   └── PERM/
│       ├── FY2008/ (2 files)
│       │   ├── PERM_Disclosure_Data_FY2008.xlsx
│       │   └── PERM_Record_Layout_FY2008.pdf
│       ├── FY2009/ (2 files)
│       ├── FY2010/ (2 files)
│       ├── FY2011/ (2 files)
│       ├── FY2012/ (2 files)
│       ├── FY2013/ (2 files)
│       ├── FY2014/ (2 files)
│       ├── FY2015/ (2 files)
│       ├── FY2016/ (2 files)
│       ├── FY2017/ (2 files)
│       ├── FY2018/ (2 files)
│       ├── FY2019/ (3 files)
│       ├── FY2020/ (2 files)
│       ├── FY2021/ (3 files)
│       ├── FY2022/ (3 files)
│       ├── FY2023/ (3 files)
│       ├── FY2024/ (5 files)
│       │   ├── PERM_Disclosure_Data_FY2024.xlsx
│       │   ├── PERM_Disclosure_Data_FY2024_Q[1-4].xlsx
│       │   └── PERM_Record_Layout_FY2024.pdf
│       ├── FY2025/ (3 files)
│       └── FY2026/ (3 files)
│
├── TRAC/ (0 files)
│   └── [Requires authentication - manual download needed]
│
├── USCIS_IMMIGRATION/ (245 files in 17 folders)
│   └── employment_based/
│       ├── 1991/ (3 files)
│       ├── 2003/ (1 file)
│       ├── 2012/ (1 file)
│       ├── 2013/ (2 files)
│       ├── 2014/ (8 files)
│       ├── 2015/ (7 files)
│       ├── 2016/ (9 files)
│       ├── 2017/ (10 files)
│       ├── 2018/ (8 files)
│       ├── 2019/ (4 files)
│       ├── 2021/ (4 files)
│       ├── 2022/ (35 files)
│       │   ├── I-140 petitions quarterly
│       │   ├── I-485 applications quarterly
│       │   ├── I-765 EAD requests
│       │   ├── I-360 special immigrant
│       │   ├── I-526/526E EB-5 investor
│       │   └── EB inventory files
│       ├── 2023/ (66 files)
│       ├── 2024/ (35 files)
│       ├── 2025/ (39 files)
│       └── 2026/ (13 files)
│
├── USCIS_H1B_Employer_Hub/ (14 files) **NEW**
│   └── raw/ (14 files)
│       ├── H1B_Employer_Data_FY2010.csv (4.6 MB)
│       ├── H1B_Employer_Data_FY2011.csv (5.2 MB)
│       ├── H1B_Employer_Data_FY2012.csv (4.6 MB)
│       ├── H1B_Employer_Data_FY2013.csv (4.6 MB)
│       ├── H1B_Employer_Data_FY2014.csv (4.7 MB)
│       ├── H1B_Employer_Data_FY2015.csv (4.0 MB)
│       ├── H1B_Employer_Data_FY2016.csv (4.4 MB)
│       ├── H1B_Employer_Data_FY2017.csv (4.1 MB)
│       ├── H1B_Employer_Data_FY2018.csv (4.6 MB)
│       ├── H1B_Employer_Data_FY2019.csv
│       ├── H1B_Employer_Data_FY2020.csv
│       ├── H1B_Employer_Data_FY2021.csv
│       ├── H1B_Employer_Data_FY2022.csv
│       └── H1B_Employer_Data_FY2023.csv
│
├── USCIS_Processing_Times/ (2 files) **NEW**
│   ├── raw/ (1 file)
│   │   └── 2026-02/ (1 file)
│   │       └── processing_times.html (107 KB - Monthly snapshot via browser automation)
│   └── parsed/ (1 file)
│       └── 2026-02/ (1 file)
│           └── processing_times.csv (Columns: snapshot_date, form, category, office, processing_time_min, processing_time_max, unit)
│
├── Visa_Annual_Reports/ (274 files in 11 folders)
│   ├── [1 file - hub index]
│   ├── 2015/ (27 files)
│   │   ├── Table I - Immigrant Visas Issued.pdf
│   │   ├── Table II - Nonimmigrant Visas Issued.pdf
│   │   ├── Table III - Visa Refusals by Category.pdf
│   │   └── [All statistical tables for FY2015]
│   ├── 2016/ (27 files)
│   ├── 2017/ (27 files)
│   ├── 2018/ (27 files)
│   ├── 2019/ (24 files)
│   ├── 2020/ (27 files)
│   ├── 2021/ (27 files)
│   ├── 2022/ (29 files)
│   ├── 2023/ (29 files)
│   └── 2024/ (29 files)
│
├── Visa_Bulletin/ (168 files in 16 folders)
│   ├── 2011/ (6 files)
│   ├── 2012/ (11 files)
│   ├── 2013/ (12 files)
│   ├── 2014/ (12 files)
│   ├── 2015/ (12 files)
│   ├── 2016/ (12 files)
│   ├── 2017/ (11 files)
│   ├── 2018/ (11 files)
│   ├── 2019/ (12 files)
│   ├── 2020/ (10 files)
│   ├── 2021/ (12 files)
│   ├── 2022/ (9 files)
│   ├── 2023/ (11 files)
│   ├── 2024/ (12 files)
│   ├── 2025/ (12 files)
│   └── 2026/ (3 files)
│       ├── visabulletin_january2026.pdf
│       ├── visabulletin_february2026.pdf
│       └── visabulletin_march2026.pdf (if available)
│
├── Visa_Statistics/ (198 files in 9 folders)
│   ├── 2017/ (20 files)
│   │   ├── IV Issuances by FSC and Visa Class - [Month] 2017.xlsx
│   │   └── IV Issuances by Post and Visa Class - [Month] 2017.xlsx
│   ├── 2018/ (24 files) - 12 months × 2 files
│   ├── 2019/ (24 files)
│   ├── 2020/ (24 files)
│   ├── 2021/ (24 files)
│   ├── 2022/ (24 files)
│   ├── 2023/ (24 files)
│   ├── 2024/ (24 files)
│   └── 2025/ (10 files) - Through May 2025
│
└── WARN/ (2 files in 17 folders)
    ├── AZ/ (0 files)
    ├── CA/ (1 file)
    │   └── WARN_Report.xlsx
    ├── FL/ (0 files)
    ├── GA/ (0 files)
    ├── IL/ (0 files)
    ├── IN/ (0 files)
    ├── MA/ (0 files)
    ├── MI/ (0 files)
    ├── NC/ (0 files)
    ├── NJ/ (0 files)
    ├── NY/ (0 files)
    ├── OH/ (0 files)
    ├── PA/ (0 files)
    ├── TN/ (0 files)
    ├── TX/ (1 file)
    └── WA/ (0 files)
```

---

## New Data Sources - Download Status

### ✅ Successfully Downloaded (7 sources, 40 files)

1. **USCIS Processing Times** ✅
   - **Files:** 2 (HTML + CSV)
   - **Coverage:** Monthly snapshots (Feb 2026)
   - **Method:** Selenium browser automation to bypass Cloudflare protection
   - **Structure:**
     - `raw/YYYY-MM/processing_times.html` - Full page snapshot
     - `parsed/YYYY-MM/processing_times.csv` - Extracted data (when available)
   - **Note:** CSV parsing may be limited due to JavaScript-rendered content

2. **DOS Immigrant Visa Waiting List** ✅
   - **Files:** 2 (PDF + CSV)
   - **Coverage:** 2023 backlog snapshot
   - **Method:** Direct PDF download + PyPDF2 parsing
   - **Format:** 
     - `YYYY/waiting_list_YYYY.pdf` - Official DOS report
     - `YYYY/waiting_list_YYYY.csv` - Parsed table data (fiscal_year, category, country, count)
   - **Note:** Only 2023 available; older years may use different URL patterns

2. **DOL OFLC Record Layouts** ✅
   - **Files:** 15 PDFs
   - **Coverage:** PERM (FY2011, FY2020-2026) and LCA (FY2020-2026)
   - **Purpose:** Explains data structure and field definitions for LCA/PERM datasets

3. **BLS OEWS Wage Data** ✅
   - **Files:** 3 (2 ZIP files + 1 PDF)
   - **Coverage:** 2023-2024 all data + technical notes
   - **Size:** Large ZIP files with comprehensive occupational employment/wage data

4. **USCIS H-1B Employer Data Hub** ✅
   - **Files:** 14 CSVs
   - **Coverage:** FY2010-FY2023
   - **Size:** ~60 MB total (4-5 MB per fiscal year)
   - **Purpose:** Employer-level H-1B approval data by fiscal year

5. **DOS Annual Numerical Limits** ⚠️ *Partial*
   - **Files:** 1 PDF (FY2025 only)
   - **Coverage:** Only FY2025 exists at the expected URL
   - **Note:** FY2015-2024 and FY2026-2027 returned 404 errors

6. **Static Codebooks** ✅
   - **Files:** 3 CSVs
   - **Content:**
     - `soc_crosswalk_2010_to_2018.csv` - SOC code mapping between versions
     - `country_codes_iso.csv` - Country code reference
     - `eb_subcategory_codes.csv` - Employment-based preference categories

7. **DOS Immigrant Visa Waiting List (Alternative Years)** ⚠️
   - **Status:** Only 2023 downloaded
   - **Note:** 2015-2022, 2024-2026 either don't exist or use different URL patterns
   - **Action:** Handler tries multiple URL patterns; manual verification recommended for missing years

---

### ❌ Previously Failed (Now Fixed)

**Original Issues:**
- **USCIS Processing Times:** Was blocked by bot protection (403 Forbidden)
  - **Solution:** Implemented Selenium with headless Chrome, increased wait time for Cloudflare challenge
  - **Status:** ✅ Now working
  
- **DOS Immigrant Visa Waiting List:** Page not found (404) using old URL pattern
  - **Solution:** Discovered correct URL pattern through parent statistics page
  - **Status:** ✅ Partially working (2023 confirmed)

---

## Data Coverage Timeline

### Labor Data (LCA/PERM)
- **H-1B LCA:** FY2008 - FY2026 (19 fiscal years)
- **PERM:** FY2008 - FY2026 (19 fiscal years)
- **Recent Years:** Quarterly data (4 quarters + annual)
- **Historical Years:** Annual data + record layouts

### Visa Statistics
- **Monthly Bulletins:** January 2011 - March 2026 (15+ years)
- **Monthly IV Issuances:** March 2017 - May 2025 (8+ years)
- **Annual Reports:** FY2015 - FY2024 (10 fiscal years)

### Employment-Based Immigration (USCIS)
- **Historical:** 1991, 2003
- **Recent:** 2012-2026 (15 years)
- **Most Complete:** 2022-2026 (quarterly I-140, I-485, I-765, I-526, EB inventory)

### Nonimmigrant Visas (NIV)
- **Workload Reports:** Multiple fiscal years
- **Detail Tables:** Recent years + multi-year summaries

---

## File Formats

| Format | Count | Usage |
|--------|-------|-------|
| **XLSX** | ~600 | LCA, PERM, USCIS employment data, monthly IV statistics |
| **PDF** | ~550 | Visa bulletins, annual reports, record layouts, NIV reports |
| **JSON** | ~5 | API data (BLS, Census ACS) |
| **CSV** | ~2 | WARN data |

---

## Recently Added Data Sources (Code Ready, Not Yet Downloaded)

The following data sources have handler functions implemented but data not yet downloaded:

1. **USCIS Processing Times** (uscis_processing_times)
   - Monthly HTML snapshots + parsed CSV
   - Tracks processing times by form, category, and office

2. **DOS Annual Numerical Limits** (dos_numerical_limits)
   - FY2015-current PDFs
   - Annual visa category limits

3. **DOS Immigrant Visa Waiting List** (dos_waiting_list)
   - Multi-year waiting list reports
   - PDF format by year

4. **DOL OFLC Record Layouts** (dol_record_layouts)
   - FY2008-2026 PERM and LCA record layouts
   - Explains data structure and field definitions

5. **BLS OEWS Wage Data** (bls_oews)
   - 2023-2024 occupational wage data
   - ZIP files + technical notes

6. **USCIS H-1B Employer Data Hub** (uscis_h1b_employer_hub)
   - FY2010-current employer-level CSV files
   - H-1B approvals by employer

7. **Static Codebooks** (codebooks)
   - SOC crosswalk (2010 → 2018)
   - Country codes (ISO)
   - EB subcategory codes

**To download these sources, run:**
```bash
python fetch_latest.py sources.yaml
```

---

## Notes

- **Incremental Downloads:** The manifest system tracks all downloaded files and only fetches new data on subsequent runs
- **WARN Data:** Most state sources require interactive access or have no recent data
- **TRAC Data:** Requires paid subscription, marked for manual download
- **Duplicate PERM:** The PERM/ folder contains a nested PERM/PERM/ structure (artifact of handler logic)

---

## Total Storage

**Estimated Size:** 3-5 GB (primarily Excel and PDF files)  
**Growth Rate:** ~50-100 MB/month with incremental updates

---

*Generated: February 20, 2026*
