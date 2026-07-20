# STATUS

## 2026-07-20 — Data-freshness scout + refresh (fixed DESNZ parser, +2026 Q1 investment)
Scoped whether new data printed since the 26 Jun build and refreshed what's live.
- **Fixed the electricity (DESNZ ET 5.1) parser.** It had been failing silently and falling back to a
  degraded 5-point stub (lost 1999–2019 history, flipped 2024 to −1.67% `live=False`). Cause: DESNZ renamed
  the heading "Table 5c" → **"Table 5.1c: electricity supplied by fuel (TWh)"** (file `ET_5.1_JUN_26.xlsx`).
  Changed `sources.electricity_consumption()` to match the stable text `"electricity supplied by fuel"`.
  Live again: full 1998→2024, 2024 = +0.09% YoY, `live=True`.
- **New live data applied (re-ran takeoff_tracker):** IPP investment share gained **2026 Q1 = 26.56%**
  (still mild); Info & Comms investment share gained **2026 Q1 = 11.37%** (neutral); 10y real yield Q2
  quarter-end finalised **1.55% → 1.72%**. Verdict unchanged: **1 strong · 1 mild · 7 neutral** (no takeoff).
  Rebuilt `dashboard/transformation.html` (reverted spurious Plotly-div-id churn on the other pages).
- **Web-checked the hand-curated adoption series:**
  - **BICS firm adoption** — already current. The DSIT AI adoption ad-hoc tables (pub. 15 Jan 2026) cover
    **waves 92–147 → Dec 2025 = 25%**, which is our last point. No newer AI module published yet.
  - **OPN sentiment** — NOT updated (flagged for Parth). New ONS reading is **June 2026 = 36%** agree "AI will
    benefit me" (3–28 Jun 2026; disagreement up to 27%, a record). But the same bulletin states **Aug 2025 = 38%**,
    whereas our series has **41%** for that period — an anchor discrepancy (likely a different OPN table/framing).
    Held rather than append over an inconsistency. **TODO:** verify the exact figure in the OPN AI dataset table,
    reconcile the Aug-2025 point, then add Jun-2026.
- No change (source not printed): GDP Q2 (out ~mid-Aug), labour productivity/capital share (still 2025 Q4),
  TFP/computer-services imports (annual, still 2024), job adverts (still May 2026), LFS microdata (2026 Q1,
  manual EUL). Committed locally (remote still not created).

## 2026-06-26 (late+++++) — Public release: cleaned for GitHub + put live on the website
Prepped the repo for public sharing (it backs an application). Added `.gitignore` (excludes the
EUL LFS microdata `data/canaries/lfs/*.zip|dta`, `data/takeoff/raw/`, copyrighted PDFs/txt/xlsx in
`reference/`, `dashboard/design-variants/`, scratch PNGs), `requirements.txt`, MIT `LICENSE` (+ data-terms
note), a rewritten public `README.md` (findings, live link, reproduce steps, microdata note), `BUILD_LOG.md`
(honest "how it was built with Claude Code", judgment-focused), and `data/canaries/lfs/README.md` (how to
obtain the microdata). **Redacted the confidential UKDS username** from `STATUS.md` and
`reference/ukds_inventory.md` BEFORE the first commit (never entered history); pulled the personal
`EMAIL_methodology.md` out of the repo (gitignored). Committed clean on `main` (87 files, 816 KB, verified
no microdata/PDF/secret in the tree). **Remote not yet created** — needs Parth's GitHub auth (see below).

