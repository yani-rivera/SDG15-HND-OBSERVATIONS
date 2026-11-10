"""Pack the records compactly and fill the page template."""
import json
import math
import re
from html import escape
from pathlib import Path

from . import __project__, __version__, credits, csp, theme
from .gbif import taxon_label
from .labels import fill
from .taxa import status_of

TEMPLATE = Path(__file__).with_name("map_template.html")
MAX_PEOPLE, MAX_PLACE, MAX_LINK = 200, 120, 500     # longest record text kept (characters)
_LINK = 'target="_blank" rel="noopener noreferrer"'


def _clean(o):
    if isinstance(o, float):
        return None if not math.isfinite(o) else o
    if isinstance(o, (list, tuple)):
        return [_clean(x) for x in o]
    if isinstance(o, dict):
        return {k: _clean(v) for k, v in o.items()}
    return o


def _json(o) -> str:
    """JSON for a <script type="application/json"> block: `<` is escaped so nothing in the
    data can close the block or open a tag."""
    s = json.dumps(_clean(o), separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return s.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def _cut(s: str, limit: int) -> str:
    return s if len(s) <= limit else s[:limit - 1].rstrip() + "…"


class _Index:
    """value -> small integer, so repeated strings are stored once."""
    def __init__(self):
        self.values, self._pos = [], {}

    def __call__(self, v):
        if v not in self._pos:
            self._pos[v] = len(self.values)
            self.values.append(v)
        return self._pos[v]


def _status_label(rec: dict, cfg: dict) -> str:
    if not cfg["_status"]:
        return ""
    status, how = status_of(rec, cfg["taxa"])
    return cfg["_labels"]["unknown_status"] if how == "unknown" else status


def pack(records: list[dict], cfg: dict) -> dict:
    taxa, status, basis, source, people, place = (_Index() for _ in range(6))
    max_unc = cfg["gbif"].get("max_uncertainty_m")
    rows = []
    for r in records:
        mappable = r["lat"] is not None and r["lon"] is not None and \
            not (max_unc and r["uncertainty_m"] and r["uncertainty_m"] > max_unc)
        src = " / ".join(x for x in (r["institutionCode"], r["collectionCode"]) if x) or "unknown"
        where = ", ".join(x for x in (r["locality"], r["stateProvince"]) if x)
        link = r["occurrenceID"]
        rows.append([
            round(r["lat"], 5) if mappable else None,
            round(r["lon"], 5) if mappable else None,
            r["year"], r["month"],
            taxa(taxon_label(r)),
            status(_status_label(r, cfg)),
            basis(r["basisOfRecord"] or "unknown"),
            source(src),
            r["gbifID"],
            (r["eventDate"] or "")[:10],
            people(_cut(r["recordedBy"] or "", MAX_PEOPLE)),
            # only web links, and only of a sane length; anything else (javascript:, data:) is dropped
            link if link.lower().startswith(("http://", "https://")) and len(link) <= MAX_LINK else "",
            r["uncertainty_m"],
            place(where[:MAX_PLACE]),
            r.get("group"),
            r.get("over_here"), r.get("over_near"),
        ])
    return {"rows": rows, "taxa": taxa.values, "status": status.values, "basis": basis.values,
            "source": source.values, "people": people.values, "place": place.values}


def _settings(cfg: dict, totals: dict, bounds, area_fc, area_totals, over) -> dict:
    m, t = cfg["map"], cfg["taxa"]
    a = cfg.get("areas") or {}
    th = cfg["_theme"]
    return {
        "labels": cfg["_labels"],
        "locale": m["locale"],
        "theme": th["page"],
        "colors": th["colors"],
        "recordTypes": cfg["_record_types"],
        "attribution": m["basemap_attribution"],
        "recordLink": cfg["_source"]["record_link"],
        "overlay": {k: v for k, v in over.items() if k != "url"} if over else None,
        "areas": ({"title": a["title"], "note": a.get("note", ""), "default": a.get("default"),
                   "variables": a["variables"], "colors": a["colors"], "noData": a["no_data_color"],
                   "extra": a.get("extra_fields", []), "extraLabels": a.get("extra_labels") or {},
                   "totals": area_totals or {}}
                  if area_fc else None),
        "groups": [{"name": x["name"], "color": x["color"], "note": x.get("note", "")} for x in cfg["groups"]],
        "hasStatus": cfg["_status"],
        "nativeLabel": t.get("default", ""),
        "introducedWords": t["introduced_words"],
        "unknownStatus": cfg["_labels"]["unknown_status"],
        "monthTotals": totals.get("totals_by_month", {}),
        "yearTotals": totals.get("totals_by_year", {}),
        "title": m["title"], "defaultYear": m.get("default_year"), "quickYears": m["quick_years"],
        "rings": m["rings_km"], "ringsMinZoom": m["rings_minzoom"],
        "basemap": m["basemap"], "bounds": bounds,
        "topN": t["top_n"], "footnotes": t.get("footnotes") or {},
    }


def _sources(cfg: dict, run_id: str, area_fc, over) -> str:
    """The Sources list as HTML: every piece of text escaped, links https only (checked in config)."""
    m, t, g, L = cfg["map"], cfg["taxa"], cfg["gbif"], cfg["_labels"]
    a, o = cfg.get("areas") or {}, cfg.get("overlay") or {}
    credit = ", ".join(
        f'<a href="{escape(c["url"])}" {_LINK}>{escape(c["text"])}</a>' if c["url"] else escape(c["text"])
        for c in m["basemap_attribution"])
    items = [
        f"<b>{escape(L['src_records'])}</b> {escape(g['citation'])}"
        + (f" (<a href=\"{escape(g['doi'])}\" {_LINK}>DOI</a>)" if g.get("doi") else "")
        + "." + (f" {escape(cfg['_source']['licence'])}" if cfg["_source"]["licence"] else ""),
        (f"<b>{escape(a['title'])}:</b> {escape(a.get('source', ''))}. {escape(a.get('geojson_source', ''))}."
         if area_fc else ""),
        (f"<b>{escape(o.get('title', 'Overlay'))}:</b> {escape(o.get('source', ''))}." if over else ""),
        f"<b>{escape(L['src_basemap'])}</b> {credit}",
        (f"<b>{escape(L['src_status'])}</b> {escape(fill(L['src_status_rule'], default=t['default']))}"
         if cfg["_status"] else ""),
        *credits.html_items(cfg["_credits"], L),
        escape(m.get("credit") or ""),
        escape(fill(L["src_built"], tool=__project__, version=__version__,
                    config=f"{cfg['_name']}.yaml", run=run_id)),
    ]
    return "".join(f"<li>{x}</li>" for x in items if x)


def build_html(cfg: dict, run_id: str, packed: dict, summary: dict, totals: dict, bounds: list,
               area_fc: dict | None = None, area_totals: dict | None = None,
               over: dict | None = None) -> str:
    m, L = cfg["map"], cfg["_labels"]
    template = TEMPLATE.read_text(encoding="utf-8")
    values = {
        "__LANG__": escape(m["locale"].split("-")[0].lower()),
        "__CSP__": escape(csp.policy(template, m["_hosts"], data_images=bool(over))),
        "__THEME_CSS__": theme.css(cfg["_theme"]),
        "__TITLE__": escape(m["title"]),
        "__SUBTITLE__": escape(m.get("subtitle") or ""),
        "__CTA__": escape(m.get("call_to_action") or ""),
        "__NOTE__": escape(m.get("data_note") or ""),
        "__LOADING__": escape(L["loading"]),
        "__SOURCES_TITLE__": escape(L["sources"]),
        "__SOURCES__": _sources(cfg, run_id, area_fc, over),
        "__SETTINGS__": _json(_settings(cfg, totals, bounds, area_fc, area_totals, over)),
        "__DATA__": _json(packed),
        "__SUMMARY__": _json(summary),
        "__AREAS__": _json(area_fc or {"type": "FeatureCollection", "features": []}),
        "__OVERLAY_URL__": _json(over["url"] if over else ""),
    }
    # one pass over the template: text that happens to look like a placeholder inside a value
    # (a record, a title) is never filled in a second time
    pattern = re.compile("|".join(re.escape(k) for k in values))
    return pattern.sub(lambda mt: values[mt.group(0)], template)
