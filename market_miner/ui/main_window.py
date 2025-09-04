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
    LogTab,
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
        self.root.title("🎮 MarketMiner Pro")
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
        self.log_tab: Optional[LogTab] = None
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
        last_output = self._user_config.get("output_path")
        if last_output:
            self.config_panel.output_file_var.set(last_output)

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
        title.grid(row=0, column=0, columnspan=2, pady=(15, 10))

        button_frame = ctk.CTkFrame(title_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(0, 15))

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
        self.config_panel.browse_btn.configure(command=self.browse_output_file)
        self.config_panel.cross_server_browse_btn.configure(
            command=self.browse_cross_server_output_file)

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

        # Logs
        log_tab = tabview.add("📝 Activity Log")
        self.log_tab = LogTab(log_tab, self.theme)
        self.log_tab.create(log_tab)

        tabview.set("📊 Progress")

    # -----------------------------
    # Helpers / UI actions
    # -----------------------------

    def _is_multi_server(self) -> bool:
        """True when 2+ servers are selected."""
        return len(self.config_panel.get_selected_servers()) > 1

    def _compute_comparison(self, item_id: int, server_data_list: List[dict]) -> Optional[dict]:
        """
        Build a comparison record for a single item across selected servers.
        Only rows with positive price are used.
        """
        priced = [d for d in server_data_list if d.get("price", 0) > 0]
        if len(priced) < 2:
            return None

        prices = {d["server"]: d["price"] for d in priced}
        lowest_server = min(prices, key=prices.get)
        highest_server = max(prices, key=prices.get)

        lowest_price = prices[lowest_server]
        highest_price = prices[highest_server]
        average = sum(prices.values()) / len(prices)

        base = priced[0]
        return {
            "itemid": item_id,
            "name": base.get("name", ""),
            "category": base.get("category", ""),
            "lowest_price": lowest_price,
            "lowest_server": lowest_server,
            "highest_price": highest_price,
            "highest_server": highest_server,
            "average_price": average,
            "price_difference": highest_price - lowest_price,
            "server_count": len(priced),
        }

    def browse_output_file(self) -> None:
        """Select the output folder; updates both per-server and cross-server paths."""
        default_dir = "output"
        current = self.config_panel.output_file_var.get()
        if current:
            current_dir = os.path.dirname(current)
            if os.path.isdir(current_dir):
                default_dir = current_dir

        folder = filedialog.askdirectory(
            title="Select Output Folder", initialdir=default_dir)
        if not folder:
            return

        output_file = os.path.join(folder, "items.csv")
        cross_server_file = os.path.join(folder, "cross_server_items.csv")
        self.config_panel.output_file_var.set(output_file)
        self.config_panel.cross_server_output_var.set(cross_server_file)

        if hasattr(self.config_panel, "output_folder_var"):
            self.config_panel.output_folder_var.set(folder)

        self._user_config["output_path"] = output_file
        save_config(self._user_config)

    def browse_cross_server_output_file(self) -> None:
        """Alias to keep both outputs in the same folder."""
        self.browse_output_file()

    def log(self, message: str, level: str = "info") -> None:
        """Log message to UI and status bar."""
        self.log_tab.log(message, level)
        self.progress_tab.progress_var.set(message)

        emoji = (
            "🟢" if level == "success" else
            "🔴" if level == "error" else
            "🟡" if level == "warning" else
            "🔵"
        )
        self.status.configure(text=f"{emoji} {message}")
        self.root.update_idletasks()

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

        # Persist last-used server and output path
        self._user_config["last_server"] = selected_servers[0]
        self._user_config["output_path"] = self.config_panel.get_output_file()
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
        self.log("Stopping scraper...", "warning")

    def scrape_worker(self) -> None:
        """Background worker that coordinates scraping and saving."""
        try:
            from_id = int(self.config_panel.from_var.get())
            to_id = int(self.config_panel.to_var.get())
            max_threads = int(self.config_panel.thread_var.get())
            output_file = self.config_panel.get_output_file().strip() or "items.csv"

            # Skipped items file beside items.csv
            skipped_path = os.path.join(os.path.dirname(
                output_file) or ".", "skipped_items.json")

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
                except Exception:
                    pass

            selected_servers = self.config_panel.get_selected_servers()
            is_multi = len(selected_servers) > 1

            # Validate server names -> IDs
            server_ids: Dict[str, int] = {}
            for name in selected_servers:
                if name in SERVERS:
                    server_ids[name] = SERVERS[name]
                else:
                    self.log(f"Unknown server '{name}'", "error")

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
            items_data: List[dict] = []
            comparison_data: List[dict] = []
            per_item_bucket = {i: [] for i in range(
                from_id, to_id + 1)} if is_multi else None

            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                self.executor = executor

                # Submit tasks
                if is_multi:
                    fut_to_key = {
                        executor.submit(self.scraper.get_item_data, item_id, sid): (item_id, sname)
                        for item_id in range(from_id, to_id + 1)
                        for sname, sid in server_ids.items()
                    }
                else:
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
                        # Be polite to the target site
                        time.sleep(0.05)

                        if result:
                            # --- NEW: handle explicit skip payload ---
                            if result.get("skip_reason"):
                                self.log(
                                    f"Skipping item {item_id} ({result.get('name', 'Unknown')}): {result['skip_reason']}",
                                    "warning",
                                )
                                save_skip(item_id, result.get(
                                    "name", "Unknown"), result["skip_reason"])
                                continue

                            row = dict(result)
                            row["server"] = sname

                            # Skip unknown-name rows for display
                            if row.get("name") == "Unknown":
                                self.log(
                                    f"Filtered: (ID: {item_id}) - No item name found", "warning")
                                save_skip(item_id, row.get("name","Unknown"), "excluded by filters")
                                continue

                            # Show per-server result
                            self.results_tab.add_row(row)

                            # Count “found” only when price > 0
                            if row.get("price", 0) > 0:
                                found_items += 1
                                price_str = f"{row['price']:,}"
                                cat = row.get("category") or "Unknown"
                                rare = row.get("rarity", "")
                                rare_disp = f" [{rare}]" if rare and rare != "Common" else ""
                                self.log(
                                    f"Found: {row['name']} (ID: {item_id}, Price: {price_str}, "
                                    f"Cat: {cat}{rare_disp})",
                                    "success",
                                )
                            else:
                                self.log(
                                    f"Filtered: (ID: {item_id}) - excluded by filters", "warning")
                                save_skip(item_id, result.get(
                                    "name", "Unknown"), result["skip_reason"])

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
                                            "success",
                                        )
                        else:
                            self.log(f"Skipping item {item_id}: excluded or failed to parse", "warning")
                            save_skip(item_id, "Unknown", "excluded or parse failure")

                        # Progress UI
                        elapsed = time.time() - start_ts
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

                self.log(
                    f"Saved {len(items_data)} rows to {output_file}", "success")

            # 2) Cross-server comparison (only if multi)
            if is_multi and comparison_data:
                cmp_file = self.config_panel.cross_server_output_var.get(
                ).strip() or "cross_server_items.csv"
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
                self.log(
                    f"Saved {len(comparison_data)} price comparisons to {cmp_file}", "success")

            elapsed = time.time() - start_ts
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
