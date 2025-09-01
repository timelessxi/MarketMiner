"""
Main window for MarketMiner Pro using CustomTkinter
"""



import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import csv
import threading
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from .theme import ModernTheme
from .components import ConfigurationPanel, ProgressTab, ResultsTab, CrossServerResultsTab, LogTab
from ..scraper import MarketMinerScraper
from ..servers import SERVERS
from ..config import load_config, save_config


class MarketMinerGUI:
    """Main GUI application for MarketMiner Pro using CustomTkinter"""

    def __init__(self, root):
        # Load user config
        self._user_config = load_config()
        # Initialize theme first
        self.theme = ModernTheme()
        self.theme.apply_theme()

        # Initialize CustomTkinter window directly
        self.root = ctk.CTk()
        self.root.title("🎮 MarketMiner Pro")
        self.root.geometry("1100x800")
        self.root.minsize(900, 600)

        # Initialize scraper
        self.scraper = MarketMinerScraper()
        self.is_running = False
        self.executor = None

        # Initialize UI components
        self.config_panel = None
        self.options_panel = None
        self.progress_tab = None
        self.results_tab = None
        self.cross_server_tab = None
        self.log_tab = None

        # Control buttons
        self.start_btn = None
        self.stop_btn = None
        self.status = None

        self.setup_ui()

        # Restore last used server and output path if available
        last_server = self._user_config.get("last_server")
        if last_server and last_server in SERVERS:
            self.config_panel.server_var.set(last_server)
            self.config_panel.selected_servers = [last_server]
            self.config_panel._update_server_display()
        last_output = self._user_config.get("output_path")
        if last_output:
            self.config_panel.output_file_var.set(last_output)

    def setup_ui(self):
        """Setup the main UI layout using CustomTkinter"""
        # Configure root grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # LEFT PANEL: Controls
        left_panel = ctk.CTkFrame(self.root)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        # Make space between panels flexible
        left_panel.grid_rowconfigure(3, weight=1)

        # Setup left panel components
        self._setup_left_panel(left_panel)

        # RIGHT PANEL: Tabbed interface
        right_panel = ctk.CTkTabview(self.root)
        right_panel.grid(row=0, column=1, sticky="nsew",
                         padx=(10, 20), pady=20)

        # Setup tabs
        self._setup_tabs(right_panel)

        # Status bar
        self.status = ctk.CTkLabel(self.root, text="🔵 Ready to start...",
                                   font=ctk.CTkFont(size=12),
                                   anchor="w")
        self.status.grid(row=1, column=0, columnspan=2,
                         sticky="ew", padx=20, pady=(0, 20))

    def _setup_left_panel(self, left_panel):
        """Setup the left control panel"""
        # Title with action buttons
        title_frame = ctk.CTkFrame(left_panel)
        title_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 15))
        title_frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(title_frame, text="⛏️ MarketMiner Pro",
                             font=ctk.CTkFont(size=20, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, pady=(15, 10))

        # Action buttons
        button_frame = ctk.CTkFrame(title_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(0, 15))

        self.start_btn = ctk.CTkButton(
            button_frame, text="▶️ Start Scraping",
            command=self.start_scraping,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40, width=140,
            fg_color=self.theme.colors['success'],
            hover_color=self.theme.colors['success_hover'])
        self.start_btn.pack(side='left', padx=(10, 5), pady=10)

        self.stop_btn = ctk.CTkButton(
            button_frame, text="⏹️ Stop",
            command=self.stop_scraping,
            state="disabled",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40, width=100,
            fg_color=self.theme.colors['danger'],
            hover_color=self.theme.colors['danger_hover'])
        self.stop_btn.pack(side='left', padx=(5, 10), pady=10)

        # Configuration panel
        self.config_panel = ConfigurationPanel(left_panel, self.theme)
        self.config_panel.create(1, 0, sticky="ew", padx=20, pady=(0, 15))

        # Connect browse buttons
        self.config_panel.browse_btn.configure(command=self.browse_output_file)
        self.config_panel.cross_server_browse_btn.configure(
            command=self.browse_cross_server_output_file)

    def _setup_left_panel(self, left_panel):
        # Title with action buttons
        title_frame = ctk.CTkFrame(left_panel)
        title_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 15))
        title_frame.grid_columnconfigure(0, weight=1)
        title = ctk.CTkLabel(title_frame, text="⛏️ MarketMiner Pro",
                             font=ctk.CTkFont(size=20, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, pady=(15, 10))
        button_frame = ctk.CTkFrame(title_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(0, 15))
        self.start_btn = ctk.CTkButton(
            button_frame, text="▶️ Start Scraping",
            command=self.start_scraping,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40, width=140,
            fg_color=self.theme.colors['success'],
            hover_color=self.theme.colors['success_hover'])
        self.start_btn.pack(side='left', padx=(10, 5), pady=10)
        self.stop_btn = ctk.CTkButton(
            button_frame, text="⏹️ Stop",
            command=self.stop_scraping,
            state="disabled",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40, width=100,
            fg_color=self.theme.colors['danger'],
            hover_color=self.theme.colors['danger_hover'])
        self.stop_btn.pack(side='left', padx=(5, 10), pady=10)
        self.config_panel = ConfigurationPanel(left_panel, self.theme)
        self.config_panel.create(1, 0, sticky="ew", padx=20, pady=(0, 15))
        self.config_panel.browse_btn.configure(command=self.browse_output_file)
        # Spacer
        spacer = ctk.CTkFrame(left_panel, height=20)
        spacer.grid(row=2, column=0, sticky="ew")
        # Configure grid weights
        left_panel.grid_columnconfigure(0, weight=1)

    def _setup_tabs(self, tabview):
        """Setup the tabbed interface"""
        # Progress tab
        progress_tab = tabview.add("📊 Progress")
        self.progress_tab = ProgressTab(progress_tab, self.theme)
        self.progress_tab.create(progress_tab)

        # Results tab
        results_tab = tabview.add("📋 Results")
        self.results_tab = ResultsTab(results_tab, self.theme)
        self.results_tab.create(results_tab)

        # Cross-server comparison tab
        cross_server_tab = tabview.add("🌐 Cross-Server")
        self.cross_server_tab = CrossServerResultsTab(
            cross_server_tab, self.theme)
        self.cross_server_tab.create(cross_server_tab)

        # Log tab
        log_tab = tabview.add("📝 Activity Log")
        self.log_tab = LogTab(log_tab, self.theme)
        self.log_tab.create(log_tab)

        # Set default tab
        tabview.set("📊 Progress")

    def _is_multi_server(self) -> bool:
        """Multi-server mode when the user selected 2+ servers."""
        return len(self.config_panel.get_selected_servers()) > 1

    def _compute_comparison(self, item_id: int, server_data_list: list):
        """
        Build a comparison dict limited to the user's selected servers.
        server_data_list: list of dicts returned by scraper.get_item_data (plus injected 'server')
        """
        # Keep only rows with a positive price
        priced = [d for d in server_data_list if d.get('price', 0) > 0]
        if len(priced) < 2:
            return None

        prices = {d['server']: d['price'] for d in priced}
        lowest_server = min(prices, key=prices.get)
        highest_server = max(prices, key=prices.get)
        lowest_price = prices[lowest_server]
        highest_price = prices[highest_server]
        avg = sum(prices.values()) / len(prices)

        base = priced[0]
        return {
            'itemid': item_id,
            'name': base.get('name', ''),
            'category': base.get('category', ''),
            'lowest_price': lowest_price,
            'lowest_server': lowest_server,
            'highest_price': highest_price,
            'highest_server': highest_server,
            'average_price': avg,
            'price_difference': highest_price - lowest_price,
            'server_count': len(priced),
        }

    def browse_output_file(self):
        """Open directory dialog to select output folder for CSV files"""
        import os
        default_dir = "output"
        # Try to use the current folder if set
        current = self.config_panel.output_file_var.get()
        if current:
            current_dir = os.path.dirname(current)
            if os.path.isdir(current_dir):
                default_dir = current_dir
        folder = filedialog.askdirectory(title="Select Output Folder", initialdir=default_dir)
        if folder:
            output_file = os.path.join(folder, "items.csv")
            cross_server_file = os.path.join(folder, "cross_server_items.csv")
            self.config_panel.output_file_var.set(output_file)
            self.config_panel.cross_server_output_var.set(cross_server_file)
            # Update folder display
            if hasattr(self.config_panel, "output_folder_var"):
                self.config_panel.output_folder_var.set(folder)
            # Save output folder to config
            self._user_config["output_path"] = output_file
            save_config(self._user_config)

    def browse_cross_server_output_file(self):
        """Open directory dialog to select output folder for CSV files (syncs both outputs)"""
        self.browse_output_file()

    def log(self, message, level="info"):
        """Add message to log with status updates"""
        self.log_tab.log(message, level)

        # Update progress tab status
        self.progress_tab.progress_var.set(message)

        # Update status bar with emoji
        status_emoji = "🟢" if level == "success" else "🔴" if level == "error" else "🟡" if level == "warning" else "🔵"
        self.status.configure(text=f"{status_emoji} {message}")

        # Force UI update
        self.root.update_idletasks()

    def start_scraping(self):
        """Start the scraping process"""
        try:
            # Validate inputs
            from_id = int(self.config_panel.from_var.get())
            to_id = int(self.config_panel.to_var.get())
            max_threads = int(self.config_panel.thread_var.get())

            if from_id >= to_id:
                messagebox.showerror(
                    "Error", "From ID must be less than To ID")
                return
            if max_threads < 1 or max_threads > 10:
                messagebox.showerror(
                    "Error", "Thread count must be between 1 and 10")
                return

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")
            return

        # Save current server and output path to config
        selected_servers = self.config_panel.get_selected_servers()
        if selected_servers:
            self._user_config["last_server"] = selected_servers[0]
        self._user_config["output_path"] = self.config_panel.get_output_file()
        save_config(self._user_config)

        # Update UI state
        self.is_running = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        # Start scraping thread
        threading.Thread(target=self.scrape_worker, daemon=True).start()

    def stop_scraping(self):
        """Stop the scraping process"""
        self.is_running = False
        if self.executor:
            self.executor.shutdown(wait=False)
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.log("Stopping scraper...", "warning")

    def scrape_worker(self):
        """Main scraping worker thread (now respects multi-select servers)"""
        try:
            from_id = int(self.config_panel.from_var.get())
            to_id = int(self.config_panel.to_var.get())
            max_threads = int(self.config_panel.thread_var.get())
            output_file = self.config_panel.get_output_file()

            selected_servers = self.config_panel.get_selected_servers()
            is_multi = len(selected_servers) > 1

            # Resolve server IDs up front
            server_ids = {}
            for name in selected_servers:
                try:
                    server_ids[name] = SERVERS[name]
                except KeyError:
                    self.log(f"Unknown server '{name}'", "error")

            if not server_ids:
                messagebox.showerror("Error", "No valid servers selected.")
                return

            total_items = to_id - from_id + 1
            total_jobs = total_items * max(1, len(server_ids))
            processed_jobs = 0
            found_items = 0
            start_time = time.time()

            # Reset/prepare UI
            self.progress_tab.progress_bar.set(0)
            if is_multi:
                self.log(
                    f"Starting multi-server scrape across {len(server_ids)} servers")
                self.cross_server_tab.clear_results()
            else:
                one = next(iter(server_ids.keys()))
                self.log(f"Starting scrape: {one} (ID: {server_ids[one]})")

            self.log(f"Range: {from_id} to {to_id} ({total_items} items)")
            self.log(f"Output: {output_file}")
            self.log(f"Threads: {max_threads}")

            # Data sinks
            items_data = []          # per-server rows for items.csv
            comparison_data = []     # per-item comparison rows (multi only)

            # Accumulator to know when we've seen all servers for an item
            per_item_bucket = {i: [] for i in range(
                from_id, to_id + 1)} if is_multi else None

            from concurrent.futures import ThreadPoolExecutor, as_completed
            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                self.executor = executor

                # Submit jobs (per item per server in multi mode)
                if is_multi:
                    fut_to_key = {
                        executor.submit(self.scraper.get_item_data, item_id, sid): (item_id, sname)
                        for item_id in range(from_id, to_id + 1)
                        for sname, sid in server_ids.items()
                    }
                else:
                    # Single server
                    sname, sid = next(iter(server_ids.items()))
                    fut_to_key = {
                        executor.submit(self.scraper.get_item_data, item_id, sid): (item_id, sname)
                        for item_id in range(from_id, to_id + 1)
                    }

                for fut in as_completed(fut_to_key):
                    if not self.is_running:
                        break

                    item_id, sname = fut_to_key[fut]
                    processed_jobs += 1

                    try:
                        result = fut.result()
                        # Always be nice to the site
                        time.sleep(0.05)

                        if result:
                            result = dict(result)
                            # annotate for the table & CSV
                            result['server'] = sname

                            # Skip items with unknown name for all outputs except cross-server
                            if result.get('name') == 'Unknown':
                                self.log(
                                    f"Filtered: {result.get('name', 'Unknown')} (ID: {item_id}) - excluded by filters", "warning")
                                continue

                            # Show in per-server Results table
                            self.results_tab.add_row(result)

                            # Count “found” only if it has a nonzero price
                            if result.get('price', 0) > 0:
                                found_items += 1
                                price_str = f"{result['price']:,}"
                                cat = result.get('category') or "Unknown"
                                rare = result.get('rarity', '')
                                rare_disp = f" [{rare}]" if rare and rare != 'Common' else ''
                                self.log(
                                    f"Found: {result['name']} (ID: {item_id}, Price: {price_str}, Cat: {cat}{rare_disp})", "success")
                            else:
                                self.log(
                                    f"Filtered: {result.get('name', 'Unknown')} (ID: {item_id}) - excluded by filters", "warning")

                            # Add to per-server CSV dataset
                            items_data.append({
                                'itemid': result.get('itemid', ''),
                                'name': result.get('name', ''),
                                'price': result.get('price', ''),
                                'stack_price': result.get('stack_price', ''),
                                'sold_per_day': result.get('sold_per_day', ''),
                                'stack_sold_per_day': result.get('stack_sold_per_day', ''),
                                'category': result.get('category', ''),
                                'stackable': result.get('stackable', 'No'),
                                'server': sname
                            })

                            # Multi: accumulate and emit a comparison row once we have all servers for the item
                            if is_multi:
                                per_item_bucket[item_id].append(result)
                                if len(per_item_bucket[item_id]) == len(server_ids):
                                    cmp_row = self._compute_comparison(
                                        item_id, per_item_bucket[item_id])
                                    if cmp_row:
                                        self.cross_server_tab.add_comparison_row(
                                            cmp_row)
                                        comparison_data.append(cmp_row)
                                        diff = f"{cmp_row['price_difference']:,}"
                                        avg = f"{cmp_row['average_price']:,.0f}"
                                        self.log(
                                            f"Price Compare: {cmp_row['name']} - "
                                            f"Low: {cmp_row['lowest_server']} ({cmp_row['lowest_price']:,}) | "
                                            f"High: {cmp_row['highest_server']} ({cmp_row['highest_price']:,}) | "
                                            f"Avg: {avg} | Diff: {diff} ({cmp_row['server_count']} servers)",
                                            "success"
                                        )

                        # Update progress UI
                        elapsed = time.time() - start_time
                        rate = (processed_jobs / elapsed) * \
                            60 if elapsed > 0 else 0
                        self.progress_tab.progress_bar.set(
                            processed_jobs / total_jobs)
                        self.progress_tab.processed_label.configure(
                            text=f"{processed_jobs}/{total_jobs}")
                        self.progress_tab.found_label.configure(
                            text=str(found_items))
                        self.progress_tab.rate_label.configure(
                            text=f"{rate:.1f}/min")
                        self.progress_tab.progress_var.set(
                            f"Processing item {item_id}...")

                    except Exception as e:
                        self.log(
                            f"Error processing item {item_id} ({sname}): {e}", "error")

            # --- Save CSVs ---
            import csv
            import os

            # 1) Per-server rows
            if items_data:
                fieldnames = ['itemid', 'name', 'price', 'stack_price', 'sold_per_day',
                              'stack_sold_per_day', 'category', 'stackable', 'server']
                # Merge with existing rows by (itemid, server)
                existing_rows = []
                if os.path.exists(output_file):
                    try:
                        with open(output_file, 'r', encoding='utf-8', newline='') as f:
                            existing_rows = list(csv.DictReader(f))
                    except Exception:
                        pass

                def key(row): return (str(row.get('itemid', '')),
                                      str(row.get('server', '')))
                merged = {key(r): r for r in existing_rows}
                for r in items_data:
                    merged[key(r)] = r

                with open(output_file, 'w', encoding='utf-8', newline='') as f:
                    w = csv.DictWriter(f, fieldnames=fieldnames)
                    w.writeheader()
                    w.writerows(merged.values())

                self.log(
                    f"Saved {len(items_data)} rows to {output_file}", "success")

            # 2) Multi-server comparison rows (optional, only when multi)
            if is_multi and comparison_data:
                cmp_file = self.config_panel.cross_server_output_var.get(
                ).strip() or "cross_server_items.csv"
                cmp_fields = ['itemid', 'name', 'category', 'lowest_price', 'lowest_server',
                              'highest_price', 'highest_server', 'average_price', 'price_difference', 'server_count']
                with open(cmp_file, 'w', encoding='utf-8', newline='') as f:
                    w = csv.DictWriter(f, fieldnames=cmp_fields)
                    w.writeheader()
                    for row in comparison_data:
                        row = dict(row)
                        row['average_price'] = round(
                            row.get('average_price', 0))
                        w.writerow(row)
                self.log(
                    f"Saved {len(comparison_data)} price comparisons to {cmp_file}", "success")

            elapsed = time.time() - start_time
            self.log(f"Scraping completed in {elapsed:.1f} seconds", "success")
            self.progress_tab.progress_var.set("Completed! 🎉")

        except Exception as e:
            self.log(f"Scraping error: {e}", "error")
            messagebox.showerror("Error", f"Scraping failed: {e}")
        finally:
            self.is_running = False
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.executor = None
