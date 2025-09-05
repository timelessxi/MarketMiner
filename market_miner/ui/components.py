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
        self.selected_servers = ["Asura"]  # List of selected servers
        self.from_var = tk.StringVar(value="1")
        self.to_var = tk.StringVar(value="100")
        self.thread_var = tk.StringVar(value="3")

        # UI components that need to be accessed later
        self.server_combo = None
        self.cross_server_browse_btn = None
        
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
        ctk.CTkLabel(self.frame, text="Servers:", 
                    font=ctk.CTkFont(size=12)).grid(
            row=1, column=0, sticky='w', padx=(20, 10), pady=(10, 5))
        
        # Server selection frame
        server_frame = ctk.CTkFrame(self.frame)
        server_frame.grid(row=1, column=1, sticky='ew', padx=(0, 20), pady=(10, 5))
        server_frame.grid_columnconfigure(0, weight=1)
        
        # Single server dropdown (default)
        self.server_combo = ctk.CTkComboBox(server_frame, variable=self.server_var, 
                                           values=list(SERVERS.keys()), 
                                           state="readonly", width=160)
        self.server_combo.grid(row=0, column=0, sticky='w', padx=10, pady=5)
        
        # Multi-server button
        self.multi_server_btn = ctk.CTkButton(server_frame, text="Select Multiple Servers", 
                                             command=self._show_server_selection,
                                             width=150, height=28)
        self.multi_server_btn.grid(row=0, column=1, sticky='e', padx=10, pady=5)
        
        # Selected servers label (initially hidden)
        self.selected_servers_label = ctk.CTkLabel(server_frame, text="", font=ctk.CTkFont(size=11))
        self.selected_servers_label.grid(row=1, column=0, columnspan=2, sticky='w', padx=10, pady=(0, 5))
        
        # Range selection
        ctk.CTkLabel(self.frame, text="Item ID Range:", 
                    font=ctk.CTkFont(size=12)).grid(
            row=3, column=0, sticky='w', padx=(20, 10), pady=5)
        
        range_frame = ctk.CTkFrame(self.frame)
        range_frame.grid(row=3, column=1, sticky='ew', padx=(0, 20), pady=5)
        
        from_entry = ctk.CTkEntry(range_frame, textvariable=self.from_var, width=80)
        from_entry.pack(side='left', padx=(10, 5))
        
        ctk.CTkLabel(range_frame, text="to", 
                    font=ctk.CTkFont(size=12)).pack(side='left', padx=5)
        
        to_entry = ctk.CTkEntry(range_frame, textvariable=self.to_var, width=80)
        to_entry.pack(side='left', padx=(5, 10))
        
        # Thread count
        ctk.CTkLabel(self.frame, text="Concurrent Threads:", 
                    font=ctk.CTkFont(size=12)).grid(
            row=4, column=0, sticky='w', padx=(20, 10), pady=5)
        
        thread_frame = ctk.CTkFrame(self.frame)
        thread_frame.grid(row=4, column=1, sticky='w', padx=(0, 20), pady=5)
        
        thread_entry = ctk.CTkEntry(thread_frame, textvariable=self.thread_var, width=60)
        thread_entry.pack(side='left', padx=(10, 5))
        
        thread_hint = ctk.CTkLabel(thread_frame, text="(recommended: 3-4)", 
                                  font=ctk.CTkFont(size=10), 
                                  text_color=("gray50", "gray60"))
        thread_hint.pack(side='left', padx=(5, 10))
        

        # Output information (no selection needed)

        output_frame = ctk.CTkFrame(self.frame)
        output_frame.grid(row=5, column=1, sticky='ew', padx=(0, 20), pady=(5, 20))

        # Show where files will be saved
        location_label = ctk.CTkLabel(output_frame, 
                                     text="📁 Files will be saved to: output/",
                                     font=ctk.CTkFont(size=11))
        location_label.grid(row=0, column=0, sticky='w', padx=10, pady=(10, 5))

        # Keep these for compatibility but they won't be used for browsing
        self.browse_btn = None
        self.cross_server_browse_btn = None

        return self.frame
    
    def _show_server_selection(self):
        """Show server selection dialog"""
        import tkinter as tk
        from tkinter import messagebox
        
        # Create server selection dialog
        dialog = tk.Toplevel(self.parent)
        dialog.title("Select Servers")
        dialog.geometry("400x500")
        dialog.resizable(False, False)
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"400x500+{x}+{y}")
        
        # Header
        header_frame = tk.Frame(dialog, bg='#212121')
        header_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(header_frame, text="Select Servers for Analysis", 
                font=('Arial', 14, 'bold'), bg='#212121', fg='white').pack()
        
        # Warning label
        warning_frame = tk.Frame(dialog, bg='#212121')
        warning_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        tk.Label(warning_frame, 
                text="⚠️ Multiple servers will take significantly longer to process",
                font=('Arial', 10), bg='#212121', fg='orange').pack()
        
        # Server list frame
        list_frame = tk.Frame(dialog, bg='#212121')
        list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Scrollable frame for servers
        canvas = tk.Canvas(list_frame, bg='#2b2b2b')
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#2b2b2b')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Server checkboxes
        server_vars = {}
        for server in sorted(SERVERS.keys()):
            var = tk.BooleanVar(value=(server in self.selected_servers))
            server_vars[server] = var
            
            checkbox = tk.Checkbutton(scrollable_frame, text=server, variable=var,
                                     bg='#2b2b2b', fg='white', selectcolor='#404040',
                                     font=('Arial', 10))
            checkbox.pack(anchor='w', padx=10, pady=2)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons
        button_frame = tk.Frame(dialog, bg='#212121')
        button_frame.pack(fill='x', padx=10, pady=10)
        
        def select_all():
            for var in server_vars.values():
                var.set(True)
        
        def clear_all():
            for var in server_vars.values():
                var.set(False)
        
        def apply_selection():
            selected = [server for server, var in server_vars.items() if var.get()]
            if not selected:
                messagebox.showerror("Error", "Please select at least one server.")
                return
            
            self.selected_servers = selected
            self._update_server_display()
            dialog.destroy()
        
        tk.Button(button_frame, text="Select All", command=select_all,
                 bg='#404040', fg='white').pack(side='left', padx=5)
        tk.Button(button_frame, text="Clear All", command=clear_all,
                 bg='#404040', fg='white').pack(side='left', padx=5)
        tk.Button(button_frame, text="Cancel", command=dialog.destroy,
                 bg='#666666', fg='white').pack(side='right', padx=5)
        tk.Button(button_frame, text="Apply", command=apply_selection,
                 bg='#1f6aa5', fg='white').pack(side='right', padx=5)
    
    def _update_server_display(self):
        """Update the server display based on selection"""
        if len(self.selected_servers) == 1:
            # Single server mode
            self.server_var.set(self.selected_servers[0])
            self.server_combo.grid()
            self.selected_servers_label.configure(text="")
        else:
            # Multi-server mode
            self.server_combo.grid_remove()
            server_text = f"Selected servers: {', '.join(self.selected_servers[:3])}"
            if len(self.selected_servers) > 3:
                server_text += f" + {len(self.selected_servers) - 3} more"
            self.selected_servers_label.configure(text=server_text)
    
    def get_selected_servers(self):
        """Get list of servers for analysis"""
        return self.selected_servers
    
    def get_output_file(self):
        """Get the output file with timestamp for unique runs"""
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        return f"output/items_{timestamp}.csv"



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
        self.rate_label = None
        self.eta_label = None
        self.progress_bar = None
        
    def create(self, tab_frame):
        """Create the progress tab using CustomTkinter"""
        self.frame = tab_frame
        
        
        # ETA display
        eta_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        eta_frame.pack(fill='x', padx=20, pady=(20, 10))
        
        ctk.CTkLabel(eta_frame, text="Estimated Time Remaining:",
                    font=ctk.CTkFont(size=12)).pack(side='left')
        
        self.eta_label = ctk.CTkLabel(eta_frame, text="--:--",
                                     font=ctk.CTkFont(size=12, weight="bold"))
        self.eta_label.pack(side='left', padx=(10, 0))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.frame, width=400)
        self.progress_bar.pack(fill='x', padx=20, pady=(0, 20))
        self.progress_bar.set(0)
        
        # Statistics frame
        stats_frame = ctk.CTkFrame(self.frame)
        stats_frame.pack(fill='x', padx=20, pady=(0, 20))
        stats_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Statistics labels
        ctk.CTkLabel(stats_frame, text="Processed", 
                    font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=0, pady=(15, 5))
        ctk.CTkLabel(stats_frame, text="Rate", 
                    font=ctk.CTkFont(size=12, weight="bold")).grid(
            row=0, column=1, pady=(15, 5))
        
        self.processed_label = ctk.CTkLabel(stats_frame, text="0/0",
                                           font=ctk.CTkFont(size=16))
        self.processed_label.grid(row=1, column=0, pady=(0, 15))
        
        self.rate_label = ctk.CTkLabel(stats_frame, text="0/min",
                                      font=ctk.CTkFont(size=16))
        self.rate_label.grid(row=1, column=1, pady=(0, 15))
        
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
        cols = ("itemid", "name", "price", "stack_price", "sold_per_day", "stack_sold_per_day", "category", "stackable", "server")
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

        for c, w in (("itemid", 80), ("name", 180), ("price", 90), ("stack_price", 90), 
                     ("sold_per_day", 100), ("stack_sold_per_day", 110), ("category", 110), ("stackable", 80), ("server", 100)):
            self.results.heading(c, text=c.replace('_', ' ').title())
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
        
        # Show both individual and stack prices when available
        price = result.get('price', 0)
        stack_price = result.get('stack_price', 0)
        
        self.results.insert("", "end", values=(
            result.get("itemid", ""),
            result.get("name", ""),
            format_number(price) if price > 0 else "",
            format_number(stack_price) if stack_price > 0 else "",
            format_number(result.get("sold_per_day", "")),
            format_number(result.get("stack_sold_per_day", "")),
            result.get("category", "") or "",
            result.get("stackable", "No") or "No",
            result.get("server", "") or ""
        ))


