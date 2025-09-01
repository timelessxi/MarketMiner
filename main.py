#!/usr/bin/env python3
"""
MarketMiner - Advanced FFXI Auction House Data Mining Tool
Scrapes and analyzes item data from FFXIAH.com auction house
Professional GUI application for market analysis
"""

import logging
from market_miner import MarketMinerGUI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    # Create the CustomTkinter GUI directly (no tkinter root needed)
    app = MarketMinerGUI(None)
    
    # Run the CustomTkinter mainloop
    app.root.mainloop()

if __name__ == "__main__":
    main()
