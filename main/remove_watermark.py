"""
Main application orchestrator for Suppression de Filigrane PDF.

Copyright © 2025 Alexandre Caby.
Licensed under the GNU General Public License v3.0.
See LICENSE for details.
"""

import logging
import os
import sys
import tkinter as tk

import customtkinter as ctk

logger = logging.getLogger("watermark_app.main")

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from mechanisms.watermark_processor import WatermarkProcessor
from ui.dialog_windows import DialogWindows
from ui.app_ui import AppUI
from ui.app_styles import AppStyles

class WatermarkRemoverApp:
    """Main application class that wires together all modules."""

    def __init__(self, root: ctk.CTk) -> None:
        """Initialise modules, show legal dialogs, and launch the app."""
        self.root = root

        # Window title with version
        try:
            version_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "..", "version.txt"
            )
            if os.path.exists(version_file):
                with open(version_file, "r") as f:
                    current_version = f.read().strip()
                    self.root.title(f"Suppression de Filigrane PDF - v{current_version}")
            else:
                self.root.title("Suppression de Filigrane PDF")
        except (OSError, ValueError) as exc:
            logger.warning("Could not read version.txt: %s", exc)
            self.root.title("Suppression de Filigrane PDF")

        self.root.geometry("650x600")
        
        # Initialize modules
        self.styles = AppStyles(root)
        self.watermark_processor = WatermarkProcessor()
        self.dialog_windows = DialogWindows(root)
        self.ui = AppUI(root, self.watermark_processor)
        
        # Set callbacks (Uniquement l'aide et le "À propos")
        self.ui.set_show_help_callback(self.dialog_windows.show_help)
        self.ui.set_show_about_callback(self.show_about)
        
        # Create UI components
        self.ui.create_ui()
        
        # Check terms before proceeding
        if not self.dialog_windows.show_terms_and_conditions():
            sys.exit(0)
    
    def show_about(self):
        """Display the about dialog with version info."""
        self.dialog_windows.show_about()