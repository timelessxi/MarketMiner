"""
Main window for MarketMiner Pro using CustomTkinter
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import csv
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from .theme import ModernTheme
from .components import ConfigurationPanel, ProgressTab, ResultsTab, CrossServerResultsTab, LogTab
from ..scraper import MarketMinerScraper
from ..servers import SERVERS


class MarketMinerGUI:
    """Main GUI application for MarketMiner Pro using CustomTkinter"""
    
    def __init__(self, root):
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
    
    def setup_ui(self):
        """Setup the main UI layout using CustomTkinter"""
        # Configure root grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        # LEFT PANEL: Controls
        left_panel = ctk.CTkFrame(self.root)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        left_panel.grid_rowconfigure(3, weight=1)  # Make space between panels flexible
        
        # Setup left panel components
        self._setup_left_panel(left_panel)
        
        # RIGHT PANEL: Tabbed interface
        right_panel = ctk.CTkTabview(self.root)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=20)
        
        # Setup tabs
        self._setup_tabs(right_panel)
        
        # Status bar
        self.status = ctk.CTkLabel(self.root, text="🔵 Ready to start...",
                                  font=ctk.CTkFont(size=12),
                                  anchor="w")
        self.status.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 20))
    
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
        self.config_panel.cross_server_browse_btn.configure(command=self.browse_cross_server_output_file)
        
    # Spacer
    # Spacer

    def _setup_left_panel(self, left_panel):
        # Title with action buttons
        title_frame = ctk.CTkFrame(left_panel)
        title_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 15))
        title_frame.grid_columnconfigure(0, weight=1)
        title = ctk.CTkLabel(title_frame, text="⛏️ MarketMiner Pro", font=ctk.CTkFont(size=20, weight="bold"))
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
        self.cross_server_tab = CrossServerResultsTab(cross_server_tab, self.theme)
        self.cross_server_tab.create(cross_server_tab)
        
        # Log tab
        log_tab = tabview.add("📝 Activity Log")
        self.log_tab = LogTab(log_tab, self.theme)
        self.log_tab.create(log_tab)
        
        # Set default tab
        tabview.set("📊 Progress")
    
    def browse_output_file(self):
        """Open file dialog to select output file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.config_panel.output_file_var.set(filename)
    
    def browse_cross_server_output_file(self):
        """Open file dialog to select cross-server output file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Select Cross-Server Output File"
        )
        if filename:
            self.config_panel.cross_server_output_var.set(filename)
    
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
                messagebox.showerror("Error", "From ID must be less than To ID")
                return
            
            if max_threads < 1 or max_threads > 10:
                messagebox.showerror("Error", "Thread count must be between 1 and 10")
                return
        
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")
            return
        
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
        """Main scraping worker thread"""
        try:
            # Get configuration
            from_id = int(self.config_panel.from_var.get())
            to_id = int(self.config_panel.to_var.get())
            max_threads = int(self.config_panel.thread_var.get())
            output_file = self.config_panel.get_output_file()
            
            # Check if cross-server analysis is enabled
            is_cross_server = self.config_panel.cross_server_var.get()
            
            if not is_cross_server:
                server_name = self.config_panel.server_var.get()
                server_id = SERVERS[server_name]
            
            total_items = to_id - from_id + 1
            processed = 0
            found_items = 0
            start_time = time.time()
            
            # Initialize progress bar
            self.progress_tab.progress_bar.set(0)
            
            if is_cross_server:
                self.log("Starting cross-server analysis: ALL SERVERS")
                self.log(f"Analyzing across {len(SERVERS)} servers")
                # Clear cross-server results
                self.cross_server_tab.clear_results()
            else:
                self.log(f"Starting scrape: {server_name} (ID: {server_id})")
            
            self.log(f"Range: {from_id} to {to_id} ({total_items} items)")
            self.log(f"Output: {output_file}")
            self.log(f"Threads: {max_threads}")
            
            # Prepare CSV fieldnames
            fieldnames = [
                'itemid', 'name', 'price', 'stack_price', 'sold_per_day', 'stack_sold_per_day', 'category', 'stackable', 'server',
            ]
            items_data = []
            cross_server_data = []  # For cross-server arbitrage opportunities
            
            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                self.executor = executor
                
                # Submit all tasks - different for cross-server vs single server
                if is_cross_server:
                    future_to_id = {
                        executor.submit(self.scraper.get_cross_server_data, item_id): item_id 
                        for item_id in range(from_id, to_id + 1)
                    }
                else:
                    future_to_id = {
                        executor.submit(self.scraper.get_item_data, item_id, server_id): item_id 
                        for item_id in range(from_id, to_id + 1)
                    }
                
                # Process completed tasks
                for future in as_completed(future_to_id):
                    if not self.is_running:
                        break
                    
                    item_id = future_to_id[future]
                    processed += 1
                    
                    try:
                        result = future.result()
                        if result:
                            # Always sleep to be nice to remote sites
                            time.sleep(0.05)

                            if is_cross_server:
                                # Handle cross-server results
                                found_items += 1
                                self.cross_server_tab.add_comparison_row(result)
                                cross_server_data.append(result)  # Store for cross-server CSV export
                                
                                # Add individual server data to regular results display only (not CSV)
                                for server_name, server_data in result['server_data'].items():
                                    server_result = dict(server_data)
                                    server_result['server'] = server_name
                                    self.results_tab.add_row(server_result)
                                    # Don't add to items_data for cross-server mode
                                
                                # Log the price comparison
                                diff_str = f"{result['price_difference']:,}"
                                avg_str = f"{result['average_price']:,.0f}"
                                server_count = result['server_count']
                                self.log(f"Price Compare: {result['name']} - Low: {result['lowest_server']} ({result['lowest_price']:,}) | High: {result['highest_server']} ({result['highest_price']:,}) | Avg: {avg_str} | Diff: {diff_str} ({server_count} servers)", "success")
                            else:
                                # Handle single-server results
                                if not (result.get('name') == 'Unknown' or result.get('price', 0) == 0):
                                    # Add server name to result
                                    result = dict(result)
                                    result['server'] = server_name
                                    items_data.append(result)
                                    found_items += 1
                                    # Add to results table
                                    self.results_tab.add_row(result)
                                    
                                    # Log the find
                                    price_str = f"{result['price']:,}" if result['price'] > 0 else "No Price"
                                    category_str = result['category'] if result['category'] else "Unknown"
                                    rarity_str = result['rarity'] if result['rarity'] != 'Common' else ""
                                    rarity_display = f" [{rarity_str}]" if rarity_str else ""
                                    self.log(f"Found: {result['name']} (ID: {item_id}, Price: {price_str}, Cat: {category_str}{rarity_display})", "success")
                                else:
                                    self.log(f"Filtered: {result['name']} (ID: {item_id}) - excluded by filters", "warning")
                    
                    except Exception as e:
                        self.log(f"Error processing item {item_id}: {e}", "error")
                    
                    # Update progress
                    elapsed_time = time.time() - start_time
                    rate = (processed / elapsed_time) * 60 if elapsed_time > 0 else 0
                    
                    # Update progress bar (0.0 to 1.0)
                    progress_ratio = processed / total_items
                    self.progress_tab.progress_bar.set(progress_ratio)
                    
                    # Update statistics
                    self.progress_tab.processed_label.configure(text=f"{processed}/{total_items}")
                    self.progress_tab.found_label.configure(text=str(found_items))
                    self.progress_tab.rate_label.configure(text=f"{rate:.1f}/min")
                    
                    # Update progress status
                    self.progress_tab.progress_var.set(f"Processing item {item_id}...")
            
            # Save results to CSV
            if is_cross_server:
                # For cross-server analysis, only save comparison data
                if cross_server_data:
                    comparison_file = output_file  # Use the cross-server output file directly
                    comparison_fieldnames = [
                        'itemid', 'name', 'category', 'lowest_price', 'lowest_server',
                        'highest_price', 'highest_server', 'average_price', 'price_difference', 'server_count'
                    ]
                    
                    try:
                        with open(comparison_file, 'w', newline='', encoding='utf-8') as csvfile:
                            writer = csv.DictWriter(csvfile, fieldnames=comparison_fieldnames)
                            writer.writeheader()
                            
                            for item in cross_server_data:
                                clean_item = {
                                    'itemid': item.get('itemid', ''),
                                    'name': item.get('name', ''),
                                    'category': item.get('category', ''),
                                    'lowest_price': item.get('lowest_price', ''),
                                    'lowest_server': item.get('lowest_server', ''),
                                    'highest_price': item.get('highest_price', ''),
                                    'highest_server': item.get('highest_server', ''),
                                    'average_price': round(item.get('average_price', 0)),
                                    'price_difference': item.get('price_difference', ''),
                                    'server_count': item.get('server_count', '')
                                }
                                writer.writerow(clean_item)
                        
                        self.log(f"Saved {len(cross_server_data)} price comparisons to {comparison_file}", "success")
                    except Exception as e:
                        self.log(f"Error saving comparison CSV: {e}", "error")
                        messagebox.showerror("Error", f"Failed to save comparison CSV file: {e}")
                else:
                    self.log("No price comparisons found to save", "warning")
            elif items_data:
                # For single-server analysis, save to regular items.csv
                try:
                    # Read existing data if file exists
                    import os
                    existing_rows = []
                    if os.path.exists(output_file):
                        with open(output_file, 'r', encoding='utf-8', newline='') as csvfile:
                            reader = csv.DictReader(csvfile)
                            for row in reader:
                                existing_rows.append(row)

                    # Build a dict for quick lookup: (itemid, server) -> row
                    key = lambda row: (str(row.get('itemid', '')), str(row.get('server', '')))
                    existing_map = {key(row): row for row in existing_rows}

                    # Overwrite or add new rows from items_data
                    for item in items_data:
                        item_server = item.get('server', server_name)
                        k = (str(item.get('itemid', '')), str(item_server))
                        # Use clean_keys to ensure all fields present
                        def clean_keys(item):
                            return {
                                'itemid': item.get('itemid', ''),
                                'name': item.get('name', ''),
                                'price': item.get('price', ''),
                                'stack_price': item.get('stack_price', ''),
                                'sold_per_day': item.get('sold_per_day', ''),
                                'stack_sold_per_day': item.get('stack_sold_per_day', ''),
                                'category': item.get('category', ''),
                                'stackable': item.get('stackable', 'No'),
                                'server': item.get('server', item_server)
                            }
                        existing_map[k] = clean_keys(item)

                    # Write all rows back
                    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(existing_map.values())

                    self.log(f"Saved {len(items_data)} items to {output_file}", "success")
                
                except Exception as e:
                    self.log(f"Error saving CSV: {e}", "error")
                    messagebox.showerror("Error", f"Failed to save CSV file: {e}")
            
            elapsed_time = time.time() - start_time
            self.log(f"Scraping completed in {elapsed_time:.1f} seconds", "success")
            self.progress_tab.progress_var.set("Completed! 🎉")
        
        except Exception as e:
            self.log(f"Scraping error: {e}", "error")
            messagebox.showerror("Error", f"Scraping failed: {e}")
        finally:
            self.is_running = False
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.executor = None