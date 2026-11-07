"""Make a map's data package for archiving (e.g. on Zenodo).

    python package_data.py --config config/bees.yaml --out ../dont-tell-the-bees-data

Writes records.csv, source_datasets.csv, taxa_status.csv, the area table (if any) and
package_provenance.json. Add the hand-written README.md to the folder before uploading.
"""
import argparse

from gbifc import __project__, __version__, gbif
from gbifc.config import load_config
from gbifc.package import make_package


def main():
    ap = argparse.ArgumentParser(description=f"{__project__} v{__version__}: data package")
    ap.add_argument("--config", required=True, help="e.g. config/bees.yaml")
    ap.add_argument("--out", required=True, help="output folder, outside this repository")
    args = ap.parse_args()

    cfg = load_config(args.config)
    records, _ = gbif.read_occurrences(
        cfg["gbif"]["file"], cfg["gbif"].get("filter"),
        groups=cfg["groups"], keep_only_groups=cfg["gbif"].get("keep_only_groups", False))
    prov = make_package(cfg, records, args.out)
    print(f"{args.out}: {prov['records_csv']['rows']} records, {prov['source_datasets']} source datasets"
          + (f", {prov['taxa']} taxa" if "taxa" in prov else "")
          + (f", {prov['area_table']['file']}" if "area_table" in prov else ""))


if __name__ == "__main__":
    main()
