import logging
from datetime import datetime
from pathlib import Path


class LogView:
    def append(self, timestamp: str, level: str, name: str, message: str):
        pass

    def clear(self):
        pass


class ViewHandler(logging.Handler):
    def __init__(self, log_view: LogView):
        super().__init__()
        self._log_view = log_view
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record: logging.LogRecord):
        try:
            timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]
            level = record.levelname
            name = record.name
            message = self.format(record)
            self._log_view.append(timestamp, level, name, message)
        except Exception:
            self.handleError(record)

    @classmethod
    def from_log_view(cls, log_view: LogView):
        if log_view is None:
            raise ValueError(f"{cls.__name__}: arguments cannot be None")

        return cls(log_view)


class FileHandler(logging.FileHandler):
    def __init__(self, file_path, name):
        super().__init__(file_path, encoding="utf-8")
        self._file_path = file_path
        self.set_name(name)
        self.setLevel(logging.DEBUG)
        self.setFormatter(logging.Formatter(
            "%(asctime)s.%(msecs)03d [%(levelname)-8s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S")
        )

    @classmethod
    def from_base_dir(cls, base_dir: str, save_dir: str = "log", app_name: str = "app",
                      init_date: str = datetime.now().strftime("%Y%m%d_%H%M%S")):
        if None in (base_dir, save_dir, app_name, init_date):
            raise ValueError(f"{cls.__name__}: arguments cannot be None")
        Path(base_dir, save_dir).mkdir(parents=True, exist_ok=True)
        file_path = Path(base_dir, save_dir, f"{app_name}_{init_date}.log").absolute()
        return cls(file_path, app_name)


class AppLogger:

    def __init__(self, name: str = "app", level: int = logging.DEBUG,
                 view_handler: ViewHandler | None = None, file_handler: FileHandler | None = None):
        self._view_handler = view_handler
        self._file_handler = file_handler
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        self._logger.propagate = False

        # View Handler
        if self._view_handler and self._view_handler not in self._logger.handlers:
            self._logger.addHandler(self._view_handler)

        # File Handler
        if self._file_handler and self._file_handler not in self._logger.handlers:
            self._logger.addHandler(self._file_handler)

    def log(self, level: int, msg: str):
        self._logger.log(level, msg)

    def d(self, msg: str): self.log(logging.DEBUG,   msg)
    def i(self, msg: str): self.log(logging.INFO,    msg)
    def w(self, msg: str): self.log(logging.WARNING, msg)
    def e(self, msg: str): self.log(logging.ERROR,   msg)
