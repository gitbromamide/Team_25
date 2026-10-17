"""Download FIDE rating lists (standard, rapid, blitz) by building URLs from FIDE's naming pattern.

Confirmed pattern for standard (HTTP 200 for jan16, jan20):
    https://ratings.fide.com/download/standard_{mon}{yy}frl_xml.zip
Rapid and blitz are ASSUMED to follow the same pattern (rapid_jan20frl_xml.zip, blitz_jan20frl_xml.zip).
Run with --check first; files reported 404 are simply skipped.
The archive starts Feb 2015. The current month is not in the archive:
    https://ratings.fide.com/download/{standard,rapid,blitz}_rating_list_xml.zip   (use --current YYYY-MM)

Usage:
  python scripts/01_list_and_download.py --format all --check --start 2015-02 --end 2016-12 --months jan,jul
  python scripts/01_list_and_download.py --format all --months jan,jul
  python scripts/01_list_and_download.py --format rapid --months jan
  python scripts/01_list_and_download.py --format all --months jan --start 2030-01 --end 2030-01 --current 2026-10
"""
import argparse, os, sys, time
import requests, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import MONTHS, FORMATS

BASE = "https://ratings.fide.com/download/"
HEAD = {"User-Agent": "Mozilla/5.0 (course project)"}

def month_range(start, end):
    y, m = map(int, start.split("-")); y2, m2 = map(int, end.split("-"))
    while (y, m) <= (y2, m2):
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1

def file_name(fmt, y, m):
    return f"{fmt}_{MONTHS[m - 1]}{y % 100:02d}frl_xml.zip"

def fetch(url, dest):
    r = requests.get(url, headers=HEAD, timeout=600, stream=True)
    if r.status_code == 200:
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
        print("saved", dest, f"{os.path.getsize(dest) / 1e6:.1f} MB")
    else:
        print("MISSING", url, r.status_code)
    return r.status_code

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--format", default="all", help="standard, rapid, blitz or all")
    ap.add_argument("--start", default="2015-02")
    ap.add_argument("--end", default="2026-09")
    ap.add_argument("--months", default="jan,jul", help="e.g. jan,jul or all")
    ap.add_argument("--current", default=None, help="YYYY-MM label for the current-month lists")
    ap.add_argument("--check", action="store_true", help="only check which files exist")
    ap.add_argument("--sleep", type=float, default=2.0)
    a = ap.parse_args()

    fmts = FORMATS if a.format == "all" else a.format.split(",")
    wanted = set(MONTHS) if a.months == "all" else set(a.months.split(","))
    months = [(y, m) for y, m in month_range(a.start, a.end) if MONTHS[m - 1] in wanted]
    os.makedirs("data/raw", exist_ok=True)
    print(f"{len(months)} months x {len(fmts)} formats")

    log = []
    for fmt in fmts:
        for y, m in months:
            name = file_name(fmt, y, m); url = BASE + name; dest = os.path.join("data/raw", name)
            if a.check:
                code = requests.head(url, headers=HEAD, timeout=60, allow_redirects=True).status_code
                print(name, code); log.append({"file": name, "status": code}); time.sleep(0.5); continue
            if os.path.exists(dest):
                continue
            log.append({"file": name, "status": fetch(url, dest)}); time.sleep(a.sleep)
        if a.current and not a.check:
            y, m = map(int, a.current.split("-"))
            dest = os.path.join("data/raw", file_name(fmt, y, m))
            if not os.path.exists(dest):
                log.append({"file": os.path.basename(dest), "status": fetch(BASE + f"{fmt}_rating_list_xml.zip", dest)})
    pd.DataFrame(log).to_csv("data/links.csv", index=False)
    print("log saved to data/links.csv")
