# UK AIEI — Feasibility Audit (2026-06-20)

Can we replicate Stanford's three-track AI Economic Indicators for the UK from public data?
Verdict per track below. Sources are real, checked URLs (audited via web research).

**Overall: Adoption Monitor and Takeoff Tracker are cleanly buildable from public data.
The Canaries labour track is the hard one — no UK equivalent of ADP exists, so it degrades
to a coarser annual age-band × 2-digit-occupation analysis.**

---

## Track 1 — Canaries Dashboard (labour) — ⚠️ PARTIAL / degraded
Stanford needs: single-year-age (22–25) × granular occupation × **monthly payroll** microdata.
No UK public source has all three. The split:

- **PAYE RTI** (HMRC via ONS): monthly, ~2–3 wk lag, near-universal — but **NO occupation**
  (industry/SIC only, derived from company sector). Has age bands + industry + region.
- **ASHE Table 20**: the only public table natively crossing **age band × 2-digit SOC ×
  earnings**. Annual, ~12-mo lag. Youngest band is 22–29 (vs Stanford's 22–25).
- **APS/LFS (Nomis)**: 4-digit SOC exists but age×4-digit cells too thin to trust; reliable
  only ~2-digit × age bands. Annual/rolling-quarterly.
- **Secure microdata (ONS SRS / UK Data Service SecureLab)**: unlocks single-year-age × fine
  SOC, but it's still *survey* (quarterly, sampled), needs ~3–4 mo accreditation, and outputs
  are disclosure-checked → **no live auto-updating public dashboard** from inside.

**Buildable v1:** ASHE Table 20 (age band × 2-digit SOC × exposure) for the annual "what" +
PAYE RTI (young-age-band employment by AI-exposed *industry*) for a monthly "when" proxy.
A true ADP-equivalent is not achievable from public data — this is the headline constraint.

## Track 2 — Takeoff Tracker (macro) — ✅ MOSTLY CLEAN (~8/12, 10/12 with effort)
Stanford tracks 12 indicators. UK mapping:

| Tier | Count | Indicators (UK source) |
|---|---|---|
| Clean | 8 | GDP growth (ONS IHYQ); MFP/TFP (ONS, *experimental*, lagged); labour productivity (ONS output/hr); real rate (BoE index-linked gilt curve); capital share (1 − ONS labour share); software & R&D shares of fixed assets (ONS capital stocks + GERD); primary energy + electricity generation (DESNZ Energy Trends/DUKES) |
| Partial | 2 | **IP/computing-equipment share of equipment stock** — hardware is buried inside ONS "other machinery & equipment" (the single most AI-relevant indicator, ironically weakest in UK data; finer ICT splits only in EU KLEMS / source surveys). Datacentre-specific electricity not split out. |
| Hard | 2 | Network-Adjusted Private Capital Share (electronics; max sector) — bespoke Stanford input-output constructs; ONS publishes raw IO Analytical Tables (annual, ~3-yr lag) but you'd rebuild the network method yourself. |

Caveat: UK MFP/capital-stock series are annual, 6–12 mo lagged, "experimental" — lower
frequency than the US series Stanford leans on. Bonus UK candidates: business investment,
PNFC profitability/profit share, GERD.

## Track 3 — Adoption Monitor (surveys) — ✅ CLEAN
- **Firm spine: ONS BICS** — fortnightly survey, AI question ~quarterly since Sept 2023,
  consistent wording, firm-size + SIC breakdowns, ~2 wk lag. Trajectory ~10% (Sep'23) →
  18% (Mar'25), 31% for 250+ firms. The only true UK firm time series.
- **Individual spine: Ofcom** Online Experiences Tracker (biannual) + Online Nation (annual):
  31% (2024) → 54% (2025) of UK adults use AI tools. Lloyds Consumer Digital Index adds a
  long-running annual consumer reading (money-domain).
- **Sector depth (cross-sectional enrichment):** DSIT AI Adoption Research (annual-ish,
  ~16% of firms, by size/sector); BoE/FCA AI in UK Financial Services (2019/22/24: 58%→75%).
- **Cross-country benchmark:** Yotzov et al. "Firm Data on AI" (NBER w34836, incl. UK via
  BoE Decision Maker Panel); ECB SAFE for EU.

Gap vs Stanford: no single high-frequency UK source for *frequency-of-use* / *by-application*.
Stitch BICS + Ofcom + DSIT/BoE-FCA + Yotzov to reproduce the structure.

---

## AI-exposure layer (feeds Track 1)
- **Best UK-native (no crosswalk pain):** arXiv 2507.22748 / GLA Economics generative-AI
  exposure index — built natively at **4-digit SOC 2020** on the ILO 2025 task framework.
  Use as primary exposure layer (Eloundou's role, but UK-keyed).
- **Automation vs augmentation (Stanford's AEI component):** Anthropic Economic Index on
  Hugging Face (`Anthropic/EconomicIndex`, latest Mar 2026) — but keyed to US O*NET and only
  released at **2-digit SOC**, so it attaches to UK occupations only as a major-group overlay.
- **If faithfully porting Stanford's exact inputs:** Eloundou + Felten AIOE US-SOC scores →
  UK SOC 2020 via **NFER CASCOT crosswalk** (one-to-many, 64 codes unmatched — indicative,
  not exact). DSIT 2023 UK exposure work exists but is SOC **2010**.

---

## Recommended v1 build order
1. **Adoption Monitor** — fastest, fully public (BICS + Ofcom backbone). Ships a real tracker.
2. **Takeoff Tracker** — public ONS/BoE/DESNZ series; ~8 indicators clean, flag the 4 weak.
3. **Canaries (labour)** — ASHE Table 20 × UK-native exposure index (annual), PAYE-RTI-by-
   industry monthly proxy. Be explicit it's a degraded analogue, not an ADP replica.

Microdata SecureLab accreditation (~3–4 mo) is a later option if we want true single-year-age
× fine-SOC analysis — but it can't feed a live public dashboard.
