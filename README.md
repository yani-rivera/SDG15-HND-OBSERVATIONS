# SDG15-HND-OBSERVATIONS

Interactive maps of biodiversity **observations** in Honduras (SDG 15, Life on land), built with
**gbif_companion**. They show where species have been recorded, which is where people looked: an
empty area means unrecorded, not absent.

**Maps:** https://yani-rivera.github.io/SDG15-HND-OBSERVATIONS/
- *Don't Tell the Bees*: https://yani-rivera.github.io/SDG15-HND-OBSERVATIONS/bees/


**Version 0.4.1** (2026-11-07) · see [CHANGELOG.md](CHANGELOG.md) · `python build.py --version`

Interactive companion maps from **any GBIF occurrence download**. One config per map:

- `config/bees.yaml`: *Don't Tell the Bees* (#30DayMapChallenge 2026, Day 1), with native status
  and foraging rings.
- `config/birds.yaml`: *What I Still Like to Hear* (Day 11, Sound), Tegucigalpa's parakeets,
  zanates, woodpeckers, owls and doves, with an effort-corrected seasonality view.

<<<<<<< HEAD
The challenge entries are the hand-made posters; these pages were built with AI-assisted code and
say so.
=======
- **Code:** [SDG15-HND-OBSERVATIONS](https://yani-rivera.github.io/SDG15-HND-OBSERVATIONS), config
  `config/bees.yaml`. `provenance.json` here records the exact code version, config hash and input
  SHA-256 used for this page.
- **Data:** GBIF.org (27 October 2026) GBIF Occurrence Download
  https://doi.org/10.15468/dl.2kgdqn (3,491 records from 43 datasets). Honey: Instituto Nacional
  de Estadística con información del Censo Agropecuario Nacional (CAN), año agrícola 2023-2024.
  Departments: SINIT (2016) via OCHA HDX. Records and honey table archived with notes on Zenodo:
  *[data DOI, added once published]*.
>>>>>>> a3966ee139d2df4a753e86656de7dc7ce7516d15

## Three separate parts

This repository holds the code and configs, plus the **built page** (`index.html` and
`provenance.json`, served by GitHub Pages); the data lives elsewhere. A change to the code never alters the published map until it is rebuilt on
purpose:

| Part | Where | Licence |
|---|---|---|
| Code (this repo) | GitHub + a Zenodo DOI per release | MIT |
| Site: the built pages | one folder per map (`bees/`, `birds/`) plus a front page `index.html`, served by GitHub Pages | follows its data |
| Data | GBIF download (cite its DOI) + a Zenodo data package per map | per source |

Every built page carries a `provenance.json` with the code version, config hash and input SHA-256,
so any published map can be rebuilt exactly. Data files never go in this repository: `data/` is
ignored by Git; `data/README.md` says where to get each file.

## Make one

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# put the input files in data/ (see data/README.md)
python build.py --config config/bees.yaml
open outputs/bees/<run_id>/map.html
```

With `run.publish_dir` set, the build also copies the page into that folder as `index.html`, with
its `provenance.json` and an empty `.nojekyll`. Each map has its own folder: the bees publish to
`bees/`, the birds to `birds/` (created on the first build); commit and push to update the live
maps. Never edit a built page by hand: rebuild instead. The front page `index.html` at the root is
hand-written: add a card to it when a new map is published.

## Archive the data

```bash
python package_data.py --config config/bees.yaml --out ../dont-tell-the-bees-data
```

Writes the map's data package outside this repository: `records.csv` (the GBIF download, all
columns, comma-separated), `source_datasets.csv` (records and licences per GBIF dataset),
`taxa_status.csv`, the area table, and `package_provenance.json`. Add a hand-written `README.md`
(method, caveats, licences) before uploading it to Zenodo.

For your own region or taxon: download occurrences from gbif.org (the "simple" CSV works; a
Darwin Core Archive's `occurrence.txt` too), copy `config/bees.yaml`, change `gbif.file`, the
citation/DOI, the filter, the status table, title and bounds, and build.

## What the page does

- **Lollipop of records over time** (per year; per month when the data covers a single year).
  Hover a stem for the count and the **top source collection** that year; click to filter.
- **Most recorded species** for the selected period, with native status, footnotes and a tie note.
  Click a species to map only it.
- **Colour by** native status or record type (museum specimen, human observation, …).
- **Foraging rings** (3 and 7 km by default) drawn at true ground distance, shown from zoom 8.
- **Record popups:** taxon, status, date, place, record type, collection, observer, location
  uncertainty, links to the GBIF record and the original (e.g. iNaturalist).
- Counts of records **without coordinates** and **without a year**, so nothing silently disappears.
- **Groups** (optional, `groups:` in the config): one colour per group, a group switcher, and the
  table shows each species' group. A record joins the first group whose `match` fits
  (e.g. `family: [Psittacidae]` or `species: [Quiscalus mexicanus]`). An optional `note:` per group
  (what they eat, where they sleep) shows under the buttons when the group is selected.
- **By month (all years):** with a group or species selected and all years shown, the stems show
  its **share of all records that month** in the download, a simple correction for observers going
  out more in some months. This needs a download wider than the groups (e.g. all birds in the area);
  `keep_only_groups: true` then maps only the groups while the totals still use everything.

- **Area layer** (optional, `areas:` in the config): a choropleth under the records, e.g. honey
  production by department, with a switch between variables (or Off), its own legend, and
  department popups. Boundaries from a GeoJSON (simplified for the web), values from a CSV,
  **joined by code, never by name**. `areas_report.csv` lists join notes; `check_totals` verifies
  the table against its published totals.
- **Raster overlay** (optional, `overlay:` in the config): e.g. tree canopy height under the
  records, with an on/off switch and a gradient legend. Any single-band GeoTIFF in any projection:
  it is reprojected to Web Mercator (nearest neighbour, values not smoothed), coloured with
  `stretch` and `colors`, and cells below `min_value` are transparent. Keep it small (city scale,
  ~10 m): it is embedded in the page. Add `sample_radius_m` to sample it at every record
  (value at the point and highest within the radius, on the original raster): popups show both
  and the panel shows the share of shown records near the layer.

## Each build writes

| File | What |
|---|---|
| `map.html` | the page (one file; needs internet for MapLibre and the OpenFreeMap base map) |
| `<config>.yaml` | exact config used |
| `provenance.json` | versions, config hash, input SHA-256, GBIF download key, DOI, citation, checks |
| `status_review.csv` | every taxon whose native status came from the default rule, for review |

## Notes for the bee map

- Input: GBIF download `0009936-261023074918325`, family Apidae, Honduras: 3,491 records,
  1890–2026; 696 without coordinates, 990 without a year, 64 with location uncertainty over 10 km,
  612 possible duplicates (same species, place and date; often a series of museum specimens).
- **1994 spike:** 531 of 541 records come from KU / SEMC (Snow Entomological Museum, University of
  Kansas): one collecting effort, not a bee boom.
- **Native status rule:** *Apis* (*A. mellifera*, Africanized) = introduced; every other Apidae
  taxon = native. Review `status_review.csv`.
- Record licences vary (CC0, CC BY, CC BY-NC); cite the GBIF download DOI.
- **Honey layer:** Instituto Nacional de Estadística con información del Censo Agropecuario
  Nacional (CAN), año agrícola 2023-2024, transcribed to
  `data/honey_ine_2023_2024.csv` (17 departments; sums match the published totals of 2,959 farms
  and 845,015.9 L; every per-farm average matches litres ÷ farms). Islas de la Bahía has no row.
  Copán produces 61.4% of the honey. Boundaries: `data/HND_ADM01.geojson`, SINIT 2016 via OCHA HDX
  (46 MB, not in the zip: use your own copy).

## Notes for the bird map

- Input: GBIF download `0021590-260928105237408`: all birds (class Aves) in a box around
  Tegucigalpa, 293,909 records, 1898–2026, ~99% eBird. Five groups kept: 107,265 records.
  **Add the download's DOI** to `config/birds.yaml` (shown on its gbif.org page).
- The 158 MB download is not in the zip: put it in `data/` with its original name.
- 2025–2026 look small because eBird reaches GBIF in yearly batches. Owls are under-recorded.
- 40,716 "possible duplicates" are expected for eBird: several birders logging the same bird at the
  same hotspot on the same day.
- **Canopy layer:** `data/tgucanopy202611.tiff` (7.9 MB, included), canopy height in metres,
  Meta and WRI Canopy Height Maps v2 (CHMv2, CC BY 4.0) resampled to 10 m, EPSG:32616, exported from
  QGIS. Cells under 1 m are transparent; colours stretch 0–25 m like the Day 11 poster. About 16%
  of the box has canopy ≥ 1 m. With `sample_radius_m: 50`, each popup shows the canopy height at
  the record and the tallest canopy within 50 m, and the panel shows the share of shown records
  within 50 m of canopy (87% of the five groups, against 58% of the area). Points mark where the
  birder logged, so this means near trees, not in trees. Doves (ground-feeding seed-eaters that
  live almost anywhere) are the baseline (`baseline_group`): 84%. Parakeets, 96%, stand out. `highlight:` adds a switch with 932 "tall tree" spots (≥ 20 m,
  local highs at least 30 m apart; 20.5 ha of canopy ≥ 20 m in the box, no patch of 1 ha or more):
  click one for its height, coordinates and a satellite link. Check them before calling them trees. Canopy heights are model estimates from imagery, not field
  measurements.
- Parrots and parakeets rise from about 5% of all bird records in January to about 8% in
  June–July (all years pooled).

## Licences

- **Code:** MIT (`LICENSE`). Cite it with `CITATION.cff` or the Zenodo DOI of the release.
- **Built pages** contain their records, so each follows its data: the bee page (`bees/`) is
  CC BY-NC 4.0; the birds page will follow its GBIF download and the canopy (CC BY 4.0), whichever
  is stricter.
- **Data** is not part of this repository. GBIF records carry their own licences (CC0, CC BY,
  CC BY-NC); a download's overall licence is the most restrictive one in it, and anything derived
  from it, including a built map, follows that licence. The bee download is CC BY-NC 4.0.

## Structure

```
build.py                CLI
config/bees.yaml        one config per companion map
config/birds.yaml
gbifc/config.py         load + validate config
gbifc/provenance.py     run folder + provenance.json
gbifc/gbif.py           read GBIF simple CSV / occurrence.txt
gbifc/taxa.py           native status lookup (species → genus → default), review list
gbifc/checks.py         record-quality summary
gbifc/areas.py          optional area layer: boundaries + table joined by code, checks
gbifc/overlay.py        optional raster overlay (reproject, colour, embed as PNG)
gbifc/publish.py        copy the finished page into the site folder
gbifc/package.py        data package for archiving (package_data.py)
gbifc/render.py         pack records → map.html
gbifc/map_template.html the page (MapLibre)
```
