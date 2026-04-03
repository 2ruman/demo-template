import os
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

from handler import Handler
from logger import Logger

_tag = "[UPS]"
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")


class UploadServer:
    def __init__(self, logger: Logger, handler: Handler, host="localhost", port=12345, mkdir=True):
        self.logger = logger
        self.handler = handler
        self.host = host
        self.port = port
        self.http_server = None

        UploadHandler._logger = logger
        UploadHandler._handler = handler

        if mkdir:
            os.makedirs(UPLOADS_DIR, exist_ok=True)

    def run_httpd(self):
        if self.http_server is not None:
            self.logger.w(f"{_tag} HTTP server is already running")
            return None

        def _do():
            self.http_server = HTTPServer((self.host, self.port), UploadHandler)
            self.logger.i(f"{_tag} Starting upload server at http://{self.host}:{self.port}")
            self.http_server.serve_forever()

        httpd = threading.Thread(target=_do, daemon=True)
        httpd.start()
        return httpd

    def start(self):
        self.httpd = self.run_httpd()
        return self

    def shutdown(self):
        if self.http_server:
            self.logger.i(f"{_tag} Shutting down upload server...")
            self.http_server.shutdown()
            self.http_server = None


class UploadHandler(BaseHTTPRequestHandler):

    _logger: Logger | None = None
    _handler: Handler | None = None

    def _debug(self, msg: str, *args, **kwargs):
        self._logger and self._logger.d(f"{_tag} {msg.format(*args, **kwargs)}")

    def _info(self, msg: str, *args, **kwargs):
        self._logger and self._logger.i(f"{_tag} {msg.format(*args, **kwargs)}")

    def _error(self, msg: str, *args, **kwargs):
        self._logger and self._logger.e(f"{_tag} {msg.format(*args, **kwargs)}")

    def do_POST(self):
        if self.path != "/upload":
            self.send_response(404)
            self.end_headers()
            self._debug("Unknown path: {}", self.path)
            return

        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self.send_response(400)
            self.end_headers()
            self._debug("Received empty content")
            return

        data = self.rfile.read(content_length)

        content_type = self.headers.get("Content-Type", "image/jpeg")
        file_ext_map = {
            "image/jpeg": ".jpg",
            "image/png":  ".png",
            "image/gif":  ".gif",
            "image/webp": ".webp",
            "image/bmp":  ".bmp",
        }
        ext = file_ext_map.get(content_type, ".jpg")

        uploads_dir = UPLOADS_DIR
        os.makedirs(uploads_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{ts}{ext}"
        filepath = os.path.join(uploads_dir, filename)

        with open(filepath, "wb") as f:
            f.write(data)

        if self._handler:
            self._handler.on_file_received(filepath, len(data))

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")


if __name__ == "__main__":
    from handler import _local as handler
    from logger import _local as logger

    logger.i(f"{_tag} Starting upload server")
    ups = UploadServer(logger, handler, "0.0.0.0", 8080).start()

    try:
        ups.httpd.join()
    except KeyboardInterrupt:
        logger.i(f"{_tag} Stopped by keyboard interrupt")
        ups.shutdown()
