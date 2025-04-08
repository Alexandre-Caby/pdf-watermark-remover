"""
Entry point for PDF Watermark Remover application.
"""

import os
import sys
import tkinter as tk

try:
    # Import differently based on whether we're frozen or not
    if getattr(sys, 'frozen', False):
        from remove_watermark import WatermarkRemoverApp
    else:
        # When running from source, use package import
        from main.remove_watermark import WatermarkRemoverApp

    if __name__ == "__main__":
        root = tk.Tk()
        
        # Set application icon
        try:
            if getattr(sys, 'frozen', False):
                # Chercher l'icône dans différents emplacements possibles
                possible_icon_paths = [
                    os.path.join(sys._MEIPASS, "assets", "icons", "icon_remove_watermark.ico"),
                    os.path.join(sys._MEIPASS, "icon_remove_watermark.ico"),
                    os.path.join(os.path.dirname(sys.executable), "assets", "icons", "icon_remove_watermark.ico"),
                    os.path.join(os.path.dirname(sys.executable), "icon_remove_watermark.ico")
                ]
                
                icon_found = False
                for icon_path in possible_icon_paths:
                    if os.path.exists(icon_path):
                        root.iconbitmap(icon_path)
                        icon_found = True
                        break
            else:
                # When running from source
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    "assets", "icons", "icon_remove_watermark.ico")
                if os.path.exists(icon_path):
                    root.iconbitmap(icon_path)
        except Exception:
            # Continue without icon
            pass
        
        # Create and run the app
        app = WatermarkRemoverApp(root)
        root.mainloop()
except Exception:
    pass
