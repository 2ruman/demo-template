class Handler:
    def on_file_received(self, filepath: str, size: int):
        pass

    def notify(self, type: str = "", msg: str = ""):
        pass


class LocalHandler(Handler):
    def on_file_received(self, filepath: str, size: int):
        print(f"File Received: {filepath} ({size} bytes)")

    def notify(self, type: str = "", msg: str = ""):
        print(f"Notication: [{type}] {msg}")


_local = LocalHandler()
