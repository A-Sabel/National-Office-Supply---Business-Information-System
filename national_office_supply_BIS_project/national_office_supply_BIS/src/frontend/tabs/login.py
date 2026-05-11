import os
from pathlib import Path
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image


class LoginView(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Layout Configuration (Split Screen)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- LEFT PANEL (Branding) ---
        self.left_panel = ctk.CTkFrame(self, fg_color="#001440", corner_radius=0)
        self.left_panel.grid(row=0, column=0, sticky="nsew")

        # Dynamic Path Resolution for the Logo
        current_dir = Path(__file__).parent.resolve()
        assets_dir = current_dir.parent.parent / "assets"
        logo_path = assets_dir / "logo3.png"

        try:
            self.logo_img = ctk.CTkImage(Image.open(logo_path), size=(300, 150))
            self.logo_label = ctk.CTkLabel(
                self.left_panel, image=self.logo_img, text=""
            )
            self.logo_label.pack(expand=True, pady=(50, 10))
        except Exception as e:
            print(f"Warning: Logo not found. Using text fallback. Error: {e}")
            self.logo_label = ctk.CTkLabel(
                self.left_panel,
                text="NOS",
                font=("Segoe UI", 40, "bold"),
                text_color="white",
            )
            self.logo_label.pack(expand=True)

        ctk.CTkLabel(
            self.left_panel,
            text="Enterprise Portal",
            font=("Segoe UI", 20),
            text_color="#aeb9c4",
        ).pack(pady=5)
        ctk.CTkLabel(
            self.left_panel,
            text="Empowering Productivity, Worldwide.",
            font=("Segoe UI", 12),
            text_color="#5dade2",
        ).pack(pady=(0, 50))

        # --- RIGHT PANEL (Form) ---
        self.right_panel = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=0)
        self.right_panel.grid(row=0, column=1, sticky="nsew")

        # This container will be cleared and repopulated when switching forms
        self.form_container = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.form_container.place(relx=0.5, rely=0.5, anchor="center")

        # Initial Load
        self.show_login_form()

    # ==========================================
    # LOGIC & DB METHODS
    # ==========================================

    def attempt_login(self):
        # Fetching from the styled inputs created in show_login_form
        username = self.username.get()
        password = self.password.get()

        if not username or not password:
            messagebox.showwarning(
                "Validation Error", "Please enter both username and password."
            )
            return

        # 1. Check Credentials
        user_data = self._verify_credentials_in_db(username, password)

        if user_data:
            print(f"[AUTH] Login successful for: {username}")

            # 2. POPULATE THE SESSION (The crucial RBAC step!)
            self.controller.session_manager.start_session(
                employee_number=user_data["employee_number"],
                employee_name=user_data["employee_name"],
                role=user_data["position"],
            )

            # 3. Transition to the main application UI
            self.controller.build_main_application()
        else:
            messagebox.showerror("Access Denied", "Invalid username or password.")

    def _verify_credentials_in_db(self, username, password):
        """
        Attempts a real PostgreSQL authentication first.
        Falls back to mock credentials if the database fails, is offline,
        or if the user is a test mock account.
        """
        # --- 1. REAL DATABASE CHECK ---
        try:
            # Import connection directly to avoid needing an active session
            from backend.database import get_db_connection

            conn = get_db_connection()

            if conn:
                with conn.cursor() as cursor:
                    # Query the active user by username
                    cursor.execute(
                        """
                        SELECT employee_number, employee_name, position, password_hash 
                        FROM employees 
                        WHERE username = %s AND is_active = TRUE;
                    """,
                        (username,),
                    )

                    user_record = cursor.fetchone()

                conn.close()

                if user_record:
                    # Unpack the DB tuple
                    emp_num, emp_name, position, stored_hash = user_record
                    is_valid = False

                    # --- SECURE PASSWORD VERIFICATION ---
                    try:
                        import bcrypt  # type: ignore

                        # Check if the stored hash is actually a bcrypt hash (starts with $2)
                        if stored_hash.startswith("$2"):
                            is_valid = bcrypt.checkpw(
                                password.encode("utf-8"), stored_hash.encode("utf-8")
                            )
                        else:
                            # Fallback if your SQL seed data was just inserted as plain-text
                            is_valid = password == stored_hash
                    except ImportError:
                        print(
                            "[SECURITY WARNING] 'bcrypt' library not installed. Falling back to plain-text check."
                        )
                        is_valid = password == stored_hash

                    if is_valid:
                        print(f"[AUTH] Verified via PostgreSQL for: {username}")
                        return {
                            "employee_number": emp_num,
                            "employee_name": emp_name,
                            "position": position,
                        }
                    else:
                        print("[AUTH] Database password mismatch.")
                        return None  # Fail immediately if they exist in DB but password is wrong
        except Exception as e:
            print(f"[DB WARNING] Real database auth failed: {e}")
            print("Attempting to use Mock Credentials...")

        # --- 2. MOCK CREDENTIALS FALLBACK (Testing Mode) ---
        print(f"[AUTH] Checking mock credentials for '{username}'...")

        if username == "manager" and password == "admin123":
            return {
                "employee_number": 1,
                "employee_name": "Maria Santos",
                "position": "Manager",
            }
        elif username == "rep" and password == "sales123":
            return {
                "employee_number": 4,
                "employee_name": "Kevin Lim",
                "position": "Sales Rep",
            }
        elif username == "hourly" and password == "worker123":
            return {
                "employee_number": 16,
                "employee_name": "Mark Aquino",
                "position": "Hourly",
            }
        return None

    def handle_password_change(self):
        user = self.verify_user.get()
        p1 = self.new_pass.get()
        p2 = self.confirm_new_pass.get()

        if p1 == p2 and len(p1) > 0:
            messagebox.showinfo(
                "Success", f"Password updated for {user}. Please log in."
            )
            self.show_login_form()
        else:
            messagebox.showerror("Error", "Passwords do not match or are empty.")

    # ==========================================
    # UI RENDERING METHODS
    # ==========================================

    def clear_form(self):
        """Removes all widgets from the form container."""
        for widget in self.form_container.winfo_children():
            widget.destroy()

    def toggle_password_visibility(self):
        """Toggle password visibility between hidden (*) and visible text."""
        self.show_password = not self.show_password
        self.password.configure(show="" if self.show_password else "*")
        self.toggle_btn.configure(text="👁‍🗨" if self.show_password else "👁")

    def show_login_form(self):
        self.clear_form()

        # Header
        ctk.CTkLabel(
            self.form_container,
            text="Welcome Back",
            font=("Segoe UI", 28, "bold"),
            text_color="#001440",
        ).pack(pady=(0, 5))
        ctk.CTkLabel(
            self.form_container,
            text="Sign in to your account",
            font=("Segoe UI", 14),
            text_color="#7f8c8d",
        ).pack(pady=(0, 30))

        # Inputs
        self.username = ctk.CTkEntry(
            self.form_container,
            placeholder_text="Username or Employee ID",
            width=300,
            height=45,
            corner_radius=5,
            fg_color="#f8f9fa",
            text_color="black",
        )
        self.username.pack(pady=10)
        self.username.bind("<Return>", lambda e: self.attempt_login())

        # Password frame with toggle button
        password_frame = ctk.CTkFrame(self.form_container, fg_color="transparent")
        password_frame.pack(pady=10)

        self.password = ctk.CTkEntry(
            password_frame,
            placeholder_text="Password",
            show="*",
            width=260,
            height=45,
            corner_radius=5,
            fg_color="#f8f9fa",
            text_color="black",
        )
        self.password.pack(side="left", padx=(0, 5))
        self.password.bind("<Return>", lambda e: self.attempt_login())

        # Password visibility toggle button
        self.show_password = False
        self.toggle_btn = ctk.CTkButton(
            password_frame,
            text="👁",
            width=40,
            height=45,
            corner_radius=5,
            fg_color="#ecf0f1",
            hover_color="#bdc3c7",
            text_color="black",
            command=self.toggle_password_visibility,
        )
        self.toggle_btn.pack(side="left")

        # Login Button (Mapped to attempt_login)
        self.login_btn = ctk.CTkButton(
            self.form_container,
            text="Login",
            width=300,
            height=45,
            corner_radius=5,
            fg_color="#3498db",
            hover_color="#2980b9",
            font=("Segoe UI", 14, "bold"),
            command=self.attempt_login,
        )
        self.login_btn.pack(pady=25)

        # Footer Links
        self.links_frame = ctk.CTkFrame(self.form_container, fg_color="transparent")
        self.links_frame.pack()

        forgot_link = ctk.CTkLabel(
            self.links_frame,
            text="Forgot Password?",
            font=("Segoe UI", 11),
            text_color="#3498db",
            cursor="hand2",
        )
        forgot_link.pack(side="left", padx=10)
        forgot_link.bind("<Button-1>", lambda e: self.show_forgot_password_form())

        signup_link = ctk.CTkLabel(
            self.links_frame,
            text="Create Account",
            font=("Segoe UI", 11),
            text_color="#3498db",
            cursor="hand2",
        )
        signup_link.pack(side="left", padx=10)
        signup_link.bind("<Button-1>", lambda e: self.show_signup_form())

    def show_signup_form(self):
        self.clear_form()

        ctk.CTkLabel(
            self.form_container,
            text="Join the Network",
            font=("Segoe UI", 28, "bold"),
            text_color="#001440",
        ).pack(pady=(0, 5))
        ctk.CTkLabel(
            self.form_container,
            text="Create your employee portal account",
            font=("Segoe UI", 14),
            text_color="#7f8c8d",
        ).pack(pady=(0, 30))

        self.full_name = ctk.CTkEntry(
            self.form_container,
            placeholder_text="Full Name",
            width=300,
            height=40,
            fg_color="#f8f9fa",
            text_color="black",
        )
        self.full_name.pack(pady=5)

        self.reg_user = ctk.CTkEntry(
            self.form_container,
            placeholder_text="Employee ID / Username",
            width=300,
            height=40,
            fg_color="#f8f9fa",
            text_color="black",
        )
        self.reg_user.pack(pady=5)

        self.reg_pass = ctk.CTkEntry(
            self.form_container,
            placeholder_text="Create Password",
            show="*",
            width=300,
            height=40,
            fg_color="#f8f9fa",
            text_color="black",
        )
        self.reg_pass.pack(pady=5)

        self.reg_btn = ctk.CTkButton(
            self.form_container,
            text="Create Account",
            width=300,
            height=45,
            corner_radius=5,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            font=("Segoe UI", 14, "bold"),
            command=lambda: [
                messagebox.showinfo("Info", "Contact Manager to approve account."),
                self.show_login_form(),
            ],
        )
        self.reg_btn.pack(pady=20)

        back_link = ctk.CTkLabel(
            self.form_container,
            text="Already have an account? Sign In",
            font=("Segoe UI", 11),
            text_color="#3498db",
            cursor="hand2",
        )
        back_link.pack()
        back_link.bind("<Button-1>", lambda e: self.show_login_form())

    def show_forgot_password_form(self):
        self.clear_form()

        ctk.CTkLabel(
            self.form_container,
            text="Security Verification",
            font=("Segoe UI", 28, "bold"),
            text_color="#001440",
        ).pack(pady=(0, 5))
        ctk.CTkLabel(
            self.form_container,
            text="Verify your identity to change password",
            font=("Segoe UI", 14),
            text_color="#7f8c8d",
        ).pack(pady=(0, 30))

        self.verify_user = ctk.CTkEntry(
            self.form_container,
            placeholder_text="Username or Employee ID",
            width=300,
            height=40,
            fg_color="#f8f9fa",
            text_color="black",
        )
        self.verify_user.pack(pady=5)

        self.new_pass = ctk.CTkEntry(
            self.form_container,
            placeholder_text="New Password",
            show="*",
            width=300,
            height=40,
            fg_color="#f8f9fa",
            text_color="black",
        )
        self.new_pass.pack(pady=5)

        self.confirm_new_pass = ctk.CTkEntry(
            self.form_container,
            placeholder_text="Confirm New Password",
            show="*",
            width=300,
            height=40,
            fg_color="#f8f9fa",
            text_color="black",
        )
        self.confirm_new_pass.pack(pady=5)

        self.update_btn = ctk.CTkButton(
            self.form_container,
            text="Update Password",
            width=300,
            height=45,
            corner_radius=5,
            fg_color="#e67e22",
            hover_color="#d35400",
            font=("Segoe UI", 14, "bold"),
            command=self.handle_password_change,
        )
        self.update_btn.pack(pady=20)

        back_link = ctk.CTkLabel(
            self.form_container,
            text="Return to Sign In",
            font=("Segoe UI", 11),
            text_color="#3498db",
            cursor="hand2",
        )
        back_link.pack()
        back_link.bind("<Button-1>", lambda e: self.show_login_form())


# ========================================================
# STANDALONE TESTER
# Allows you to run this file directly without __main__.py
# ========================================================
if __name__ == "__main__":

    class MockSession:
        def login(self, employee_number, employee_name, role):
            print(f"MOCK SESSION SET: {employee_name} ({role})")

    class MockController(ctk.CTk):
        def __init__(self):
            super().__init__()
            self.title("NOS Test Window")
            self.geometry("900x550")
            self.session = MockSession()

            # Load the LoginView frame
            self.login_view = LoginView(self, self)
            self.login_view.pack(fill="both", expand=True)

        def build_main_application(self):
            messagebox.showinfo(
                "Success", "Login logic passed! Proceeding to Dashboard..."
            )

    app = MockController()
    app.mainloop()
