"""Read an occurrence table into plain dicts.

A GBIF occurrence download (simple CSV = tab-separated, unquoted; or a DwC-A occurrence.txt)
works as it is. Any other table (your own survey, a museum or iNaturalist export; comma-,
semicolon- or tab-separated) works too when its columns use GBIF's (Darwin Core) names, or
when the config's `columns:` section says which of its columns holds each one."""
import csv
import re
from pathlib import Path

FIELDS = ["gbifID", "occurrenceID", "family", "genus", "species", "scientificName", "taxonRank",
          "countryCode", "stateProvince", "locality", "decimalLatitude", "decimalLongitude",
          "coordinateUncertaintyInMeters", "eventDate", "year", "month", "basisOfRecord",
          "institutionCode", "collectionCode", "recordedBy", "license", "datasetKey"]


REQUIRED = ("decimalLatitude", "decimalLongitude", "species")
_ISO_DATE = re.compile(r"(\d{4})(?:-(\d{2}))?")


def open_table(path: Path):
    """(open file, DictReader). Tab-separated files are read unquoted, as GBIF writes them;
    otherwise the separator is a semicolon if the header has more of those than commas."""
    with path.open(encoding="utf-8-sig", newline="") as f:
        header = f.readline()
    f = path.open(encoding="utf-8-sig", newline="")
    if "\t" in header:
        return f, csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
    return f, csv.DictReader(f, delimiter=";" if header.count(";") > header.count(",") else ",")


def _check_columns(path: Path, header: list[str], columns: dict, filters: dict, groups: list[dict]) -> None:
    """Every column the config relies on must be in the file; say which is not, and what is there."""
    there = ", ".join(header[:40]) + (" …" if len(header) > 40 else "")
    absent = {dwc: col for dwc, col in columns.items() if col not in header}
    if absent:
        raise ValueError(f"{path.name}: columns: names column(s) that are not in the file: "
                         f"{', '.join(f'{d}: {c}' for d, c in absent.items())}. The file has: {there}")
    known = set(header) | set(columns)
    missing = [c for c in REQUIRED if c not in known]
    if missing:
        raise ValueError(f"{path.name}: no column for {', '.join(missing)}. If the file names them differently, "
                         f"say so under columns: in the config (e.g. decimalLatitude: lat). The file has: {there}")
    used = {k: "gbif.filter" for k in filters} | {k: f"groups[{g['name']}].match" for g in groups for k in g["match"]}
    unknown = {k: where for k, where in used.items() if k not in known}
    if unknown:
        raise ValueError(f"{path.name}: {', '.join(f'{where} uses {k}' for k, where in unknown.items())}, "
                         f"but the file has no such column. The file has: {there}")


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
                     keep_only_groups: bool = False, columns: dict | None = None,
                     dates_from_event: bool = False) -> tuple[list[dict], dict]:
    """Returns (records, stats).

    `columns` maps a GBIF field name to the file's own column name (e.g. decimalLatitude: lat);
    filters and group matches may use either name. With `dates_from_event`, a record with no
    year or month takes them from an ISO eventDate (2024-05-17); GBIF downloads already carry both.

    `filters` (AND across fields) decides what counts at all. Totals by year and by month
    are taken over everything passing `filters`, BEFORE any group selection, so a group's
    share of all records can be shown (a simple correction for observer effort).
    With `keep_only_groups`, records outside every group are counted but not kept."""
    path = Path(path)
    f, rows = open_table(path)
    columns = columns or {}
    filters = {k: set(v) for k, v in (filters or {}).items()}
    groups = groups or []
    try:
        _check_columns(path, list(rows.fieldnames or []), columns, filters, groups)
    except ValueError:
        f.close()
        raise
    out = []
    stats = {"rows": 0, "filtered_out": 0, "outside_groups": 0,
             "totals_by_year": {}, "totals_by_month": {}}
    with f:
        for r in rows:
            stats["rows"] += 1
            for field, col in columns.items():      # the file's own column names -> GBIF's
                r[field] = r.get(col)
            if dates_from_event and not (r.get("year") and r.get("month")):
                found = _ISO_DATE.match((r.get("eventDate") or "").strip())
                if found:
                    r["year"] = r.get("year") or found.group(1)
                    r["month"] = r.get("month") or (found.group(2) or "")
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
