"""
UK AI Transformation Tracker — macro indicators of AI-driven 'takeoff' (explosive, capital-led
growth), the UK analogue of Stanford DEL's 12-indicator Transformation Tracker.

Method mirrors Stanford:
  - FLOW indicators are shown as year-over-year % growth (YoY is the smoothing).
  - SHARE indicators are logit-transformed (a bounded 0-1 share becomes unbounded, comparable
    to a growth rate; "up = transformation").
  - Each indicator is scored by how far today's value sits from its 1997-2019 AVERAGE, in SDs (z),
    in the takeoff-consistent direction (rising = takeoff). z>=2 strong, z>=1 mild, -1..1 neutral,
    <-1 contradictory. This is a level-vs-history test, so the label always matches the direction:
    genuinely elevated vs the pre-AI norm = mild/strong; flat or below = neutral/contradictory.
  - All series are clipped to a common SAMPLE_START (1997, like Stanford) so baselines are comparable.

UK-specific changes vs the US tracker (see PROJECT.md / methodology email):
  - Datacentre-demand projection DROPPED (a forecast, not an observed series).
  - Electricity GENERATION growth added (DESNZ ET 5.1) — the observed analogue.
  - ICT-services IMPORTS growth added (ONS BoP FJDL): the UK is an AI *adopter*, so AI capital
    deepening shows up as imported cloud/compute services, not domestic capital stock.
  - Network-Adjusted Private Capital Share (Stanford #6/#7) OMITTED: needs IO tables and a
    domestic electronics supply chain the UK doesn't have — structurally weak UK signal.

Clean ONS CDIDs pull LIVE; xlsx/zip series pull live with a curated fallback (flagged).
Run: python src/takeoff_tracker.py
Outputs: data/takeoff/scorecard.csv, data/takeoff/<indicator>.csv, charts/takeoff/*.png
"""
import os, sys, pandas as pd, numpy as np, matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ons_fetch import fetch_series
import sources

SAMPLE_START = pd.Timestamp("1997-01-01")   # Stanford fits trends from ~1997
SPLIT = pd.Timestamp("2019-01-01")          # pre-AI baseline ends 2019

def live(fn, *a, **k):
    try: return fn(*a, **k)
    except Exception as e: print(f"  ! live parse failed {getattr(fn,'__name__',fn)}: {e}"); return None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "takeoff"); CHARTS = os.path.join(ROOT, "charts", "takeoff")
os.makedirs(DATA, exist_ok=True); os.makedirs(CHARTS, exist_ok=True)
plt.rcParams.update({"figure.dpi": 130, "font.size": 9.5, "axes.spines.top": False, "axes.spines.right": False})
SCORE_COLOR = {"strong": "#c0392b", "mild": "#e08e0b", "neutral": "#7f8c8d", "contradictory": "#2980b9"}

def df_from(dates, vals):
    return pd.DataFrame({"date": pd.to_datetime(dates), "value": vals}).dropna().reset_index(drop=True)

def clip(df):
    return df[df.date >= SAMPLE_START].reset_index(drop=True) if df is not None else None

def yoy(df):
    """Year-over-year % growth (real, chained-volume inputs). For sub-annual series this is a
    4-quarter comparison; we also apply a trailing 4-period rolling mean to smooth."""
    d = df.dropna(subset=["value"]).sort_values("date").reset_index(drop=True)
    gap = d.date.diff().dt.days.median()
    per = 1 if gap > 200 else (4 if gap > 45 else 12)
    d = d.assign(value=(d.value / d.value.shift(per) - 1) * 100).dropna().reset_index(drop=True)
    if per > 1:
        d["value"] = d["value"].rolling(per, min_periods=2).mean()
        d = d.dropna().reset_index(drop=True)
    return d

def score_z(df, share=False, higher=True):
    """Score the latest value vs its 1997-2019 AVERAGE, in SDs (z), in the takeoff-consistent
    direction (higher=True means rising = takeoff). z>0 = the indicator is above its pre-AI norm
    in the takeoff direction. This is a LEVEL-vs-history test (not trend extrapolation), so the
    label always matches the direction: genuinely elevated = mild/strong, flat/below = neutral."""
    d = df.dropna(subset=["value"]).copy()
    if len(d) < 2: return "neutral", 0.0
    y = d.value.astype(float).values
    if share:
        p = np.clip(y / 100.0, 1e-3, 1 - 1e-3); y = np.log(p / (1 - p))
    pre = (d.date < SPLIT).values
    base = y[pre] if pre.sum() >= 2 else y[:-1]
    s = base.std(ddof=1) or 1e-9
    z = (y[-1] - base.mean()) / s
    if not higher: z = -z
    return ("strong" if z >= 2 else "mild" if z >= 1 else "neutral" if z > -1 else "contradictory"), float(z)

