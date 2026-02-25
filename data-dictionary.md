# DATA_DICTIONARY.md

**Repository:** `fetch-immigration-data`  
**Last updated:** 2026‑02‑20

This document describes every dataset downloaded into this project: the **purpose**, **what files contain**, **key fields to extract**, **how they join** with other datasets, the **update cadence**, and **caveats**.  
This dictionary is the functional contract for Project 2 (model‑builder) and Project 3 (public app).

> Tip: Keep the raw source files and record layouts for auditability; do not overwrite past snapshots.

---

## 0) Canonical Codebooks & Join Keys

Location: `downloads/Codebooks/`  
Files:
- `soc_crosswalk_2010_to_2018.csv` — maps older SOC codes to SOC 2018
- `country_codes_iso.csv` — country canonicalization (name → ISO2/ISO3)
- `eb_subcategory_codes.csv` — maps sub‑classes (e.g., E11, E21/NIW) to canonical EB1..EB5 + labels

**Primary joins used across the warehouse**
- Country → `country_codes_iso` (prefer ISO3)  
- EB category → `eb_subcategory_codes` (and direct EB1..EB5 labels)  
- SOC → `soc_crosswalk_2010_to_2018` (normalize to SOC 2018)  
- Employer → normalized `employer_name` (deterministic aliasing)  
- Geography → selected area system (MSA/CBSA); maintain a single geo mapping

---

## 1) Visa Bulletin

**Path**: `downloads/Visa_Bulletin/` (monthly PDFs, 2011–2026)  
**Purpose**: Monthly EB **cutoff dates** (Final Action & Dates for Filing) by category and chargeability; drives PD forecasting & retrogression risk.

**Key fields to extract (normalized)**
- `bulletin_year`, `bulletin_month`  
- `chart` ∈ {`FAD` (Final Action), `DFF` (Dates for Filing)}  
- `category` ∈ {EB1..EB5 (with sub‑rows where present)}  
- `country` (chargeability)  
- `cutoff_date` (nullable)  
- `status_flag` ∈ {`C` (current), `U` (unavailable)}  

**Joins**
- `category` ↔ EB codebook  
- `country` ↔ ISO codebook

**Cadence**: Monthly  
**Caveats**: Footnotes can carry material exceptions (hold, unavailable, intra‑month notes). Store raw PDFs.

---

## 2) DOS Annual Numerical Limits

**Path**: `downloads/DOS_Numerical_Limits/` (FY2025 present)  
**Purpose**: Annual **worldwide** and **per‑country** visa caps per EB category; constrains queue simulations and explains tight months.

**Key fields**
- `fiscal_year`  
- `category` (E1..E5; keep family if parsed)  
- `worldwide_limit`  
- `per_country_limit` (≈7% policy context)  
- `notes`

**Joins**: `category` ↔ EB codebook  
**Cadence**: Annual  
**Caveats**: Older FY PDFs may reside at older paths; keep FY2025 as ground truth and backfill as available.

---

## 3) DOS Annual Immigrant Visa Waiting List

**Path**: `downloads/DOS_Waiting_List/` (2023 PDF + CSV)  
**Purpose**: As‑of‑Nov‑1 **backlog snapshot** by category/country; calibrates model priors for queue size.

**Key fields**
- `fiscal_year`  
- `category`  
- `country`  
- `count`

**Joins**: `category` ↔ EB codebook; `country` ↔ ISO codebook  
**Cadence**: Annual  
**Caveats**: URL patterns vary; store raw PDF and derived CSV with provenance.

---

## 4) Visa Annual Reports

**Path**: `downloads/Visa_Annual_Reports/` (2015–2024)  
**Purpose**: Official **annual** statistics across immigrant/nonimmigrant categories, by class, post, country. Great for historical baselines and QA.

**Key fields** (vary by table)
- `fiscal_year`  
- `visa_class` (e.g., E11/E12/E21…)  
- `country` or `post`  
- `issued` (and sometimes refusals)

