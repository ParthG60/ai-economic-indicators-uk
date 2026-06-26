# The Canaries Method — what Brynjolfsson, Chandar & Chen (2025) actually do

Elaboration of the methodology in *Canaries in the Coal Mine? Six Facts about the Recent
Employment Effects of Artificial Intelligence* (Nov 2025), the paper the Stanford Canaries
Dashboard operationalises. This is the blueprint we'd need to approximate for the UK — so it's
worth being precise about each moving part and where UK data forces a compromise (see
`FEASIBILITY.md`).

## The core idea in one line
Take a near-universal, high-frequency **payroll panel**, tag every worker with their **occupation's
AI exposure** and their **age**, then watch whether employment in high-exposure occupations
diverges from low-exposure ones — and whether that divergence is concentrated among the young.

## 1. The data: a balanced ADP payroll panel
- **Source.** ADP, the largest US payroll processor (~25M workers). Individual-level, monthly.
- **Balanced firm panel.** They keep only firms with earnings records in *every* month from
  **Jan 2021 → Sep 2025**. This is the central design choice: it strips out firms entering/leaving
  ADP, so measured changes are *within-firm* employment changes, not artefacts of ADP's client
  churn. (Cost: it under-weights startups and deaths — a survivorship lens.)
- **Worker restrictions.** Positive earnings; exclude part-timers; age < 70. ~3.5–5M workers/month.
- **Occupation tagging.** ADP records job titles for ~70% of workers (7,000+ standardised titles);
  ADP's team maps each to a **2010 SOC** code using title + description + industry + location.
  Workers without a title are dropped. This is the linchpin the UK lacks — no UK payroll source
  (PAYE RTI) carries occupation at all.
- **Birth month** is imputed from the US CDC birth-month distribution (privacy: they see birth
  year, not date) so age bands are clean.

## 2. The exposure layer (two independent measures)
1. **Eloundou et al. (2024) "GPTs are GPTs."** AI exposure estimated per O*NET *task* (GPT-4
   validated against human labels), aggregated to occupation. They use the **GPT-4-based β
   measure** at the **2018 SOC** level.
2. **Anthropic Economic Index (Handa et al. 2025).** From millions of real Claude conversations,
   the share of queries mapping to each O*NET task → aggregated to occupation usage shares.
   Crucially it splits each task's usage into **automative / augmentative / neither** — letting them
   test whether *how* AI is used (substitute vs complement) predicts employment, not just *how
   much*. (Directive + Feedback-Loop = automation; Task-Iteration, Learning, Validation =
   augmentation.)
- A **BLS 2010→2018 SOC crosswalk** merges exposure scores onto the payroll data.
- Occupations are then sorted into **AI-exposure quintiles** (employment-weighted).

## 3. The descriptive engine (Facts 1–3, 5)
- **Normalisation.** Employment per (age group × exposure quintile) is indexed to **1.0 in
  October 2022** (just before ChatGPT) and tracked monthly. Everything is a *relative* trajectory
  from that baseline, which is why the charts read as "divergence since ChatGPT."
- **The cut that matters.** Age group × exposure quintile. The headline is that the lines fan apart
  for **22–25-year-olds** (top-2 exposure quintiles fall ~6%, bottom quintiles rise 5–13%) but
  barely move for workers 35+. Older workers act as the within-occupation control.
- **Fact 3 (usage type).** Re-run the same cut but rank occupations by the AEI **automation ratio**
  vs **augmentation ratio**. Automation-skewed occupations show the youth declines; augmentation-
  skewed ones don't. Same machinery, different exposure variable.
- **Fact 5 (wages).** Repeat on real annual base salary (PCE-deflated to 2017 $). Finding: little
  divergence — adjustment shows up in *headcount, not pay* (wage stickiness).

## 4. The causal-ish core (Fact 4): a Poisson event study with firm×time effects
The descriptive divergence could just be that AI-exposed young workers happen to sit in firms hit
by other shocks (e.g. rate-sensitive sectors). To rule out that class of confounder, for each age
group they estimate:

```
log( E[ y_{f,q,t} ] ) = Σ_{q'≠1} Σ_{j≠-1} γ_{q',j} · 1{t=j} · 1{q'=q}  +  α_{f,q}  +  β_{f,t}  +  ε
```

- `f` = firm, `q` = exposure quintile, `t` = month; **t = −1 is October 2022** (the omitted base).
- `y` = employment count in that firm × quintile × month.
- **α_{f,q}** (firm-quintile effects) absorb baseline hiring differences across quintiles within a firm.
- **β_{f,t}** (firm-time effects) absorb *any* shock hitting all of a firm's workers equally in a month
  — interest rates, sector demand, a layoff round. This is the workhorse: it means γ is identified
  off **within-firm, within-month** differences between exposure quintiles.
- **γ_{q,t}** — the coefficients of interest — trace the differential employment path of quintile `q`
  relative to the least-exposed quintile, relative to Oct 2022.
- **Why Poisson** (not OLS-in-logs): employment cells contain zeros; Poisson handles them and is
  the recommended estimator (Chen & Roth 2024). SEs **clustered by firm**.
- **Sample restrictions for the regression.** Firms must hire ≥10 workers in the age group in every
  period, and Σ_t y ≥ 100 per quintile (≈2 workers/quintile/month). Results robust to these.
- **Result.** For 22–25s, top quintiles show a **~15 log-point** relative employment decline, large
  and significant; other age groups small and insignificant.

## 5. Robustness (Fact 6) — the alternative-explanation gauntlet
Each is "redo the cut while removing/conditioning on X":
- **Drop tech occupations** (2010 SOC 15-1xxx) and **drop IT/computer-systems firms** (NAICS 51,
  5415) → pattern holds (not just a software-hiring-slump story).
- **Telework**: split by Dingel-Neiman remotability → not purely a remote-work story.
- **Placebo in time**: the exposure taxonomy did *not* predict youth employment before ~2022
  (incl. the COVID unemployment spike) → not a pre-existing trend.
- **College share**: holds for high- and low-college occupations; for low-college, divergence
  extends up to age ~40.

## 6. What this forces for a UK replication
The method needs four things layered on one dataset: **(a) within-firm panel structure, (b) monthly
frequency, (c) occupation at fine granularity, (d) worker age.** The UK has no single source with all
four. The faithful-but-degraded UK path (see `FEASIBILITY.md`):
- **Descriptive engine (Facts 1–2):** ASHE Table 20 gives **age band × 2-digit SOC × employment/
  earnings**, annual. Index to a pre-ChatGPT base year, sort 2-digit SOC into exposure quintiles
  using the **UK-native arXiv 2507.22748 / GLA SOC-2020 exposure index**, track the youngest band
  (22–29). Monthly cadence only as a **PAYE-RTI-by-industry** proxy (no occupation).
- **Fact 3 (usage type):** attach **Anthropic Economic Index** automation/augmentation at 2-digit SOC.
- **Fact 4 (firm×time Poisson):** *not* reproducible publicly — needs firm identifiers in microdata.
  Requires ONS SecureLab (LFS/APS) accreditation (~3–4 mo), and even then it's survey, not payroll,
  so the firm×time design is weak. This is the part of the Canaries method the UK genuinely can't
  match without bespoke data access.

**Bottom line:** we can reproduce the *descriptive* Canaries story for the UK at coarser resolution
(age band × 2-digit occupation × exposure, annual). We cannot reproduce the *identification* (the
firm×time Poisson event study) from public data — that's the honest ceiling.
