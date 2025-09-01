"""
Legacy GUI module - now imports from modular UI structure
"""

# Import the new modular GUI
from .ui import MarketMinerGUI

# Keep the old import working for compatibility
__all__ = ['MarketMinerGUI']