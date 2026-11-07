# Don't Tell the Bees: bee records and honey production in Honduras (data package)

Data behind *Don't Tell the Bees*, a map of every bee record in Honduras on GBIF, made for the
#30DayMapChallenge 2026 (Day 1, Points), and its interactive companion. It pairs where bees have
been **recorded** (3,491 GBIF records, 1890–2026) with where **honey** is produced (INE, Censo
Agropecuario Nacional 2023–2024, by department).

The records show where people looked, not where bees live. Empty areas on the map are unrecorded,
not empty of bees.

**Author:** Yanira A. Rivera · ORCID [0000-0003-3309-5256](https://orcid.org/0000-0003-3309-5256)
**Interactive map:** https://yani-rivera.github.io/SDG15-DONT-TELL-THE-BEES/
**Code:** [SDG15-HND-OBSERVATIONS](https://github.com/yani-rivera/SDG15-HND-OBSERVATIONS), v0.4.1
(`package_data.py` made this package; `package_provenance.json` records the exact inputs)

## Files

| File | What |
|---|---|
| `records.csv` | All 3,491 records of the GBIF download, all 50 columns, comma-separated UTF-8. Same rows and values as GBIF's tab-separated file; only the separator changed. |
| `source_datasets.csv` | The 43 GBIF datasets the records come from: `datasetKey`, number of records, licence(s). |
| `taxa_status.csv` | The 184 taxa, their record counts, and the native status used on the map, with where it came from (`species`, `genus` or `default`). |
| `honey_ine_2023_2024.csv` | Honey production by department, transcribed from the INE table. The first line, starting with `#`, gives the source. |
| `package_provenance.json` | Code version, config hash, SHA-256 of every input and output, row counts. |
| `README.md` | This file. |

## Sources

- **Bee records:** GBIF.org (27 October 2026) GBIF Occurrence Download
  https://doi.org/10.15468/dl.2kgdqn. Query: family Apidae, country Honduras. Download key
  `0009936-261023074918325`. Not filtered after download.
- **Honey:** Instituto Nacional de Estadística con información del Censo Agropecuario Nacional
  (CAN), año agrícola 2023-2024. Transcribed by Yanira A. Rivera; the sums match INE's published
  totals (2,959 farms, 845,015.9 litres) and every per-farm average matches litres ÷ farms.
- **Departments** (used to draw the honey layer, not included here): SINIT (2016) via OCHA HDX,
  Honduras subnational administrative boundaries (COD-AB). Join key `adm1_pcode`.

## Columns

**`records.csv`** follows GBIF's simple download format (Darwin Core terms). The ones the map uses:
`gbifID` (link: https://www.gbif.org/occurrence/<gbifID>), `datasetKey`, `species`, `genus`,
`scientificName`, `taxonRank`, `decimalLatitude`, `decimalLongitude` (WGS84),
`coordinateUncertaintyInMeters`, `eventDate`, `year`, `month`, `basisOfRecord`,
`institutionCode`, `collectionCode`, `recordedBy`, `license`, `rightsHolder`.

**`honey_ine_2023_2024.csv`:** `adm1_pcode` (department code, two digits), `departamento`,
`explotaciones` (farms with honey production), `produccion_litros` (litres),
`promedio_litros_por_explotacion` (litres per farm, as published).

## Method notes

- **Native status:** *Apis mellifera* (Africanized honey bee) and genus-level *Apis* records are
  introduced; every other Apidae taxon is treated as native by default. `taxa_status.csv` shows
  which taxa got the default, for review. *Eulaema cingulata* carries a note: identification not
  verified.
- **Foraging rings** (3 km and 7 km) on the map are illustrative: honey bees often fly 3 km or
  more; many native bees, such as stingless bees, stay much closer.
  *[Source for the ring distances: to be added.]*
- The hidden bee drawn on the poster is an illustration, not a record. It is not in this data.

## Caveats

- **Sampling bias:** records cluster where entomologists and naturalists worked (Zamorano, Cusuco,
  the Tegucigalpa corridor). La Mosquitia is nearly empty.
- **1994:** 531 of the year's 541 records come from one collecting effort catalogued by KU (Snow
  Entomological Museum, University of Kansas), not from more bees.
- 696 records have no coordinates and 990 have no year; 64 have a location uncertainty over 10 km;
  612 are possible duplicates (same species, place and date, often a series of museum specimens).
- 1,854 records are preserved specimens and 1,492 human observations (1,210 of them from
  iNaturalist).
- **Honey:** Islas de la Bahía has no row in the INE table. Copán produces 61.4% of the litres.
  Honey is reported per department, so it cannot be matched to individual records.

## Licence

- `records.csv`, `source_datasets.csv`, `taxa_status.csv`: **CC BY-NC 4.0**. The GBIF records
  carry CC0, CC BY or CC BY-NC licences (1,628 of 3,491 are CC BY-NC); the download's overall
  licence is the most restrictive one. Each record's own licence and rights holder are in its
  `license` and `rightsHolder` columns.
- `honey_ine_2023_2024.csv`: figures from the Instituto Nacional de Estadística (INE), reproduced
  with source attribution.

## How to cite

Cite this package (its Zenodo DOI) and the GBIF download it is built on:

> GBIF.org (27 October 2026) GBIF Occurrence Download https://doi.org/10.15468/dl.2kgdqn
