from functools import wraps

def require_role(allowed_roles):
    """
    Decorator to restrict method access based on user role.
    Assumes the class using it has a 'self.session' attribute.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # 1. Fail-safe: Check if session exists at all
            if not hasattr(self, 'session') or self.session is None:
                raise PermissionError("System Error: No active security session found.")
            
            # 2. RBAC Enforcement
            if self.session.role not in allowed_roles:
                raise PermissionError(
                    f"Access Denied: The role '{self.session.role}' is not authorized to perform this action."
                )
                
            # 3. If passed, execute the actual database function
            return func(self, *args, **kwargs)
        return wrapper
    return decorator