# Ï MarketMiner Pro

**Advanced FFXI Auction House Data Mining Tool**

MarketMiner Pro is a sophisticated Python application for scraping and analyzing item data from FFXIAH.com auction house. Built with a modern CustomTkinter interface, it provides comprehensive market analysis capabilities for Final Fantasy XI players and traders.

## < Features

### <¯ **Core Functionality**
- **Multi-server Support** - Scrape data from any FFXI server
- **Configurable Range Scanning** - Set custom item ID ranges
- **Concurrent Processing** - Multi-threaded scraping for maximum speed
- **Real-time Results** - Live table updates as items are discovered
- **Advanced Filtering** - Filter by price, rarity, and availability

### =Ê **Data Collection**
- **Auction House Prices** - Current market prices and stock levels
- **Sales Analytics** - Items sold per day calculations
- **FFXIclopedia Integration** - Fetch detailed item descriptions and stats
- **Category Classification** - Automatic item categorization
- **Rarity Detection** - Identify rare, exclusive, and common items

### =» **Modern Interface**
- **CustomTkinter GUI** - Modern, native-looking interface
- **Dark Theme** - Professional appearance with system integration
- **Tabbed Interface** - Organized Progress, Results, and Activity Log views
- **Real-time Progress** - Live statistics and progress tracking
- **Horizontal Scrolling** - View all data columns in results table

### =È **Output & Analysis**
- **CSV Export** - Standard format for data analysis
- **Comprehensive Data** - Includes prices, descriptions, crafting info
- **Market Trends** - Sales velocity and stock analysis
- **Professional Reports** - Clean, organized data output

## =€ Quick Start

### Prerequisites
- Python 3.8 or higher
- Internet connection for data scraping

### Installation
```bash
# Clone the repository
git clone [repository-url]
cd MarketMiner

# Install dependencies
pip install -r requirements.txt
```

### Usage
```bash
# Run the GUI application
python main.py

# Or run as a module
python -m market_miner
```

## =Ë Dependencies

- **customtkinter** - Modern GUI framework
- **requests** - HTTP client for web scraping
- **beautifulsoup4** - HTML parsing
- **lxml** - XML/HTML parser
- **pandas** - Data analysis (optional)
- **tabulate** - Table formatting

## <® How to Use

1. **Launch** the application
2. **Configure** your scraping parameters:
   - Select target server
   - Set item ID range
   - Adjust thread count
   - Choose output file location
3. **Set Options**:
   - Include/exclude items without prices
   - Include/exclude rare items
   - Enable FFXIclopedia data fetching
4. **Start Scraping** and monitor progress
5. **View Results** in the live results table
6. **Export Data** automatically to CSV

## =' Configuration Options

### Server Selection
Choose from all available FFXI servers including:
- Asura, Bahamut, Bismarck, Carbuncle, Cerberus
- Fenrir, Lakshmi, Leviathan, Odin, Phoenix
- Quetzalcoatl, Ragnarok, Shiva, Siren, Valefor

### Performance Settings
- **Concurrent Threads**: 1-20 threads for optimal performance
- **Rate Limiting**: Built-in delays for respectful scraping
- **Error Handling**: Automatic retry and error recovery

### Data Filtering
- **Price Filters**: Include/exclude items without market prices
- **Rarity Filters**: Control inclusion of rare and exclusive items
- **Wiki Integration**: Toggle FFXIclopedia data enrichment

## =Ê Output Format

MarketMiner exports data in CSV format with the following columns:

- `itemid` - Unique item identifier
- `name` - Item name
- `price` - Current auction house price
- `stock` - Available quantity
- `sold_per_day` - Sales velocity
- `category` - Item category
- `rarity` - Rarity classification
- `url` - FFXIclopedia URL
- `wiki_name` - Wiki display name
- `description` - Item description
- `stackable` - Stack size information
- `wiki_category` - Wiki category
- `resale_price` - NPC resale value
- `used_in` - Crafting usage
- `synthesis_recipes` - Recipe information
- `obtain` - How to obtain the item

## ¡ Performance

- **Multi-threaded Architecture** - Concurrent processing for speed
- **Intelligent Rate Limiting** - Respectful to target servers
- **Memory Efficient** - Optimized for large datasets
- **Real-time Updates** - Live progress and results display

## =á Ethical Usage

MarketMiner is designed for respectful data collection:
- Built-in rate limiting to avoid server overload
- Reasonable default thread counts
- Transparent about scraping activities
- Respects robots.txt and server policies

## =Ý License

This project is for educational and personal use. Please respect FFXIAH.com's terms of service and use responsibly.

## > Contributing

Contributions welcome! Please read our contributing guidelines and submit pull requests for any improvements.

## =Þ Support

For issues, questions, or feature requests, please open an issue on our GitHub repository.

---

**MarketMiner Pro v2.0** - *Professional FFXI Market Analysis Tool*