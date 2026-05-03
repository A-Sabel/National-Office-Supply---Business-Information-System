import customtkinter as ctk
from PIL import Image
import os

class LoginScreen(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window Setup
        self.title("NOS Enterprise Portal - Login")
        self.geometry("900x550")
        self.resizable(False, False)

        # Layout Configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- LEFT PANEL (Branding) ---
        self.left_panel = ctk.CTkFrame(self, fg_color="#001440", corner_radius=0)
        self.left_panel.grid(row=0, column=0, sticky="nsew")

        try:
            # Using logo3.png as specified in your directory
            logo_path = r"national_office_supply_BIS_project\national_office_supply_BIS\src\assets\logo3.png"
            self.logo_img = ctk.CTkImage(Image.open(logo_path), size=(300, 150))
            self.logo_label = ctk.CTkLabel(self.left_panel, image=self.logo_img, text="")
            self.logo_label.pack(expand=True, pady=(50, 10))
        except Exception:
            self.logo_label = ctk.CTkLabel(self.left_panel, text="NOS", font=("Segoe UI", 40, "bold"), text_color="white")
            self.logo_label.pack(expand=True)

        ctk.CTkLabel(self.left_panel, text="Enterprise Portal", font=("Segoe UI", 20), text_color="#aeb9c4").pack(pady=5)
        ctk.CTkLabel(self.left_panel, text="Empowering Productivity, Worldwide.", font=("Segoe UI", 12), text_color="#5dade2").pack(pady=(0, 50))

        # --- RIGHT PANEL (Form) ---
        self.right_panel = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=0)
        self.right_panel.grid(row=0, column=1, sticky="nsew")

        # This container will be cleared and repopulated when switching
        self.form_container = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.form_container.place(relx=0.5, rely=0.5, anchor="center")

        # Initial Load
        self.show_login_form()

    def clear_form(self):
        """Removes all widgets from the form container."""
        for widget in self.form_container.winfo_children():
            widget.destroy()

    def show_login_form(self):
        self.clear_form()

        # Header
        ctk.CTkLabel(self.form_container, text="Welcome Back", font=("Segoe UI", 28, "bold"), text_color="#001440").pack(pady=(0, 5))
        ctk.CTkLabel(self.form_container, text="Sign in to your account", font=("Segoe UI", 14), text_color="#7f8c8d").pack(pady=(0, 30))

        # Inputs
        self.username = ctk.CTkEntry(self.form_container, placeholder_text="Username or Employee ID", 
                                     width=300, height=45, corner_radius=5, fg_color="#333333", text_color="white")
        self.username.pack(pady=10)

        self.password = ctk.CTkEntry(self.form_container, placeholder_text="Password", show="*", 
                                     width=300, height=45, corner_radius=5, fg_color="#333333", text_color="white")
        self.password.pack(pady=10)

        # Login Button
        self.login_btn = ctk.CTkButton(self.form_container, text="Login", width=300, height=45, corner_radius=5, 
                                       fg_color="#3498db", hover_color="#2980b9", font=("Segoe UI", 14, "bold"), 
                                       command=self.handle_login)
        self.login_btn.pack(pady=25)

        # Footer Links
        self.links_frame = ctk.CTkFrame(self.form_container, fg_color="transparent")
        self.links_frame.pack()
        
        forgot_link = ctk.CTkLabel(self.links_frame, text="Forgot Password?", font=("Segoe UI", 11), 
                                   text_color="#3498db", cursor="hand2")
        forgot_link.pack(side="left", padx=10)
        # Bind it to the new method
        forgot_link.bind("<Button-1>", lambda e: self.show_forgot_password_form())
        
        signup_link = ctk.CTkLabel(self.links_frame, text="Create Account", font=("Segoe UI", 11), 
                                   text_color="#3498db", cursor="hand2")
        signup_link.pack(side="left", padx=10)
        signup_link.bind("<Button-1>", lambda e: self.show_signup_form())
        

    def show_signup_form(self):
        self.clear_form()

        # Header
        ctk.CTkLabel(self.form_container, text="Join the Network", font=("Segoe UI", 28, "bold"), text_color="#001440").pack(pady=(0, 5))
        ctk.CTkLabel(self.form_container, text="Create your employee portal account", font=("Segoe UI", 14), text_color="#7f8c8d").pack(pady=(0, 30))

        # Signup Inputs
        self.full_name = ctk.CTkEntry(self.form_container, placeholder_text="Full Name", width=300, height=40)
        self.full_name.pack(pady=5)

        self.reg_user = ctk.CTkEntry(self.form_container, placeholder_text="Employee ID / Username", width=300, height=40)
        self.reg_user.pack(pady=5)

        self.reg_pass = ctk.CTkEntry(self.form_container, placeholder_text="Create Password", show="*", width=300, height=40)
        self.reg_pass.pack(pady=5)

        self.confirm_pass = ctk.CTkEntry(self.form_container, placeholder_text="Confirm Password", show="*", width=300, height=40)
        self.confirm_pass.pack(pady=5)

        # Register Button
        self.reg_btn = ctk.CTkButton(self.form_container, text="Create Account", width=300, height=45, corner_radius=5, 
                                     fg_color="#2ecc71", hover_color="#27ae60", font=("Segoe UI", 14, "bold"), 
                                     command=self.handle_signup)
        self.reg_btn.pack(pady=20)

        # Back to Login
        back_link = ctk.CTkLabel(self.form_container, text="Already have an account? Sign In", 
                                 font=("Segoe UI", 11), text_color="#3498db", cursor="hand2")
        back_link.pack()
        back_link.bind("<Button-1>", lambda e: self.show_login_form())

    def handle_login(self):
        print(f"Logging in: {self.username.get()}")
        # Integrate with DatabaseManager later
        if hasattr(self, 'on_success'):
            self.on_success("Manager")

    def handle_signup(self):
        print(f"Registering: {self.reg_user.get()}")
        # Add logic to save to PostgreSQL/SQLite here
        self.show_login_form()
        
    def show_forgot_password_form(self):
        self.clear_form()

        # Header
        ctk.CTkLabel(self.form_container, text="Security Verification", 
                     font=("Segoe UI", 28, "bold"), text_color="#001440").pack(pady=(0, 5))
        ctk.CTkLabel(self.form_container, text="Verify your identity to change password", 
                     font=("Segoe UI", 14), text_color="#7f8c8d").pack(pady=(0, 30))

        # Verification Inputs
        self.verify_user = ctk.CTkEntry(self.form_container, placeholder_text="Username or Employee ID", 
                                        width=300, height=40)
        self.verify_user.pack(pady=5)

        self.new_pass = ctk.CTkEntry(self.form_container, placeholder_text="New Password", 
                                     show="*", width=300, height=40)
        self.new_pass.pack(pady=5)

        self.confirm_new_pass = ctk.CTkEntry(self.form_container, placeholder_text="Confirm New Password", 
                                             show="*", width=300, height=40)
        self.confirm_new_pass.pack(pady=5)

        # Update Button
        self.update_btn = ctk.CTkButton(self.form_container, text="Update Password", 
                                        width=300, height=45, corner_radius=5, 
                                        fg_color="#e67e22", hover_color="#d35400", 
                                        font=("Segoe UI", 14, "bold"), 
                                        command=self.handle_password_change)
        self.update_btn.pack(pady=20)

        # Back to Login
        back_link = ctk.CTkLabel(self.form_container, text="Return to Sign In", 
                                 font=("Segoe UI", 11), text_color="#3498db", cursor="hand2")
        back_link.pack()
        back_link.bind("<Button-1>", lambda e: self.show_login_form())

    def handle_password_change(self):
        # Technical Lead Tip: Add a simple validation check here
        user = self.verify_user.get()
        p1 = self.new_pass.get()
        p2 = self.confirm_new_pass.get()

        if p1 == p2 and len(p1) > 0:
            print(f"Password updated for user: {user}")
            # Later, this will be an UPDATE query in your PostgreSQL database
            self.show_login_form()
        else:
            print("Passwords do not match or are empty.")

if __name__ == "__main__":
    app = LoginScreen()
    app.mainloop()