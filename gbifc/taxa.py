"""Native status and footnotes, looked up species → genus → default."""
from collections import Counter

from .gbif import taxon_label


def status_of(rec: dict, taxa_cfg: dict) -> tuple[str, str]:
    """(status, how) — how = 'species' | 'genus' | 'default' | 'unknown'."""
    table = taxa_cfg.get("status") or {}
    if rec["species"] and rec["species"] in table:
        return table[rec["species"]], "species"
    if rec["genus"] and rec["genus"] in table:
        return table[rec["genus"]], "genus"
    if not rec["species"] and not rec["genus"]:
        return "Unknown", "unknown"
    return taxa_cfg["default"], "default"


def status_review(records: list[dict], taxa_cfg: dict) -> list[dict]:
    """Every taxon whose status came from the default rule, with its record count."""
    c = Counter(taxon_label(r) for r in records if status_of(r, taxa_cfg)[1] == "default")
    return [{"taxon": t, "records": n, "status_assigned": taxa_cfg["default"]}
            for t, n in sorted(c.items(), key=lambda x: (-x[1], x[0]))]
