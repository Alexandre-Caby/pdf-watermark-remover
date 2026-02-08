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

# Import modules
from mechanisms.watermark_processor import WatermarkProcessor
from mechanisms.activation_manager import ActivationManager
from ui.dialog_windows import DialogWindows
from ui.app_ui import AppUI
from ui.app_styles import AppStyles
from mechanisms import auto_updater

class WatermarkRemoverApp:
    """Main application class that wires together all modules."""

    def __init__(self, root: ctk.CTk) -> None:
        """Initialise modules, show legal dialogs, and validate activation."""
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
        self.activation_manager = ActivationManager(root)
        self.dialog_windows = DialogWindows(root)
        self.ui = AppUI(root, self.watermark_processor)
        
        # Set callbacks
        self.ui.set_show_help_callback(self.dialog_windows.show_help)
        self.ui.set_show_about_callback(self.show_about)
        self.ui.set_check_updates_callback(self.check_for_updates)
        self.dialog_windows.set_update_callback(self.check_for_updates)
        
        # Create UI components
        self.ui.create_ui()
        
        # Check terms and activation before proceeding
        if not self.dialog_windows.show_terms_and_conditions():
            sys.exit(0)
            
        if not self.activation_manager.validate_activation():
            sys.exit(0)
        
        # Schedule an update check after application starts (2 seconds delay)
        self.root.after(2000, lambda: self.check_for_updates(silent=True))
    
    def check_for_updates(self, silent=False):
        """Check if a newer version is available and offer to update."""
        updater = auto_updater.AutoUpdater(self.root)
        return updater.check_for_updates(silent=silent)
    
    def show_about(self):
        """Display the about dialog with version info."""
        self.dialog_windows.show_about()