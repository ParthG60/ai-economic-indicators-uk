# AI Economic Indicators — UK

## Goal
Replicate the Stanford Digital Economy Lab's **AI Economic Indicators (AIEI)** for the
**UK economy**. Stanford's project: https://digitaleconomy.stanford.edu/project/indicators/

The AIEI is a high-frequency measurement dashboard tracking AI's economic footprint along
three tracks. This project builds a UK analogue using UK data sources.

## The Stanford framework (what we're replicating)
Three components, from Research Note #1 (June 2026):

1. **Canaries Dashboard — labour market.** Monthly employment trends sliced by worker age
   × occupational AI exposure. Core finding: early-career workers (22–25) in AI-exposed
   occupations show ~16% relative employment declines post-ChatGPT; older workers stable.
   Automation-type usage correlates with declines; augmentation does not. Built on ADP
   payroll microdata + Eloundou et al. (2024) exposure scores + Anthropic Economic Index
   automation/augmentation ratios.

2. **Transformation Tracker — macro.** 12 aggregate indicators of "AI takeoff" (explosive
   capital-driven growth): output/TFP/labour-productivity growth, capital share, IP-equipment
   & two software shares, real rates, energy & electricity generation, network-adjusted
   capital share. Flows shown as YoY growth, shares logit-transformed; each scored by how far
   today's value sits above its 1997–2019 trend (residual SDs → neutral/mild/strong/contra).
   Rationale traces to Nordhaus (2021) "Are We Approaching an Economic Singularity?".

   **UK-tuned indicator set (ours, 13).** The US and UK sit on opposite sides of the AI supply
   chain (US = producer, UK = adopter), so we diverge from a blind 12-clone:
   - DROP the NESO datacentre-demand projection (a forecast, not observed) → ADD electricity
     **generation** growth (DESNZ ET 5.1), the observed analogue. UK generation is flat/falling,
     a noisier AI proxy than in the US.
   - ADD **ICT-services imports** growth (ONS BoP `FJDL`): the UK's AI capital deepening arrives
     as imported cloud/compute, not domestic capital stock. (Computer-services imports doubled
     2019→2024, £5.3bn→£11.2bn — our clearest UK takeoff signal.)
   - OMIT Network-Adjusted Private Capital Share (Stanford #6/#7): needs IO tables + a domestic
     electronics supply chain the UK lacks — structurally weak signal.
   - FLAG the capital share as noisier than the US (North Sea oil, finance, housing) and the
     domestic-capital shares (IP-equipment, software) as structurally muted (AI hardware imported).

3. **Adoption Monitor — surveys.** Individual + firm AI adoption rates, frequency of use,
   by application and country.

## UK replication strategy (draft — to refine)
| Stanford input | US source | UK analogue (candidate) |
|---|---|---|
| Payroll microdata | ADP | HMRC PAYE RTI (ONS earnings/employment), ASHE, LFS |
| Occupational AI exposure | Eloundou et al. SOC scores | Map to UK SOC 2020; ONS has published AI-exposure work |
| Automation/augmentation | Anthropic Economic Index | AEI is occupation-level, reusable |
| Macro takeoff series | BEA/BLS/FRED | ONS national accounts, productivity, capital stock |
| Adoption surveys | Gallup/Pew/Bick et al. | ONS BICS (Business Insights), Lloyds, gov.uk surveys |

## Constraints / open questions
- No UK equivalent of ADP microdata access — biggest gap. Need to assess what ONS PAYE RTI
  granularity allows (age × occupation cross-tabs).
- Occupation crosswalk US SOC → UK SOC 2020 required for exposure scores.
- Decide scope of v1: likely Adoption Monitor + Takeoff Tracker first (public macro data),
  Canaries-style labour analysis second (microdata-constrained).

## Status
See STATUS.md. Reference papers in `reference/` (AIEI note + Canaries paper, with .txt extracts).
