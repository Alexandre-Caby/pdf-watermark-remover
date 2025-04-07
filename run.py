"""
Entry point for PDF Watermark Remover application.
"""

import os
import sys
import tkinter as tk
import traceback

# Enable debugging and create a simple log file
def log_message(msg):
    """Log a message to a file for debugging PyInstaller issues"""
    try:
        log_path = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), 
                              "watermark_error.log")
        with open(log_path, "a") as f:
            f.write(f"{msg}\n")
    except:
        pass  # Silently fail if logging doesn't work

try:
    log_message(f"Starting application")
    log_message(f"Frozen: {getattr(sys, 'frozen', False)}")
    if getattr(sys, 'frozen', False):
        log_message(f"MEIPASS: {sys._MEIPASS if hasattr(sys, '_MEIPASS') else 'Not available'}")
    log_message(f"sys.path: {sys.path}")
    
    # Import differently based on whether we're frozen or not
    if getattr(sys, 'frozen', False):
        # When running as frozen executable, use direct import
        # This works because all .py files are copied to the same directory
        log_message("Using direct import (frozen app)")
        from remove_watermark import WatermarkRemoverApp
    else:
        # When running from source, use package import
        log_message("Using package import (source code)")
        from main.remove_watermark import WatermarkRemoverApp

    if __name__ == "__main__":
        root = tk.Tk()
        
        # Set application icon
        try:
            if getattr(sys, 'frozen', False):
                # When frozen, look for icon in the root of MEIPASS or in assets folder
                icon_path = os.path.join(sys._MEIPASS, "assets", "icons", "icon_remove_watermark.ico")
                if not os.path.exists(icon_path):
                    # Try alternate location
                    icon_path = os.path.join(sys._MEIPASS, "icon_remove_watermark.ico")
            else:
                # When running from source
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                      "assets", "icons", "icon_remove_watermark.ico")
            
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
                log_message(f"Loaded icon from: {icon_path}")
            else:
                log_message(f"Icon not found at: {icon_path}")
        except Exception as e:
            log_message(f"Could not load icon: {e}")
            # Continue without icon
        
        # Create and run the app
        app = WatermarkRemoverApp(root)
        root.mainloop()

except Exception as e:
    log_message(f"Critical error: {str(e)}")
    log_message(traceback.format_exc())
    
    # Show error dialog
    try:
        error_root = tk.Tk()
        error_root.title("Error Starting Application")
        error_root.geometry("500x300")
        tk.Label(error_root, text="Error Starting Application", font=("Arial", 16, "bold")).pack(pady=20)
        tk.Label(error_root, text=str(e), wraplength=450).pack(pady=10)
        tk.Label(error_root, text="Please check watermark_error.log for details").pack(pady=10)
        tk.Button(error_root, text="Exit", command=error_root.destroy).pack(pady=20)
        error_root.mainloop()
    except:
        pass  # Last resort - if even the error window fails