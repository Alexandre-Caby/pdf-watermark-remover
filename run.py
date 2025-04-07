"""
Entry point for PDF Watermark Remover application.
"""

import os
import sys
import tkinter as tk

# Adjust Python's import path based on how we're running
if getattr(sys, 'frozen', False):
    if hasattr(sys, '_MEIPASS'):
        base_dir = sys._MEIPASS
    else:
        # Fallback to executable directory
        base_dir = os.path.dirname(sys.executable)
    
    # Add the base directory and module directories to path
    sys.path.insert(0, base_dir)
    sys.path.insert(0, os.path.join(base_dir, 'main'))
    sys.path.insert(0, os.path.join(base_dir, 'mechanisms'))
    sys.path.insert(0, os.path.join(base_dir, 'ui'))
    
    # Import with the path already set up
    from main.remove_watermark import WatermarkRemoverApp
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, base_dir)
    from main.remove_watermark import WatermarkRemoverApp

if __name__ == "__main__":
    root = tk.Tk()
    # Set application icon
    try:
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, "assets", "icons", "icon_remove_watermark.ico")
        else:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    "assets", "icons", "icon_remove_watermark.ico")
        root.iconbitmap(icon_path)
    except Exception as e:
        print(f"Could not load icon: {e}")
        # Continue without the icon
    
    app = WatermarkRemoverApp(root)
    root.mainloop()