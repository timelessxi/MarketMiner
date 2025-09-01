import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class MarketMinerScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def get_item_data(self, item_id, server_id):
        """
        Scrapes item data for a specific item ID and server
        Returns dict with item data or None if failed
        """
        try:
            # Step 1: Get redirect URL (equivalent to HEAD request in PowerShell)
            item_url = f"https://www.ffxiah.com/item/{item_id}"
            head_response = self.session.head(item_url, allow_redirects=True)
            final_url = head_response.url
            
            # Step 2: POST request with server ID
            post_data = {'sid': server_id}
            response = self.session.post(final_url, data=post_data)
            response.raise_for_status()
            
            # Step 3: Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Initialize item data
            item_data = {
                'itemid': item_id,
                'name': 'Unknown',
                'price': 0,
                'stock': 0,
                'sold_per_day': 0,
                'category': '',
                'rarity': 'Common'
            }
            
            # Extract item name
            name_element = soup.find('span', class_='item-name')
            if name_element:
                item_data['name'] = name_element.text.strip().replace('\u00a0', '').strip()
            
            # Extract category from breadcrumb navigation
            breadcrumb_links = soup.find_all('a', href=lambda href: href and '/browse/' in href)
            categories = []
            for link in breadcrumb_links:
                category = link.text.strip()
                if category and category != 'Root':
                    categories.append(category)
            item_data['category'] = ' > '.join(categories) if categories else 'Unknown'
            
            # Extract rarity and other flags from item stats
            item_stats = soup.find('span', class_='item-stats')
            rarity_flags = []
            if item_stats:
                stats_text = item_stats.text.lower()
                
                # Check for various rarity indicators
                if 'rare' in stats_text:
                    rarity_flags.append('Rare')
                if 'exclusive' in stats_text or 'ex' in stats_text:
                    rarity_flags.append('Exclusive')
                if 'no auction' in stats_text:
                    rarity_flags.append('No Auction')
                if 'no sale' in stats_text:
                    rarity_flags.append('No Sale')
                if 'cursed' in stats_text:
                    rarity_flags.append('Cursed')
                if 'temporary' in stats_text:
                    rarity_flags.append('Temporary')
                    
            # Set rarity based on flags found
            if rarity_flags:
                item_data['rarity'] = ', '.join(rarity_flags)
            else:
                item_data['rarity'] = 'Common'
            
            # Extract stock
            stock_element = soup.find('span', class_='stock')
            if stock_element:
                try:
                    item_data['stock'] = int(stock_element.text.strip())
                except ValueError:
                    item_data['stock'] = 0
            
            # Extract sales per day
            spd_element = soup.find('span', id='sales-per-day')
            if spd_element and spd_element.parent and spd_element.parent.parent:
                try:
                    spd_text = spd_element.parent.parent.text.split()[0]
                    item_data['sold_per_day'] = float(spd_text) if spd_text else 0
                except (ValueError, IndexError):
                    item_data['sold_per_day'] = 0
            
            # Extract price using HTML structure analysis
            # Look for the median price in the item info table
            price_found = False
            
            # Method 1: Look for "Median" row in the item stats table
            median_cells = soup.find_all(string=lambda text: text and text.strip() == 'Median')
            for median_cell in median_cells:
                if median_cell.parent:
                    # Find the next cell (price value)
                    median_row = median_cell.find_parent('tr')
                    if median_row:
                        cells = median_row.find_all('td')
                        if len(cells) >= 2:
                            price_span = cells[1].find('span')
                            if price_span:
                                price_text = price_span.text.strip().replace(',', '')
                                if price_text.isdigit():
                                    try:
                                        item_data['price'] = int(price_text)
                                        price_found = True
                                        break
                                    except ValueError:
                                        continue
            
            # Method 2: Look for the "Last" sale price as fallback
            if not price_found:
                last_cells = soup.find_all(string=lambda text: text and text.strip() == 'Last')
                for last_cell in last_cells:
                    if last_cell.parent:
                        last_row = last_cell.find_parent('tr')
                        if last_row:
                            cells = last_row.find_all('td')
                            if len(cells) >= 2:
                                price_span = cells[1].find('span')
                                if price_span:
                                    price_text = price_span.text.strip().replace(',', '')
                                    if price_text.isdigit():
                                        try:
                                            item_data['price'] = int(price_text)
                                            price_found = True
                                            break
                                        except ValueError:
                                            continue
            
            # Method 3: Look for any price in sales history table
            if not price_found:
                sales_tables = soup.find_all('table', class_='tbl-sales')
                for sales_table in sales_tables:
                    price_cells = sales_table.find_all('td')
                    for cell in price_cells:
                        price_text = cell.text.strip().replace(',', '')
                        # Look for numeric prices (not dates or names)
                        if price_text.isdigit() and len(price_text) >= 2:
                            try:
                                potential_price = int(price_text)
                                if potential_price >= 10:  # Reasonable minimum
                                    item_data['price'] = potential_price
                                    price_found = True
                                    break
                            except ValueError:
                                continue
                    if price_found:
                        break
            
            # Method 4: Set price to 0 for items that cannot be sold
            if not price_found:
                item_data['price'] = 0  # Keep items without prices, set price to 0

            return item_data

        except requests.RequestException as e:
            logger.error(f"Request failed for item {item_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing item {item_id}: {e}")
            return None