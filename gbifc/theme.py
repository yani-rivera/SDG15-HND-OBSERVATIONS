"""Page theme: dark or light background, and the colours of the panel, chart and points.

`map.theme` picks a preset (panel, popups, chart and a matching base map). `map.colors`
sets the data colours; `map.theme_colors` can change single colours of the preset.
Every colour is checked (#rrggbb) before it is written into the page, and colours that
would be hard to see on the chosen background are reported at build time.
"""
from . import validate as v

# Each preset: the base map that goes with it, the page colours, and default data colours.
# `map_bg` is the base map's land colour (OpenFreeMap dark / positron); it is only used to
# check that points will be visible, never drawn.
THEMES = {
    "dark": {
        "basemap": "https://tiles.openfreemap.org/styles/dark",
        "panel_opacity": 0.95,
        "page": {
            "bg": "#141518", "panel": "#141518", "ink": "#f2eee6", "muted": "#a8a29a",
            "line": "#2e3036", "button": "#202227", "row_line": "#1d1f23", "hover": "#1f2126",
            "tip": "#0d0e10", "popup": "#1a1b1f", "axis": "#3a3c42", "error": "#ee8888",
            "area_line": "#0b0b0c", "point_outline": "#141518", "no_data": "#1c1d20",
            "select": "#ffffff", "map_bg": "#0c0c0c",
        },
        "data": {
            "accent": "#f5b301", "introduced": "#f3efe6", "other": "#9aa0a6",
            "basis": ["#f5b301", "#7cc6fe", "#e86f5a", "#b48ef0", "#9aa0a6"],
        },
    },
    "light": {
        "basemap": "https://tiles.openfreemap.org/styles/positron",
        "panel_opacity": 0.96,
        "page": {
            "bg": "#f2f3f0", "panel": "#ffffff", "ink": "#1d1f24", "muted": "#5d626b",
            "line": "#d8d6d0", "button": "#f1efea", "row_line": "#eceae5", "hover": "#f4f2ed",
            "tip": "#ffffff", "popup": "#ffffff", "axis": "#b5b2ab", "error": "#b3261e",
            "area_line": "#ffffff", "point_outline": "#2b2d33", "no_data": "#e3e1dc",
            "select": "#1d1f24", "map_bg": "#f2f3f0",
        },
        "data": {
            "accent": "#8a5a00", "introduced": "#46505c", "other": "#8a8f98",
            "basis": ["#a86f00", "#1c6fb0", "#c2412d", "#7347c2", "#6b7078"],
        },
    },
}
DATA_KEYS = ("accent", "native", "introduced", "other", "ring", "basis")
MIN_POINT_CONTRAST = 1.6     # a dot against the base map
MIN_TEXT_CONTRAST = 3.0      # the accent used for the title, links and thin chart lines


def _rgb(c: str) -> tuple[int, int, int]:
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def _luminance(c: str) -> float:
    def lin(x):
        x /= 255
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(x) for x in _rgb(c))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    """WCAG contrast ratio between two colours (1 = identical, 21 = black on white)."""
    la, lb = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def mix(a: str, b: str, share_of_a: float) -> str:
    return "#" + "".join(f"{round(x * share_of_a + y * (1 - share_of_a)):02x}" for x, y in zip(_rgb(a), _rgb(b)))


def resolve(map_cfg: dict, where: str = "map") -> dict:
    """The theme for one map: preset + overrides + data colours, all validated.

    Returns {"name", "basemap", "page": {...}, "colors": {...}, "panel_opacity"}."""
    name = v.one_of(map_cfg.get("theme", "dark"), tuple(THEMES), f"{where}.theme")
    preset = THEMES[name]

    page = dict(preset["page"])
    overrides = map_cfg.get("theme_colors") or {}
    if not isinstance(overrides, dict):
        raise v.ConfigError(f"{where}.theme_colors: expected a list of name: colour pairs")
    for key, value in overrides.items():
        if key not in page:
            raise v.ConfigError(f"{where}.theme_colors: unknown colour {key!r}; choose from {', '.join(page)}")
        page[key] = v.color(value, f"{where}.theme_colors.{key}")

    given = map_cfg.get("colors") or {}
    if not isinstance(given, dict):
        raise v.ConfigError(f"{where}.colors: expected a list of name: colour pairs")
    unknown = [k for k in given if k not in DATA_KEYS]
    if unknown:
        raise v.ConfigError(f"{where}.colors: unknown colour(s) {unknown}; choose from {', '.join(DATA_KEYS)}")
    data = dict(preset["data"])
    for key in ("accent", "native", "introduced", "other", "ring"):
        if key in given:
            data[key] = v.color(given[key], f"{where}.colors.{key}")
    data.setdefault("native", data["accent"])
    data.setdefault("ring", data["accent"])
    if "basis" in given:
        data["basis"] = v.colors(given["basis"], f"{where}.colors.basis")

    # colours worked out from the others
    accent = data["accent"]
    dark, light = sorted((page["ink"], page["panel"]), key=_luminance)
    page["accent_text"] = accent if contrast(accent, page["panel"]) >= MIN_TEXT_CONTRAST else page["ink"]
    page["on_accent"] = max((dark, light, "#141518", "#ffffff"), key=lambda c: contrast(c, accent))
    page["selected_row"] = mix(accent, page["panel"], 0.10)
    return {"name": name, "basemap": preset["basemap"], "page": page, "colors": data,
            "panel_opacity": preset["panel_opacity"]}


def css(theme: dict) -> str:
    """The theme as CSS variables for the page's :root (values are validated colours only)."""
    p = theme["page"]
    r, g, b = _rgb(p["panel"])
    pairs = {
        "--bg": p["bg"], "--panel": f"rgba({r},{g},{b},{theme['panel_opacity']})", "--ink": p["ink"],
        "--muted": p["muted"], "--line": p["line"], "--accent": theme["colors"]["accent"],
        "--accent-text": p["accent_text"], "--on-accent": p["on_accent"], "--button": p["button"],
        "--row-line": p["row_line"], "--hover": p["hover"], "--selected-row": p["selected_row"],
        "--tip": p["tip"], "--popup": p["popup"], "--error": p["error"],
    }
    return ":root { " + " ".join(f"{k}:{val};" for k, val in pairs.items()) + " }"


def contrast_notes(theme: dict, groups: list[dict] | None = None, extra: dict | None = None) -> list[dict]:
    """Colours that will be hard to see: points against the base map, the accent against the panel."""
    p, c = theme["page"], theme["colors"]
    notes = []
    points = {f"map.colors.{k}": c[k] for k in ("native", "introduced", "other", "ring")}
    points.update({f"map.colors.basis[{i}]": col for i, col in enumerate(c["basis"])})
    points.update({f"groups[{g['name']}].color": g["color"] for g in groups or []})
    points.update(extra or {})
    for where, col in points.items():
        ratio = contrast(col, p["map_bg"])
        if ratio < MIN_POINT_CONTRAST:
            notes.append({"where": where, "color": col, "against": f"{theme['name']} base map",
                          "contrast": round(ratio, 2),
                          "note": "hard to see on this background; choose a colour further from it"})
    ratio = contrast(c["accent"], p["panel"])
    if ratio < MIN_TEXT_CONTRAST:
        notes.append({"where": "map.colors.accent", "color": c["accent"], "against": f"{theme['name']} panel",
                      "contrast": round(ratio, 2),
                      "note": "too faint for text: the title, links and chart use the text colour instead"})
    return notes
