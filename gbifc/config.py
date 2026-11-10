"""Load a companion config, fill in defaults, and check every value that reaches the page."""
import difflib
from pathlib import Path

import yaml

from . import credits, labels, theme
from .gbif import FIELDS
from . import validate as v
from .validate import ConfigError

REQUIRED = {"gbif": ["file", "citation"], "map": ["title"]}
SECTIONS = ("run", "gbif", "source", "columns", "credits", "taxa", "groups", "map", "areas", "overlay", "labels", "legend")
GBIF_RECORD_URL = "https://www.gbif.org/occurrence/{id}"
MAP_KEYS = ("title", "subtitle", "data_note", "call_to_action", "credit", "totals_label",
            "default_year", "quick_years", "rings_km", "rings_minzoom",
            "theme", "theme_colors", "colors", "basemap", "basemap_attribution", "basemap_hosts",
            "bounds", "locale")
OPENFREEMAP = "https://tiles.openfreemap.org/"
OPENFREEMAP_CREDIT = [
    {"text": "OpenFreeMap", "url": "https://openfreemap.org"},
    {"text": "© OpenMapTiles", "url": "https://www.openmaptiles.org/"},
    {"text": "© OpenStreetMap contributors", "url": "https://www.openstreetmap.org/copyright"},
]


def _unknown(given, known, prefix: str) -> list[str]:
    notes = []
    for key in given or {}:
        if key not in known:
            close = difflib.get_close_matches(str(key), known, n=1)
            notes.append(f"unknown option {prefix}{key} (ignored)" + (f"; did you mean {prefix}{close[0]}?" if close else ""))
    return notes


def _check_gbif(g: dict) -> None:
    v.text(g["citation"], "gbif.citation")
    if g.get("doi"):
        g["doi"] = v.https_url(g["doi"], "gbif.doi")
    flt = g.get("filter") or {}
    if not isinstance(flt, dict) or not all(isinstance(vals, list) for vals in flt.values()):
        raise ConfigError("gbif.filter: expected field: [values] pairs, e.g. family: [Apidae]")
    if g.get("country"):   # shorthand for the usual country filter
        code = v.country(g["country"], "gbif.country")
        if flt.get("countryCode") not in (None, [code]):
            raise ConfigError(f"gbif.country is {code} but gbif.filter.countryCode says {flt['countryCode']}: keep one")
        flt["countryCode"] = [code]
    g["filter"] = {k: [str(x) for x in vals] for k, vals in flt.items()}
    if g.get("max_uncertainty_m") is not None:
        v.number(g["max_uncertainty_m"], "gbif.max_uncertainty_m", 0)


def _source(cfg: dict, L: dict) -> dict:
    """Where the records come from: GBIF (the default) or any other table.

    Decides the per-record link in popups, the per-record licence sentence under Sources, and
    whether a DOI is expected. Returns {"kind", "name", "licence", "record_link"}."""
    s = cfg.get("source") or {}
    if not isinstance(s, dict):
        raise ConfigError("source: expected kind, and optionally name and record_link")
    if "licence" in s:
        raise ConfigError("source.licence: the licence of the records goes in credits.records_licence")
    kind = v.one_of(s.get("kind", "gbif"), ("gbif", "other"), "source.kind")
    link = s.get("record_link")
    if link:
        if not isinstance(link, dict) or "{id}" not in str(link.get("url", "")):
            raise ConfigError("source.record_link: expected url with {id} where the record's id goes, "
                              "e.g. url: \"https://example.org/records/{id}\", and optionally text")
        link = {"url": v.https_url(link["url"], "source.record_link.url"),
                "text": v.text(link.get("text", L["record_link"]), "source.record_link.text", 80)}
    elif kind == "gbif":
        link = {"url": GBIF_RECORD_URL, "text": L["gbif_record"]}
    return {"kind": kind,
            "name": v.text(s["name"], "source.name", 200) if s.get("name") else None,
            "licence": L["src_licence"] if kind == "gbif" else None,
            "record_link": link or None}


def _columns(given) -> dict:
    """`columns:` — GBIF field name: the file's own column name."""
    given = given or {}
    if not isinstance(given, dict):
        raise ConfigError("columns: expected pairs like decimalLatitude: lat")
    out = {}
    for field, col in given.items():
        if field not in FIELDS:
            close = difflib.get_close_matches(str(field), FIELDS, n=3)
            raise ConfigError(f"columns: {field!r} is not a field the map reads"
                              + (f"; did you mean {', '.join(close)}?" if close else "")
                              + f". Fields: {', '.join(FIELDS)}")
        out[field] = v.text(col, f"columns.{field}", 200)
    return out


