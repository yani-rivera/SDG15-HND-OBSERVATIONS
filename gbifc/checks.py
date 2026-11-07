"""ABC checks on the records: what can't be mapped or dated, and what is imprecise."""
import csv
from collections import Counter
from pathlib import Path


def summary(records: list[dict], max_uncertainty_m) -> dict:
    no_coords = sum(1 for r in records if r["lat"] is None or r["lon"] is None)
    no_year = sum(1 for r in records if r["year"] is None)
    unc = [r["uncertainty_m"] for r in records if r["uncertainty_m"] is not None]
    dup_keys = Counter((r["species"], r["lat"], r["lon"], r["eventDate"]) for r in records
                       if r["lat"] is not None and r["eventDate"])
    return {
        "records": len(records),
        "no_coordinates": no_coords,
        "no_year": no_year,
        "uncertainty_over_10km": sum(1 for u in unc if u > 10_000),
        "hidden_by_max_uncertainty": (sum(1 for u in unc if u > max_uncertainty_m)
                                      if max_uncertainty_m else 0),
        "possible_duplicates": sum(n - 1 for n in dup_keys.values() if n > 1),
        "by_basis": dict(Counter(r["basisOfRecord"] or "unknown" for r in records).most_common()),
    }


def write_csv(rows: list[dict], path):
    if not rows:
        Path(path).write_text("no rows\n", encoding="utf-8")
        return
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
