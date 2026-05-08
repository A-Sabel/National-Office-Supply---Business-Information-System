from tkinter import ttk
import customtkinter as ctk


class CustomerTable(ctk.CTkFrame):
    COLUMNS = (
        "ID",
        "Company",
        "Contact",
        "Phone",
        "Address",
        "Balance",
        "Active",
        "Tier",
    )

    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color="#ffffff",
            corner_radius=12,
            border_width=1,
            border_color="#e0e0e0",
        )

        self._row_index = 0
        self._row_base_tags = {}
        self._hover_item = None

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Customers.Treeview",
            font=("Segoe UI", 11),
            rowheight=32,
            background="#ffffff",
            fieldbackground="#ffffff",
            borderwidth=0,
        )
        style.configure(
            "Customers.Treeview.Heading",
            font=("Segoe UI", 11, "bold"),
            background="#2c3e50",
            foreground="#ffffff",
            relief="flat",
        )
        style.map("Customers.Treeview.Heading", 
                    background=[("active", "#34495e")],
                    foreground=[("active", "#ffffff")])

        self.tree = ttk.Treeview(
            self,
            columns=self.COLUMNS,
            show="headings",
            height=20,
            style="Customers.Treeview",
        )
        self._configure_columns()

        self.tree.tag_configure("even", background="#ffffff", foreground="#2c3e50")
        self.tree.tag_configure("odd", background="#f2f4f7", foreground="#2c3e50")
        self.tree.tag_configure(
            "debt_even",
            background="#fff1f1",
            foreground="#b42318",
            font=("Segoe UI", 11, "bold"),
        )
        self.tree.tag_configure(
            "debt_odd",
            background="#fee9e9",
            foreground="#b42318",
            font=("Segoe UI", 11, "bold"),
        )
        self.tree.tag_configure(
            "hover_even", background="#eef3f9", foreground="#2c3e50"
        )
        self.tree.tag_configure("hover_odd", background="#e8eef6", foreground="#2c3e50")
        self.tree.tag_configure(
            "hover_debt_even",
            background="#fbe9e9",
            foreground="#a61b1b",
            font=("Segoe UI", 11, "bold"),
        )
        self.tree.tag_configure(
            "hover_debt_odd",
            background="#f8e2e2",
            foreground="#a61b1b",
            font=("Segoe UI", 11, "bold"),
        )

        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)
        self.vsb.pack(side="right", fill="y")
        self.hsb.pack(side="bottom", fill="x", padx=10, pady=(0, 8))
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree.bind("<Motion>", self._on_row_hover)
        self.tree.bind("<Leave>", self._clear_hover)

        self.empty_state = ctk.CTkFrame(
            self,
            fg_color="#ffffff",
            corner_radius=10,
            border_width=1,
            border_color="#e5e7eb",
        )
        self.empty_title = ctk.CTkLabel(
            self.empty_state,
            text="No customers found",
            font=("Segoe UI", 15, "bold"),
            text_color="#2c3e50",
        )
        self.empty_title.pack(pady=(20, 6), padx=20)
        self.empty_subtitle = ctk.CTkLabel(
            self.empty_state,
            text="Try clearing filters or changing your search.",
            font=("Segoe UI", 12),
            text_color="#7f8c8d",
        )
        self.empty_subtitle.pack(pady=(0, 20), padx=20)

    def _configure_columns(self):
        self.tree.heading("ID", text="ID")
        self.tree.column("ID", width=60, anchor="center")

        self.tree.heading("Company", text="Company")
        self.tree.column("Company", width=220, anchor="w")

        self.tree.heading("Contact", text="Contact")
        self.tree.column("Contact", width=160, anchor="w")

        self.tree.heading("Phone", text="Phone")
        self.tree.column("Phone", width=130, anchor="w")

        self.tree.heading("Address", text="Address")
        self.tree.column("Address", width=300, anchor="w")

        self.tree.heading("Balance", text="Balance")
        self.tree.column("Balance", width=130, anchor="e")

        self.tree.heading("Active", text="Active")
        self.tree.column("Active", width=80, anchor="center")

        self.tree.heading("Tier", text="Tier")
        self.tree.column("Tier", width=100, anchor="w")

    def clear(self):
        self._row_index = 0
        self._row_base_tags = {}
        self._hover_item = None
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.hide_empty_state()

    def insert_row(self, values, balance: float = 0.0):
        is_even = self._row_index % 2 == 0
        if balance > 0:
            tag = "debt_even" if is_even else "debt_odd"
        else:
            tag = "even" if is_even else "odd"

        item_id = self.tree.insert("", "end", values=values, tags=(tag,))
        self._row_base_tags[item_id] = tag
        self._row_index += 1

    def _hover_tag_for(self, base_tag):
        mapping = {
            "even": "hover_even",
            "odd": "hover_odd",
            "debt_even": "hover_debt_even",
            "debt_odd": "hover_debt_odd",
        }
        return mapping.get(base_tag, base_tag)

    def _restore_item_tag(self, item_id):
        base_tag = self._row_base_tags.get(item_id)
        if base_tag is not None:
            self.tree.item(item_id, tags=(base_tag,))

    def _clear_hover(self, _event=None):
        if self._hover_item:
            self._restore_item_tag(self._hover_item)
            self._hover_item = None

    def _on_row_hover(self, event):
        item_id = self.tree.identify_row(event.y)

        if item_id == self._hover_item:
            return

        if self._hover_item:
            self._restore_item_tag(self._hover_item)
            self._hover_item = None

        if not item_id:
            return

        base_tag = self._row_base_tags.get(item_id)
        if base_tag is None:
            return

        hover_tag = self._hover_tag_for(base_tag)
        if hover_tag is None:
            return

        # Ensure we pass a tuple of strings (no None) to `tags`
        self.tree.item(item_id, tags=(hover_tag,))
        self._hover_item = item_id

    def show_empty_state(self, title: str, subtitle: str):
        self.empty_title.configure(text=title)
        self.empty_subtitle.configure(text=subtitle)
        self.empty_state.place(relx=0.5, rely=0.48, anchor="center")
        try:
            # Ensure the empty-state card is above the treeview and scrollbars
            self.empty_state.lift()
        except Exception:
            # Fallback for widget implementations without lift
            try:
                self.empty_state.tkraise()
            except Exception:
                pass

    def hide_empty_state(self):
        self.empty_state.place_forget()
