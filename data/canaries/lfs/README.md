# Labour Force Survey microdata goes here (not included)

The labour-market track is built from **LFS quarterly person files**, which are licensed
under the UK Data Service (UKDS) **End User Licence** to a single named researcher. They
**cannot be redistributed**, so they are deliberately excluded from this repository.

## How to obtain them yourself

1. Register for a free account at the [UK Data Service](https://ukdataservice.ac.uk/) and
   agree to the End User Licence.
2. Download the **Quarterly Labour Force Survey** person files (study series 2000), Stata
   format, for the quarters you want (this project uses 2019 Q1 through the latest available).
3. Drop the downloaded `.zip` (or unzipped `.dta`) files into this folder.
4. Run `python src/canaries_lfs_hiring.py` (and the other `canaries_lfs_*.py` scripts) to
   regenerate the aggregated CSVs in `data/canaries/` that the dashboard reads.

The scripts only ever write **aggregated, indexed statistics** (weighted employment by
exposure quintile, age band, and quarter). No person-level record leaves the pipeline, which
is what keeps the published outputs within the licence.
