# MarketMiner Pro

Scrapes FFXI auction house data from FFXIAH.com for market analysis and price tracking.

## What it does

- Scrapes item prices from FFXIAH auction house
- Works with single servers or all active servers
- Real-time progress with time estimates
- Exports to timestamped CSV files
- Clean dark theme interface

## Installation

Need Python 3.8+:

```bash
git clone https://github.com/timelessxi/MarketMiner.git
cd MarketMiner
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Or download the executable from [Releases](https://github.com/timelessxi/MarketMiner/releases).

## Usage

1. Pick your server
2. Set item ID range to scan
3. Hit start and wait

Results save automatically with timestamps so you can compare different runs.

## Output

**Single server**: Item prices, sales data, categories per server
**Cross-server**: Price comparisons across all servers showing best deals

Files created:
- `items_YYYYMMDD_HHMMSS.csv` - Your results
- `cross_server_items_YYYYMMDD_HHMMSS.csv` - Price comparisons (if using multiple servers)
- `skipped_items.json` - Items that can't be sold (already pre-populated)

## Notes

- Uses 3-5 threads by default (don't go crazy)
- Remembers bad items from previous runs to speed things up
- Cross-server scans take longer but show price differences
- Data comes from FFXIAH.com - use responsibly

## License

MIT License - see LICENSE file

---

Built for the FFXI community