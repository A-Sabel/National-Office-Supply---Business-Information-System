"""
Monkey-patch for CustomTkinter mouse-wheel scroll bug.

Issue: CTkScrollableFrame._mouse_wheel_all() fails when event.widget is a string
(widget name) instead of the actual widget object. This patch wraps the method
to handle this edge case gracefully.
"""

import customtkinter as ctk


def patch_ctk_mouse_wheel():
    """Patch CTkScrollableFrame to handle string widget references in mouse-wheel events."""
    original_mouse_wheel = ctk.CTkScrollableFrame._mouse_wheel_all

    def patched_mouse_wheel(self, event):
        """Wrapper that safely handles event.widget as string or widget object."""
        try:
            # Ensure event.widget is a widget object, not a string
            widget = event.widget
            if isinstance(widget, str):
                # If it's a string (widget name), try to get the actual widget
                widget = self.nametowidget(widget)
                event.widget = widget
            return original_mouse_wheel(self, event)
        except (AttributeError, KeyError, TypeError):
            # Silently ignore wheel events that can't be processed
            pass

    ctk.CTkScrollableFrame._mouse_wheel_all = patched_mouse_wheel
