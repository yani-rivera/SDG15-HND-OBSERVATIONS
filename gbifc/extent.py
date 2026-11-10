"""Opening view of the map when the config does not give one (`map.bounds: auto`).

Fits the records that can be mapped, with a little room around them. A single stray
coordinate (a record placed in the sea, or in another country) widens the view, so the
result is logged in provenance.json: check it, and set `map.bounds` by hand if needed.
"""


def bounds_of(records: list[dict], max_uncertainty_m=None, pad: float = 0.04) -> list[list[float]]:
    """[[west, south], [east, north]] around every record the map will draw."""
    pts = [(r["lon"], r["lat"]) for r in records
           if r["lat"] is not None and r["lon"] is not None
           and not (max_uncertainty_m and r["uncertainty_m"] and r["uncertainty_m"] > max_uncertainty_m)]
    if not pts:
        raise ValueError("map.bounds: no record has coordinates, so the opening view cannot be "
                         "worked out; set map.bounds: [[west, south], [east, north]]")
    w, e = min(p[0] for p in pts), max(p[0] for p in pts)
    s, n = min(p[1] for p in pts), max(p[1] for p in pts)
    dx = max((e - w) * pad, 0.01)       # at least about 1 km, so one point still gets a view
    dy = max((n - s) * pad, 0.01)
    return [[round(max(w - dx, -180), 4), round(max(s - dy, -85), 4)],
            [round(min(e + dx, 180), 4), round(min(n + dy, 85), 4)]]
