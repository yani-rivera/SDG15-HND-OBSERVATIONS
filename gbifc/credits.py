"""Who made the map and under which licences: the config's `credits:` section.

One place to write down authorship, the licence of the records, the licence of the map
itself, thanks and notes. It is shown under Sources on the page and copied into
provenance.json, so every build documents its own credits.
"""
from html import escape

from . import validate as v

FIELDS = ("author", "author_url", "records_licence", "map_licence", "acknowledgements", "notes")
# licences that get a link to their text; anything else is shown as written
LICENCES = {
    "CC0 1.0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC BY-NC 4.0": "https://creativecommons.org/licenses/by-nc/4.0/",
    "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "CC BY-NC-SA 4.0": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
    "ODbL 1.0": "https://opendatacommons.org/licenses/odbl/1-0/",
}
_LINK = 'target="_blank" rel="noopener noreferrer"'


def resolve(given: dict | None, where: str = "credits") -> dict:
    """The section with every value checked; fields left out are None."""
    given = given or {}
    if not isinstance(given, dict):
        raise v.ConfigError(f"{where}: expected fields such as author and records_licence")
    unknown = [k for k in given if k not in FIELDS]
    if unknown:
        raise v.ConfigError(f"{where}: unknown field(s) {unknown}; choose from {', '.join(FIELDS)}")
    out = {k: (v.text(given[k], f"{where}.{k}", 600) if given.get(k) else None) for k in FIELDS}
    if out["author_url"]:
        out["author_url"] = v.https_url(out["author_url"], f"{where}.author_url")
    return out


def _licence(name: str) -> str:
    url = LICENCES.get(name.strip())
    return f'<a href="{url}" {_LINK}>{escape(name)}</a>' if url else escape(name)


def html_items(c: dict, labels: dict) -> list[str]:
    """Lines for the page's Sources list (escaped; links are https, checked above or built in)."""
    items = []
    if c["author"]:
        who = f'<a href="{escape(c["author_url"])}" {_LINK}>{escape(c["author"])}</a>' if c["author_url"] else escape(c["author"])
        items.append(f"<b>{escape(labels['credit_author'])}</b> {who}")
    licences = [f"{escape(labels[label])} {_licence(c[key])}"
                for key, label in (("records_licence", "credit_records_licence"), ("map_licence", "credit_map_licence")) if c[key]]
    if licences:
        items.append(f"<b>{escape(labels['credit_licences'])}</b> " + "; ".join(licences))
    if c["acknowledgements"]:
        items.append(f"<b>{escape(labels['credit_thanks'])}</b> {escape(c['acknowledgements'])}")
    if c["notes"]:
        items.append(escape(c["notes"]))
    return items
