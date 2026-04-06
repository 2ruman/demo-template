import os
import queue
import threading
import time
from datetime import datetime
from typing import override

import customtkinter as ctk
from PIL import Image

from handler import Handler
from logger import Logger
from theme import COLORS
from toast import ToastNotification
from ups import UPLOADS_DIR, UploadServer

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8080
MIN_DISPLAY_SEC = 1.0


class LogView(ctk.CTkFrame):

    MAX_LINES = 2000
    TAG_FONT_NORM = ("Courier New", 8)
    TAG_FONT_BOLD = ("Courier New", 8, "bold")

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(fg_color=COLORS["bg"], corner_radius=12)

        toolbar = ctk.CTkFrame(self, fg_color=COLORS["panel"], corner_radius=8)
        toolbar.pack(fill="x", padx=(10, 0), pady=(10, 0))

        ctk.CTkLabel(
            toolbar, text="◉ LOG CONSOLE",
            font=ctk.CTkFont("Courier New", 11, "bold"),
            text_color=COLORS["accent2"],
        ).pack(side="left", padx=12, pady=6)

        self._auto_scroll = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            toolbar, text="Auto-scroll",
            variable=self._auto_scroll,
            font=ctk.CTkFont("Courier New", 10),
            text_color=COLORS["dim"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent2"],
            checkmark_color="white",
            border_color=COLORS["border"],
        ).pack(side="right", padx=(0, 10))

        self._notification = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            toolbar, text="Notification",
            variable=self._notification,
            font=ctk.CTkFont("Courier New", 10),
            text_color=COLORS["dim"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent2"],
            checkmark_color="white",
            border_color=COLORS["border"],
        ).pack(side="right", padx=(0, 10))

        ctk.CTkButton(
            toolbar, text="Clear",
            width=60, height=24,
            font=ctk.CTkFont("Courier New", 10),
            fg_color=COLORS["surface"],
            hover_color=COLORS["border"],
            text_color=COLORS["dim"],
            command=self.clear,
        ).pack(side="right", padx=(0, 10))

        self._text = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont("Courier New", 12),
            fg_color=COLORS["bg"],
            text_color=COLORS["fg"],
            border_width=1,
            border_color=COLORS["border"],
            corner_radius=8,
            wrap="none",
            state="disabled",
        )
        self._text.pack(fill="both", expand=True, padx=(10, 0), pady=(10, 0))

        self._setup_tags()
        self._lock = threading.Lock()
        self._line_count = 0

    def _setup_tags(self):
        tb = self._text._textbox
        for key in ("DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"):
            tb.tag_configure(key, foreground=COLORS[key], font=self.TAG_FONT_BOLD)
        tb.tag_configure("ts",   foreground=COLORS["ts"],   font=self.TAG_FONT_NORM)
        tb.tag_configure("name", foreground=COLORS["name"], font=self.TAG_FONT_NORM)
        tb.tag_configure("msg",  foreground=COLORS["fg"],   font=self.TAG_FONT_NORM)

    def append(self, timestamp: str, level: str, name: str, message: str):
        def _do():
            with self._lock:
                tb = self._text._textbox
                tb.configure(state="normal")
                self._line_count += 1
                if self._line_count > self.MAX_LINES:
                    tb.delete("1.0", "2.0")
                    self._line_count -= 1
                tb.insert("end", f"[{timestamp}] ", "ts")
                tb.insert("end", f"{level:<8}", level)
                tb.insert("end", f" {name}: ", "name")
                tb.insert("end", f"{message}\n", "msg")
                tb.configure(state="disabled")
                if self._auto_scroll.get():
                    tb.see("end")
        self._text.after(0, _do)

    @property
    def notification_enabled(self):
        return self._notification.get()

    def clear(self):
        tw = self._text._textbox
        tw.configure(state="normal")
        tw.delete("1.0", "end")
        tw.configure(state="disabled")
        self._line_count = 0