# ---------------------------------------------------------------- assemble series
S = {}
def addind(key, label, unit, df, latest, note, share=False, higher=True, live_flag=True):
    """Add an indicator: score it, build a structured multi-line rationale, store scoring config."""
    df = clip(df)
    sc, z = score_z(df, share=share, higher=higher)
    arrow = "above" if z >= 0 else "below"
    rationale = (f"<b>{label}</b>"
                 f"<br>Latest: {latest}"
                 f"<br>{abs(z):.1f}σ {arrow} its 1997–2019 average → <b>{sc} evidence</b>"
                 f"<br>{note}")
    S[key] = dict(label=label, unit=unit, df=df, score=sc, z=round(z, 2), rationale=rationale,
                  share=share, higher=higher, live=live_flag)
    return sc, z

def safe(path, cdid, ds, prefer="quarters"):
    try: return fetch_series(path, cdid, ds, prefer)
    except Exception as e: print(f"  ! live fetch failed {cdid}: {e}"); return None

# --- LIVE ONS pulls ---------------------------------------------------------------
gdp = safe("economy/grossdomesticproductgdp", "ABMI", "PN2")                              # GDP CVM SA £m (level)
prod = safe("employmentandlabourmarket/peopleinwork/labourproductivity", "LZVB", "PRDY")  # output/hr index
lshare = safe("employmentandlabourmarket/peopleinwork/labourproductivity", "FZLN", "UCST")# labour share %
ict = safe("economy/nationalaccounts/balanceofpayments", "FJDL", "pb")                    # imports: computer services £m (Pink Book, annual)
ict_tot = safe("economy/nationalaccounts/balanceofpayments", "KTMX", "ukea", prefer="years")  # imports: total goods & services £m (current vintage, to 2025)
ipp_inv = safe("economy/grossdomesticproductgdp", "TLPK", "ukea")                         # GFCF: intellectual property products (software+R&D) £m CP SA
tot_inv = safe("economy/grossdomesticproductgdp", "NPQS", "ukea")                         # GFCF: total asset £m CP SA
ic_inv = safe("economy/grossdomesticproductgdp", "DS8D", "cxnv")                          # Info & Comms industry business investment £m CP SA
tot_businv = safe("economy/grossdomesticproductgdp", "NPEK", "cxnv")                      # total business investment £m CP SA

# 1. Output growth (YoY GDP) — takeoff = sustained acceleration
if gdp is not None:
    g = yoy(clip(gdp))
    addind("output_growth", "Output growth (GDP, YoY)", "% YoY", g,
           f"{g.value.iloc[-1]:+.1f}% YoY", "Ordinary trend growth — output isn't accelerating.")

# 2. Labour productivity growth (YoY output/hr)
if prod is not None:
    g = yoy(clip(prod))
    addind("labour_productivity_growth", "Labour productivity growth (output/hr, YoY)", "% YoY", g,
           f"{g.value.iloc[-1]:+.1f}% YoY", "Productivity growth is weak — no AI-driven break.")

# 3. Computer-services imports as a SHARE of total imports (UK-native: AI arrives as imported
#    cloud/compute, so it deepens as a rising slice of the import basket, not domestic capital).
#    The Pink Book (FJDL) lags a year, so splice on the granular service-type dataset, which runs
#    ahead on the same NSA basis (identical on the overlap) — keeps the series on the latest year.
ict_fresh = live(sources.computer_services_imports)
if ict_fresh is not None and len(ict_fresh):
    if ict is None:
        ict = ict_fresh
    else:
        extra = ict_fresh[ict_fresh.date > ict.date.max()]
        if len(extra):
            ict = pd.concat([ict, extra], ignore_index=True)
            print(f"  + computer-services imports advanced to {extra.date.max().year} via service-type dataset")
if ict is not None and ict_tot is not None:
    m = clip(ict).merge(ict_tot[["date", "value"]], on="date", suffixes=("", "_tot"))
    sh = pd.DataFrame({"date": m.date, "value": m.value / m.value_tot * 100})
    addind("computer_services_imports", "Computer-services imports (% of total imports)", "%", sh,
           f"{sh.value.iloc[-1]:.2f}% of all UK imports (was ~0.5% pre-2020)",
           "The UK buys AI as imported cloud/compute — elevated well above its pre-AI norm.", share=True)

# 4. Capital share of income (100 - labour share)
if lshare is not None:
    cap = clip(lshare).copy(); cap["value"] = 100 - cap["value"]
    addind("capital_share", "Capital share of income (100 - labour share)", "%", cap,
           f"{cap.value.iloc[-1]:.1f}% of income",
           "Capital's slice of income; UK series is noisier than the US (oil, finance, housing).", share=True)

