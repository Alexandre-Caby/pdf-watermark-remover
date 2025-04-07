"""
Entry point for PDF Watermark Remover application.
"""

import os
import sys
import tkinter as tk

if getattr(sys, 'frozen', False):
    sys.path.insert(0, sys._MEIPASS)
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the main application
from main.remove_watermark import WatermarkRemoverApp

if __name__ == "__main__":
    root = tk.Tk()
    # Set application icon
    try:
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                "assets", "icons", "icon_remove_watermark.ico")
        root.iconbitmap(icon_path)
    except:
        pass  # Ignore if icon can't be loaded
    
    app = WatermarkRemoverApp(root)
    root.mainloop()