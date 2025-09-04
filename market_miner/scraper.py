import logging
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
logger = logging.getLogger(__name__)

class MarketMinerScraper:
    def __init__(self, *, timeout: float = 15.0):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        self.timeout = timeout

    def get_item_data(self, item_id: int | str, server_id: int | str):
        """
        Scrape item data for a specific item ID and server.

        Returns:
            dict: Item data payload, or None if the item is non-sellable/non-tradeable
                  (Exclusive/No Auction/No Sale) or if a request/parsing error occurs.
        """
        try:
            # Resolve final item URL (FFXIAH often redirects /item/{id})
            item_url = f"https://www.ffxiah.com/item/{item_id}"
            head_resp = self.session.head(item_url, allow_redirects=True, timeout=self.timeout)
            final_url = head_resp.url

            # Set the active server via POST to the item page
            resp = self.session.post(final_url, data={"sid": server_id}, timeout=self.timeout)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.content, "html.parser")

            # ---------- Base payload ----------
            item_data = {
                "itemid": item_id,
                "name": "Unknown",
                "price": 0,
                "stack_price": 0,
                "sold_per_day": 0,
                "stack_sold_per_day": 0,
                "category": "",
                "rarity": "Common",
                "stackable": "No",
                "is_stack_price": False,
            }

            # ---------- Name + inline stack-size badge (e.g., "Alexandrite x99") ----------
            name_el = soup.select_one("span.item-name")
            if name_el:
                name_text = name_el.get_text(" ", strip=True).replace("\u00a0", " ").strip()
                item_data["name"] = name_text
                m = re.search(r"\bx(\d+)\b", name_text, flags=re.I)
                if m:
                    item_data["stackable"] = m.group(1)
                    item_data["name"] = re.sub(r"\s*x\d+\s*", "", name_text, flags=re.I).strip()
                    item_data["is_stack_price"] = True  # current view appears to be the stack variant

            # ---------- Category via breadcrumbs ----------
            cats = []
            for a in soup.find_all("a", href=lambda h: h and "/browse/" in h):
                txt = (a.get_text(strip=True) or "")
                if txt and txt.lower() != "root":
                    cats.append(txt)
            item_data["category"] = " > ".join(cats) if cats else "Unknown"

            # ---------- Rarity flags (visual badges + text hints) ----------
            rarity_flags: list[str] = []
            if soup.select_one("span.ex"):
                rarity_flags.append("Exclusive")
            if soup.select_one("span.rare"):
                rarity_flags.append("Rare")

            # Text-based flags that sometimes appear in item body
            stats_text = " ".join(el.get_text(" ", strip=True).lower() for el in soup.select("span.item-stats"))
            def page_has(pattern: str) -> bool:
                return soup.find(string=re.compile(pattern, re.I)) is not None

            if "no auction" in stats_text or page_has(r"\bno\s*auction\b"):
                rarity_flags.append("No Auction")
            if "no sale" in stats_text or page_has(r"\bno\s*sale\b"):
                rarity_flags.append("No Sale")
            if "cursed" in stats_text:
                rarity_flags.append("Cursed")
            if "temporary" in stats_text:
                rarity_flags.append("Temporary")

            # Skip non-sellable/non-tradeable items early
            if any(flag in rarity_flags for flag in ("Exclusive", "No Auction", "No Sale")):
                return {
                    "itemid": item_id,
                    "name": item_data.get("name", "Unknown"),
                    "rarity": ", ".join(rarity_flags) if rarity_flags else "Common",
                    "skip_reason": "non-sellable/non-tradeable",
                }

            item_data["rarity"] = ", ".join(rarity_flags) if rarity_flags else "Common"

            # ---------- Stack info (if there is a separate stack view) ----------
            if item_data["stackable"] == "No":
                stack_link = soup.find("a", href=lambda h: h and "?stack=1" in h)
                if stack_link:
                    stack_url = stack_link.get("href")
                    if not stack_url.startswith("http"):
                        stack_url = urljoin(final_url, stack_url)

                    try:
                        stack_resp = self.session.get(stack_url, timeout=self.timeout)
                        stack_resp.raise_for_status()
                        stack_soup = BeautifulSoup(stack_resp.content, "html.parser")

                        stack_name_el = stack_soup.select_one("span.item-name")
                        if stack_name_el:
                            stack_name = stack_name_el.get_text(" ", strip=True).replace("\u00a0", " ").strip()
                            m2 = re.search(r"\bx(\d+)\b", stack_name, flags=re.I)
                            if m2:
                                item_data["stackable"] = m2.group(1)

                                # Stack median / last price
                                stack_price = self._extract_price_from_tables(stack_soup)
                                item_data["stack_price"] = stack_price

                                # Stack sales/day
                                spd_el = stack_soup.find("span", id="sales-per-day")
                                item_data["stack_sold_per_day"] = self._parse_sales_per_day(spd_el)
                            else:
                                # Stack page exists but no size badge was found
                                item_data["stackable"] = "Yes"
                        else:
                            item_data["stackable"] = "Yes"

                        item_data["is_stack_price"] = False  # we’re returning the single-item view

                    except Exception as e:
                        logger.error(f"Error fetching stack data for item {item_id}: {e}")
                        item_data["stackable"] = "Yes"

            # ---------- Sales/day (single item) ----------
            spd_el = soup.find("span", id="sales-per-day")
            item_data["sold_per_day"] = self._parse_sales_per_day(spd_el)

            # ---------- Price (single item) ----------
            item_data["price"] = self._extract_price_from_tables(soup)

            return item_data

        except requests.RequestException as e:
            logger.error(f"Request failed for item {item_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing item {item_id}: {e}")
            return None

    def _parse_sales_per_day(self, spd_el) -> float:
        """FFXIAH renders '(X sold/day)' with the numeric value in the grandparent row."""
        if spd_el and spd_el.parent and spd_el.parent.parent:
            try:
                txt = spd_el.parent.parent.get_text(" ", strip=True)
                num = txt.split()[0]
                return round(float(num), 2) if num else 0.0
            except (ValueError, IndexError):
                return 0.0
        return 0.0

    def _extract_price_from_tables(self, soup: BeautifulSoup) -> int:
        """
        Extract a best-guess price using page tables.
        Priority: 'Median' row -> 'Last' row -> first numeric from sales history.
        """
        # Median
        for cell in soup.find_all(string=lambda t: t and t.strip() == "Median"):
            row = cell.find_parent("tr")
            if not row:
                continue
            tds = row.find_all("td")
            if len(tds) >= 2:
                span = tds[1].find("span")
                if span:
                    price_text = span.get_text(strip=True).replace(",", "")
                    if price_text.isdigit():
                        return int(price_text)

        # Last
        for cell in soup.find_all(string=lambda t: t and t.strip() == "Last"):
            row = cell.find_parent("tr")
            if not row:
                continue
            tds = row.find_all("td")
            if len(tds) >= 2:
                span = tds[1].find("span")
                if span:
                    price_text = span.get_text(strip=True).replace(",", "")
                    if price_text.isdigit():
                        return int(price_text)

        # Sales history fallback
        for tbl in soup.find_all("table", class_="tbl-sales"):
            for td in tbl.find_all("td"):
                txt = td.get_text(strip=True).replace(",", "")
                if txt.isdigit() and len(txt) >= 2:
                    try:
                        val = int(txt)
                        if val >= 10:
                            return val
                    except ValueError:
                        pass

        return 0

    def get_cross_server_data(self, item_id: int | str):
        """
        Compare the item across all servers and compute summary stats.

        Returns:
            dict with cross-server price stats, or None if insufficient data.
        """
        from .servers import SERVERS  # expects a mapping {server_name: server_id}

        server_data: dict[str, dict] = {}
        price_list: list[int] = []

        for server_name, server_id in SERVERS.items():
            data = self.get_item_data(item_id, server_id)
            if not data or data.get("name") == "Unknown":
                continue
            server_data[server_name] = data
            if data.get("price", 0) > 0:
                price_list.append(data["price"])

        if len(server_data) < 2:
            return None  # need multiple servers observed
        if not price_list:
            return None  # no pricing at all

        servers_with_prices = {
            s: d for s, d in server_data.items() if d.get("price", 0) > 0
        }
        if len(servers_with_prices) < 2:
            return None

        prices = {s: d["price"] for s, d in servers_with_prices.items()}
        lowest_server = min(prices, key=prices.get)
        highest_server = max(prices, key=prices.get)

        lowest_price = prices[lowest_server]
        highest_price = prices[highest_server]
        average_price = sum(price_list) / len(price_list)

        base = server_data[lowest_server]

        return {
            "itemid": item_id,
            "name": base["name"],
            "category": base["category"],
            "lowest_price": lowest_price,
            "lowest_server": lowest_server,
            "highest_price": highest_price,
            "highest_server": highest_server,
            "average_price": average_price,
            "price_difference": highest_price - lowest_price,
            "server_count": len(servers_with_prices),  # with price
            "total_servers": len(server_data),         # all with data
            "server_data": server_data,                # full details
        }