# --- LIVE xlsx/zip pulls with curated fallback ------------------------------------
realy_live = live(sources.boe_real_yield_10y)
mfp_live = live(sources.mfp_market_sector)
elec_live = live(sources.electricity_consumption)

def pick(df, fb_dates, fb_vals):
    return (df, True) if df is not None and len(df) else (df_from(fb_dates, fb_vals), False)

# 7. MFP / TFP growth (ONS growth-accounting, market sector), YoY of the annual index
mfp, mfp_live_f = pick(mfp_live, ["2018","2019","2020","2021","2022","2023","2024"],
                       [99.6,99.9,98.1,100.42,100.00,98.35,97.79])
g = yoy(clip(mfp))
addind("tfp_growth", "Multifactor productivity growth (TFP, YoY)", "% YoY", g,
       f"{g.value.iloc[-1]:+.1f}% YoY", "Total factor productivity is flat/negative — the opposite of takeoff.", live_flag=mfp_live_f)

# 8. 10y real interest rate (BoE index-linked gilt, level, 1985->present)
realy, realy_live_f = pick(realy_live, ["1997-12-31","2008-12-31","2019-12-31","2026-06-30"], [3.1,1.6,-2.4,1.55])
addind("real_yield", "10y real interest rate (index-linked gilt)", "%", clip(realy),
       f"{realy.value.iloc[-1]:.2f}%", "Real cost of capital — back to mid-1990s levels after the QE-era trough.", live_flag=realy_live_f)

# 9. IPP (software + R&D) INVESTMENT as a share of total GFCF (FLOW, not net stock — a capex
#    surge shows up without the depreciation/price lag of a stock ratio). This is where AI capex
#    lands (software, data, R&D). Quarterly CP, averaged over 1 year (4q rolling mean), logit.
#    Replaces the old computer-hardware NET-STOCK share, which was price-deflated and at historic
#    lows; UK investment has shifted decisively from equipment to intangibles since ~2005.
if ipp_inv is not None and tot_inv is not None:
    m = clip(ipp_inv).merge(tot_inv[["date", "value"]], on="date", suffixes=("", "_tot"))
    sh = pd.DataFrame({"date": m.date, "value": (m.value / m.value_tot * 100)})
    sh["value"] = sh["value"].rolling(4, min_periods=2).mean()
    sh = sh.dropna().reset_index(drop=True)
    addind("ipp_investment_share", "IPP (software + R&D) investment (% of GFCF, 4q avg)", "%", sh,
           f"{sh.value.iloc[-1]:.1f}% of investment (was ~21% in 1998)",
           "Software/R&D capex — where AI investment lands. Elevated vs history, but plateaued since 2019.", share=True)

# 10. Information & Communication sector investment as a share of total business investment — the
#     "BUILDING" side: the sector that builds datacentres, hosting, software and IT infrastructure.
#     A hosting tripwire — rises if/when the UK builds AI infrastructure at home. Quarterly CP,
#     4q-avg, logit. (Replaced the software/(software+R&D) composition ratio — low-signal for takeoff.)
if ic_inv is not None and tot_businv is not None:
    m = clip(ic_inv).merge(tot_businv[["date", "value"]], on="date", suffixes=("", "_tot"))
    sh = pd.DataFrame({"date": m.date, "value": (m.value / m.value_tot * 100)})
    sh["value"] = sh["value"].rolling(4, min_periods=2).mean()
    sh = sh.dropna().reset_index(drop=True)
    addind("infocomm_investment_share", "Info & Comms sector investment (% of business investment, 4q avg)", "%", sh,
           f"{sh.value.iloc[-1]:.1f}% of business investment",
           "The datacentre/hosting/software sector — mid-range, no unusual buildout. The 'building' tripwire if the UK starts hosting AI.", share=True)

# (retired) Software + R&D share of fixed assets — the STOCK twin of the IPP investment FLOW (#9);
# fundamentally correlated (stock = accumulated flow), so we keep only the more responsive flow.

# 11. Electricity consumption growth (DESNZ ET 5.1, supplied incl. net imports), YoY. Late-stage
#     AI signal: datacentres are still ~2-3% of UK power, swamped by EVs/heat-pumps/weather, so
#     this only lights up once AI compute load becomes material. (Primary energy consumption
#     dropped — too broad: transport + heating dominate, AI is a rounding error in it.)
elec, elec_live_f = pick(elec_live, ["2019","2020","2021","2022","2023","2024"],
                         [333.0,321.0,317.0,313.0,300.0,295.0])
g = yoy(clip(elec))
addind("electricity_consumption_growth", "Electricity consumption growth (YoY)", "% YoY", g,
       f"{g.value.iloc[-1]:+.1f}% YoY", "UK power demand is flat/declining — not yet an AI signal (datacentres are still ~2-3% of load).", live_flag=elec_live_f)

