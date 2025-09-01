"""
UI Components for MarketMiner Pro using CustomTkinter
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import time
from ..servers import SERVERS


class ConfigurationPanel:
    """Configuration panel with server, range, threads, and file options"""
    
    def __init__(self, parent, theme):
        self.parent = parent
        self.theme = theme
        self.frame = None
        
        # Variables
        self.server_var = tk.StringVar(value="Asura")
        self.from_var = tk.StringVar(value="1")
        self.to_var = tk.StringVar(value="100")
        self.thread_var = tk.StringVar(value="6")
        self.output_file_var = tk.StringVar(value="items.csv")
        
    def create(self, row, column, **grid_options):
        """Create the configuration panel using CustomTkinter"""
        self.frame = ctk.CTkFrame(self.parent)
        self.frame.grid(row=row, column=column, **grid_options)
        self.frame.grid_columnconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkLabel(self.frame, text="⚙️ Configuration", 
                             font=ctk.CTkFont(size=16, weight="bold"))
        header.grid(row=0, column=0, columnspan=2, sticky='w', padx=20, pady=(20, 10))
        
        # Server selection
        ctk.CTkLabel(self.frame, text="Server:", 
                    font=ctk.CTkFont(size=12)).grid(
            row=1, column=0, sticky='w', padx=(20, 10), pady=(10, 5))
        
        server_combo = ctk.CTkComboBox(self.frame, variable=self.server_var, 
                                      values=list(SERVERS.keys()), 
                                      state="readonly", width=160)
        server_combo.grid(row=1, column=1, sticky='ew', padx=(0, 20), pady=(10, 5))
        
        # Range selection
        ctk.CTkLabel(self.frame, text="Item ID Range:", 
                    font=ctk.CTkFont(size=12)).grid(
            row=2, column=0, sticky='w', padx=(20, 10), pady=5)
        
        range_frame = ctk.CTkFrame(self.frame)
        range_frame.grid(row=2, column=1, sticky='ew', padx=(0, 20), pady=5)
        
        from_entry = ctk.CTkEntry(range_frame, textvariable=self.from_var, width=80)
        from_entry.pack(side='left', padx=(10, 5))
        
        ctk.CTkLabel(range_frame, text="to", 
                    font=ctk.CTkFont(size=12)).pack(side='left', padx=5)
        
        to_entry = ctk.CTkEntry(range_frame, textvariable=self.to_var, width=80)
        to_entry.pack(side='left', padx=(5, 10))
        
        # Thread count
        ctk.CTkLabel(self.frame, text="Concurrent Threads:", 
                    font=ctk.CTkFont(size=12)).grid(
            row=3, column=0, sticky='w', padx=(20, 10), pady=5)
        
        thread_entry = ctk.CTkEntry(self.frame, textvariable=self.thread_var, width=80)
        thread_entry.grid(row=3, column=1, sticky='w', padx=(0, 20), pady=5)
        
        # Output file
        ctk.CTkLabel(self.frame, text="Output File:", 
                    font=ctk.CTkFont(size=12)).grid(
            row=4, column=0, sticky='w', padx=(20, 10), pady=5)
        
        file_frame = ctk.CTkFrame(self.frame)
        file_frame.grid(row=4, column=1, sticky='ew', padx=(0, 20), pady=(5, 20))
        file_frame.grid_columnconfigure(0, weight=1)
        
        file_entry = ctk.CTkEntry(file_frame, textvariable=self.output_file_var)
        file_entry.grid(row=0, column=0, sticky='ew', padx=(10, 5), pady=10)
        
        self.browse_btn = ctk.CTkButton(file_frame, text="📁 Browse", width=100)
        self.browse_btn.grid(row=0, column=1, padx=(5, 10), pady=10)
        
        return self.frame


class OptionsPanel:
    """Options panel with filters and advanced settings"""
    
    def __init__(self, parent, theme):
        self.parent = parent
        self.theme = theme
        self.frame = None
        
        # Variables
        self.include_no_price_var = tk.BooleanVar(value=True)
        self.include_rare_var = tk.BooleanVar(value=True)
        self._advanced_shown = tk.BooleanVar(value=False)
        
    def create(self, row, column, **grid_options):
        """Create the options panel using CustomTkinter"""
        self.frame = ctk.CTkFrame(self.parent)
        self.frame.grid(row=row, column=column, **grid_options)
        
        # Header
        header = ctk.CTkLabel(self.frame, text="🔧 Options", 
                             font=ctk.CTkFont(size=16, weight="bold"))
        header.grid(row=0, column=0, sticky='w', padx=20, pady=(20, 10))
        
        # Basic options
        include_no_price_cb = ctk.CTkCheckBox(self.frame, text="Include items without prices", 
                                             variable=self.include_no_price_var)
        include_no_price_cb.grid(row=1, column=0, sticky='w', padx=20, pady=5)
        
        include_rare_cb = ctk.CTkCheckBox(self.frame, text="Include rare/exclusive items", 
                                         variable=self.include_rare_var)
        include_rare_cb.grid(row=2, column=0, sticky='w', padx=20, pady=5)
        
        # Advanced toggle
        def toggle_advanced():
            self._advanced_shown.set(not self._advanced_shown.get())
            if self._advanced_shown.get():
                adv_frame.grid()
                adv_toggle.configure(text="Advanced ▼")
            else:
                adv_frame.grid_remove()
                adv_toggle.configure(text="Advanced ▶")
        
        adv_toggle = ctk.CTkButton(self.frame, text="Advanced ▶", 
                                  command=toggle_advanced, 
                                  width=120, height=28,
                                  fg_color="transparent",
                                  hover_color=("gray70", "gray30"))
        adv_toggle.grid(row=3, column=0, sticky='w', padx=20, pady=(10, 5))
        
        # Advanced frame
        adv_frame = ctk.CTkFrame(self.frame)
        adv_frame.grid(row=4, column=0, sticky='ew', padx=20, pady=(5, 20))
        
        
        # Hide advanced by default
        adv_frame.grid_remove()
        
        return self.frame


class ProgressTab:
    """Progress tab with status, progress bar, and statistics"""
    
    def __init__(self, parent, theme):
        self.parent = parent
        self.theme = theme
        self.frame = None
        
        # Variables
        self.progress_var = tk.StringVar(value="Ready to start...")
        
        # Components
        self.processed_label = None
        self.found_label = None
        self.rate_label = None
        self.progress_bar = None
        
    def create(self, tab_frame):
        """Create the progress tab using CustomTkinter"""
        self.frame = tab_frame
        
        # Status header
        status_header = ctk.CTkLabel(self.frame, text="Status", 
                                    font=ctk.CTkFont(size=18, weight="bold"))
        status_header.pack(anchor='w', padx=20, pady=(20, 10))
        
        # Status label
        status_label = ctk.CTkLabel(self.frame, textvariable=self.progress_var,
                                   font=ctk.CTkFont(size=12))
        status_label.pack(anchor='w', padx=20, pady=(0, 15))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.frame, width=400)
        self.progress_bar.pack(fill='x', padx=20, pady=(0, 20))
        self.progress_bar.set(0)
        
        # Statistics frame
        stats_frame = ctk.CTkFrame(self.frame)
        stats_frame.pack(fill='x', padx=20, pady=(0, 20))
        stats_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Statistics labels
        ctk.CTkLabel(stats_frame, text="Processed", 
                    font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=0, pady=(15, 5))
        ctk.CTkLabel(stats_frame, text="Found", 
                    font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=1, pady=(15, 5))
        ctk.CTkLabel(stats_frame, text="Rate", 
                    font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=2, pady=(15, 5))
        
        self.processed_label = ctk.CTkLabel(stats_frame, text="0/0",
                                           font=ctk.CTkFont(size=16))
        self.processed_label.grid(row=1, column=0, pady=(0, 15))
        
        self.found_label = ctk.CTkLabel(stats_frame, text="0",
                                       font=ctk.CTkFont(size=16))
        self.found_label.grid(row=1, column=1, pady=(0, 15))
        
        self.rate_label = ctk.CTkLabel(stats_frame, text="0/min",
                                      font=ctk.CTkFont(size=16))
        self.rate_label.grid(row=1, column=2, pady=(0, 15))
        
        return self.frame


class ResultsTab:
    """Results tab with live data table"""
    
    def __init__(self, parent, theme):
        self.parent = parent
        self.theme = theme
        self.frame = None
        self.results = None
        
    def create(self, tab_frame):
        """Create the results tab - using tkinter Treeview since CTk doesn't have a table widget"""
        self.frame = tab_frame
        
        # Header
        header = ctk.CTkLabel(self.frame, text="Live Results", 
                             font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(anchor='w', padx=20, pady=(20, 15))
        
        # Table frame
        table_frame = tk.Frame(self.frame, bg='#212121')
        table_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        
        # Treeview for results table
        cols = ("itemid", "name", "price", "stock", "sold_per_day", "category", "rarity")
        self.results = ttk.Treeview(table_frame, columns=cols, show="headings", height=16)
        
        # Configure style for dark theme
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", 
                       background='#2b2b2b',
                       foreground='#dce4ee',
                       fieldbackground='#2b2b2b')
        style.configure("Treeview.Heading",
                       background='#404040',
                       foreground='#dce4ee')
        
        for c, w in (("itemid", 80), ("name", 220), ("price", 90), ("stock", 80), 
                     ("sold_per_day", 110), ("category", 120), ("rarity", 90)):
            self.results.heading(c, text=c.title())
            self.results.column(c, width=w, anchor='w', stretch=False, minwidth=w)
        
        # Vertical scrollbar
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.results.yview)
        self.results.configure(yscrollcommand=v_scrollbar.set)
        
        # Horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.results.xview)
        self.results.configure(xscrollcommand=h_scrollbar.set)
        
        # Grid the treeview and scrollbars
        self.results.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        
        return self.frame
    
    def add_row(self, result):
        """Add a result row to the table"""
        def format_number(x):
            try:
                return f"{int(x):,}"
            except:
                return x if x is not None else ""
        
        self.results.insert("", "end", values=(
            result.get("itemid", ""),
            result.get("name", ""),
            format_number(result.get("price", "")),
            format_number(result.get("stock", "")),
            format_number(result.get("sold_per_day", "")),
            result.get("category", "") or "",
            result.get("rarity", "") or ""
        ))


