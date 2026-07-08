"""
Dialog Windows Module – modern CustomTkinter dialogs.

Houses the EULA acceptance dialog, usage help guide, and About box.
"""

import logging
import os
import re
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

logger = logging.getLogger("watermark_app.dialogs")

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def _render_markdown(textbox: ctk.CTkTextbox, markdown_text: str) -> None:
    """Render a small, practical subset of Markdown into a CTkTextbox.

    Supports '#', '##', '### ' headings, '**bold**' inline spans, and
    '- ' / '* ' bullet lists. This avoids showing raw '##'/'**' syntax
    to the user while keeping legal documents editable as plain .md files.
    """
    textbox.tag_config("h1", font=("", 16, "bold"))
    textbox.tag_config("h2", font=("", 14, "bold"))
    textbox.tag_config("h3", font=("", 13, "bold"))
    textbox.tag_config("bold", font=("", 12, "bold"))
    textbox.tag_config("bullet", lmargin1=18, lmargin2=30)
    textbox.tag_config("body", font=("", 12))

    def insert_inline(text: str, base_tag: str) -> None:
        pos = 0
        for match in _BOLD_RE.finditer(text):
            if match.start() > pos:
                textbox.insert("end", text[pos:match.start()], base_tag)
            textbox.insert("end", match.group(1), (base_tag, "bold"))
            pos = match.end()
        textbox.insert("end", text[pos:], base_tag)

    for raw_line in markdown_text.splitlines():
        stripped = raw_line.strip()

        if stripped.startswith("### "):
            insert_inline(stripped[4:], "h3")
            textbox.insert("end", "\n\n")
        elif stripped.startswith("## "):
            insert_inline(stripped[3:], "h2")
            textbox.insert("end", "\n\n")
        elif stripped.startswith("# "):
            insert_inline(stripped[2:], "h1")
            textbox.insert("end", "\n\n")
        elif stripped.startswith("- ") or stripped.startswith("* "):
            textbox.insert("end", "•  ", "bullet")
            insert_inline(stripped[2:], "bullet")
            textbox.insert("end", "\n")
        elif not stripped:
            textbox.insert("end", "\n")
        else:
            insert_inline(stripped, "body")
            textbox.insert("end", "\n")


