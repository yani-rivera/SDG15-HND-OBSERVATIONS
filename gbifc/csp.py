"""The page's security policy (Content-Security-Policy), written into every built page.

It tells the browser exactly what the page may run and load:
  - scripts: only the page's own script (pinned by its SHA-256, so not even one character
    can differ) and the MapLibre file named in the template; nothing typed into a record
    by a third party can run, even if an escaping mistake slipped through;
  - connections: only the base map's host(s); images: those hosts and the page's own site;
  - nothing else: no plugins, no frames, no forms, no <base> tricks.

The MapLibre addresses are read from the template, so the policy and the page cannot drift.
"""
import base64
import hashlib
import re

_APP = re.compile(r'<script id="app">(.*?)</script>', re.S)
_LIB_JS = re.compile(r'<script src="(https://[^"]+)"')
_LIB_CSS = re.compile(r'<link href="(https://[^"]+)" rel="stylesheet"')


def script_hash(template: str) -> str:
    """'sha256-…' of the page's own script, exactly as the browser will see it."""
    found = _APP.findall(template)
    if len(found) != 1:
        raise ValueError("template: expected exactly one <script id=\"app\"> block")
    code = found[0]
    if re.search(r"__[A-Z_]+__", code):
        raise ValueError("template: the app script must not contain placeholders (its hash is fixed)")
    code = code.replace("\r\n", "\n").replace("\r", "\n")      # as the HTML parser normalises it
    return "sha256-" + base64.b64encode(hashlib.sha256(code.encode("utf-8")).digest()).decode()


def policy(template: str, hosts: list[str], data_images: bool = False) -> str:
    """The policy for a page built from `template` whose base map loads from `hosts`.

    `data_images`: the page embeds an image (the raster overlay) that the map library
    fetches from a data: address."""
    lib_js, lib_css = _LIB_JS.findall(template), _LIB_CSS.findall(template)
    if len(lib_js) != 1 or len(lib_css) != 1:
        raise ValueError("template: expected one external script and one external stylesheet (MapLibre)")
    allowed = " ".join(hosts)
    rules = [
        "default-src 'none'",
        f"script-src '{script_hash(template)}' {lib_js[0]}",
        f"style-src 'unsafe-inline' {lib_css[0]}",
        f"img-src 'self' data: blob: {allowed}",       # 'self': the browser's own favicon request
        f"connect-src {allowed}" + (" data:" if data_images else ""),
        "worker-src blob:",
        "child-src blob:",
        "base-uri 'none'",
        "form-action 'none'",
    ]
    return "; ".join(rules)
