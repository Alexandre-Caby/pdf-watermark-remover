"""
Activation Manager Module
Handles software activation, validation, and licensing.
"""

import os
import hmac
import json
import uuid
import datetime
import webbrowser
import urllib.parse
import tkinter as tk
from tkinter import messagebox
from mechanisms import secure_activation

class ActivationManager:
    """Manages software activation and validation."""
    
    def __init__(self, root):
        """Initialize with root window."""
        self.root = root
        # Determine the best location for activation file
        if os.name == 'nt':  # Windows
            self.activation_file = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 
                                            "PDFWatermarkRemover", ".filigrane_activation")
        else:  # macOS/Linux
            self.activation_file = os.path.join(os.path.expanduser('~'), 
                                            ".config", "pdfwatermarkremover", ".filigrane_activation")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.activation_file), exist_ok=True)
    
    def validate_activation(self):
        """Validate if the software is activated using encrypted activation data."""
        try:
            machine_id = str(uuid.getnode())

            if not os.path.exists(self.activation_file):
                return self.request_activation(machine_id)
            
            try:
                with open(self.activation_file, "r") as f:
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
            except Exception as e:
                return self.request_activation(machine_id)
        except Exception as e:
            messagebox.showerror("Erreur d'activation", "Une erreur est survenue lors de la validation d'activation.")
            return False
        
    def generate_activation_code(self, machine_id, expiry_date):
        """Generate an activation code using HMAC with a secret salt."""
        secret_salt = os.environ.get("ACTIVATION_SALT")
        if not secret_salt:
            return False
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
                try:
                    # Prepare data to store in an encrypted form
                    activation_data = {
                        "machine_id": machine_id,
                        "expiry_date": expiry_date,
                        "activation_code": activation_code
                    }
                    encrypted = secure_activation.encrypt_activation_data(activation_data)
                    
                    # Use a more accessible location
                    try:
                        act_file = os.path.join(os.path.expanduser("~"), ".filigrane_activation")
                        with open(act_file, "w") as f:
                            f.write(encrypted)
                        
                        # Try to make it hidden
                        try:
                            import ctypes
                            if os.name == 'nt':
                                FILE_ATTRIBUTE_HIDDEN = 0x02
                                ctypes.windll.kernel32.SetFileAttributesW(act_file, FILE_ATTRIBUTE_HIDDEN)
                        except:
                            pass
                    except PermissionError:
                        # Fallback to AppData\Local which usually has write permissions
                        app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
                        act_file = os.path.join(app_data, ".filigrane_activation")
                        with open(act_file, "w") as f:
                            f.write(encrypted)
                    
                    messagebox.showinfo(
                        "Activation réussie", 
                        f"Le logiciel a été activé avec succès jusqu'au {expiry_date}."
                    )
                    response[0] = True
                    activation_dialog.destroy()
                except Exception as e:
                    messagebox.showerror("Erreur", f"Une erreur est survenue: {str(e)}")
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