def _check_map(m: dict, th: dict) -> None:
    for key in ("title", "subtitle", "data_note", "call_to_action", "credit", "totals_label"):
        if m.get(key) is not None:
            v.text(m[key], f"map.{key}")
    m["basemap"] = v.https_url(m.get("basemap") or th["basemap"], "map.basemap")
    credit = m.get("basemap_attribution")
    if not credit:
        if not m["basemap"].startswith(OPENFREEMAP):
            raise ConfigError("map.basemap_attribution: required with your own base map. The page shows this "
                              "credit on the map itself, so give the text your base map's provider asks for")
        credit = OPENFREEMAP_CREDIT
    if isinstance(credit, str):
        credit = [{"text": credit}]
    if not isinstance(credit, list):
        raise ConfigError("map.basemap_attribution: expected text, or a list of {text, url} entries")
    m["basemap_attribution"] = [
        {"text": v.text(c.get("text"), f"map.basemap_attribution[{i}].text", 200),
         "url": v.https_url(c["url"], f"map.basemap_attribution[{i}].url") if c.get("url") else None}
        if isinstance(c, dict) else {"text": v.text(c, f"map.basemap_attribution[{i}]", 200), "url": None}
        for i, c in enumerate(credit)]
    hosts = m.get("basemap_hosts") or []
    if not isinstance(hosts, list):
        raise ConfigError("map.basemap_hosts: expected a list of host names")
    m["_hosts"] = sorted({v.host_of(m["basemap"]), *(v.host(h, f"map.basemap_hosts[{i}]") for i, h in enumerate(hosts))})
    m["bounds"] = None if m.get("bounds") in (None, "auto") else v.bounds(m["bounds"], "map.bounds")
    m["locale"] = v.locale(m.get("locale", "en-US"), "map.locale")
    m["rings_km"] = v.numbers(m.get("rings_km") or [], "map.rings_km")
    if any(k <= 0 for k in m["rings_km"]):
        raise ConfigError("map.rings_km: distances must be greater than 0")
    m["rings_minzoom"] = v.number(m.get("rings_minzoom", 8), "map.rings_minzoom", 0, 24)
    if m.get("default_year") is not None:
        v.number(m["default_year"], "map.default_year")
    m["quick_years"] = v.numbers(m.get("quick_years") or [], "map.quick_years")


def _check_groups(groups, path_name: str) -> None:
    if not isinstance(groups, list):
        raise ConfigError("groups: expected a list")
    for i, g in enumerate(groups):
        if not isinstance(g, dict) or not g.get("name") or not g.get("match") or not g.get("color"):
            raise ConfigError(f"{path_name}: every group needs name, color and match")
        v.text(g["name"], f"groups[{i}].name", 80)
        g["color"] = v.color(g["color"], f"groups[{g['name']}].color")
        if g.get("note") is not None:
            v.text(g["note"], f"groups[{g['name']}].note")
        if not isinstance(g["match"], dict) or not all(isinstance(vals, list) for vals in g["match"].values()):
            raise ConfigError(f"groups[{g['name']}].match: expected field: [values] pairs")


def _check_areas(a: dict, th: dict) -> None:
    for key in ("geojson", "table", "id_field", "table_id", "title", "variables", "colors"):
        if key not in a:
            raise ConfigError(f"areas: missing {key}")
    v.text(a["title"], "areas.title", 120)
    a["colors"] = v.colors(a["colors"], "areas.colors", at_least=2)
    a["no_data_color"] = v.color(a.get("no_data_color", th["page"]["no_data"]), "areas.no_data_color")
    if not isinstance(a["variables"], list) or not a["variables"]:
        raise ConfigError("areas.variables: expected at least one variable")
    for i, var in enumerate(a["variables"]):
        where = f"areas.variables[{i}]"
        if not isinstance(var, dict) or not var.get("key") or not var.get("label"):
            raise ConfigError(f"{where}: needs key, label and breaks")
        v.text(var["label"], f"{where}.label", 120)
        var["breaks"] = v.numbers(var.get("breaks"), f"{where}.breaks", at_least=1)
        if var["breaks"] != sorted(var["breaks"]):
            raise ConfigError(f"{where}.breaks: must go from low to high")
        if len(var["breaks"]) + 1 > len(a["colors"]):
            raise ConfigError(f"{where}: {len(var['breaks'])} breaks need {len(var['breaks']) + 1} colours "
                              f"in areas.colors (there are {len(a['colors'])})")
    known = [var["key"] for var in a["variables"]]
    if a.get("default") is not None and a["default"] not in known:
        raise ConfigError(f"areas.default: {a['default']!r} is not one of the variables ({', '.join(known)})")


