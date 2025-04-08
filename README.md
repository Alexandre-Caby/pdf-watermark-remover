# PDF Watermark Remover

A desktop application for removing watermarks from PDF documents in a corporate environment.

## Features

- Remove diagonal watermarks (red text)
- Remove footer watermarks (blue text)
- Process individual files or entire folders
- Secure activation system
- **Modular architecture** with separation of UI, core mechanisms, and main application logic
- External legal documents loaded at runtime (EULA, Terms of Service, etc.)
- Enhanced build process with obfuscation and updated GitHub workflow

## Requirements

- Windows 10 or later
- Python 3.8+ (if running from source)

## Installation

Download the latest executable from the [Releases](https://github.com/Alexandre-Caby/pdf-watermark-remover/releases) page.

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

# Run from source using the new entry point
python run.py

# To build an executable with PyInstaller using the new structure:
# Make sure you have Python 3.9+ for best compatibility with the build scripts.
pip install pyinstaller
pyarmor obfuscate --recursive --output dist_obf run.py
pyinstaller --onefile --windowed --icon=assets/icons/icon_remove_watermark.ico --add-data "version.txt;." --add-data ".env;." dist_obf/run.py
```

## Project Structure

```
pdf-watermark-remover/
│
├── .gitignore
├── CHANGELOG.md
├── LICENSE
├── README.md
├── requirements.txt
├── run.py                <-- New entry point
├── version.txt
├── .github/
│   └── workflows/
│       └── build.yml    <-- Updated build script with obfuscation and tagging support
├── assets/
│   ├── icons/
│   │   └── icon_remove_watermark.ico
│   └── legal/           <-- External legal documents (EULA.md, Terms_of_Service.md, etc.)
├── main/
│   └── remove_watermark.py
├── mechanisms/
│   ├── activation_manager.py
│   ├── auto_updater.py
│   ├── secure_activation.py
│   └── watermark_processor.py
└── ui/
    ├── app_styles.py
    ├── app_ui.py
    └── dialog_windows.py
```

## License

© 2025 Alexandre Caby. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution, modification, public display, or public performance of this software is strictly prohibited.
