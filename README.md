# Don't Tell the Bees: interactive companion

Every bee record in Honduras on GBIF, 1890–2026, on one interactive map: records over time, the
most recorded species, native and introduced bees, 3 and 7 km foraging rings when zoomed in, and
honey production by department underneath. Records show where people looked, not where bees live.

Companion to the poster *Don't Tell the Bees*, #30DayMapChallenge 2026, Day 1 (Points).

**Live map:** https://yani-rivera.github.io/SDG15-DONT-TELL-THE-BEES/

## This repository holds only the built page

`index.html` and `provenance.json` (added by the first build) are written by the builder, not edited by hand. To change the
map, change the code or its config and rebuild:

- **Code:** [SDG15-HND-OBSERVATIONS](https://yani-rivera.github.io/SDG15-HND-OBSERVATIONS/), config
  `config/bees.yaml`. `provenance.json` here records the exact code version, config hash and input
  SHA-256 used for this page.
- **Data:** GBIF.org (27 October 2026) GBIF Occurrence Download
  https://doi.org/10.15468/dl.2kgdqn (3,491 records from 43 datasets). Honey: Instituto Nacional
  de Estadística con información del Censo Agropecuario Nacional (CAN), año agrícola 2023-2024.
  Departments: SINIT (2016) via OCHA HDX. Records and honey table archived with notes on Zenodo:
  *[data DOI, added once published]*.

## Licence

The bee records carry CC0, CC BY and CC BY-NC licences; the download's overall licence is
**CC BY-NC 4.0**, and so is this page's content. Honey figures are INE's, reproduced with source
attribution. Cite the GBIF download DOI above when using the records.

Map and data curation: Yanira A. Rivera · ORCID
[0000-0003-3309-5256](https://orcid.org/0000-0003-3309-5256). Interactive companion built with
AI-assisted code.