class CrossServerResultsTab:
    """Cross-server comparison results tab with arbitrage opportunities"""
    
    def __init__(self, parent, theme):
        self.parent = parent
        self.theme = theme
        self.frame = None
        self.results = None
        
    def create(self, tab_frame):
        """Create the cross-server results tab"""
        self.frame = tab_frame

        # Header
        header = ctk.CTkLabel(self.frame, text="Cross-Server Analysis", 
                             font=ctk.CTkFont(size=18, weight="bold"))
        header.pack(anchor='w', padx=20, pady=(20, 15))

        # Table frame
        table_frame = tk.Frame(self.frame, bg='#212121')
        table_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # Treeview for cross-server results
        cols = ("itemid", "name", "category", "lowest_price", "lowest_server", 
               "highest_price", "highest_server", "average_price", "price_difference", "server_count")
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

        # Column configurations
        col_configs = [
            ("itemid", 80, "Item ID"),
            ("name", 200, "Item Name"),
            ("category", 100, "Category"),
            ("lowest_price", 80, "Low Price"),
            ("lowest_server", 90, "Low Server"),
            ("highest_price", 80, "High Price"),
            ("highest_server", 90, "High Server"),
            ("average_price", 80, "Avg Price"),
            ("price_difference", 80, "Difference"),
            ("server_count", 60, "Servers")
        ]
        
        for col, width, title in col_configs:
            self.results.heading(col, text=title)
            self.results.column(col, width=width, anchor='w', stretch=False, minwidth=width)

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
    
    def add_comparison_row(self, item_data):
        """Add a cross-server comparison row"""
        def format_number(x):
            try:
                return f"{int(x):,}"
            except:
                return x if x is not None else ""
        
        self.results.insert("", "end", values=(
            item_data.get("itemid", ""),
            item_data.get("name", ""),
            item_data.get("category", ""),
            format_number(item_data.get("lowest_price", "")),
            item_data.get("lowest_server", ""),
            format_number(item_data.get("highest_price", "")),
            item_data.get("highest_server", ""),
            format_number(item_data.get("average_price", "")),
            format_number(item_data.get("price_difference", "")),
            item_data.get("server_count", "")
        ))
    
    def clear_results(self):
        """Clear all results from the table"""
        for item in self.results.get_children():
            self.results.delete(item)



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