**Joins**: `visa_class` ↔ EB codebook; `country` ↔ ISO codebook  
**Cadence**: Annual  
**Caveats**: Table layouts differ across years; capture table name and page in extraction lineage.

---

## 5) Visa Monthly Statistics (IV Issuances)

**Path**: `downloads/Visa_Statistics/` (2017–2025 monthly)  
**Purpose**: **Monthly** immigrant visa issuances by **country** and **post**, used for movement context and cross‑checks.

**Key fields**
- `report_year`, `report_month`  
- `visa_class`  
- `country` or `post`  
- `issued`

**Joins**: `visa_class` ↔ EB codebook; `country` ↔ ISO codebook  
**Cadence**: Monthly (lagged)  
**Caveats**: Some files group sub‑classes differently; keep a small mapping per year if needed.

---

## 6) USCIS Immigration Data Library

**Path**: `downloads/USCIS_IMMIGRATION/` (1991–2026; strongest for 2022–2026)  
**Purpose**: Form‑level USCIS volumes/outcomes (I‑140, I‑485, I‑765, EB inventories, EB‑5, etc.); powers **denial trends**, **pipeline** analysis.

**Key fields** (depend on table)
- `fiscal_year`, `quarter`  
- `form_type` (I‑140, I‑485, I‑765, etc.)  
- `category` (if available)  
- `received`, `approved`, `denied`, `pending`  
- `office` (sometimes), `notes`

**Joins**: `category` ↔ EB codebook  
**Cadence**: Quarterly/periodic  
**Caveats**: Definitions and breakouts shift; preserve readme/metadata alongside each table.

---

## 7) DOL LCA (H‑1B) Disclosure

**Path**: `downloads/LCA/` and `downloads/LCA/H1B/` (FY2008–2026)  
**Purpose**: Employer **intent** filings with wage/SOC/location → **wage comparison**, **sponsorship hotspots**, employer context.  
**Important**: **LCA is intent, not hire/approval**.

**Key fields** (schema varies by FY; verify with record layouts)
- `CASE_STATUS`  
- `EMPLOYER_NAME`, `EMPLOYER_ADDRESS`  
- `SOC_CODE`, `SOC_TITLE`  
- `WAGE_RATE_OF_PAY`, `WAGE_UNIT`, `PREVAILING_WAGE`, `WAGE_LEVEL`  
- `WORKSITE_CITY`, `WORKSITE_STATE`  
- `NAICS_CODE`  
- `RECEIVED_DATE`, `DECISION_DATE`

**Joins**  
- `SOC_CODE` ↔ SOC codebook (normalize to SOC 2018)  
- Employer name ↔ normalized entity (alias table)  
- Worksite geo ↔ OEWS area mapping

**Cadence**: Quarterly + annual  
**Caveats**: Major schema change in FLAG era (FY2020+); use record layouts for accurate parsing.

---

## 8) DOL PERM Disclosure

**Path**: `downloads/PERM/` (FY2008–2026)  
**Purpose**: EB green card **labor certification outcomes** used for **GC‑friendliness**, **audit risk**, and **denial trends**.

**Key fields** (verify per FY via record layouts)
- `CASE_STATUS`, `DECISION_DATE`  
- `AUDIT_FLAG`  
- `EMPLOYER_NAME`, `NAICS_CODE`  
- `JOB_TITLE`, `SOC_CODE`  
- `WAGE_OFFER_FROM`, `WAGE_OFFER_TO`, `PW_SOURCE`  
- `WORKSITE_*` (city/state/zip)

**Joins**: SOC ↔ SOC codebook; Employer ↔ normalized entity; Geo ↔ area mapping  
**Cadence**: Quarterly + annual  
**Caveats**: Version drift by FY; always pin extractor to the matching record layout.

---

## 9) DOL OFLC Record Layouts

