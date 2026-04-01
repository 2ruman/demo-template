import random
from collections import deque

from app import LOG_LEVEL_MAP

import logger


def play(thatLogger: logger.AppLogger):
    _demo_logger = logger.AppLogger("demo", thatLogger._logger.level,
                                    thatLogger._view_handler, thatLogger._file_handler)

    for (level, msg) in gen_arbitrary_logs():
        _demo_logger.log(level, msg)


def gen_arbitrary_logs(n=100):
    lines = read_last_lines("/var/log/syslog", n)
    return [(random.choice(list(LOG_LEVEL_MAP.values())), value.strip()) for value in lines]


def read_last_lines(file_path, n=20):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            last_lines = deque(f, maxlen=n)
            return list(last_lines)
    except FileNotFoundError:
        return ["File not found."]
