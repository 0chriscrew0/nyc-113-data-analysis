#!/usr/bin/env python3
"""Download NYC 311 service requests for 2022-2025 from the Socrata API.

Paginates by month, then by unique_key within each month (keyset
pagination), since offset-based paging degrades badly on a dataset
this size. Writes one CSV per month to data/raw/311/, skipping months
that already have a completed file so a crashed run can resume.
"""

import csv
import os
import time
from datetime import date
from pathlib import Path

import requests

BASE_URL = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"
FIELDS = [
    "unique_key", "created_date", "closed_date", "agency", "complaint_type",
    "descriptor", "incident_zip", "city", "borough", "status",
    "open_data_channel_type", "community_board", "council_district",
    "latitude", "longitude",
]
PAGE_SIZE = 50000
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "311"
START_YEAR, START_MONTH = 2022, 1
END_YEAR, END_MONTH = 2025, 12
APP_TOKEN = os.environ.get("SOCRATA_APP_TOKEN")


def month_ranges():
    y, m = START_YEAR, START_MONTH
    while (y, m) <= (END_YEAR, END_MONTH):
        start = date(y, m, 1)
        end = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
        yield start, end
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def get_with_retry(session, params, max_retries=6):
    for attempt in range(max_retries):
        try:
            resp = session.get(BASE_URL, params=params, timeout=60)
            if resp.status_code == 429:
                raise requests.HTTPError("rate limited")
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as e:
            wait = min(2 ** attempt, 60)
            print(f"    retry {attempt + 1}/{max_retries} after {e!r}, waiting {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"exceeded {max_retries} retries for params={params}")


def fetch_month(start, end, session):
    out_path = OUT_DIR / f"{start:%Y-%m}.csv"
    if out_path.exists():
        print(f"  {out_path.name} already exists, skipping")
        return

    cursor = 0
    rows_written = 0
    tmp_path = out_path.with_suffix(".csv.part")
    with tmp_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        while True:
            where = (
                f"created_date >= '{start:%Y-%m-%d}T00:00:00' "
                f"AND created_date < '{end:%Y-%m-%d}T00:00:00' "
                f"AND unique_key::number > {cursor}"
            )
            params = {
                "$select": ",".join(FIELDS),
                "$where": where,
                "$order": "unique_key::number",
                "$limit": PAGE_SIZE,
            }
            if APP_TOKEN:
                params["$$app_token"] = APP_TOKEN
            page = get_with_retry(session, params)
            if not page:
                break
            for row in page:
                writer.writerow({k: row.get(k, "") for k in FIELDS})
            rows_written += len(page)
            cursor = int(page[-1]["unique_key"])
            if len(page) < PAGE_SIZE:
                break
    tmp_path.rename(out_path)
    print(f"  {out_path.name}: {rows_written} rows")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    for start, end in month_ranges():
        print(f"{start:%Y-%m}")
        fetch_month(start, end, session)


if __name__ == "__main__":
    main()
