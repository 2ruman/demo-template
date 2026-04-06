import customtkinter as ctk

_BASIC_COLORS = {
    "INFO":    "#2196F3",
    "SUCCESS": "#4CAF50",
    "WARNING": "#FF9800",
    "ERROR":   "#F44336",
}

_MODERN_DARK_COLORS = {
    "INFO":    "#1E2D3D",
    "SUCCESS": "#1A2E22",
    "WARNING": "#2E2210",
    "ERROR":   "#2E1515",
}

COLORS = _MODERN_DARK_COLORS


class ToastNotification:

    _stack = []
    _single = False
    _center = False
    _anchor = None  # widget to position next to (right side, vertically centered)

    def __init__(self, parent, message: str, duration: int = 2000, type: str = "INFO",
                 r_corner: bool = True):
        if ToastNotification._single:
            for t in ToastNotification._stack[:]:
                t.win.attributes("-alpha", 0.0)
                t._destroy()

        self.parent = parent
        self.message = message
        self.duration = duration
        self.type = type
        self.r_corner = r_corner
        self.win = ctk.CTkToplevel(self.parent)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.0)
        try:
            self.win.wm_attributes("-toolwindow", True)
        except Exception:
            pass

        fg_color = COLORS.get(type, list(COLORS)[0])

        self.frame = ctk.CTkFrame(self.win, fg_color=fg_color, corner_radius=15 if r_corner else 0)
        self.frame.pack(fill="both", expand=True)

        bc = self.frame.cget("bg_color")[-1]
        self.win.configure(bg=bc)
        self.win.configure(fg=bc)
        self.win.configure(bg_color=bc)
        self.win.configure(fg_color=bc)
        try:
            self.win.wm_attributes("-transparentcolor", bc)
        except Exception:
            pass

        wrap_length = 260
        ctk.CTkLabel(
            self.frame,
            text=message,
            text_color="white",
            wraplength=wrap_length,
            font=ctk.CTkFont(size=12),
            justify="left"
        ).pack(padx=18, pady=14)

        self.win.update_idletasks()

        ToastNotification._stack.append(self)
        self._reposition_all(self if self._single else None)
        self._fade_in()

    def _reposition_all(self, single=None):
        px = self.parent.winfo_rootx()
        py = self.parent.winfo_rooty()
        wx = px + 4
        wy = py + self.parent.winfo_height() - 4

        if single is not None:
            if self.frame.winfo_exists():
                anchor = ToastNotification._anchor
                if anchor is not None and anchor.winfo_exists():
                    th = self.win.winfo_height()
                    wx = anchor.winfo_rootx() + anchor.winfo_width() + 8
                    """ Center vs Top vs Bottom """
                    # Center-aligned
                    # wy = anchor.winfo_rooty() + (anchor.winfo_height() - th) // 2
                    # Top-aligned
                    wy = anchor.winfo_rooty()
                    # Bottom-aligned
                    # wy = anchor.winfo_rooty() + (anchor.winfo_height() - th)
                    """ ----------------------- """
                    self.win.geometry(f"+{wx}+{wy}")
                elif ToastNotification._center:
                    tw = self.win.winfo_width()
                    th = self.win.winfo_height()
                    wx = px + (self.parent.winfo_width() - tw) // 2
                    wy = py + (self.parent.winfo_height() - th) // 2
                    self.win.geometry(f"+{wx}+{wy}")
                else:
                    wy -= self.frame.winfo_height()
                    self.win.geometry(f"+{wx}+{wy}")
            return

        for t in reversed(ToastNotification._stack):
            wy -= t.frame.winfo_height()
            t.win.geometry(f"+{wx}+{wy}")
            wy -= 4

    def _fade_in(self, alpha: float = 0.0, step: float = 0.08):
        alpha = min(alpha + step, 1.0)
        self.win.attributes("-alpha", alpha)
        if alpha < 1.0:
            self.win.after(20, lambda: self._fade_in(alpha, step))
        else:
            self.win.after(self.duration, lambda: self._fade_out(alpha, step))

    def _fade_out(self, alpha: float = 1.0, step: float = 0.08):
        alpha = max(alpha - step, 0.0)
        self.win.attributes("-alpha", alpha)
        if alpha > 0.0:
            self.win.after(20, lambda: self._fade_out(alpha, step))
        else:
            self._destroy()

    def _destroy(self):
        if self in ToastNotification._stack:
            ToastNotification._stack.remove(self)
        self.win.destroy()
        self._reposition_all()


# For Test
if __name__ == "__main__":
    app = ctk.CTk()
    # app._set_appearance_mode("light")
    app._set_appearance_mode("dark")
    app.geometry("800x600")
    app.title("Toast Notification Test")

    MESSAGES = {
        "INFO": "Loading files...",
        "SUCCESS": "File saved successfully.",
        "WARNING":
        "Storage is full: Free up space or change where new content is saved. "
        "Storage is full: Free up space or change where new content is saved. "
        "Storage is full: Free up space or change where new content is saved.",
        "ERROR": "Network connection failed.",
    }

    controls = ctk.CTkFrame(app, fg_color="transparent")
    controls.pack(pady=(20, 0))
    ctk.CTkLabel(controls, text="Toast -> ").pack(side="left", padx=8, pady=10)
    for type, label in [("INFO", "Info"), ("SUCCESS", "Success"),
                        ("WARNING", "Warning"), ("ERROR", "Error")]:
        ctk.CTkButton(
            controls, text=label, width=80,
            command=lambda t=type: ToastNotification(app, MESSAGES[t], type=t),
            ).pack(side="left", padx=(0, 8))

    opts = ctk.CTkFrame(app, fg_color="transparent")
    opts.pack(pady=(10, 0))
    ctk.CTkLabel(opts, text="Single mode:").pack(side="left", padx=8, pady=8)

    def toggle_single():
        ToastNotification._single = not ToastNotification._single
        toggle_btn.configure(text=f"Single: {'ON' if ToastNotification._single else 'OFF'}")

    def toggle_center():
        ToastNotification._center = not ToastNotification._center
        center_btn.configure(text=f"Center: {'ON' if ToastNotification._center else 'OFF'}")

    toggle_btn = ctk.CTkButton(opts, text="Single: OFF", width=100, command=toggle_single)
    toggle_btn.pack(side="left", padx=(0, 8))

    center_btn = ctk.CTkButton(opts, text="Center: OFF", width=100, command=toggle_center)
    center_btn.pack(side="left", padx=(0, 8))

    app.mainloop()
