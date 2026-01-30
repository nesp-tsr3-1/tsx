import os
from datetime import datetime
import logging
import time
from contextlib import contextmanager
import faulthandler
import collections
import functools
import importlib.resources
import multiprocessing
from threading import Thread
from six.moves.queue import Queue, Empty
import platform
import sys

from tsx.config import config

log = logging.getLogger(__name__)

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
    return datetime.now().isoformat()

def get_resource(path):
    return importlib.resources.files("tsx.resources") / path

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
        levelname = record.levelname
        if (levelname not in self.counters):
            self.counters[levelname] = 0
        self.counters[levelname] += 1

    def count(self, level):
        return self.counters.get(level, 0)

@contextmanager
def log_time(msg):
    t1 = time.time()
    yield
    t2 = time.time()
    log.info('%s: %0.2fs' % (msg, t2 - t1))

# Helpers to inject lists of values into SQL queries
def sql_list_placeholder(name, items):
    return ', '.join([':%s%s' % (name, i) for i in range(len(items))])

def sql_list_argument(name, items):
    return dict(zip(['%s%s' % (name, i) for i in range(len(items))], items))

# Based on: https://wiki.python.org/moin/PythonDecoratorLibrary#Memoize
class memoized(object):
    '''Decorator. Caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned
    (not reevaluated).
    '''
    def __init__(self, func):
        self.func = func
        self.cache = {}
    def __call__(self, *args, **kwargs):
        key = ((args, tuple(sorted(kwargs.items()))))

        if not isinstance(key, collections.Hashable):
            # uncacheable. a list, for instance.
            # better to not cache than blow up.
            return self.func(*args, **kwargs)
        if key in self.cache:
            return self.cache[key]
        else:
            value = self.func(*args, **kwargs)
            self.cache[key] = value
            return value
    def __repr__(self):
        '''Return the function's docstring.'''
        return self.func.__doc__
    def __get__(self, obj, objtype):
        '''Support instance methods.'''
        return functools.partial(self.__call__, obj)

try:
    default_num_workers = config.getint("processing","num_workers")
except Exception:
    default_num_workers = None


# Helper to get next item from queue without constantly blocking
def next(q):
    while True:
        try:
            return q.get(True, 1) # Get with timeout so thread isn't constantly blocked
        except Empty:
            pass
        except Exception:
            log.exception("Exception getting item from queue")
            raise

# Takes tasks from a work queue, processes them with 'target', and puts the results on to a result queu
# Terminates when it encounters 'None' on the work queue.
def worker(target, work_q, result_q):
    faulthandler.enable()
    while True:
        task = next(work_q)
        if task is None:
            break
        try:
            result_q.put((target(*task), None))
        except Exception:
            e = sys.exc_info()[0]
            log.exception("Exception in worker")
            result_q.put((None, e))

def run_parallel(target, tasks, n_workers = default_num_workers, use_processes = True):
    """
    Runs tasks in parallel

    `target` is a function
    `tasks` is a list of argument tuples passed to the function. If `target` only takes one argument, then it doesn't need to
    be wrapped in a tuple.

    A generator yielding the result of each task is returned, in the form of a (result, error) tuple which allows errors to be
    handled. The generator must be consumed in order to ensure all tasks are processed.
    Results are yielded in the order they are completed, which is generally not the same as the order in which they are supplied.

    Example::

        def do_hard_work(a, b):
            ...

        tasks = [(1,2), (5,2), (3,4) ....]

        for result, error in run_parallel(do_hard_work, tasks):
            print result

    A pool of worker threads (or processes if `use_processes = True`) is used to process the tasks.
    Threads may not always be able to achieve parallelism due to Python GIL.
    If using processes, be careful not to use shared global resources such as database connection pools in the target function.
    The number of workers defaults to the number of cpu cores as reported by `multiprocessing.cpu_count`, but can be set
    using the `n_workers` parameter.
    """
    if n_workers is None:
        n_workers = multiprocessing.cpu_count()

    # Multiprocessing has issues on Windows (TODO: check if this is still the case now that we are using the 'spawn' method, see below)
    if platform.system() == 'Windows':
        use_processes = False


    # I ran into major issues trying to use Python Multiprocessing, e.g.:
    # - https://docs.python.org/3.7/library/multiprocessing.html#contexts-and-start-methods
    # - https://bugs.python.org/issue37677
    #
    # In particular I could not get MySQL connections to work even though I was careful to create brand new connections after
    # forking a new process.
    #
    # However, on Mac at least, switching from 'fork' to 'spawn' method seems to work very well. I had to refactor some code,
    # but I think it is now more explicit what is being shared over process boundaries.
    # TODO: Test on Windows and Linux

    if use_processes:
        mp = multiprocessing.get_context('spawn')

    Q = mp.Queue if use_processes else Queue

    # Setup queues

    work_q = Q()
    result_q = Q()
    workers = []

    for i in range(0, n_workers):
            if use_processes:
                p = mp.Process(target = worker, args = (target, work_q, result_q))
                p.daemon = True # Kill process if parent terminates early
                p.start()
                workers.append(p)
            else:
                t = Thread(target = worker, args = (target, work_q, result_q))
                t.daemon = True
                t.start()
                workers.append(t)

    # Feed in tasks and yield results
    i = 0
    for task in tasks:
        # Tasks must always be tuples
        if type(task) is not tuple:
            task = (task,)
        work_q.put(task)
        i += 1
        # Start getting results once all threads have something to do
        if i > n_workers:
            yield next(result_q)
            i -= 1

    # Signal threads to stop
    for j in range(0, n_workers):
        work_q.put(None)

    # Finish collecting results
    while i > 0:
        yield next(result_q)
        i -= 1

    # Wait for workers to terminate
    for w in workers:
        w.join()

# https://code.activestate.com/recipes/52308-the-simple-but-handy-collector-of-a-bunch-of-named
class Bunch:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)
