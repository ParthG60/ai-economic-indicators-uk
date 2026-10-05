"""
Build the UK AI Economic Indicators dashboard as a single interactive HTML page.
Charts are Plotly (hover/zoom/legend-toggle); plotly.js loads from CDN (needs internet to render).
Reads the CSVs produced by the three trackers; regenerate after running them (or via run_all.py).

Design: the agreed "Institute" identity (navy + teal, Bricolage Grotesque / Hanken Grotesk),
see reference/DESIGN.md. Palette is colour-blind-safe (Okabe-Ito): dark blue vs orange (the canonical
two-class pair, distinct in lightness as well as hue), never red-vs-green; hover labels stay readable.
Run: python src/build_dashboard.py  ->  dashboard/index.html
"""
import os, textwrap, datetime, pandas as pd, plotly.graph_objects as go, plotly.io as pio
from plotly.subplots import make_subplots
from plotly.offline import get_plotlyjs_version

BUILD_DATE = datetime.date.today().strftime("%d %B %Y")   # shown as the "data last refreshed" stamp

# Multi-page site: each page is its own HTML file, so plotly.js loads once per page from a shared
# CDN <script> in the head (not injected per-figure). Every figure therefore embeds no library.
PLOTLY_CDN = f"https://cdn.plot.ly/plotly-{get_plotlyjs_version()}.min.js"

def wrap2(s, width=30):
    """Wrap a long label to 2 lines (collapse any overflow into line 2) — no truncation."""
    lines = textwrap.wrap(s, width=width)
    return lines[0] + ("<br>" + " ".join(lines[1:]) if len(lines) > 1 else "")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASH = os.path.join(ROOT, "dashboard"); os.makedirs(DASH, exist_ok=True)
def D(*p): return os.path.join(ROOT, "data", *p)

# --- Institute design tokens (navy + teal) ---
FONT = '"Hanken Grotesk", system-ui, -apple-system, sans-serif'
INK, MUTED, ACCENT = "#0b1f33", "#5c6b78", "#0e7c86"
PAPER, SURFACE, RULE, GRID, LINE = "#f4f7f8", "#ffffff", "#dde6ea", "#eef2f4", "#cdd8de"
NAVY = INK
# colour-blind-safe categorical palette (Okabe-Ito) — distinguishable under deuteran/protan/tritan
BLUE, ORANGE, VERM, TEALG, PURPLE, GREYBAR = "#0072B2", "#E69F00", "#D55E00", "#009E73", "#7d539e", "#aebcc6"
# semantic aliases used by the chart helpers (blue vs vermillion = the safe contrast pair)
RED, GREEN, AMBER = VERM, BLUE, ORANGE
# evidence ramp: lightness-ordered teal (CB-safe by lightness alone); contradictory a distinct hue
SCORE = {"strong": "#0e7c86", "mild": "#74bcc4", "neutral": "#cdd9de", "contradictory": "#b3679b"}
CHATGPT = "2022-11-01"
_first = [True]

def div(fig):
    html = pio.to_html(fig, include_plotlyjs=False, full_html=False,
                       config={"displayModeBar": False, "responsive": True})
    _first[0] = False
    return html

