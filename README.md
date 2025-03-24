# PDF Watermark Remover

A desktop application for removing watermarks from PDF documents in a corporate environment.

## Features

- Remove diagonal watermarks (red text)
- Remove footer watermarks (blue text)
- Process individual files or entire folders
- Works with most standard PDF watermarks
- Secure activation system

## Requirements

- Windows 10 or later
- Python 3.8+ (if running from source)

## Installation

Download the latest executable from the [Releases](https://github.com/Alexandre-Caby/pdf-watermark-remover/releases) page.

## Usage

1. Launch the application
2. Choose between single file or folder processing
3. Select source file(s) and destination
4. Enter watermark parameters if needed
5. Click "Launch watermark removal"

## Building from Source

```bash
# Install dependencies
pip install -r requirements.txt

# Run from source
python remove_watermark.py

# Build executable with PyInstaller
pip install pyinstaller
pyinstaller --onefile --windowed --icon=icon_remove_watermark.ico remove_watermark.py
```
## License
Copyright © 2025 Alexandre Caby. All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution, modification, public display, or public performance of this software is strictly prohibited.
