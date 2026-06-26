"""
UK Canaries v2 (employment-based) — ACTUAL EMPLOYMENT by occupational AI-exposure quintile.

The big upgrade over v1.1 (adverts): this uses real EMPLOYMENT, not hiring demand. Stanford's
Canaries tracks employment by age x occupation x firm in ADP payroll microdata. We can't get the
age/firm cut for free (needs ONS SecureLab ASHE), but we CAN get real employment by 4-digit
occupation over time, for free, from the ONS Annual Population Survey via the Nomis API.

Data:
- Employment: Nomis APS dataset NM_218 (employment by SOC2020, national, Count), calendar-year
  rolling periods Jan-Dec 2021..2025. Free public API, no key.
- Exposure: ILO 2025 GenAI task index (mean GPT-4o automation score) keyed to ISCO-08, joined to
  SOC2020 4-digit via the ONS coding-index crosswalk (modal ISCO) — same layer as v1.1.

Method: each 4-digit occupation gets an exposure score; occupations are sorted into employment-
weighted quintiles Q1 (least exposed) .. Q5 (most exposed); each quintile's total employment is
indexed to 2022 (the eve of ChatGPT, Nov 2022). Q5 vs Q1 = is EMPLOYMENT in the most AI-exposed
occupations diverging from the least-exposed since ChatGPT?

Honest gaps vs Stanford: still NO worker-age cut (the entry-level effect) and NO firm panel — both
need ASHE secure microdata (the planned v3). APS is a survey, so 4-digit cells are sampling-noisy;
quintile baskets (aggregates of ~80 occupations each) are far more robust than single occupations.

Run: python src/canaries_employment.py  ->  data/canaries/*.csv, charts/canaries/*.png
"""
import os, sys, io, requests, pandas as pd, numpy as np, matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "canaries"); CHARTS = os.path.join(ROOT, "charts", "canaries")
REF = os.path.join(ROOT, "reference")
os.makedirs(DATA, exist_ok=True); os.makedirs(CHARTS, exist_ok=True)
plt.rcParams.update({"figure.dpi": 130, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

BASE_YEAR = 2022   # eve of ChatGPT (Nov 2022)

# ---- 1. exposure score per SOC2020 4-digit (SOC2020 -> modal ISCO08 -> ILO mean_gpt4o) ----
cw = pd.read_csv(os.path.join(REF, "soc2020_isco08_crosswalk.csv"))[["SOC2020", "ISCO08", "isco_share"]]
ilo = pd.read_csv(os.path.join(REF, "ilo2025_isco08_occupation_exposure.csv"))[["isco4", "mean_gpt4o"]]
expo = (cw.merge(ilo, left_on="ISCO08", right_on="isco4", how="left")
          .dropna(subset=["mean_gpt4o"]).set_index("SOC2020")["mean_gpt4o"])
names = pd.read_csv(os.path.join(REF, "soc2020_isco08_crosswalk.csv")).set_index("SOC2020")["SOC2020_title"]

# ---- 2. APS employment by 4-digit SOC2020, national, Count, calendar-year periods ----
def fetch_aps_employment():
    u = ("https://www.nomisweb.co.uk/api/v01/dataset/NM_218_1.data.csv?geography=2092957697"
         "&jtype=0&ftpt=0&etype=0&c_sex=0&measure=1&measures=20100"
         "&select=date_name,soc2020_full_name,obs_value")
    df = pd.read_csv(io.StringIO(requests.get(u, timeout=120).text)).dropna(subset=["OBS_VALUE"])
    df["soc"] = df.SOC2020_FULL_NAME.str.extract(r"^(\d{4}) :")[0]
    df = df.dropna(subset=["soc"]); df["soc"] = df.soc.astype(int)
    df = df[df.DATE_NAME.str.startswith("Jan")]                       # Jan-Dec calendar years
    df["year"] = df.DATE_NAME.str.extract(r"Dec (\d{4})")[0].astype(int)
    return df.pivot_table(index="year", columns="soc", values="OBS_VALUE")

emp = fetch_aps_employment()
years = sorted(emp.index)
base = BASE_YEAR if BASE_YEAR in years else years[0]

# ---- 3. employment-weighted exposure quintiles (base-year employment weights) ----
socs = [s for s in emp.columns if s in expo.index]
occ = pd.DataFrame({"exposure": expo.loc[socs], "w": emp.loc[base, socs]}).dropna().sort_values("exposure")
occ["cum"] = occ.w.cumsum() / occ.w.sum()
occ["quintile"] = np.minimum((occ["cum"] * 5).astype(int), 4) + 1
occ["title"] = [names.get(s, str(s)) for s in occ.index]
occ.to_csv(os.path.join(DATA, "employment_exposure_quintiles.csv"))

def basket(q, yr): return emp.loc[yr, occ.index[occ.quintile == q]].sum()
out = pd.DataFrame({"year": years})
for q in (1, 5):
    bv = basket(q, base)
    out[f"Q{q}_index"] = [basket(q, y) / bv * 100 for y in years]
out["Q5_minus_Q1"] = out.Q5_index - out.Q1_index
out.to_csv(os.path.join(DATA, "canaries_employment_by_exposure.csv"), index=False)

latest = years[-1]
print(f"Canaries v2 (employment, 4-digit SOC2020 quintiles) — base {base}=100, latest {latest}")
print(f"  {len(occ)} occupations, employment {emp.loc[latest].sum():,.0f} (latest)")
print(f"  Q5 most-exposed employment: {out.Q5_index.iloc[-1]-100:+.1f}% vs {base}")
print(f"  Q1 least-exposed employment:{out.Q1_index.iloc[-1]-100:+.1f}% vs {base}")
print(f"  gap (Q5-Q1):                {out.Q5_minus_Q1.iloc[-1]:+.1f} index pts")
print("  most-exposed (Q5) e.g.:", ", ".join(occ[occ.quintile == 5].sort_values("exposure", ascending=False).title.head(4)))

# ---- chart: Q5 vs Q1 employment index ----
fig, ax = plt.subplots(figsize=(8.5, 4.7))
ax.plot(out.year, out.Q5_index, "o-", lw=2.4, color="#c0392b", label="Most AI-exposed occupations (Q5)")
ax.plot(out.year, out.Q1_index, "o-", lw=2.4, color="#2a6", label="Least AI-exposed occupations (Q1)")
ax.axhline(100, color="#999", lw=0.8, ls="--")
ax.set_title("UK Canaries v2: EMPLOYMENT by AI-exposure quintile", fontweight="bold")
ax.set_ylabel(f"Employment index ({base} = 100)"); ax.set_xticks(out.year)
ax.legend(fontsize=9, frameon=False)
fig.text(0.01, 0.01, "Source: ONS Annual Population Survey (Nomis NM_218), employment by 4-digit SOC2020 x ILO 2025 GenAI exposure. No age/firm cut (needs ASHE).", fontsize=7, color="#666")
fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(os.path.join(CHARTS, "3_employment_by_exposure.png")); plt.close(fig)
print("  chart ->", os.path.join(CHARTS, "3_employment_by_exposure.png"))

# ---- 4. AEI automation vs augmentation (Stanford's key distinction) ----
# Among AI-exposed occupations, does AI tend to DO the task (automation, displacement risk) or
# ASSIST (augmentation)? Split exposed occupations by the Anthropic Economic Index automation share.
aei_path = os.path.join(REF, "aei_automation_by_soc2020.csv")
if os.path.exists(aei_path):
    aei = pd.read_csv(aei_path).set_index("SOC2020")["aei_automation_share"]
    # Q4+Q5 = most AI-exposed (by ILO score), EXCLUDING manual major groups (5 skilled trades,
    # 8 operatives, 9 elementary) — physical jobs the exposure crosswalk occasionally mis-rates
    # (e.g. telecoms installers). Keeps cognitive/clerical/sales/caring where AI exposure is real.
    MANUAL = {5, 8, 9}
    exp = occ[(occ.quintile >= 4) & (~(occ.index.to_series() // 1000).isin(MANUAL))].copy()
    exp["auto"] = aei.reindex(exp.index)
    exp = exp.dropna(subset=["auto"])
    # Tag only the CLEAR cases by ABSOLUTE automation score; DROP the messy 0.40-0.60 middle (0.5 is
    # 'balanced' usage, so anything near it is ambiguous — incl. Chief executives at 0.49). Sensitivity
    # check (see STATUS): augmentation growth (+7..+10%) and the augmentation>automation GAP (+4..+12pts)
    # are ROBUST to the cut; the automation ABSOLUTE change is NOT (flips -3.5%..+2.6%, small group) —
    # so we report the gap/augmentation, not 'automation fell'.
    T_AUTO, T_AUG = 0.60, 0.40
    grp = {"automation": exp.index[exp.auto >= T_AUTO], "augmentation": exp.index[exp.auto <= T_AUG]}
    aa_out = pd.DataFrame({"year": years})
    for label, idx in grp.items():
        bv = emp.loc[base, idx].sum()
        aa_out[label + "_index"] = [emp.loc[y, idx].sum() / bv * 100 for y in years]
    aa_out.to_csv(os.path.join(DATA, "canaries_employment_automation.csv"), index=False)
    print(f"  [AEI] exposed-occupation employment vs {base}: "
          f"automation-type {aa_out.automation_index.iloc[-1]-100:+.1f}% vs "
          f"augmentation-type {aa_out.augmentation_index.iloc[-1]-100:+.1f}%  "
          f"({len(grp['automation'])} vs {len(grp['augmentation'])} occupations)")
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    ax.plot(aa_out.year, aa_out.automation_index, "o-", lw=2.4, color="#c0392b", label="Automation-type (AI does the task)")
    ax.plot(aa_out.year, aa_out.augmentation_index, "o-", lw=2.4, color="#2a6", label="Augmentation-type (AI assists)")
    ax.axhline(100, color="#999", lw=0.8, ls="--"); ax.set_xticks(aa_out.year)
    ax.set_title("Among AI-exposed jobs: automation-type vs augmentation-type employment", fontweight="bold")
    ax.set_ylabel(f"Employment index ({base} = 100)"); ax.legend(fontsize=9, frameon=False)
    fig.text(0.01, 0.01, "Exposed occupations (top 40% ILO GenAI exposure) split by Anthropic Economic Index automation share. Source: ONS APS x ILO x AEI.", fontsize=7, color="#666")
    fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(os.path.join(CHARTS, "4_automation_vs_augmentation.png")); plt.close(fig)
    print("  chart ->", os.path.join(CHARTS, "4_automation_vs_augmentation.png"))

    # ---- 5. most-affected vs resilient exposed occupations (employment change base->latest) ----
    mv = occ[(occ.quintile >= 4) & (~(occ.index.to_series() // 1000).isin(MANUAL))].copy()
    mv["emp_base"] = emp.loc[base, mv.index]; mv["emp_latest"] = emp.loc[latest, mv.index]
    mv = mv[mv.emp_base >= 50000]                      # APS counts are persons; keep sizeable occupations (less noise)
    mv["chg_pct"] = (mv.emp_latest / mv.emp_base - 1) * 100
    mv["auto"] = aei.reindex(mv.index)
    mv = mv.dropna(subset=["auto", "chg_pct"])
    mv["type"] = np.where(mv.auto >= T_AUTO, "automation", np.where(mv.auto <= T_AUG, "augmentation", "mixed"))
    mv = mv[mv.type != "mixed"]                          # only clearly-tagged occupations
    mv[["title", "exposure", "auto", "type", "emp_base", "emp_latest", "chg_pct"]].sort_values("chg_pct").to_csv(
        os.path.join(DATA, "canaries_occupation_movers.csv"), index=False)
    print("  most-affected (exposed, biggest falls):", "; ".join(mv.sort_values("chg_pct").title.head(3)))
    print("  most-resilient (exposed, biggest rises):", "; ".join(mv.sort_values("chg_pct", ascending=False).title.head(3)))
