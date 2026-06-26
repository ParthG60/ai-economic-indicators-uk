"""Canaries (LFS longitudinal) — flows: displacement vs non-hiring.

The stock cut (canaries_lfs.py) shows employment of young workers in AI-exposed jobs is lower
since ChatGPT. A stock can fall two ways with opposite meanings: young workers are PUSHED OUT
of exposed jobs (displacement), or they are NEVER HIRED IN (the entry door closing). Stanford's
thesis is about the hiring margin. Only longitudinal data can tell them apart.

The LFS longitudinal files follow the same person across waves (5-quarter = a year apart;
2-quarter = consecutive quarters). Wave variables are suffixed 1..5 (SOC20M1..5, ILODEFR1..5,
AGE1..5), with LGWT* the longitudinal weight. We compare each young worker's occupation and
employment status at the start vs the end of their panel, and ask, before vs after ChatGPT:

  EXIT  rate from exposed (Q5) jobs   = displacement   (start in Q5, end not in Q5)
  ENTRY rate into exposed (Q5) jobs   = hiring margin   (start not in Q5, end in Q5)

If the post-ChatGPT decline is driven by a falling ENTRY rate rather than a rising EXIT rate,
the mechanism is non-hiring, not displacement, matching the Stanford entry-level story.

Headline uses the 5-quarter (12-month) panel: PRE = 2021 starts (transitions end pre-ChatGPT),
POST = 2024 starts (fully post). 2-quarter (3-month) panel reported as short-run robustness.

Run: python src/canaries_lfs_flows.py
"""
import glob, io, os, re, zipfile
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LFS = os.path.join(ROOT, "data", "canaries", "lfs")
OUT = os.path.join(ROOT, "data", "canaries")
QUINT = os.path.join(OUT, "occupation_exposure_quintiles.csv")
BANDS = {"22-25": (22, 25), "35-49": (35, 49)}
PRE5, POST5 = [2021], [2024]                 # 5q cohort start-years (12-month transitions)
PRE2, POST2 = [2021, 2022], [2024, 2025]     # 2q cohort start-years (3-month transitions)


def _open(path):
    z = zipfile.ZipFile(path)
    inner = [n for n in z.namelist() if n.lower().endswith(".dta")][0]
    return io.BytesIO(z.open(inner).read()), os.path.basename(inner)


def load_long():
    qmap = pd.read_csv(QUINT).rename(columns={"Unnamed: 0": "soc"}).assign(
        soc=lambda d: d.soc.astype(int)).set_index("soc")["quintile"]
    seen, rows = set(), []
    for f in sorted(glob.glob(os.path.join(LFS, "*.zip"))):
        buf, name = _open(f)
        m = re.search(r"lgwt\d+_(\dq)_(\w{4})_(\w{4})", name.lower())
        if not m:
            continue
        hz, s, e = m.group(1), m.group(2), m.group(3)
        if (hz, s, e) in seen:                       # skip duplicate downloads
            continue
        seen.add((hz, s, e))
        up = {c.upper(): c for c in pd.io.stata.StataReader(buf).variable_labels().keys()}
        waves = sorted(int(k[6:]) for k in up if re.fullmatch(r"SOC20M\d", k))
        a, b = waves[0], waves[-1]
        wt = next((up[c] for c in up if c.startswith("LGWT")), None)
        cols = {up[f"SOC20M{a}"]: "s0", up[f"SOC20M{b}"]: "s1", up[f"ILODEFR{a}"]: "i0",
                up[f"ILODEFR{b}"]: "i1", up[f"AGE{a}"]: "age", wt: "wt"}
        buf.seek(0)
        d = pd.read_stata(buf, columns=list(cols), convert_categoricals=False).rename(columns=cols)
        for c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
        d = d.dropna(subset=["wt", "age"])
        d["emp0"] = (d.i0 == 1) & d.s0.notna()
        d["emp1"] = (d.i1 == 1) & d.s1.notna()
        d["q0"] = d.s0.map(qmap)
        d["q1"] = d.s1.map(qmap)
        d["hz"] = hz
        d["syear"] = 2000 + int(s[2:])
        rows.append(d[["hz", "syear", "age", "wt", "emp0", "emp1", "q0", "q1"]])
    return pd.concat(rows, ignore_index=True)


def rates(d, hz, years, lo, hi):
    s = d[(d.hz == hz) & d.syear.isin(years) & (d.age >= lo) & (d.age <= hi)]
    W = lambda m: float(s.wt[m].sum())
    inQ5 = s.emp0 & (s.q0 == 5)
    base = W(inQ5)
    pool = W(~inQ5)                                   # candidates to enter Q5
    return {
        "n_start_Q5": int(inQ5.sum()),
        "exit_nonemp": W(inQ5 & ~s.emp1) / base * 100,
        "exit_to_lesser": W(inQ5 & s.emp1 & (s.q1 != 5)) / base * 100,
        "exit_total": W(inQ5 & ((~s.emp1) | (s.q1 != 5))) / base * 100,
        "retained_Q5": W(inQ5 & s.emp1 & (s.q1 == 5)) / base * 100,
        "entry_rate": W(~inQ5 & s.emp1 & (s.q1 == 5)) / pool * 100,
    }


def main():
    d = load_long()
    print(f"Loaded {len(d):,} linked person-records "
          f"(2q {int((d.hz=='2q').sum()):,} | 5q {int((d.hz=='5q').sum()):,})\n")

    recs = []
    for hz, pre, post in [("5q", PRE5, POST5), ("2q", PRE2, POST2)]:
        horizon = "12-month" if hz == "5q" else "3-month"
        print(f"===== {hz.upper()} panel ({horizon} transitions) =====")
        for band, (lo, hi) in BANDS.items():
            rp, rq = rates(d, hz, pre, lo, hi), rates(d, hz, post, lo, hi)
            print(f"\n  Age {band}  (start in most-exposed Q5; n {rp['n_start_Q5']}->{rq['n_start_Q5']})")
            print(f"    EXIT from exposed (total)   PRE {rp['exit_total']:5.1f}%   POST {rq['exit_total']:5.1f}%   d {rq['exit_total']-rp['exit_total']:+.1f}")
            print(f"      | to non-employment       PRE {rp['exit_nonemp']:5.1f}%   POST {rq['exit_nonemp']:5.1f}%   d {rq['exit_nonemp']-rp['exit_nonemp']:+.1f}")
            print(f"      | to a less-exposed job    PRE {rp['exit_to_lesser']:5.1f}%   POST {rq['exit_to_lesser']:5.1f}%   d {rq['exit_to_lesser']-rp['exit_to_lesser']:+.1f}")
            print(f"    ENTRY into exposed          PRE {rp['entry_rate']:5.2f}%   POST {rq['entry_rate']:5.2f}%   d {rq['entry_rate']-rp['entry_rate']:+.2f}")
            for period, r in [("pre", rp), ("post", rq)]:
                recs.append(dict(horizon=hz, band=band, period=period, **r))
        print()
    pd.DataFrame(recs).round(2).to_csv(os.path.join(OUT, "canaries_lfs_flows.csv"), index=False)
    print("Wrote canaries_lfs_flows.csv")


if __name__ == "__main__":
    main()