def _check_overlay(o: dict) -> None:
    if "file" not in o or "colors" not in o:
        raise ConfigError("overlay: needs file and colors")
    o["colors"] = v.colors(o["colors"], "overlay.colors", at_least=2)
    for key in ("title", "unit", "baseline_group", "baseline_label"):
        if o.get(key) is not None:
            v.text(o[key], f"overlay.{key}", 200)
    if "stretch" in o:
        lo, hi = v.numbers(o["stretch"], "overlay.stretch", at_least=2)[:2]
        if not lo < hi:
            raise ConfigError("overlay.stretch: the first value must be lower than the second")
    for key, low, high in (("min_value", None, None), ("opacity", 0, 1), ("sample_radius_m", 0, None)):
        if o.get(key) is not None:
            v.number(o[key], f"overlay.{key}", low, high)
    h = o.get("highlight")
    if h:
        v.text(h.get("label", ""), "overlay.highlight.label", 200)
        h["color"] = v.color(h.get("color", "#ffffff"), "overlay.highlight.color")
        v.number(h.get("min_value"), "overlay.highlight.min_value")
        v.number(h.get("min_separation_m", 30), "overlay.highlight.min_separation_m", 0)


def load_config(path: str | Path) -> dict:
    path = Path(path)
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict):
        raise ConfigError(f"{path.name}: not a config (expected sections such as gbif: and map:)")
    if "records" in cfg and "gbif" not in cfg:      # `records:` reads better for a file that is not from GBIF
        cfg["gbif"] = cfg.pop("records")
    try:
        for section, keys in REQUIRED.items():
            missing = [k for k in keys if k not in (cfg.get(section) or {})]
            if missing:
                raise ConfigError(f"[{section}] missing {missing}")
        notes = _unknown(cfg, SECTIONS, "") + _unknown(cfg["map"], MAP_KEYS, "map.")

        cfg["run"] = cfg.get("run") or {}
        cfg["run"].setdefault("output_dir", f"outputs/{path.stem}")
        cfg["taxa"] = cfg.get("taxa") or {}
        cfg["groups"] = cfg.get("groups") or []
        cfg["_status"] = "default" in cfg["taxa"]      # native-status rule present?
        if not cfg["_status"] and not cfg["groups"]:
            raise ConfigError("needs a `taxa` (native status) or a `groups` section")
        cfg["taxa"]["introduced_words"] = [v.text(w, "taxa.introduced_words", 80)
                                           for w in cfg["taxa"].get("introduced_words") or ["Introduced"]]
        cfg["taxa"]["top_n"] = int(v.number(cfg["taxa"].get("top_n", 10), "taxa.top_n", 1, 200))

        th = theme.resolve(cfg["map"])
        _check_gbif(cfg["gbif"])
        _check_map(cfg["map"], th)
        _check_groups(cfg["groups"], path.name)
        if cfg.get("areas"):
            _check_areas(cfg["areas"], th)
        if cfg.get("overlay"):
            _check_overlay(cfg["overlay"])

        given = dict(cfg.get("labels") or {})
        if cfg["map"].get("totals_label"):             # older configs set this one under map:
            given.setdefault("totals", cfg["map"]["totals_label"])
        cfg["_labels"] = labels.resolve(given)
        cfg["_source"] = _source(cfg, cfg["_labels"])
        cfg["_columns"] = _columns(cfg.get("columns"))
        cfg["_credits"] = credits.resolve(cfg.get("credits"))
        legend = cfg.get("legend") or {}
        notes += _unknown(legend, ("record_types",), "legend.")
        cfg["_record_types"] = labels.record_types(legend.get("record_types"))
        cfg["_theme"] = th
        highlight = (cfg.get("overlay") or {}).get("highlight") or {}
        cfg["_contrast"] = theme.contrast_notes(
            th, cfg["groups"],
            {"overlay.highlight.color": highlight["color"]} if highlight else None)
    except ConfigError as e:
        raise ConfigError(f"{path.name}: {e}") from None
    cfg["_notes"] = notes
    cfg["_path"] = str(path.resolve())
    cfg["_name"] = path.stem
    return cfg
