"""
UK Canaries v1.1 (demand-side) — online job-advert volumes by occupational AI-exposure QUINTILE.

The real Canaries study tracks EMPLOYMENT by age x occupation x firm in ADP payroll microdata
(not public in the UK). This is the buildable demand-side analogue: monthly ONLINE JOB-ADVERT
counts by 4-digit SOC 2020 (ONS 'Textkernel New Online Job Adverts', Jan 2018-present), with each
occupation assigned an AI-exposure score, sorted into advert-weighted QUINTILES (mirroring the
Canaries Q1..Q5 design), and tracked relative to the eve of ChatGPT. It answers: is hiring DEMAND
in the most AI-exposed occupations diverging from the least-exposed since late 2022?

Exposure scores (v1.1, precise): ILO 2025 GenAI task index (mean GPT-4o automation score, 0-1)
keyed to ISCO-08, joined to UK SOC 2020 4-digit via the ONS SOC2020<->ISCO-08 coding-index
crosswalk (modal ISCO per SOC group). Replaces the coarse 2-digit high/low split of v1.

What this is NOT (honest gaps vs the real method): adverts != employment (demand, not stock);
NO worker-age / entry-level cut (adverts carry no age -> forward Adzuna API / Lightcast); NO firm
panel / firm-time FE (-> v2 ASHE-secure flagship). See CANARIES_METHOD.md / FEASIBILITY.md.

Run: python src/canaries.py  ->  data/canaries/*.csv, charts/canaries/*.png
"""
import os, sys, io, pandas as pd, numpy as np, matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ons_fetch import resolve_ons_current_xlsx, fetch_bytes
import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "canaries"); CHARTS = os.path.join(ROOT, "charts", "canaries")
REF = os.path.join(ROOT, "reference")
os.makedirs(DATA, exist_ok=True); os.makedirs(CHARTS, exist_ok=True)
plt.rcParams.update({"figure.dpi": 130, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

BASE = "2022-10-01"   # eve of ChatGPT (Nov 2022)
TK_PAGE = "https://www.ons.gov.uk/economy/economicoutputandproductivity/output/datasets/textkernelnewonlinejobadverts"

# ---- 1. exposure score per SOC2020 4-digit: SOC2020 -> ISCO08 (modal) -> ILO mean_gpt4o ----
cw = pd.read_csv(os.path.join(REF, "soc2020_isco08_crosswalk.csv"))[["SOC2020", "ISCO08", "isco_share"]]
ilo = pd.read_csv(os.path.join(REF, "ilo2025_isco08_occupation_exposure.csv"))[["isco4", "mean_gpt4o"]]
expo = cw.merge(ilo, left_on="ISCO08", right_on="isco4", how="left").rename(columns={"mean_gpt4o": "exposure"})
expo = expo.dropna(subset=["exposure"]).set_index("SOC2020")
# 64 SOC groups map to their modal ISCO with <50% share (lossy) — flagged, not dropped.
n_lossy = int((expo.isco_share < 0.5).sum())

# ---- 2. Textkernel 4-digit SOC monthly advert counts ----
url = resolve_ons_current_xlsx(TK_PAGE)
raw = fetch_bytes(url, "textkernel.xlsx")
wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
rows = list(wb["3.Occupation 4-Digit NSA"].iter_rows(values_only=True))
header = rows[4]
dates = pd.to_datetime([r[0] for r in rows[5:] if r[0]])
series = {}
for ci, name in enumerate(header):
    if ci < 2 or not name: continue
    try: code = int(str(name).strip()[:4])
    except ValueError: continue
    if code in expo.index: series[code] = [r[ci] for r in rows[5:] if r[0]]
adv = pd.DataFrame(series, index=dates).apply(pd.to_numeric, errors="coerce")
adv.index.name = "date"

# ---- 3. advert-weighted exposure quintiles (Q1 least exposed ... Q5 most) ----
size = adv.mean()                                   # avg monthly adverts per occupation = weight
occ = pd.DataFrame({"exposure": expo.loc[size.index, "exposure"], "size": size}).dropna()
occ = occ.sort_values("exposure")
occ["cum_share"] = occ["size"].cumsum() / occ["size"].sum()
occ["quintile"] = (np.minimum((occ["cum_share"] * 5).astype(int), 4) + 1)   # 1..5
occ.to_csv(os.path.join(DATA, "occupation_exposure_quintiles.csv"))

def basket(q): return adv[occ.index[occ.quintile == q]].sum(axis=1)
out = pd.DataFrame({"Q5_most_exposed": basket(5), "Q1_least_exposed": basket(1)})
# 12-month trailing average (strip vacancy seasonality + dampen ONS's Oct2025-Feb2026 imputation)
for c in list(out.columns): out[c + "_smooth"] = out[c].rolling(12, min_periods=12).mean()
out["Q5_index"] = out.Q5_most_exposed_smooth / out.loc[BASE, "Q5_most_exposed_smooth"] * 100
out["Q1_index"] = out.Q1_least_exposed_smooth / out.loc[BASE, "Q1_least_exposed_smooth"] * 100
out["Q5_minus_Q1"] = out.Q5_index - out.Q1_index
out.to_csv(os.path.join(DATA, "canaries_demand_by_exposure.csv"))
out = out.dropna(subset=["Q5_index", "Q1_index"])
latest = out.index.max()

print(f"Canaries v1.1 (demand-side, 4-digit SOC quintiles) — base {BASE}=100, latest {latest.date()}")
print(f"  {len(occ)} occupations scored ({n_lossy} with lossy ISCO mapping)")
print(f"  Q5 most-exposed adverts: {out.loc[latest,'Q5_index']-100:+.1f}% vs base")
print(f"  Q1 least-exposed adverts:{out.loc[latest,'Q1_index']-100:+.1f}% vs base")
print(f"  gap (Q5-Q1):             {out.loc[latest,'Q5_minus_Q1']:+.1f} index pts")
top = occ[occ.quintile == 5].join(expo[["isco_share"]]).sort_values("exposure", ascending=False)
top_titles = cw.merge(pd.read_csv(os.path.join(REF,"soc2020_isco08_crosswalk.csv"))[["SOC2020","SOC2020_title"]], on="SOC2020")
names = pd.read_csv(os.path.join(REF,"soc2020_isco08_crosswalk.csv")).set_index("SOC2020")["SOC2020_title"]
print("  most-exposed (Q5) e.g.:", ", ".join(names.get(c,str(c)) for c in top.head(4).index))

# ---- chart 1: Q5 vs Q1 advert index ----
fig, ax = plt.subplots(figsize=(8.5,4.7))
ax.plot(out.index, out.Q5_index, lw=2.2, color="#c0392b", label="Most AI-exposed occupations (Q5)")
ax.plot(out.index, out.Q1_index, lw=2.2, color="#2a6", label="Least AI-exposed occupations (Q1)")
ax.axhline(100, color="#999", lw=0.8, ls="--")
ax.axvline(pd.Timestamp("2022-11-01"), color="k", lw=0.9, ls=":")
ax.text(pd.Timestamp("2022-12-01"), ax.get_ylim()[1]*0.96, "ChatGPT", fontsize=8, va="top")
ax.set_title("UK Canaries v1.1: job-advert demand by AI-exposure quintile", fontweight="bold")
ax.set_ylabel(f"Advert volume index, 12m avg ({BASE[:7]} = 100)")
ax.legend(fontsize=9, frameon=False)
fig.text(0.01,0.01,"Source: ONS 'Textkernel New Online Job Adverts', 4-digit SOC 2020 x ILO 2025 GenAI exposure. Demand (vacancies), not employment; no age cut.", fontsize=7, color="#666")
fig.tight_layout(rect=(0,0.03,1,1)); fig.savefig(os.path.join(CHARTS,"1_demand_by_exposure.png")); plt.close(fig)

# ---- chart 2: relative gap ----
fig, ax = plt.subplots(figsize=(8.5,4.2))
g = out.Q5_minus_Q1
ax.plot(out.index, g, lw=2, color="#36c")
ax.fill_between(out.index, g, 0, where=g<0, color="#c0392b", alpha=0.18)
ax.fill_between(out.index, g, 0, where=g>=0, color="#2a6", alpha=0.18)
ax.axhline(0, color="#333", lw=0.8); ax.axvline(pd.Timestamp("2022-11-01"), color="k", lw=0.9, ls=":")
ax.set_title("Most-exposed advert demand relative to least-exposed", fontweight="bold")
ax.set_ylabel("Q5 index − Q1 index (pts)")
ax.text(pd.Timestamp("2022-12-01"), ax.get_ylim()[1]*0.9, "ChatGPT", fontsize=8)
fig.text(0.01,0.01,"Below 0 = most-exposed hiring demand lagging least-exposed since the 2022-10 base.", fontsize=7, color="#666")
fig.tight_layout(rect=(0,0.03,1,1)); fig.savefig(os.path.join(CHARTS,"2_relative_gap.png")); plt.close(fig)

print("  charts ->", CHARTS)
