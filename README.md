# PDF Watermark Remover

A desktop application for removing watermarks from PDF documents in a corporate environment.

## Features

- Remove diagonal watermarks (red text)
- Remove footer watermarks (blue text)
- Process individual files or entire folders
- **Modular architecture** with separation of UI, core mechanisms, and main application logic
- External legal documents loaded at runtime (EULA, Terms of Service, etc.)
- Obfuscated, single-file executable build via PyArmor + PyInstaller
- Release integrity verified with a SHA-256 checksum published alongside each build

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

# Run from source
python run.py

# To build an executable:
pip install pyinstaller pyarmor
pyarmor gen --recursive --output dist_obf run.py main/ mechanisms/ ui/
pyinstaller --onefile --windowed ^
    --icon=assets/icons/icon_remove_watermark.ico ^
    --add-data "version.txt;." ^
    --add-data "assets/*;assets" ^
    dist_obf/run.py
```

## Project Structure

```
pdf-watermark-remover/
├── run.py                    # Application entry point
├── version.txt
├── requirements.txt
├── CHANGELOG.md
├── LICENSE                   # GPL-3.0
├── .github/
│   └── workflows/
│       └── build.yml         # CI/CD: obfuscation, PyInstaller build, SHA-256 checksum
├── assets/
│   ├── icons/
│   └── legal/                # EULA, Terms of Service, Copyright Notice, etc.
├── main/
│   └── remove_watermark.py   # Main application orchestrator
├── mechanisms/
│   └── watermark_processor.py# PDF watermark removal engine
└── ui/
    ├── app_styles.py         # Theme and style definitions
    ├── app_ui.py             # Main Tkinter GUI
    └── dialog_windows.py     # EULA, Help, and About dialogs
```

## License

Copyright (C) 2025 Alexandre Caby.

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 3.

See the [LICENSE](LICENSE) file for full details.