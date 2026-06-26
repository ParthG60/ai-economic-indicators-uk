"""Canaries age cut — LFS microdata (EUL), quarterly.

Tests whether AI-exposed occupations are shedding YOUNG workers faster than older ones,
the core Canaries-v2 hypothesis. Reads LFS quarterly person files (Stata .dta) from
data/canaries/lfs/ (raw or inside the UKDS zip), joins each person's SOC20M to our
exposure quintiles, and tracks the young-worker share of employment by exposure quintile.

Builds a QUARTERLY series (19 calendar quarters, 2021 Q1 -> 2026 Q1) with a 4-quarter
rolling mean to remove seasonality and LFS sampling noise. Skips overlapping rolling
quarters and household files automatically.
"""
import glob
import io
import os
import re
import zipfile
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LFS_DIR = os.path.join(ROOT, "data", "canaries", "lfs")
QUINTILES = os.path.join(ROOT, "data", "canaries", "occupation_exposure_quintiles.csv")
OUT_DIR = os.path.join(ROOT, "data", "canaries")

CALENDAR_Q = {"jm": 1, "aj": 2, "js": 3, "od": 4}
Q_END = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}
YOUNG = {"16-24": (16, 24), "22-25": (22, 25)}   # 16-24 = ours; 22-25 = Brynjolfsson cut


def _open_dta(path):
    if path.lower().endswith(".zip"):
        zf = zipfile.ZipFile(path)
        inner = [n for n in zf.namelist() if n.lower().endswith(".dta")][0]
        return io.BytesIO(zf.open(inner).read()), os.path.basename(inner)
    with open(path, "rb") as fh:
        return io.BytesIO(fh.read()), os.path.basename(path)


def _read_dta_cols(buf, want):
    buf.seek(0)
    rdr = pd.io.stata.StataReader(buf)
    up = {c.upper(): c for c in rdr.variable_labels().keys()}
    cols, names = [], {}
    for key, p in want.items():
        hit = up.get(p) or next((up[c] for c in sorted(up) if c.startswith(p)), None)
        if hit:
            cols.append(hit)
            names[hit] = key
    buf.seek(0)
    return pd.read_stata(buf, columns=cols, convert_categoricals=False).rename(columns=names)


def load():
    files = sorted(glob.glob(os.path.join(LFS_DIR, "*.zip")) +
                   glob.glob(os.path.join(LFS_DIR, "*.dta")))
    if not files:
        print("No LFS files in", LFS_DIR, "- see reference/ukds_inventory.md")
        return None

    q = pd.read_csv(QUINTILES).rename(columns={"Unnamed: 0": "soc"})
    qmap = q.assign(soc=q.soc.astype(int)).set_index("soc")["quintile"]
    want = {"soc": "SOC20M", "age": "AGE", "ilo": "ILODEFR", "wt": "PWT"}

    parts = []
    for f in files:
        buf, inner = _open_dta(f)
        m = re.search(r"lfsp_([a-z]{2})(\d{2})", inner.lower())   # person files only
        if not m or m.group(1) not in CALENDAR_Q:
            continue
        cc, yy = m.group(1), int("20" + m.group(2))
        d = _read_dta_cols(buf, want)
        for c in ["soc", "age", "ilo", "wt"]:
            d[c] = pd.to_numeric(d[c], errors="coerce")
        d = d[d.ilo == 1].dropna(subset=["soc", "age", "wt"])
        d["quintile"] = d.soc.astype(int).map(qmap)
        d = d.dropna(subset=["quintile"])
        d["date"] = pd.Timestamp(yy, *Q_END[CALENDAR_Q[cc]])
        parts.append(d[["date", "quintile", "age", "wt"]])
    return pd.concat(parts, ignore_index=True) if parts else None


def young_share(d, lo, hi):
    """Weighted % of employment aged lo..hi, per (date, quintile)."""
    g = d.groupby(["date", "quintile"])
    tot = g.wt.sum()
    yng = d[(d.age >= lo) & (d.age <= hi)].groupby(["date", "quintile"]).wt.sum()
    pct = (yng / tot * 100)
    return pct.unstack("quintile").sort_index()


def main():
    d = load()
    if d is None:
        return
    nq = d.date.nunique()
    print(f"Loaded {nq} quarters, {len(d):,} employed person-records "
          f"({d.date.min():%Y-%m} to {d.date.max():%Y-%m})\n")

    out = {}
    for label, (lo, hi) in YOUNG.items():
        raw = young_share(d, lo, hi)
        roll = raw.rolling(4, min_periods=2).mean()        # 4Q deseasonalised
        raw.columns = [f"Q{int(c)}" for c in raw.columns]
        roll.columns = [f"Q{int(c)}" for c in roll.columns]
        raw.round(2).to_csv(os.path.join(OUT_DIR, f"canaries_age_cut_q_{lo}_{hi}_raw.csv"))
        roll.round(2).to_csv(os.path.join(OUT_DIR, f"canaries_age_cut_q_{lo}_{hi}_roll.csv"))
        out[label] = roll
        # Gap = most-exposed minus least-exposed young share (4Q-smoothed).
        roll["Q5_minus_Q1"] = roll["Q5"] - roll["Q1"]
        print(f"=== Young {label} share of employment, 4-quarter rolling mean (%) ===")
        print(roll[["Q1", "Q5", "Q5_minus_Q1"]].dropna().round(2).to_string())
        print()

    print("Wrote quarterly raw + 4Q-rolling CSVs for both age bands.")


if __name__ == "__main__":
    main()