Website (`~/personal-website`, already pushed + live): copied the 4 dashboard pages to
`ai-economic-indicators-uk/` so it serves at **parthgoyal.uk/ai-economic-indicators-uk/**; swapped the
homepage "proud of" bullet from the polarization model to the dashboard; added BOTH the dashboard and the
polarization model to the projects list; synced the Copy-for-LLM profile with a projects section. Pushed
to Pages and verified live: homepage bullet present, dashboard + all 3 sub-pages HTTP 200, and a headless
render of the production canaries page shows charts drawing correctly.

**To finish (Parth, one-time GitHub login):**
```
cd ~/ai-economic-indicators-uk
gh auth login
gh repo create ai-economic-indicators-uk --public --source=. --remote=origin --push
```
That creates the repo and pushes; it also makes the two `github.com/ParthG60/ai-economic-indicators-uk`
links (projects page + Copy-for-LLM) resolve. Also: rotate the UKDS password (it was typed in plaintext
this session) and scrub `~/.claude` transcripts before sharing any agent logs.

## 2026-06-26 (late++++) — Reverted the CB toggle; fixed the colours themselves instead
Parth rejected the dash/marker/hatch toggle ("not fatter lines and dashed boxes") — wanted the *colours*
CB-friendly, not a redundant-encoding overlay. So: **fully removed** the `CB_JS` block, nav button,
`.cbtoggle`/`.navright` CSS, `page()` injection and footer mention (back to clean nav). Then **re-paired
every two-series chart on dark blue `#0072B2` vs orange `#E69F00`** (was blue vs vermillion `#D55E00`):
the Okabe-Ito canonical 2-class pair, which differs in *lightness* as well as hue so it survives all CB
types. Changed: `QC[5]` (Q5 ramp), the most-exposed card accent, automation line, and both on-site/home
Q5 lines in the WFH chart. **Verified** with a Machado-2009 deuteranopia + protanopia simulation on the
rendered page — blue stays dark-blue, orange reads as a clearly lighter yellow, separable in both. Updated
the module docstring and DESIGN.md APPLIED note. No data/pipeline changes.

## 2026-06-26 (late++) — Simplified both toggle charts to Q5 vs Q1 only
Checked the data: the middle quintiles don't form a clean dose-response gradient (stock 22-25 has Q3/Q4
*above* 100, hiring has Q2 highest), so they added clutter and a distracting counter-signal without
strengthening the causal read. Dropped Q2/Q3/Q4: both toggle charts now show most-exposed (Q5) vs
least-exposed (Q1) only. One-line change via `QSHOW=(5,1)` in `quintile_toggle()`.

## 2026-06-26 (late+) — Chart 1 now an age toggle; un-bolded captions
- **Replaced the static 35-49 control line** on the "What's happening" (stock) chart with an age-band
  toggle, mirroring the hiring chart. Bands **22-25 / 26-34 / 35-49 / 50-64**, default 22-25 (keeps the
  -8.6% headline; the gap is 22-25-only, older bands flat, so the toggle IS the control now). Shows all
  five quintiles like the hiring chart.
- **New data:** `canaries_lfs_hiring.py` now also emits `canaries_lfs_stock.csv` (all employed by band ×
  quintile; stock bands start at 22-25 since sample is ample, hiring stays 22-30 for sample). Refactored
  `build_dashboard.py` chart builders into one shared `quintile_toggle()` helper (used by both fya + fhire).
- **Un-bolded the chart captions** (`.chart-sub`): removed mid-sentence `<b>` so the labour page matches
  the plain sub-text style of the other sections. Chart-1 caption made age-neutral (it's a toggle now).
- Verified by headless render: both toggle charts consistent, control line gone, captions plain.

## 2026-06-26 (late) — Broke up the labour-page text blob into a reading guide + chart captions
Feedback: the top "how to read" paragraph was a text-heavy, ugly blob. Restructured for presentation:
- **Replaced the blob with three compact tiles** (`.guide`/`.gcard`): Exposure / Two views to compare / The
  big caveat. One short line each, scannable.
- **Pushed detail onto the charts.** `chart()` now takes an optional `sub=` caption (`.chart-sub`); each of
  the four labour charts gets a one-line caption explaining what it shows (headcount = slow; recent hires =
  fast, with the numbers; auto-vs-aug; on-site recovery). Detail now sits where it's relevant.
- **WFH nuance** (overlap is intuitive, can't separate but doesn't dismiss) moved into the methodology block.
- Verified by headless render: clean structured layout, no em-dashes, big paragraph gone.

## 2026-06-26 (eve) — Labour-market page copy + home headline tweaks (reader feedback)
- **Renamed "Canaries" → "Labour market"** in nav, home card, page eyebrow/title (file stays canaries.html).
  Credited the source on the page and home card: Stanford's "canaries" study (Brynjolfsson and co-authors, 2025).
- **Moved the "How to read it" note to the top** of the labour page (before the cards), per request.
- **Explained headcount vs hiring in plain words** (no "stock/flow" jargon): chart 1 "counts everyone holding
  these jobs today" (slow-moving) vs chart 3 "only people hired in the past year" (fast-moving) — the gap is
  the hiring-door signal.
- **Reframed the WFH caveat**: not a debunk. High AI-exposure and high home-working travel together by
  definition (AI hits knowledge/desk work = the remote-capable work), so we can't separate the two effects,
  rather than remote work explaining it away.
- **Home adoption headline → adults** (54% used an AI tool, from 31%) instead of firms (more dramatic).
- **"Britain" → "UK"** everywhere. Verified by headless render (home + labour page).

## 2026-06-26 (pm) — Split dashboard into a 4-page site + concise methodology + humanized copy
Goal: make it reader-friendly. All in `build_dashboard.py` (now writes 4 files, not 1).
- **Multi-page.** `index.html` is a home page: hero + three hover cards (Adoption / Transformation / Canaries),
  each with a headline stat and a link. Three section pages (`adoption.html`, `transformation.html`,
  `canaries.html`), each with a sticky top nav (active state) and cross-links. Helpers added: `nav()`,
  `page()`, shared `HEAD`/`STYLE`/`FOOT`; new CSS for `.nav`, `.home-card`, `.method`.
- **Plotly per page.** Switched from per-figure CDN injection to one shared `<script src=cdn.plot.ly/...>`
  in every page head (`PLOTLY_CDN` via `get_plotlyjs_version()`); all figures now `include_plotlyjs=False`.
- **Methodology moved to the foot.** Each section ends with a concise "Data & methodology" block
  (what it measures / sources / how to read it). Headers are now short (one verdict + one lede). 
- **No obscure refs.** "NBER w34836" → "Yotzov and co-authors (2026)"; footer rewritten in plain English.
- **Humanized copy.** Rewrote all section/home/method prose; removed every em-dash (incl. chart titles),
  fixed double-negatives ("down 8.6%", "fell only 9%"). 
- **Stale tracker values:** computer-services imports, TFP, electricity are ANNUAL official series whose
  latest complete year is 2024 (forcing quarterly still returns annual); 2025 annuals aren't published yet.
  Left as-is and documented in the transformation methodology. Quarterly series run to late-2025/2026.
- **Verified** by headless-Edge render of all 4 pages (home cards, nav active, 2×2 canaries grid, heatmap +
  9 small multiples, methodology blocks): readable and correct.

## 2026-06-26 — Canaries: replaced fragile flows chart with a recent-hire hiring measure (+ age toggle)
Goal: make the hiring-margin point robust and Stanford-like (quintiles × age toggle), drop the old flows chart.
- **Diagnosed the old flows chart as underpowered.** The linked longitudinal "entry/exit" used the LFS
  panel, which stacks three sample killers (linking loss + narrow age + requiring a *transition*): only
  ~559 young non-emp→emp moves across all years, → dozens per pre/post×quintile cell. The earlier
  "entry fell 22%" looked smooth only because it pooled in thousands of job-switchers (convoluted new
  entrants with movers — Parth's catch). Stock charts don't have this: ~1,540 young employed/qtr,
  ~314 young-in-Q5/qtr. The small-sample problem was unique to the flows chart.
- **New measure: `canaries_lfs_hiring.py`.** Recent hires = `EMPLEN ∈ {1,2,3}` (<12 months' tenure) on
  the large cross-section, indexed 2022 Q4 = 100, 4Q-rolling, by exposure quintile × age bracket.
  Healthy samples (~130–213 Q5 recent hires/qtr per bracket). Output `canaries_lfs_hiring.csv`.
- **Headline result (the mechanism the stock can't show):** young (22-30) hiring into most-exposed jobs
  -28% vs -15% least-exposed (gap -13pts), while the *stock* fell only -8.6% → fewer let in, not pushed
  out. Penalty fades with age (placebo): 22-30 -13pts → 31-40 -3 → 41-50 +16 → 51-64 +1.
- **Age cuts:** kept the paper's **22-25 for the stock** charts (sharpest entry-level signal; widening to
  22-30 washes the stock gap to ~0), **widened the hiring chart to 22-30** for sample. Footnoted on the
  dashboard. Older brackets exposed via toggle.
- **Dashboard (`build_dashboard.py`):** removed `fflow`; added `fhire` — all 5 quintiles with a Plotly
  dropdown age toggle (22-30/31-40/41-50/51-64), CB-safe quintile ramp (Q1 blue→Q5 vermillion, Q5 bold),
  legend moved to bottom. Rewrote card 2 + the "How to read it" note to the recent-hire framing; dropped
  the now-unused linked-panel numbers. `run_all.py`: swapped `canaries_lfs_flows.py`→`canaries_lfs_hiring.py`.
- Next: optional — graduate-only (RQF6+) cut of the hiring chart; render-check toggle on iPad/mobile widths.

## 2026-06-25 (pm) — Dashboard UX + accessibility overhaul (Institute theme applied)
Acted on Parth's /goal feedback, all in `build_dashboard.py`:
- **Applied the Institute design** (navy + teal, Bricolage Grotesque / Hanken Grotesk, radius-11 cards,
  soft shadows). Tokens documented in reference/DESIGN.md.
- **Colour-blind accessible**: replaced the red/green series with Okabe-Ito (blue #0072B2, vermillion
  #D55E00, teal #009E73, orange #E69F00); added line-dash as a redundant cue; heatmap is now a
  lightness-ordered teal ramp (CB-safe by lightness) + purple for contradictory. No red-vs-green anywhere.
- **Hover readability**: forced white-bg / navy-text hoverlabels everywhere → fixes the unreadable
  light-bar hover in the Adoption section; every bar now has an explicit labelled hovertemplate.
- **Macro tracker heatmap hover FIXED (round 2)**: first attempt used nested `customdata[0]/[1]` (which
  Plotly heatmaps don't reliably index) AND still showed the static current "Latest:" rationale on every
  cell — so it read as "still latest". Now each cell carries a FLAT customdata string showing THAT year's
  actual indicator value (asof-joined from the per-indicator series, with a 400-day freshness guard →
  "n/a" for trailing years with no data) + that cell's evidence level. Confirmed values vary per cell
  (electricity: 2022 −4.04 Contradictory → 2023 −0.55 → 2024 0.13 → 2025/26 n/a). NB heatmap x-axis is
  ANNUAL (history is scored per year 2022–2026), not quarterly — flag if Parth wants quarterly granularity
  (needs takeoff_tracker.py to score quarterly).
- **Canaries consolidated 8 charts -> 4** around an explicit "So what" verdict line: (1) what's happening
  young Q5 vs Q1 (+35-49 control folded in), (2) is it AI — auto vs aug, (3) why — exit vs entry flows,
  (4) the catch — WFH control. Age-gradient/roles/demand/age-specificity charts dropped; their findings
  compressed into one tight caveat note. Fixes the overlap (2x2 grid, min 460px, gap 22, t=46 margin,
  legend y=1.13) and the "not clear / so what" complaint.
10 charts total (was 14). Rebuilt + verified, no unfilled placeholders, 152KB.
- **Zoom/reflow overlap FIXED** (Parth diagnosed it happens on Chrome zoom change): Plotly only
  re-lays-out on window.resize, which zoom/grid-reflow doesn't reliably fire. Added a ResizeObserver
  on every `.chart` box that calls Plotly.Plots.resize on any box change (rAF-debounced), plus
  `.chart{overflow:hidden}` and forced 100% plot width as a safety net. No feedback loop (resize keeps
  fixed height, width is grid-controlled). RESIZE_JS injected before </body>.
Next: optional — render-check on a real browser at laptop/iPad/mobile widths; qualification cut (HIQUL15D).

## 2026-06-25 — Canaries flows: displacement vs non-hiring (LFS longitudinal) + design variants
Parth downloaded the LFS longitudinal back-catalogue: **16 Five-Quarter** (lgwt..5q.., 12-month
transitions) + **17 Two-Quarter** (lgwt..2q.., 3-month) cohorts, 2021→2026. Built
`src/canaries_lfs_flows.py` (wave vars suffixed 1..5: SOC20M1..5, ILODEFR1..5, AGE1..5; LGWT* weight;
compares start vs end occupation/status per person; dedupes the one duplicate 2q download).
**Headline result — the mechanism is the hiring door, not displacement:**
- Young (22-25) **exit** rate from exposed (Q5) jobs barely moved (2q 15.6%→14.7%; 5q 18.4%→18.6%).
- Young **entry** rate INTO exposed jobs fell (~22% at 3-month: 3.6%→2.8%; ~36% at 12-month: 5.6%→3.6%).
- So the lower young stock in exposed jobs = fewer hired in, not more pushed out (Stanford's entry-level story).
Honest caveats: 5q young-Q5 cells tiny (n 40→61) — 2q (n 510→928) carries it; the 35-49 control's exits
actually ROSE at 12-month (general 2024 churn in the mix); doesn't resolve the WFH confounder. Output:
`canaries_lfs_flows.csv`. Dashboard: added a "Displacement, or a closing door?" subsection + grouped
exit/entry bar chart + a 5th card ("Young hired into exposed jobs −22%"). 14 charts, rebuilt + verified.
Wired canaries_lfs_flows.py into run_all.py.
Design side (Parth's UI idea): built `src/design_variants.py` → 4 identities applied to the real dashboard
slice (whitepaper / **institute** [recommended] / lab / civic) in `dashboard/design-variants/`, token sets
in `reference/DESIGN.md`. AWAITING Parth's pick to parametrise build_dashboard.py + restyle the full dashboard.
Next: (a) restyle dashboard once a design is chosen; (b) optionally the qualification cut (HIQUL15D, in hand);
(c) APS person microdata deprioritised.

## 2026-06-24 (pm) — Canaries extensions: which roles/age cuts, and the WFH control (key, qualifying result)
Built `src/canaries_lfs_detail.py` (reuses canaries_lfs.load; added `soc`, `home`/`wfh` to the loader).
Three outputs, all LFS microdata:
- **Age gradient** (`canaries_lfs_age_gradient.csv`): in most-exposed jobs the fall is purely entry-level —
  22-25 **−8.6%**, 16-21 −4.6%, and every band 26+ flat or up (26-29 +2.3, 30-34 +2.4, 35-49 +1.6).
- **Roles** (`canaries_lfs_roles.csv`): biggest young-worker falls in exposed occupations 21/22→25/26 are
  clerical/admin — Receptionists −53% (WFH 2%!), Pensions/insurance clerks −47%, Book-keepers −38%,
  Business/financial project mgmt −26%. Risers all augmentation-type (sales execs +101%, IT support +62%,
  accountants +32%). SOC4×young cells noisy → illustrative.
- **WFH control** (`canaries_lfs_wfh_control.csv`) — the important one. Q5 is 39% mainly-WFH vs Q1 5%, so
  WFH is the obvious confounder. **Restricting to ON-SITE young workers, the Q5 decline DISAPPEARS**:
  Q5 +5.0%, Q1 −0.4%, gap **+5.4 pts** (vs −7.8 for all). The entire decline is among **home-based** young
  workers (Q5 −35%, still falling; home-Q1 cells too thin to compare). Two non-separable readings: (a) WFH
  really is the confounder (return-to-office / remote-hiring), (b) AI-exposure ≈ home-workability (codifiable
  desk tasks), so on-site conditioning is a **bad control** that drops the treated jobs. Either way the clean
  "AI cuts young exposed jobs" headline is **materially qualified** — now stated plainly on the dashboard.
Dashboard: replaced the all-ages APS movers chart with 3 microdata charts (age-gradient bar, young-roles bar,
WFH-control lines). Updated the caveat note + added a "Does it survive controlling for WFH?" subsection.
13 charts total, rebuilt + verified. Wired canaries_lfs.py + canaries_lfs_detail.py into run_all.py.
Next: refresh the Gmail draft to include the WFH qualifier (prior draft r4078436885988613839 is now incomplete).

## 2026-06-24 — Canaries upgraded to LFS microdata: the real age × exposure cut (faithful Stanford replication)
The big one. The LFS EUL quarterly person files are now in `data/canaries/lfs/` (19 calendar quarters,
2021 Q1 → 2026 Q1, ~605k employed person-records pooled). This delivers the **age × exposure employment
cut WITHOUT waiting for ASHE SecureLab** — the thing EMAIL_methodology.md said was 3 months away.
Built `src/canaries_lfs.py` (the faithful Stanford engine):
- Employment level = Σ person weights; indexed to **2022 Q4** (trailing 4Q = calendar 2022, pre-takeoff);
  4-quarter rolling to kill LFS seasonality + 2023-24 response-rate noise.
- Outputs: `canaries_lfs_age_exposure.csv` (band × quintile index), `canaries_lfs_young_autoaug.csv`
  (22-25 automation vs augmentation), `canaries_lfs_summary.csv` (cards).
**Results (strong, faithful):**
- 22-25 in most-exposed (Q5) employment **−8.6% vs 2022 Q4**; least-exposed (Q1) ~flat; **35-49 flat at
  every exposure level** (age-specific — the Stanford control holds).
- 22-25 automation-type **−8.2%** (trough **−33% in 2024**) vs augmentation-type **+5.7%** (gap +13.9 pts).
  Divergence is post-2023, no pre-trend. Both Stanford signatures (age-specific + automation-specific)
  reproduced. Q4 (2nd quintile) young actually rose — effect concentrated in the very top quintile.
Rewrote the Canaries section of `src/build_dashboard.py`: replaced the APS all-ages annual charts with
4 microdata charts (young Q5 vs Q1; young auto vs aug; age-specificity young-Q5 vs prime-Q5; advert
demand as corroboration). New cards + honest caveats (descriptive not causal, no firm×time Poisson,
2024 grad-hiring confounder, LFS noise). Dashboard rebuilt and verified.
Created a Gmail **draft** (to Parth, id r4078436885988613839) announcing the upgrade in the
EMAIL_methodology voice. NOTE: the Gmail MCP tool can't attach the 164KB HTML, so the draft says
"attached" but Parth must drag-drop `dashboard/index.html` when sending (or I can host on Drive for a link).
Next: optionally (a) host dashboard on Drive and swap "attached" for a live link, (b) extend the age cut
to the qualification dimension (HIQUL15D) or the Five-Quarter Longitudinal flows (SN 9486).

## 2026-06-23 — UK Data Service EUL access: documentation pulled, age-cut pipeline built
Parth's UKDS account *(username redacted)* was approved, **End User Licence (Safeguarded)** tier.
Activation still pending on his side (click the 23 Jun email link, tick EUL boxes, register).
UKDS pushes no data; microdata is a manual per-study download behind his login, so I cannot pull it.
What I did instead, all without login:
- Downloaded the public LFS user guides to `reference/ukds_docs/` (Vol 3 variables 2022, Vol 4 derived
  2016, Vol 10 longitudinal) and confirmed exact variable names.
- Wrote `reference/ukds_inventory.md`: what the EUL tier unlocks, ranked, with study numbers.
- Built `src/canaries_age_cut.py` against the real LFS variables (`SOC20M` 4-digit, `AGE`, `ILODEFR`,
  `HIQUL15D`, `PWT*` auto-detected). Joins our existing `occupation_exposure_quintiles.csv`. Runs the
  moment a `.tab/.dta/.sav` lands in `data/canaries/lfs/`. Dry-run prints fetch instructions cleanly.
Key findings: **LFS EUL** is the prize (occupation × age × qualification in one record → the young-worker
cut, our core Canaries-v2 hypothesis). **UKHLS EUL (SN 6614) strips detailed SOC/SIC**, so it can't carry
the occupation join — adoption/tech-use only. Transformation track gains nothing (we already pull those
aggregates live). Firm panel (ASHE, pooled QLFS/APS) is Secure tier, separate accreditation.
Next: Parth downloads QLFS quarters (start SN 9388 = Jan–Mar 2025, grab latest 4–8), unzips into
`data/canaries/lfs/`, I run the pipeline and wire results into the Canaries section.

## 2026-06-22 — Threshold-sensitivity check: automation result is NOT robust (important)
Parth challenged the 0.5 cut (0.4-0.6 is the messy zone). Ran a sensitivity sweep of the auto/aug
thresholds — the key finding, and it tempers our headline:
- **Augmentation growth is robust**: +7% to +10% across all thresholds (0.5–0.65).
- **The augmentation>automation GAP is robust**: +4 to +12 pts at every cut.
- **The automation ABSOLUTE change is NOT robust**: flips -3.5% / +2.6% / -2.1% / +1.9% across cuts;
  the automation group is small (7–27 occ) so a couple of occupations swing the sign.
Decision: thresholds → **automation ≥0.60, augmentation ≤0.40** (drop the messy 0.4–0.6 middle, per
Parth). Reframed the whole Canaries section to report only what's robust — "augmentation roles grew
(+8.2%) and outgrew automation at every threshold (gap +10pts)", explicitly NOT "automation roles were
cut". Cards: replaced the automation-% card with the robust **augmentation−automation gap**. Both
caveats (non-robust automation + occupational-upgrading confound) now on the dashboard.
Verified the rebuilt auto/aug chart via kaleido PNG.

## 2026-06-22 — Manager-tag fix (absolute thresholds), heatmap → annual AI-era, kaleido verify
- **Automation tag was mis-classifying managers** (Chief executives, score 0.49, tagged automation —
  nonsense). Root cause: tercile split is relative to the exposed set, so borderline managerial roles
  got pulled in. Fix: **absolute AEI thresholds** — automation >=0.50, augmentation <=0.40, drop the
  0.40-0.50 middle. CEOs/marketing/advertising managers now fall into the dropped middle. Result is
  cleaner AND stronger: **automation -3.5% vs augmentation +8.2%** (27 vs 69 occ); automation set is
  now clean admin/finance/clerical (taxation experts, book-keepers, customer service).
- **Heatmap**: quarterly-from-2025 was genuinely static (only 1/9 scores moved — macro evidence doesn't
  flip quarterly). Switched to **annual year-ends across the AI era (2022->latest)**: now 6/9 move
  (imports mild->strong, capital share mild->neutral, productivity/TFP dip to contradictory in 2023).
- **Employment chart "still breaks at 2023"**: installed **kaleido** and rendered the actual figure to
  PNG — it correctly shows 2021-2025 (Q5 peaks 2023 then declines). So the fix WAS in the file; Parth
  was seeing a browser-cached render. (Bonus: kaleido now lets us render Plotly charts to PNG to verify
  visually, working around the broken Edge headless screenshot.)
- **Employment-by-quintile chart cut off at 2023** (2024–25 invisible). Root cause: Plotly 6 encodes
  numeric numpy arrays as base64, and that chart had NO explicit x-range, so autorange mis-computed off
  the encoded array and stopped at 2023. Fix: pass plain Python lists + set explicit x-range
  `[min-0.2, max+0.2]`. (The full-width auto/aug chart was unaffected only because it already had a
  forced range — a good tell.) Lesson: numeric-x line charts need plain lists or an explicit range.
- **Heatmap**: Parth wanted recent focus — switched from annual 2020→latest back to **quarterly from
  2025-Q1** (Q1 2025 → Q2 2026). Quarterly indicators (real yield, IPP, Info&Comms, output, productivity)
  move within the window; annual ones hold at their latest release.

## 2026-06-22 — Refined automation/augmentation tagging + chart clarity
Parth skeptical of the auto/aug tagging (telecoms installers tagged automation — a physical job).
Verified AEI tags ARE face-valid at extremes (data entry/secretaries/typists = top automation;
psychologists/scientists/researchers = bottom). Two refinements in `canaries_employment.py`:
- **Terciles, not median**: tag only the clear top-third (automation) vs bottom-third (augmentation)
  of AEI automation score; drop the ambiguous middle third.
- **Exclude manual major groups** (SOC 5 skilled trades, 8 operatives, 9 elementary) from the exposed
  set — physical jobs the ILO exposure crosswalk occasionally mis-rates (removed telecoms installers).
- Result holds and is cleaner: **automation -0.1% vs augmentation +9.0%** (43 vs 43 occ). Most-affected
  now Receptionists/Public-services associates/Advertising managers (all cognitive — face-valid).
  Occupational-upgrading confound still flagged on the dashboard (suggestive, not proof).
- **Chart fix**: the automation/augmentation chart was cramped in the 2-col grid. Moved to full-width
  with end-of-line value labels (+9.0% / -0.1%) and a y-title; dropped the redundant demand-gap chart.

## 2026-06-22 — frontend-design redesign, heatmap→annual, labour-exposure sense-check
- **Installed + used the `frontend-design` skill**. Redesigned the dashboard to an editorial/institutional
  aesthetic (warm paper #f6f3ec, **Newsreader** serif display, **IBM Plex Sans** body, **IBM Plex Mono**
  numerals/labels, numbered eyebrow sections, hairline rules, staggered load animation, refined muted
  palette with sharp semantic accents). Replaced the navy-gradient/Inter generic look. Still one
  self-contained HTML, responsive (laptop/iPad/mobile), Plotly via CDN.
- **Heatmap now moves**: was static (annual data carried-forward across quarters). Switched score-history
  to **annual year-end columns 2020→latest**, which shows real evolution — computer-services imports build
  mild→**strong** (2024), real yields flip contradictory→neutral (QE trough lifting), IPP's COVID spike
  fades strong→mild. (Monthly is meaningless for UK macro data — it's annual/quarterly.)
- **Labour-exposure sense-check** (Parth flagged "seemingly contradictory"):
  - Exposure mapping is **face-valid** (Q5 = data entry/brokers/typists/underwriters; Q1 = bricklayers/
    forestry/street cleaners). But exposure is **ILO international** (not UK-native) + 64/412 SOC groups have
    lossy (<50%) modal-ISCO mapping; AEI automation covers 353/412 and is **US** Claude-usage crosswalked to UK.
  - The "contradiction" resolved: demand (a FLOW) collapsed while employment (a STOCK) held = hiring-margin
    adjustment, not a contradiction. The automation(−0.5%)/augmentation(+8.4%) split matches Stanford's
    direction BUT is **confounded with occupational upgrading** — augmentation "winners" are mostly
    managers/professionals, automation "losers" mostly clerical; that decline-of-clerical trend predates
    GenAI. Added this caveat to the dashboard note. Clean test still needs the age cut (ASHE v3).
  - Employment + adverts ARE UK (APS/Nomis, Textkernel); the two exposure layers are international/US.
- **Distortion fix**: Plotly chart titles were overlapping the top legend, and the ChatGPT v-line was
  pulling the adoption x-axis back into dead space. Moved ALL chart titles into HTML card headers
  (`.chart-t`), removed Plotly titles (legend now sits clean at top), dropped the ChatGPT line from the
  adoption charts (kept on Canaries demand where it's in-range), added `automargin`.
- **Responsive**: viewport meta already present; made chart grids fluid (`minmax(min(440px,100%),1fr)`
  + `min-width:0` so Plotly shrinks instead of overflowing), Plotly `responsive:true`, and added a
  `@media(max-width:760px)` breakpoint (single-column charts, smaller header/section padding/fonts).
  Now degrades cleanly laptop → iPad → mobile.
- **Design skill research**: best fit = Anthropic's official **`frontend-design`** skill (anthropics/skills
  marketplace — 50 styles/21 palettes/font pairings/charts, covers responsive dashboards). Alternatives:
  Tailwind Design System (wshobson/agents), UI/UX Pro Max. Recommended to Parth; install via Claude Code
  `/plugin`. Pending Parth's go-ahead to install + do a deeper design pass with it.
Parth caught a real inconsistency: electricity (flat/down) read **mild** while imports/IPP (rising) read
**neutral** — backwards. Root cause: trend-EXTRAPOLATION scoring (above a declining trend = positive).
- **Fixed scoring** (`score_z`): every indicator now scored on **level vs its 1997–2019 AVERAGE** (in SDs,
  takeoff-direction), so label matches direction — genuinely elevated = mild/strong, flat/below = neutral.
  New read: **1 strong / 1 mild / 7 neutral**. Computer-services imports = **strong** (z=+2.3, the UK-adopter
  signal); IPP = **mild** (z=+1.7); **electricity = neutral** (z=+0.2, was wrongly mild). Output/productivity/
  TFP neutral. Each indicator stores share/higher + z; rationale is now multi-line (nicer hover).
- **Evidence heatmap** (`scorecard_history.csv`): score each indicator as-of each quarter since 2025
  (carry-forward), rendered as an indicators×quarters Plotly heatmap coloured by evidence; hover = rationale.
  Replaces the old live/latest/as-of table. Evidence-level legend added.
- **Per-indicator charts**: zero line shown, growth charts now include 0 in range.
- **Canaries**: added a "how to read" box (explains exposure + automation/augmentation) and a **most-affected
  vs most-resilient occupations** chart (`canaries_occupation_movers.csv`: exposed occupations by employment
  change since 2022, coloured by automation/augmentation; APS 4-digit so flagged survey-noisy).

## 2026-06-22 — Dashboard redesigned: interactive Plotly + cleaner design
Rewrote `build_dashboard.py` from base64 matplotlib PNGs to **interactive Plotly** (hover/zoom/
legend-toggle) with a cleaner Stanford-ish design (Inter font, card grid, accent section headers,
soft shadows). 10 interactive charts from the CSVs; plotly.js via CDN (needs internet to render;
file is now 146KB vs 1MB). Scorecard bars show the rationale on hover. The trackers still emit their
matplotlib PNGs for the methodology email/static use. NB: Edge headless --screenshot is broken in
this env, so no auto-preview — open dashboard/index.html in a browser. Offline option (inline
plotly.js, ~4MB) available if needed.

## 2026-06-22 — Canaries v2 (EMPLOYMENT + Anthropic Economic Index) + adoption OPN survey
Big session. Sourced free data to build an 80/20 of the real Canaries employment study, and pulled
the ONS OPN individual survey. **No paid sources, no API keys** (all free/scrapable).

**Free sources found & used:**
- **ONS Annual Population Survey** via **Nomis API** (free, no key): dataset `NM_218_1`, national
  employment by **4-digit SOC2020**, Count, calendar-year periods 2021-2025. Joins directly to our
  ILO exposure (both SOC2020 4-digit). `geography=2092957697`, dims jtype/ftpt/etype/c_sex=0, measure=1.
- **Anthropic Economic Index** (Hugging Face `Anthropic/EconomicIndex`, MIT, free): release_2025_03_27
  task-level automation/augmentation. Built `src/build_aei_exposure.py` → chains AEI O*NET-SOC →
  ISCO-08 (BLS `ISCO_SOC_Crosswalk.xls`, fetched with a browser UA — 403s bots) → UK SOC2020 (our
  crosswalk), caching `reference/aei_automation_by_soc2020.csv` (353 occ, automation share 0-1, mean .36).
  AEI automation = directive+feedback_loop; augmentation = validation+task_iteration+learning.
- **ONS OPN** ("Public opinions & social trends: AI"): it's ATTITUDES not usage — pulled the Table_7
  trend (% GB adults agree "AI will benefit me", 38%→41%, Nov23→Aug25) as an individual SENTIMENT series.

**Built — `src/canaries_employment.py` (Canaries v2):**
- Real EMPLOYMENT by AI-exposure quintile (APS × ILO), indexed to 2022. Result: Q5 +1.4% vs Q1 -0.9%
  (gap +2.3pts) — i.e. the all-ages employment STOCK is ~flat, OPPOSITE the advert-demand collapse.
  That contrast = a **hiring-margin adjustment** (vacancies cut, incumbents stay → effect at entry level).
- **AEI automation vs augmentation cut** (Stanford's key distinction): among exposed occupations,
  **automation-type employment -0.5% vs augmentation-type +8.4%** since 2022 — the exact direction of
  Stanford's finding, and it explains why the aggregate quintile looks flat (augmentation masks automation).
- Charts 3 (employment) + 4 (automation/augmentation) added; v1.1 adverts kept as the demand companion.

**Adoption:** added OPN sentiment series + dashboard card. Dashboard Canaries section reframed around
the automation/augmentation headline. `run_all.py` now runs `canaries_employment.py`.
(`build_aei_exposure.py` is a one-off — re-run only to refresh the cached AEI crosswalk.)

### Still open (v3, needs ONS SecureLab ASHE — not free)
- Worker-AGE cut (the entry-level effect, the one thing the all-ages stock can't show) and the
  firm×time panel. APS confirmed to NOT cross occupation×age for free. Adoption: usage (vs sentiment)
  2nd individual source still optional.

## 2026-06-22 — Transformation Tracker: review pass (share, smoothing, long real yields, pruning)
Parth review of each indicator → fixes:
- **ICT-services imports**: switched from YoY growth to **% of total imports** (FJDL / KTMX, both
  CP NSA annual; logit). The share rose 0.25%→1.22% (1997→2024), nearly doubling since 2019, but
  vs the full 1997-2019 trend it's **on-trend (z=-0.2) → neutral**. The growth framing had read
  mild; the share is the more honest "is capex deepening net of trade growth" signal. NB verdict
  is baseline-sensitive: a 2012-2019 plateau baseline would make the post-2020 rise a breakout.
- **Output (GDP) & labour productivity**: confirmed **real** (ABMI chained-volume; LZVB output/hr
  index). YoY now **smoothed with a 4-quarter trailing rolling mean** (`yoy()` applies it to all
  sub-annual series).
- **10y real yield**: extended BoE zip read to ALL period files → **1985-present** (was 2015+).
  Scored vs the pre-2019 **level distribution** not a trend (real yields fell secularly to 2019,
  so a linear extrapolation would falsely read the rebound as strong). Now z=+0.4 → neutral, no
  longer flagged short-sample.
- **Dropped** the two non-Stanford extras (business-investment growth, PNFC net rate of return) —
  they weren't in Stanford's 12 and added noise. Easily restorable.
- Net: **11 indicators, all live, 0 strong / 1 mild / 10 neutral** (mild = software+R&D share of
  fixed assets).

### Computer-hardware stock → intangible investment FLOW (done)
Parth: remove the net-stock hardware ratio, use a flow, average higher-freq data over 1 year.
- Replaced the computer-hardware **net-stock** share with an **investment-flow** share off ONS GFCF
  by sector/asset (dataset `ukea`, CP SA quarterly, CDIDs via the workbook's CDID row): `NPQS` =
  total GFCF, `TLPW` = ICT & machinery, `TLPK` = IPP (software+R&D). 4-quarter rolling mean.
- First tried **ICT & machinery / GFCF** but it's bundled (ICT + general machinery), nominally
  price-deflated, and at **historic lows (24%→14%)** — its "mild vs trend" was a downtrend artifact.
- Switched to **IPP (software + R&D) investment / GFCF** — where AI capex actually lands. It rose
  21%→27% but **plateaued since 2019** and sits slightly *below* its rising trend → **neutral
  (z=-0.9)**. Honest result: no AI-capex breakout in the UK investment mix. (The intangible *stock*
  share stays mild — accumulation continues even as the flow pace flattens; a nice stock/flow
  contrast we now show both of.)
- New `yoy()` also applies a 4-quarter rolling mean to all sub-annual growth series.

### Renames + energy consolidation (done)
- `ict_services_imports` → **`computer_services_imports`** (it's BoP computer SERVICES imports, FJDL,
  not ICT hardware) — relabelled for accuracy.
- **Dropped primary energy** (all-energy Mtoe — too broad, AI invisible in it). **Switched electricity
  generation → consumption**: same ET 5.1 file, now Table **5c "electricity supplied"** (incl. net
  interconnector imports = demand met regardless of source; generation alone understates demand
  because the UK increasingly imports power). `sources.electricity_consumption()`. Scores **mild** —
  demand stopped its long efficiency decline (mild vs the downtrend, à la Stanford's US read), but
  that's broad electrification (EVs/heat pumps) not AI datacentres yet. Late-stage AI signal.
- Net: **10 indicators, all live, 0 strong / 2 mild / 8 neutral** (mild = intangible stock share,
  electricity consumption).

### Design note (adopter vs host)
The muted indicators (electricity, ICT-equipment investment) are the ones that REVIVE if/when the UK
starts hosting AI domestically — keep them as low-weighted "hosting tripwires." Imports lead in the
adopter phase; equipment/electricity/services-exports lead in the host phase. Core takeoff test stays
output + productivity (economy-agnostic). The tracker's job = show the wedge: adoption up, output flat.

### Building-side indicator added + lean consolidation (done)
- Added the **"building" tripwire**: Info & Comms **sector** business investment as a share of total
  business investment (`DS8D`/`NPEK`, dataset `cxnv`, quarterly CP, 4q-avg, logit). The sector that
  builds datacentres/hosting/software/IT. Scored vs the **level** distribution (range-bound ~10-12%,
  so trend-extrapolation would false-flag) → **neutral, 11.9%, mid-range**. Correct tripwire behaviour:
  flat now, lifts if the UK starts hosting AI at home. (NB: with trend-scoring it false-flagged STRONG
  off a tiny residual SD — a reminder our simple scoring inflates persistent series vs Stanford's AR(p)
  bootstrap; we use `trend=False` for range-bound series as the pragmatic fix.)
- **Retired** `software_share` (software/(software+R&D) — a within-intangibles composition mix, low
  signal for takeoff). `caps`/`capital_stock_shares` now unused by the tracker.
- **Net: 9 indicators, all live, 0 strong / 1 mild / 8 neutral** (mild = electricity consumption).
  Clean balanced set: growth/productivity (output, labour prod, TFP) · capital/returns (capital share,
  real yield) · AI channels (computer-services imports = buy abroad, IPP investment = build intangibles,
  Info&Comms investment = build infrastructure) · energy (electricity consumption).

### Hosting tripwires (the adopter→host transition)
- **Building** = now live (Info&Comms investment, above). **Power** = datacentre electricity / grid-
  connection MW — NOT a clean UK series yet (DESNZ datacentre reporting nascent, NESO queue messy);
  reserve the slot, wire when published.

### Open
- Adoption: still want a 2nd individual source (ONS OPN / Reuters) — needs a verified figure.
- Possible: harden scoring to AR(p)-bootstrap (Stanford-faithful) so persistent series stop needing
  the manual trend=False switch.

## 2026-06-21 — Transformation Tracker overhaul (Stanford-faithful method + UK tuning)
Reworked the macro tracker after reading the live Stanford "Transformation Tracker" page (12
indicators, NAPCS = *Network-Adjusted Private Capital Share* not the product classification;
shares logit-transformed; trend fit 1997→2019 + bootstrap). Implemented their method and
UK-tuned the indicator set. Now **13 indicators, all live, 0 strong / 3 mild / 10 neutral**.
- **Method change**: flows → **YoY % growth** (the smoothing); shares → **logit**; every series
  clipped to a common **SAMPLE_START=1997** (matches Stanford); scoring = `trend_score()` —
  latest value in residual-SDs above its own 1997–2019 linear trend (z≥2 strong, ≥1 mild,
  −1..1 neutral, <−1 contra). Replaces the old ad-hoc fixed thresholds.
- **New indicators**: split software into the two Stanford ratios — Software/(Software+R&D) and
  (Software+R&D)/FixedAssets (both logit); GDP now **output growth (YoY)** via ABMI; TFP & labour
  productivity now **YoY growth**; IP-equipment share now logit.
- **UK tuning** (the strategic bit): DROPPED datacentre projection → ADDED **electricity
  generation growth** (DESNZ ET 5.1, live; UK gen falling 312→286 TWh, −2.7% YoY). ADDED
  **ICT-services imports growth** (ONS BoP `FJDL`, live) — the adopter-economy channel; computer-
  services imports doubled 2019→2024 (£5.3bn→£11.2bn), **mild**, our clearest UK signal. OMITTED
  NAPCS (needs IO tables + a UK electronics supply chain that doesn't exist).
- **Files**: `sources.py` — `capital_stock_shares()` now returns ip_equipment/software_share/
  intangible_share; new `electricity_generation()` (ET 5.1 transposed-sheet parser, Table 5b
  total). `takeoff_tracker.py` rewritten (SAMPLE_START/SPLIT, `yoy()`, `trend_score()`).
  `build_dashboard.py` — contradictory colour + new section copy. Renamed Takeoff→Transformation.
- **3 mild**: ICT-services imports, 10y real yield (short sample, flagged), intangible-capital share.

### Adoption — decided, partially actioned
Audited vs Stanford (their adoption sources are mostly *individual* surveys: Gallup, Bick-Blandin-
Deming, Hartley). We already cover firms better than they do (BICS headline + DSIT ad-hoc +
BoE/FCA finance). The one real gap is a **second high-quality individual source** beyond Ofcom
(ONS OPN or Reuters Institute) — not yet wired because it needs a verified figure, not a curated
guess. Pick up: pull ONS OPN AI-use reading and add as a second individual series.

## 2026-06-20 — Canaries v1.1 (4-digit quintiles), run_all.py, methodology email
- **Canaries v1.1**: swapped the coarse 2-digit high/low split for the faithful Canaries quintile
  design at 4-digit SOC. Built SOC2020→ISCO-08 crosswalk (`reference/soc2020_isco08_crosswalk.csv`,
  412 groups, modal ISCO from ONS Vol 2 coding index) → joined ILO 2025 GenAI scores → assigned
  each occupation an exposure score → advert-weighted quintiles Q1..Q5. **Q5 most-exposed advert
  demand now -61% vs Q1 -38% (23pt gap)**, sharper than the 2-digit 16pt. Q5 occupations = data
  entry, broking, typing, underwriting (clerical/cognitive, as expected). 61/399 groups have lossy
  (<50% share) ISCO mapping — flagged. `data/canaries/occupation_exposure_quintiles.csv` lists assignments.
- **`src/run_all.py`**: one command regenerates all 3 trackers + dashboard in order. Verified clean.
- **`EMAIL_methodology.md`**: shareable methodology email covering all 3 tracks + honest limits.

### Next up
- v2 flagship: start ONS SecureLab ASHE accreditation (single-year age × 4-digit SOC × firm `ENTREF`).
- Optional: forward Adzuna API collector for the entry-level/age cut.

## 2026-06-20 — Canaries v1 (demand-side) built + unified HTML dashboard
- **Canaries v1** (`src/canaries.py`): the buildable demand-side analogue. Pulls ONS **Textkernel
  New Online Job Adverts** (monthly advert counts by 2-digit SOC 2020, 2018→2026, live via
  current-file resolver), buckets occupations into HIGH vs LOW AI-exposure (cognitive/clerical
  vs manual/care, per ILO 2025 GenAI index + UK GAISI gradient), 12-month trailing avg, indexed
  to Oct-2022. **Result: high- and low-exposure advert demand track in lockstep until ChatGPT,
  then diverge — high-exposure now -52% vs low -36% (a 16pt relative gap).** No pre-trend; clean
  divergence post-late-2022. Charts: levels + relative gap.
  - Honest gaps documented in-module: adverts≠employment; NO age/entry-level cut (adverts carry
    no age → forward Adzuna API / Lightcast); NO firm panel (→ v2 ASHE-secure flagship).
  - Exposure data: sourced ILO 2025 ISCO-08 GenAI scores (`reference/ilo2025_isco08_occupation_
    exposure.csv`); UK GAISI (arXiv 2507.22748) data not public until Q2 2026.
- **Dashboard** (`src/build_dashboard.py`): single self-contained `dashboard/index.html` (embedded
  base64 charts, no server) showing all 3 tracks + latest-value cards + the takeoff scorecard
  table. Regenerate after running the 3 trackers. Edge-headless preview confirmed clean render.

### Canaries roadmap (decided with Parth: phased)
- **v1 = this** (demand-side advert tracker, descriptive). Done.
- **v1.1**: swap 2-digit exposure tiers for precise 4-digit SOC2020 scores via SOC2020↔ISCO-08
  crosswalk onto the ILO CSV + Textkernel 4-digit sheet.
- **v2 flagship** = ASHE-secure microdata (`SN 6689` / ADR UK ASHE-PAYE): single-year age ×
  4-digit SOC × firm (`ENTREF`) panel → the real firm×time Poisson event study, ANNUAL. Needs
  ~3-month ONS accreditation — start the clock in parallel.
- Optional entry-level cut: forward Adzuna API collection or Lightcast licence.

## 2026-06-20 — Takeoff Tracker: wired live pulls, retired curated points
- New `src/sources.py` with live parsers (each with curated fallback):
  - **Capital-stock asset shares** (computer hardware N11321N, software+R&D N1173N+N1171N over
    total N11N) — ONS capital-stocks xlsx, full 1995-2024 annual series.
  - **MFP** — ONS growth-accounting; `resolve_ons_current_xlsx()` scrapes the dataset page for
    the rotating current filename, then parses Table_7 (market sector, 2022=100).
  - **10y real yield** — BoE `glcrealddata.zip`; locates the 10y column by maturity header,
    combines 2016-2024 + 2025-present spot curves, resamples quarter-end (clean 2016→2026 path).
  - **Primary energy** — DESNZ ET 1.2 via gov.uk page scrape (Annual sheet, unadjusted total).
- Added `fetch_bytes()` (cached binary) + `resolve_ons_current_xlsx()` to `ons_fetch.py`.
- Result: **10 of 11 indicators now pull live** (ONS/BoE/DESNZ); only datacentre demand stays
  curated (it's a NESO FES projection, not an observed series). Verdict unchanged: 0 strong /
  3 mild / 8 neutral. Real-yield chart now shows the full -3%→+1.5% rise, not 5 anchors.
- Cleaned up temp inspection scripts in `reference/`.

### Next up
- Optional: live datacentre demand if NESO publishes an observed series (currently projection only).
- Begin Canaries v1 (degraded): ASHE Table 20 × UK-native exposure index (arXiv 2507.22748 / GLA).
- Consider a combined index/dashboard page across the three tracks.

## 2026-06-20 — Built Adoption Monitor + Takeoff Tracker; documented Canaries method
- **Canaries method**: wrote `CANARIES_METHOD.md` — full elaboration of Brynjolfsson/Chandar/
  Chen (2025): balanced ADP firm panel, Eloundou + Anthropic Economic Index exposure layers,
  age×exposure-quintile descriptive engine (indexed to Oct-2022), and the Fact-4 Poisson
  event-study with firm-quintile + firm-time fixed effects. Flags exactly which parts the UK
  can't replicate from public data (the firm×time identification).
- **Adoption Monitor** (`src/adoption_monitor.py`): tidy CSVs + 4 charts. Firm spine = ONS BICS
  (10 dated points, 9%→25% Sep23→Dec25); individual spine = Ofcom (31%→54%); by-sector; and
  cross-country (Yotzov w34836, UK 71%). Runs clean, no network needed (curated survey data).
- **Takeoff Tracker** (`src/takeoff_tracker.py` + `src/ons_fetch.py`): 11 indicators scored
  neutral/mild/strong. **5 pulled LIVE from ONS** (GDP IHYQ, productivity LZVB, capital share
  via FZLN, business investment NPEL, PNFC return LRWW); 6 curated (MFP, real yield, computer-
  hardware & software/R&D capital shares, primary energy, NESO datacentre projection).
  Verdict: **0 strong / 3 mild / 8 neutral → no decisive UK takeoff**, echoing Stanford.
- Cracked the "missing" Takeoff vars: computer-hardware capital stock = ONS asset N11321N;
  EU KLEMS for ICT capital history; NESO FES for datacentre demand; IO Analytical Tables route
  for network-adjusted capital share (not yet built). Found the dead-API gotcha (api.ons.gov.uk
  decommissioned → www.ons.gov.uk host).
- Wrote `README.md`.

### Next up
- Takeoff: parse `reference/capital_stocks_by_asset.xlsx` for full hardware/software share
  series (replace curated points); add live BoE real-yield workbook pull.
- Canaries v1 (degraded): build ASHE Table 20 (age band × 2-digit SOC) × UK-native exposure
  index (arXiv 2507.22748 / GLA) indexed to a pre-ChatGPT base.
- Consider a simple combined dashboard / index page.

## 2026-06-20 — Feasibility audit complete
- Ran a 4-stream web audit of UK data availability → wrote `FEASIBILITY.md`. Verdict:
  - **Adoption Monitor**: ✅ clean (ONS BICS firm spine + Ofcom individual spine).
  - **Takeoff Tracker**: ✅ ~8/12 indicators clean from ONS/BoE/DESNZ; 2 partial (IP-equipment
    share — hardware buried in "machinery & equipment"), 2 hard (network-adjusted capital share).
  - **Canaries (labour)**: ⚠️ degraded — no UK ADP. Best public build = ASHE Table 20
    (age band × 2-digit SOC × earnings, annual) + PAYE-RTI-by-industry monthly proxy.
  - **Exposure layer**: UK-native arXiv 2507.22748 / GLA index (4-digit SOC 2020) beats
    crosswalking US scores; Anthropic Economic Index (Hugging Face) for automation/augmentation
    at 2-digit only.
- Recommended v1 order: Adoption Monitor → Takeoff Tracker → Canaries.

### Next up
- Parth to confirm v1 build order (recommend starting with Adoption Monitor).
- Then: pull BICS AI ad-hoc tables + Ofcom readings into a first `data/` series and chart it.

## 2026-06-20 — Project kickoff
- Created top-level repo `~/ai-economic-indicators-uk/` (tracker → own repo per convention).
- Moved source PDFs into `reference/`: `AIEI_RN01_Jun26.pdf` (Stanford AIEI Research Note #1,
  June 2026) and `CanariesintheCoalMine_Nov25.pdf` (Brynjolfsson/Chandar/Chen, Nov 2025).
  Extracted `.txt` versions alongside for searchability.
- Read both. Drafted PROJECT.md with the three-track framework + a first-pass US→UK
  data-source crosswalk.

### Next up
- Decide v1 scope (recommend: Adoption Monitor + Takeoff Tracker first — public data;
  Canaries labour analysis second, gated on UK microdata access).
- Audit UK data availability: ONS PAYE RTI age×occupation granularity; UK SOC 2020 crosswalk
  for Eloundou exposure scores; ONS productivity/capital-stock series for Takeoff.
- Confirm with Parth: scope, and whether this stays a tracker repo vs feeds a Substack post.
