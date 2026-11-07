"""Load and validate a companion config."""
from pathlib import Path
import yaml

REQUIRED = {"gbif": ["file", "citation"], "map": ["title", "colors", "bounds"]}


def load_config(path: str | Path) -> dict:
    path = Path(path)
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    for section, keys in REQUIRED.items():
        missing = [k for k in keys if k not in (cfg.get(section) or {})]
        if missing:
            raise ValueError(f"{path.name}: [{section}] missing {missing}")
    # optional sections
    cfg["taxa"] = cfg.get("taxa") or {}
    cfg.setdefault("groups", [])
    cfg["_status"] = "default" in cfg["taxa"]      # native-status rule present?
    if not cfg["_status"] and not cfg["groups"]:
        raise ValueError(f"{path.name}: needs a `taxa` (native status) or a `groups` section")
    for g in cfg["groups"]:
        if not g.get("name") or not g.get("match") or not g.get("color"):
            raise ValueError(f"{path.name}: every group needs name, color and match")
    cfg["_path"] = str(path.resolve())
    cfg["_name"] = path.stem
    return cfg