def style(fig, h=340, title=None, unified=True, pct=False, legend=True):
    # chart titles live in the HTML card header (.chart-t); readable hoverlabel fixes light-bar hovers
    fig.update_layout(
        font=dict(family=FONT, size=12.5, color=INK), height=h,
        margin=dict(l=10, r=18, t=46, b=10),
        hovermode=("x unified" if unified else "closest"),
        hoverlabel=dict(bgcolor="#ffffff", bordercolor=RULE, font=dict(family=FONT, size=12, color=INK)),
        showlegend=legend,
        legend=dict(orientation="h", y=1.13, yanchor="bottom", x=0, font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        plot_bgcolor=SURFACE, paper_bgcolor=SURFACE,
        xaxis=dict(showgrid=False, showline=True, linecolor=LINE, ticks="outside", tickcolor=LINE, tickfont=dict(size=11), automargin=True),
        yaxis=dict(showgrid=True, gridcolor=GRID, zeroline=False, ticks="", tickfont=dict(size=11),
                   ticksuffix="%" if pct else None, automargin=True),
    )
    return fig

def chatgpt_line(fig):
    fig.add_vline(x=CHATGPT, line=dict(color="#9bb8bd", width=1, dash="dot"))
    fig.add_annotation(x=CHATGPT, yref="paper", y=1.0, text="ChatGPT", showarrow=False,
                       font=dict(size=10, color=MUTED), xanchor="left", xshift=4)
    return fig

def card(label, value, sub="", accent=ACCENT):
    return (f"<div class='card'><div class='cval' style='color:{accent}'>{value}</div>"
            f"<div class='clab'>{label}</div><div class='csub'>{sub}</div></div>")

def chart(fig, title="", sub=""):
    # title + optional one-line caption sit OUTSIDE the clipped plot wrapper (never cut on resize/zoom)
    head = f"<div class='chart-t'>{title}</div>" if title else ""
    subh = f"<div class='chart-sub'>{sub}</div>" if sub else ""
    return f"<div class='chart'>{head}{subh}<div class='chart-plot'>{div(fig)}</div></div>"

# ============================================================ ADOPTION
bics = pd.read_csv(D("adoption", "bics_firm_adoption.csv")); bics["d"] = pd.to_datetime(bics.date + "-01")
ind = pd.read_csv(D("adoption", "individual_adoption.csv")); ind["d"] = pd.to_datetime(ind.date + "-01")
opn = pd.read_csv(D("adoption", "opn_individual_sentiment.csv")); opn["d"] = pd.to_datetime(opn.date + "-01")
sec = pd.read_csv(D("adoption", "bics_firm_adoption_by_sector.csv"))
xc = pd.read_csv(D("adoption", "crosscountry_firm_adoption.csv"))
ukr = xc[xc.country == "United Kingdom"].iloc[0]
firms_month = bics.d.iloc[-1].strftime("%B %Y")     # latest BICS wave, e.g. "June 2026"

adoption_cards = "".join([
    card("UK firms using AI", f"{bics.firm_10plus_pct.iloc[-1]:.0f}%", f"ONS BICS, 10+ employees · from {bics.firm_10plus_pct.iloc[0]:.0f}% (Sep-23)", BLUE),
    card("UK adults using AI", f"{ind.ofcom_adults_used_ai_pct.dropna().iloc[-1]:.0f}%", f"Ofcom · from {ind.ofcom_adults_used_ai_pct.dropna().iloc[0]:.0f}% (2023)", ACCENT),
    card("Adults: “AI will benefit me”", f"{opn.agree_ai_benefits_me_pct.iloc[-1]:.0f}%", f"ONS OPN sentiment · from {opn.agree_ai_benefits_me_pct.iloc[0]:.0f}% (Nov-23)", ORANGE),
    card("Large firms (250+)", f"{bics.headline_250plus_pct.dropna().iloc[-1]:.0f}%", "ONS BICS · latest", BLUE),
    card("UK firms vs peers", f"{ukr.any_ai_pct:.0f}%", f"any AI · US {xc[xc.country=='United States'].any_ai_pct.iloc[0]:.0f}% / DE {xc[xc.country=='Germany'].any_ai_pct.iloc[0]:.0f}%", NAVY),
])

f1 = go.Figure()
f1.add_scatter(x=bics.d, y=bics.firm_10plus_pct, name="All firms, 10+ employees (BICS)", line=dict(color=BLUE, width=2.8), hovertemplate="%{y:.1f}%")
ba = bics.dropna(subset=["headline_all_pct"])
f1.add_scatter(x=ba.d, y=ba.headline_all_pct, name="All businesses, incl. micro (to 2025)", line=dict(color="#c3ccd4", width=1.6), hovertemplate="%{y:.0f}%")
f1.add_scatter(x=bics.d, y=bics.adhoc_using_pct, name="Consistent definition (DSIT)", line=dict(color="#8aa0ad", width=1.8, dash="dash"), hovertemplate="%{y:.1f}%")
b2 = bics.dropna(subset=["headline_250plus_pct"])
f1.add_scatter(x=b2.d, y=b2.headline_250plus_pct, name="Large firms (250+)", mode="lines+markers", line=dict(color=ORANGE, width=2, dash="dot"), hovertemplate="%{y:.0f}%")
style(f1, pct=True)

f2 = go.Figure()
io_ = ind.dropna(subset=["ofcom_adults_used_ai_pct"])
f2.add_scatter(x=io_.d, y=io_.ofcom_adults_used_ai_pct, name="Adults using AI (Ofcom)", mode="lines+markers", line=dict(color=BLUE, width=2.8), hovertemplate="%{y:.0f}%")
f2.add_scatter(x=opn.d, y=opn.agree_ai_benefits_me_pct, name="“AI will benefit me” (ONS OPN)", mode="lines+markers", line=dict(color=ORANGE, width=2.4), hovertemplate="%{y:.0f}%")
style(f2, pct=True)

secs = [c for c in sec.columns if c != "date"]; last = sec.iloc[-1]; first = sec.iloc[0]
order = sorted(secs, key=lambda s: last[s])
f3 = go.Figure()
f3.add_bar(y=order, x=[last[s] for s in order], orientation="h", name="Dec 2025", marker_color=BLUE, hovertemplate="%{y}<br>Dec 2025: %{x:.0f}%<extra></extra>")
f3.add_bar(y=order, x=[first[s] for s in order], orientation="h", name="Sep 2023", marker_color="#c3ccd4", hovertemplate="%{y}<br>Sep 2023: %{x:.0f}%<extra></extra>")
f3.update_layout(barmode="overlay"); style(f3, h=360, pct=True, unified=False)
f3.update_xaxes(ticksuffix="%")

f4 = go.Figure()
cols = [ORANGE if c == "United Kingdom" else "#bcccd6" for c in xc.country]
f4.add_bar(x=xc.country, y=xc.any_ai_pct, marker_color=cols, hovertemplate="%{x}<br>any AI: %{y:.0f}%<extra></extra>", showlegend=False)
style(f4, h=300, pct=True, unified=False, legend=False)

adoption_charts = (chart(f1, "Firm AI adoption") + chart(f2, "Individuals: use &amp; sentiment")
                   + chart(f3, "Adoption by sector (hover for each value)") + chart(f4, "UK firms vs peers"))

# ============================================================ TAKEOFF
sc = pd.read_csv(D("takeoff", "scorecard.csv"))
hist = pd.read_csv(D("takeoff", "scorecard_history.csv"))
n = sc.score.value_counts()
order_s = {"strong": 0, "mild": 1, "neutral": 2, "contradictory": 3}
sd = sc.sort_values("score", key=lambda c: c.map(order_s))
verdict = f"{n.get('strong',0)} strong &middot; {n.get('mild',0)} mild &middot; {n.get('neutral',0)} neutral" + (f" &middot; {n.get('contradictory',0)} contra" if n.get('contradictory',0) else "")
LVLN = {s: i + 1 for i, s in enumerate(["contradictory", "neutral", "mild", "strong"])}
LABEL = {"strong": "Strong", "mild": "Mild", "neutral": "Neutral", "contradictory": "Contradictory"}
score_legend = "<div class='legend'>" + "".join(
    f"<span class='sq' style='background:{SCORE[s]}'></span>{lab}" for s, lab in
    [("strong", "Strong"), ("mild", "Mild"), ("neutral", "Neutral"), ("contradictory", "Contradictory (against)")]) + "</div>"

# evidence heatmap: indicators × quarters. Hover shows THIS cell's quarter + its own evidence level
# (previously every cell reused the latest rationale — fixed: per-cell level, plus the indicator note).
periods = sorted(hist.period_date.unique())
plab = {p: hist[hist.period_date == p].period.iloc[0] for p in periods}
cur = sc.set_index("key"); okeys = list(sd.key)[::-1]
# preload each indicator's own series so each cell hover shows THAT year's actual value (not the latest)
series = {k: pd.read_csv(D("takeoff", f"{k}.csv")).assign(date=lambda x: pd.to_datetime(x.date)).sort_values("date") for k in okeys}
Z, HOV, ylab = [], [], []
for k in okeys:
    ylab.append(cur.loc[k, "indicator"]); s = series[k]; row, hv = [], []
    for p in periods:
        cell = hist[(hist.key == k) & (hist.period_date == p)]
        sco = cell.score.iloc[0] if len(cell) else cur.loc[k, "score"]
        sub = s[s.date <= pd.Timestamp(p)]                                   # value as of that period (asof)
        fresh = len(sub) and (pd.Timestamp(p) - sub.date.iloc[-1]).days <= 400
        val = f"value <b>{sub.value.iloc[-1]:.2f}</b>" if fresh else "value n/a"
        row.append(LVLN[sco]); hv.append(f"{val} &middot; {LABEL[sco]} evidence")   # flat per-cell string
    Z.append(row); HOV.append(hv)
cs = [[0, SCORE["contradictory"]], [.25, SCORE["contradictory"]], [.25, SCORE["neutral"]], [.5, SCORE["neutral"]],
      [.5, SCORE["mild"]], [.75, SCORE["mild"]], [.75, SCORE["strong"]], [1, SCORE["strong"]]]
fh = go.Figure(go.Heatmap(z=Z, x=[plab[p] for p in periods], y=ylab, customdata=HOV, colorscale=cs,
                          zmin=0.5, zmax=4.5, showscale=False, xgap=3, ygap=3,
                          hovertemplate="<b>%{y}</b><br>%{x}: %{customdata}<extra></extra>"))
fh.update_layout(font=dict(family=FONT, size=11.5, color=INK), height=36 * len(okeys) + 60,
                 margin=dict(l=10, r=14, t=12, b=8), plot_bgcolor=PAPER, paper_bgcolor=SURFACE,
                 hoverlabel=dict(bgcolor="#ffffff", bordercolor=RULE, font=dict(family=FONT, size=12, color=INK), align="left"),
                 xaxis=dict(side="top", tickfont=dict(size=11), showgrid=False),
                 yaxis=dict(tickfont=dict(size=11.5), showgrid=False, autorange="reversed"))

# per-indicator small multiples (uniform teal line; per-point hover shows that quarter's value)
keys = list(sd.key); ncol = 3; nrow = -(-len(keys) // ncol)
fg = make_subplots(rows=nrow, cols=ncol, subplot_titles=[wrap2(i) for i in sd.indicator],
                   vertical_spacing=0.2, horizontal_spacing=0.07)
for i, (_, r) in enumerate(sd.iterrows()):
    d = pd.read_csv(D("takeoff", f"{r.key}.csv")); d["date"] = pd.to_datetime(d.date)
    rr, cc = i // ncol + 1, i % ncol + 1
    fg.add_scatter(x=d.date, y=d.value, mode="lines", line=dict(color=ACCENT, width=2),
                   showlegend=False, hovertemplate="%{x|%b %Y}: %{y:.2f}<extra></extra>", row=rr, col=cc)
    if "YoY" in str(r.unit):
        lo, hi = min(0, d.value.min()), max(0, d.value.max()); pad = (hi - lo) * 0.12 or 1
        fg.update_yaxes(range=[lo - pad, hi + pad], row=rr, col=cc)
fg.update_layout(font=dict(family=FONT, size=10.5, color=INK), height=235 * nrow, margin=dict(l=8, r=8, t=34, b=8),
                 plot_bgcolor="white", paper_bgcolor="white",
                 hoverlabel=dict(bgcolor="#ffffff", bordercolor=RULE, font=dict(family=FONT, size=12, color=INK)))
fg.update_xaxes(showgrid=False, showline=True, linecolor=LINE, tickfont=dict(size=9))
fg.update_yaxes(showgrid=True, gridcolor=GRID, zeroline=True, zerolinecolor="#c4cad4", zerolinewidth=1.3, tickfont=dict(size=9))
for a in fg.layout.annotations: a.font.size = 10.5; a.font.color = INK   # 2-line wrapped subplot titles
takeoff_charts = chart(fh, "Evidence by indicator, by quarter. Hover any cell for its quarter, level and rationale") + chart(fg, "Each indicator over time vs its 1997–2019 average (hover for the value at any quarter)")

# ============================================================ CANARIES
# Consolidated to four charts around one "so what". All from LFS microdata (stock + longitudinal flows).
ae = pd.read_csv(D("canaries", "canaries_lfs_age_exposure.csv"), parse_dates=["date"])
young = ae[ae.band == "22-25"].dropna(subset=["Q5"]); prime = ae[ae.band == "35-49"].dropna(subset=["Q5"])
aa = pd.read_csv(D("canaries", "canaries_lfs_young_autoaug.csv"), parse_dates=["date"]).dropna(subset=["automation"])
summ = pd.read_csv(D("canaries", "canaries_lfs_summary.csv")).set_index("metric")["value"]
summ = summ[summ.index != "asof"].astype(float)
ag = pd.read_csv(D("canaries", "canaries_lfs_age_gradient.csv"))
wc = pd.read_csv(D("canaries", "canaries_lfs_wfh_control.csv"), parse_dates=["date"]).dropna(subset=["onsite_Q5"])
hire = pd.read_csv(D("canaries", "canaries_lfs_hiring.csv"), parse_dates=["date"])
stock = pd.read_csv(D("canaries", "canaries_lfs_stock.csv"), parse_dates=["date"])
SBRACKETS = ["22-25", "26-34", "35-49", "50-64"]
HBRACKETS = ["22-30", "31-40", "41-50", "51-64"]
# shared colour-blind-safe quintile ramp (least-exposed blue -> most-exposed vermillion) for both toggles
QC = {1: BLUE, 2: TEALG, 3: "#9aa7b1", 4: VERM, 5: ORANGE}
QNAME = {1: "Q1 least-exposed", 2: "Q2", 3: "Q3", 4: "Q4", 5: "Q5 most-exposed"}

QSHOW = (5, 1)   # show only most-exposed (Q5) vs least-exposed (Q1); middle quintiles add clutter, not signal
def quintile_toggle(df, brackets, value_col, y_title):
    """Build a Plotly figure: most- vs least-exposed lines per age band, with an age-band dropdown."""
    fig = go.Figure()
    for bi, b in enumerate(brackets):
        hb = df[df.bracket == b].pivot(index="date", columns="quintile", values=value_col)
        for q in QSHOW:
            fig.add_scatter(x=hb.index, y=hb[q], name=QNAME[q], legendgroup=QNAME[q], visible=(bi == 0),
                            line=dict(color=QC[q], width=3.0), hovertemplate=QNAME[q] + ": %{y:.0f}<extra></extra>")
    fig.add_hline(y=100, line=dict(color="#c4cad4", width=1, dash="dash")); chatgpt_line(fig)
    style(fig); fig.update_yaxes(title_text=y_title, title_font=dict(size=11))
    btns = []
    for bi, b in enumerate(brackets):
        vis = [False] * (len(brackets) * len(QSHOW))
        for j in range(len(QSHOW)):
            vis[bi * len(QSHOW) + j] = True
        btns.append(dict(label=f"Age {b}", method="update", args=[{"visible": vis}]))
    fig.update_layout(
        legend=dict(orientation="h", y=-0.17, yanchor="top", x=0, font=dict(size=10.5)),
        margin=dict(l=10, r=18, t=58, b=72),
        updatemenus=[dict(type="dropdown", direction="down", x=1.0, xanchor="right", y=1.18, yanchor="bottom",
                          showactive=True, bgcolor=SURFACE, bordercolor=RULE, font=dict(size=11), buttons=btns)])
    return fig
_hl = hire[hire.bracket == "22-30"].pivot(index="date", columns="quintile", values="idx").dropna()
hire_q5 = _hl[5].iloc[-1] - 100      # young (22-30) recent hires into most-exposed jobs, vs 2022 Q4
hire_q1 = _hl[1].iloc[-1] - 100      # ... into least-exposed jobs
hire_gap = _hl[5].iloc[-1] - _hl[1].iloc[-1]
auto_trough = aa.automation.min()
wcl = wc.iloc[-1]
onsite_gap = wcl.onsite_Q5 - wcl.onsite_Q1
y16 = float(ag.loc[ag.band == "16-21", "Q5"].iloc[0])

canaries_cards = "".join([
    card("Young in most-exposed jobs", f"{summ.young_q5:+.1f}%", "age 22-25 · employment vs 2022 Q4", ORANGE),
    card("Hiring into exposed jobs", f"{hire_q5:+.0f}%", "age 22-30 recent hires vs 2022 Q4 · the mechanism", ORANGE),
    card("On-site young, WFH-adjusted", f"{wcl.onsite_Q5-100:+.1f}%", "decline vanishes among on-site workers", ACCENT),
    card("Older workers (control)", f"{summ.prime_q5:+.1f}%", "age 35-49, most-exposed · ~flat", MUTED),
])

# 1 — WHAT: employment in the job (the stock) by exposure quintile, with an age-band toggle.
#     Default 22-25 (where the gap lives); older bands are flat, so the toggle replaces the old control line.
fya = quintile_toggle(stock, SBRACKETS, "idx", "Employment index, 2022 Q4 = 100")

# 2 — IS IT AI: young automation- vs augmentation-type employment
fab = go.Figure()
fab.add_scatter(x=aa.date, y=aa.automation, name="Automation-type (AI does the task)", line=dict(color=ORANGE, width=2.8), hovertemplate="Automation-type: %{y:.0f}<extra></extra>")
fab.add_scatter(x=aa.date, y=aa.augmentation, name="Augmentation-type (AI assists)", line=dict(color=BLUE, width=2.8), hovertemplate="Augmentation-type: %{y:.0f}<extra></extra>")
fab.add_hline(y=100, line=dict(color="#c4cad4", width=1, dash="dash")); chatgpt_line(fab)
style(fab); fab.update_yaxes(title_text="Employment index, 2022 Q4 = 100", title_font=dict(size=11))

# 3 — WHY: the hiring margin. Recent hires (under 12 months' tenure) by exposure quintile,
#     with an age-band toggle (widened to 22-30 for sample). Older bands are a built-in placebo.
fhire = quintile_toggle(hire, HBRACKETS, "idx", "Recent-hire index, 2022 Q4 = 100")

# 4 — THE CATCH: WFH control, on-site young workers
fwfh = go.Figure()
fwfh.add_scatter(x=wc.date, y=wc.onsite_Q5, name="On-site · most-exposed (Q5)", line=dict(color=ORANGE, width=2.8), hovertemplate="On-site Q5: %{y:.0f}<extra></extra>")
fwfh.add_scatter(x=wc.date, y=wc.onsite_Q1, name="On-site · least-exposed (Q1)", line=dict(color=BLUE, width=2.8), hovertemplate="On-site Q1: %{y:.0f}<extra></extra>")
fwfh.add_scatter(x=wc.date, y=wc.home_Q5, name="Home-based · most-exposed (Q5)", line=dict(color=ORANGE, width=2, dash="dot"), hovertemplate="Home-based Q5: %{y:.0f}<extra></extra>")
fwfh.add_hline(y=100, line=dict(color="#c4cad4", width=1, dash="dash")); chatgpt_line(fwfh)
style(fwfh); fwfh.update_yaxes(title_text="Employment index, 2022 Q4 = 100", title_font=dict(size=11))

canaries_grid = (
    chart(fya, "What’s happening: employment by AI-exposure (2022 Q4 = 100)",
          "Counts everyone in the job, so the total moves slowly. Use the dropdown to change the age band: "
          "the gap sits in the youngest, and closes for older workers.")
    + chart(fab, "Is it AI? Young employment where AI <i>does</i> the task vs <i>assists</i>",
            "Where AI does the task, employment fell; where it only assists, it grew.")
    + chart(fhire, "Why: the hiring door. Recent hires by exposure (toggle the age band)",
            f"Counts only the past year’s hires, so it reacts fast: down {abs(hire_q5):.0f}% into the most-exposed "
            f"jobs vs {abs(hire_q1):.0f}% the least. Slide the age band up and the gap fades by the 40s.")
    + chart(fwfh, "The catch: among on-site young workers, the decline disappears",
            "Restrict to on-site young workers and the most-exposed line recovers. The fall lives in home-workable roles."))

# ============================================================ ASSEMBLE
# Zoom/reflow-resistant resize: Plotly only re-lays-out on window.resize, but Chrome zoom and the grid
# flipping columns reflow the chart boxes without firing it, so SVGs overflow and overlap. A
# ResizeObserver on each chart box calls Plotly.Plots.resize whenever that box changes, for any reason.
RESIZE_JS = """<script>
(function(){
  function resizeAll(){
    if(!window.Plotly) return;
    document.querySelectorAll('.js-plotly-plot').forEach(function(gd){ try{ window.Plotly.Plots.resize(gd); }catch(e){} });
  }
  var raf=0;
  function schedule(){ if(raf) cancelAnimationFrame(raf); raf=requestAnimationFrame(resizeAll); }
  window.addEventListener('resize', schedule);
  window.addEventListener('load', function(){ resizeAll(); setTimeout(resizeAll,250); });
  if('ResizeObserver' in window){
    var ro=new ResizeObserver(schedule);
    document.querySelectorAll('.chart').forEach(function(c){ ro.observe(c); });
  }
})();
</script>"""

STYLE = f"""<style>
 :root{{--ink:{INK};--muted:{MUTED};--accent:{ACCENT};--paper:{PAPER};--surface:{SURFACE};--rule:{RULE}}}
 *{{box-sizing:border-box}} html{{scroll-behavior:smooth}}
 body{{font-family:{FONT};margin:0;background:var(--paper);color:var(--ink);-webkit-font-smoothing:antialiased;line-height:1.5;font-size:15px}}
 .wrap,main,footer{{max-width:1160px;margin:0 auto;padding-left:28px;padding-right:28px}}
 .serif{{font-family:"Bricolage Grotesque",system-ui,sans-serif}}
 .mono{{font-family:"IBM Plex Mono",ui-monospace,monospace}}
 /* nav */
 .nav{{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.93);backdrop-filter:blur(8px);border-bottom:1px solid var(--rule)}}
 .nav .wrap{{display:flex;align-items:center;justify-content:space-between;gap:10px;padding-top:13px;padding-bottom:13px}}
 .brand{{font-family:"Bricolage Grotesque",system-ui,sans-serif;font-weight:700;font-size:15px;color:var(--ink);border:0;letter-spacing:-.2px}}
 .brand b{{color:var(--accent);font-weight:700}}
 .navlinks{{display:flex;gap:3px;flex-wrap:wrap}}
 .navlinks a{{font-size:13px;color:var(--muted);border:0;padding:6px 12px;border-radius:7px;transition:.15s}}
 .navlinks a:hover{{background:#eef5f6;color:var(--ink)}}
 .navlinks a.active{{background:var(--accent);color:#fff}}
 /* page header */
 .pagehead{{padding:44px 0 4px}}
 .kicker{{font-family:"IBM Plex Mono",monospace;font-size:11.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--accent);margin:0 0 16px}}
 h1{{font-family:"Bricolage Grotesque",system-ui,sans-serif;font-weight:700;font-size:clamp(32px,5vw,50px);line-height:1.03;letter-spacing:-.6px;margin:0;max-width:18ch}}
 .lede{{font-size:17.5px;color:var(--muted);max-width:62ch;margin:20px 0 0;line-height:1.55}}
 .meta{{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.04em;color:var(--muted);margin:22px 0 0;display:flex;gap:8px 22px;flex-wrap:wrap;align-items:center}}
 .dot{{width:7px;height:7px;border-radius:50%;background:{ACCENT};display:inline-block;margin-right:7px;vertical-align:1px}}
 /* sections */
 main{{padding-top:0;padding-bottom:60px;animation:rise .6s cubic-bezier(.2,.7,.2,1) both}}
 section{{padding:18px 0 8px}}
 @keyframes rise{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
 .eyebrow{{font-family:"IBM Plex Mono",monospace;font-size:11.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--accent);margin:0 0 11px}}
 h2{{font-family:"Bricolage Grotesque",system-ui,sans-serif;font-weight:700;font-size:clamp(25px,3.4vw,33px);letter-spacing:-.4px;margin:0 0 6px;line-height:1.1}}
 .sub{{color:var(--muted);font-size:15px;margin:10px 0 22px;max-width:78ch;line-height:1.6}}
 .sub b{{color:var(--ink);font-weight:600}} .sub i{{color:#46586a}}
 .verdict{{font-family:"Bricolage Grotesque",system-ui,sans-serif;font-size:20px;font-weight:500;margin:6px 0 16px;color:var(--ink);max-width:80ch;line-height:1.4}}
 .verdict b{{color:{ACCENT};font-weight:700}}
 /* metric cards */
 .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(186px,1fr));gap:1px;margin:4px 0 26px;background:var(--rule);border:1px solid var(--rule);border-radius:10px;overflow:hidden}}
 .card{{background:var(--surface);padding:18px 20px;transition:background .15s}}
 .card:hover{{background:#f8fbfc}}
 .cval{{font-family:"IBM Plex Mono",monospace;font-size:29px;font-weight:500;letter-spacing:-1px;line-height:1}}
 .clab{{font-size:13px;font-weight:600;margin-top:9px;color:var(--ink)}}
 .csub{{font-size:11.5px;color:var(--muted);margin-top:3px;line-height:1.45}}
 /* home cards (hover to choose a track) */
 .home-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(258px,1fr));gap:18px;margin:34px 0 8px}}
 .home-card{{display:block;border:1px solid var(--rule);border-radius:14px;background:var(--surface);padding:26px 24px;box-shadow:0 1px 2px rgba(11,31,51,.04);transition:transform .18s cubic-bezier(.2,.7,.2,1),box-shadow .18s,border-color .18s}}
 .home-card:hover{{transform:translateY(-5px);box-shadow:0 16px 34px rgba(11,31,51,.11);border-color:#cfe0e3}}
 .home-card .hn{{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--accent);letter-spacing:.18em}}
 .home-card h3{{font-family:"Bricolage Grotesque",system-ui,sans-serif;font-weight:700;font-size:22px;margin:12px 0 8px;color:var(--ink);letter-spacing:-.3px}}
 .home-card p{{font-size:14px;color:var(--muted);margin:0 0 18px;line-height:1.55}}
 .home-card .stat{{font-family:"IBM Plex Mono",monospace;font-size:31px;font-weight:500;color:var(--ink);letter-spacing:-1px;line-height:1}}
 .home-card .statl{{font-size:12px;color:var(--muted);margin-top:5px;line-height:1.45}}
 .home-card .go{{font-size:13px;color:var(--accent);font-weight:600;margin-top:18px;display:inline-block}}
 /* charts */
 .grid2{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(460px,100%),1fr));gap:22px}}
 .grid1{{display:block}}
 .chart{{border:1px solid var(--rule);border-radius:11px;padding:6px 12px 8px;background:var(--surface);min-width:0;margin-bottom:22px;box-shadow:0 1px 2px rgba(11,31,51,.04)}}
 .chart-plot{{overflow:hidden;min-width:0}}
 .chart .js-plotly-plot,.chart .plot-container,.chart .svg-container{{width:100%!important;max-width:100%}}
 .chart-t{{font-size:13px;font-weight:600;color:var(--ink);padding:11px 6px 2px;letter-spacing:.01em;overflow-wrap:break-word}}
 .chart-t i{{color:#46586a;font-style:italic}}
 .chart-sub{{font-size:11.5px;font-weight:400;color:#5c6b78;padding:0 6px 5px;line-height:1.45;overflow-wrap:break-word}}
 .chart-sub b{{color:var(--ink);font-weight:600}}
 /* reading guide (compact orientation tiles) */
 .guide{{display:grid;grid-template-columns:repeat(auto-fit,minmax(216px,1fr));gap:13px;margin:8px 0 26px}}
 .gcard{{background:var(--surface);border:1px solid var(--rule);border-radius:11px;padding:15px 17px;box-shadow:0 1px 2px rgba(11,31,51,.04)}}
 .gcard .gl{{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);margin:0 0 7px}}
 .gcard p{{margin:0;font-size:13px;color:#3c4a57;line-height:1.55}}
 .gcard p b{{color:var(--ink);font-weight:600}}
 /* evidence legend + note */
 .legend{{display:flex;flex-wrap:wrap;gap:8px 20px;align-items:center;font-size:12.5px;color:var(--muted);margin:10px 0 18px}}
 .legend .sq{{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:7px;vertical-align:-1px;border:1px solid var(--rule)}}
 .note{{background:#eef5f6;border:1px solid var(--rule);border-left:4px solid var(--accent);border-radius:10px;padding:14px 17px;font-size:13.5px;color:#3c4a57;margin:14px 0 22px;line-height:1.62;max-width:92ch}}
 .note b{{color:var(--ink)}} .note i{{color:#46586a}}
 /* data & methodology */
 .method{{background:var(--surface);border:1px solid var(--rule);border-radius:12px;padding:24px 26px 12px;margin:34px 0 0}}
 .method h3{{font-family:"Bricolage Grotesque",system-ui,sans-serif;font-weight:700;font-size:19px;margin:0 0 2px;color:var(--ink)}}
 .method h4{{font-size:11.5px;font-family:"IBM Plex Mono",monospace;letter-spacing:.09em;text-transform:uppercase;color:var(--accent);margin:18px 0 6px}}
 .method p{{font-size:13.5px;color:#3c4a57;line-height:1.62;margin:0 0 12px;max-width:92ch}}
 .method p b{{color:var(--ink)}} .method p i{{color:#46586a}}
 footer{{padding-top:30px;padding-bottom:56px;color:var(--muted);font-size:12px;line-height:1.7;font-family:"IBM Plex Mono",monospace;letter-spacing:.02em;border-top:1px solid var(--rule);margin-top:30px}}
 a{{color:var(--accent);text-decoration:none;border-bottom:1px solid {RULE}}}
 @media (max-width:760px){{
   .wrap,main,footer{{padding-left:18px;padding-right:18px}}
   .pagehead{{padding:30px 0 2px}} .lede{{font-size:15.5px}}
   .sub{{font-size:14px}} .cval{{font-size:25px}} .verdict{{font-size:17px}}
   .grid2{{grid-template-columns:1fr}} .cards{{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}}
 }}
</style>"""

HEAD = ("<meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<link rel='preconnect' href='https://fonts.googleapis.com'><link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>"
        "<link href='https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,600;12..96,700&family=Hanken+Grotesk:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap' rel='stylesheet'>"
        f"<script src='{PLOTLY_CDN}'></script>" + STYLE)

PAGES = [("index.html", "Home"), ("adoption.html", "Adoption"),
         ("transformation.html", "Transformation"), ("canaries.html", "Labour market")]

def nav(active):
    links = "".join(f"<a href='{href}' class='{'active' if label == active else ''}'>{label}</a>" for href, label in PAGES)
    return (f"<div class='nav'><div class='wrap'><a class='brand' href='index.html'>UK AI&nbsp;<b>Economic Indicators</b></a>"
            f"<nav class='navlinks'>{links}</nav></div></div>")

FOOT = ("<footer><div class='wrap' style='padding:0'>Built from public UK data: ONS (Business Insights survey, "
        "Labour Force Survey microdata via the UK Data Service, national accounts, productivity, trade, the Opinions "
        "and Lifestyle Survey), Bank of England, the Department for Energy Security and Net Zero, and Ofcom. "
        "Occupational exposure from the ILO (2025); automation and augmentation shares from the Anthropic Economic "
        "Index; cross-country firm adoption from Yotzov and co-authors (2026). After the Stanford Digital Economy Lab. "
        "Colours are colour-blind-safe. Charts are interactive: hover, zoom, and click the legend. "
        f"<span style='color:{ACCENT}'>Data last refreshed {BUILD_DATE}.</span></div></footer>")

def page(slug, title, active, body):
    html = (f"<!doctype html><html lang='en'><head>{HEAD}<title>{title}</title></head><body>"
            f"{nav(active)}<main>{body}</main>{FOOT}{RESIZE_JS}</body></html>")
    open(os.path.join(DASH, slug), "w", encoding="utf-8").write(html)
    return slug

# ---- home ---------------------------------------------------------------------------------------
firms_now = bics.firm_10plus_pct.iloc[-1]; adults_now = ind.ofcom_adults_used_ai_pct.dropna().iloc[-1]
n_strong, n_mild = int(n.get("strong", 0)), int(n.get("mild", 0))
home_cards = "".join([
    (f"<a class='home-card' href='adoption.html'><div class='hn'>01</div><h3>Adoption</h3>"
     f"<p>How far AI use has spread across UK firms and people, and whether the public expects to gain from it.</p>"
     f"<div class='stat'>{adults_now:.0f}%</div><div class='statl'>of UK adults have used an AI tool, up from {ind.ofcom_adults_used_ai_pct.dropna().iloc[0]:.0f}% in 2023</div>"
     f"<div class='go'>View the adoption track &rarr;</div></a>"),
    (f"<a class='home-card' href='transformation.html'><div class='hn'>02</div><h3>Transformation</h3>"
     f"<p>Whether AI is yet visible in the wider economy as fast, capital-led growth, across nine macro indicators.</p>"
     f"<div class='stat'>{n_strong}&thinsp;/&thinsp;9</div><div class='statl'>indicators show strong evidence of takeoff; the rest are mild or neutral</div>"
     f"<div class='go'>View the transformation track &rarr;</div></a>"),
    (f"<a class='home-card' href='canaries.html'><div class='hn'>03</div><h3>Labour market</h3>"
     f"<p>Whether AI is changing who gets hired, starting with young workers in the most exposed jobs. After Stanford's &lsquo;canaries&rsquo; study.</p>"
     f"<div class='stat'>{hire_q5:+.0f}%</div><div class='statl'>hiring of under-30s into the most AI-exposed jobs, since late 2022</div>"
     f"<div class='go'>View the labour-market track &rarr;</div></a>"),
])
home_body = (
    "<div class='pagehead'>"
    "<p class='kicker'>UK economic measurement, after the Stanford Digital Economy Lab</p>"
    "<h1>UK AI Economic Indicators</h1>"
    "<p class='lede'>Is AI being adopted, changing the wider economy, and reshaping who gets hired in the UK? "
    "Three tracks, each built from public UK data. Pick one to begin.</p>"
    "<div class='meta'><span><span class='dot'></span>ONS &middot; Bank of England &middot; DESNZ &middot; Ofcom &middot; UK Data Service</span></div>"
    "</div>"
    f"<div class='home-grid'>{home_cards}</div>")
page("index.html", "UK AI Economic Indicators", "Home", home_body)

# ---- adoption -----------------------------------------------------------------------------------
adoption_method = (
    "<div class='method'><h3>Data &amp; methodology</h3>"
    "<p>This track asks a simple question: how many UK firms and people actually use AI, and how do people feel about it.</p>"
    "<h4>Where the numbers come from</h4>"
    "<p><b>Firms.</b> The ONS Business Insights and Conditions Survey, a regular survey of UK businesses. The headline "
    "line counts firms with 10 or more employees that say they currently use AI — the basis ONS now leads with, running "
    f"to {firms_month}. A faint line shows the older all-business cut (including firms under 10 staff), which ONS stopped "
    "featuring after 2025; a third line, published by DSIT on a consistent definition, ran to Dec 2025.</p>"
    "<p><b>People.</b> Ofcom's Online Nation and Adults' Media Use surveys, for whether adults have used a generative-AI "
    "tool. Sentiment comes from the ONS Opinions and Lifestyle Survey, which asks whether people think AI will benefit them.</p>"
    "<p><b>Other countries.</b> Firm adoption across countries is from Yotzov and co-authors (2026); the UK figure there "
    "draws on the Bank of England's Decision Maker Panel.</p>"
    "<h4>How to read it</h4>"
    "<p>The firm measures use different definitions and different base populations, so compare each line with its own "
    "past rather than reading across the lines. Survey questions also vary, which is why the levels differ.</p></div>")
adoption_body = (
    "<div class='pagehead'><p class='eyebrow'>01 &middot; Adoption</p><h1>Who is using AI</h1>"
    "<p class='lede'>AI use is climbing on every measure. Among UK businesses with 10 or more employees, adoption has gone "
    f"from roughly a tenth in 2023 to over a third by {firms_month}, and just over half of adults say they have used an AI tool.</p></div>"
    f"<div class='cards'>{adoption_cards}</div>"
    f"<div class='grid2'>{adoption_charts}</div>"
    f"{adoption_method}")
page("adoption.html", "Adoption · UK AI Economic Indicators", "Adoption", adoption_body)

# ---- transformation ---------------------------------------------------------------------------
trans_method = (
    "<div class='method'><h3>Data &amp; methodology</h3>"
    "<p>This track asks whether AI is yet showing up in the wider economy as fast, capital-led growth, the kind of "
    "break from the past that Nordhaus (2021) called an economic singularity.</p>"
    "<h4>How each indicator is scored</h4>"
    "<p>Every series is compared with its own 1997 to 2019 average, before AI, and scored by how far above that norm "
    "it now sits, measured in standard deviations and in the direction that would signal takeoff. Growth series are "
    "shown as year-on-year change; share series are transformed so that rising always means more transformation. The "
    "four levels are strong, mild, neutral, and contradictory. This is a test against history, not a forecast.</p>"
    "<h4>The series and their sources</h4>"
    "<p>Output, productivity, the labour and capital shares, trade and investment come from the ONS; the real interest "
    "rate from the Bank of England; electricity from DESNZ. Two of the nine are annual official statistics whose "
    "latest complete year is 2024 (multifactor productivity and electricity); computer-services imports now runs to "
    "2025, and the rest run to late 2025 or early 2026.</p>"
    "<h4>Why it is tuned for the UK</h4>"
    "<p>The UK buys AI more than it builds it, so the clearest signal is computer-services imports, the cloud and "
    "compute bought from abroad. Domestic-capital measures are weaker here than in the US, because the hardware is "
    "imported, so we read them with that in mind.</p></div>")
_nw = {0: "No", 1: "One", 2: "Two", 3: "Three", 4: "Four"}
strong_lede = (
    f"{_nw.get(n_strong, n_strong)} strong signal{'s' if n_strong != 1 else ''} "
    f"{'points' if n_strong == 1 else 'point'} the same way, "
    + ("both on the input side: the money the UK spends importing cloud and compute, and business "
       "investment in software and R&amp;D."
       if n_strong == 2 else
       "on the input side: imported cloud and compute, and business investment in software and R&amp;D.")
) if n_strong else "No indicator yet shows strong evidence of takeoff."
trans_body = (
    "<div class='pagehead'><p class='eyebrow'>02 &middot; Transformation</p><h1>Is AI driving explosive growth yet</h1>"
    f"<p class='verdict'>Verdict: {verdict}.</p>"
    f"<p class='lede'>No clear sign of takeoff, which matches what Stanford finds for the US. {strong_lede} "
    "Core output and productivity look ordinary.</p></div>"
    f"{score_legend}"
    "<p class='sub'>The grid reads left to right by year, from 2022 onward. Hover any cell for that year's value and "
    "its evidence level; the charts below show each indicator against its pre-AI average.</p>"
    f"<div class='grid1'>{takeoff_charts}</div>"
    f"{trans_method}")
page("transformation.html", "Transformation · UK AI Economic Indicators", "Transformation", trans_body)

# ---- canaries -----------------------------------------------------------------------------------
canaries_method = (
    "<div class='method'><h3>Data &amp; methodology</h3>"
    "<p>This track follows an early warning sign from Brynjolfsson and co-authors (2025): if AI is changing hiring, it "
    "should show up first among young workers in the jobs AI can do most of.</p>"
    "<h4>The data</h4>"
    "<p>Labour Force Survey microdata from the UK Data Service: 19 quarterly files with single-year age, four-digit "
    "occupation, and a person weight that grosses the sample up to the population. Employment is that weighted "
    "headcount, indexed to the quarter before ChatGPT (late 2022) and smoothed over four quarters to remove "
    "seasonality and survey noise.</p>"
    "<h4>Measuring AI exposure</h4>"
    "<p>Each occupation gets an exposure score from the ILO's 2025 generative-AI index, mapped onto UK occupations and "
    "sorted into five equal-employment groups, from least exposed (Q1) to most exposed (Q5). For exposed jobs we also "
    "split automation, where AI does the task, from augmentation, where it assists, using the Anthropic Economic Index.</p>"
    "<h4>The hiring measure</h4>"
    "<p>Recent hires are people with under a year at their employer. Counting only them strips out long-tenured staff "
    "and shows the hiring decision directly. The hiring chart widens the young band to ages 22 to 30 so the recent-hire "
    "sample is large enough to split five ways; the stock charts keep the study's 22 to 25 band, where the entry-level "
    "signal is sharpest.</p>"
    "<h4>What it can and cannot say</h4>"
    "<p>This is descriptive. It shows patterns and their timing, not cause. The most-exposed jobs are also the most "
    "home-workable, and that overlap is not a coincidence: AI has landed hardest on knowledge and desk work, which is "
    "the work that can be done remotely. So an AI effect cannot be cleanly separated from a remote-work one. That is a "
    "reason for caution, not a reason to dismiss the signal. A firm-level causal test would need the ONS Secure Lab, and "
    "the 2023 to 2024 survey samples are noisy, so read the trajectory rather than single points.</p></div>")
canaries_guide = (
    "<div class='guide'>"
    "<div class='gcard'><p class='gl'>Exposure</p><p><b>Q5</b> is the desk and clerical work AI can do (data entry, "
    "payroll, insurance). <b>Q1</b> is manual work.</p></div>"
    "<div class='gcard'><p class='gl'>Two views to compare</p><p>One chart counts <b>everyone</b> in these jobs; another "
    "counts only the <b>past year’s hires</b>. Hiring falling while the total holds means the change is at the hiring "
    "gate, not layoffs.</p></div>"
    "<div class='gcard'><p class='gl'>The big caveat</p><p>These jobs are also the most <b>home-workable</b>, so an AI "
    "effect and a remote-work effect can’t be fully told apart.</p></div>"
    "</div>")
canaries_body = (
    "<div class='pagehead'><p class='eyebrow'>03 &middot; Labour market</p><h1>AI-exposed jobs and the young</h1>"
    f"<p class='verdict'>Since ChatGPT, hiring of young workers into the most AI-exposed jobs has dropped sharply, and "
    f"their employment there is down {abs(summ.young_q5):.1f}%. But the whole effect sits in remote-capable roles, so "
    f"treat it as a warning sign rather than proof of AI. This track follows Stanford's &lsquo;canaries&rsquo; study "
    "(Brynjolfsson and co-authors, 2025), rebuilt on UK data.</p></div>"
    f"{canaries_guide}"
    f"<div class='cards'>{canaries_cards}</div>"
    f"<div class='grid2'>{canaries_grid}</div>"
    f"{canaries_method}")
page("canaries.html", "Labour market · UK AI Economic Indicators", "Labour market", canaries_body)

print("Dashboard written -> 4 pages in", DASH)
print(f"  Adoption: firms {firms_now:.0f}%, adults {adults_now:.0f}%, sentiment {opn.agree_ai_benefits_me_pct.iloc[-1]:.0f}%")
print(f"  Transformation: {verdict}")
print(f"  Canaries: young 22-25 stock {summ.young_q5:+.1f}%; 22-30 exposed hiring {hire_q5:+.0f}% (Q5-Q1 {hire_gap:+.0f}pts); on-site {wcl.onsite_Q5-100:+.1f}%")
