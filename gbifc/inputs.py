"""The input files a config needs, checked before a build starts.

Data never goes in the repository, so a fresh copy of the code has an empty data/ folder.
Naming what is missing, and where each file comes from, is kinder than a Python error.
"""
from pathlib import Path


def required_files(cfg: dict) -> list[tuple[str, str, str]]:
    """(config option, path, where the file comes from) for every input of this map."""
    g, a, o = cfg["gbif"], cfg.get("areas") or {}, cfg.get("overlay") or {}
    files = [("gbif.file", g["file"], g.get("citation", ""))]
    if a:
        files.append(("areas.geojson", a["geojson"], a.get("geojson_source", "")))
        files.append(("areas.table", a["table"], a.get("source", "")))
    if o:
        files.append(("overlay.file", o["file"], o.get("source", "")))
    return files


def missing(cfg: dict) -> list[str]:
    """One line per input file that is not there."""
    return [f"{option}: {path} not found" + (f"\n    source: {source}" if source else "")
            for option, path, source in required_files(cfg) if not Path(path).expanduser().is_file()]
