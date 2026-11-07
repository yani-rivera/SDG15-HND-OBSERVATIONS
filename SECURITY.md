# Security

## Reporting

If you find a security problem in this code or in a page it builds, please open a private report
through GitHub (**Security → Report a vulnerability**) rather than a public issue.

## What the code does to stay safe

The builder takes text from third-party GBIF records (place names, collectors, links) and puts it
into a public web page, so it treats that text as untrusted:

- **Escaping:** every record field shown on the page is HTML-escaped; data embedded in the page
  has `<` escaped, so a record cannot close the `<script>` tag.
- **Links:** a record's "original" link is kept only if it starts with `http://` or `https://`
  (checked when building and again in the page), so `javascript:` links cannot get in. GBIF ids
  are URL-encoded. External links open with `rel="noopener"`.
- **Outside code:** MapLibre 4.7.1 is loaded from unpkg with Subresource Integrity hashes; the
  browser refuses the file if it changes. When upgrading MapLibre, update both hashes in
  `gbifc/map_template.html`.
- **Config:** YAML is read with `yaml.safe_load`; no `eval`, `exec` or shell calls.
- **No secrets:** the base map (OpenFreeMap) needs no API key; never put keys or tokens in configs.
- **No data in the repository:** `data/` and `outputs/` are ignored by Git.

## Keep in mind

- `provenance.json` (published with each page) records the input paths as written in the config:
  use relative paths, not paths with your user name.
- Pages need MapLibre and the OpenFreeMap base map from the internet; if either is unavailable,
  the map does not draw, but no other code is loaded.
