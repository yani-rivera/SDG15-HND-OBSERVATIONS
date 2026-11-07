"""Optional area layer (e.g. honey production by department) under the records.

Boundaries come from a GeoJSON (simplified for the web); values from a CSV joined
by an ID code, never by name. Checks: join coverage both ways, name agreement
(accent-insensitive), and expected totals."""
import csv
import json
import unicodedata
from pathlib import Path

from shapely.geometry import mapping, shape


def _norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower().strip()


def _num(x):
    x = (x or "").strip()
    return float(x) if x else None


def _round_coords(o, nd=4):
    if isinstance(o, (list, tuple)):
        return [_round_coords(x, nd) for x in o]
    return round(o, nd) if isinstance(o, float) else o


def load_areas(acfg: dict) -> tuple[dict, dict, list[dict]]:
    """Returns (feature collection, totals, issues)."""
    g = json.loads(Path(acfg["geojson"]).read_text(encoding="utf-8"))
    idf, lab = acfg["id_field"], acfg.get("label_field", acfg["id_field"])
    with Path(acfg["table"]).open(encoding="utf-8-sig", newline="") as f:
        lines = [ln for ln in f if not ln.lstrip().startswith("#")]  # allow source/comment lines
        rows = {r[acfg["table_id"]].strip(): r for r in csv.DictReader(lines)}
    keys = [v["key"] for v in acfg["variables"]] + list(acfg.get("extra_fields", []))
    issues, feats, geo_ids = [], [], set()

    for feat in g["features"]:
        code = str(feat["properties"][idf]).strip()
        geo_ids.add(code)
        geom = shape(feat["geometry"]).simplify(acfg.get("simplify_deg", 0.003), preserve_topology=True)
        props = {"id": code, "name": feat["properties"].get(lab, code)}
        row = rows.get(code)
        if row is None:
            issues.append({"id": code, "name": props["name"], "issue": "no row in table (shown as no data)"})
        else:
            tname = row.get(acfg.get("table_label", ""), "")
            if tname:
                if _norm(tname) != _norm(props["name"]):
                    issues.append({"id": code, "name": props["name"], "issue": f"table name differs: {tname}"})
                props["name"] = tname  # the table's spelling (with accents)
            for k in keys:
                props[k] = _num(row.get(k))
        props["name"] = (acfg.get("name_overrides") or {}).get(code, props["name"])
        feats.append({"type": "Feature", "properties": props,
                      "geometry": _round_coords(mapping(geom))})

    for code in rows.keys() - geo_ids:
        issues.append({"id": code, "name": rows[code].get(acfg.get("table_label", ""), ""),
                       "issue": "row has no boundary (not drawn)"})

    totals = {k: round(sum(_num(r.get(k)) or 0 for r in rows.values()), 3) for k in keys}
    for k, expected in (acfg.get("check_totals") or {}).items():
        if abs(totals.get(k, 0) - expected) > max(0.5, abs(expected) * 1e-6):
            issues.append({"id": "", "name": "TOTAL", "issue": f"{k}: sum {totals.get(k)} ≠ expected {expected}"})
    return {"type": "FeatureCollection", "features": feats}, totals, issues
