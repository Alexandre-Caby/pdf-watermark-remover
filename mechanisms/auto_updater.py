"""
Auto-updater module for PDF Watermark Remover application.
Handles checking for updates, downloading and installing new versions.
"""

import os
import json
import ssl
import urllib.request
import tempfile
import tkinter as tk
from tkinter import ttk, messagebox
import sys

class AutoUpdater:
    """Handles the application update process."""
    
    def __init__(self, parent_window, github_repo="Alexandre-Caby/pdf-watermark-remover"):
        """Initialize the updater with parent window reference."""
        self.parent = parent_window
        self.github_repo = github_repo
        self.current_version = self._get_current_version()
        self.update_installer_path = None
    
    def _get_current_version(self):
        """Get the current version from the version.txt file."""
        try:
            # Determine base path based on whether running frozen or not
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                
            version_file = os.path.join(base_path, "version.txt")
            
            if os.path.exists(version_file):
                with open(version_file, "r") as f:
                    return f.read().strip()
            return "1.0"  # Fallback version
        except:
            return "1.0"  # Fallback version
    
    def check_for_updates(self, silent=False, auto_install=False):
        """Check if a newer version is available and offer to update."""
        try:
            # GitHub API URL for latest release
            github_api_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            
            # Create a request with a custom User-Agent header
            req = urllib.request.Request(github_api_url, headers={'User-Agent': 'Mozilla/5.0'})
            
            # Create an SSL context for secure HTTPS connections
            context = ssl.create_default_context()
            
            # Download release info using the secure context
            with urllib.request.urlopen(req, timeout=3, context=context) as response:
                release_info = json.loads(response.read().decode('utf-8'))
            
            # Extract version (GitHub tag name without 'v' prefix)
            latest_version = release_info.get("tag_name", "").replace("v", "")
            download_url = release_info.get("assets", [{}])[0].get("browser_download_url", "")
            
            # Get release notes (body of the release)
            release_notes = release_info.get("body", "")
            
            # Format changes as bullet points
            changes = []
            for line in release_notes.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):  # Skip headings
                    changes.append(line)
            
            # Compare versions (simple string comparison works for x.y.z format)
            if latest_version and latest_version > self.current_version and download_url:
                # Format changes list
                changes_text = "\n".join([f"• {change}" for change in changes[:5]])  # Show first 5 changes
                if not changes_text:
                    changes_text = "Améliorations diverses et corrections de bugs."
                
                if auto_install:
                    # Automatically download and prepare update
                    return self.download_and_prepare_update(latest_version, download_url)
                else:
                    # Show update dialog with option to download
                    update_message = f"""Une nouvelle version ({latest_version}) est disponible!

Votre version actuelle: {self.current_version}

Changements:
{changes_text}

Voulez-vous télécharger et installer la mise à jour?"""
                    
                    if messagebox.askyesno("Mise à jour disponible", update_message):
                        return self.download_and_prepare_update(latest_version, download_url)
                return True
            elif not silent:
                messagebox.showinfo("Pas de mise à jour", "Vous utilisez déjà la dernière version.")
            return False
        except Exception as e:
            if not silent:
                messagebox.showwarning(
                    "Vérification des mises à jour", 
                    f"Impossible de vérifier les mises à jour: {str(e)}"
                )
            return False
    
    def download_and_prepare_update(self, new_version, download_url):
        """Download the update and prepare it for installation."""
        try:
            # Show progress dialog
            progress_dialog = tk.Toplevel(self.parent)
            progress_dialog.title("Téléchargement en cours")
            progress_dialog.geometry("400x150")
            progress_dialog.transient(self.parent)
            progress_dialog.grab_set()
            progress_dialog.resizable(False, False)
            
            # Progress label
            progress_label = tk.Label(
                progress_dialog,
                text=f"Téléchargement de la version {new_version}...",
                font=("Arial", 10)
            )
            progress_label.pack(pady=(20, 10))
            
            # Progress bar
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(
                progress_dialog,
                variable=progress_var,
                maximum=100,
                length=350
            )
            progress_bar.pack(pady=10, padx=25)
            
            # Update function for progress bar
            def update_progress(count, block_size, total_size):
                if total_size > 0:
                    percent = min(count * block_size * 100 / total_size, 100)
                    progress_var.set(percent)
                    progress_dialog.update()
            
            # Prepare download location
            download_dir = os.path.join(tempfile.gettempdir(), "pdf_watermark_updater")
            os.makedirs(download_dir, exist_ok=True)
            
            installer_path = os.path.join(download_dir, f"Suppression_de_Filigrane_PDF-{new_version}.exe")
            
            # Download the file
            try:
                urllib.request.urlretrieve(download_url, installer_path, reporthook=update_progress)
                progress_dialog.destroy()
                
                # Offer to install
                if messagebox.askyesno(
                    "Téléchargement terminé",
                    f"La mise à jour vers la version {new_version} a été téléchargée avec succès.\n\n"
                    "Souhaitez-vous l'installer maintenant?\n\n"
                    "L'application va se fermer et la mise à jour sera installée."
                ):
                    # Create a batch script to wait for this app to close, then run the installer
                    batch_script = os.path.join(download_dir, "update.bat")
                    with open(batch_script, "w") as f:
                        f.write(f"""@echo off
echo Attente de la fermeture de l'application...
ping 127.0.0.1 -n 2 > nul
echo Installation de la mise à jour...
start "" "{installer_path}"
del "%~f0"
""")
                    
                    # Run the batch script and exit the application
                    os.startfile(batch_script)
                    self.parent.after(500, self.parent.quit)
                    return True
                else:
                    # Save the path for later
                    self.update_installer_path = installer_path
                    return True
                    
            except Exception as e:
                progress_dialog.destroy()
                messagebox.showerror(
                    "Erreur de téléchargement",
                    f"Impossible de télécharger la mise à jour: {str(e)}\n\n"
                    "Veuillez réessayer plus tard ou télécharger manuellement la mise à jour."
                )
                return False
                
        except Exception as e:
            messagebox.showerror(
                "Erreur de mise à jour",
                f"Une erreur est survenue lors de la préparation de la mise à jour: {str(e)}"
            )
            return False