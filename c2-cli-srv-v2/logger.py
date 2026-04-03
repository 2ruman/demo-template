class Logger:
    def d(self, msg: str):
        pass

    def i(self, msg: str):
        pass

    def w(self, msg: str):
        pass

    def e(self, msg: str):
        pass

    def s(self, msg: str):
        pass

    def c(self, msg: str):
        pass


class LocalLogger(Logger):
    def d(self, msg: str):
        print(f"[{'DEBUG':>8}] {msg}")

    def i(self, msg: str):
        print(f"[{'INFO':>8}] {msg}")

    def w(self, msg: str):
        print(f"[{'WARNING':>8}] {msg}")

    def e(self, msg: str):
        print(f"[{'ERROR':>8}] {msg}")

    def s(self, msg: str):
        print(f"[{'SUCCESS':>8}] {msg}")

    def c(self, msg: str):
        print(f"[{'CRITICAL':>8}] {msg}")


_local = LocalLogger()
