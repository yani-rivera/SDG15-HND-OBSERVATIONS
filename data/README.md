# data/

Input files go here. Nothing in this folder is tracked by Git except this note: the data is cited
by DOI and archived on Zenodo, never stored with the code. Keep each file's original name; the
configs refer to them by these paths, and `provenance.json` records the SHA-256 of every file a
build used.

## Don't Tell the Bees (`config/bees.yaml`)

| File | What | Where to get it |
|---|---|---|
| `0009936-261023074918325.csv` | GBIF occurrence download, family Apidae, Honduras (3,491 records) | https://doi.org/10.15468/dl.2kgdqn (download the "simple" CSV and unzip it) |
| `honey_ine_2023_2024.csv` | Honey production by department | Instituto Nacional de Estadística, Censo Agropecuario Nacional (CAN), año agrícola 2023-2024; the transcribed table is in the bee map's data package on Zenodo |
| `HND_ADM01.geojson` | Department boundaries (fields `ADM1_PCODE`, `ADM1_ES`) | SINIT (2016) via OCHA HDX: "Honduras - Subnational Administrative Boundaries", admin level 1, saved as GeoJSON |

## What I Still Like to Hear (`config/birds.yaml`)

| File | What | Where to get it |
|---|---|---|
| `0021590-260928105237408.csv` | GBIF occurrence download, class Aves, Honduras, polygon around Tegucigalpa (293,909 records, 12 datasets, CC BY-NC 4.0) | https://doi.org/10.15468/dl.s23z73 (download the "simple" CSV and unzip it) |
| `tgucanopy202611.tiff` | Tree canopy height (m), 10 m, EPSG:32616 | Meta and World Resources Institute, Canopy Height Maps v2 (CHMv2), clipped to Tegucigalpa and resampled to 10 m |

## A map of your own

Put your GBIF download here and point `gbif.file` in your copy of `config/template.yaml` at it.
If a file is missing, the build stops and lists what it needs.
