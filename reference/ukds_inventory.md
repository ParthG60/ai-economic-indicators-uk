# UK Data Service access — inventory and tracker fit

Account: *(username redacted)* (registered 2026-06-23). Tier: **End User Licence (Safeguarded)**.
Activation still pending (click the link in the 23 Jun email, tick the EUL boxes, register).

UKDS does not push data. You log into the catalogue, accept each study's licence, and
download the zip yourself. There is no open API for the microdata, so the pull is manual.
Documentation (variable guides) is public and already downloaded to `reference/ukds_docs/`.

## What the EUL tier unlocks, ranked by fit to our tracker

| Priority | Study | SN | What it gives us | Track |
|---|---|---|---|---|
| 1 | Quarterly Labour Force Survey (individual quarters) | 9388 = Jan–Mar 2025; grab latest 4–8 quarters | `SOC20M` 4-digit × `AGE` single-year × `HIQUL15D` qualification in one record | Canaries age cut |
| 2 | LFS Two-Quarter Longitudinal | 9302 (and rolling) | Same people across 2 quarters → real occupation exits/flows | Canaries movers |
| 3 | LFS Five-Quarter Longitudinal | 9486 | Year-on-year transitions for the same person | Canaries movers |
| 4 | Understanding Society (UKHLS) main, EUL | 6614 | Person-level tech-use / home-working over time | Adoption (usage) |
| — | Annual Population Survey microdata | (EUL quarters) | occupation × region × age cross-tabs | nice-to-have |

### Does NOT help
- **Transformation track**: all ONS macro aggregates we already pull live from ons.gov.uk, more current than UKDS holds them.
- **Firm panel (v3)**: ASHE, pooled QLFS (SN 6727), pooled APS (SN 6721) are **Secure Access**, not EUL. Needs separate accreditation (months).

## Caveat that changes the plan
UKHLS **EUL (SN 6614) strips detailed SOC and SIC codes** (kept only in the Secure version).
So UKHLS cannot carry the 4-digit occupation × exposure join. Use it only for the
adoption/tech-use angle, not the Canaries occupation crosswalk. The LFS EUL quarterly files
**do** keep `SOC20M` at 4 digits and single-year `AGE`, which is why LFS is the right source
for the age cut.

## LFS variable shopping list (confirmed from Vol 3, 2022)
Select these when downloading, or just take the full file and the pipeline subsets them:

- `SOC20M` — main job occupation, SOC2020, 4-digit unit group (joins our exposure quintiles)
- `AGE` — single year of age; `AGES` — banded fallback
- `ILODEFR` — ILO economic activity (1 = in employment)
- `HIQUL15D` — highest qualification, detailed (for the qualification cut)
- `INDC07M` — industry, SIC2007 main
- `NSECM` — socio-economic class (optional)
- `GRSSWK` — gross weekly pay; `PIWTxx` — income weight (pay analysis only)
- `PWTxx` — person weight; the `xx` is the reweighting vintage (e.g. PWT24). Pipeline auto-detects the `PWT*` column.

Data caveat: LFS response rates fell badly in 2023–24, so single-quarter estimates from
that window are volatile. Pool quarters and lean on the longitudinal files where possible.

## Source links
- QLFS Jan–Mar 2025: https://datacatalogue.ukdataservice.ac.uk/studies/study/9388
- LFS 2-Qtr Longitudinal: https://datacatalogue.ukdataservice.ac.uk/studies/study/9302
- LFS 5-Qtr Longitudinal: https://datacatalogue.ukdataservice.ac.uk/studies/study/9486
- UKHLS main EUL: https://datacatalogue.ukdataservice.ac.uk/studies/study/6614
- LFS Vol 3 variables (2022): https://doc.ukdataservice.ac.uk/doc/7674/mrdoc/pdf/lfs_vol3_variabledetails2022js.pdf
