"""
Application Styles Module
Defines styles for the application UI.
"""

from tkinter import ttk

class AppStyles:
    """Style configuration for the application."""
    
    def __init__(self, root):
        """Initialize styles for the application."""
        self.root = root
        self.setup_styles()
    
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