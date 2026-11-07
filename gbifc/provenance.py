"""Run folder + provenance.json (versions, config hash, input hash, GBIF citation)."""
import hashlib
import json
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import __project__, __version__


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Run:
    def __init__(self, cfg: dict):
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.dir = Path(cfg["run"]["output_dir"]) / run_id
        self.dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(cfg["_path"], self.dir / Path(cfg["_path"]).name)
        g = cfg["gbif"]
        self.prov = {
            "run_id": run_id,
            "project": __project__,
            "script_version": __version__,
            "config": Path(cfg["_path"]).name,
            "config_sha256": sha256(cfg["_path"]),
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "environment": {"python": sys.version.split()[0], "platform": platform.platform()},
            "input": {"file": g["file"], "sha256": sha256(g["file"]),
                      "gbif_download_key": g.get("download_key"), "gbif_doi": g.get("doi"),
                      "citation": g["citation"]},
            "steps": [],
        }
        self.save()

    def log_step(self, name: str, **info):
        self.prov["steps"].append(
            {"step": name, "finished_utc": datetime.now(timezone.utc).isoformat(), **info})
        self.save()

    def save(self):
        (self.dir / "provenance.json").write_text(
            json.dumps(self.prov, indent=2, ensure_ascii=False), encoding="utf-8")
