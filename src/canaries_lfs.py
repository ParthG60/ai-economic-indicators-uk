"""Canaries (LFS microdata) — the faithful Stanford replication, now possible.

Stanford's Canaries headline is employment by AGE x AI-EXPOSURE, indexed to the eve of
ChatGPT: among 22-25-year-olds, employment in the most AI-exposed occupations falls while
older workers barely move. Until now the UK tracker only had APS *annual aggregates* with no
age cut. The LFS EUL quarterly person files (data/canaries/lfs/) carry single-year AGE x
4-digit SOC2020 x person weight, so we can finally cut employment by age x exposure directly.

This pipeline reads the LFS quarterly person files (Stata .dta inside the UKDS zips), tags
each worker with their occupation's AI-exposure quintile and (for exposed jobs) whether AI
tends to AUTOMATE or AUGMENT the task (Anthropic Economic Index), then builds:

  1. canaries_lfs_age_exposure.csv  — employment index by age band x exposure quintile
     (4Q-rolling, base 2022 Q4 = 100). The headline: young (22-25) Q5 vs Q1 vs a 35-49 control.
  2. canaries_lfs_young_autoaug.csv — young (22-25) employment index in automation- vs
     augmentation-type exposed jobs (isolates *AI-related* employment).
  3. canaries_lfs_summary.csv       — latest index values for the dashboard cards.

Employment level = sum of person weights (PWT*), i.e. the grossed-up headcount estimate.
Baseline = 2022 Q4, whose trailing 4-quarter mean spans calendar 2022 (ChatGPT launched end
Nov 2022, so the baseline is effectively pre-takeoff). 4-quarter rolling removes LFS
seasonality and damps the 2023-24 response-rate noise.

Run: python src/canaries_lfs.py
"""
import glob, io, os, re, zipfile
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LFS_DIR = os.path.join(ROOT, "data", "canaries", "lfs")
OUT = os.path.join(ROOT, "data", "canaries")
QUINTILES = os.path.join(OUT, "occupation_exposure_quintiles.csv")
AEI = os.path.join(ROOT, "reference", "aei_automation_by_soc2020.csv")

CALENDAR_Q = {"jm": 1, "aj": 2, "js": 3, "od": 4}
Q_END = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}
BASE = pd.Timestamp(2022, 12, 31)            # eve of ChatGPT (trailing 4Q = calendar 2022)
BANDS = {"22-25": (22, 25), "35-49": (35, 49)}   # young (paper's cut) vs prime-age control
T_AUTO, T_AUG, MANUAL = 0.60, 0.40, {5, 8, 9}    # AEI thresholds; drop manual major groups


def _open_dta(path):
    if path.lower().endswith(".zip"):
        zf = zipfile.ZipFile(path)
        inner = [n for n in zf.namelist() if n.lower().endswith(".dta")][0]
        return io.BytesIO(zf.open(inner).read()), os.path.basename(inner)
    with open(path, "rb") as fh:
        return io.BytesIO(fh.read()), os.path.basename(path)


def _read_cols(buf, want):
    buf.seek(0)
    up = {c.upper(): c for c in pd.io.stata.StataReader(buf).variable_labels().keys()}
    cols, names = [], {}
    for key, p in want.items():
        hit = up.get(p) or next((up[c] for c in sorted(up) if c.startswith(p)), None)
        if hit:
            cols.append(hit); names[hit] = key
    buf.seek(0)
    return pd.read_stata(buf, columns=cols, convert_categoricals=False).rename(columns=names)


