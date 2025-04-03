"""
Suppression de Filigrane PDF
Copyright © 2025 Alexandre Caby. All rights reserved.

This software is proprietary and confidential.
Unauthorized copying, distribution, modification, public display,
or public performance of this software is strictly prohibited.

This software is provided under a license agreement and may be used
only in accordance with the terms of that agreement.
"""

import fitz  # PyMuPDF
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import shutil
import tempfile
import time
import uuid
import hashlib
import datetime
import base64
import webbrowser
import urllib.parse
import json
import ssl
import urllib.request
import secure_activation  # Added secure activation module
import hmac

class WatermarkRemoverApp:
    """Main application class for PDF watermark removal."""

    #----------------------------------------------------------------
    # UPDATE SYSTEM
    #----------------------------------------------------------------

    def check_for_updates(self, silent=False):
        """Check if a newer version is available and offer to update."""
        try:
            # Get current version from local file
            current_version = "1.0"  # Fallback version
            try:
                version_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "version.txt")
                if os.path.exists(version_file):
                    with open(version_file, "r") as f:
                        current_version = f.read().strip()
            except:
                pass
            
            # GitHub API URL for latest release
            github_api_url = "https://api.github.com/repos/Alexandre-Caby/pdf-watermark-remover/releases/latest"
            
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
            if latest_version and latest_version > current_version and download_url:
                # Format changes list
                changes_text = "\n".join([f"• {change}" for change in changes[:5]])  # Show first 5 changes
                if not changes_text:
                    changes_text = "Améliorations diverses et corrections de bugs."
                
                # Show update dialog
                update_message = f"""Une nouvelle version ({latest_version}) est disponible!

    Votre version actuelle: {current_version}

    Changements:
    {changes_text}

    Voulez-vous télécharger la mise à jour?"""
                
                if messagebox.askyesno("Mise à jour disponible", update_message):
                    # Open download URL in web browser
                    webbrowser.open(download_url)
                    messagebox.showinfo(
                        "Téléchargement en cours", 
                        "La mise à jour est en cours de téléchargement.\n\n"
                        "1. Fermez l'application actuelle\n"
                        "2. Installez la nouvelle version\n"
                        "3. Redémarrez l'application"
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
    def __init__(self, root):
        """Initialize the application."""
        self.root = root
        self.root.title("Suppression de Filigrane PDF")
        self.root.geometry("650x600")
        
        # Initialize variables
        self.init_variables()
        
        # Set up styles
        self.setup_styles()
        
        # Create UI components
        self.create_ui()
        
        # Set initial states
        self.toggle_footer_options()
        
        # Check terms and activation before proceeding
        if not self.show_terms_and_conditions():
            import sys
            sys.exit(0)
            
        if not self.validate_activation():
            import sys
            sys.exit(0)
        
        # Schedule an update check after application starts (2 seconds delay)
        self.root.after(2000, lambda: self.check_for_updates(silent=True))
    
    #----------------------------------------------------------------
    # VARIABLE AND STYLE INITIALIZATION
    #----------------------------------------------------------------
    
    def init_variables(self):
        """Initialize all tkinter variables."""
        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.name_var = tk.StringVar(value="")  # No default name
        self.footer_var = tk.StringVar(value="DOCUMENT NON APPLICABLE")
        self.progress_var = tk.IntVar()
        self.status_var = tk.StringVar()
        self.file_mode_var = tk.BooleanVar(value=False)
        self.use_footer_var = tk.BooleanVar(value=True)  # Checked by default
    
    def setup_styles(self):
        """Configure ttk styles for a consistent look."""
        self.style = ttk.Style()
        self.style.configure('TButton', font=('Arial', 10))
        self.style.configure('TLabel', font=('Arial', 10))
        self.style.configure('TCheckbutton', font=('Arial', 10))
        self.style.configure('TFrame', padding=5)
        self.style.configure('Help.TButton', font=('Arial', 10, 'bold'))
        self.style.configure('Note.TFrame', background='#f0f7ff')
        self.style.configure('Action.TButton', font=('Arial', 10, 'bold'))
    
    #----------------------------------------------------------------
    # UI CONSTRUCTION METHODS
    #----------------------------------------------------------------
    
    def create_ui(self):
        """Create the complete user interface."""
        # Main container
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill='both', expand=True)
        
        # Add UI sections
        self.create_mode_section()
        self.create_input_section()
        self.create_output_section()
        self.create_parameters_section()
        self.create_action_section()
        self.create_progress_section()
        self.create_menu_bar()
    
    def create_mode_section(self):
        """Create the file mode selection section."""
        mode_frame = ttk.Frame(self.main_frame)
        mode_frame.pack(fill='x', pady=(0, 10))
        
        # File mode checkbox
        ttk.Checkbutton(
            mode_frame, 
            text="Traiter un seul fichier PDF", 
            variable=self.file_mode_var, 
            command=self.toggle_file_mode
        ).pack(side='left')
        
        # Help button
        help_button = ttk.Button(
            mode_frame, 
            text="?", 
            width=3, 
            command=self.show_help, 
            style='Help.TButton'
        )
        help_button.pack(side='right')
    
    def create_input_section(self):
        """Create the input selection section."""
        ttk.Label(self.main_frame, text="Source :").pack(anchor='w', pady=(0, 5))
        
        input_frame = ttk.Frame(self.main_frame)
        input_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Entry(
            input_frame, 
            textvariable=self.input_var, 
            width=50
        ).pack(side='left', expand=True, fill='x')
        
        self.input_button = ttk.Button(
            input_frame, 
            text="Parcourir", 
            command=self.select_input
        )
        self.input_button.pack(side='right', padx=(5, 0))
    
    def create_output_section(self):
        """Create the output destination section."""
        ttk.Label(self.main_frame, text="Destination :").pack(anchor='w', pady=(0, 5))
        
        output_frame = ttk.Frame(self.main_frame)
        output_frame.pack(fill='x', pady=(0, 15))
        
        ttk.Entry(
            output_frame, 
            textvariable=self.output_var, 
            width=50
        ).pack(side='left', expand=True, fill='x')
        
        ttk.Button(
            output_frame, 
            text="Parcourir", 
            command=self.select_output
        ).pack(side='right', padx=(5, 0))
    
    def create_parameters_section(self):
        """Create the watermark parameters section."""
        params_frame = ttk.LabelFrame(self.main_frame, text="Paramètres des filigranes")
        params_frame.pack(fill='x', pady=(0, 15))
        
        # Name watermark (red diagonal)
        ttk.Label(
            params_frame, 
            text="Nom dans le filigrane diagonal (rouge) :"
        ).pack(anchor='w', pady=(5, 5), padx=10)
        
        ttk.Entry(
            params_frame, 
            textvariable=self.name_var, 
            width=50
        ).pack(fill='x', pady=(0, 10), padx=10)
        
        # Footer watermark (blue text)
        footer_frame = ttk.Frame(params_frame)
        footer_frame.pack(fill='x', pady=(0, 10), padx=10)
        
        ttk.Checkbutton(
            footer_frame, 
            text="Utiliser le filigrane de pied de page (bleu) :", 
            variable=self.use_footer_var, 
            command=self.toggle_footer_options
        ).pack(anchor='w')
        
        self.footer_entry = ttk.Entry(
            params_frame, 
            textvariable=self.footer_var, 
            width=50
        )
        self.footer_entry.pack(fill='x', pady=(0, 10), padx=10)
    
    def create_action_section(self):
        """Create the action buttons section."""
        self.start_button = ttk.Button(
            self.main_frame, 
            text="Lancer la suppression des filigranes", 
            command=self.process_in_thread
        )
        self.start_button.pack(pady=15)
    
    def create_progress_section(self):
        """Create the progress display section."""
        self.progress_bar = ttk.Progressbar(
            self.root, 
            variable=self.progress_var, 
            maximum=100
        )
        # Progress bar is initially hidden
        
        self.status_label = ttk.Label(
            self.root, 
            textvariable=self.status_var
        )
        # Status label is initially hidden
    
    def create_menu_bar(self):
        """Create the application menu bar."""
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)
        
        # Create File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Vérifier les mises à jour", command=self.check_for_updates)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.root.quit)
        
        # Create Help menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Aide", menu=help_menu)
        help_menu.add_command(label="Guide d'utilisation", command=self.show_help)
        help_menu.add_command(label="À propos", command=self.show_about)
    
    #----------------------------------------------------------------
    # UI CALLBACK METHODS
    #----------------------------------------------------------------
    
    def toggle_file_mode(self):
        """Toggle between single file and folder processing modes."""
        if self.file_mode_var.get():
            self.input_button.config(text="Sélectionner un fichier PDF")
            self.input_button.config(command=self.select_single_file)
        else:
            self.input_button.config(text="Parcourir")
            self.input_button.config(command=self.select_input)
    
    def toggle_footer_options(self):
        """Enable or disable footer text entry based on checkbox."""
        if self.use_footer_var.get():
            self.footer_entry.config(state="normal")
        else:
            self.footer_entry.config(state="disabled")
    
    def select_input(self):
        """Open folder selection dialog for input."""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.input_var.set(folder_selected)
    
    def select_output(self):
        """Open folder selection dialog for output."""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.output_var.set(folder_selected)
    
    def select_single_file(self):
        """Open file selection dialog for single PDF."""
        file_selected = filedialog.askopenfilename(filetypes=[("Fichiers PDF", "*.pdf")])
        if file_selected:
            self.input_var.set(file_selected)
            # Enable single file mode
            self.file_mode_var.set(True)
    
    def process_in_thread(self):
        """Start processing in a separate thread to keep UI responsive."""
        # Disable start button during processing
        self.start_button.config(state=tk.DISABLED)
        
        input_path = self.input_var.get()
        output_path = self.output_var.get()
        name_pattern = self.name_var.get()
        footer_pattern = self.footer_var.get() if self.use_footer_var.get() else ""
        
        # Validate inputs
        if not input_path:
            messagebox.showerror("Erreur", "Veuillez sélectionner un dossier source ou un fichier PDF.")
            self.start_button.config(state=tk.NORMAL)
            return
        
        if not output_path and not self.file_mode_var.get():
            messagebox.showerror("Erreur", "Veuillez sélectionner un dossier de destination.")
            self.start_button.config(state=tk.NORMAL)
            return
        
        # Handle single file mode
        if self.file_mode_var.get():
            if not input_path.lower().endswith(".pdf"):
                messagebox.showerror("Erreur", "Le fichier sélectionné n'est pas un PDF.")
                self.start_button.config(state=tk.NORMAL)
                return
                
            if not output_path:
                # Generate output filename in same directory
                dirname = os.path.dirname(input_path)
                filename = os.path.basename(input_path)
                name, ext = os.path.splitext(filename)
                timestamp = int(time.time())
                output_file = os.path.join(dirname, f"{name}_sans_filigrane_{timestamp}{ext}")
            elif os.path.isdir(output_path):
                # Generate output filename in specified directory
                filename = os.path.basename(input_path)
                name, ext = os.path.splitext(filename)
                timestamp = int(time.time())
                output_file = os.path.join(output_path, f"{name}_sans_filigrane_{timestamp}{ext}")
            else:
                # Use specified full path
                output_file = output_path
        
        # Show progress indicators
        self.progress_var.set(0)
        self.progress_bar.pack(pady=10, fill='x', padx=20)
        self.status_var.set("Démarrage du traitement...")
        self.status_label.pack(pady=5)
        
        # Define thread function
        def run_process():
            success = False
            
            try:
                if self.file_mode_var.get():
                    # Process single file
                    self.status_var.set(f"Traitement de {os.path.basename(input_path)}...")
                    success = self.remove_watermark_by_structure(
                        input_path, output_file, name_pattern, footer_pattern, 
                        self.progress_var
                    )
                else:
                    # Process folder
                    success = self.process_folder(
                        input_path, output_path, name_pattern, footer_pattern, 
                        self.progress_var, self.status_var
                    )
            except Exception as e:
                success = False
                self.root.after(0, lambda: self.status_var.set(f"Erreur: {str(e)}"))
                self.root.after(0, lambda: messagebox.showerror("Erreur", f"Une erreur est survenue: {str(e)}"))
            
            # Update UI
            self.root.after(0, lambda: self.progress_var.set(100))
            if success:
                self.root.after(0, lambda: self.status_var.set("Suppression des filigranes terminée !"))
                self.root.after(0, lambda: messagebox.showinfo("Succès", "Suppression des filigranes terminée !"))
            
            # Re-enable start button
            self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
        
        # Start processing thread
        thread = threading.Thread(target=run_process)
        thread.daemon = True
        thread.start()
    
    #----------------------------------------------------------------
    # WATERMARK REMOVAL FUNCTIONS
    #----------------------------------------------------------------
    
    def remove_watermark_by_structure(self, pdf_path, output_path, name_pattern, 
                                     footer_pattern="DOCUMENT NON APPLICABLE", progress_var=None):
        """Remove watermarks by analyzing the PDF structure."""
        try:
            # Create temporary file
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, f"temp_{int(time.time())}_{os.path.basename(output_path)}")
            
            # Open source document
            src_doc = fitz.open(pdf_path)
            total_pages = len(src_doc)
            
            # For each page
            for page_num, page in enumerate(src_doc):
                modified = False
                
                # Get all content streams for the page
                for xref in page.get_contents():
                    content = src_doc.xref_stream(xref)
                    if not content:
                        continue
                    
                    # Decode content with multiple fallbacks to handle encoding issues
                    content_text = content.decode('utf-8', errors='ignore')
                    
                    # 1. Handle named watermark (diagonal red text)
                    if name_pattern in content_text:
                        content = content.replace(name_pattern.encode('utf-8'), b'')
                        modified = True
                    
                    # 2. Handle footer text (blue text at bottom)
                    if footer_pattern and footer_pattern in content_text:
                        content = content.replace(footer_pattern.encode('utf-8'), b'')
                        modified = True
                    
                    # 3. Special handling for the date watermark with both approaches
                    
                    # First approach: Direct text matching with flexible end detection
                    date_watermark_partial = "Document non tenu"
                    if date_watermark_partial in content_text:
                        # Find start position of this text
                        start_pos = content_text.find(date_watermark_partial)
                        
                        # Look for ending markers (Tj or ET)
                        end_markers = ["Tj", "ET", "TD", ")"]
                        for marker in end_markers:
                            end_pos = content_text.find(marker, start_pos + 10)
                            if end_pos > 0:
                                # Find the opening parenthesis before this sequence
                                open_paren = content_text.rfind("(", 0, start_pos + 15)
                                if open_paren > 0:
                                    # Extract the section to remove
                                    section_to_remove = content_text[open_paren:end_pos+len(marker)]
                                    # Replace with empty content (preserving structure)
                                    if "(" in section_to_remove and ")" in section_to_remove:
                                        content = content.replace(
                                            section_to_remove.encode('utf-8'), 
                                            b'()'
                                        )
                                        modified = True
                                        break
                    
                    # Second approach: Byte pattern matching (hex encoded text)
                    hex_patterns = [
                        b'44 6f 63 75 6d 65 6e 74 20 6e 6f 6e 20 74 65 6e 75',  # "Document non tenu"
                        b'6f 63 75 6d 65 6e 74 20 6e 6f 6e 20 74 65 6e 75',      # "ocument non tenu"
                        b'44 6f 63 75 6d',                                       # "Docum"
                        b'6e 6f 6e 20 74 65 6e 75'                               # "non tenu"
                    ]
                    
                    for pattern in hex_patterns:
                        if pattern in content:
                            # Find all occurrences of this pattern
                            start_idx = 0
                            while True:
                                start_idx = content.find(pattern, start_idx)
                                if start_idx == -1:
                                    break
                                    
                                # Find the nearest opening parenthesis before this
                                open_idx = max(0, start_idx - 100)
                                chunk = content[open_idx:start_idx + 200]
                                
                                # Check if we have a parenthesis sequence
                                open_paren_pos = chunk.rfind(b'(', 0, 100)
                                if open_paren_pos >= 0:
                                    # Find the corresponding closing parenthesis
                                    close_paren_pos = chunk.find(b')', open_paren_pos)
                                    if close_paren_pos > open_paren_pos:
                                        # Extract and remove this content
                                        removal_chunk = chunk[open_paren_pos:close_paren_pos+1]
                                        content = content.replace(removal_chunk, b'()')
                                        modified = True
                                
                                start_idx += 10  # Move forward to avoid endless loop
                    
                    # 4. Handle red text (diagonal watermark) by color markers
                    if b'1 0 0 rg' in content or b'0.8 0 0 rg' in content or b'1 0 0 RG' in content:
                        # Find position of red color marker
                        red_pos = max(
                            content.find(b'1 0 0 rg'),
                            content.find(b'0.8 0 0 rg'),
                            content.find(b'1 0 0 RG')
                        )
                        
                        if red_pos > 0:
                            # Find next text operator (BT...ET sequence)
                            bt_pos = content.find(b'BT', red_pos - 50)
                            et_pos = content.find(b'ET', red_pos)
                            
                            if bt_pos > 0 and et_pos > bt_pos:
                                # Replace the entire text block with empty BT/ET
                                text_block = content[bt_pos:et_pos+2]
                                content = content.replace(text_block, b'BT ET')
                                modified = True
                    
                    # Update content if modified
                    if modified:
                        src_doc.update_stream(xref, content)
                
                # Update progress
                if progress_var is not None:
                    progress_var.set(int((page_num + 1) / total_pages * 100))
            
            # Save the document
            src_doc.save(temp_file, garbage=4, deflate=True, clean=True)
            src_doc.close()
            
            # Copy to final destination
            try:
                shutil.copy2(temp_file, output_path)
                try:
                    os.remove(temp_file)
                except:
                    pass

                # Add a subtle identification to the processed file
                try:
                    output_doc = fitz.open(output_path)
                    for page in output_doc:
                        text = f"Traité par Supprimer Filigrane PDF - ID:{int(time.time())}"
                        page.insert_text((5, 5), text, fontsize=4, color=(0.9, 0.9, 0.9))
                    output_doc.save(output_path, garbage=4, deflate=True, clean=True)
                    output_doc.close()
                except:
                    pass  # Continue even if watermark can't be added
                return True
            except Exception as e:
                messagebox.showwarning("Attention", 
                    f"Impossible d'écrire dans {output_path}.\nLe fichier traité est disponible dans: {temp_file}")
                return False
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du traitement de {pdf_path}: {str(e)}")
            return False
    
    def process_folder(self, input_folder, output_folder, name_pattern, 
                      footer_pattern="DOCUMENT NON APPLICABLE", progress_var=None, status_var=None):
        """Process all PDF files in a folder."""
        try:
            # Create destination folder if it doesn't exist
            if not os.path.exists(output_folder):
                try:
                    os.makedirs(output_folder)
                except:
                    messagebox.showerror("Erreur", f"Impossible de créer le dossier de destination: {output_folder}")
                    return False
            
            # Get all PDF files in source folder
            pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith(".pdf")]
            total_files = len(pdf_files)
            
            if total_files == 0:
                if status_var:
                    status_var.set("Aucun fichier PDF trouvé dans le dossier source.")
                return False
            
            # Process each PDF file
            for i, filename in enumerate(pdf_files):
                input_path = os.path.join(input_folder, filename)
                output_path = os.path.join(output_folder, filename)
                
                # Update status
                if status_var:
                    status_var.set(f"Traitement de {filename} ({i+1}/{total_files})")
                
                # Process the file
                success = self.remove_watermark_by_structure(input_path, output_path, name_pattern, footer_pattern)
                
                # Update overall progress
                if progress_var is not None:
                    progress_var.set(int((i + 1) / total_files * 100))
                
                if not success:
                    if status_var:
                        status_var.set(f"Erreur lors du traitement de {filename}")
                    return False
            
            if status_var:
                status_var.set(f"Traitement terminé. {total_files} fichiers traités.")
            return True
            
        except Exception as e:
            if status_var:
                status_var.set(f"Erreur: {str(e)}")
            messagebox.showerror("Erreur", f"Une erreur est survenue: {str(e)}")
            return False
    
    #----------------------------------------------------------------
    # DIALOG WINDOWS
    #----------------------------------------------------------------
    
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
        
        # Add terms of use text
        terms_text.insert("1.0", """CONTRAT DE LICENCE UTILISATEUR FINAL

En utilisant ce logiciel, vous acceptez les termes et conditions suivants :

1. PROPRIÉTÉ
   Ce logiciel est la propriété de Alexandre Caby (Alternant ingénieur chez TechniFret) et est protégé par les lois sur le droit d'auteur.

2. LICENCE
   Alexandre Caby vous accorde une licence non exclusive et non transférable pour utiliser ce logiciel.

3. RESTRICTIONS
   Vous ne pouvez pas :
   - Copier ou reproduire le logiciel
   - Modifier, adapter ou traduire le logiciel
   - Décompiler, désassembler ou faire de l'ingénierie inverse
   - Distribuer, louer ou sous-licencier le logiciel
   - Supprimer ou modifier les mentions de droit d'auteur

4. GARANTIE LIMITÉE
   Ce logiciel est fourni "tel quel" sans garantie d'aucune sorte.

5. LIMITATION DE RESPONSABILITÉ
   En aucun cas Alexandre Caby (Alternant ingénieur chez TechniFret) ne sera responsable de dommages directs,
   indirects, accessoires ou consécutifs résultant de l'utilisation de ce logiciel.

6. RÉSILIATION
   Cette licence est effective jusqu'à sa résiliation. Votre licence sera automatiquement
   résiliée si vous ne respectez pas les termes et conditions.

7. LOI APPLICABLE
   Ce contrat est régi par les lois de France.
                      
8. USAGE PROFESSIONNEL
   Ce logiciel est destiné à un usage professionnel au sein de l'entreprise.
   Son utilisation requiert l'approbation explicite d'Alexandre Caby (Alternant ingénieur chez TechniFret).
   L'utilisation de ce logiciel implique que l'entreprise a obtenu cette approbation.
   
9. INTERDICTION DE TRANSFERT
   Ce logiciel ne peut pas être transféré, partagé ou utilisé en dehors de
   l'entreprise autorisée, même par ses employés à des fins personnelles.
""")
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
        note_frame = ttk.Frame(scrollable_frame, style='Note.TFrame')
        note_frame.pack(fill="x", pady=(20, 10))
        
        note_title = ttk.Label(
            note_frame,
            text="REMARQUE IMPORTANTE:",
            font=("Arial", 10, "bold")
        )
        note_title.pack(anchor="w")
        
        note_content = ttk.Label(
            note_frame,
            text="L'outil supprime automatiquement le texte \"Document non tenu à jour...\" quelle que soit la date.",
            wraplength=550,
            justify="left"
        )
        note_content.pack(anchor="w", padx=15, pady=(5, 0))
        
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
            logo_img = tk.PhotoImage(file="icon_remove_watermark.ico")
            logo_label = tk.Label(about_dialog, image=logo_img, bg="#f5f5f5")
            logo_label.image = logo_img  # Keep a reference
            logo_label.pack(pady=(20, 10))
        except:
            pass  # Continue if icon can't be loaded
        
        # Application name
        title_label = tk.Label(
            about_dialog, 
            text="Suppression de Filigrane PDF",
            font=("Arial", 16, "bold"),
            bg="#f5f5f5"
        )
        title_label.pack(pady=(0, 5))
        
        # Version info
        version_label = tk.Label(
            about_dialog, 
            text="Version 1.0",
            font=("Arial", 10),
            bg="#f5f5f5"
        )
        version_label.pack(pady=(0, 20))
        
        # Copyright notice
        copyright_label = tk.Label(
            about_dialog, 
            text="Copyright © 2025 Alexandre Caby. All rights reserved.",
            font=("Arial", 10),
            bg="#f5f5f5"
        )
        copyright_label.pack(pady=(0, 20))
        
        # Legal text
        legal_frame = tk.Frame(about_dialog, bg="#f5f5f5")
        legal_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        legal_text = tk.Text(legal_frame, height=8, width=50, wrap="word", bg="#ffffff")
        legal_text.pack(fill="both", expand=True)
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
    
    #----------------------------------------------------------------
    # ACTIVATION SYSTEM
    #----------------------------------------------------------------
    
    def validate_activation(self):
        """Validate if the software is activated using encrypted activation data."""
        try:
            machine_id = str(uuid.getnode())
            activation_file = os.path.join(os.path.expanduser("~"), ".filigrane_activation")
            if not os.path.exists(activation_file):
                return self.request_activation(machine_id)
            try:
                with open(activation_file, "r") as f:
                    encrypted_data = f.read().strip()
                # Decrypt the activation data
                data = secure_activation.decrypt_activation_data(encrypted_data)
                stored_machine_id = data.get("machine_id", "")
                expiry_date = data.get("expiry_date", "")
                activation_code = data.get("activation_code", "")
                
                if stored_machine_id != machine_id:
                    return self.request_activation(machine_id)
                    
                expiry = datetime.datetime.strptime(expiry_date, "%Y-%m-%d")
                if datetime.datetime.now() > expiry:
                    messagebox.showwarning(
                        "Activation expirée",
                        "Votre période d'activation a expiré. Veuillez contacter l'administrateur."
                    )
                    return self.request_activation(machine_id)
                
                expected_code = self.generate_activation_code(machine_id, expiry_date)
                # Use constant-time comparison to mitigate timing attacks
                if not hmac.compare_digest(activation_code, expected_code):
                    return self.request_activation(machine_id)
                return True
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                # Do not log sensitive details in error messages.
                return self.request_activation(machine_id)
        except Exception as e:
            # Avoid leaking sensitive details in the error message
            messagebox.showerror("Erreur d'activation", "Une erreur est survenue lors de la validation d'activation.")
            return False

    def generate_activation_code(self, machine_id, expiry_date):
        """Generate an activation code using HMAC with a secret salt."""
        secret_salt = os.environ.get("ACTIVATION_SALT", "DefaultSalt1234")
        # Use HMAC with SHA256 and return first 16 hex digits.
        h = hmac.new(secret_salt.encode('utf-8'),
                     f"{machine_id}|{expiry_date}".encode('utf-8'),
                     digestmod="sha256")
        return h.hexdigest()[:16]
        
    def request_activation(self, machine_id):
        """Show activation dialog and process activation using encrypted storage."""
        activation_dialog = tk.Toplevel(self.root)
        activation_dialog.title("Activation requise")
        activation_dialog.geometry("500x430")
        activation_dialog.resizable(False, False)
        activation_dialog.transient(self.root)
        activation_dialog.grab_set()
        activation_dialog.configure(bg="#f5f5f5")
        
        # Title
        title_label = tk.Label(
            activation_dialog, 
            text="ACTIVATION DU LOGICIEL",
            font=("Arial", 16, "bold"),
            bg="#f5f5f5"
        )
        title_label.pack(pady=(20, 10))
        
        # Explanation
        explanation = tk.Label(
            activation_dialog,
            text="Ce logiciel nécessite une activation avant utilisation.\nVeuillez contacter Alexandre Caby (Alternant ingénieur chez TechniFret) pour obtenir un code d'activation.",
            justify="center",
            bg="#f5f5f5",
            wraplength=400
        )
        explanation.pack(pady=(0, 20))
        
        # Machine ID display
        id_frame = tk.Frame(activation_dialog, bg="#f5f5f5")
        id_frame.pack(fill="x", padx=20)
        
        id_label = tk.Label(
            id_frame,
            text="ID de votre machine:",
            font=("Arial", 10, "bold"),
            bg="#f5f5f5"
        )
        id_label.pack(anchor="w")
        
        machine_id_display = tk.Entry(id_frame, width=40)
        machine_id_display.insert(0, machine_id)
        machine_id_display.config(state="readonly")
        machine_id_display.pack(fill="x", pady=(5, 15))
        
        # Email request button
        def send_email_request():
            user = os.getlogin()
            
            # Create plain text for clipboard and display
            plain_text = f"""
        ID Machine: {machine_id}
        Utilisateur: {user}
        """
            
            # First try: Copy to clipboard and show instructions
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(plain_text)
                
                messagebox.showinfo(
                    "Informations copiées", 
                    "Les informations nécessaires ont été copiées dans le presse-papiers.\n\n"
                    "1. Ouvrez votre client email\n"
                    "2. Créez un nouveau message à alexandre.caby@sncf.fr\n"
                    "3. Objet: Demande de licence pour l'application 'Suppression de Filigrane PDF'\n"
                    "4. Collez le contenu du presse-papiers (Ctrl+V) dans le corps du message\n"
                    "5. Envoyez le message"
                )
                
                # Try to open default email client as a convenience
                try:
                    recipient = "alexandre.caby@sncf.fr"
                    subject = "Demande de licence pour l'application 'Suppression de Filigrane PDF'"
                    body = f"""Bonjour Alexandre,

        Je souhaite obtenir un code d'activation pour le logiciel "Suppression de Filigrane PDF".

        Informations requises:
        {plain_text}

        Merci de me fournir un code d'activation.

        Cordialement,
        """
                    # Use the simplest approach possible
                    import urllib.parse
                    email_url = f"mailto:{recipient}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
                    webbrowser.open(email_url, new=1)
                except:
                    pass  # Already showed instructions, so ignore any failure here
                    
            except Exception as e:
                messagebox.showerror(
                    "Erreur", 
                    f"Impossible de copier les informations: {str(e)}\n\n"
                    "Veuillez noter manuellement l'ID Machine et contacter l'administrateur."
                )

        email_button = tk.Button(
            id_frame,
            text="Envoyer une demande d'activation par email",
            command=send_email_request,
            bg="#e8f4ff",
            font=("Arial", 9)
        )
        email_button.pack(fill="x", pady=(0, 5))
        
        # Activation code entry
        code_frame = tk.Frame(activation_dialog, bg="#f5f5f5")
        code_frame.pack(fill="x", padx=20)
        
        code_label = tk.Label(
            code_frame,
            text="Code d'activation:",
            font=("Arial", 10, "bold"),
            bg="#f5f5f5"
        )
        code_label.pack(anchor="w")
        
        activation_code_var = tk.StringVar()
        activation_code_entry = tk.Entry(code_frame, width=40, textvariable=activation_code_var)
        activation_code_entry.pack(fill="x", pady=(5, 5))
        
        # Response tracking
        response = [False]
        
        def validate_code():
            entered_code = activation_code_var.get().strip()
            if not entered_code:
                messagebox.showwarning("Code manquant", "Veuillez entrer un code d'activation.")
                return
            if '|' not in entered_code:
                messagebox.showerror("Code invalide", "Le format du code d'activation est invalide.")
                return
            code_parts = entered_code.split('|')
            if len(code_parts) != 2:
                messagebox.showerror("Code invalide", "Le format du code d'activation est invalide.")
                return
            activation_code, expiry_date = code_parts
            try:
                expiry = datetime.datetime.strptime(expiry_date, "%Y-%m-%d")
                if datetime.datetime.now() > expiry:
                    messagebox.showerror("Code expiré", "Ce code d'activation a déjà expiré.")
                    return
                expected_code = self.generate_activation_code(machine_id, expiry_date)
                if activation_code != expected_code:
                    messagebox.showerror("Code invalide", "Le code d'activation est incorrect.")
                    return
                # Prepare data to store in an encrypted form
                activation_data = {
                    "machine_id": machine_id,
                    "expiry_date": expiry_date,
                    "activation_code": activation_code
                }
                encrypted = secure_activation.encrypt_activation_data(activation_data)
                act_file = os.path.join(os.path.expanduser("~"), ".filigrane_activation")
                with open(act_file, "w") as f:
                    f.write(encrypted)
                # Example Windows-specific: make the file hidden.
                try:
                    import ctypes
                    if os.name == 'nt':
                        FILE_ATTRIBUTE_HIDDEN = 0x02
                        ctypes.windll.kernel32.SetFileAttributesW(act_file, FILE_ATTRIBUTE_HIDDEN)
                except:
                    pass
                messagebox.showinfo(
                    "Activation réussie", 
                    f"Le logiciel a été activé avec succès jusqu'au {expiry_date}."
                )
                response[0] = True
                activation_dialog.destroy()
            except Exception as e:
                messagebox.showerror("Erreur", f"Une erreur est survenue: {str(e)}")
        
        def on_cancel():
            response[0] = False
            activation_dialog.destroy()
        
        # Buttons
        buttons_frame = tk.Frame(activation_dialog, bg="#f5f5f5")
        buttons_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        cancel_button = tk.Button(
            buttons_frame,
            text="Annuler",
            command=on_cancel,
            width=10
        )
        cancel_button.pack(side="left")
        
        activate_button = tk.Button(
            buttons_frame,
            text="Activer",
            command=validate_code,
            width=10
        )
        activate_button.pack(side="right")
        
        # Contact information
        contact_label = tk.Label(
            activation_dialog,
            text="Pour obtenir un code d'activation, contactez:\nAlexandre Caby (Alternant ingénieur chez TechniFret)\nEmail: alexandre.caby@sncf.fr",
            justify="center",
            bg="#f5f5f5",
            font=("Arial", 9)
        )
        contact_label.pack(pady=(20, 0))
        
        # Wait for dialog to close
        self.root.wait_window(activation_dialog)
        return response[0]   

# ----------------------------------------------------------------
    
# Application startup
if __name__ == "__main__":
    root = tk.Tk()
    # Set application icon
    try:
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon_remove_watermark.ico")
        root.iconbitmap(icon_path)
    except:
        pass  # Ignore if icon can't be loaded
    
    app = WatermarkRemoverApp(root)
    root.mainloop()