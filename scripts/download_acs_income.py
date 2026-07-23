#!/usr/bin/env python3
"""Download ACS 5-year median household income (B19013) for NYC ZCTAs.

The Census API doesn't support filtering ZCTAs by state for this table,
so this pulls all ~33,000 ZCTAs nationwide in one call and keeps only
the ones with a NYC ZIP prefix. Writes a small reference table meant
to be committed to the repo, not treated as raw data.
"""

import csv
import os
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
ACS_YEAR = 2023  # most recent 5-year ACS vintage available at download time
BASE_URL = f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5"
OUT_PATH = ROOT / "data" / "reference" / "nyc_zcta_median_income.csv"

# Standard NYC ZIP code prefixes by borough.
NYC_ZIP_PREFIXES = (
    "100", "101", "102",  # Manhattan
    "103",                # Staten Island
    "104",                # Bronx
    "110", "111", "112", "113", "114", "116",  # Queens + Brooklyn (112)
)

CENSUS_NULL = "-666666666"  # Census sentinel for suppressed/unavailable estimates


def load_env_file(path):
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def main():
    load_env_file(ROOT / ".env")
    api_key = os.environ.get("CENSUS_API_KEY")
    if not api_key:
        raise SystemExit("CENSUS_API_KEY not set (add it to .env)")

    params = {
        "get": "NAME,B19013_001E",
        "for": "zip code tabulation area:*",
        "key": api_key,
    }
    resp = requests.get(BASE_URL, params=params, timeout=60)
    resp.raise_for_status()
    rows = resp.json()
    header, records = rows[0], rows[1:]
    zcta_idx = header.index("zip code tabulation area")
    income_idx = header.index("B19013_001E")

    nyc_rows = [
        (r[zcta_idx], r[income_idx])
        for r in records
        if r[zcta_idx].startswith(NYC_ZIP_PREFIXES) and r[income_idx] != CENSUS_NULL
    ]
    nyc_rows.sort(key=lambda r: r[0])

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["zcta", "median_household_income"])
        writer.writerows(nyc_rows)

    print(f"{len(nyc_rows)} NYC ZCTAs written to {OUT_PATH}")
    print(f"(nationwide pull returned {len(records)} ZCTAs total)")


if __name__ == "__main__":
    main()
