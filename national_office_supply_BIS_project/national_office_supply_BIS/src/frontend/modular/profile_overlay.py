import customtkinter as ctk

class ProfileOverlay(ctk.CTkFrame):
    def __init__(self, parent, username="Andrea Ysabela", designation="BSCS - 2D", role="Manager", is_pinned=False):
        # Increased width to 340px and added a subtle highlight if pinned
        border_color = "#3498db" if is_pinned else "#e0e0e0"
        super().__init__(parent, fg_color="#ffffff", corner_radius=12, 
                         border_width=2 if is_pinned else 1, border_color=border_color, width=340)
        
        # --- 1. COMPACT HEADER ---
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=20, pady=(15, 5)) # Reduced top/bottom padding
        
        # Avatar and Name on same line to save height
        self.top_row = ctk.CTkFrame(self.header, fg_color="transparent")
        self.top_row.pack(fill="x")
        
        ctk.CTkLabel(self.top_row, text="👤", font=("Segoe UI", 32)).pack(side="left", padx=(0, 15))
        
        self.text_stack = ctk.CTkFrame(self.top_row, fg_color="transparent")
        self.text_stack.pack(side="left")
        
        ctk.CTkLabel(self.text_stack, text=username, font=("Segoe UI", 16, "bold"), 
                     text_color="#2c3e50").pack(anchor="w")
        ctk.CTkLabel(self.text_stack, text=designation, font=("Segoe UI", 12), 
                     text_color="#7f8c8d").pack(anchor="w")

        # --- 2. TIGHTENED INFO SECTION ---
        self.info_container = ctk.CTkFrame(self, fg_color="#f8f9fa", corner_radius=10)
        self.info_container.pack(fill="x", padx=15, pady=10)

        # Using a 2-column approach inside rows to minimize vertical space
        self._add_compact_row("ID", "2026-TUP-001", "Dept", "Computing")
        self._add_compact_row("Role", role, "Status", "Active")

        # --- 3. SESSION ACTION ---
        self.logout_btn = ctk.CTkButton(
            self, text="Log Out", fg_color="#e74c3c", hover_color="#c0392b",
            text_color="white", corner_radius=8, height=32, font=("Segoe UI", 12, "bold"),
            command=lambda: parent.logout() 
        )
        self.logout_btn.pack(fill="x", padx=15, pady=(5, 15))

    def _add_compact_row(self, L1, V1, L2, V2):
        row = ctk.CTkFrame(self.info_container, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=4)
        
        # Column 1
        ctk.CTkLabel(row, text=f"{L1}:", font=("Segoe UI", 10, "bold"), text_color="#34495e").pack(side="left")
        ctk.CTkLabel(row, text=V1, font=("Segoe UI", 10), text_color="#95a5a6").pack(side="left", padx=(5, 15))
        
        # Column 2
        ctk.CTkLabel(row, text=V2, font=("Segoe UI", 10), text_color="#95a5a6").pack(side="right")
        ctk.CTkLabel(row, text=f"{L2}:", font=("Segoe UI", 10, "bold"), text_color="#34495e").pack(side="right", padx=5)