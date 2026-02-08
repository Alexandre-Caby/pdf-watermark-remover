"""
Activation Manager Module.

Handles software activation lifecycle: validation of stored activation
data, HMAC-based code generation, and the activation request dialog.
"""

import datetime
import hmac
import json
import logging
import os
import urllib.parse
import uuid
import webbrowser
import tkinter as tk
from tkinter import messagebox
from typing import Optional, Union

import customtkinter as ctk

from mechanisms import secure_activation
from mechanisms.machine_id import get_machine_id, get_legacy_machine_id
from mechanisms.network_utils import fetch_json
from mechanisms._secrets import get_activation_salt

logger = logging.getLogger("watermark_app.activation")

# Default contact info used as final fallback
_DEFAULT_ADMIN_CONTACT = {
    "name": "Alexandre Caby",
    "email": "alexandre.caby@sncf.fr",
    "role": "Alternant ingénieur chez TechniFret",
}

_ADMIN_CONTACT_URL = (
    "https://raw.githubusercontent.com/Alexandre-Caby/"
    "pdf-watermark-remover/main/admin_contact.json"
)

_REVOCATION_LIST_URL = (
    "https://raw.githubusercontent.com/Alexandre-Caby/"
    "pdf-watermark-remover/main/revocation_list.json"
)


