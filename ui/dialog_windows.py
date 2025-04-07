"""
Dialog Windows Module
Contains all application dialog windows and popups.
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox

class DialogWindows:
    """Dialog window management for the application."""
    
    def __init__(self, root):
        """Initialize with root window."""
        self.root = root
        
    def show_terms_and_conditions(self):
        """Display terms and conditions that must be accepted."""
        # Check if terms have been accepted before
        terms_file = os.path.join(os.path.expanduser("~"), ".filigrane_terms_accepted")
        if os.path.exists(terms_file):
            return True  # Already accepted
        
        terms_dialog = tk.Toplevel(self.root)
        terms_dialog.title("Conditions d'utilisation")
        terms_dialog.geometry("600x500")
        terms_dialog.transient(self.root)
        terms_dialog.grab_set()
        
        # Make the dialog modal
        terms_dialog.focus_set()
        
        # Terms title
        title_label = tk.Label(
            terms_dialog, 
            text="CONDITIONS D'UTILISATION",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(20, 10))
        
        # Scrollable terms text
        terms_frame = tk.Frame(terms_dialog)
        terms_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        scrollbar = tk.Scrollbar(terms_frame)
        scrollbar.pack(side="right", fill="y")
        
        terms_text = tk.Text(
            terms_frame, 
            wrap="word", 
            yscrollcommand=scrollbar.set,
            height=15
        )
        terms_text.pack(fill="both", expand=True)
        scrollbar.config(command=terms_text.yview)
        
        # Load EULA from assets/legal folder
        legal_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                "assets", "legal", "EULA.md")
        try:
            with open(legal_path, "r", encoding="utf-8") as f:
                terms_content = f.read()
            terms_text.insert("1.0", terms_content)
        except Exception as e:
            # Fallback to a shorter message directing user to find the full terms
            terms_text.insert("1.0", """CONTRAT DE LICENCE UTILISATEUR FINAL

    Le fichier EULA.md n'a pas pu être chargé. Veuillez consulter le dossier 'assets/legal' pour les conditions complètes d'utilisation.

    Résumé des conditions:
    - Ce logiciel est la propriété d'Alexandre Caby
    - Une licence non-exclusive vous est accordée pour une utilisation professionnelle
    - Toute copie, modification ou distribution non autorisée est interdite
    - Le logiciel est fourni "tel quel" sans garantie

    Pour les conditions complètes, veuillez contacter l'administrateur.""")
        
        terms_text.config(state="disabled")  # Make read-only
        
        # Agreement checkbox
        agreement_var = tk.BooleanVar()
        agreement_check = tk.Checkbutton(
            terms_dialog, 
            text="J'ai lu et j'accepte les conditions d'utilisation",
            variable=agreement_var
        )
        agreement_check.pack(pady=(5, 10))
        
        # Buttons frame
        buttons_frame = tk.Frame(terms_dialog)
        buttons_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Response tracking
        response = [False]  # Use list for mutable closure
        
        def on_accept():
            if agreement_var.get():
                # Save acceptance
                try:
                    with open(terms_file, "w") as f:
                        f.write("accepted")
                except:
                    pass  # Continue even if we can't save
                response[0] = True
                terms_dialog.destroy()
            else:
                messagebox.showwarning(
                    "Acceptation requise", 
                    "Vous devez accepter les conditions d'utilisation pour continuer."
                )
        
        def on_decline():
            response[0] = False
            terms_dialog.destroy()
            
        # Decline button
        decline_button = tk.Button(
            buttons_frame, 
            text="Refuser", 
            command=on_decline
        )
        decline_button.pack(side="left", padx=(0, 10))
        
        # Accept button
        accept_button = tk.Button(
            buttons_frame, 
            text="Accepter", 
            command=on_accept
        )
        accept_button.pack(side="right")
        
        # Wait for dialog to close
        self.root.wait_window(terms_dialog)
        
        if not response[0]:
            # If declined, exit the application
            self.root.destroy()
            return False
            
        return True
        
    def show_help(self):
        """Display help dialog with usage instructions."""
        # Create dialog window
        help_dialog = tk.Toplevel(self.root)
        help_dialog.title("Guide d'utilisation")
        help_dialog.geometry("600x500")
        help_dialog.resizable(True, True)
        help_dialog.transient(self.root)  # Set to be on top of the main window
        help_dialog.grab_set()  # Make dialog modal
        
        # Style the dialog
        help_dialog.configure(bg="#f5f5f5")
        
        # Main frame with padding
        main_frame = ttk.Frame(help_dialog, padding="20")
        main_frame.pack(fill='both', expand=True)
        
        # Scrollable text area with improved scrolling
        help_canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=help_canvas.yview)
        scrollable_frame = ttk.Frame(help_canvas)
        
        # Configure scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: help_canvas.configure(scrollregion=help_canvas.bbox("all"))
        )
        
        # Create window in canvas
        help_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        help_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack the canvas and scrollbar
        help_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Enable mousewheel scrolling
        def _on_mousewheel(event):
            # Scroll 2 units for each mousewheel click
            help_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _on_mousewheel_linux(event):
            # For Linux systems
            if event.num == 4:  # Scroll up
                help_canvas.yview_scroll(-1, "units")
            elif event.num == 5:  # Scroll down
                help_canvas.yview_scroll(1, "units")
        
        # Bind mousewheel events - platform specific
        if os.name == 'nt':  # Windows
            help_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        else:  # Linux and macOS
            help_canvas.bind_all("<Button-4>", _on_mousewheel_linux)
            help_canvas.bind_all("<Button-5>", _on_mousewheel_linux)
        
        # Title section
        title_label = ttk.Label(
            scrollable_frame, 
            text="GUIDE D'UTILISATION",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 15), anchor="center")
        
        # Sections with content
        sections = [
            {
                "title": "1. SÉLECTION DU FICHIER/DOSSIER",
                "content": [
                    "• Choisissez un fichier PDF individuel en cochant \"Traiter un seul fichier PDF\"",
                    "• Ou sélectionnez un dossier contenant plusieurs PDFs à traiter en masse"
                ]
            },
            {
                "title": "2. DESTINATION",
                "content": [
                    "• Indiquez où enregistrer le(s) fichier(s) traité(s)",
                    "• Si vide pour un fichier unique, le résultat sera dans le même dossier"
                ]
            },
            {
                "title": "3. PARAMÈTRES DES FILIGRANES",
                "content": [
                    "• \"Nom dans le filigrane diagonal (rouge)\": Entrez le nom qui apparaît en diagonale",
                    "• \"Filigrane de pied de page (bleu)\": Généralement \"DOCUMENT NON APPLICABLE\""
                ]
            },
            {
                "title": "4. TRAITEMENT",
                "content": [
                    "• Cliquez sur \"Lancer la suppression des filigranes\"",
                    "• Une barre de progression affichera l'avancement"
                ]
            }
        ]
        
        # Add each section with styling
        for section in sections:
            # Section frame with background color
            section_frame = ttk.Frame(scrollable_frame)
            section_frame.pack(fill="x", pady=10)
            
            # Section title with separator
            title_frame = ttk.Frame(section_frame)
            title_frame.pack(fill="x")
            
            title = ttk.Label(
                title_frame, 
                text=section["title"],
                font=("Arial", 11, "bold")
            )
            title.pack(anchor="w", pady=(0, 5))
            
            ttk.Separator(section_frame).pack(fill="x", pady=(0, 5))
            
            # Section content
            for line in section["content"]:
                content = ttk.Label(
                    section_frame,
                    text=line,
                    wraplength=550,
                    justify="left"
                )
                content.pack(anchor="w", padx=15)
        
        # Add a note at the bottom with visual distinction
        note_frame = ttk.Frame(scrollable_frame)
        note_frame.pack(fill="x", pady=(20, 10))

        # Add a thin border
        note_border = ttk.Frame(note_frame, style='TFrame', borderwidth=1, relief="solid")
        note_border.pack(fill="x", padx=5, pady=5)
        
        note_title = ttk.Label(
            note_border,
            text="REMARQUE IMPORTANTE:",
            font=("Arial", 10, "bold")
        )
        note_title.pack(anchor="w", padx=10, pady=(10, 0))

        note_content = ttk.Label(
            note_border,
            text="L'outil supprime automatiquement le texte \"Document non tenu à jour...\" quelle que soit la date.",
            wraplength=500,
            justify="left"
        )
        note_content.pack(anchor="w", padx=15, pady=(5, 10))
        
        # Close button
        close_button = ttk.Button(
            scrollable_frame,
            text="Fermer",
            command=help_dialog.destroy,
            style='Action.TButton'
        )
        close_button.pack(pady=20)
        
        # Unbind mouse events when dialog is closed
        def on_close():
            help_canvas.unbind_all("<MouseWheel>")
            help_canvas.unbind_all("<Button-4>")
            help_canvas.unbind_all("<Button-5>")
            help_dialog.destroy()
        
        help_dialog.protocol("WM_DELETE_WINDOW", on_close)
        
        # Center the dialog on the main window
        help_dialog.update_idletasks()
        width = help_dialog.winfo_width()
        height = help_dialog.winfo_height()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        help_dialog.geometry(f"+{x}+{y}")
        
        # Focus canvas for keyboard navigation
        help_canvas.focus_set()
    
    def show_about(self):
        """Display copyright and legal information."""
        about_dialog = tk.Toplevel(self.root)
        about_dialog.title("À propos de Suppression de Filigrane PDF")
        about_dialog.geometry("500x400")
        about_dialog.resizable(False, False)
        about_dialog.transient(self.root)
        about_dialog.grab_set()
        
        # Styling for the dialog
        about_dialog.configure(bg="#f5f5f5")
        
        # Logo/Icon at top
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "assets", "icons", "icon_remove_watermark.ico")
            logo_img = tk.PhotoImage(file=icon_path)
            logo_label = tk.Label(about_dialog, image=logo_img, bg="#f5f5f5")
            logo_label.image = logo_img  # Keep a reference
            logo_label.pack(pady=(20, 10))
        except Exception as e:
            pass  # Continue if icon can't be loaded
        
        # Application name
        title_label = tk.Label(
            about_dialog, 
            text="Suppression de Filigrane PDF",
            font=("Arial", 16, "bold"),
            bg="#f5f5f5"
        )
        title_label.pack(pady=(0, 5))
        
        # Version info - get current version from file
        try:
            version_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "version.txt")
            if os.path.exists(version_file):
                with open(version_file, "r") as f:
                    current_version = f.read().strip()
            else:
                current_version = "1.0"
        except:
            current_version = "1.0"
            
        version_label = tk.Label(
            about_dialog, 
            text=f"Version {current_version}",
            font=("Arial", 10),
            bg="#f5f5f5"
        )
        version_label.pack(pady=(0, 20))
        
        # Add an update button to the about dialog
        update_button = tk.Button(
            about_dialog,
            text="Vérifier les mises à jour",
            command=lambda: self.update_callback() if hasattr(self, 'update_callback') else None,
            width=20
        )
        update_button.pack(pady=(0, 10))
        
        # Copyright notice - Load from Copyright_Notice.md
        try:
            copyright_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                        "assets", "legal", "Copyright_Notice.md")
            with open(copyright_path, "r", encoding="utf-8") as f:
                copyright_content = f.read().splitlines()
                # Use first line as the copyright notice
                copyright_text = next((line for line in copyright_content if line.strip() and line.strip()[0] != '#'), 
                                "Copyright © 2025 Alexandre Caby. All rights reserved.")
        except:
            copyright_text = "Copyright © 2025 Alexandre Caby. All rights reserved."
        
        copyright_label = tk.Label(
            about_dialog, 
            text=copyright_text,
            font=("Arial", 10),
            bg="#f5f5f5"
        )
        copyright_label.pack(pady=(0, 20))
        
        # Legal text - Load from legal files
        legal_frame = tk.Frame(about_dialog, bg="#f5f5f5")
        legal_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        legal_text = tk.Text(legal_frame, height=8, width=50, wrap="word", bg="#ffffff")
        legal_text.pack(fill="both", expand=True)
        
        # Try to load copyright details from the copyright notice file
        try:
            copyright_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                        "assets", "legal", "Copyright_Notice.md")
            with open(copyright_path, "r", encoding="utf-8") as f:
                # Skip the title and first line to get to the legal content
                lines = f.readlines()
                start_line = next((i for i, line in enumerate(lines) if "PROPRIETARY SOFTWARE" in line), 1)
                content = "".join(lines[start_line:])
                legal_text.insert("1.0", content)
        except:
            # Fallback to hardcoded text
            legal_text.insert("1.0", """Ce logiciel est protégé par le droit d'auteur et les traités internationaux.

    Toute reproduction ou distribution non autorisée de ce programme, ou de toute partie de celui-ci, peut entraîner de sévères sanctions civiles et pénales, et sera poursuivie dans toute la mesure permise par la loi.

    Ce logiciel est fourni sous licence et peut être utilisé uniquement conformément aux termes de cette licence.""")
        
        legal_text.config(state="disabled")  # Make read-only
        
        # Close button
        close_button = tk.Button(
            about_dialog, 
            text="Fermer", 
            command=about_dialog.destroy,
            width=10
        )
        close_button.pack(pady=(0, 20))

    def set_update_callback(self, callback):
        """Set callback for the update button in the about dialog."""
        self.update_callback = callback