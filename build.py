"""Build an interactive companion map from a GBIF occurrence download.

    python build.py --config config/bees.yaml
    python build.py --version
"""
import argparse

from gbifc import __project__, __version__
from gbifc.config import load_config
from gbifc.provenance import Run
from gbifc import gbif, taxa, checks, render, areas, overlay
from gbifc.provenance import sha256
from gbifc.publish import publish


def main():
    ap = argparse.ArgumentParser(description=f"{__project__} v{__version__}")
    ap.add_argument("--version", action="version", version=f"{__project__} {__version__}")
    ap.add_argument("--config", required=True, help="e.g. config/bees.yaml")
    args = ap.parse_args()

    cfg = load_config(args.config)
    run = Run(cfg)
    print(f"{__project__} v{__version__} [{cfg['_name']}] → {run.dir}")

    records, stats = gbif.read_occurrences(
        cfg["gbif"]["file"], cfg["gbif"].get("filter"),
        groups=cfg["groups"], keep_only_groups=cfg["gbif"].get("keep_only_groups", False))
    totals = {k: stats.pop(k) for k in ("totals_by_year", "totals_by_month")}
    run.log_step("read", **stats)

    summ = checks.summary(records, cfg["gbif"].get("max_uncertainty_m"))
    if cfg["_status"]:
        review = taxa.status_review(records, cfg["taxa"])
        checks.write_csv(review, run.dir / "status_review.csv")
        summ["taxa_with_default_status"] = len(review)
    if cfg["groups"]:
        summ["by_group"] = {g["name"]: sum(1 for r in records if r["group"] == i)
                            for i, g in enumerate(cfg["groups"])}
    run.log_step("checks", **summ)
    print(f"records: {summ['records']} · no coordinates: {summ['no_coordinates']} · "
          f"no year: {summ['no_year']} · uncertainty >10 km: {summ['uncertainty_over_10km']} · "
          f"possible duplicates: {summ['possible_duplicates']}")

    area_fc = area_totals = None
    if cfg.get("areas"):
        area_fc, area_totals, area_issues = areas.load_areas(cfg["areas"])
        checks.write_csv(area_issues, run.dir / "areas_report.csv")
        run.log_step("areas", features=len(area_fc["features"]), totals=area_totals,
                     issues=len(area_issues))
        print(f"areas: {len(area_fc['features'])} features, {len(area_issues)} join notes (areas_report.csv)")

    over = None
    if cfg.get("overlay"):
        over, ostats = overlay.build_overlay(cfg["overlay"])
        run.log_step("overlay", file=cfg["overlay"]["file"], sha256=sha256(cfg["overlay"]["file"]), **ostats)
        print(f"overlay: {ostats['web_size']} px, {ostats['png_kb']} KB, "
              f"{ostats['share_at_or_above_min']:.1%} of pixels ≥ {cfg['overlay'].get('min_value')}")
        if cfg["overlay"].get("highlight"):
            peaks, pstats = overlay.find_peaks(cfg["overlay"])
            over["highlight"] = {**{k: v for k, v in cfg["overlay"]["highlight"].items()}, **pstats, "points": peaks}
            run.log_step("overlay_highlight", **pstats)
            print(f"highlight: {pstats['peaks']} spots ≥ {pstats['highlight_min']} ({pstats.get('area_ha_at_or_above')} ha)")
        if cfg["overlay"].get("sample_radius_m"):
            sstats = overlay.sample_records(cfg["overlay"], records)
            over["sample"] = sstats
            run.log_step("overlay_sample", **sstats)
            print(f"overlay at records: {sstats.get('share_with_value_ge_min_within_radius', 0):.1%} of records within "
                  f"{sstats.get('sample_radius_m'):g} m of a value ≥ {cfg['overlay'].get('min_value')} "
                  f"(area: {sstats.get('area_share_ge_min_within_radius', 0):.1%})")

    packed = render.pack(records, cfg)
    html = render.build_html(cfg, run.dir.name, packed, summ, totals, area_fc, area_totals, over)
    out = run.dir / "map.html"
    out.write_text(html, encoding="utf-8")
    run.log_step("map", output=out.name, size_mb=round(out.stat().st_size / 1e6, 2))
    print(f"map: {out} ({out.stat().st_size / 1e6:.2f} MB)")

    site_dir = cfg["run"].get("publish_dir")
    if site_dir:   # copy the finished page into the site folder (its own repo)
        run.log_step("publish", site_dir=site_dir)
        site = publish(run.dir, site_dir)
        print(f"site: {site} (index.html, provenance.json)")


if __name__ == "__main__":
    main()
