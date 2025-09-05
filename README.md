# MarketMiner Pro

A Python tool for scraping FFXI auction house data from FFXIAH.com. Built this to help with market analysis and price tracking across servers.

## What it does

- Scrapes item data from FFXIAH auction house pages
- Works with single servers or all servers at once  
- Shows real-time results as it finds items
- Exports everything to CSV for spreadsheet analysis
- Has a decent GUI built with CustomTkinter

## Features

**Data Collection:**
- Individual item prices and sales data
- Stack prices for stackable items (12s, 99s)
- Cross-server price comparisons 
- Item categories
- Sales velocity tracking

**Interface:**
- Dark theme GUI that doesn't hurt your eyes
- Real-time progress tracking
- Live results table that updates as it scrapes
- Tabbed interface for progress/results/logs

**Performance:**
- Multi-threaded scraping (configurable 1-20 threads)
- Built-in rate limiting so we don't hammer their servers
- Handles errors and retries automatically

## Installation

You'll need Python 3.8 or newer.

```bash
git clone https://github.com/your-username/MarketMiner.git
cd MarketMiner

# Set up virtual environment (recommended)
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

Just run it:
```bash
python main.py
```

The GUI is pretty straightforward:
1. Pick your server (or "All Servers" for cross-server analysis)
2. Set the item ID range you want to scan
3. Adjust thread count if needed (5-10 works well)
4. Hit start and watch it go

Results get saved to a CSV file automatically.

## Output

**Single server mode** gives you:
- Item ID, name, individual price, stack price
- Sales per day for both individual and stacks  
- Item category and stackability info
- Server name

**Cross-server mode** shows:
- Lowest/highest prices across all servers
- Which servers have the best/worst prices
- Average prices and price differences
- How many servers actually have data

## Configuration

**Servers:** All the usual suspects - Asura, Bahamut, Carbuncle, etc. Full list of 35+ servers supported (includes inactive servers with old data).

**Performance:** Start with 3-5 threads. More isn't always better and might get you rate limited.

## Dependencies

The usual suspects:
- `requests` for web scraping
- `beautifulsoup4` for parsing HTML
- `customtkinter` for the GUI
- `pandas` for data handling
- A few others (see requirements.txt)

## Fair Warning

This scrapes data from FFXIAH.com, so:
- Don't go crazy with the thread count
- Built-in rate limiting should keep you safe
- Use it responsibly 
- Respect their servers and ToS

## Contributing

Found a bug? Want to add a feature? PRs welcome. Just try to keep the code readable.

## Issues

If something breaks, open an issue on GitHub with:
- What you were doing
- What went wrong  
- Your Python version
- Any error messages

---

Built for the FFXI community. Happy trading!