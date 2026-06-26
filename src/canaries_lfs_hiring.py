"""Canaries (LFS microdata) — employment by AGE BAND x AI-exposure, for the two toggle charts.

Two views of the same microdata, both indexed to 2022 Q4 = 100 by exposure quintile, each with
an age-band toggle on the dashboard:

  1. STOCK  (canaries_lfs_stock.csv)  — EVERYONE employed in the job. A slow-moving total: it is
     dominated by people who were already there and tend to stay, so a hiring change only erodes
     it gradually. The Q5-vs-Q1 gap lives entirely in the youngest band (22-25); older bands are
     flat. Bands: 22-25 / 26-34 / 35-49 / 50-64 (the stock has ample sample even at 22-25).
  2. HIRING (canaries_lfs_hiring.csv) — only RECENT HIRES (under 12 months with the employer,
     EMPLEN in {1,2,3}). Strips out incumbents, so it shows the hiring decision directly and moves
     fast. The young band is widened to 22-30 for sample (~210 vs ~90 most-exposed hires/quarter).
     Bands: 22-30 / 31-40 / 41-50 / 51-64; older bands are a built-in placebo.

Employment = sum of person weights (PWT*), 4-quarter rolling, indexed to 2022 Q4 (eve of ChatGPT).

Run: python src/canaries_lfs_hiring.py
"""
import glob, io, os, re, zipfile
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LFS = os.path.join(ROOT, "data", "canaries", "lfs")
OUT = os.path.join(ROOT, "data", "canaries")
QUINT = os.path.join(OUT, "occupation_exposure_quintiles.csv")

CAL = {"jm": 1, "aj": 2, "js": 3, "od": 4}
QE = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}
BASE = pd.Timestamp(2022, 12, 31)
RECENT = {1, 2, 3}                                    # EMPLEN: <3m, 3-6m, 6-12m = hired in last year
STOCK_BRACKETS = {"22-25": (22, 25), "26-34": (26, 34), "35-49": (35, 49), "50-64": (50, 64)}
HIRE_BRACKETS = {"22-30": (22, 30), "31-40": (31, 40), "41-50": (41, 50), "51-64": (51, 64)}


def _open(path):
    z = zipfile.ZipFile(path)
    inner = [n for n in z.namelist() if n.lower().endswith(".dta")][0]
    return io.BytesIO(z.open(inner).read()), os.path.basename(inner)


def load():
    qmap = pd.read_csv(QUINT).rename(columns={"Unnamed: 0": "soc"})
    qmap = qmap.assign(soc=lambda d: d.soc.astype(int)).set_index("soc")["quintile"]
    want = {"soc": "SOC20M", "age": "AGE", "ilo": "ILODEFR", "emplen": "EMPLEN"}
    parts = []
    for f in sorted(glob.glob(os.path.join(LFS, "*.zip")) + glob.glob(os.path.join(LFS, "*.dta"))):
        buf, inner = _open(f) if f.lower().endswith(".zip") else (io.BytesIO(open(f, "rb").read()), os.path.basename(f))
        m = re.search(r"lfsp_([a-z]{2})(\d{2})", inner.lower())
        if not m or m.group(1) not in CAL:
            continue
        up = {c.upper(): c for c in pd.io.stata.StataReader(buf).variable_labels().keys()}
        cols, names = [], {}
        for k, p in want.items():
            h = up.get(p) or next((up[c] for c in sorted(up) if c.startswith(p)), None)
            if h:
                cols.append(h); names[h] = k
        pw = next((up[c] for c in sorted(up) if c.startswith("PWT")), None)
        cols.append(pw); names[pw] = "wt"
        buf.seek(0)
        d = pd.read_stata(buf, columns=cols, convert_categoricals=False).rename(columns=names)
        for c in ("soc", "age", "ilo", "wt", "emplen"):
            d[c] = pd.to_numeric(d.get(c), errors="coerce")
        d = d[d.ilo == 1].dropna(subset=["soc", "age", "wt"])
        d["soc"] = d.soc.astype(int)
        d["quintile"] = d.soc.map(qmap)
        d["recent"] = d.emplen.isin(RECENT)
        d["date"] = pd.Timestamp(int("20" + m.group(2)), *QE[CAL[m.group(1)]])
        parts.append(d.dropna(subset=["quintile"])[["date", "quintile", "age", "wt", "recent"]])
    return pd.concat(parts, ignore_index=True)


def index_by_quintile(sub):
    """4Q-rolling weighted headcount by quintile, indexed to 2022 Q4 = 100."""
    lvl = sub.groupby(["date", "quintile"]).wt.sum().unstack("quintile").sort_index()
    roll = lvl.rolling(4, min_periods=2).mean()
    return roll / roll.loc[BASE] * 100


def build(d, brackets, recent_only, path, label):
    rows = []
    print(f"\n{label}:")
    for b, (lo, hi) in brackets.items():
        sub = d[(d.age >= lo) & (d.age <= hi)]
        if recent_only:
            sub = sub[sub.recent]
        idx = index_by_quintile(sub)
        last = idx.dropna().iloc[-1]
        print(f"  [{b}] vs 2022 Q4:  Q5 {last.get(5)-100:+5.1f}%   Q1 {last.get(1)-100:+5.1f}%   "
              f"Q5-Q1 {last.get(5)-last.get(1):+5.1f} pts")
        for date, r in idx.iterrows():
            for q in (1, 2, 3, 4, 5):
                if pd.notna(r.get(q)):
                    rows.append({"date": date.date(), "bracket": b, "quintile": int(q), "idx": round(r[q], 2)})
    pd.DataFrame(rows).to_csv(path, index=False)
    print(f"  -> wrote {os.path.basename(path)} ({len(rows)} rows)")


def main():
    d = load()
    print(f"Loaded {d.date.nunique()} quarters ({d.date.min():%Y-%m}..{d.date.max():%Y-%m}); "
          f"{len(d):,} employed records, {int(d.recent.sum()):,} recent hires")
    build(d, STOCK_BRACKETS, False, os.path.join(OUT, "canaries_lfs_stock.csv"), "STOCK (all employed)")
    build(d, HIRE_BRACKETS, True, os.path.join(OUT, "canaries_lfs_hiring.csv"), "HIRING (recent hires)")


if __name__ == "__main__":
    main()
