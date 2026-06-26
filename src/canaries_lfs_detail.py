"""Canaries (LFS microdata) — detail + WFH robustness.

Three extensions to canaries_lfs.py, all from the same LFS person-file load:

  1. AGE GRADIENT — which age cuts are hit hardest. Employment change since 2022 Q4 by fine
     age band, in the most-exposed quintile (Q5) vs the least (Q1).  -> canaries_lfs_age_gradient.csv
  2. ROLES — which occupations are shedding young (22-25) workers. Per 4-digit SOC, average
     quarterly employment in 2021-22 vs 2025-26, for AI-exposed jobs (Q4-Q5), with each role's
     AEI automation tag and home-working propensity.  -> canaries_lfs_roles.csv
  3. WFH CONTROL — the confounder test. The most-exposed jobs are also the home-workable ones
     (Q5 ~39% mainly-WFH vs Q1 ~5%), so "it's just remote work, not AI" is a live story. We
     re-run the young (22-25) Q5-vs-Q1 employment index among workers who are NOT mainly home-
     based (on-site), where the WFH channel is shut off by construction. If Q5 still falls
     relative to Q1, the decline isn't a working-from-home artefact.  -> canaries_lfs_wfh_control.csv

Run: python src/canaries_lfs_detail.py   (after the LFS files are in data/canaries/lfs/)
"""
import os
import pandas as pd
from canaries_lfs import load, BASE, OUT, ROOT

AGE_BANDS = [("16-21", 16, 21), ("22-25", 22, 25), ("26-29", 26, 29),
             ("30-34", 30, 34), ("35-49", 35, 49), ("50-64", 50, 64)]
PRE, POST = (2021, 2022), (2025, 2026)        # pooled windows either side of the AI take-off
MIN_PRE_N = 40                                 # min unweighted young records in PRE (noise floor)


def idx_series(sub):
    """4Q-rolling weighted employment for a row-subset, indexed to 2022 Q4 = 100."""
    roll = sub.groupby("date").wt.sum().sort_index().rolling(4, min_periods=2).mean()
    return roll / roll.loc[BASE] * 100


def main():
    d = load()
    titles = (pd.read_csv(os.path.join(ROOT, "reference", "soc2020_isco08_crosswalk.csv"))
              .drop_duplicates("SOC2020").set_index("SOC2020")["SOC2020_title"])
    expo = pd.read_csv(os.path.join(OUT, "occupation_exposure_quintiles.csv")).rename(
        columns={"Unnamed: 0": "soc"}).set_index("soc")["exposure"]
    wfh_prop = d.groupby("soc").apply(lambda g: (g.wt * g.wfh).sum() / g.wt.sum() * 100)

    # 1. AGE GRADIENT — % change since 2022 Q4 by age band, Q5 vs Q1
    rows = []
    for lab, lo, hi in AGE_BANDS:
        r = {"band": lab}
        for q in (1, 5):
            s = idx_series(d[(d.quintile == q) & (d.age >= lo) & (d.age <= hi)]).dropna()
            r[f"Q{q}"] = round(s.iloc[-1] - 100, 1) if len(s) else None
        rows.append(r)
    grad = pd.DataFrame(rows)
    grad.to_csv(os.path.join(OUT, "canaries_lfs_age_gradient.csv"), index=False)
    print("Age gradient — employment % change since 2022 Q4 (most-exposed Q5 vs least Q1):")
    print(grad.to_string(index=False), "\n")

    # 2. ROLES — young (22-25) employment, 2021-22 vs 2025-26, AI-exposed occupations
    y = d[(d.age >= 22) & (d.age <= 25)].copy()
    y["win"] = y.date.dt.year.map(lambda yr: "pre" if yr in PRE else ("post" if yr in POST else None))
    yw = y.dropna(subset=["win"])
    npre = yw[yw.win == "pre"].groupby("soc").size()
    g = yw.groupby(["soc", "win", "date"]).wt.sum().groupby(level=["soc", "win"]).mean().unstack("win")
    g = g.dropna(subset=["pre", "post"]).join(npre.rename("pre_n"))
    g = g[(g.pre_n >= MIN_PRE_N)]
    g["pct"] = (g.post / g.pre - 1) * 100
    qmap = pd.read_csv(os.path.join(OUT, "occupation_exposure_quintiles.csv")).rename(
        columns={"Unnamed: 0": "soc"}).set_index("soc")["quintile"]
    g["quintile"] = qmap.reindex(g.index)
    g = g[g.quintile >= 4]                                     # AI-exposed only
    g["aitype"] = d.drop_duplicates("soc").set_index("soc")["aitype"].reindex(g.index)
    g["exposure"] = expo.reindex(g.index)
    g["wfh_prop"] = wfh_prop.reindex(g.index).round(0)
    g["title"] = [titles.get(s, str(s)) for s in g.index]
    roles = g.reset_index()[["soc", "title", "quintile", "exposure", "aitype", "wfh_prop",
                             "pre", "post", "pre_n", "pct"]].sort_values("pct")
    roles.round(1).to_csv(os.path.join(OUT, "canaries_lfs_roles.csv"), index=False)
    print(f"Young-worker roles ({len(roles)} exposed occupations, 2021-22 -> 2025-26):")
    print("  biggest FALLS:")
    for _, r in roles.head(6).iterrows():
        print(f"    {r.pct:+6.1f}%  {r.title[:42]:42s}  WFH {r.wfh_prop:.0f}%  {r.aitype or '-'}")
    print("  biggest RISES:")
    for _, r in roles.tail(4).iloc[::-1].iterrows():
        print(f"    {r.pct:+6.1f}%  {r.title[:42]:42s}  WFH {r.wfh_prop:.0f}%  {r.aitype or '-'}")

    # 3. WFH CONTROL — young 22-25 Q5 vs Q1, on-site (not mainly-home) vs home-based
    yng = d[(d.age >= 22) & (d.age <= 25)]
    out = {}
    for wf, name in [(0, "onsite"), (1, "home")]:
        for q in (1, 5):
            s = idx_series(yng[(yng.wfh == wf) & (yng.quintile == q)])
            out[f"{name}_Q{q}"] = s
    wfhc = pd.DataFrame(out).round(2)
    wfhc.to_csv(os.path.join(OUT, "canaries_lfs_wfh_control.csv"))
    last = wfhc.dropna(subset=["onsite_Q1", "onsite_Q5"]).iloc[-1]
    # overall (all WFH statuses) gap for comparison
    allg = {q: idx_series(yng[yng.quintile == q]).dropna().iloc[-1] for q in (1, 5)}
    print("\nWFH control — young (22-25) employment vs 2022 Q4:")
    print(f"  ALL workers:     Q5 {allg[5]-100:+.1f}%   Q1 {allg[1]-100:+.1f}%   gap {allg[5]-allg[1]:+.1f} pts")
    print(f"  ON-SITE only:    Q5 {last.onsite_Q5-100:+.1f}%   Q1 {last.onsite_Q1-100:+.1f}%   "
          f"gap {last.onsite_Q5-last.onsite_Q1:+.1f} pts  <- WFH channel shut off")
    print("\nWrote canaries_lfs_age_gradient.csv, canaries_lfs_roles.csv, canaries_lfs_wfh_control.csv")


if __name__ == "__main__":
    main()