class ActivationManager:
    """Manages software activation and validation."""

    def __init__(self, root: ctk.CTk) -> None:
        """Initialise with the application root window."""
        self.root = root
        self._admin_contact: Optional[dict] = None

    # ── Admin contact ─────────────────────────────────────────────

    def _get_admin_contact(self) -> dict:
        """Fetch admin contact info from GitHub, with cache + fallback."""
        if self._admin_contact is None:
            self._admin_contact = fetch_json(
                _ADMIN_CONTACT_URL,
                cache_key="admin_contact",
                default=_DEFAULT_ADMIN_CONTACT,
                timeout=5,
            )
        return self._admin_contact

    # ── Revocation ────────────────────────────────────────────────

    def _is_code_revoked(self, activation_code: str) -> bool:
        """Check whether the activation code appears on the remote revocation list."""
        try:
            data = fetch_json(
                _REVOCATION_LIST_URL,
                cache_key="revocation_list",
                default={"revoked_codes": []},
                timeout=5,
            )
            revoked = data.get("revoked_codes", [])
            if activation_code in revoked:
                logger.warning("Activation code is on the revocation list")
                return True
        except Exception as exc:
            logger.debug("Revocation list check skipped: %s", exc)
        return False

    # ── Validation ────────────────────────────────────────────────

    def validate_activation(self) -> bool:
        """Validate whether the software is activated.

        Reads the encrypted activation file, checks machine ID match,
        verifies expiry date, and validates HMAC code.  Falls back to
        the activation request dialog on any failure.

        Supports both the new composite machine ID and the legacy
        MAC-only ID for backward compatibility.
        """
        try:
            new_machine_id = get_machine_id()
            legacy_machine_id = get_legacy_machine_id()
            activation_file = os.path.join(
                os.path.expanduser("~"), ".filigrane_activation"
            )

            if not os.path.exists(activation_file):
                return self.request_activation(new_machine_id)

            try:
                with open(activation_file, "r") as fh:
                    encrypted_data = fh.read().strip()

                data = secure_activation.decrypt_activation_data(encrypted_data)
                stored_machine_id = data.get("machine_id", "")
                expiry_date = data.get("expiry_date", "")
                activation_code = data.get("activation_code", "")

                # Accept either new or legacy machine ID
                if stored_machine_id == new_machine_id:
                    active_machine_id = new_machine_id
                elif stored_machine_id == legacy_machine_id:
                    active_machine_id = legacy_machine_id
                    logger.info("Accepted legacy machine ID format")
                else:
                    return self.request_activation(new_machine_id)

                expiry = datetime.datetime.strptime(expiry_date, "%Y-%m-%d")
                if datetime.datetime.now() > expiry:
                    messagebox.showwarning(
                        "Activation expirée",
                        "Votre période d'activation a expiré. "
                        "Veuillez contacter l'administrateur.",
                    )
                    return self.request_activation(new_machine_id)

                expected_code = self.generate_activation_code(
                    active_machine_id, expiry_date
                )
                if not hmac.compare_digest(activation_code, expected_code):
                    return self.request_activation(new_machine_id)

                # Check remote revocation list
                full_code = f"{activation_code}|{expiry_date}"
                if self._is_code_revoked(full_code):
                    messagebox.showwarning(
                        "Licence révoquée",
                        "Votre licence a été révoquée par l'administrateur.\n"
                        "Veuillez le contacter pour obtenir une nouvelle "
                        "activation.",
                    )
                    return self.request_activation(new_machine_id)

                return True

            except (json.JSONDecodeError, ValueError, KeyError) as exc:
                logger.warning(
                    "Activation file corrupted or invalid: %s", exc
                )
                return self.request_activation(new_machine_id)

        except Exception as exc:
            logger.error(
                "Activation validation error: %s", exc, exc_info=True
            )
            messagebox.showerror(
                "Erreur d'activation",
                "Une erreur est survenue lors de la validation d'activation.",
            )
            return False

    # ── Code generation ───────────────────────────────────────────

    def generate_activation_code(
        self, machine_id: str, expiry_date: str
    ) -> Union[str, bool]:
        """Generate an activation code using HMAC-SHA256.

        Returns the first 16 hex characters of the HMAC digest,
        or False if the ACTIVATION_SALT is missing.
        """
        secret_salt = get_activation_salt()
        if not secret_salt:
            return False
        h = hmac.new(
            secret_salt.encode("utf-8"),
            f"{machine_id}|{expiry_date}".encode("utf-8"),
            digestmod="sha256",
        )
        return h.hexdigest()[:16]

    # ── Activation dialog ─────────────────────────────────────────

    def request_activation(self, machine_id: str) -> bool:
        """Show a modern activation dialog and process the entered code."""
        admin = self._get_admin_contact()
        admin_name = admin.get("name", _DEFAULT_ADMIN_CONTACT["name"])
        admin_email = admin.get("email", _DEFAULT_ADMIN_CONTACT["email"])
        admin_role = admin.get("role", _DEFAULT_ADMIN_CONTACT["role"])

        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Activation requise")
        dialog.geometry("520x500")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # ── Title ─────────────────────────────────────────────────
        ctk.CTkLabel(
            dialog,
            text="ACTIVATION DU LOGICIEL",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(24, 8))

        # ── Explanation ───────────────────────────────────────────
        ctk.CTkLabel(
            dialog,
            text=(
                f"Ce logiciel nécessite une activation avant utilisation.\n"
                f"Veuillez contacter {admin_name} ({admin_role}) "
                f"pour obtenir un code d'activation."
            ),
            justify="center",
            wraplength=440,
        ).pack(pady=(0, 16))

        # ── Machine ID card ───────────────────────────────────────
        id_card = ctk.CTkFrame(dialog, corner_radius=8)
        id_card.pack(fill="x", padx=24, pady=(0, 8))

        ctk.CTkLabel(
            id_card,
            text="ID de votre machine :",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(12, 4))

        machine_entry = ctk.CTkEntry(id_card, width=400)
        machine_entry.insert(0, machine_id)
        machine_entry.configure(state="disabled")
        machine_entry.pack(fill="x", padx=14, pady=(0, 10))

        # Email request button
        def send_email_request() -> None:
            user = os.getlogin()
            plain_text = f"ID Machine: {machine_id}\nUtilisateur: {user}"
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(plain_text)
                messagebox.showinfo(
                    "Informations copiées",
                    "Les informations nécessaires ont été copiées dans "
                    "le presse-papiers.\n\n"
                    f"1. Ouvrez votre client email\n"
                    f"2. Créez un nouveau message à {admin_email}\n"
                    "3. Objet : Demande de licence pour l'application "
                    "'Suppression de Filigrane PDF'\n"
                    "4. Collez le contenu du presse-papiers (Ctrl+V)\n"
                    "5. Envoyez le message",
                )
                try:
                    subject = (
                        "Demande de licence pour l'application "
                        "'Suppression de Filigrane PDF'"
                    )
                    body = (
                        f"Bonjour {admin_name},\n\n"
                        "Je souhaite obtenir un code d'activation pour "
                        "le logiciel « Suppression de Filigrane PDF ».\n\n"
                        f"Informations requises :\n{plain_text}\n\n"
                        "Merci de me fournir un code d'activation.\n\n"
                        "Cordialement,"
                    )
                    email_url = (
                        f"mailto:{admin_email}"
                        f"?subject={urllib.parse.quote(subject)}"
                        f"&body={urllib.parse.quote(body)}"
                    )
                    webbrowser.open(email_url, new=1)
                except Exception as mail_err:
                    logger.debug("Could not open email client: %s", mail_err)
            except Exception as exc:
                messagebox.showerror(
                    "Erreur",
                    f"Impossible de copier les informations : {exc}\n\n"
                    "Veuillez noter manuellement l'ID Machine et "
                    "contacter l'administrateur.",
                )

        ctk.CTkButton(
            id_card,
            text="Envoyer une demande d'activation par email",
            command=send_email_request,
        ).pack(fill="x", padx=14, pady=(0, 12))

        # ── Activation code entry ─────────────────────────────────
        code_card = ctk.CTkFrame(dialog, corner_radius=8)
        code_card.pack(fill="x", padx=24, pady=(0, 8))

        ctk.CTkLabel(
            code_card,
            text="Code d'activation :",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).pack(anchor="w", padx=14, pady=(12, 4))

        activation_code_var = tk.StringVar()
        ctk.CTkEntry(
            code_card, textvariable=activation_code_var, width=400,
            placeholder_text="Collez votre code ici…",
        ).pack(fill="x", padx=14, pady=(0, 12))

        # ── Response tracking ─────────────────────────────────────
        response = [False]

        def validate_code() -> None:
            entered_code = activation_code_var.get().strip()
            if not entered_code:
                messagebox.showwarning(
                    "Code manquant",
                    "Veuillez entrer un code d'activation.",
                )
                return
            if "|" not in entered_code:
                messagebox.showerror(
                    "Code invalide",
                    "Le format du code d'activation est invalide.",
                )
                return
            code_parts = entered_code.split("|")
            if len(code_parts) != 2:
                messagebox.showerror(
                    "Code invalide",
                    "Le format du code d'activation est invalide.",
                )
                return

            activation_code, expiry_date = code_parts
            try:
                expiry = datetime.datetime.strptime(expiry_date, "%Y-%m-%d")
                if datetime.datetime.now() > expiry:
                    messagebox.showerror(
                        "Code expiré",
                        "Ce code d'activation a déjà expiré.",
                    )
                    return

                expected_code = self.generate_activation_code(
                    machine_id, expiry_date
                )
                if not hmac.compare_digest(activation_code, expected_code):
                    messagebox.showerror(
                        "Code invalide",
                        "Le code d'activation est incorrect.",
                    )
                    return

                # Persist encrypted activation data
                activation_data = {
                    "machine_id": machine_id,
                    "expiry_date": expiry_date,
                    "activation_code": activation_code,
                }
                encrypted = secure_activation.encrypt_activation_data(
                    activation_data
                )

                try:
                    act_file = os.path.join(
                        os.path.expanduser("~"), ".filigrane_activation"
                    )
                    with open(act_file, "w") as fh:
                        fh.write(encrypted)
                    # Try to hide the file on Windows
                    try:
                        import ctypes

                        if os.name == "nt":
                            ctypes.windll.kernel32.SetFileAttributesW(
                                act_file, 0x02
                            )
                    except (OSError, AttributeError) as hide_err:
                        logger.debug(
                            "Could not hide activation file: %s", hide_err
                        )
                except PermissionError:
                    app_data = os.environ.get(
                        "LOCALAPPDATA", os.path.expanduser("~")
                    )
                    act_file = os.path.join(app_data, ".filigrane_activation")
                    with open(act_file, "w") as fh:
                        fh.write(encrypted)

                messagebox.showinfo(
                    "Activation réussie",
                    f"Le logiciel a été activé avec succès "
                    f"jusqu'au {expiry_date}.",
                )
                response[0] = True
                dialog.destroy()
            except Exception as exc:
                messagebox.showerror(
                    "Erreur", f"Une erreur est survenue : {exc}"
                )

        def on_cancel() -> None:
            response[0] = False
            dialog.destroy()

        # ── Action buttons ────────────────────────────────────────
        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(8, 8))

        ctk.CTkButton(
            btn_row, text="Annuler", width=120,
            fg_color="gray50", hover_color="gray40",
            command=on_cancel,
        ).pack(side="left")

        ctk.CTkButton(
            btn_row, text="Activer", width=120,
            command=validate_code,
        ).pack(side="right")

        # ── Contact footer ────────────────────────────────────────
        ctk.CTkLabel(
            dialog,
            text=(
                f"Pour obtenir un code d'activation, contactez :\n"
                f"{admin_name} ({admin_role})\n"
                f"Email : {admin_email}"
            ),
            justify="center",
            font=ctk.CTkFont(size=11),
        ).pack(pady=(8, 16))

        # Wait for dialog to close
        self.root.wait_window(dialog)
        return response[0]
