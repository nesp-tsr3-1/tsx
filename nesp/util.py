import os
import tzlocal
from datetime import datetime
import logging

# https://stackoverflow.com/a/47087513/165783
def next_path(path_pattern):
    """
    Finds the next free path in an sequentially named list of files

    e.g. path_pattern = 'file-%s.txt':

    file-1.txt
    file-2.txt
    file-3.txt

    Runs in log(n) time where n is the number of existing files in sequence
    """
    i = 1

    # First do an exponential search
    while os.path.exists(path_pattern % i):
        i = i * 2

    # Result lies somewhere in the interval (i/2..i]
    # We call this interval (a..b] and narrow it down until a + 1 = b
    a, b = (i / 2, i)
    while a + 1 < b:
        c = (a + b) / 2 # interval midpoint
        a, b = (c, b) if os.path.exists(path_pattern % c) else (a, c)

    return path_pattern % b, b


def local_iso_datetime():
    """
    Returns ISO8601 formatted timestamp for the current time and timezone
    """
    return tzlocal.get_localzone().localize(datetime.now()).isoformat()

# https://stackoverflow.com/a/31142078/165783
class CounterHandler(logging.Handler):
    """
    Logging handler that counts logged messages by level

    e.g::

        handler = CounterHandler()
        logger.addHandler(handler)

        ... code that uses logger ...

        print("Warnings: %s" % handler.count(logging.WARN))
        print("Errors: %s" % handler.count(logging.ERROR))
    """
    counters = None

    def __init__(self, *args, **kwargs):
        super(CounterHandler, self).__init__(*args, **kwargs)
        self.counters = {}

    def emit(self, record):
        l = record.levelname
        if (l not in self.counters):
            self.counters[l] = 0
        self.counters[l] += 1

    def count(self, level):
        return self.counters.get(level, 0)
