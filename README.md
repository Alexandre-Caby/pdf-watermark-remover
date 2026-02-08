# PDF Watermark Remover

A desktop application for removing watermarks from PDF documents in a corporate environment.

## Features

- Remove diagonal watermarks (red text)
- Remove footer watermarks (blue text)
- Process individual files or entire folders
- Secure activation system with per-key revocation
- Automatic updates with SHA-256 integrity verification
- Internationalization support (French / English)
- **Modular architecture** with separation of UI, core mechanisms, and main application logic
- External legal documents loaded at runtime (EULA, Terms of Service, etc.)
- Enhanced build process with obfuscation and updated GitHub workflow

## Requirements

- Windows 10 or later
- Python 3.9+ (if running from source)

## Installation

Download the latest executable from the [Releases](https://github.com/Alexandre-Caby/pdf-watermark-remover/releases) page.

The SHA-256 checksum is listed in the release notes — verify it after download to ensure integrity.

## Usage

1. Launch the application.
2. Choose between single file or folder processing.
3. Select source file(s) and destination.
4. Enter watermark parameters if needed.
5. Click "Launch watermark removal".

## Building from Source

```bash
# Install dependencies
pip install -r requirements.txt

# Run from source (requires a .env file with ACTIVATION_SALT and APP_SECRET_KEY)
python run.py

# To build an executable:
pip install pyinstaller pyarmor
pyarmor obfuscate --recursive --output dist_obf run.py
pyinstaller --onefile --windowed ^
    --icon=assets/icons/icon_remove_watermark.ico ^
    --add-data "version.txt;." ^
    --add-data "locales;locales" ^
    --add-data "admin_contact.json;." ^
    --add-data "revocation_list.json;." ^
    --add-data "assets/*;assets" ^
    dist_obf/run.py
```

## Project Structure

```
pdf-watermark-remover/
├── run.py                    # Application entry point
├── version.txt
├── admin_contact.json        # Remote-configurable admin contact info
├── revocation_list.json      # Revoked activation codes (synced from admin tool)
├── requirements.txt
├── CHANGELOG.md
├── LICENSE                   # GPL-3.0
├── .github/
│   └── workflows/
│       └── build.yml         # CI/CD: obfuscation, XOR secrets, SHA-256 checksum
├── assets/
│   ├── icons/
│   └── legal/                # EULA, Terms of Service, Copyright Notice, etc.
├── locales/
│   ├── fr.json               # French UI strings (default)
│   └── en.json               # English UI strings
├── main/
│   └── remove_watermark.py   # Main application orchestrator
├── mechanisms/
│   ├── _secrets.py           # Secret provider (env-var dev / XOR-obfuscated prod)
│   ├── activation_manager.py # Activation lifecycle & HMAC validation
│   ├── auto_updater.py       # GitHub release checker with SHA-256 verification
│   ├── i18n.py               # Internationalization helper
│   ├── machine_id.py         # Hardware fingerprint generator
│   ├── network_utils.py      # Enterprise-resilient HTTPS (proxy, SSL fallback, cache)
│   ├── secure_activation.py  # AES-256-GCM encryption of activation data
│   └── watermark_processor.py# PDF watermark removal engine
└── ui/
    ├── app_styles.py         # Theme and style definitions
    ├── app_ui.py             # Main Tkinter GUI
    └── dialog_windows.py     # EULA, Help, and About dialogs
```

## Administration Tool

A separate **admin activation tool** (`Watermark_project_activation/`) allows a trusted administrator to:

- Generate HMAC-SHA256 activation codes for end users
- Track all issued keys in a local SQLite database
- Revoke / reactivate individual keys
- Export a `revocation_list.json` for the user app to check at startup

See `Watermark_project_activation/BUILD.md` for build instructions.

## License

Copyright (C) 2025 Alexandre Caby.

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 3.

See the [LICENSE](LICENSE) file for full details.
