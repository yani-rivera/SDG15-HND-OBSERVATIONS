"""Copy a finished build into a site folder (e.g. a GitHub Pages repo).

The site folder only ever receives built files: index.html, provenance.json and
an empty .nojekyll. Nothing in it is edited by hand, so a rebuild can always
replace it, and provenance.json records exactly which code, config and data made it.
"""
import shutil
from pathlib import Path

SITE_FILES = {"map.html": "index.html", "provenance.json": "provenance.json"}


def publish(run_dir: Path, site_dir: str | Path) -> Path:
    site = Path(site_dir).expanduser()
    site.mkdir(parents=True, exist_ok=True)   # e.g. birds/ on the first build
    for src, dst in SITE_FILES.items():
        shutil.copy(Path(run_dir) / src, site / dst)
    (site / ".nojekyll").touch()   # GitHub Pages: serve files as they are
    return site
