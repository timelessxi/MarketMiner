#!/usr/bin/env python3
"""
Entry point for running MarketMiner as a module
Usage: python -m market_miner
"""

from .gui import MarketMinerGUI


def main():
    # Create MarketMiner GUI directly
    app = MarketMinerGUI(None)
    app.root.mainloop()


if __name__ == "__main__":
    main()