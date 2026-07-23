# Data sources

Raw and processed data are gitignored. This file is the source of truth for
where everything came from. Fill in the blanks as each dataset is pulled.

## NYC 311 Service Requests (2022-2025)

- **Source:** NYC Open Data, Socrata dataset `erm2-nwe9`
- **URL:** https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9
- **Filter:** `created_date` between 2022-01-01 and 2025-12-31
- **Download method:** `scripts/download_311.py`. Paginates by month, then by `unique_key` within each month (keyset pagination on `unique_key::number`, since offset paging degrades on a dataset this size). Writes one CSV per month to `data/raw/311/`, then `duckdb` combines them into a single Parquet file at `data/processed/311_2022_2025.parquet`.
- **Download date:** 2026-07-22
- **Row count at download:** 13,506,490 (matches the API's `count(*)` for the same date filter exactly)
- **Raw size:** 2.3 GB across 48 monthly CSVs; 480 MB as a single Parquet file
- **Columns kept:** the source dataset has ~48 columns; only the ones the analysis actually needs were pulled: `unique_key`, `created_date`, `closed_date`, `agency`, `complaint_type`, `descriptor`, `incident_zip`, `city`, `borough`, `status`, `open_data_channel_type`, `community_board`, `council_district`, `latitude`, `longitude`. Dropped things like address strings, park/vehicle/bridge fields, and the NYC computed-region codes, since none of them feed the hypotheses in `PLAN.md`.

## ACS Median Household Income (B19013, ZCTA level)

- **Source:** U.S. Census Bureau, ACS 5-Year Estimates, table B19013
- **URL:** https://api.census.gov/data/2023/acs/acs5
- **Vintage:** 2023 5-year (2019-2023), the most recent available at download time
- **Download method:** `scripts/download_acs_income.py`. The Census API doesn't support filtering ZCTAs by state for this table, so the script pulls all ~33,000 ZCTAs nationwide in one call and keeps the ones with a NYC ZIP prefix. Needs a free key from https://api.census.gov/data/key_signup.html, read from a `CENSUS_API_KEY` environment variable (see `.env.example`). Rows with the Census suppression sentinel (`-666666666`) are dropped.
- **Download date:** 2026-07-22
- **Output:** `data/reference/nyc_zcta_median_income.csv`, 192 ZCTAs, committed to the repo since it's small
- **Note:** ZCTAs approximate ZIP codes but aren't identical; see the limitations section of `PLAN.md`.

## NYC ZIP Code Tabulation Areas (boundary shapefile)

- **Source:** NYC Open Data
- **URL:** _TBD_
- **Download date:** _TBD_
