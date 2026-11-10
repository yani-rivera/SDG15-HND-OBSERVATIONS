"""Every piece of text the page shows, with its default wording.

A config can replace any of them under `labels:` (to fit another subject, country or
language) and describe GBIF record types under `legend.record_types:`. Words in {braces}
are filled in by the page; a replacement may use only the ones its default uses.
"""
import difflib
from string import Formatter

from . import validate as v

DEFAULTS = {
    # panel sections
    "show": "Show",
    "all": "All",
    "period": "Period",
    "all_years": "All years",
    # chart of records over time
    "over_time": "Records over time",
    "by_year": "By year",
    "by_month": "By month (all years)",
    "by_month_title": "Records by month",
    "share_title": "Share of {totals}, by month",
    "hint_click": "click a stem to filter",
    "hint_share": "corrects for when people go out",
    "hint_pick_group": "pick a group for shares",
    "no_year": "{n} records have no year",
    "no_month": "{n} records have no month",
    "chart_by_year": "Records per year",
    "chart_by_month": "Records per month",
    "record_one": "record",
    "record_many": "records",
    "tip_share": "= {share} of {totals} that month",
    "tip_top_source": "top source: {source} ({n})",
    "tip_all_years": "(all years)",
    "totals": "all records",
    # species table
    "top_title": "Most recorded species",
    "show_all_species": "show all species",
    "col_species": "Species",
    "col_records": "Records",
    "col_group": "Group",
    "col_status": "Status",
    "ties": "{n} more species also with {m} {records} not shown.",
    "taxa_count": "{n} {taxa} in {period}. Click a species to map it.",
    "taxon_one": "taxon",
    "taxon_many": "taxa",
    # colour legend
    "color_by": "Colour by",
    "by_group": "Group",
    "by_status": "Native status",
    "by_basis": "Record type",
    "introduced": "Introduced",
    "unidentified": "Not identified to genus",
    "unknown_status": "Unknown",
    # distance rings around records
    "rings_title": "Distance rings",
    "rings_hint": "appear from zoom {zoom}",
    "ring_km": "{km} km",
    "rings_note": "",
    # raster overlay
    "overlay_here": "{layer} here:",
    "overlay_none_under": "none (under {min} {unit})",
    "overlay_near": "highest within {radius} m:",
    "overlay_none": "none",
    "overlay_stat": "{pct}% of shown records are within {radius} m of {layer}",
    "overlay_area_share": "({pct}% of the area is)",
    "overlay_typical": "typical highest nearby:",
    "overlay_note": "",
    "overlay_no_records": "No shown records inside the {layer} layer.",
    "highlight_title": "{label} · {n} spots",
    "highlight_rank": "#{rank} of {n}",
    "satellite_link": "see on satellite",
    # area layer
    "area_off": "Off",
    "no_data": "no data",
    "area_no_data": "No data in the source table.",
    "area_share": "({pct}% of total)",
    # counts and status line
    "counts": "{n} {records}{what}{when} · {mapped} on the map, {unmapped} without coordinates.",
    "counts_of": " of {name}",
    "counts_in": " in {year}",
    "loading": "Loading…",
    "status_done": "{n} records · {mapped} with coordinates",
    "map_error": "Map error: {message}",
    "blocked": "Blocked by this page's security policy: {host}. If the base map needs it, add it to map.basemap_hosts in the config and rebuild.",
    # record popup
    "date_unknown": "date unknown",
    "recorded_by": "recorded by",
    "location_uncertainty": "location ± {m} m",
    "gbif_record": "GBIF record",
    "record_link": "record",
    "original": "original",
    # sources list
    "sources": "Sources",
    "src_records": "Records:",
    "src_licence": "Each record keeps its own licence (CC0, CC BY or CC BY-NC); see the download.",
    "src_basemap": "Basemap:",
    "src_status": "Native status:",
    "src_status_rule": "author's rule — {default} unless listed otherwise (species, then genus); see status_review.csv in the build.",
    "credit_author": "Map and data curation:",
    "credit_licences": "Licences:",
    "credit_records_licence": "records",
    "credit_map_licence": "this map",
    "credit_thanks": "Thanks to:",
    "src_built": "Built with {tool} v{version} ({config}), run {run}.",
}