# ---------------------------------------------------------------- write CSVs + per-indicator charts
rows = []
for k, v in S.items():
    v["df"].to_csv(os.path.join(DATA, f"{k}.csv"), index=False)
    rows.append({"indicator": v["label"], "key": k, "score": v["score"], "z": v["z"], "live": v["live"],
                 "latest_date": v["df"].date.iloc[-1].date(),
                 "latest_value": round(v["df"].value.iloc[-1], 2), "unit": v["unit"], "rationale": v["rationale"]})
    fig, ax = plt.subplots(figsize=(5.2, 3))
    is_growth = "YoY" in v["unit"]
    ax.plot(v["df"].date, v["df"].value, "o-", color=SCORE_COLOR[v["score"]], lw=2, ms=3)
    if is_growth: ax.axhline(0, color="#999", lw=0.7)
    ax.set_title(v["label"], fontsize=9.5, fontweight="bold")
    ax.set_ylabel(v["unit"], fontsize=8)
    ax.text(0.98, 0.06, v["score"].upper(), transform=ax.transAxes, ha="right", fontsize=10,
            fontweight="bold", color=SCORE_COLOR[v["score"]])
    fig.tight_layout(); fig.savefig(os.path.join(CHARTS, f"ind_{k}.png")); plt.close(fig)

score_df = pd.DataFrame(rows)
score_df.to_csv(os.path.join(DATA, "scorecard.csv"), index=False)

# ---------------------------------------------------------------- score history (heatmap)
# Score each indicator as-of each YEAR-END across the AI era (2022->latest). Quarterly was static —
# UK macro evidence doesn't flip quarter-to-quarter (only 1 of 9 moved). Annual columns from 2022
# (eve of ChatGPT) show real movement: imports build mild->strong, productivity/TFP dip, etc.
def score_asof(v, asof):
    sub = v["df"][v["df"].date <= asof]
    return score_z(sub, share=v["share"], higher=v["higher"])[0] if len(sub) >= 2 else None
latest_all = max(v["df"].date.max() for v in S.values())
periods = [pd.Timestamp(f"{y}-12-31") for y in range(2022, latest_all.year + 1)]
hist = [{"key": k, "indicator": v["label"], "period": str(p.year),
         "period_date": p.date(), "score": score_asof(v, p)}
        for p in periods for k, v in S.items() if score_asof(v, p)]
pd.DataFrame(hist).to_csv(os.path.join(DATA, "scorecard_history.csv"), index=False)

# ---------------------------------------------------------------- summary scorecard chart
HEIGHT = {"contradictory": 1, "neutral": 2, "mild": 3, "strong": 4}
order = {"strong": 0, "mild": 1, "neutral": 2, "contradictory": 3}
sd = score_df.sort_values("score", key=lambda c: c.map(order))
fig, ax = plt.subplots(figsize=(9.2, 0.5 * len(sd) + 1.3))
y = range(len(sd))
ax.barh(list(y), [HEIGHT[s] for s in sd.score], color=[SCORE_COLOR[s] for s in sd.score])
ax.set_yticks(list(y)); ax.set_yticklabels(sd.indicator, fontsize=8.5)
ax.set_xticks([1, 2, 3, 4]); ax.set_xticklabels(["contra", "neutral", "mild", "strong"]); ax.set_xlim(0, 4.4)
ax.invert_yaxis()
for i, (s, lv) in enumerate(zip(sd.score, sd.live)):
    ax.text(HEIGHT[s] + 0.06, i, "●" if lv else "○", va="center", fontsize=8, color="#444")
n = sd.score.value_counts()
verdict = f"{n.get('strong',0)} strong / {n.get('mild',0)} mild / {n.get('neutral',0)} neutral"
if n.get('contradictory', 0): verdict += f" / {n.get('contradictory',0)} contra"
ax.set_title(f"UK AI Transformation Tracker: {verdict}", fontweight="bold", fontsize=12.5, pad=12)
fig.text(0.01, 0.02, "● live pull (ONS / BoE / DESNZ)   ○ curated", fontsize=8, color="#555")
fig.text(0.01, 0.005, "Latest value vs each indicator's 1997-2019 average (SDs), in the takeoff direction. Method mirrors Stanford DEL Transformation Tracker.", fontsize=7, color="#666")
fig.tight_layout(rect=(0, 0.06, 1, 1)); fig.savefig(os.path.join(CHARTS, "0_scorecard.png")); plt.close(fig)

print("Transformation Tracker built:")
print(score_df[["indicator", "score", "latest_value", "unit", "live"]].to_string(index=False))
print("\n  NAPCS (network-adjusted capital share) omitted — needs IO tables + a UK electronics supply chain that doesn't exist.")
print(f"  scorecard -> {os.path.join(DATA,'scorecard.csv')}")
print(f"  charts    -> {CHARTS}")
