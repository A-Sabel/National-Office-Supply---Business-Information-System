import customtkinter as ctk
import psycopg2

class ProfileOverlay(ctk.CTkFrame):
    def __init__(self, parent, controller, session, db_config, is_pinned=False):
        super().__init__(parent, fg_color="#ffffff", corner_radius=12, 
                         border_width=2 if is_pinned else 1, 
                         border_color="#3498db" if is_pinned else "#e0e0e0", width=340)
        
        self.controller = controller
        self.session = session
        self.db_config = db_config
        
        # --- State for SSN Toggling ---
        self.full_ssn = "000-00-0000"
        self.ssn_hidden = True
        self.full_address = "No Address Loaded"

        # 1. Fetch the extra details from DB
        self._fetch_employee_details()

        # --- 1. HEADER ---
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=20, pady=(15, 5))
        
        top_row = ctk.CTkFrame(self.header, fg_color="transparent")
        top_row.pack(fill="x")
        
        ctk.CTkLabel(top_row, text="👤", font=("Segoe UI", 32)).pack(side="left", padx=(0, 15))
        
        text_stack = ctk.CTkFrame(top_row, fg_color="transparent")
        text_stack.pack(side="left")
        
        ctk.CTkLabel(text_stack, text=self.session.employee_name, font=("Segoe UI", 16, "bold"), 
                 text_color="#2c3e50").pack(anchor="w")
        # Map internal Hourly role to a display label "Regular" (frontend-only)
        role_display = "Regular" if getattr(self.session, "role", "") == "Hourly" else getattr(self.session, "role", "")
        ctk.CTkLabel(text_stack, text=role_display, font=("Segoe UI", 12), 
                 text_color="#3498db").pack(anchor="w")

        # --- 2. INFO SECTION ---
        self.info_container = ctk.CTkFrame(self, fg_color="#f8f9fa", corner_radius=10)
        self.info_container.pack(fill="x", padx=15, pady=10)

        # Row 1: ID and Status
        self._add_compact_row(self.info_container, "EMP ID", f"#{self.session.employee_number:04d}", "STATUS", "Active")

        # Row 2: SSN with Toggle (Masked by default)
        ssn_row = ctk.CTkFrame(self.info_container, fg_color="transparent")
        ssn_row.pack(fill="x", padx=10, pady=4)
        
        ctk.CTkLabel(ssn_row, text="SSN:", font=("Segoe UI", 10, "bold"), text_color="#34495e").pack(side="left")
        self.ssn_label = ctk.CTkLabel(ssn_row, text=self._get_masked_ssn(), font=("Segoe UI", 10), text_color="#7f8c8d")
        self.ssn_label.pack(side="left", padx=5)
        
        self.toggle_btn = ctk.CTkButton(ssn_row, text="👁", width=20, height=20, fg_color="transparent", 
                                        text_color="#3498db", hover_color="#e0e0e0", command=self._toggle_ssn)
        self.toggle_btn.pack(side="left")

        # Row 3: Address (From Database)
        addr_row = ctk.CTkFrame(self.info_container, fg_color="transparent")
        addr_row.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(addr_row, text="ADDR:", font=("Segoe UI", 10, "bold"), text_color="#34495e").pack(side="left")
        ctk.CTkLabel(addr_row, text=self.full_address, font=("Segoe UI", 10), text_color="#7f8c8d", 
                     wraplength=200, justify="left").pack(side="left", padx=5)

        # --- 3. LOGOUT ---
        ctk.CTkButton(self, text="Log Out", fg_color="#e74c3c", hover_color="#c0392b",
                      corner_radius=8, height=32, font=("Segoe UI", 12, "bold"),
                      command=self.controller.logout).pack(fill="x", padx=15, pady=(5, 15))

    def _fetch_employee_details(self):
        """Connects to DB to get SSN and Address for the current user."""
        try:
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            cur.execute("SELECT ssn, employee_address FROM employees WHERE employee_number = %s", 
                        (self.session.employee_number,))
            result = cur.fetchone()
            if result:
                self.full_ssn, self.full_address = result
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error fetching profile details: {e}")

    def _get_masked_ssn(self):
        """Returns the masked version of the SSN: ***-**-1234."""
        if len(self.full_ssn) < 4: return "***"
        return f"***-**-{self.full_ssn[-4:]}"

    def _toggle_ssn(self):
        """Switches between masked and full SSN."""
        if self.ssn_hidden:
            self.ssn_label.configure(text=self.full_ssn)
            self.toggle_btn.configure(text="🔒")
        else:
            self.ssn_label.configure(text=self._get_masked_ssn())
            self.toggle_btn.configure(text="👁")
        self.ssn_hidden = not self.ssn_hidden

    def _add_compact_row(self, container, L1, V1, L2, V2):
        row = ctk.CTkFrame(container, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=4)
        ctk.CTkLabel(row, text=f"{L1}:", font=("Segoe UI", 10, "bold"), text_color="#34495e").pack(side="left")
        ctk.CTkLabel(row, text=V1, font=("Segoe UI", 10), text_color="#7f8c8d").pack(side="left", padx=(5, 15))
        ctk.CTkLabel(row, text=V2, font=("Segoe UI", 10, "bold"), text_color="#2ecc71").pack(side="right")
        ctk.CTkLabel(row, text=f"{L2}:", font=("Segoe UI", 10, "bold"), text_color="#34495e").pack(side="right", padx=5)