# GBIF basisOfRecord values: the name shown in the legend and a short explanation (hover).
RECORD_TYPES = {
    "PRESERVED_SPECIMEN": {"label": "Preserved specimen", "hint": "A specimen kept in a museum or collection."},
    "FOSSIL_SPECIMEN": {"label": "Fossil specimen", "hint": "A fossil kept in a collection."},
    "LIVING_SPECIMEN": {"label": "Living specimen", "hint": "A living organism kept in a garden, zoo or culture collection."},
    "MATERIAL_SAMPLE": {"label": "Material sample", "hint": "A physical sample, such as tissue, DNA or an environmental sample."},
    "MATERIAL_CITATION": {"label": "Material citation", "hint": "A specimen cited in a scientific publication."},
    "HUMAN_OBSERVATION": {"label": "Human observation", "hint": "Seen or heard and reported by a person, with no specimen kept (for example iNaturalist or eBird)."},
    "MACHINE_OBSERVATION": {"label": "Machine observation", "hint": "Recorded by a device, such as a camera trap, sound recorder or tag."},
    "OBSERVATION": {"label": "Observation", "hint": "An observation; the publisher did not say how it was made."},
    "OCCURRENCE": {"label": "Occurrence", "hint": "A record whose type the publisher did not specify."},
    "unknown": {"label": "Unknown", "hint": "The record gives no record type."},
}


def _fields(s: str) -> set[str]:
    return {name for _, name, _, _ in Formatter().parse(s) if name}


def resolve(given: dict | None, where: str = "labels") -> dict:
    """Defaults with the config's replacements; unknown names and unknown {words} are errors."""
    given = given or {}
    if not isinstance(given, dict):
        raise v.ConfigError(f"{where}: expected a list of name: text pairs")
    out = dict(DEFAULTS)
    for key, value in given.items():
        if key not in DEFAULTS:
            close = difflib.get_close_matches(str(key), DEFAULTS, n=3)
            raise v.ConfigError(f"{where}: unknown label {key!r}" + (f"; did you mean {', '.join(close)}?" if close else "")
                                + " (gbifc/labels.py lists them all)")
        value = v.text(value, f"{where}.{key}")
        try:
            extra = _fields(value) - _fields(DEFAULTS[key])
        except ValueError:
            raise v.ConfigError(f"{where}.{key}: unbalanced {{braces}} in {value!r}") from None
        if extra:
            allowed = ", ".join("{" + f + "}" for f in sorted(_fields(DEFAULTS[key]))) or "none"
            raise v.ConfigError(f"{where}.{key}: unknown {{{'}, {'.join(sorted(extra))}}}; this label can use: {allowed}")
        out[key] = value
    return out


def record_types(given: dict | None, where: str = "legend.record_types") -> dict:
    """Legend entry per GBIF record type: {code: {label, hint, color?}}, defaults plus the config's."""
    given = given or {}
    if not isinstance(given, dict):
        raise v.ConfigError(f"{where}: expected one entry per record type, e.g. HUMAN_OBSERVATION")
    out = {code: dict(entry) for code, entry in RECORD_TYPES.items()}
    for code, entry in given.items():
        if not isinstance(entry, dict) or set(entry) - {"label", "hint", "color"}:
            raise v.ConfigError(f"{where}.{code}: expected any of label, hint, color")
        merged = out.setdefault(str(code), {})
        for key in ("label", "hint"):
            if key in entry:
                merged[key] = v.text(entry[key], f"{where}.{code}.{key}", 300)
        if "color" in entry:
            merged["color"] = v.color(entry["color"], f"{where}.{code}.color")
    return out


def fill(template: str, **values) -> str:
    """Fill {words} in a label (builder side; the page has its own copy of this)."""
    for key, value in values.items():
        template = template.replace("{" + key + "}", str(value))
    return template
