import functools
import threading


def synchronized(function):
    lock = threading.Lock()

    @functools.wraps(function)
    def wrapper(self, *args, **kwargs):
        with lock:
            return function(self, *args, **kwargs)
    return wrapper


class XTBState:
    def __init__(self):
        self._balance = None

    @property
    def balance(self):
        return self._balance

    @balance.setter
    @synchronized
    def balance(self, value):
        self._balance = value
