from typing import Optional


class AppSession:
    def __init__(self):
        self.employee_number: Optional[int] = None
        self.employee_name: Optional[str] = None
        self.role: Optional[str] = None  # Manager, Sales Rep, or Hourly

    def login(self, employee_number, employee_name, role):
        self.employee_number = employee_number
        self.employee_name = employee_name
        self.role = role
        print(f"[SECURITY] Session started for: {self.employee_name} ({self.role})")

    def logout(self):
        self.employee_number = None
        self.employee_name = None
        self.role = None
        print("[SECURITY] Session terminated.")

    def is_authenticated(self):
        return self.employee_number is not None
