"""
Entry point for PDF Watermark Remover application.
Bootstraps logging, resolves frozen/source imports, and launches the main window.
"""

import os
import sys
import logging
import logging.handlers
import tkinter as tk
import traceback

import customtkinter as ctk


def _setup_logging() -> logging.Logger:
    """Configure application-wide logging with a rotating file handler."""
    if getattr(sys, 'frozen', False):
        log_dir = os.path.dirname(sys.executable)
    else:
        log_dir = os.path.dirname(os.path.abspath(__file__))

    log_path = os.path.join(log_dir, "watermark_app.log")
    logger = logging.getLogger("watermark_app")
    logger.setLevel(logging.DEBUG)

    try:
        handler = logging.handlers.RotatingFileHandler(
            log_path, maxBytes=1_048_576, backupCount=3, encoding="utf-8"
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(handler)
    except OSError:
        # If we cannot write to the log location, add a NullHandler so
        # logging calls don't raise. The app should still start.
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
            text="Consultez watermark_app.log pour plus de détails.",
        ).pack(pady=10)
        tk.Button(error_root, text="Quitter", command=error_root.destroy).pack(pady=20)
        error_root.mainloop()
    except Exception:
        pass  # Last resort — if even the error window fails