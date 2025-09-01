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
                'stack_price': 0,
                'sold_per_day': 0,
                'stack_sold_per_day': 0,
                'category': '',
                'rarity': 'Common',
                'stackable': 'No'
            }
            
            # Extract item name and check for stack size
            name_element = soup.find('span', class_='item-name')
            if name_element:
                name_text = name_element.text.strip().replace('\u00a0', ' ').strip()
                item_data['name'] = name_text
                
                # Check for stack size in item name (e.g., "Alexandrite x99")
                import re
                stack_match = re.search(r'x(\d+)', name_text)
                if stack_match:
                    stack_size = stack_match.group(1)
                    # Clean the item name to remove the stack size
                    clean_name = re.sub(r'\s*x\d+\s*', '', name_text).strip()
                    item_data['name'] = clean_name
                    item_data['stackable'] = stack_size
                    item_data['is_stack_price'] = True  # Flag to indicate this is a stack price
                else:
                    item_data['is_stack_price'] = False
            
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
            
            # Check for stackable information by looking for stack link (only if not already detected from name)
            if item_data['stackable'] == 'No':
                stack_link = soup.find('a', href=lambda href: href and '?stack=1' in href)
                if stack_link:
                    # Item is stackable - get the stack URL and fetch stack data
                    stack_url = stack_link.get('href')
                    if not stack_url.startswith('http'):
                        # Relative URL, make it absolute
                        from urllib.parse import urljoin
                        stack_url = urljoin(final_url, stack_url)
                    
                    try:
                        # Fetch stack page data
                        stack_response = self.session.get(stack_url)
                        stack_response.raise_for_status()
                        stack_soup = BeautifulSoup(stack_response.content, 'html.parser')
                        
                        # Extract stack size from item name on stack page
                        stack_name_element = stack_soup.find('span', class_='item-name')
                        if stack_name_element:
                            stack_name_text = stack_name_element.text.strip().replace('\u00a0', ' ').strip()
                            import re
                            stack_match = re.search(r'x(\d+)', stack_name_text)
                            if stack_match:
                                stack_size = stack_match.group(1)
                                item_data['stackable'] = stack_size
                                
                                # Extract stack price using the same price extraction logic
                                stack_price = 0
                                price_found = False
                                
                                # Method 1: Look for "Median" row in the item stats table
                                median_cells = stack_soup.find_all(string=lambda text: text and text.strip() == 'Median')
                                for median_cell in median_cells:
                                    if median_cell.parent:
                                        median_row = median_cell.find_parent('tr')
                                        if median_row:
                                            cells = median_row.find_all('td')
                                            if len(cells) >= 2:
                                                price_span = cells[1].find('span')
                                                if price_span:
                                                    price_text = price_span.text.strip().replace(',', '')
                                                    if price_text.isdigit():
                                                        try:
                                                            stack_price = int(price_text)
                                                            price_found = True
                                                            break
                                                        except ValueError:
                                                            continue
                                
                                # Method 2: Look for "Last" sale price as fallback
                                if not price_found:
                                    last_cells = stack_soup.find_all(string=lambda text: text and text.strip() == 'Last')
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
                                                                stack_price = int(price_text)
                                                                price_found = True
                                                                break
                                                            except ValueError:
                                                                continue
                                
                                # Store stack price in the item data
                                item_data['stack_price'] = stack_price
                                
                                # Extract stack sales per day from stack page
                                stack_spd_element = stack_soup.find('span', id='sales-per-day')
                                if stack_spd_element and stack_spd_element.parent and stack_spd_element.parent.parent:
                                    try:
                                        stack_spd_text = stack_spd_element.parent.parent.text.split()[0]
                                        item_data['stack_sold_per_day'] = round(float(stack_spd_text), 2) if stack_spd_text else 0
                                    except (ValueError, IndexError):
                                        item_data['stack_sold_per_day'] = 0
                                else:
                                    item_data['stack_sold_per_day'] = 0
                            else:
                                # Stackable but couldn't determine size from name
                                item_data['stackable'] = 'Yes'
                                item_data['stack_price'] = 0
                                item_data['stack_sold_per_day'] = 0
                        else:
                            # Stackable but couldn't get stack page data
                            item_data['stackable'] = 'Yes' 
                            item_data['stack_price'] = 0
                            item_data['stack_sold_per_day'] = 0
                            
                    except Exception as e:
                        logger.error(f"Error fetching stack data for item {item_id}: {e}")
                        # Still mark as stackable even if we can't get stack data
                        item_data['stackable'] = 'Yes'
                        item_data['stack_price'] = 0
                        item_data['stack_sold_per_day'] = 0
                    
                    item_data['is_stack_price'] = False  # Individual item price, not stack price
            
            # Extract sales per day
            spd_element = soup.find('span', id='sales-per-day')
            if spd_element and spd_element.parent and spd_element.parent.parent:
                try:
                    spd_text = spd_element.parent.parent.text.split()[0]
                    item_data['sold_per_day'] = round(float(spd_text), 2) if spd_text else 0
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
    
    def get_cross_server_data(self, item_id):
        """
        Get item data across ALL servers for comprehensive comparison
        Returns dict with server data and calculated statistics
        """
        from .servers import SERVERS
        
        server_data = {}
        all_prices = []
        
        # Check ALL servers, not just selected ones
        for server_name, server_id in SERVERS.items():
            data = self.get_item_data(item_id, server_id)
            if data and data.get('name') != 'Unknown':
                server_data[server_name] = data
                # Include all prices (even 0) for true market representation
                if data.get('price', 0) > 0:
                    all_prices.append(data['price'])
        
        if len(server_data) < 2:
            return None  # Need at least 2 servers with data
        
        if not all_prices:
            return None  # Need at least some pricing data
        
        # Find lowest and highest prices from servers with pricing data
        servers_with_prices = {server: data for server, data in server_data.items() if data.get('price', 0) > 0}
        
        if len(servers_with_prices) < 2:
            return None  # Need at least 2 servers with pricing
            
        prices = {server: data['price'] for server, data in servers_with_prices.items()}
        lowest_server = min(prices, key=prices.get)
        highest_server = max(prices, key=prices.get)
        
        lowest_price = prices[lowest_server]
        highest_price = prices[highest_server]
        
        # Calculate average price across servers that have pricing data
        average_price = sum(all_prices) / len(all_prices)
        
        # Use data from any server as base (lowest price server)
        base_data = server_data[lowest_server]
        
        return {
            'itemid': item_id,
            'name': base_data['name'],
            'category': base_data['category'],
            'lowest_price': lowest_price,
            'lowest_server': lowest_server,
            'highest_price': highest_price,
            'highest_server': highest_server,
            'average_price': average_price,
            'price_difference': highest_price - lowest_price,
            'server_count': len(servers_with_prices),  # Servers with pricing data
            'total_servers': len(server_data),  # All servers with item data
            'server_data': server_data  # Full data for all servers
        }