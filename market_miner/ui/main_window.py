"""
Main window for MarketMiner Pro (CustomTkinter)
"""

from __future__ import annotations

import csv
import os
import threading
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import suppress
from typing import Dict, List, Optional

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox

from .theme import ModernTheme
from .components import (
    ConfigurationPanel,
    ProgressTab,
    ResultsTab,
    CrossServerResultsTab,
)
from ..scraper import MarketMinerScraper
from ..servers import SERVERS
from ..config import load_config, save_config


class MarketMinerGUI:
    """Main GUI application for MarketMiner Pro using CustomTkinter."""

    def __init__(self, root: Optional[tk.Tk] = None):
        # --- Config / theme ---
        self._user_config: Dict[str, str] = load_config()
        self.theme = ModernTheme()
        self.theme.apply_theme()

        # --- Root window ---
        # If a root was passed, use it; otherwise create a CTk root.
        self.root: ctk.CTk = root if isinstance(root, ctk.CTk) else ctk.CTk()
        self.root.title("MarketMiner Pro - FFXI Auction House Tool")
        self.root.geometry("1100x800")
        self.root.minsize(900, 600)

        # --- Core state ---
        self.scraper = MarketMinerScraper()
        self.is_running = False
        self.executor: Optional[ThreadPoolExecutor] = None

        # --- UI refs (set in setup) ---
        self.config_panel: Optional[ConfigurationPanel] = None
        self.progress_tab: Optional[ProgressTab] = None
        self.results_tab: Optional[ResultsTab] = None
        self.cross_server_tab: Optional[CrossServerResultsTab] = None
        self.start_btn: Optional[ctk.CTkButton] = None
        self.stop_btn: Optional[ctk.CTkButton] = None
        self.status: Optional[ctk.CTkLabel] = None

        # Build UI
        self.setup_ui()

        # Restore last selections
        last_server = self._user_config.get("last_server")
        if last_server and last_server in SERVERS:
            self.config_panel.server_var.set(last_server)
            self.config_panel.selected_servers = [last_server]
            self.config_panel._update_server_display()

    # -----------------------------
    # UI construction
    # -----------------------------

    def setup_ui(self) -> None:
        """Create main layout and widgets."""
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # Left pane (controls)
        left_panel = ctk.CTkFrame(self.root)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        left_panel.grid_rowconfigure(3, weight=1)  # allow stretch
        self._setup_left_panel(left_panel)

        # Right pane (tabs)
        right_panel = ctk.CTkTabview(self.root)
        right_panel.grid(row=0, column=1, sticky="nsew",
                         padx=(10, 20), pady=20)
        self._setup_tabs(right_panel)

        # Status bar
        self.status = ctk.CTkLabel(
            self.root,
            text="🔵 Ready to start...",
            font=ctk.CTkFont(size=12),
            anchor="w",
        )
        self.status.grid(row=1, column=0, columnspan=2,
                         sticky="ew", padx=20, pady=(0, 5))
        
        # Attribution footer
        attribution = ctk.CTkLabel(
            self.root,
            text="Data sourced from FFXIAH.com | Use responsibly and respect their terms of service",
            font=ctk.CTkFont(size=10),
            text_color=("gray50", "gray60"),
            anchor="center",
        )
        attribution.grid(row=2, column=0, columnspan=2,
                        sticky="ew", padx=20, pady=(0, 20))

    def _setup_left_panel(self, left_panel: ctk.CTkFrame) -> None:
        """Controls: title, start/stop, configuration."""
        # Title + buttons
        title_frame = ctk.CTkFrame(left_panel)
        title_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 15))
        title_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            title_frame, text="⛏️ MarketMiner Pro", font=ctk.CTkFont(size=20, weight="bold")
        )
        title.grid(row=0, column=0, columnspan=2, pady=(15, 5))
        
        subtitle = ctk.CTkLabel(
            title_frame, text="Final Fantasy XI Auction House Data from FFXIAH.com", 
            font=ctk.CTkFont(size=11), text_color=("gray50", "gray60")
        )
        subtitle.grid(row=1, column=0, columnspan=2, pady=(0, 10))

        button_frame = ctk.CTkFrame(title_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(0, 15))

        self.start_btn = ctk.CTkButton(
            button_frame,
            text="▶️ Start Scraping",
            command=self.start_scraping,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40,
            width=140,
            fg_color=self.theme.colors["success"],
            hover_color=self.theme.colors["success_hover"],
        )
        self.start_btn.pack(side="left", padx=(10, 5), pady=10)

        self.stop_btn = ctk.CTkButton(
            button_frame,
            text="⏹️ Stop",
            command=self.stop_scraping,
            state="disabled",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40,
            width=100,
            fg_color=self.theme.colors["danger"],
            hover_color=self.theme.colors["danger_hover"],
        )
        self.stop_btn.pack(side="left", padx=(5, 10), pady=10)

        # Configuration panel
        self.config_panel = ConfigurationPanel(left_panel, self.theme)
        self.config_panel.create(1, 0, sticky="ew", padx=20, pady=(0, 15))

        # Spacer + grid weight
        spacer = ctk.CTkFrame(left_panel, height=20)
        spacer.grid(row=2, column=0, sticky="ew")
        left_panel.grid_columnconfigure(0, weight=1)

    def _setup_tabs(self, tabview: ctk.CTkTabview) -> None:
        """Create tabs and initialize their contents."""
        # Progress
        progress_tab = tabview.add("📊 Progress")
        self.progress_tab = ProgressTab(progress_tab, self.theme)
        self.progress_tab.create(progress_tab)

        # Results (per-server)
        results_tab = tabview.add("📋 Results")
        self.results_tab = ResultsTab(results_tab, self.theme)
        self.results_tab.create(results_tab)

        # Cross-server
        cross_server_tab = tabview.add("🌐 Cross-Server")
        self.cross_server_tab = CrossServerResultsTab(
            cross_server_tab, self.theme)
        self.cross_server_tab.create(cross_server_tab)


        tabview.set("📊 Progress")

    # -----------------------------
    # Helpers / UI actions
    # -----------------------------

    def _format_eta(self, seconds: float) -> str:
        """Format ETA in MM:SS or HH:MM:SS format"""
        if seconds <= 0 or seconds > 86400:  # Cap at 24 hours
            return "--:--"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    def _is_multi_server(self) -> bool:
        """True when 2+ servers are selected."""
        return len(self.config_panel.get_selected_servers()) > 1

    def _compute_comparison(self, item_id: int, server_data_list: List[dict], price_type: str = "individual") -> Optional[dict]:
        """
        Build a comparison record for a single item across selected servers.
        price_type: "individual" or "stack" to specify which prices to compare.
        """
        server_prices = {}
        
        for d in server_data_list:
            server = d["server"]
            if price_type == "stack":
                price = d.get("stack_price", 0)
            else:
                price = d.get("price", 0)
            
            if price > 0:
                server_prices[server] = price
        
        if len(server_prices) < 2:
            return None

        lowest_server = min(server_prices, key=server_prices.get)
        highest_server = max(server_prices, key=server_prices.get)

        lowest_price = server_prices[lowest_server]
        highest_price = server_prices[highest_server]
        average = sum(server_prices.values()) / len(server_prices)

        # Get base info from first available item
        base = server_data_list[0]
        item_name = base.get("name", "")
        if price_type == "stack":
            stackable_size = base.get("stackable", "No")
            if stackable_size != "No":
                item_name += f" (Stack x{stackable_size})"

        return {
            "itemid": item_id,
            "name": item_name,
            "category": base.get("category", ""),
            "lowest_price": lowest_price,
            "lowest_server": lowest_server,
            "highest_price": highest_price,
            "highest_server": highest_server,
            "average_price": average,
            "price_difference": highest_price - lowest_price,
            "server_count": len(server_prices),
        }


    def log(self, message: str, level: str = "info") -> None:
        """Log message (simplified - no UI logging)."""
        # Could add console logging here if needed
        pass

    # -----------------------------
    # Organized logging methods
    # -----------------------------

    def _log_scrape_start(self, server_ids: Dict[str, int], from_id: int, to_id: int, max_threads: int, output_file: str) -> None:
        """Log scraping startup information."""
        total_items = to_id - from_id + 1
        is_multi = len(server_ids) > 1
        
        if is_multi:
            self.log(f"🚀 Starting cross-server analysis on {len(server_ids)} servers")
            self.cross_server_tab.clear_results()
        else:
            server_name = next(iter(server_ids.keys()))
            self.log(f"🚀 Starting market scan on {server_name} server")

        self.log(f"📊 Checking {total_items:,} items (ID {from_id} to {to_id})")
        self.log(f"💾 Results will be saved to: {output_file}")
        self.log(f"⚡ Using {max_threads} concurrent connections")

    def _log_item_found(self, item_id: int, row: dict) -> None:
        """Log successful item discovery."""
        price_str = f"{row['price']:,} gil"
        category = row.get("category") or "Unknown"
        rarity = row.get("rarity", "")
        rarity_display = f" [{rarity}]" if rarity and rarity != "Common" else ""
        
        self.log(
            f"💰 {row['name']} - {price_str} in {category}{rarity_display}",
            "success"
        )

    def _log_item_skipped(self, item_id: int, name: str, reason: str) -> None:
        """Log skipped items with consistent format."""
        display_name = name if name != "Unknown" else ""
        if display_name:
            reason_friendly = {
                "non-sellable/non-tradeable": "not available for sale",
                "no price found": "no current market price",
                "failed to fetch or parse": "data unavailable"
            }.get(reason, reason)
            self.log(f"⏭️ {display_name} - {reason_friendly}", "warning")
        else:
            reason_display = {
                "no item name": "Item not found in database",
                "no price found": "No market data available", 
                "failed to fetch or parse": "Unable to retrieve data"
            }.get(reason, reason)
            self.log(f"⏭️ Item #{item_id} - {reason_display}", "warning")

    def _log_price_comparison(self, cmp_row: dict) -> None:
        """Log cross-server price comparison results."""
        diff = f"{cmp_row['price_difference']:,} gil"
        avg = f"{cmp_row['average_price']:,.0f} gil"
        low_price = f"{cmp_row['lowest_price']:,} gil"
        high_price = f"{cmp_row['highest_price']:,} gil"
        
        self.log(
            f"🔄 {cmp_row['name']} prices: {low_price} on {cmp_row['lowest_server']} → "
            f"{high_price} on {cmp_row['highest_server']} (avg: {avg}, profit: {diff})",
            "success"
        )

    def _log_completion(self, items_count: int, comparison_count: int, elapsed: float, output_file: str, cmp_file: str = None) -> None:
        """Log completion summary."""
        if items_count > 0:
            self.log(f"📁 Exported {items_count:,} items to {output_file}", "success")
        
        if comparison_count > 0 and cmp_file:
            self.log(f"📁 Saved {comparison_count:,} cross-server opportunities to {cmp_file}", "success")
        
        minutes = int(elapsed // 60)
        seconds = elapsed % 60
        if minutes > 0:
            time_str = f"{minutes}m {seconds:.0f}s"
        else:
            time_str = f"{elapsed:.1f}s"
        
        self.log(f"✅ Market analysis complete! Finished in {time_str}", "success")
        self.progress_tab.progress_var.set("Analysis Complete! 🎉")

    # -----------------------------
    # Start/stop + worker
    # -----------------------------

    def start_scraping(self) -> None:
        """Validate inputs, persist config, and start worker thread."""
        try:
            from_id = int(self.config_panel.from_var.get())
            to_id = int(self.config_panel.to_var.get())
            max_threads = int(self.config_panel.thread_var.get())

            if from_id >= to_id:
                messagebox.showerror(
                    "Error", "From ID must be less than To ID")
                return
            if not (1 <= max_threads <= 10):
                messagebox.showerror(
                    "Error", "Thread count must be between 1 and 10")
                return

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")
            return

        selected_servers = self.config_panel.get_selected_servers()
        if not selected_servers:
            messagebox.showerror("Error", "Select at least one server.")
            return

        # Persist last-used server
        self._user_config["last_server"] = selected_servers[0]
        save_config(self._user_config)

        # UI state
        self.is_running = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        threading.Thread(target=self.scrape_worker, daemon=True).start()

    def stop_scraping(self) -> None:
        """Signal the worker to stop and disable the Stop button."""
        self.is_running = False
        if self.executor:
            self.executor.shutdown(wait=False, cancel_futures=True)
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.log("🛑 Stopping market analysis...", "warning")

    def scrape_worker(self) -> None:
        """Background worker that coordinates scraping and saving."""
        try:
            from_id = int(self.config_panel.from_var.get())
            to_id = int(self.config_panel.to_var.get())
            max_threads = int(self.config_panel.thread_var.get())
            output_file = self.config_panel.get_output_file().strip() or "items.csv"

            # Skipped items file - single file for all runs
            skipped_path = os.path.join(os.path.dirname(
                output_file) or ".", "skipped_items.json")

            # Load existing skipped items to avoid re-checking them
            known_skipped = {}
            if os.path.exists(skipped_path):
                try:
                    with open(skipped_path, "r", encoding="utf-8") as f:
                        known_skipped = json.load(f) or {}
                    self.log(f"📋 Loaded {len(known_skipped)} previously skipped items")
                except Exception as e:
                    self.log(f"⚠️ Could not load skipped items: {e}", "warning")
                    known_skipped = {}

            def save_skip(item_id, name, reason):
                """Append/merge one skipped item into skipped_items.json."""
                try:
                    data = {}
                    if os.path.exists(skipped_path):
                        with open(skipped_path, "r", encoding="utf-8") as f:
                            data = json.load(f) or {}
                    key = str(item_id)
                    name = name or "Unknown"
                    entry = data.get(
                        key, {"itemid": item_id, "name": name, "reason": reason})

                    if entry.get("name", "Unknown") == "Unknown" and name != "Unknown":
                        entry["name"] = name

                    existing = entry.get("reason", "")
                    parts = [p.strip() for p in existing.split(
                        ";") if p.strip()] if existing else []
                    if reason not in parts:
                        parts.append(reason)
                    entry["reason"] = "; ".join(parts)

                    data[key] = entry
                    os.makedirs(os.path.dirname(skipped_path)
                                or ".", exist_ok=True)
                    with open(skipped_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False,
                                  indent=2, sort_keys=True)
                except Exception as e:
                    self.log(f"⚠️ Could not save skip info for item #{item_id}: {e}", "error")

            selected_servers = self.config_panel.get_selected_servers()
            is_multi = self._is_multi_server()

            # Validate server names -> IDs
            server_ids: Dict[str, int] = {}
            for name in selected_servers:
                if name in SERVERS:
                    server_ids[name] = SERVERS[name]
                else:
                    self.log(f"❌ Server '{name}' not recognized", "error")

            if not server_ids:
                messagebox.showerror("Error", "No valid servers selected.")
                return

            total_items = to_id - from_id + 1
            total_jobs = total_items * max(1, len(server_ids))
            processed_jobs = 0
            found_items = 0
            start_ts = time.time()

            # Reset UI progress
            self.progress_tab.progress_bar.set(0)
            
            # Set scraping status
            if is_multi:
                self.progress_tab.progress_var.set(f"Scraping {len(server_ids)} servers...")
            else:
                server_name = list(server_ids.keys())[0]
                self.progress_tab.progress_var.set(f"Scraping {server_name}...")
            
            # Log startup information
            self._log_scrape_start(server_ids, from_id, to_id, max_threads, output_file)

            # Data sinks
            items_data: List[dict] = []
            comparison_data: List[dict] = []
            per_item_bucket = {i: [] for i in range(
                from_id, to_id + 1)} if is_multi else None

            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                self.executor = executor

                # Submit tasks
                if is_multi:
                    # For multi-server: validate each item ID exists first, then query all servers
                    validated_items = set()
                    validation_server = next(iter(server_ids.items()))  # Pick first server for validation
                    val_sname, val_sid = validation_server
                    
                    # Phase 1: Filter out known skipped items, then validate remaining
                    items_to_check = []
                    for item_id in range(from_id, to_id + 1):
                        if str(item_id) in known_skipped:
                            # Already know this item should be skipped
                            skip_info = known_skipped[str(item_id)]
                            self._log_item_skipped(item_id, skip_info.get("name", "Unknown"), f"previously skipped: {skip_info.get('reason', 'unknown')}")
                            processed_jobs += 1
                        else:
                            items_to_check.append(item_id)
                    
                    self.log(f"⏭️ Auto-skipped {len(range(from_id, to_id + 1)) - len(items_to_check)} previously known items")
                    
                    validation_futures = {
                        executor.submit(self.scraper.get_item_data, item_id, val_sid): item_id
                        for item_id in items_to_check
                    }
                    
                    for val_fut in as_completed(validation_futures):
                        if not self.is_running:
                            break
                        
                        item_id = validation_futures[val_fut]
                        processed_jobs += 1
                        try:
                            result = val_fut.result()
                            if result and result.get("name") != "Unknown":
                                # Check if item is sellable - if not, skip all servers
                                rarity = result.get("rarity", "")
                                if any(flag in rarity for flag in ["Exclusive", "No Auction", "No Sale"]):
                                    # Item exists but not sellable - skip all servers
                                    self._log_item_skipped(item_id, result.get("name", "Unknown"), "non-sellable/non-tradeable")
                                    save_skip(item_id, result.get("name", "Unknown"), "non-sellable/non-tradeable")
                                    continue
                                
                                validated_items.add(item_id)
                                # Process the validation server result immediately
                                row = dict(result)
                                row["server"] = val_sname
                                if row.get("price", 0) > 0:
                                    found_items += 1
                                    self._log_item_found(item_id, row)
                                    self.results_tab.add_row(row)
                                    items_data.append({
                                        "itemid": row.get("itemid", ""),
                                        "name": row.get("name", ""),
                                        "price": row.get("price", 0),
                                        "stack_price": row.get("stack_price", 0),
                                        "sold_per_day": row.get("sold_per_day", 0),
                                        "stack_sold_per_day": row.get("stack_sold_per_day", 0),
                                        "category": row.get("category", ""),
                                        "stackable": row.get("stackable", "No"),
                                        "server": val_sname
                                    })
                                    per_item_bucket[item_id].append(row)
                                else:
                                    rarity = row.get("rarity", "")
                                    if any(flag in rarity for flag in ["Exclusive", "No Auction", "No Sale"]):
                                        skip_reason = "non-sellable/non-tradeable"
                                    else:
                                        skip_reason = "no price found"
                                    self._log_item_skipped(item_id, row.get("name", "Unknown"), skip_reason)
                                    save_skip(item_id, row.get("name", "Unknown"), skip_reason)
                            else:
                                # Invalid item ID - skip entirely
                                self._log_item_skipped(item_id, "Unknown", "item does not exist")
                                save_skip(item_id, "Unknown", "item does not exist")
                        except Exception as e:
                            self._log_item_skipped(item_id, "Unknown", f"validation error: {e}")
                            save_skip(item_id, "Unknown", f"validation error: {e}")
                        
                        # Update progress during validation
                        time.sleep(0.05)
                        current_total = total_items + len(validated_items) * (len(server_ids) - 1)
                        progress = processed_jobs / max(current_total, processed_jobs)
                        
                        # Update progress components individually
                        self.progress_tab.progress_bar.set(progress)
                        self.progress_tab.processed_label.configure(text=f"{processed_jobs}/{current_total}")
                        
                        elapsed = time.time() - start_ts
                        rate = (processed_jobs / elapsed * 60) if elapsed > 0 else 0
                        self.progress_tab.rate_label.configure(text=f"{rate:.1f}/min")
                        
                        # Calculate ETA
                        remaining_jobs = current_total - processed_jobs
                        if rate > 0 and remaining_jobs > 0:
                            eta_seconds = (remaining_jobs / rate) * 60
                            eta_text = self._format_eta(eta_seconds)
                        else:
                            eta_text = "--:--"
                        self.progress_tab.eta_label.configure(text=eta_text)
                    
                    # Phase 2: Query remaining servers for validated items only
                    remaining_servers = [(sname, sid) for sname, sid in server_ids.items() if sname != val_sname]
                    if validated_items and remaining_servers:
                        fut_to_key = {
                            executor.submit(self.scraper.get_item_data, item_id, sid): (item_id, sname)
                            for item_id in validated_items
                            for sname, sid in remaining_servers
                        }
                    else:
                        fut_to_key = {}  # No additional queries needed
                    
                    # Update total jobs count: validation phase + remaining servers for validated items  
                    total_jobs = total_items + len(validated_items) * (len(server_ids) - 1)
                else:
                    # Single server mode - also skip known items
                    sname, sid = next(iter(server_ids.items()))
                    
                    items_to_check = []
                    for item_id in range(from_id, to_id + 1):
                        if str(item_id) in known_skipped:
                            skip_info = known_skipped[str(item_id)]
                            self._log_item_skipped(item_id, skip_info.get("name", "Unknown"), f"previously skipped: {skip_info.get('reason', 'unknown')}")
                            processed_jobs += 1
                        else:
                            items_to_check.append(item_id)
                    
                    if items_to_check != list(range(from_id, to_id + 1)):
                        self.log(f"⏭️ Auto-skipped {len(range(from_id, to_id + 1)) - len(items_to_check)} previously known items")
                    
                    fut_to_key = {
                        executor.submit(self.scraper.get_item_data, item_id, sid): (item_id, sname)
                        for item_id in items_to_check
                    }

                for fut in as_completed(fut_to_key):
                    if not self.is_running:
                        break

                    item_id, sname = fut_to_key[fut]
                    processed_jobs += 1

                    try:
                        result = fut.result()
                        # Be polite to the target site
                        time.sleep(0.05)

                        if result:

                            row = dict(result)
                            row["server"] = sname

                            # Skip unknown-name rows for display
                            if row.get("name") == "Unknown":
                                    self._log_item_skipped(item_id, "Unknown", "no item name")
                                    save_skip(item_id, "Unknown", "no item name")
                                    continue

                            # Only process items with valid prices
                            if row.get("price", 0) > 0:
                                found_items += 1
                                self._log_item_found(item_id, row)
                                # Show per-server result
                                self.results_tab.add_row(row)
                            else:
                                    # Determine skip reason based on item properties
                                    rarity = row.get("rarity", "")
                                    if any(flag in rarity for flag in ["Exclusive", "No Auction", "No Sale"]):
                                        skip_reason = "non-sellable/non-tradeable"
                                    else:
                                        skip_reason = "no price found"
                                    
                                    self._log_item_skipped(item_id, row.get("name","Unknown"), skip_reason)
                                    save_skip(item_id, row.get("name","Unknown"), skip_reason)
                                    continue

                            # Accumulate for CSV
                            items_data.append(
                                {
                                    "itemid": row.get("itemid", ""),
                                    "name": row.get("name", ""),
                                    "price": row.get("price", ""),
                                    "stack_price": row.get("stack_price", ""),
                                    "sold_per_day": row.get("sold_per_day", ""),
                                    "stack_sold_per_day": row.get("stack_sold_per_day", ""),
                                    "category": row.get("category", ""),
                                    "stackable": row.get("stackable", "No"),
                                    "server": sname,
                                }
                            )

                            # Cross-server compare once all server rows for this item are in
                            if is_multi:
                                per_item_bucket[item_id].append(row)
                                if len(per_item_bucket[item_id]) == len(server_ids):
                                    # Generate comparison for individual prices
                                    cmp_row = self._compute_comparison(
                                        item_id, per_item_bucket[item_id], "individual")
                                    if cmp_row:
                                        self.cross_server_tab.add_comparison_row(cmp_row)
                                        comparison_data.append(cmp_row)
                                        self._log_price_comparison(cmp_row)
                                    
                                    # Generate separate comparison for stack prices if available
                                    stack_cmp_row = self._compute_comparison(
                                        item_id, per_item_bucket[item_id], "stack")
                                    if stack_cmp_row:
                                        self.cross_server_tab.add_comparison_row(stack_cmp_row)
                                        comparison_data.append(stack_cmp_row)
                                        self._log_price_comparison(stack_cmp_row)
                        else:
                            self._log_item_skipped(item_id, "Unknown", "failed to fetch or parse")
                            save_skip(item_id, "Unknown", "failed to fetch or parse")

                        # Progress UI
                        elapsed = time.time() - start_ts
                        rate = (processed_jobs / elapsed) * \
                            60 if elapsed > 0 else 0
                        self.progress_tab.progress_bar.set(
                            processed_jobs / total_jobs)
                        self.progress_tab.processed_label.configure(
                            text=f"{processed_jobs}/{total_jobs}")
                        self.progress_tab.rate_label.configure(
                            text=f"{rate:.1f}/min")
                        
                        # Calculate and display ETA
                        remaining_jobs = total_jobs - processed_jobs
                        if rate > 0 and remaining_jobs > 0:
                            eta_seconds = (remaining_jobs / rate) * 60
                            eta_text = self._format_eta(eta_seconds)
                        else:
                            eta_text = "--:--"
                        self.progress_tab.eta_label.configure(text=eta_text)

                    except Exception as e:
                        self.log(
                            f"Error processing item {item_id} ({sname}): {e}", "error")

            # --- Save CSVs ---

            # 1) Per-server rows: merge by (itemid, server)
            if items_data:
                fieldnames = [
                    "itemid",
                    "name",
                    "price",
                    "stack_price",
                    "sold_per_day",
                    "stack_sold_per_day",
                    "category",
                    "stackable",
                    "server",
                ]
                existing_rows = []
                if os.path.exists(output_file):
                    with suppress(Exception):
                        with open(output_file, "r", encoding="utf-8", newline="") as f:
                            existing_rows = list(csv.DictReader(f))

                def _key(row: dict) -> tuple[str, str]:
                    return (str(row.get("itemid", "")), str(row.get("server", "")))

                merged = {_key(r): r for r in existing_rows}
                for r in items_data:
                    merged[_key(r)] = r

                os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
                with open(output_file, "w", encoding="utf-8", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=fieldnames)
                    w.writeheader()
                    w.writerows(merged.values())

            # 2) Cross-server comparison (only if multi)
            cmp_file = None
            if is_multi and comparison_data:
                # Extract timestamp from output_file to keep filenames consistent
                base_name = os.path.basename(output_file).replace("items_", "").replace(".csv", "")
                cmp_file = f"output/cross_server_items_{base_name}.csv"
                cmp_fields = [
                    "itemid",
                    "name",
                    "category",
                    "lowest_price",
                    "lowest_server",
                    "highest_price",
                    "highest_server",
                    "average_price",
                    "price_difference",
                    "server_count",
                ]
                os.makedirs(os.path.dirname(cmp_file) or ".", exist_ok=True)
                with open(cmp_file, "w", encoding="utf-8", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=cmp_fields)
                    w.writeheader()
                    for row in comparison_data:
                        r = dict(row)
                        r["average_price"] = round(r.get("average_price", 0))
                        w.writerow(r)
            elapsed = time.time() - start_ts
            self.progress_tab.progress_bar.set(1.0)
            
            # Log completion summary
            self._log_completion(
                len(items_data), 
                len(comparison_data) if is_multi else 0, 
                elapsed, 
                output_file, 
                cmp_file
            )

        except Exception as e:
            self.log(f"❌ Analysis failed: {e}", "error")
            messagebox.showerror("Error", f"Scraping failed: {e}")
        finally:
            self.is_running = False
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.executor = None
