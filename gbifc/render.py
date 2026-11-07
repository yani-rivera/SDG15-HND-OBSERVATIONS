"""Pack the records compactly and fill the page template."""
import json
import math
import re
from html import escape
from pathlib import Path

from . import __project__, __version__
from .gbif import taxon_label
from .taxa import status_of

TEMPLATE = Path(__file__).with_name("map_template.html")


def _clean(o):
    if isinstance(o, float):
        return None if not math.isfinite(o) else o
    if isinstance(o, (list, tuple)):
        return [_clean(x) for x in o]
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    return o


def _json(o) -> str:
    s = json.dumps(_clean(o), separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return s.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


class _Index:
    """value -> small integer, so repeated strings are stored once."""
    def __init__(self):
        self.values, self._pos = [], {}

    def __call__(self, v):
        if v not in self._pos:
            self._pos[v] = len(self.values)
            self.values.append(v)
        return self._pos[v]


def pack(records: list[dict], cfg: dict) -> dict:
    taxa, status, basis, source, people, place = (_Index() for _ in range(6))
    max_unc = cfg["gbif"].get("max_uncertainty_m")
    rows = []
    for r in records:
        mappable = r["lat"] is not None and r["lon"] is not None and \
            not (max_unc and r["uncertainty_m"] and r["uncertainty_m"] > max_unc)
        src = " / ".join(x for x in (r["institutionCode"], r["collectionCode"]) if x) or "unknown"
        where = ", ".join(x for x in (r["locality"], r["stateProvince"]) if x)
        rows.append([
            round(r["lat"], 5) if mappable else None,
            round(r["lon"], 5) if mappable else None,
            r["year"], r["month"],
            taxa(taxon_label(r)),
            status(status_of(r, cfg["taxa"])[0] if cfg["_status"] else ""),
            basis(r["basisOfRecord"] or "unknown"),
            source(src),
            r["gbifID"],
            (r["eventDate"] or "")[:10],
            people(r["recordedBy"] or ""),
            r["occurrenceID"] if r["occurrenceID"].startswith("http") else "",
            r["uncertainty_m"],
            place(where[:120]),
            r.get("group"),
            r.get("over_here"), r.get("over_near"),
        ])
    return {"rows": rows, "taxa": taxa.values, "status": status.values, "basis": basis.values,
            "source": source.values, "people": people.values, "place": place.values}


def build_html(cfg: dict, run_id: str, packed: dict, summary: dict, totals: dict,
               area_fc: dict | None = None, area_totals: dict | None = None,
               over: dict | None = None) -> str:
    m, t, g = cfg["map"], cfg["taxa"], cfg["gbif"]
    a = cfg.get("areas") or {}
    o = cfg.get("overlay") or {}
    settings = {
        "overlay": {k: v for k, v in over.items() if k != "url"} if over else None,
        "areas": ({"title": a["title"], "note": a.get("note", ""), "default": a.get("default"),
                   "variables": a["variables"], "colors": a["colors"],
                   "noData": a.get("no_data_color", "#1c1d20"),
                   "extra": a.get("extra_fields", []), "extraLabels": a.get("extra_labels") or {},
                   "totals": area_totals or {}}
                  if area_fc else None),
        "groups": [{"name": x["name"], "color": x["color"], "note": x.get("note", "")} for x in cfg["groups"]],
        "hasStatus": cfg["_status"],
        "monthTotals": totals.get("totals_by_month", {}),
        "yearTotals": totals.get("totals_by_year", {}),
        "totalsLabel": m.get("totals_label", "all records"),
        "title": m["title"], "defaultYear": m.get("default_year"), "quickYears": m.get("quick_years") or [],
        "rings": m.get("rings_km") or [], "ringsMinZoom": m.get("rings_minzoom", 8),
        "colors": m["colors"], "basemap": m["basemap"], "bounds": m["bounds"],
        "topN": t.get("top_n", 10), "footnotes": t.get("footnotes") or {},
        "introducedWords": ["Introduced"],
    }
    sources = "".join(f"<li>{x}</li>" for x in [
        f"<b>Records:</b> {escape(g['citation'])}"
        + (f" (<a href=\"{escape(g['doi'])}\" target=\"_blank\" rel=\"noopener\">DOI</a>)" if g.get("doi") else "")
        + ". Each record keeps its own licence (CC0, CC BY or CC BY-NC); see the download.",
        (f"<b>{escape(a['title'])}:</b> {escape(a.get('source', ''))}. {escape(a.get('geojson_source', ''))}."
         if area_fc else ""),
        (f"<b>{escape(o.get('title', 'Overlay'))}:</b> {escape(o.get('source', ''))}." if over else ""),
        f"<b>Basemap:</b> {escape(m.get('basemap_attribution', ''))}",
        (f"<b>Native status:</b> author's rule — {escape(t['default'])} unless listed otherwise "
         "(species, then genus); see status_review.csv in the build.") if cfg["_status"] else "",
        escape(m.get("credit", "")),
        f"Built with {escape(__project__)} v{escape(__version__)} ({escape(cfg['_name'])}.yaml), run {escape(run_id)}.",
    ] if x)
    values = {
        "__TITLE__": escape(m["title"]),
        "__SUBTITLE__": escape(m.get("subtitle", "")),
        "__CTA__": escape(m.get("call_to_action", "")),
        "__NOTE__": escape(m.get("data_note", "")),
        "__SOURCES__": sources,
        "__SETTINGS__": _json(settings),
        "__DATA__": _json(packed),
        "__SUMMARY__": _json(summary),
        "__AREAS__": _json(area_fc or {"type": "FeatureCollection", "features": []}),
        "__OVERLAY_URL__": _json(over["url"] if over else ""),
    }
    pattern = re.compile("|".join(re.escape(k) for k in values))
    return pattern.sub(lambda mt: values[mt.group(0)], TEMPLATE.read_text(encoding="utf-8"))
