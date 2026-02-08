"""
Machine identification module.

Generates a stable, harder-to-spoof hardware fingerprint by combining
multiple identifiers (MAC address + Windows Machine GUID).  Falls back
gracefully on non-Windows platforms or when registry access fails.

For backward compatibility with existing activation files that used the
old ``str(uuid.getnode())`` format, :func:`get_legacy_machine_id` is
also provided.
"""

import hashlib
import logging
import uuid
from typing import Optional

logger = logging.getLogger("watermark_app.machine_id")


def _get_windows_machine_guid() -> Optional[str]:
    """Read the Windows MachineGuid from the registry.

    Returns:
        The MachineGuid string, or None if unavailable.
    """
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
        )
        value, _ = winreg.QueryValueEx(key, "MachineGuid")
        winreg.CloseKey(key)
        return str(value)
    except Exception as exc:
        logger.debug("Could not read Windows MachineGuid: %s", exc)
        return None


def get_machine_id() -> str:
    """Generate a stable machine fingerprint.

    Combines the MAC address with the Windows Machine GUID (when
    available) and returns a SHA-256 hex digest truncated to 16
    characters so it stays user-friendly.

    Returns:
        A 16-character hex string identifying this machine.
    """
    mac = str(uuid.getnode())
    win_guid = _get_windows_machine_guid() or ""

    raw = f"{mac}|{win_guid}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def get_legacy_machine_id() -> str:
    """Return the old-format machine ID for backward compatibility.

    The previous version used ``str(uuid.getnode())`` directly.
    """
    return str(uuid.getnode())
