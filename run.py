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
    
    # When running frozen, we need to manually handle imports 
    if getattr(sys, 'frozen', False):
        # Add the modules directly from MEIPASS location
        meipass_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(sys.executable)
        
        # Add main directory to path if it exists
        main_dir = os.path.join(meipass_dir, 'main')
        log_message(f"Checking if main dir exists: {os.path.exists(main_dir)}")
        if os.path.exists(main_dir):
            sys.path.insert(0, main_dir)
            
        # Now try importing with the modified path
        try:
            from main.remove_watermark import WatermarkRemoverApp
            log_message("Successfully imported WatermarkRemoverApp from main.remove_watermark")
        except ImportError as e:
            log_message(f"First import attempt failed: {e}")
            # Try direct import (which would work if files were flattened)
            try:
                sys.path.insert(0, meipass_dir)
                from remove_watermark import WatermarkRemoverApp
                log_message("Successfully imported WatermarkRemoverApp directly")
            except ImportError as e2:
                log_message(f"Direct import also failed: {e2}")
                
                # Last resort: look for specific file in main folder and import it
                try:
                    import importlib.util
                    remove_watermark_path = os.path.join(meipass_dir, 'main', 'remove_watermark.py')
                    log_message(f"Trying to import directly from: {remove_watermark_path}")
                    log_message(f"File exists: {os.path.exists(remove_watermark_path)}")
                    
                    if os.path.exists(remove_watermark_path):
                        spec = importlib.util.spec_from_file_location("remove_watermark", remove_watermark_path)
                        remove_watermark = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(remove_watermark)
                        WatermarkRemoverApp = remove_watermark.WatermarkRemoverApp
                        log_message("Successfully imported using importlib")
                    else:
                        raise ImportError(f"Could not find remove_watermark.py at {remove_watermark_path}")
                except Exception as e3:
                    log_message(f"All import attempts failed: {e3}")
                    raise ImportError(f"Failed to import WatermarkRemoverApp: {e2}") from e2
    else:
        # Normal import when running from source
        base_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, base_dir)
        from main.remove_watermark import WatermarkRemoverApp

    if __name__ == "__main__":
        root = tk.Tk()
        # Set application icon
        try:
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, "assets", "icons", "icon_remove_watermark.ico")
                log_message(f"Looking for icon at: {icon_path}")
                if not os.path.exists(icon_path):
                    # Try alternate location
                    icon_path = os.path.join(sys._MEIPASS, "icon_remove_watermark.ico") 
                    log_message(f"Trying alternate icon path: {icon_path}")
            else:
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                       "assets", "icons", "icon_remove_watermark.ico")
            
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
            else:
                log_message(f"Icon not found at {icon_path}")
        except Exception as e:
            log_message(f"Could not load icon: {e}")
            # Continue without the icon
        
        app = WatermarkRemoverApp(root)
        root.mainloop()

except Exception as e:
    log_message(f"Critical error: {str(e)}")
    log_message(traceback.format_exc())
    
    # Show error dialog
    try:
        error_root = tk.Tk()
        error_root.title("Error Starting Application")
        error_root.geometry("600x400")
        tk.Label(error_root, text="Error Starting Application", font=("Arial", 16, "bold")).pack(pady=20)
        tk.Label(error_root, text=str(e), wraplength=550).pack(pady=10)
        tk.Label(error_root, text="Please check watermark_error.log for details").pack(pady=10)
        tk.Button(error_root, text="Exit", command=error_root.destroy).pack(pady=20)
        error_root.mainloop()
    except:
        pass  # Last resort - if even the error window fails