class LogTab:
    """Log tab with colored message display"""
    
    def __init__(self, parent, theme):
        self.parent = parent
        self.theme = theme
        self.frame = None
        self.log_text = None
        
    def create(self, tab_frame):
        """Create the log tab using CustomTkinter"""
        self.frame = tab_frame
        
        # Header
        header = ctk.CTkLabel(self.frame, text="Activity Log", 
                             font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(anchor='w', padx=20, pady=(20, 15))
        
        # Log text area using CustomTkinter textbox
        self.log_text = ctk.CTkTextbox(self.frame, wrap="word",
                                      font=ctk.CTkFont(family="Consolas", size=11))
        self.log_text.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        return self.frame
    
    def log(self, message, level="info"):
        """Add a message to the log"""
        timestamp = time.strftime('%H:%M:%S')
        
        # Determine message type and emoji
        if "Found:" in message:
            level = "success"
            emoji = "✅"
        elif "Error" in message or "error" in message.lower():
            level = "error"
            emoji = "❌"
        elif "Filtered:" in message:
            level = "warning" 
            emoji = "🔒"
        elif "Starting" in message or "Completed" in message:
            level = "info"
            emoji = "🚀" if "Starting" in message else "🎉"
        else:
            emoji = "ℹ️"
        
        formatted = f"[{timestamp}] {emoji} {message}\n"
        
        # Insert text and scroll to bottom
        self.log_text.insert("end", formatted)
        self.log_text.see("end")