def load():
    files = sorted(glob.glob(os.path.join(LFS_DIR, "*.zip")) + glob.glob(os.path.join(LFS_DIR, "*.dta")))
    q = pd.read_csv(QUINTILES).rename(columns={"Unnamed: 0": "soc"})
    qmap = q.assign(soc=q.soc.astype(int)).set_index("soc")["quintile"]

    # auto/aug tag: exposed (Q4-Q5), non-manual, clear AEI cases only
    aei = pd.read_csv(AEI).set_index("SOC2020")["aei_automation_share"]
    exposed = [s for s in qmap.index[qmap >= 4] if (s // 1000) not in MANUAL]
    auto = aei.reindex(exposed)
    typemap = {}
    for s, a in auto.dropna().items():
        if a >= T_AUTO: typemap[s] = "automation"
        elif a <= T_AUG: typemap[s] = "augmentation"

    want = {"soc": "SOC20M", "age": "AGE", "ilo": "ILODEFR", "wt": "PWT", "home": "HOME"}
    parts = []
    for f in files:
        buf, inner = _open_dta(f)
        m = re.search(r"lfsp_([a-z]{2})(\d{2})", inner.lower())   # person files, calendar quarters
        if not m or m.group(1) not in CALENDAR_Q:
            continue
        d = _read_cols(buf, want)
        for c in ("soc", "age", "ilo", "wt", "home"):
            d[c] = pd.to_numeric(d.get(c), errors="coerce")
        d = d[d.ilo == 1].dropna(subset=["soc", "age", "wt"])
        d["soc"] = d.soc.astype(int)
        d["quintile"] = d.soc.map(qmap)
        d["aitype"] = d.soc.map(typemap)
        d["wfh"] = (d.home == 1).astype(int)            # HOME==1 = mainly works from own home
        d["date"] = pd.Timestamp(int("20" + m.group(2)), *Q_END[CALENDAR_Q[m.group(1)]])
        parts.append(d.dropna(subset=["quintile"])[["date", "soc", "quintile", "aitype", "age", "wt", "wfh"]])
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def index_by(d, key, lo, hi):
    """4Q-rolling weighted employment for ages lo..hi, by `key`, indexed to 2022 Q4 = 100."""
    sub = d[(d.age >= lo) & (d.age <= hi)].dropna(subset=[key])
    lvl = sub.groupby(["date", key]).wt.sum().unstack(key).sort_index()
    roll = lvl.rolling(4, min_periods=2).mean()
    return roll / roll.loc[BASE] * 100


def main():
    d = load()
    if d.empty:
        print("No LFS microdata in data/canaries/lfs/ (EUL files are local-only). "
              "Skipping — committed aggregate CSVs are kept.")
        return
    print(f"Loaded {d.date.nunique()} quarters, {len(d):,} employed person-records "
          f"({d.date.min():%Y-%m}..{d.date.max():%Y-%m})\n")

    # 1. age x exposure-quintile employment index
    frames = []
    for band, (lo, hi) in BANDS.items():
        idx = index_by(d, "quintile", lo, hi)
        idx.columns = [f"Q{int(c)}" for c in idx.columns]
        idx.insert(0, "band", band)
        frames.append(idx)
        last = idx.dropna().iloc[-1]
        print(f"[{band}] employment vs 2022 Q4:  Q5 {last.Q5-100:+.1f}%   Q1 {last.Q1-100:+.1f}%   "
              f"Q5-Q1 {last.Q5-last.Q1:+.1f} pts")
    age_exp = pd.concat(frames).round(2)
    age_exp.to_csv(os.path.join(OUT, "canaries_lfs_age_exposure.csv"))

    # 2. young (22-25) automation- vs augmentation-type employment index
    lo, hi = BANDS["22-25"]
    aa = index_by(d, "aitype", lo, hi).round(2)
    aa.to_csv(os.path.join(OUT, "canaries_lfs_young_autoaug.csv"))
    aal = aa.dropna().iloc[-1]
    print(f"\n[22-25, AI-exposed] automation-type {aal.automation-100:+.1f}%   "
          f"augmentation-type {aal.augmentation-100:+.1f}%   "
          f"gap {aal.augmentation-aal.automation:+.1f} pts (vs 2022 Q4)")

    # 3. summary for dashboard cards
    yexp = age_exp[age_exp.band == "22-25"].dropna().iloc[-1]
    pexp = age_exp[age_exp.band == "35-49"].dropna().iloc[-1]
    pd.DataFrame([
        {"metric": "young_q5", "value": yexp.Q5 - 100},
        {"metric": "young_q1", "value": yexp.Q1 - 100},
        {"metric": "young_gap", "value": yexp.Q5 - yexp.Q1},
        {"metric": "prime_q5", "value": pexp.Q5 - 100},
        {"metric": "young_auto", "value": aal.automation - 100},
        {"metric": "young_aug", "value": aal.augmentation - 100},
        {"metric": "asof", "value": age_exp.dropna().index.max()},
    ]).to_csv(os.path.join(OUT, "canaries_lfs_summary.csv"), index=False)
    print("\nWrote canaries_lfs_age_exposure.csv, canaries_lfs_young_autoaug.csv, canaries_lfs_summary.csv")


if __name__ == "__main__":
    main()
