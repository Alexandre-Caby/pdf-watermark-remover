"""
Internationalization (i18n) helper.

Loads translation strings from JSON locale files and provides a
simple ``t(key, **kwargs)`` interface.  Fall-through behaviour: if
a key is missing in the active locale, French is used as the
ultimate fallback (since the UI was originally written in French).

Usage::

    from mechanisms.i18n import t, set_locale

    set_locale("en")  # switch to English
    label.configure(text=t("start_removal_button"))
    msg = t("activation_success_message", date="2026-01-15")

Copyright (C) 2025 Alexandre Caby
SPDX-License-Identifier: GPL-3.0-or-later
"""

import json
import logging
import os
from typing import Dict, Optional

logger = logging.getLogger("watermark_app.i18n")

_LOCALES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")

# Module-level state
_current_locale: str = "fr"
_strings: Dict[str, str] = {}
_fallback_strings: Dict[str, str] = {}


def _load_locale_file(locale_code: str) -> Dict[str, str]:
    """Load a locale JSON file and return its key-value map."""
    path = os.path.join(_LOCALES_DIR, f"{locale_code}.json")
    if not os.path.isfile(path):
        logger.warning("Locale file not found: %s", path)
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("Loaded locale '%s' (%d keys)", locale_code, len(data))
        return data
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to load locale '%s': %s", locale_code, exc)
        return {}


def set_locale(locale_code: str) -> None:
    """Switch the active locale.

    Args:
        locale_code: ISO 639-1 code, e.g. ``"fr"`` or ``"en"``.
    """
    global _current_locale, _strings, _fallback_strings

    _current_locale = locale_code
    _strings = _load_locale_file(locale_code)

    # Always keep French as fallback
    if locale_code != "fr":
        _fallback_strings = _load_locale_file("fr")
    else:
        _fallback_strings = _strings


def get_locale() -> str:
    """Return the current locale code."""
    return _current_locale


def get_available_locales():
    """Return a list of available locale codes."""
    if not os.path.isdir(_LOCALES_DIR):
        return ["fr"]
    return sorted(
        os.path.splitext(f)[0]
        for f in os.listdir(_LOCALES_DIR)
        if f.endswith(".json")
    )


def t(key: str, **kwargs) -> str:
    """Translate a key, with optional format arguments.

    Falls back to the French string, then to the raw key name
    (so the UI never shows an empty string).

    Args:
        key: The translation key (e.g. ``"start_removal_button"``).
        **kwargs: Named placeholders to substitute via ``str.format()``.

    Returns:
        The translated and formatted string.
    """
    value: Optional[str] = _strings.get(key) or _fallback_strings.get(key)
    if value is None:
        logger.debug("Missing translation key: '%s'", key)
        return key  # Last resort: return the key itself

    if kwargs:
        try:
            value = value.format(**kwargs)
        except (KeyError, IndexError) as exc:
            logger.warning("Format error for key '%s': %s", key, exc)
    return value


# Auto-load French on import so the app works even if set_locale()
# is never called explicitly.
set_locale("fr")
