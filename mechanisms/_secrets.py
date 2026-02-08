"""
Secrets module — runtime provider.

In **development** this file reads from environment variables (loaded
via ``python-dotenv``).  During CI/CD the build script replaces this
entire file with one that contains XOR-obfuscated values, which are
then further protected by PyArmor obfuscation.

Never commit real secret values to this file.

Copyright (C) 2025 Alexandre Caby
SPDX-License-Identifier: GPL-3.0-or-later
"""

import os


def _xor_decode(data: bytes, key: bytes) -> str:
    """XOR-decode *data* with *key* (repeating) and return UTF-8 string."""
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data)).decode("utf-8")


# ── CI/CD will overwrite the two functions below ──────────

def get_app_secret_key() -> str:
    """Return the APP_SECRET_KEY value."""
    return os.environ.get("APP_SECRET_KEY", "")


def get_activation_salt() -> str:
    """Return the ACTIVATION_SALT value."""
    return os.environ.get("ACTIVATION_SALT", "")
