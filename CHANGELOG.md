# Changelog

Version lives in `gbifc/__init__.py`; printed by `python build.py --version` and stored in every
`provenance.json`.

## 0.5.0 — 2026-11-10
Security release, plus options to make a map your own. Rebuild and republish each map to apply
the security fixes: a published page only changes when it is rebuilt.

Security
- Base map credit: MapLibre's attribution control is off and the page writes the credit itself
  (plain text and https links from `map.basemap_attribution`). MapLibre 4.7.1 writes the base map
  provider's attribution into the page as unchecked HTML (GHSA-jrc7-96c5-q579, fixed upstream
  only from 6.4.1), so pages built with 0.4.1 or earlier would run script sent by a compromised
  provider. See SECURITY.md.
- Page security policy (Content-Security-Policy) on every built page and on the front page: only
  the page's own script (by SHA-256) and the pinned MapLibre file may run, connections go only to
  the base map's host(s); inline handlers, `eval`, frames and forms are refused (`gbifc/csp.py`).
  A request the policy refuses is named in the panel.
- Config values are checked before anything is written (`gbifc/validate.py`): colours `#rrggbb`,
  numbers, https links (DOI, base map), host names, bounds, locale. Config text is escaped
  wherever the page shows it. A wrong value stops the build with the option's name.
- `provenance.json` no longer publishes absolute or home paths (file name only).
- Record text: collector lists are cut at 200 characters, "original" links over 500 characters
  are dropped; external links open with `rel="noopener noreferrer"`.
- Requirements: Pillow 13.0.0 or later (fixes the advisories open against earlier versions).

Options (all optional; with none set, a map looks as before)
- `map.theme: dark | light`: panel, chart, popups and a matching base map (OpenFreeMap dark or
  positron). `map.theme_colors` changes single theme colours.
- `map.colors`: `accent` now also colours the title, buttons and links (the title was gold on
  every map before); new `basis` list for record-type colours. Colours default to the theme's.
  The build reports colours that will be hard to see on the background (`contrast_notes` in
  `provenance.json`).
- `gbif.country: HN`: keeps one country's records. `map.bounds: auto` (or leave it out): the
  opening view is fitted to the records and logged in `provenance.json`.
- `labels:`: every text of the panel, popups, legends and sources can be replaced, for another
  subject or language (`gbifc/labels.py` lists them). The bee-specific rings note and the
  bird-specific canopy sentences moved from the page into `bees.yaml` and `birds.yaml`.
- `legend.record_types:`: name, hover explanation and colour per GBIF record type; built-in
  explanations for the standard types.
- `map.locale`: number and month formats. `taxa.introduced_words`: which statuses count as
  introduced. `map.basemap_hosts`: extra hosts for a base map of your own.
- `credits:`: author (with optional link), licence of the records, licence of the map, thanks and
  notes in one section; shown under Sources and copied into `provenance.json`. Known licences
  link to their text. `map.credit` (free text) still works.
- Records that are not from GBIF: `source.kind: other` (no gbif.org links, no DOI expected,
  optional `record_link` per record) and `columns:` to say which column of the
  file holds each field (e.g. `decimalLatitude: lat`). Comma-, semicolon- or tab-separated files.
  Year and month are taken from an ISO `eventDate` when such a file has no year column. A column
  the config relies on but the file lacks is reported with the file's actual column names.
- `config/template.yaml`: a starter config for any country.

Birds
- *What I Still Like to Hear* (Tegucigalpa parakeets, zanates, woodpeckers, owls and doves over
  the tree canopy) published at `birds/`; the front page and README link it.
- A map from GBIF whose DOI (`gbif.doi`) or licence (`credits.records_licence`) is not filled in
  is built but not published.

Other
- Missing input files are listed with their source before anything is built.
- Unknown or mistyped options are reported (and ignored) instead of passing silently.
- `provenance.json`: SHA-256 of the area table and boundaries; theme, locale and allowed hosts.
- `data/README.md` added (it was referenced but missing); leftover merge-conflict lines removed
  from README.md.

## 0.4.1 — 2026-11-07
- Code, sites and data kept apart: `data/` is ignored by Git (`data/README.md` says where each
  input comes from); optional `run.publish_dir` copies the finished page into a site folder (e.g.
  GitHub Pages) as index.html with provenance.json and .nojekyll. One folder per map: bees publish to
  `bees/` (https://yani-rivera.github.io/SDG15-HND-OBSERVATIONS/bees/), birds to `birds/`; the
  publish folder is created if missing. A hand-written front page at the root links to each map.
- Birds: canopy credit says what was changed (clipped to Tegucigalpa, resampled to 10 m) and links
  the CC BY 4.0 licence.
- `package_data.py`: writes a map's data package for Zenodo (records.csv, source_datasets.csv,
  taxa_status.csv, area table, package_provenance.json), outside the repository.
- Bees: credit line states the records' licence (CC BY-NC 4.0).
- Base map: OpenFreeMap Dark (no API key, no registration) instead of CARTO Dark Matter, whose
  base maps now require a personal API key that should not live in a public code repository.
- MIT licence and CITATION.cff (for citing, and for Zenodo's GitHub release archiving).
- Security: MapLibre script and stylesheet loaded with Subresource Integrity (sha384), so a
  modified file from the CDN is refused; "original record" links only for http(s) URLs (checked in
  the builder and again in the page); GBIF ids URL-encoded in links. SECURITY.md added.

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
