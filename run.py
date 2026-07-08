"""
Entry point for PDF Watermark Remover application.
Bootstraps logging, resolves frozen/source imports, and launches the main window.
"""

import os
import sys
import logging
import tkinter as tk
import traceback

import customtkinter as ctk


def _setup_logging() -> logging.Logger:
    """Configure the application logger without writing anything to disk.

    Modules still call logger.info/warning/error as before; a NullHandler
    simply discards those records so no watermark_app.log file is ever
    created next to the executable.
    """
    logger = logging.getLogger("watermark_app")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.NullHandler())
    return logger


logger = _setup_logging()

try:
    logger.info("Starting application")
    logger.info("Frozen: %s", getattr(sys, 'frozen', False))
    if getattr(sys, 'frozen', False):
        logger.info("MEIPASS: %s", getattr(sys, '_MEIPASS', 'Not available'))
    logger.debug("sys.path: %s", sys.path)

    # Always use package import — PyInstaller preserves package structure
    # when building from the obfuscated dist_obf/ directory.
    logger.info("Importing main.remove_watermark")
    from main.remove_watermark import WatermarkRemoverApp

    if __name__ == "__main__":
        root = ctk.CTk()

        # Set application icon
        try:
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(
                    sys._MEIPASS, "assets", "icons", "icon_remove_watermark.ico"
                )
                if not os.path.exists(icon_path):
                    icon_path = os.path.join(sys._MEIPASS, "icon_remove_watermark.ico")
            else:
                icon_path = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "assets", "icons", "icon_remove_watermark.ico",
                )

            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
                logger.info("Loaded icon from: %s", icon_path)
            else:
                logger.warning("Icon not found at: %s", icon_path)
        except Exception as exc:
            logger.warning("Could not load icon: %s", exc)

        # Create and run the app
        app = WatermarkRemoverApp(root)
        root.mainloop()

except Exception as exc:
    logger.critical("Critical error: %s", exc, exc_info=True)

    # Show error dialog as a last resort
    try:
        error_root = tk.Tk()
        error_root.title("Erreur au démarrage")
        error_root.geometry("500x300")
        tk.Label(
            error_root, text="Erreur au démarrage", font=("Arial", 16, "bold")
        ).pack(pady=20)
        tk.Label(error_root, text=str(exc), wraplength=450).pack(pady=10)
        tk.Label(
            error_root,
            text="Si le problème persiste, contactez le support technique.",
            wraplength=450,
        ).pack(pady=10)
        tk.Button(error_root, text="Quitter", command=error_root.destroy).pack(pady=20)
        error_root.mainloop()
    except Exception:
        pass  # Last resort — if even the error window fails