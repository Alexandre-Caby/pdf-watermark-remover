"""
Application Styles Module.

Configures CustomTkinter appearance mode and colour theme.
All widgets created after this configuration inherit the theme
automatically — no per-widget style objects needed.
"""

import customtkinter as ctk


class AppStyles:
    """Style configuration for the application."""

    # ── Palette constants (light, dark) ──────────────────────────
    ACCENT = "#1f6aa5"
    ACCENT_HOVER = "#144870"
    SUCCESS = "#2fa572"
    DANGER = "#d9534f"
    CARD = ("#ffffff", "#2b2b2b")
    SECTION_BG = ("#f0f4f8", "#1e1e1e")
    HEADER_BG = ("gray92", "gray14")
    MUTED_TEXT = ("gray40", "gray60")

    def __init__(self, root: ctk.CTk) -> None:
        """Initialise CustomTkinter theme settings."""
        self.root = root
        self.setup_styles()

    @staticmethod
    def setup_styles() -> None:
        """Set global CustomTkinter appearance."""
        ctk.set_appearance_mode("system")      # Follows OS light/dark
        ctk.set_default_color_theme("blue")    # Built-in blue accent
