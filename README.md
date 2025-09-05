# MarketMiner Pro

A Python tool for scraping FFXI auction house data from FFXIAH.com. Built this to help with market analysis and price tracking across servers.

## What it does

- Scrapes item data from FFXIAH auction house pages
- Works with single servers or all servers at once  
- Shows real-time results as it finds items
- Exports everything to timestamped CSV files
- Has a clean GUI built with CustomTkinter

## Key Features

**Smart Performance:**
- Multi-threaded scraping (configurable 1-20 threads)
- Intelligent item validation - skips non-existent items quickly
- Remembers previously skipped items to avoid re-checking
- Built-in rate limiting to respect servers

**Data Collection:**
- Individual item prices and sales data
- Stack prices for stackable items (12s, 99s)
- Cross-server price comparisons 
- Item categories and sales velocity

**Modern Interface:**
- Dark theme GUI with real-time progress tracking
- Estimated time remaining display
- Live results table that updates as it scrapes
- Clean tabbed interface: Progress, Results, Cross-Server

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

The GUI is straightforward:
1. Pick your server (or "All Servers" for cross-server analysis)
2. Set the item ID range you want to scan
3. Adjust thread count if needed (3-5 recommended)
4. Hit start and watch the progress

Results get saved automatically with timestamps.

## Output Files

Each run creates unique timestamped files:
- `items_20250105_143052.csv` - Per-server results
- `cross_server_items_20250105_143052.csv` - Price comparisons (multi-server only)  
- `skipped_items.json` - Cumulative log of excluded items

**Single server results include:**
- Item ID, name, individual/stack prices
- Sales per day for both individual and stacks  
- Item category and stackability info

**Cross-server analysis shows:**
- Lowest/highest prices across all servers
- Which servers have the best/worst prices
- Average prices and price differences
- Server coverage statistics

## Performance & Optimization

**Smart Skipping:**
- Validates items on one server before checking all servers
- Remembers non-sellable items from previous runs
- Automatically skips known bad items for faster subsequent runs

**Recommended Settings:**
- **Threads**: 3-5 (more isn't always better)
- **Servers**: Single server for focused analysis, multi-server for price comparison
- **Ranges**: Start small (1-1000) to get familiar

**Server Notes:**
- Includes all 35+ FFXI servers (including inactive ones with old data)
- Cross-server scans take significantly longer
- Inactive servers may have stale data

## Dependencies

- `requests` - Web scraping
- `beautifulsoup4` - HTML parsing  
- `customtkinter` - Modern GUI
- `pandas` - Data handling
- `lxml` - Fast parsing
- `tabulate` - Table formatting

## Fair Warning

This scrapes data from FFXIAH.com, so:
- Don't go crazy with the thread count
- Built-in rate limiting keeps you safe
- Use it responsibly and respect their servers
- Follow FFXIAH.com's terms of service

## Contributing

Found a bug? Want to add a feature? PRs welcome. Just keep the code readable.

## Troubleshooting

If something breaks, check:
- Your internet connection
- Python version (3.8+ required)
- Virtual environment is activated
- All dependencies installed correctly

For bugs, open a GitHub issue with:
- What you were doing
- Error messages
- Your setup info

---

**MarketMiner Pro** - Built for the FFXI community. Happy trading!