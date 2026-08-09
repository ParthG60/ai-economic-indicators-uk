"""
UK AI Adoption Monitor — builds tidy CSVs + charts from public UK survey data.

Mirrors Stanford's Adoption Monitor (firm + individual AI adoption over time).
Data is hand-curated from public UK sources (see FEASIBILITY.md / source URLs below);
survey series are not cleanly API-pullable, so the figures are seeded here and dated.

Run: python src/adoption_monitor.py
Outputs: data/adoption/*.csv, charts/adoption/*.png

NOTE on denominators: firm-adoption sources measure DIFFERENT things (16% DSIT strict ...
71% NBER exec panel ... 75% BoE finance-only). They are kept as separate series on purpose.
Do not chart them on one axis as if comparable.
"""
import os, pandas as pd, matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "adoption"); CHARTS = os.path.join(ROOT, "charts", "adoption")
os.makedirs(DATA, exist_ok=True); os.makedirs(CHARTS, exist_ok=True)
plt.rcParams.update({"figure.dpi": 130, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

# ---------------------------------------------------------------- 1. FIRM SPINE: ONS BICS
# Firm spine (% currently using >=1 AI technology). PRIMARY = ONS BICS headline on the
# 10+ EMPLOYEES basis, which ONS's "AI in UK businesses: 2023 to 2026" article (pub 20 Jul
# 2026) has made its canonical cut and runs to wave 159 / June 2026. Retained as HISTORICAL:
# the all-business bulletin headline (headline_all_pct, ONS stopped featuring it for 2026 —
# it only confirmed 25% all-business at Dec 2025) and the DSIT ad-hoc consistent-definition
# series (waves 92-147 only; no newer ad-hoc release). None = not published on that basis.
# Sources: ONS "AI in UK businesses: 2023 to 2026" (Figure 1) + BICS bulletins + DSIT AI ad-hoc
# tables (waves 92-147). https://www.ons.gov.uk/businessindustryandtrade/business/businessservices/articles/artificialintelligenceinukbusinesses/2023to2026
bics = pd.DataFrame({
    "date":      ["2023-09","2023-12","2024-03","2024-06","2024-09","2024-12","2025-03","2025-06","2025-09","2025-12","2026-03","2026-06"],
    "wave":      [92,98,105,111,117,123,129,135,141,147,153,159],
    "firm_10plus_pct":   [11.9,11.8,13.8,14.8,17.8,18.2,20.6,25.1,27.2,28.7,32.1,34.9], # ONS BICS headline, 10+ employees (canonical, to Jun-2026)
    "headline_all_pct":  [9,10,14,13,15,16,18,20,23,25,None,None],          # ONS bulletin headline, ALL businesses (historical; not published for 2026)
    "headline_250plus_pct":[18,None,24,25,30,28,31,None,None,44,None,None], # large firms (250+)
    "adhoc_using_pct":   [16.3,15.4,21.0,19.8,21.4,23.9,25.3,27.3,31.5,32.6,None,None],   # DSIT ad-hoc, consistent definition (waves 92-147 only)
    "adhoc_planning_pct":[18.9,17.0,20.6,19.1,19.7,20.6,23.4,25.6,25.6,29.5,None,None],
})
bics.to_csv(os.path.join(DATA,"bics_firm_adoption.csv"), index=False)

# BICS by sector (DSIT ad-hoc, % currently using AI)
bics_sector = pd.DataFrame({
    "date":["2023-09","2023-12","2024-03","2024-06","2024-09","2024-12","2025-03","2025-06","2025-09","2025-12"],
    "Adv Manufacturing":[22.0,17.9,31.5,29.8,32.8,29.4,30.0,28.7,42.4,48.3],
    "Creative":        [27.5,26.3,34.0,31.0,36.8,35.8,40.2,39.9,45.6,49.3],
    "Defence":         [10.2,13.1,4.8,14.0,3.9,13.2,15.0,16.1,28.2,35.2],
    "Digital & Tech":  [30.0,26.7,32.9,32.0,34.5,35.8,39.1,39.3,42.1,45.4],
    "Prof & Biz Svcs": [17.2,18.7,27.4,25.6,28.4,31.4,35.4,34.4,39.5,43.4],
    "All business":    [16.3,15.4,21.0,19.8,21.4,23.9,25.3,27.3,31.5,32.6],
})
bics_sector.to_csv(os.path.join(DATA,"bics_firm_adoption_by_sector.csv"), index=False)

# ---------------------------------------------------------------- 2. INDIVIDUAL SPINE: Ofcom + Lloyds
# % of UK adults / internet users who have used generative-AI tools.
# Sources: Ofcom Online Nation 2023/24 + Adults' Media Use & Attitudes 2024/25; Lloyds CDI 2025.
individual = pd.DataFrame({
    "date":   ["2023-11","2024-06","2024-11","2025-11"],
    "ofcom_adults_used_ai_pct":[31, 41, None, 54],   # Online Nation 2023(31) / 2024(41 past-yr) / Adults Media 2025(54)
    "source": ["Ofcom Online Nation 2023","Ofcom Online Nation 2024","",
               "Ofcom Adults Media 2025"],
})
individual.to_csv(os.path.join(DATA,"individual_adoption.csv"), index=False)

# ---------------------------------------------------------------- 2b. INDIVIDUAL SENTIMENT: ONS OPN
# ONS Opinions and Lifestyle Survey (OPN) AI module measures attitudes, not usage: % of GB adults
# who AGREE that AI will benefit them. A repeated official individual-level series (Table 7 trend).
# Source: ONS "Public opinions and social trends, GB: artificial intelligence", Nov 2023-Jun 2026.
opn = pd.DataFrame({
    "date":   ["2023-11","2024-01","2024-03","2024-06","2024-08","2024-11","2025-08","2026-06"],
    "agree_ai_benefits_me_pct": [38, 39, 38, 37, 39, 43, 41, 36],
})
opn.to_csv(os.path.join(DATA,"opn_individual_sentiment.csv"), index=False)

# ---------------------------------------------------------------- 3. FINANCIAL SERVICES: BoE/FCA
boe_fs = pd.DataFrame({
    "year":[2019,2022,2024],
    "currently_using_pct":[None,58,75],      # 2019 reported 'using or developing'
    "using_or_developing_pct":[67,72,None],
    "planning_pct":[None,14,10],
})
boe_fs.to_csv(os.path.join(DATA,"boe_financial_services.csv"), index=False)

# ---------------------------------------------------------------- 4. CROSS-COUNTRY: Yotzov et al. (NBER w34836)
xcountry = pd.DataFrame({
    "country":["United States","United Kingdom","Germany","Australia"],
    "any_ai_pct":[78,71,65,59],
    "text_gen_pct":[54,33,46,30],
    "data_ml_pct":[37,33,21,22],
    "robotics_pct":[13,14,4,7],
})
xcountry.to_csv(os.path.join(DATA,"crosscountry_firm_adoption.csv"), index=False)

# ================================================================ CHARTS
def _x(dates): return pd.to_datetime([d+"-01" for d in dates])

# Chart 1: firm adoption over time
fig, ax = plt.subplots(figsize=(8,4.5))
ax.plot(_x(bics.date), bics.headline_all_pct, "o-", lw=2, label="ONS BICS headline (all firms)")
ax.plot(_x(bics.date), bics.adhoc_using_pct, "s--", lw=1.6, color="#888", label="BICS/DSIT ad-hoc (consistent definition)")
ax.plot(_x([d for d,v in zip(bics.date,bics.headline_250plus_pct) if v]),
        [v for v in bics.headline_250plus_pct if v], "^:", lw=1.6, color="#c44", label="Large firms (250+)")
ax.axvline(pd.Timestamp("2022-11-01"), color="k", lw=0.8, ls=":"); ax.text(pd.Timestamp("2022-11-15"), 5, "ChatGPT", rotation=90, va="bottom", fontsize=8)
ax.yaxis.set_major_formatter(PercentFormatter()); ax.set_ylim(0,50)
ax.set_title("UK firm AI adoption is climbing steadily", fontweight="bold")
ax.set_ylabel("% of businesses using AI"); ax.legend(fontsize=8, frameon=False)
fig.text(0.01,0.01,"Source: ONS Business Insights and Conditions Survey (BICS), Sep 2023-Dec 2025", fontsize=7, color="#666")
fig.tight_layout(rect=(0,0.03,1,1)); fig.savefig(os.path.join(CHARTS,"1_firm_adoption_timeseries.png")); plt.close(fig)

# Chart 2: individual adoption
fig, ax = plt.subplots(figsize=(7,4.2))
ind = individual.dropna(subset=["ofcom_adults_used_ai_pct"])
ax.plot(_x(ind.date), ind.ofcom_adults_used_ai_pct, "o-", lw=2.2, color="#2a6")
for d,v in zip(ind.date, ind.ofcom_adults_used_ai_pct): ax.annotate(f"{v:.0f}%",(_x([d])[0],v),textcoords="offset points",xytext=(0,8),ha="center",fontsize=9)
ax.yaxis.set_major_formatter(PercentFormatter()); ax.set_ylim(0,65)
ax.set_title("UK adults using AI tools: 31% → 54% in two years", fontweight="bold")
ax.set_ylabel("% of UK adults / internet users")
fig.text(0.01,0.01,"Source: Ofcom Online Nation & Adults' Media Use and Attitudes, 2023-2025", fontsize=7, color="#666")
fig.tight_layout(rect=(0,0.03,1,1)); fig.savefig(os.path.join(CHARTS,"2_individual_adoption_timeseries.png")); plt.close(fig)

# Chart 3: firm adoption by sector (latest vs first wave)
fig, ax = plt.subplots(figsize=(8,4.5))
secs = [c for c in bics_sector.columns if c!="date"]
first, last = bics_sector.iloc[0], bics_sector.iloc[-1]
order = sorted(secs, key=lambda s: last[s])
y = range(len(order))
ax.barh(y, [last[s] for s in order], color="#36c", label="Dec 2025")
ax.barh(y, [first[s] for s in order], color="#bcd", height=0.45, label="Sep 2023")
ax.set_yticks(list(y)); ax.set_yticklabels(order, fontsize=9)
ax.xaxis.set_major_formatter(PercentFormatter())
ax.set_title("AI adoption by sector — broad-based gains", fontweight="bold")
ax.legend(fontsize=8, frameon=False)
fig.text(0.01,0.01,"Source: ONS BICS / DSIT AI adoption ad-hoc tables (waves 92-147)", fontsize=7, color="#666")
fig.tight_layout(rect=(0,0.03,1,1)); fig.savefig(os.path.join(CHARTS,"3_firm_adoption_by_sector.png")); plt.close(fig)

# Chart 4: cross-country
fig, ax = plt.subplots(figsize=(7,4.2))
ax.bar(xcountry.country, xcountry.any_ai_pct, color=["#36c" if c=="United Kingdom" else "#bbb" for c in xcountry.country])
for i,v in enumerate(xcountry.any_ai_pct): ax.text(i,v+1,f"{v}%",ha="center",fontsize=9)
ax.yaxis.set_major_formatter(PercentFormatter()); ax.set_ylim(0,90)
ax.set_title("Firm AI adoption: UK vs peers (any AI)", fontweight="bold"); ax.set_ylabel("% of firms")
fig.text(0.01,0.01,"Source: Yotzov et al., 'Firm Data on AI', NBER w34836 (2026); UK via BoE Decision Maker Panel", fontsize=7, color="#666")
fig.tight_layout(rect=(0,0.03,1,1)); fig.savefig(os.path.join(CHARTS,"4_crosscountry_firm_adoption.png")); plt.close(fig)

print("Adoption Monitor built:")
print("  CSVs   ->", DATA)
print("  charts ->", CHARTS)
for f in sorted(os.listdir(CHARTS)): print("    -", f)
