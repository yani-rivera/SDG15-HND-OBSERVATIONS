"""Optional raster overlay (e.g. tree canopy height) drawn under the records.

The raster is reprojected to Web Mercator (EPSG:3857) so a MapLibre image source lines
up exactly with the points, coloured with a stretch, made transparent below a threshold,
and embedded as a PNG."""
import base64
import io

import numpy as np
import rasterio
from PIL import Image
from rasterio.warp import Resampling, calculate_default_transform, reproject, transform_bounds


def _hex(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _ramp(values: np.ndarray, colors: list[str]) -> np.ndarray:
    """values in 0..1 -> RGB via linear interpolation between the given colours."""
    stops = np.array([_hex(c) for c in colors], dtype=float)
    x = np.linspace(0, 1, len(stops))
    return np.stack([np.interp(values, x, stops[:, i]) for i in range(3)], axis=-1)


def build_overlay(ocfg: dict) -> tuple[dict, dict]:
    """Returns (overlay for the page, stats for provenance)."""
    with rasterio.open(ocfg["file"]) as src:
        band = src.read(1).astype("float32")
        nodata = src.nodata
        src_crs, src_transform = src.crs, src.transform
        width, height, bounds = src.width, src.height, src.bounds
        res = src.res

    dst_crs = "EPSG:3857"
    tr, w, h = calculate_default_transform(src_crs, dst_crs, width, height, *bounds)
    merc = np.full((h, w), np.nan, dtype="float32")
    reproject(band, merc, src_transform=src_transform, src_crs=src_crs, src_nodata=nodata,
              dst_transform=tr, dst_crs=dst_crs, dst_nodata=np.nan, resampling=Resampling.nearest)

    lo, hi = ocfg.get("stretch", [float(np.nanmin(merc)), float(np.nanmax(merc))])
    vmin = ocfg.get("min_value", lo)
    valid = np.isfinite(merc) & (merc >= vmin)
    t = np.clip((np.nan_to_num(merc, nan=lo) - lo) / (hi - lo), 0, 1)
    rgb = _ramp(t, ocfg["colors"])
    alpha = np.where(valid, int(255 * ocfg.get("opacity", 0.85)), 0)
    img = np.dstack([rgb, alpha]).astype("uint8")

    buf = io.BytesIO()
    Image.fromarray(img, "RGBA").save(buf, format="PNG", optimize=True)
    left, bottom, right, top = transform_bounds(dst_crs, "EPSG:4326",
                                                tr.c, tr.f + tr.e * h, tr.c + tr.a * w, tr.f)
    page = {
        "title": ocfg.get("title", "Overlay"),
        "unit": ocfg.get("unit", ""),
        "stretch": [lo, hi], "minValue": vmin, "colors": ocfg["colors"],
        "defaultOn": ocfg.get("default_on", True),
        "baselineGroup": ocfg.get("baseline_group"), "baselineLabel": ocfg.get("baseline_label"),
        "url": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(),
        "coordinates": [[left, top], [right, top], [right, bottom], [left, bottom]],
    }
    finite = band[np.isfinite(band)] if nodata is None else band[(band != nodata) & np.isfinite(band)]
    stats = {
        "source_crs": str(src_crs), "source_resolution": [round(r, 3) for r in res],
        "source_size": [width, height], "web_size": [w, h],
        "share_at_or_above_min": round(float((finite >= vmin).mean()), 4),
        "max_value": float(finite.max()), "png_kb": round(len(buf.getvalue()) / 1024, 1),
        "bounds_wgs84": [round(left, 5), round(bottom, 5), round(right, 5), round(top, 5)],
    }
    return page, stats


def sample_records(ocfg: dict, records: list[dict]) -> dict:
    """Overlay value at each record and the highest value within `sample_radius_m`.

    Sampled on the original raster (its own CRS and cells), not the web image. Adds
    r["over_here"] and r["over_near"] (rounded to 0.1; None outside the raster or for
    records without coordinates). Returns summary stats for provenance."""
    from rasterio.warp import transform as warp_points
    from scipy.ndimage import maximum_filter

    radius = float(ocfg["sample_radius_m"])
    with rasterio.open(ocfg["file"]) as src:
        band = src.read(1).astype("float32")
        if src.nodata is not None:
            band[band == src.nodata] = np.nan
        crs, tr = src.crs, src.transform
        cell = abs(src.res[0])
    k = 2 * int(round(radius / cell)) + 1
    yy, xx = np.mgrid[:k, :k] - k // 2
    disc = (xx ** 2 + yy ** 2) * cell ** 2 <= radius ** 2        # round neighbourhood, not a square
    near = maximum_filter(np.nan_to_num(band, nan=-1), footprint=disc, mode="constant", cval=-1)

    pts = [r for r in records if r.get("lat") is not None and r.get("lon") is not None]
    for r in records:
        r["over_here"] = r["over_near"] = None
    if not pts:
        return {}
    xs, ys = warp_points("EPSG:4326", crs, [r["lon"] for r in pts], [r["lat"] for r in pts])
    rows, cols = rasterio.transform.rowcol(tr, xs, ys)
    h, w = band.shape
    inside = n_near = 0
    vmin = ocfg.get("min_value", 0)
    for r, i, j in zip(pts, rows, cols):
        if 0 <= i < h and 0 <= j < w and np.isfinite(band[i, j]):
            inside += 1
            r["over_here"] = round(float(band[i, j]), 1)
            r["over_near"] = round(float(near[i, j]), 1) if near[i, j] >= 0 else None
            n_near += (near[i, j] >= vmin)
    return {"sample_radius_m": radius, "records_inside_raster": inside,
            "share_with_value_ge_min_within_radius": round(n_near / inside, 4) if inside else None,
            "area_share_ge_min_within_radius": round(float(((near >= vmin) & np.isfinite(band)).sum()
                                                           / np.isfinite(band).sum()), 4)}


def find_peaks(ocfg: dict) -> tuple[list, dict]:
    """Local maxima at or above `highlight.min_value` (e.g. tall trees), at least
    `highlight.min_separation_m` apart, on the original raster. Returns ([lon, lat, value]...), stats."""
    from rasterio.warp import transform as warp_points
    from scipy import ndimage as ndi

    hcfg = ocfg["highlight"]
    with rasterio.open(ocfg["file"]) as src:
        band = src.read(1).astype("float32")
        if src.nodata is not None:
            band[band == src.nodata] = np.nan
        crs, tr, cell = src.crs, src.transform, abs(src.res[0])
    a = np.nan_to_num(band, nan=-1)
    k = 2 * int(round(hcfg.get("min_separation_m", 30) / cell)) + 1
    peak = (ndi.maximum_filter(a, size=k, mode="constant", cval=-1) == a) & (a >= hcfg["min_value"])
    # plateaus: keep one cell per flat-topped group
    lab, n = ndi.label(peak)
    if n == 0:
        return [], {"peaks": 0}
    centers = ndi.maximum_position(a, lab, range(1, n + 1))
    rows = np.array([c[0] for c in centers]); cols = np.array([c[1] for c in centers])
    vals = a[rows, cols]
    xs, ys = rasterio.transform.xy(tr, rows, cols)
    lon, lat = warp_points(crs, "EPSG:4326", list(xs), list(ys))
    order = np.argsort(-vals)
    pts = [[round(lon[i], 6), round(lat[i], 6), round(float(vals[i]), 1)] for i in order]
    area_ha = float((a >= hcfg["min_value"]).sum() * cell * cell / 1e4)
    return pts, {"peaks": len(pts), "highlight_min": hcfg["min_value"],
                 "area_ha_at_or_above": round(area_ha, 1), "max": float(vals.max())}
