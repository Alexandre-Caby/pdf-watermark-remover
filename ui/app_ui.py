"""
Application UI Module
Contains UI components and handlers for the application.
"""

import os
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import time
import threading

class AppUI:
    """UI components for PDF Watermark Remover."""
    
    def __init__(self, root, watermark_processor):
        """Initialize UI with root window and watermark processor."""
        self.root = root
        self.watermark_processor = watermark_processor
        self.init_variables()
    
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
        
        # Set initial states
        self.toggle_footer_options()
    
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
            command=self.show_help_callback if hasattr(self, 'show_help_callback') else None, 
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
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # Create File menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Fichier", menu=self.file_menu)
        self.file_menu.add_command(
            label="Vérifier les mises à jour", 
            command=self.check_updates_callback if hasattr(self, 'check_updates_callback') else None
        )
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Quitter", command=self.root.quit)
        
        # Create Help menu
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Aide", menu=self.help_menu)
        self.help_menu.add_command(
            label="Guide d'utilisation", 
            command=self.show_help_callback if hasattr(self, 'show_help_callback') else None
        )
        self.help_menu.add_command(
            label="À propos", 
            command=self.show_about_callback if hasattr(self, 'show_about_callback') else None
        )
    
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
                    success = self.watermark_processor.remove_watermark_by_structure(
                        input_path, output_file, name_pattern, footer_pattern, 
                        self.progress_var
                    )
                else:
                    # Process folder
                    success = self.watermark_processor.process_folder(
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
    
    # Callback setter methods
    def set_show_help_callback(self, callback):
        """Set callback for help button."""
        self.show_help_callback = callback
    
    def set_show_about_callback(self, callback):
        """Set callback for about menu item."""
        self.show_about_callback = callback
    
    def set_check_updates_callback(self, callback):
        """Set callback for check updates menu item."""
        self.check_updates_callback = callback