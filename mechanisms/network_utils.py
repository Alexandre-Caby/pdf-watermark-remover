"""
Network utilities for enterprise-resilient HTTPS fetching.

Provides a robust HTTP(S) fetching layer that handles:
- System proxy auto-detection (Windows IE/Edge settings, env vars)
- SSL flexibility for corporate SSL inspection
- Local caching with graceful degradation on network failure
- All GitHub API and raw content fetches go through this module

All functions are designed to **never raise** — they return cached
or default values on failure, ensuring the app always starts.
"""

import json
import logging
import os
import ssl
import sys
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

logger = logging.getLogger("watermark_app.network")

# Trusted GitHub domains (only these are allowed for relaxed SSL fallback)
_TRUSTED_DOMAINS = frozenset({
    "api.github.com",
    "raw.githubusercontent.com",
    "github.com",
    "objects.githubusercontent.com",
})

# Cache directory
_CACHE_DIR: Optional[str] = None


def _get_cache_dir() -> str:
    """Return the local cache directory, creating it if needed."""
    global _CACHE_DIR
    if _CACHE_DIR is None:
        home = os.path.expanduser("~")
        _CACHE_DIR = os.path.join(home, ".filigrane_cache")
        os.makedirs(_CACHE_DIR, exist_ok=True)
    return _CACHE_DIR


def _build_opener(
    ssl_context: Optional[ssl.SSLContext] = None,
) -> urllib.request.OpenerDirector:
    """Build a URL opener with system proxy support.

    Reads proxy settings from:
    1. Windows system proxy (IE/Edge registry settings)
    2. HTTP_PROXY / HTTPS_PROXY environment variables
    Both are handled automatically by ``urllib.request.getproxies()``.

    Args:
        ssl_context: Optional SSL context passed to
            :class:`urllib.request.HTTPSHandler` so every request made
            through this opener uses the given TLS settings.
    """
    handlers: list = [urllib.request.ProxyHandler(urllib.request.getproxies())]
    if ssl_context is not None:
        handlers.append(urllib.request.HTTPSHandler(context=ssl_context))
    return urllib.request.build_opener(*handlers)


def _get_ssl_context(url: str) -> ssl.SSLContext:
    """Return an SSL context appropriate for the given URL.

    First tries the default (strict) context. If we know the domain
    is trusted, we also prepare a fallback context for environments
    with corporate SSL inspection.
    """
    return ssl.create_default_context()


def _get_relaxed_ssl_context() -> ssl.SSLContext:
    """Return a relaxed SSL context for trusted GitHub domains only.

    WARNING: This disables certificate verification. Only used as a
    last-resort fallback for corporate networks with SSL inspection
    that inject untrusted CA certificates.
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _is_trusted_domain(url: str) -> bool:
    """Check if the URL targets a trusted GitHub domain."""
    try:
        from urllib.parse import urlparse
        hostname = urlparse(url).hostname or ""
        return hostname in _TRUSTED_DOMAINS
    except Exception:
        return False


def fetch_url(
    url: str,
    timeout: int = 5,
    headers: Optional[Dict[str, str]] = None,
) -> Optional[bytes]:
    """Fetch raw bytes from a URL with proxy + SSL resilience.

    Args:
        url: The HTTPS URL to fetch.
        timeout: Request timeout in seconds (default 5).
        headers: Optional extra HTTP headers.

    Returns:
        Response body as bytes, or None on any failure.
    """
    req_headers = {"User-Agent": "PDF-Watermark-Remover/1.0"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)

    # Attempt 1: strict SSL + system proxy
    try:
        ctx = _get_ssl_context(url)
        opener = _build_opener(ssl_context=ctx)
        with opener.open(req, timeout=timeout) as resp:
            return resp.read()
    except (urllib.error.URLError, ssl.SSLError, OSError) as exc:
        logger.debug("Fetch attempt 1 failed for %s: %s", url, exc)

    # Attempt 2: relaxed SSL (only for trusted GitHub domains)
    if _is_trusted_domain(url):
        try:
            ctx = _get_relaxed_ssl_context()
            logger.warning(
                "Retrying %s with relaxed SSL (corporate proxy suspected)", url
            )
            opener = _build_opener(ssl_context=ctx)
            with opener.open(req, timeout=timeout) as resp:
                return resp.read()
        except (urllib.error.URLError, ssl.SSLError, OSError) as exc:
            logger.debug("Fetch attempt 2 (relaxed SSL) failed for %s: %s", url, exc)

    return None


def fetch_json(
    url: str,
    cache_key: Optional[str] = None,
    default: Optional[Any] = None,
    timeout: int = 5,
) -> Any:
    """Fetch JSON from a URL with caching and fallback.

    On success, the result is cached locally under *cache_key*.
    On any failure, the cached value is returned. If no cache exists,
    *default* is returned. **Never raises.**

    Args:
        url: The HTTPS URL to fetch JSON from.
        cache_key: Filename for local cache (e.g., "admin_contact").
        default: Value returned when both fetch and cache fail.
        timeout: Request timeout in seconds.

    Returns:
        Parsed JSON (dict/list), cached value, or *default*.
    """
    data = fetch_url(url, timeout=timeout)

    if data is not None:
        try:
            result = json.loads(data.decode("utf-8"))
            # Cache the successful result
            if cache_key:
                _save_cache(cache_key, result)
            return result
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.warning("Invalid JSON from %s: %s", url, exc)

    # Fallback to cache
    if cache_key:
        cached = _load_cache(cache_key)
        if cached is not None:
            logger.info("Using cached data for %s", cache_key)
            return cached

    return default


def _save_cache(key: str, data: Any) -> None:
    """Persist JSON data to the cache directory."""
    try:
        path = os.path.join(_get_cache_dir(), f"{key}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        logger.debug("Could not write cache for %s: %s", key, exc)


def _load_cache(key: str) -> Optional[Any]:
    """Load JSON data from the cache directory."""
    try:
        path = os.path.join(_get_cache_dir(), f"{key}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        logger.debug("Could not read cache for %s: %s", key, exc)
    return None


def check_connectivity(github_repo: str = "Alexandre-Caby/pdf-watermark-remover") -> Dict[str, Any]:
    """Run a connectivity diagnostic against GitHub.

    Returns a dict with diagnostic info intended for display in the UI.
    """
    import urllib.parse

    results: Dict[str, Any] = {
        "status": "unknown",
        "proxy_detected": bool(urllib.request.getproxies()),
        "proxy_settings": urllib.request.getproxies(),
        "api_reachable": False,
        "raw_reachable": False,
        "error": None,
    }

    # Test GitHub API
    api_url = f"https://api.github.com/repos/{github_repo}"
    api_data = fetch_url(api_url, timeout=5)
    results["api_reachable"] = api_data is not None

    # Test raw content
    raw_url = f"https://raw.githubusercontent.com/{github_repo}/main/version.txt"
    raw_data = fetch_url(raw_url, timeout=5)
    results["raw_reachable"] = raw_data is not None

    if results["api_reachable"] and results["raw_reachable"]:
        results["status"] = "ok"
    elif results["api_reachable"] or results["raw_reachable"]:
        results["status"] = "partial"
    else:
        results["status"] = "unreachable"
        results["error"] = (
            "Impossible de joindre GitHub. Vérifiez votre connexion "
            "réseau ou contactez votre service informatique."
        )

    return results
