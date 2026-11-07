# Changelog

Version lives in `gbifc/__init__.py`; printed by `python build.py --version` and stored in every
`provenance.json`.

## 0.4.1 — 2026-11-07
- Code, sites and data kept apart: `data/` is ignored by Git (`data/README.md` says where each
  input comes from); optional `run.publish_dir` copies the finished page into a site folder (its
  own GitHub Pages repo) as index.html with provenance.json and .nojekyll. Bees publish to
  `../SDG15-DONT-TELL-THE-BEES`.
- `package_data.py`: writes a map's data package for Zenodo (records.csv, source_datasets.csv,
  taxa_status.csv, area table, package_provenance.json), outside the repository.
- Bees: credit line states the records' licence (CC BY-NC 4.0).
- Base map: OpenFreeMap Dark (no API key, no registration) instead of CARTO Dark Matter, whose
  base maps now require a personal API key that should not live in a public code repository.
- MIT licence and CITATION.cff (for citing, and for Zenodo's GitHub release archiving).

## 0.4.0 — 2026-11-05
- Optional raster overlay (`overlay:`): e.g. tree canopy height, reprojected to Web Mercator
  (nearest neighbour), coloured with a stretch, transparent below `min_value`, embedded as a PNG
  under the records, with an on/off switch and a gradient legend. Input SHA-256 and pixel stats in
  `provenance.json`.
- Overlay sampling (`sample_radius_m`): value at each record and highest within the radius
  (round neighbourhood, original raster); shown in popups and as a live panel stat.
- Birds: tree canopy (Meta/WRI CHMv2, 10 m) under the records, sampled within 50 m.
- Overlay highlight (`highlight:`): local highs at or above a value (birds: 932 tall-tree spots
  ≥ 20 m, at least 30 m apart), clickable, with height, coordinates and a satellite link, off by
  default. A model can mistake a tower for a tree: check them.
- Birds: call to action explains that Merlin sightings reach GBIF only through eBird checklists.
- Group notes (`note:` per group): shown under the group buttons when a group is selected.
- Overlay baseline (`baseline_group`): the panel compares the shown records with a reference group
  (birds: doves, the ground-feeding seed-eaters that live everywhere).
- "1 taxon" instead of "1 taxa".
- Lollipop: wider left margin so four-digit axis labels fit.
- New requirements: rasterio, numpy, Pillow (only needed for overlays).

## 0.3.0 — 2026-11-05
- Optional area layer (`areas:`): choropleth under the records with a variable switch (or Off),
  legend, popups with share of total and extra fields; GeoJSON simplified for the web; CSV joined
  by code; checks for join coverage, name agreement and expected totals (`areas_report.csv`).
- Bees: honey production by department (INE, Censo Agropecuario 2023–2024).

## 0.2.0 — 2026-11-05
- Groups: `groups:` config (name, colour, match on any GBIF field), `keep_only_groups`, group
  switcher, colour by group, group column in the species table, group in popups.
- Seasonality: "By month (all years)" view; with a group or species selected, stems show the share
  of all records that month (totals taken before group selection) to correct for observer effort.
- Native status is optional (only when `taxa.default` is set).
- The map only re-filters / re-colours when the selection actually changed (faster with 100k+ points).
- New config: `birds.yaml` (Tegucigalpa birds).

## 0.1.0 — 2026-11-05
- First version, generic for any GBIF occurrence download; first config: `bees.yaml`
  (Don't Tell the Bees companion).
- Lollipop over time (year, or month for single-year data) with top source per stem; top-N species
  table with native status, footnotes and tie note; colour by status or record type; true-distance
  foraging rings from zoom 8; record popups with GBIF and original links; click-to-filter.
- Checks: records without coordinates or year, location uncertainty > 10 km, possible duplicates,
  taxa with default native status (`status_review.csv`).
