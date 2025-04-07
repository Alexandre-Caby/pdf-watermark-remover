# Changelog

All notable changes to the PDF Watermark Remover will be documented in this file.

## [1.1.0] - 2025-04-07

### Major Code Restructuring
- Reorganized code into a modular architecture:
  - Separated UI components into `ui/`
  - Core mechanisms moved to `mechanisms/`
  - Main application logic now resides in `main/`
  - New entry point (`run.py`) created for better organization
- External legal documents now stored in `assets/legal` and loaded dynamically by the UI

### Build System Improvements
- Updated GitHub workflow (`.github/workflows/build.yml`) to support the new folder structure
- Implemented recursive obfuscation with PyArmor for the entire project
- Enhanced error checking and tagging during the build process

### Documentation and UI Enhancements
- Updated README to reflect new architecture and build process
- Legal content, including EULA and other documents, is now loaded from external files, reducing hardcoded text in the UI
- Minor UI tweaks for improved readability

## [1.0.4] - 2025-04-07

### Key Activation Improvements
- Improved saving of the license key in local storage
- Security improvements including environment variable handling

## [1.0.3] - 2025-04-06

### Fix Bugs
- Fixed the launch of the app standalone on Windows

## [1.0.2] - 2025-04-03

### Fix Bugs
- Fixed an issue with application launch during release usage

## [1.0.1] - 2025-04-03

### Security Improvements
- Use constant-time comparison
- Strict SSL certificate verification
- Enhanced handling of environment variables

## [1.0.0] - 2025-03-25

### Added
- Initial release with support for removing red diagonal and blue footer watermarks
- Batch processing for multiple PDF files
- License activation system