import http.server
import ssl
import threading
import os
import sys

# Configuration ────────────────────────────────────────────────────────────
HTTP_PORT  = int(os.environ.get("HTTP_PORT",  "12345"))
TLS_PORT   = int(os.environ.get("TLS_PORT",   "23456"))
CERT_FILE  = os.path.join(os.path.dirname(__file__), "cert.pem")
KEY_FILE   = os.path.join(os.path.dirname(__file__), "key.pem")
IMAGE_FILE = os.path.join(os.path.dirname(__file__), "sample.jpeg")

# Play scenario state: 0 = send text, 1 = send image
_play_state = 0
_play_lock  = threading.Lock()

# Request handler ──────────────────────────────────────────────────────────
class WhatsUpHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/sync":
            self._handle_sync()
        elif self.path == "/message":
            self._handle_message()
        else:
            self._send(404, "text/plain", b"Not Found")

    def _handle_sync(self):
        print(f"[sync] {self.client_address[0]} → ACK")
        self._send(200, "text/plain", b"ACK")

    def _handle_message(self):
        global _play_state
        with _play_lock:
            state = _play_state
            _play_state = (_play_state + 1) % 2

        if state == 0:
            # Step 1: send image
            if not os.path.exists(IMAGE_FILE):
                print(f"[message] ERROR: {IMAGE_FILE} not found")
                self._send(404, "text/plain", b"Image not found")
                return
            with open(IMAGE_FILE, "rb") as f:
                data = f.read()
            print(f"[message] → image ({len(data)} bytes)")
            self._send(200, "image/jpeg", data)
        else:
            # Step 2: send text
            text = "Look at this! !t's so funny!"
            print(f"[message] → text: {text!r}")
            self._send(200, "text/plain", text.encode())

    def _send(self, code, content_type, body):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # suppress default access log (we print our own)


# Server threads ───────────────────────────────────────────────────────────
def run_http():
    server = http.server.HTTPServer(("0.0.0.0", HTTP_PORT), WhatsUpHandler)
    print(f"[HTTP]  listening on port {HTTP_PORT}")
    server.serve_forever()


def run_https():
    if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
        print(f"[HTTPS] cert/key not found — run gen_cert.py first, skipping TLS server")
        return
    server = http.server.HTTPServer(("0.0.0.0", TLS_PORT), WhatsUpHandler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(CERT_FILE, KEY_FILE)
    server.socket = ctx.wrap_socket(server.socket, server_side=True)
    print(f"[HTTPS] listening on port {TLS_PORT}")
    server.serve_forever()


# Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not os.path.exists(IMAGE_FILE):
        print(f"WARNING: {IMAGE_FILE} not found. Copy sample.jpeg here before running /message.")

    t_http  = threading.Thread(target=run_http,  daemon=True)
    t_https = threading.Thread(target=run_https, daemon=True)
    t_http.start()
    t_https.start()

    print("WhatsUp Demo Server running. Press Ctrl+C to stop.")
    try:
        t_http.join()
        t_https.join()
    except KeyboardInterrupt:
        print("\nStopped.")
