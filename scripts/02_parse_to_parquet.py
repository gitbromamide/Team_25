"""Parse every zip in data/raw into data/interim/<format>/<snapshot>.parquet.

The format (standard/rapid/blitz) is read from the file name prefix. Only XML lists are parsed.
The rating column is taken from <rapid_rating>/<blitz_rating> when present in a rapid/blitz file,
otherwise from <rating>. The tag names seen in the first player are printed so you can verify.
"""
import glob, os, sys, zipfile
import xml.etree.ElementTree as ET
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import snapshot_from_name, format_from_name

def parse_zip(path, snapshot, fmt):
    rows, seen = [], None
    with zipfile.ZipFile(path) as z:
        xmls = [n for n in z.namelist() if n.lower().endswith(".xml")]
        if not xmls:
            return None
        with z.open(xmls[0]) as f:
            for _, el in ET.iterparse(f, events=("end",)):
                if el.tag == "player":
                    if seen is None:
                        seen = [c.tag for c in el]
                    r = el.findtext(f"{fmt}_rating") if fmt != "standard" else None
                    if not r:
                        r = el.findtext("rating")
                    rows.append({"fideid": el.findtext("fideid"), "country": el.findtext("country"),
                                 "sex": el.findtext("sex"), "title": el.findtext("title"),
                                 "rating": r, "birthday": el.findtext("birthday"),
                                 "flag": el.findtext("flag")})
                    el.clear()
    df = pd.DataFrame(rows)
    for c in ["fideid", "rating", "birthday"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["snapshot"] = snapshot
    df["format"] = fmt
    return df, seen

if __name__ == "__main__":
    shown = set()
    for path in sorted(glob.glob("data/raw/*.zip")):
        name = os.path.basename(path)
        snap, fmt = snapshot_from_name(name), format_from_name(name)
        if snap is None:
            print("skip (cannot read month/year from name):", name); continue
        os.makedirs(f"data/interim/{fmt}", exist_ok=True)
        out = f"data/interim/{fmt}/{snap}.parquet"
        if os.path.exists(out):
            continue
        res = parse_zip(path, snap, fmt)
        if res is None:
            print("skip (no XML inside):", name); continue
        df, seen = res
        if fmt not in shown:
            print(f"[{fmt}] tags in first player:", seen); shown.add(fmt)
        df.to_parquet(out, index=False)
        print(f"{fmt} {snap}: {len(df):,} players, {df['rating'].notna().sum():,} rated -> {out}")
