"""Read a GBIF occurrence download (simple CSV = tab-separated, unquoted; or a
comma-separated export; or a DwC-A occurrence.txt) into plain dicts."""
import csv
from pathlib import Path

FIELDS = ["gbifID", "occurrenceID", "family", "genus", "species", "scientificName", "taxonRank",
          "countryCode", "stateProvince", "locality", "decimalLatitude", "decimalLongitude",
          "coordinateUncertaintyInMeters", "eventDate", "year", "month", "basisOfRecord",
          "institutionCode", "collectionCode", "recordedBy", "license", "datasetKey"]


def _reader(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        header = f.readline()
    tab = "\t" in header
    f = path.open(encoding="utf-8-sig", newline="")
    if tab:  # GBIF simple downloads: tab-separated, no quoting
        return f, csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
    return f, csv.DictReader(f)


def _float(x):
    try:
        return float(x) if x not in (None, "") else None
    except ValueError:
        return None


def _int(x):
    v = _float(x)
    return int(v) if v is not None else None


def group_of(row: dict, groups: list[dict]) -> int | None:
    """Index of the first group whose `match` fits the row (any listed field value)."""
    for i, g in enumerate(groups):
        if any((row.get(field) or "") in set(vals) for field, vals in g["match"].items()):
            return i
    return None


def read_occurrences(path, filters: dict | None = None, groups: list[dict] | None = None,
                     keep_only_groups: bool = False) -> tuple[list[dict], dict]:
    """Returns (records, stats).

    `filters` (AND across fields) decides what counts at all. Totals by year and by month
    are taken over everything passing `filters`, BEFORE any group selection, so a group's
    share of all records can be shown (a simple correction for observer effort).
    With `keep_only_groups`, records outside every group are counted but not kept."""
    path = Path(path)
    f, rows = _reader(path)
    missing = [c for c in ("decimalLatitude", "decimalLongitude", "species") if c not in (rows.fieldnames or [])]
    if missing:
        f.close()
        raise ValueError(f"{path.name}: not a GBIF occurrence table (missing {missing})")
    filters = {k: set(v) for k, v in (filters or {}).items()}
    groups = groups or []
    out = []
    stats = {"rows": 0, "filtered_out": 0, "outside_groups": 0,
             "totals_by_year": {}, "totals_by_month": {}}
    with f:
        for r in rows:
            stats["rows"] += 1
            if any((r.get(k) or "") not in vals for k, vals in filters.items()):
                stats["filtered_out"] += 1
                continue
            y, m = _int(r.get("year")), _int(r.get("month"))
            if y is not None:
                stats["totals_by_year"][y] = stats["totals_by_year"].get(y, 0) + 1
            if m is not None:
                stats["totals_by_month"][m] = stats["totals_by_month"].get(m, 0) + 1
            gi = group_of(r, groups) if groups else None
            if groups and keep_only_groups and gi is None:
                stats["outside_groups"] += 1
                continue
            rec = {k: (r.get(k) or "").strip() for k in FIELDS}
            rec["lat"] = _float(rec.pop("decimalLatitude"))
            rec["lon"] = _float(rec.pop("decimalLongitude"))
            rec["uncertainty_m"] = _float(rec.pop("coordinateUncertaintyInMeters"))
            rec["year"], rec["month"] = y, m
            rec["group"] = gi
            out.append(rec)
    stats["kept"] = len(out)
    stats["totals_by_year"] = dict(sorted(stats["totals_by_year"].items()))
    stats["totals_by_month"] = dict(sorted(stats["totals_by_month"].items()))
    return out, stats


def taxon_label(rec: dict) -> str:
    """Species if known, else 'Genus sp.', else the family."""
    if rec["species"]:
        return rec["species"]
    if rec["genus"]:
        return f"{rec['genus']} sp."
    return rec["family"] or "Unidentified"
