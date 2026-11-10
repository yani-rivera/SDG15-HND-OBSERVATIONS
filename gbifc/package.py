"""Data package for archiving a map's inputs (e.g. on Zenodo).

Writes, into an output folder:
  records.csv          every record of the GBIF download, all columns, as comma-separated UTF-8
                       (a format change only: same rows, same values)
  source_datasets.csv  GBIF datasetKey, records kept from it, and its licence(s) (for crediting
                       publishers, and for a GBIF derived-dataset registration if ever needed)
  taxa_status.csv      every taxon with its record count and the native status the map gives it,
                       and whether that status came from the species, the genus or the default
  <area table>         the area table (e.g. honey by department), copied unchanged
  package_provenance.json  code version, config hash, input SHA-256s, row counts

The README for the package is written by hand: it carries the judgement (method, caveats,
licences) that a script should not invent.
"""
import csv
import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from . import __project__, __version__
from .gbif import open_table, taxon_label
from .provenance import sha256
from .taxa import status_of


def _raw_rows(path: Path):
    """All rows and columns of the records file, untouched (whatever its separator)."""
    f, rd = open_table(path)
    with f:
        return rd.fieldnames, list(rd)


def write_records(src: Path, out: Path) -> tuple[list[str], list[dict]]:
    fields, rows = _raw_rows(src)
    with (out / "records.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return fields, rows


def write_source_datasets(rows: list[dict], out: Path) -> int:
    count, licences = Counter(), defaultdict(set)
    for r in rows:
        k = r.get("datasetKey", "")
        count[k] += 1
        licences[k].add(r.get("license", ""))
    with (out / "source_datasets.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["datasetKey", "records", "license"])
        for k, n in count.most_common():
            w.writerow([k, n, ";".join(sorted(licences[k]))])
    return len(count)


def write_taxa_status(records: list[dict], taxa_cfg: dict, out: Path) -> int:
    seen = {}
    for r in records:
        label = taxon_label(r)
        status, how = status_of(r, taxa_cfg)
        e = seen.setdefault(label, {"taxon": label, "genus": r.get("genus", ""), "records": 0,
                                    "status": status, "status_from": how})
        e["records"] += 1
    rows = sorted(seen.values(), key=lambda e: (-e["records"], e["taxon"]))
    with (out / "taxa_status.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["taxon", "genus", "records", "status", "status_from"])
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def make_package(cfg: dict, records: list[dict], out_dir: str | Path) -> dict:
    out = Path(out_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    src = Path(cfg["gbif"]["file"])
    fields, rows = write_records(src, out)
    prov = {
        "project": __project__,
        "script_version": __version__,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "config": Path(cfg["_path"]).name,
        "config_sha256": sha256(cfg["_path"]),
        "gbif": {"file": src.name, "sha256": sha256(src), "doi": cfg["gbif"].get("doi"),
                 "citation": cfg["gbif"]["citation"]},
        "records_csv": {"rows": len(rows), "columns": len(fields), "sha256": sha256(out / "records.csv")},
        "source_datasets": write_source_datasets(rows, out),
    }
    if cfg.get("_status"):
        prov["taxa"] = write_taxa_status(records, cfg["taxa"], out)
    area = cfg.get("areas") or {}
    if area.get("table"):
        t = Path(area["table"])
        shutil.copy(t, out / t.name)
        prov["area_table"] = {"file": t.name, "sha256": sha256(t), "source": area.get("source")}
    (out / "package_provenance.json").write_text(json.dumps(prov, indent=2, ensure_ascii=False),
                                                 encoding="utf-8")
    return prov
