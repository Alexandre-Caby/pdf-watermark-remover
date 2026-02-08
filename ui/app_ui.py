"""
Application UI Module – modern CustomTkinter interface.

Provides all main-window widgets: mode switch, source / destination
pickers, watermark parameter card, action button, and progress bar.
"""

import os
import time
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk


class AppUI:
    """Modern UI components for PDF Watermark Remover."""

    def __init__(self, root: ctk.CTk, watermark_processor) -> None:
        """Initialise UI with the root window and watermark processor."""
        self.root = root
        self.watermark_processor = watermark_processor
        # Callbacks — set after construction via setters
        self.show_help_callback = None
        self.show_about_callback = None
        self.check_updates_callback = None
        self.init_variables()

    # ── Variables ──────────────────────────────────────────────────

    def init_variables(self) -> None:
        """Initialise all tkinter variables."""
        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.name_var = tk.StringVar(value="")
        self.footer_var = tk.StringVar(value="DOCUMENT NON APPLICABLE")
        self.progress_var = tk.IntVar()
        self.status_var = tk.StringVar()
        self.file_mode_var = tk.BooleanVar(value=False)
        self.use_footer_var = tk.BooleanVar(value=True)

        # Bridge IntVar(0-100) → CTkProgressBar(0.0-1.0)
        self.progress_var.trace_add("write", self._on_progress_changed)

    def _on_progress_changed(self, *_args) -> None:
        if hasattr(self, "progress_bar"):
            self.progress_bar.set(
                max(0.0, min(1.0, self.progress_var.get() / 100.0))
            )

    # ── UI assembly ───────────────────────────────────────────────

    def create_ui(self) -> None:
        """Build the complete user interface."""
        # Scrollable container for the whole window
        self.main_frame = ctk.CTkScrollableFrame(self.root, corner_radius=0)
        self.main_frame.pack(fill="both", expand=True, padx=0, pady=0)

        self._create_header()

        # Central content pane
        content = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        self._create_mode_section(content)
        self._create_io_section(content)
        self._create_parameters_section(content)
        self._create_action_section(content)
        self._create_progress_section(content)
        self.create_menu_bar()

        # Apply initial state
        self.toggle_footer_options()

    # ── Header ────────────────────────────────────────────────────

    def _create_header(self) -> None:
        header = ctk.CTkFrame(
            self.main_frame, corner_radius=0, height=56,
            fg_color=("gray92", "gray14"),
        )
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="  Suppression de Filigrane PDF",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left", padx=16)

        ctk.CTkButton(
            header, text="?", width=36, height=36,
            corner_radius=18,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=lambda: (
                self.show_help_callback() if self.show_help_callback else None
            ),
        ).pack(side="right", padx=16)

    # ── Mode switch ───────────────────────────────────────────────

    def _create_mode_section(self, parent: ctk.CTkFrame) -> None:
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.pack(fill="x", pady=(16, 0))

        ctk.CTkSwitch(
            card,
            text="  Traiter un seul fichier PDF",
            variable=self.file_mode_var,
            command=self.toggle_file_mode,
            onvalue=True, offvalue=False,
        ).pack(padx=16, pady=14, anchor="w")

    # ── Source / Destination ──────────────────────────────────────

    def _create_io_section(self, parent: ctk.CTkFrame) -> None:
        # Source
        ctk.CTkLabel(
            parent, text="Source",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", pady=(16, 4))

        src = ctk.CTkFrame(parent, fg_color="transparent")
        src.pack(fill="x")

        ctk.CTkEntry(
            src, textvariable=self.input_var,
            placeholder_text="Sélectionnez un dossier ou fichier PDF…",
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.input_button = ctk.CTkButton(
            src, text="Parcourir", width=110,
            command=self.select_input,
        )
        self.input_button.pack(side="right")

        # Destination
        ctk.CTkLabel(
            parent, text="Destination",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", pady=(14, 4))

        dst = ctk.CTkFrame(parent, fg_color="transparent")
        dst.pack(fill="x")

        ctk.CTkEntry(
            dst, textvariable=self.output_var,
            placeholder_text="Sélectionnez un dossier de destination…",
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            dst, text="Parcourir", width=110,
            command=self.select_output,
        ).pack(side="right")

    # ── Watermark parameters card ─────────────────────────────────

    def _create_parameters_section(self, parent: ctk.CTkFrame) -> None:
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.pack(fill="x", pady=(16, 0))

        ctk.CTkLabel(
            card, text="Paramètres des filigranes",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(14, 6))

        # Diagonal name
        ctk.CTkLabel(
            card, text="Nom dans le filigrane diagonal (rouge) :",
        ).pack(anchor="w", padx=16, pady=(4, 2))
        ctk.CTkEntry(
            card, textvariable=self.name_var,
            placeholder_text="Entrez le nom…",
        ).pack(fill="x", padx=16, pady=(0, 10))

        # Footer toggle + input
        ctk.CTkCheckBox(
            card,
            text="Utiliser le filigrane de pied de page (bleu) :",
            variable=self.use_footer_var,
            command=self.toggle_footer_options,
            onvalue=True, offvalue=False,
        ).pack(anchor="w", padx=16, pady=(4, 2))

        self.footer_entry = ctk.CTkEntry(card, textvariable=self.footer_var)
        self.footer_entry.pack(fill="x", padx=16, pady=(0, 14))

    # ── Action button ─────────────────────────────────────────────

    def _create_action_section(self, parent: ctk.CTkFrame) -> None:
        self.start_button = ctk.CTkButton(
            parent,
            text="Lancer la suppression des filigranes",
            height=44,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.process_in_thread,
        )
        self.start_button.pack(fill="x", pady=(20, 0))

    # ── Progress ──────────────────────────────────────────────────

    def _create_progress_section(self, parent: ctk.CTkFrame) -> None:
        self.progress_frame = ctk.CTkFrame(parent, fg_color="transparent")
        # Frame is hidden until processing starts

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame, height=14, corner_radius=7,
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 6))

        self.status_label = ctk.CTkLabel(
            self.progress_frame,
            textvariable=self.status_var,
            font=ctk.CTkFont(size=12),
        )
        self.status_label.pack(anchor="w")

    # ── Native menu bar (no CTk equivalent) ───────────────────────

    def create_menu_bar(self) -> None:
        """Build the application menu bar."""
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(
            label="Vérifier les mises à jour",
            command=lambda: (
                self.check_updates_callback()
                if self.check_updates_callback else None
            ),
        )
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.root.quit)

        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Aide", menu=help_menu)
        help_menu.add_command(
            label="Guide d'utilisation",
            command=lambda: (
                self.show_help_callback()
                if self.show_help_callback else None
            ),
        )
        help_menu.add_command(
            label="À propos",
            command=lambda: (
                self.show_about_callback()
                if self.show_about_callback else None
            ),
        )

    # ── Interactions ──────────────────────────────────────────────

    def toggle_file_mode(self) -> None:
        """Switch between single-file and folder processing."""
        if self.file_mode_var.get():
            self.input_button.configure(text="Choisir un PDF")
            self.input_button.configure(command=self.select_single_file)
        else:
            self.input_button.configure(text="Parcourir")
            self.input_button.configure(command=self.select_input)

    def toggle_footer_options(self) -> None:
        """Enable / disable the footer text entry."""
        self.footer_entry.configure(
            state="normal" if self.use_footer_var.get() else "disabled"
        )

    def select_input(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.input_var.set(folder)

    def select_output(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.output_var.set(folder)

    def select_single_file(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("Fichiers PDF", "*.pdf")]
        )
        if path:
            self.input_var.set(path)
            self.file_mode_var.set(True)

    # ── Processing ────────────────────────────────────────────────

    def process_in_thread(self) -> None:
        """Launch watermark removal in a background thread."""
        self.start_button.configure(state="disabled")

        input_path = self.input_var.get()
        output_path = self.output_var.get()
        name_pattern = self.name_var.get()
        footer_pattern = (
            self.footer_var.get() if self.use_footer_var.get() else ""
        )

        # Validate
        if not input_path:
            messagebox.showerror(
                "Erreur",
                "Veuillez sélectionner un dossier source ou un fichier PDF.",
            )
            self.start_button.configure(state="normal")
            return

        if not output_path and not self.file_mode_var.get():
            messagebox.showerror(
                "Erreur",
                "Veuillez sélectionner un dossier de destination.",
            )
            self.start_button.configure(state="normal")
            return

        output_file = ""
        if self.file_mode_var.get():
            if not input_path.lower().endswith(".pdf"):
                messagebox.showerror(
                    "Erreur", "Le fichier sélectionné n'est pas un PDF."
                )
                self.start_button.configure(state="normal")
                return

            base, ext = os.path.splitext(os.path.basename(input_path))
            stamp = int(time.time())
            if not output_path:
                output_file = os.path.join(
                    os.path.dirname(input_path),
                    f"{base}_sans_filigrane_{stamp}{ext}",
                )
            elif os.path.isdir(output_path):
                output_file = os.path.join(
                    output_path, f"{base}_sans_filigrane_{stamp}{ext}"
                )
            else:
                output_file = output_path

        # Show progress
        self.progress_var.set(0)
        self.progress_frame.pack(fill="x", pady=(16, 0))
        self.status_var.set("Démarrage du traitement…")

        def run_process() -> None:
            success = False
            try:
                if self.file_mode_var.get():
                    self.status_var.set(
                        f"Traitement de {os.path.basename(input_path)}…"
                    )
                    success = self.watermark_processor.remove_watermark_by_structure(
                        input_path, output_file, name_pattern,
                        footer_pattern, self.progress_var,
                    )
                else:
                    success = self.watermark_processor.process_folder(
                        input_path, output_path, name_pattern,
                        footer_pattern, self.progress_var, self.status_var,
                    )
            except Exception as exc:
                success = False
                self.root.after(
                    0, lambda: self.status_var.set(f"Erreur : {exc}")
                )
                self.root.after(
                    0,
                    lambda: messagebox.showerror(
                        "Erreur", f"Une erreur est survenue : {exc}"
                    ),
                )

            self.root.after(0, lambda: self.progress_var.set(100))
            if success:
                self.root.after(
                    0,
                    lambda: self.status_var.set(
                        "Suppression des filigranes terminée !"
                    ),
                )
                self.root.after(
                    0,
                    lambda: messagebox.showinfo(
                        "Succès",
                        "Suppression des filigranes terminée !",
                    ),
                )
            self.root.after(
                0, lambda: self.start_button.configure(state="normal")
            )

        thread = threading.Thread(target=run_process, daemon=True)
        thread.start()

    # ── Callback setters ──────────────────────────────────────────

    def set_show_help_callback(self, callback) -> None:
        self.show_help_callback = callback

    def set_show_about_callback(self, callback) -> None:
        self.show_about_callback = callback

    def set_check_updates_callback(self, callback) -> None:
        self.check_updates_callback = callback
