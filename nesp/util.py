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


from multiprocessing import cpu_count
from threading import Thread
from Queue import Queue, Empty
import math


def run_parallel(target, tasks, n_threads = None):
    """
    Runs tasks in parallel

    `target` is a function
    `tasks` is a list of argument tuples passed to the function. If `target` only takes one argument, then it doesn't need to
    be wrapped in a tuple.

    A generator yielding the result of each task is returned, in the form of a (result, error) tuple which allows errors to be
    handled. The generator must be consumed in order to ensure all tasks are processed.
    Results are yielded in the order they are completed, which is generally not the same as the order in which they are supplied.

    Example::

        do_hard_work(a, b):
            ...

        tasks = [(1,2), (5,2), (3,4) ....]

        for result, error in run_parallel(do_hard_work, tasks):
            print result

    """
    if n_threads is None:
        n_threads = cpu_count()

    # Setup queues
    work_q = Queue()
    result_q = Queue()

    # Setup worker threads
    def worker():
        while True:
            task = work_q.get()
            if task is None:
                break
            try:
                if type(task) != tuple:
                    task = (task,)
                result_q.put((target(*task), None))
            except Exception as e:
                result_q.put((None, e))

    for i in range(0, n_threads):
            t = Thread(target = worker)
            t.daemon = True
            t.start()

    def next_result():
        while True:
            try:
                return result_q.get(True, 1) # Get with timeout so main thread isn't constantly blocked
            except Empty:
                pass

    # Feed in tasks and yield results
    i = 0
    for task in tasks:
        work_q.put(task)
        i += 1
        # Start getting results once all threads have something to do
        if i > n_threads:
            yield next_result()
            i -= 1

    # Signal threads to stop
    for j in range(0, n_threads):
        work_q.put(None)

    # Finish collecting results
    while i > 0:
        yield next_result()
        i -= 1
