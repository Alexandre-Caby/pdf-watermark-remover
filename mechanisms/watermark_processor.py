"""
PDF Watermark Processing Module
Handles all PDF-related operations including watermark removal.
"""

import fitz  # PyMuPDF
import os
import shutil
import tempfile
import time
from tkinter import messagebox

class WatermarkProcessor:
    """Handles PDF watermark removal functionality."""
    
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