class DialogWindows:
    """Dialog window management for the application."""

    def __init__(self, root: ctk.CTk) -> None:
        """Initialise with the application root window."""
        self.root = root

    # ── EULA ──────────────────────────────────────────────────────

    def show_terms_and_conditions(self) -> bool:
        """Display the EULA; must be accepted to continue.

        Returns True if accepted, False otherwise (also destroys root).
        """
        terms_file = os.path.join(
            os.path.expanduser("~"), ".filigrane_terms_accepted"
        )
        if os.path.exists(terms_file):
            return True

        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Conditions d'utilisation")
        dialog.geometry("660x560")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.focus_set()
        dialog.resizable(False, False)

        # Title
        ctk.CTkLabel(
            dialog,
            text="CONDITIONS D'UTILISATION",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(24, 12))

        # EULA body
        textbox = ctk.CTkTextbox(
            dialog, wrap="word", height=300, corner_radius=8,
        )
        textbox.pack(fill="both", expand=True, padx=24, pady=(0, 12))

        legal_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "assets", "legal", "EULA.md",
        )
        try:
            with open(legal_path, "r", encoding="utf-8") as fh:
                _render_markdown(textbox, fh.read())
        except Exception:
            _render_markdown(
                textbox,
                "# CONTRAT DE LICENCE UTILISATEUR FINAL\n\n"
                "Le fichier EULA.md n'a pas pu être chargé. "
                "Veuillez consulter le dossier 'assets/legal' pour les "
                "conditions complètes d'utilisation.\n\n"
                "**Résumé des conditions :**\n"
                "- Ce logiciel est distribué sous licence GPL-3.0\n"
                "- L'auteur original est Alexandre Caby\n"
                "- Vous pouvez utiliser, modifier et redistribuer le "
                "logiciel sous les mêmes termes\n"
                "- Le logiciel est fourni « en l'état » sans garantie",
            )
        textbox.configure(state="disabled")

        # Agreement checkbox
        agreement_var = tk.BooleanVar()
        ctk.CTkCheckBox(
            dialog,
            text="J'ai lu et j'accepte les conditions d'utilisation",
            variable=agreement_var,
            onvalue=True, offvalue=False,
        ).pack(pady=(4, 14))

        # Buttons
        response = [False]

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(0, 24))

        def on_accept() -> None:
            if agreement_var.get():
                try:
                    with open(terms_file, "w") as fh:
                        fh.write("accepted")
                except OSError as exc:
                    logger.warning("Could not save terms acceptance: %s", exc)
                response[0] = True
                dialog.destroy()
            else:
                messagebox.showwarning(
                    "Acceptation requise",
                    "Vous devez accepter les conditions d'utilisation "
                    "pour continuer.",
                )

        def on_decline() -> None:
            response[0] = False
            dialog.destroy()

        ctk.CTkButton(
            btn_row, text="Refuser", width=130,
            fg_color="gray50", hover_color="gray40",
            command=on_decline,
        ).pack(side="left")

        ctk.CTkButton(
            btn_row, text="Accepter", width=130,
            command=on_accept,
        ).pack(side="right")

        self.root.wait_window(dialog)

        if not response[0]:
            self.root.destroy()
            return False
        return True

    # ── Help guide ────────────────────────────────────────────────

    def show_help(self) -> None:
        """Display usage instructions in a modern scrollable dialog."""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Guide d'utilisation")
        dialog.geometry("640x560")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(True, True)

        scroll = ctk.CTkScrollableFrame(dialog, corner_radius=0)
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(
            scroll,
            text="GUIDE D'UTILISATION",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(24, 16), anchor="center")

        sections = [
            {
                "title": "1.  Sélection du fichier / dossier",
                "lines": [
                    "• Cochez « Traiter un seul fichier PDF » pour un "
                    "fichier individuel.",
                    "• Sinon, sélectionnez un dossier pour traiter tous "
                    "les PDFs en masse.",
                ],
            },
            {
                "title": "2.  Destination",
                "lines": [
                    "• Indiquez où enregistrer le(s) fichier(s) traité(s).",
                    "• Si vide pour un fichier unique, le résultat est placé "
                    "dans le même dossier.",
                ],
            },
            {
                "title": "3.  Paramètres des filigranes",
                "lines": [
                    "• « Nom dans le filigrane diagonal (rouge) » : "
                    "le texte en diagonale.",
                    "• « Filigrane de pied de page (bleu) » : généralement "
                    "« DOCUMENT NON APPLICABLE ».",
                ],
            },
            {
                "title": "4.  Traitement",
                "lines": [
                    "• Cliquez sur « Lancer la suppression des filigranes ».",
                    "• Une barre de progression affichera l'avancement.",
                ],
            },
        ]

        for sec in sections:
            card = ctk.CTkFrame(scroll, corner_radius=8)
            card.pack(fill="x", padx=20, pady=(0, 12))

            ctk.CTkLabel(
                card, text=sec["title"],
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(anchor="w", padx=14, pady=(12, 4))

            for line in sec["lines"]:
                ctk.CTkLabel(
                    card, text=line, wraplength=540, justify="left",
                ).pack(anchor="w", padx=24, pady=1)

            # Card bottom padding
            ctk.CTkFrame(card, height=8, fg_color="transparent").pack()

        # Important note
        note = ctk.CTkFrame(
            scroll, corner_radius=8,
            border_width=2, border_color=("#1f6aa5", "#1f6aa5"),
        )
        note.pack(fill="x", padx=20, pady=(8, 8))

        ctk.CTkLabel(
            note, text="REMARQUE IMPORTANTE",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(12, 2))

        ctk.CTkLabel(
            note,
            text=(
                "L'outil supprime automatiquement le texte "
                "« Document non tenu à jour… » quelle que soit la date."
            ),
            wraplength=540, justify="left",
        ).pack(anchor="w", padx=24, pady=(0, 12))

        # Close button
        ctk.CTkButton(
            scroll, text="Fermer", width=140, command=dialog.destroy,
        ).pack(pady=(12, 24))

        # Centre on parent
        dialog.update_idletasks()
        x = self.root.winfo_x() + (
            self.root.winfo_width() - dialog.winfo_width()
        ) // 2
        y = self.root.winfo_y() + (
            self.root.winfo_height() - dialog.winfo_height()
        ) // 2
        dialog.geometry(f"+{x}+{y}")

    # ── About ─────────────────────────────────────────────────────

    def show_about(self) -> None:
        """Display copyright, version, and legal information."""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("À propos")
        dialog.geometry("620x720")
        dialog.minsize(560, 620)
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()

        # Icon
        try:
            icon_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "assets", "icons", "icon_remove_watermark.ico",
            )
            if os.path.exists(icon_path):
                logo_img = tk.PhotoImage(file=icon_path)
                lbl = ctk.CTkLabel(dialog, image=logo_img, text="")
                lbl.image = logo_img  # prevent GC
                lbl.pack(pady=(24, 8))
        except Exception:
            pass

        # App name
        ctk.CTkLabel(
            dialog,
            text="Suppression de Filigrane PDF",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=(0, 4))

        # Version
        try:
            vpath = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "version.txt",
            )
            with open(vpath, "r") as fh:
                ver = fh.read().strip()
        except Exception:
            ver = "1.0"

        ctk.CTkLabel(
            dialog, text=f"Version {ver}",
            font=ctk.CTkFont(size=13),
        ).pack(pady=(0, 16))

        # Copyright
        try:
            cp_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "assets", "legal", "Copyright_Notice.md",
            )
            with open(cp_path, "r", encoding="utf-8") as fh:
                lines = fh.read().splitlines()
                cp_text = next(
                    (l for l in lines if l.strip() and not l.strip().startswith("#")),
                    "Copyright © 2025 Alexandre Caby. All rights reserved.",
                )
                cp_text = _BOLD_RE.sub(r"\1", cp_text).strip("* ").strip()
        except Exception:
            cp_text = "Copyright © 2025 Alexandre Caby. All rights reserved."

        ctk.CTkLabel(
            dialog, text=cp_text, font=ctk.CTkFont(size=12),
        ).pack(pady=(0, 16))

        # Legal text box — takes up the remaining space and scrolls
        legal_box = ctk.CTkTextbox(
            dialog, corner_radius=8, wrap="word",
        )
        legal_box.pack(fill="both", expand=True, padx=24, pady=(0, 16))

        try:
            with open(cp_path, "r", encoding="utf-8") as fh:
                all_lines = fh.readlines()
                start = next(
                    (i for i, l in enumerate(all_lines) if "LOGICIEL LIBRE" in l),
                    1,
                )
                _render_markdown(legal_box, "".join(all_lines[start:]))
        except Exception:
            _render_markdown(
                legal_box,
                "Ce logiciel est distribué sous la licence GNU General "
                "Public License v3.0.\n\n"
                "L'auteur original de ce logiciel est Alexandre Caby.\n\n"
                "Vous êtes libre d'utiliser, modifier et redistribuer ce "
                "logiciel sous les mêmes termes de la GPL-3.0.\n\n"
                "Le logiciel est fourni « en l'état » sans garantie "
                "d'aucune sorte.",
            )
        legal_box.configure(state="disabled")

        # Close
        ctk.CTkButton(
            dialog, text="Fermer", width=130, command=dialog.destroy,
        ).pack(pady=(0, 24))

        # Centre on parent
        dialog.update_idletasks()
        x = self.root.winfo_x() + (
            self.root.winfo_width() - dialog.winfo_width()
        ) // 2
        y = self.root.winfo_y() + (
            self.root.winfo_height() - dialog.winfo_height()
        ) // 2
        dialog.geometry(f"+{x}+{y}")