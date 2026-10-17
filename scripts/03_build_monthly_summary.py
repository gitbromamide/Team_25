"""Build data/processed/summary.csv: one row per (format, snapshot, country)."""
import glob, os
import pandas as pd

THRESHOLDS = [2000, 2300, 2500, 2700]

def summarize(df):
    d = df[df["rating"].notna()].copy()
    d["titled"] = d["title"].isin(["GM", "IM"])
    d["gm"] = d["title"].eq("GM")
    # 'flag' appears to mark inactive players; verify in the audit section of the notebook.
    d["active_guess"] = ~d["flag"].fillna("").str.lower().str.contains("i")
    for t in THRESHOLDS:
        d[f"ge{t}"] = d["rating"] >= t
    g = d.groupby(["format", "snapshot", "country"])
    out = g.agg(n_rated=("rating", "size"),
                n_active_guess=("active_guess", "sum"),
                n_titled=("titled", "sum"), n_gm=("gm", "sum"),
                mean_rating=("rating", "mean"),
                top10_mean=("rating", lambda s: s.nlargest(10).mean()),
                top100_mean=("rating", lambda s: s.nlargest(100).mean()),
                **{f"ge{t}": (f"ge{t}", "sum") for t in THRESHOLDS})
    return out.reset_index()

if __name__ == "__main__":
    paths = sorted(glob.glob("data/interim/*/*.parquet"))
    flat = sorted(glob.glob("data/interim/*.parquet"))  # old layout = standard lists
    parts = []
    for p in flat + paths:
        df = pd.read_parquet(p)
        if "format" not in df.columns:
            df["format"] = "standard"
        parts.append(summarize(df))
    os.makedirs("data/processed", exist_ok=True)
    res = pd.concat(parts, ignore_index=True)
    res.to_csv("data/processed/summary.csv", index=False)
    print("wrote data/processed/summary.csv:", len(res), "rows;", res.groupby("format")["snapshot"].nunique().to_dict())
