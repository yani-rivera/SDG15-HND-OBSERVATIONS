# Security

## Reporting

If you find a security problem in this code or in a page it builds, please open a private report
through GitHub (**Security → Report a vulnerability**) rather than a public issue.

## What the code does to stay safe

The builder takes text from third-party GBIF records (place names, collectors, links) and from a
config that people copy and share, and puts both into a public web page. It treats both as
untrusted.

- **Page security policy:** every built page carries a Content-Security-Policy. The browser runs
  only the page's own script (pinned by its SHA-256) and the pinned MapLibre file, connects only
  to the base map's host(s), and refuses everything else: other scripts, inline event handlers,
  `eval`, frames, forms and `<base>`. If an escaping mistake ever slipped through, injected code
  would still not run. `gbifc/csp.py` builds the policy; the allowed hosts are recorded in
  `provenance.json`.
- **Escaping:** every record field and every config text shown on the page is HTML-escaped; data
  embedded in the page has `<` escaped, so a record cannot close its `<script>` block.
- **Config values are checked** before anything is written (`gbifc/validate.py`): colours must be
  `#rrggbb`, numbers must be numbers, links and the base map must be `https://`, hosts must be
  plain host names, labels may only use the `{words}` their default uses. A value that fails is
  reported by name and nothing is built.
- **Links:** a record's "original" link is kept only if it starts with `http://` or `https://`
  and is of a sane length (checked when building and again in the page), so `javascript:` and
  `data:` links cannot get in. Record ids are URL-encoded, and a `source.record_link` of your own
  must be `https://`. External links open with
  `rel="noopener noreferrer"`.
- **Base map credit:** the page writes the credit itself, as plain text and `https://` links from
  the config. MapLibre's own attribution control is switched off, because MapLibre 4 puts the
  base map provider's HTML into the page unchecked (see below).
- **Outside code:** MapLibre 4.7.1 is loaded from unpkg with Subresource Integrity hashes; the
  browser refuses the file if it changes. When upgrading MapLibre, update both hashes in
  `gbifc/map_template.html`.
- **Config:** YAML is read with `yaml.safe_load`; no `eval`, `exec` or shell calls.
- **No secrets:** the base map (OpenFreeMap) needs no API key; never put keys or tokens in configs.
- **No data in the repository:** `data/` and `outputs/` are ignored by Git.
- **No local paths published:** `provenance.json` keeps relative paths as written; of an absolute
  or home (`~`) path it keeps only the file name, so a user name or folder layout is not published.

## Known advisory: MapLibre GL JS (GHSA-jrc7-96c5-q579)

MapLibre GL JS up to 6.4.0 can let HTML in a tile source's attribution run script in the page
(fixed in 6.4.1, hardened further up to 6.12.0). Version 4.7.1, used here, has no attribution
sanitizer at all. Pages built with gbif_companion 0.4.1 or earlier show the base map provider's
attribution through MapLibre and are exposed if that provider (or its host) is ever compromised.

From 0.5.0 the pages are not exposed: MapLibre's attribution control is off, so that code never
receives the provider's HTML, and the page security policy blocks injected script as a second
barrier. **Rebuild and republish each map with 0.5.0 or later to apply this.**

MapLibre itself stays at 4.7.1 for now: versions 6 and later are loaded differently (ES modules,
a separate worker file) and need their own tested release. Tools that only compare version
numbers will keep flagging 4.7.1 until then.

## Keep in mind

- Python packages: `requirements.txt` asks for Pillow 13.0.0 or later, which fixes the advisories
  open against earlier versions. Run `pip install -U -r requirements.txt` now and then.
- A base map of your own (`map.basemap`) is trusted to draw the map, not to run code: list any
  extra hosts it loads from in `map.basemap_hosts`, or the page will refuse them and say so.
- Pages need MapLibre and the base map from the internet; if either is unavailable, the map does
  not draw, but no other code is loaded.