class ImageView(ctk.CTkFrame):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(fg_color=COLORS["bg"], corner_radius=12)

        toolbar = ctk.CTkFrame(self, fg_color=COLORS["panel"], corner_radius=8)
        toolbar.pack(fill="x", padx=(10, 0), pady=(10, 0))

        ctk.CTkLabel(
            toolbar, text="◈ IMAGE VIEWER",
            font=ctk.CTkFont("Courier New", 11, "bold"),
            text_color=COLORS["accent2"],
        ).pack(side="left", padx=12, pady=6)

        self._queue_label = ctk.CTkLabel(
            toolbar, text="Queue: 0",
            font=ctk.CTkFont("Courier New", 10),
            text_color=COLORS["dim"],
        )
        self._queue_label.pack(side="right", padx=(0, 12))

        self._filename_label = ctk.CTkLabel(
            toolbar, text="—",
            font=ctk.CTkFont("Courier New", 10),
            text_color=COLORS["dim"],
        )
        self._filename_label.pack(side="right", padx=(0, 12))

        self._img_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface"],
            corner_radius=8,
            border_width=1,
            border_color=COLORS["border"],
        )
        self._img_frame.pack(fill="both", expand=True, padx=(10, 0), pady=(10, 0))

        self._img_label = ctk.CTkLabel(
            self._img_frame,
            text="Waiting for images...",
            font=ctk.CTkFont("Courier New", 13),
            text_color=COLORS["dim"],
        )
        self._img_label.place(relx=0.5, rely=0.5, anchor="center")

    def show_image(self, img_path: str, queue_size: int = 0):
        def _do():
            try:
                w = self._img_frame.winfo_width()
                h = self._img_frame.winfo_height()
                if w < 10:
                    w, h = 500, 500

                pil_img = Image.open(img_path)
                pil_img.thumbnail((w - 20, h - 20), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(
                    light_image=pil_img, dark_image=pil_img,
                    size=(pil_img.width, pil_img.height),
                )
                self._img_label.configure(image=ctk_img, text="")
                self._img_label.image = ctk_img
                self._filename_label.configure(text=os.path.basename(img_path))
                self._queue_label.configure(text=f"Queue: {queue_size}")
            except Exception as e:
                self._img_label.configure(text=f"Error loading image:\n{e}", image=None)
        self._img_frame.after(0, _do)

    def update_queue_size(self, size: int):
        self._queue_label.configure(text=f"Queue: {size}")


class C2Server(ctk.CTk, Logger, Handler):

    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")

        self.title("C2 Server")
        self.geometry("1280x740")
        self.configure(fg_color=COLORS["bg"])

        self._img_queue = queue.Queue()
        self._total_received = 0
        self._running = False
        self._ups = None

        ToastNotification._single = True

        self._init_ui()
        self._start_servers()
        self._start_display_loop()

    def _init_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=COLORS["panel"], corner_radius=0, height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr, text="⬡ C2 Server",
            font=ctk.CTkFont("Courier New", 24, "bold"),
            text_color=COLORS["accent"],
        ).pack(side="left", padx=24)
        ctk.CTkLabel(
            hdr, text="Exfiltration Server - @2ruman",
            font=ctk.CTkFont("Courier New", 10),
            text_color=COLORS["dim"],
        ).pack(side="right", padx=24)

        # Body
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(12, 0))
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=5)
        body.columnconfigure(2, weight=4)
        body.rowconfigure(0, weight=1)
        body.rowconfigure(1, weight=0)

        # Sidebar (col 0)
        sidebar = ctk.CTkFrame(body, fg_color=COLORS["panel"], corner_radius=12)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._init_sidebar(sidebar)

        # Log View (col 1)
        self._log_view = LogView(body)
        self._log_view.grid(row=0, column=1, sticky="nsew", padx=(0, 8))

        # Image View (col 2)
        self._image_view = ImageView(body)
        self._image_view.grid(row=0, column=2, sticky="nsew")

        # Footer
        ctk.CTkLabel(
            body, text="https://github.com/2ruman",
            font=ctk.CTkFont("Courier New", 10),
            text_color=COLORS["dim"],
        ).grid(row=1, column=2, sticky="es")

    def _init_sidebar(self, parent):
        ctk.CTkLabel(
            parent, text="SERVER CONTROLS",
            font=ctk.CTkFont("Courier New", 11, "bold"),
            text_color=COLORS["accent2"],
        ).pack(pady=(18, 16), padx=16, anchor="w")

        # Profile Image
        img_frame = ctk.CTkFrame(parent, fg_color=COLORS["border"], corner_radius=6)
        img_frame.pack(pady=(0, 16), padx=16)

        img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profile", "profile.png")
        if os.path.exists(img_path):
            pil_img = Image.open(img_path)
            pil_img = pil_img.resize((120, 160), Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(120, 160))
            img_label = ctk.CTkLabel(img_frame, image=ctk_img, text="")
            img_label.image = ctk_img
            img_label.pack(padx=2, pady=2)
        else:
            img_label = ctk.CTkLabel(
                img_frame, text="NO IMAGE",
                font=ctk.CTkFont("Courier New", 12),
                text_color=COLORS["dim"],
                width=120, height=160,
            )
            img_label.pack(padx=2, pady=2)
        ToastNotification._anchor = img_label

        # Divider
        ctk.CTkFrame(parent, height=2, fg_color=COLORS["border"]).pack(fill="x", padx=16, pady=(0, 16))

        # Status
        status_frame = ctk.CTkFrame(parent, fg_color=COLORS["surface"], corner_radius=8)
        status_frame.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkLabel(
            status_frame, text="STATUS",
            font=ctk.CTkFont("Courier New", 9),
            text_color=COLORS["dim"],
        ).pack(anchor="w", padx=10, pady=(8, 2))
        self._status_label = ctk.CTkLabel(
            status_frame, text="● STOPPED",
            font=ctk.CTkFont("Courier New", 12, "bold"),
            text_color=COLORS["ERROR"],
        )
        self._status_label.pack(anchor="w", padx=10, pady=(0, 8))

        # Port
        port_frame = ctk.CTkFrame(parent, fg_color=COLORS["surface"], corner_radius=8)
        port_frame.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkLabel(
            port_frame, text="PORT",
            font=ctk.CTkFont("Courier New", 9),
            text_color=COLORS["dim"],
        ).pack(anchor="w", padx=10, pady=(8, 2))
        ctk.CTkLabel(
            port_frame, text=str(DEFAULT_PORT),
            font=ctk.CTkFont("Courier New", 14, "bold"),
            text_color=COLORS["fg"],
        ).pack(anchor="w", padx=10, pady=(0, 8))

        # Received count
        recv_frame = ctk.CTkFrame(parent, fg_color=COLORS["surface"], corner_radius=8)
        recv_frame.pack(fill="x", padx=16, pady=(0, 16))
        ctk.CTkLabel(
            recv_frame, text="RECEIVED",
            font=ctk.CTkFont("Courier New", 9),
            text_color=COLORS["dim"],
        ).pack(anchor="w", padx=10, pady=(8, 2))
        self._received_label = ctk.CTkLabel(
            recv_frame, text="0 images",
            font=ctk.CTkFont("Courier New", 12, "bold"),
            text_color=COLORS["INFO"],
        )
        self._received_label.pack(anchor="w", padx=10, pady=(0, 8))

        # Divider
        ctk.CTkFrame(parent, height=2, fg_color=COLORS["border"]).pack(fill="x", padx=16, pady=(0, 16))

        # Toggle button
        self._toggle_btn = ctk.CTkButton(
            parent, text="■  Stop Server",
            font=ctk.CTkFont("Courier New", 12, "bold"),
            fg_color=COLORS["ERROR"],
            hover_color="#cc3333",
            text_color="white",
            height=36,
            command=self._toggle_servers,
        )
        self._toggle_btn.pack(fill="x", padx=16)

        # Uploads path
        ctk.CTkFrame(parent, height=2, fg_color=COLORS["border"]).pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(
            parent, text=f"Uploads  »  {os.path.basename(UPLOADS_DIR)}",
            font=ctk.CTkFont("Courier New", 10),
            text_color=COLORS["dim"],
        ).pack(anchor="w", padx=16)

    @override
    def d(self, msg: str):
        self.after(0, lambda: self._log("DEBUG", msg))

    @override
    def i(self, msg: str):
        self.after(0, lambda: self._log("INFO", msg))

    @override
    def w(self, msg: str):
        self.after(0, lambda: self._log("WARNING", msg))

    @override
    def e(self, msg: str):
        self.after(0, lambda: self._log("ERROR", msg))

    @override
    def s(self, msg: str):
        self.after(0, lambda: self._log("SUCCESS", msg))

    @override
    def c(self, msg: str):
        self.after(0, lambda: self._log("CRITICAL", msg))

    def _log(self, level: str, message: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_view.append(ts, level, "server", message)

    def _start_servers(self):
        self._running = True
        if self._ups:
            self.d("Server already running")
            return
        else:
            self._ups = UploadServer(
                logger=self, handler=self, host=DEFAULT_HOST, port=DEFAULT_PORT).start()

        self.after(100, lambda: self._update_status(True))
        self.i(f"Server listening on {self._ups.host}:{self._ups.port}")
        self.i("POST /upload  —  where to send image files")
        self.d(f"Uploads directory: {UPLOADS_DIR}")

    def _stop_servers(self):
        self._running = False
        if self._ups:
            self._ups.shutdown()
            self._ups = None
        self.after(0, lambda: self._update_status(False))
        self.w("Server stopped")

    def _toggle_servers(self):
        if self._running:
            self._stop_servers()
        else:
            self._start_servers()

    def _update_status(self, running: bool):
        if running:
            self._status_label.configure(text="● RUNNING", text_color=COLORS["INFO"])
            self._toggle_btn.configure(
                text="■  Stop Server",
                fg_color=COLORS["ERROR"],
                hover_color="#cc3333",
            )
        else:
            self._status_label.configure(text="● STOPPED", text_color=COLORS["ERROR"])
            self._toggle_btn.configure(
                text="▶  Start Server",
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent2"],
            )

    @override
    def on_file_received(self, filepath: str, size: int):
        """Called from HTTP handler thread — thread-safe via after()"""
        self._img_queue.put(filepath)
        self._total_received += 1
        count = self._total_received
        qsize = self._img_queue.qsize()

        def _update():
            self._received_label.configure(text=f"{count} images")
            self.s(f"Saved: {os.path.basename(filepath)} ({size:,} bytes)")
            self.d(f"Queue size: {qsize}")
            if self._log_view.notification_enabled:
                ToastNotification(
                    self,
                    f"Received: {os.path.basename(filepath)} ({size:,} bytes)",
                    type="SUCCESS",
                )

        self.after(0, _update)

    def _start_display_loop(self):
        def _loop():
            while True:
                filepath = self._img_queue.get()
                qsize = self._img_queue.qsize()
                self.after(0, lambda p=filepath, q=qsize: self._image_view.show_image(p, q))
                time.sleep(MIN_DISPLAY_SEC)

        threading.Thread(target=_loop, daemon=True).start()


if __name__ == "__main__":
    app = C2Server()
    app.mainloop()
