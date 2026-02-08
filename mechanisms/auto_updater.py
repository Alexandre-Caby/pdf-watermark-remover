"""
Auto-updater module for PDF Watermark Remover application.

Handles checking for updates against GitHub releases, downloading
new versions, and launching an update batch script.
"""

import hashlib
import json
import logging
import os
import re
import ssl
import sys
import tempfile
import tkinter as tk
import urllib.request
from tkinter import messagebox

import customtkinter as ctk
from typing import Optional, Tuple

logger = logging.getLogger("watermark_app.updater")


def _parse_version(version_str: str) -> Tuple[int, ...]:
    """Parse a version string like '1.10.2' into a comparable tuple (1, 10, 2)."""
    try:
        return tuple(int(p) for p in version_str.strip().split("."))
    except (ValueError, AttributeError):
        return (0,)

class AutoUpdater:
    """Handles the application update process."""
    
    def __init__(self, parent_window, github_repo="Alexandre-Caby/pdf-watermark-remover"):
        """Initialize the updater with parent window reference."""
        self.parent = parent_window
        self.github_repo = github_repo
        self.current_version = self._get_current_version()
        self.update_installer_path = None
    
    def _get_current_version(self) -> str:
        """Get the current version from the version.txt file."""
        try:
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                
            version_file = os.path.join(base_path, "version.txt")

            if os.path.exists(version_file):
                with open(version_file, "r") as f:
                    return f.read().strip()
            return "1.0"
        except (OSError, ValueError) as exc:
            logger.warning("Could not read version.txt: %s", exc)
            return "1.0"
    
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

            # Try to extract SHA-256 checksum from release body
            # Expected format: SHA256: <hexdigest>  or  `SHA256: <hexdigest>`
            expected_checksum: Optional[str] = None
            checksum_match = re.search(
                r"SHA256:\s*`?([a-fA-F0-9]{64})`?", release_notes
            )
            if checksum_match:
                expected_checksum = checksum_match.group(1).lower()
                logger.info("Found release checksum: %s...", expected_checksum[:12])
            else:
                logger.warning("No SHA-256 checksum found in release notes")

            # Format changes as bullet points
            changes = []
            for line in release_notes.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):  # Skip headings
                    changes.append(line)
            
            # Compare versions using tuple comparison (handles multi-digit segments)
            if (
                latest_version
                and _parse_version(latest_version) > _parse_version(self.current_version)
                and download_url
            ):
                # Format changes list
                changes_text = "\n".join([f"• {change}" for change in changes[:5]])  # Show first 5 changes
                if not changes_text:
                    changes_text = "Améliorations diverses et corrections de bugs."
                
                if auto_install:
                    return self.download_and_prepare_update(
                        latest_version, download_url, expected_checksum
                    )
                else:
                    # Show update dialog with option to download
                    update_message = f"""Une nouvelle version ({latest_version}) est disponible!

Votre version actuelle: {self.current_version}

Changements:
{changes_text}

Voulez-vous télécharger et installer la mise à jour?"""
                    
                    if messagebox.askyesno("Mise à jour disponible", update_message):
                        return self.download_and_prepare_update(
                            latest_version, download_url, expected_checksum
                        )
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
    
    def download_and_prepare_update(
        self,
        new_version: str,
        download_url: str,
        expected_checksum: Optional[str] = None,
    ) -> bool:
        """Download the update, verify its integrity, and prepare installation."""
        try:
            # Show progress dialog
            progress_dialog = ctk.CTkToplevel(self.parent)
            progress_dialog.title("Téléchargement en cours")
            progress_dialog.geometry("440x160")
            progress_dialog.transient(self.parent)
            progress_dialog.grab_set()
            progress_dialog.resizable(False, False)

            ctk.CTkLabel(
                progress_dialog,
                text=f"Téléchargement de la version {new_version}\u2026",
                font=ctk.CTkFont(size=13),
            ).pack(pady=(24, 14))

            progress_bar = ctk.CTkProgressBar(
                progress_dialog, width=380, height=14, corner_radius=7,
            )
            progress_bar.set(0)
            progress_bar.pack(pady=(0, 12), padx=30)

            def update_progress(count, block_size, total_size):
                if total_size > 0:
                    progress_bar.set(min(count * block_size / total_size, 1.0))
                    progress_dialog.update()
            
            # Prepare download location
            download_dir = os.path.join(tempfile.gettempdir(), "pdf_watermark_updater")
            os.makedirs(download_dir, exist_ok=True)
            
            installer_path = os.path.join(download_dir, f"Suppression_de_Filigrane_PDF-{new_version}.exe")
            
            # Download the file
            try:
                urllib.request.urlretrieve(download_url, installer_path, reporthook=update_progress)

                # Verify integrity if a checksum was provided in the release
                if expected_checksum:
                    sha256 = hashlib.sha256()
                    with open(installer_path, "rb") as f:
                        for chunk in iter(lambda: f.read(65536), b""):
                            sha256.update(chunk)
                    actual_checksum = sha256.hexdigest().lower()
                    if actual_checksum != expected_checksum:
                        logger.error(
                            "Checksum mismatch: expected %s, got %s",
                            expected_checksum, actual_checksum,
                        )
                        progress_dialog.destroy()
                        messagebox.showerror(
                            "Erreur d'intégrité",
                            "Le fichier téléchargé est corrompu ou a été modifié.\n"
                            "La mise à jour a été annulée par sécurité.\n\n"
                            "Veuillez réessayer ou télécharger manuellement.",
                        )
                        try:
                            os.remove(installer_path)
                        except OSError:
                            pass
                        return False
                    logger.info("Checksum verified successfully")

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