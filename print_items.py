import argparse
import pandas as pd
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tabulate import tabulate

# -----------------------------
# Utility: simple tooltip
# -----------------------------
class ToolTip:
    def __init__(self, widget, text_fn):
        self.widget = widget
        self.text_fn = text_fn  # lambda returning text
        self.tipwindow = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _=None):
        if self.tipwindow is not None:
            return
        text = self.text_fn()
        if not text:
            return
        x, y, cx, cy = self.widget.bbox("insert") or (0, 0, 0, 0)
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(
            tw,
            text=text,
            justify=tk.LEFT,
            relief=tk.SOLID,
            borderwidth=1,
            background="#ffffe0",
            padx=5,
            pady=3,
            font=("TkDefaultFont", 9),
            wraplength=600,
        )
        label.pack(ipadx=1)

    def hide(self, _=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


def print_csv_file(filename, num_rows=None, columns=None, filter_col=None, filter_val=None):
    try:
        df = pd.read_csv(filename, encoding='utf-8')
        if df.empty:
            print("The file is empty.")
            return
        if filter_col and filter_val is not None and filter_col in df.columns:
            df = df[df[filter_col].astype(str) == str(filter_val)]
        if columns:
            # only keep columns that exist
            columns = [c for c in columns if c in df.columns]
            if columns:
                df = df[columns]
        if num_rows is not None:
            df = df.head(num_rows)
        print(tabulate(df, headers='keys', tablefmt='grid', showindex=True))
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
    except KeyError as e:
        print(f"Column not found: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


class CSVViewer(tk.Tk):
    """Improved GUI for very wide CSVs.

    Key features:
    - Column windowing: show a sliding window of N columns out of all columns.
    - Column chooser dialog with search and Select All / None.
    - Autosize column widths (min/max) based on sample rows.
    - Sticky top controls; persistent filters.
    - Double-click a row to open a detail inspector (shows all columns in a vertical table).
    - Tooltips for truncated cell values.
    """

    def __init__(self):
        super().__init__()
        self.title("CSV Viewer (Wide-friendly)")
        self.geometry("1100x700")
        self.df = None
        self.filtered_df = None
        self.filename = None

        # Column window controls
        self.col_window_start = tk.IntVar(value=0)  # start index (inclusive)
        self.col_window_count = tk.IntVar(value=12) # number of columns to show

        # Filter controls
        self.filter_col_var = tk.StringVar()
        self.filter_val_var = tk.StringVar()

        # Selected columns set (None -> all)
        self.selected_columns = None

        self._build_ui()

    # ------------- UI construction -------------
    def _build_ui(self):
        outer = ttk.Frame(self)
        outer.pack(fill=tk.BOTH, expand=True)

        # Top bar
        top = ttk.Frame(outer)
        top.pack(fill=tk.X, padx=10, pady=8)

        ttk.Button(top, text="Open CSV", command=self.open_file).pack(side=tk.LEFT)

        ttk.Label(top, text="Filter Col").pack(side=tk.LEFT, padx=(12, 4))
        self.filter_col_entry = ttk.Entry(top, textvariable=self.filter_col_var, width=18)
        self.filter_col_entry.pack(side=tk.LEFT)

        ttk.Label(top, text="Value").pack(side=tk.LEFT, padx=(8, 4))
        self.filter_val_entry = ttk.Entry(top, textvariable=self.filter_val_var, width=18)
        self.filter_val_entry.pack(side=tk.LEFT)

        ttk.Button(top, text="Apply Filter", command=self.apply_filter).pack(side=tk.LEFT, padx=6)
        ttk.Button(top, text="Clear Filter", command=self.clear_filter).pack(side=tk.LEFT)

        ttk.Separator(outer, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=4)

        # Column controls
        colbar = ttk.Frame(outer)
        colbar.pack(fill=tk.X, padx=10, pady=6)

        ttk.Label(colbar, text="Column window start").pack(side=tk.LEFT)
        start_spin = ttk.Spinbox(colbar, from_=0, to=1000000, textvariable=self.col_window_start, width=6, command=self.refresh_view)
        start_spin.pack(side=tk.LEFT, padx=(6, 12))

        ttk.Label(colbar, text="# visible columns").pack(side=tk.LEFT)
        count_spin = ttk.Spinbox(colbar, from_=1, to=1000000, textvariable=self.col_window_count, width=6, command=self.refresh_view)
        count_spin.pack(side=tk.LEFT, padx=(6, 12))

        ttk.Button(colbar, text="Choose Columns…", command=self.open_column_chooser).pack(side=tk.LEFT)
        ttk.Button(colbar, text="Fit Column Widths", command=self.autosize_columns).pack(side=tk.LEFT, padx=6)

        # Tree + scrollbars
        tree_frame = ttk.Frame(outer)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(tree_frame, show="headings")
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # Scrollbars
        self.scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.scroll_x.pack(fill=tk.X, side=tk.BOTTOM)
        self.tree.configure(xscrollcommand=self.scroll_x.set)

        self.scroll_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.scroll_y.pack(fill=tk.Y, side=tk.RIGHT)
        self.tree.configure(yscrollcommand=self.scroll_y.set)

        # Row inspector
        self.tree.bind("<Double-1>", self.open_row_inspector)

    # ------------- File & Data -------------
    def open_file(self):
        file = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv"), ("All files", "*.*")])
        if not file:
            return
        try:
            self.df = pd.read_csv(file, encoding='utf-8')
            self.filename = file
            self.filtered_df = self.df.copy()
            self.selected_columns = None
            # Console preview (limit to 20 rows)
            print("\nLoaded CSV: {}".format(file))
            print(tabulate(self.df.head(20), headers='keys', tablefmt='grid', showindex=True))
            if len(self.df) > 20:
                print(f"... ({len(self.df)} rows total, showing first 20)")
            self.refresh_view()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def get_active_columns(self):
        if self.filtered_df is None:
            return []
        cols = list(self.filtered_df.columns)
        if self.selected_columns is not None:
            cols = [c for c in cols if c in self.selected_columns]
        # Apply windowing
        start = max(0, min(self.col_window_start.get(), max(0, len(cols)-1)))
        count = max(1, self.col_window_count.get())
        return cols[start:start+count]

    def refresh_view(self):
        if self.filtered_df is None:
            return
        cols = self.get_active_columns()
        df_show = self.filtered_df[cols] if cols else self.filtered_df
        self.display_df(df_show)

    # ------------- Display -------------
    def display_df(self, df):
        # Clear
        self.tree.delete(*self.tree.get_children())
        self.tree['columns'] = list(df.columns)

        # Configure headings and default widths
        for col in df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=160, anchor=tk.W, stretch=False)

        # Insert rows
        for _, row in df.iterrows():
            values = []
            for v in row.tolist():
                s = "" if pd.isna(v) else str(v)
                # Shorten for display; full value via tooltip in inspector
                values.append(s)
            self.tree.insert('', tk.END, values=values)

        # Attach simple tooltip to the whole tree that shows cell under cursor
        def _tooltip_text():
            region = self.tree.identify('region', self.tree.winfo_pointerx()-self.tree.winfo_rootx(), self.tree.winfo_pointery()-self.tree.winfo_rooty())
            if region != 'cell':
                return ''
            rowid = self.tree.identify_row(self.tree.winfo_pointery()-self.tree.winfo_rooty())
            colid = self.tree.identify_column(self.tree.winfo_pointerx()-self.tree.winfo_rootx())
            if not rowid or not colid:
                return ''
            vals = self.tree.item(rowid, 'values')
            try:
                idx = int(colid.replace('#', '')) - 1
                return vals[idx] if idx < len(vals) else ''
            except Exception:
                return ''
        # (Re)create tooltip each refresh
        self.tree.tooltip = ToolTip(self.tree, _tooltip_text)

    def autosize_columns(self, sample_rows=200, min_w=80, max_w=380):
        if not self.tree['columns']:
            return
        # Measure header + sample of body text widths using a hidden label
        tester = tk.Label(self, font=("TkDefaultFont", 9))
        df = self.filtered_df if self.filtered_df is not None else pd.DataFrame()
        sample = df.head(sample_rows)
        for col in self.tree['columns']:
            texts = [str(col)] + ["" if pd.isna(v) else str(v) for v in sample[col].tolist()] if col in sample.columns else [str(col)]
            width_px = max(tester.winfo_reqwidth(), max(tester.winfo_fpixels(f"{len(t)}p") for t in texts))  # fallback
            # Better measurement via configure + update_idletasks
            maxlen = max(len(t) for t in texts)
            tester.configure(text="W" * maxlen)
            tester.update_idletasks()
            width_px = tester.winfo_width() + 24  # padding
            # Clamp
            width_px = max(min_w, min(max_w, width_px))
            self.tree.column(col, width=int(width_px))
        tester.destroy()

    # ------------- Filters -------------
    def apply_filter(self):
        if self.df is None:
            return
        df = self.df.copy()
        filter_col = self.filter_col_var.get().strip()
        filter_val = self.filter_val_var.get().strip()
        if filter_col and filter_val and filter_col in df.columns:
            df = df[df[filter_col].astype(str) == filter_val]
        self.filtered_df = df
        self.refresh_view()

    def clear_filter(self):
        if self.df is None:
            return
        self.filter_col_var.set("")
        self.filter_val_var.set("")
        self.filtered_df = self.df.copy()
        self.refresh_view()

    # ------------- Column chooser -------------
    def open_column_chooser(self):
        if self.filtered_df is None:
            return
        cols = list(self.filtered_df.columns)
        dlg = tk.Toplevel(self)
        dlg.title("Choose Columns")
        dlg.geometry("420x520")
        dlg.transient(self)
        dlg.grab_set()

        search_var = tk.StringVar()
        tk.Label(dlg, text="Search").pack(anchor='w', padx=10, pady=(10, 0))
        search = ttk.Entry(dlg, textvariable=search_var)
        search.pack(fill=tk.X, padx=10)

        frame = tk.Frame(dlg)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        canvas = tk.Canvas(frame)
        yscroll = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
        inner = tk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor='nw')
        canvas.configure(yscrollcommand=yscroll.set)
        canvas.pack(side='left', fill='both', expand=True)
        yscroll.pack(side='right', fill='y')

        vars_map = {}
        def rebuild():
            for w in inner.winfo_children():
                w.destroy()
            query = search_var.get().lower()
            shown = [c for c in cols if query in c.lower()]
            for c in shown:
                v = vars_map.get(c) or tk.BooleanVar(value=(self.selected_columns is None or c in self.selected_columns))
                vars_map[c] = v
                ttk.Checkbutton(inner, text=c, variable=v).pack(anchor='w')
        rebuild()

        def on_search(*_):
            rebuild()
        search_var.trace_add('write', on_search)

        btns = ttk.Frame(dlg)
        btns.pack(fill=tk.X, padx=10, pady=(0, 10))
        def select_all():
            for c in cols:
                vars_map[c].set(True)
        def select_none():
            for c in cols:
                vars_map[c].set(False)
        ttk.Button(btns, text="Select All", command=select_all).pack(side=tk.LEFT)
        ttk.Button(btns, text="Select None", command=select_none).pack(side=tk.LEFT, padx=6)

        def apply_and_close():
            chosen = [c for c in cols if vars_map[c].get()]
            self.selected_columns = set(chosen) if len(chosen) != len(cols) else None
            self.refresh_view()
            dlg.destroy()
        ttk.Button(btns, text="Apply", command=apply_and_close).pack(side=tk.RIGHT)

    # ------------- Row inspector -------------
    def open_row_inspector(self, event=None):
        item = self.tree.identify_row(event.y) if event else None
        if not item:
            return
        values = self.tree.item(item, 'values')
        cols = self.tree['columns']
        if not cols:
            return
        dlg = tk.Toplevel(self)
        dlg.title("Row Details")
        dlg.geometry("600x600")
        canvas = tk.Canvas(dlg)
        yscroll = ttk.Scrollbar(dlg, orient='vertical', command=canvas.yview)
        frame = ttk.Frame(canvas)
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frame, anchor='nw')
        canvas.configure(yscrollcommand=yscroll.set)
        canvas.pack(side='left', fill='both', expand=True)
        yscroll.pack(side='right', fill='y')
        for c, v in zip(cols, values):
            r = ttk.Frame(frame)
            r.pack(fill=tk.X, padx=10, pady=4)
            ttk.Label(r, text=c+":", width=24).pack(side=tk.LEFT)
            txt = tk.Text(r, height=3, wrap='word')
            txt.insert('1.0', v)
            txt.configure(state='disabled')
            txt.pack(side=tk.LEFT, fill=tk.X, expand=True)


# -----------------------------
# CLI & main
# -----------------------------

def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--gui':
        app = CSVViewer()
        app.mainloop()
    else:
        parser = argparse.ArgumentParser(description="Print CSV file as a pretty table with filtering and column selection.")
        parser.add_argument("filename", nargs="?", default="items.csv", help="CSV file to print (default: items.csv)")
        parser.add_argument("-n", "--num-rows", type=int, default=None, help="Number of rows to print (default: all)")
        parser.add_argument("-c", "--columns", nargs="*", help="Columns to display (space separated)")
        parser.add_argument("-f", "--filter", nargs=2, metavar=("COLUMN", "VALUE"), help="Filter: COLUMN VALUE")
        args = parser.parse_args()

        filter_col, filter_val = (args.filter if args.filter else (None, None))
        print_csv_file(
            args.filename,
            num_rows=args.num_rows,
            columns=args.columns,
            filter_col=filter_col,
            filter_val=filter_val
        )

if __name__ == "__main__":
    main()
