"""
Theme and styling configuration for MarketMiner Pro using CustomTkinter
"""

import customtkinter as ctk


class ModernTheme:
    """Modern theme configuration using CustomTkinter"""
    
    def __init__(self):
        self.colors = {
            'bg': '#212121',
            'card_bg': '#2b2b2b',
            'accent': '#1f538d',
            'accent_hover': '#14375e',
            'success': '#2fa572',
            'success_hover': '#207a50',
            'danger': '#d50000',
            'danger_hover': '#b71c1c',
            'warning': '#ff6f00',
            'text': '#dce4ee',
            'text_secondary': '#9ca3af',
            'border': '#404040'
        }
    
    def apply_theme(self, root=None):
        """Apply the modern CustomTkinter theme"""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        return None