class Handler:
    def on_file_received(self, filepath: str, size: int):
        pass


class LocalHandler(Handler):
    def on_file_received(self, filepath: str, size: int):
        print(f"File Received: {filepath} ({size} bytes)")

_local = LocalHandler()