**Path**: `downloads/DOL_Record_Layouts/` (PERM & LCA; FY2011, 2020–2026)  
**Purpose**: Authoritative **schemas** for LCA & PERM by FY; mandatory for accurate parsing.

**Usage**  
- Map raw columns → canonical schema  
- Track field renames, enumerations, nullability  
- Keep layout version in lineage for each parsed table

---

## 10) USCIS H‑1B Employer Data Hub

**Path**: `downloads/USCIS_H1B_Employer_Hub/raw/` (FY2010–2023 CSVs)  
**Purpose**: Employer‑level H‑1B **approvals/denials** by FY; enriches employer insights (with LCA/PERM context).

**Key fields** (vary by FY)
- `fiscal_year`  
- `employer_name`, `city`, `state`  
- `approvals`, `denials` (sometimes split by initial/continuing)

**Joins**: Employer name ↔ normalized entity  
**Cadence**: Annual  
**Caveats**: Archived dataset; use as **supplementary** signal vs. PERM.

---

## 11) BLS OEWS (Wage Percentiles)

**Path**: `downloads/BLS_OEWS/` (2023–2024 "All data" ZIP/XLSX + notes)  
**Purpose**: Official **wage percentiles** (P10/25/Median/75/90) by **SOC** and **area** for salary competitiveness analysis.

**Key fields** (from all‑data tables)
- `occ_code` (SOC), `occ_title`  
- `area_code`, `area_title`  
- `employment`  
- `hourly_mean`, `annual_mean`  
- `pct10`, `pct25`, `median`, `pct75`, `pct90`

**Joins**: SOC ↔ SOC codebook (2018); Area ↔ chosen geo mapping  
**Cadence**: Annual (May)  
**Caveats**: SOC/area delineations evolve; keep the technical notes alongside loaders.

---

## 12) ACS (Census)

**Path**: `downloads/ACS/` (e.g., nativity)  
**Purpose**: Contextual demographics for normalization (e.g., per‑capita rates, geographic controls).

**Key fields**: table‑specific; retain original metadata JSON  
**Cadence**: Annual  
**Caveats**: Use only as contextual enrichers, not core facts.

---

## 13) DHS Yearbook

**Path**: `downloads/DHS_Yearbook/`  
**Purpose**: Long‑run immigration totals and breakdowns; good QA reference and contextual backdrop.

**Cadence**: Annual  
**Caveats**: Aggregated; not used for fine‑grained model features.

---

## 14) NIV Statistics

**Path**: `downloads/NIV_Statistics/`  
**Purpose**: Nonimmigrant visa workload and detail tables for context on job‑market flows.

**Cadence**: Annual  
**Caveats**: Primarily contextual; formats vary.

---

# Warehouse Targets (high‑level)

You will normalize the above into (suggested):
- `dim_time`, `dim_country`, `dim_visa_class`, `dim_soc`, `dim_area`, `dim_employer`
- `fact_cutoffs` (Visa Bulletin)
- `fact_perm` (PERM outcomes)
- `fact_lca` (LCA filings)
- `fact_oews` (wage percentiles)
- `fact_uscis_forms` (I‑140/I‑485 volumes/outcomes)
- `fact_iv_issuances_monthly` (DOS monthly)
- `fact_waiting_list` (DOS annual backlog)

Keep **source provenance** columns on all facts: `source_file`, `source_url`, `ingested_at`, `record_layout_version` (where relevant), and (for PDFs) `page_ref`.

---

# Disclaimers (show in UI)

- **LCA ≠ hire or petition approval**; LCAs reflect employer intent and may include location changes.  
- **Forecasts are estimates**, not legal advice; always show **P10/P50/P90** ranges and cite month.  

- **SOC and area definitions change**; visualizations reflect the latest normalizations.

---

## Appendix A — Field Inventory (to be appended)

Use the prompt below in Copilot/agent to auto‑append a short "Field Inventory" section with actual columns and inferred types from representative files:
