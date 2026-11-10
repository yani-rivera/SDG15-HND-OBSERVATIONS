"""Small checks for config values that end up in the page.

A config is plain text that people copy and share, and its values are written into
HTML, CSS and links. Each kind of value is checked against a strict shape here, so a
typo gives a clear message at build time and nothing unexpected reaches the page.
"""
import re
from urllib.parse import urlsplit

_HEX = re.compile(r"#[0-9a-fA-F]{6}")
_LOCALE = re.compile(r"[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*")
_COUNTRY = re.compile(r"[A-Z]{2}")
_HOST = re.compile(r"[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+(:\d{1,5})?")


class ConfigError(ValueError):
    """A config value that cannot be used; the message says where and why."""


def color(value, where: str) -> str:
    """A colour as #rrggbb (six hex digits)."""
    if not isinstance(value, str) or not _HEX.fullmatch(value):
        raise ConfigError(f"{where}: expected a colour like \"#f5b301\" (# and six hex digits), got {value!r}")
    return value.lower()


def colors(values, where: str, at_least: int = 1) -> list[str]:
    if not isinstance(values, (list, tuple)) or len(values) < at_least:
        raise ConfigError(f"{where}: expected a list of at least {at_least} colour(s)")
    return [color(v, f"{where}[{i}]") for i, v in enumerate(values)]


def number(value, where: str, minimum: float | None = None, maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{where}: expected a number, got {value!r}")
    if minimum is not None and value < minimum or maximum is not None and value > maximum:
        raise ConfigError(f"{where}: {value} is outside {minimum} to {maximum}")
    return value


def numbers(values, where: str, at_least: int = 0) -> list:
    if not isinstance(values, (list, tuple)) or len(values) < at_least:
        raise ConfigError(f"{where}: expected a list of at least {at_least} number(s)")
    return [number(v, f"{where}[{i}]") for i, v in enumerate(values)]


def text(value, where: str, max_len: int = 2000) -> str:
    if not isinstance(value, str):
        raise ConfigError(f"{where}: expected text, got {value!r}")
    if len(value) > max_len:
        raise ConfigError(f"{where}: longer than {max_len} characters")
    return value


def https_url(value, where: str) -> str:
    """A link the page may use: https only, with a host, no user:password part."""
    if not isinstance(value, str):
        raise ConfigError(f"{where}: expected an https:// address, got {value!r}")
    parts = urlsplit(value)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password \
            or any(c in value for c in " \"'<>\\`\n\r\t"):
        raise ConfigError(f"{where}: expected an https:// address, got {value!r}")
    return value


def host_of(url: str) -> str:
    """The origin a page security policy has to allow for this address, e.g. https://tiles.example.org"""
    parts = urlsplit(url)
    return f"https://{parts.netloc.lower()}"


def host(value, where: str) -> str:
    """A bare host name (optionally with a port) to allow in the page security policy."""
    if not isinstance(value, str) or not _HOST.fullmatch(value.lower()):
        raise ConfigError(f"{where}: expected a host name like \"tiles.example.org\", got {value!r}")
    return f"https://{value.lower()}"


def locale(value, where: str) -> str:
    if not isinstance(value, str) or not _LOCALE.fullmatch(value):
        raise ConfigError(f"{where}: expected a language tag like \"en-US\" or \"es-HN\", got {value!r}")
    return value


def country(value, where: str) -> str:
    if not isinstance(value, str) or not _COUNTRY.fullmatch(value):
        raise ConfigError(f"{where}: expected a two-letter country code in capitals like \"HN\", got {value!r}")
    return value


def bounds(value, where: str) -> list[list[float]]:
    """[[west, south], [east, north]] in degrees."""
    try:
        (w, s), (e, n) = value
    except (TypeError, ValueError):
        raise ConfigError(f"{where}: expected [[west, south], [east, north]] or \"auto\"") from None
    number(w, where, -180, 180), number(e, where, -180, 180)
    number(s, where, -90, 90), number(n, where, -90, 90)
    if not (w < e and s < n):
        raise ConfigError(f"{where}: west must be less than east and south less than north")
    return [[w, s], [e, n]]


def one_of(value, options, where: str):
    if value not in options:
        raise ConfigError(f"{where}: expected one of {', '.join(map(str, options))}; got {value!r}")
    return value
