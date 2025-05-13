import threading
from typing import TypeVar

K = TypeVar('K')
R = TypeVar('R')
class Manager:

    def __init__(self):
        self._kv = {}
        self._lock_add_lock = threading.Lock()
        self._create_locks = {}

    def get(self, config: K = None) -> R:
        if config:
            v = self._kv.get(config)
            if v and self._validate(v):
                return v
            else:
                _create_lock = None
                with self._lock_add_lock:
                    _create_lock = self._create_locks.setdefault(config, threading.Lock())
                with _create_lock:
                    instance = self._create(config)
                    self._put(config, instance)
                    return instance
        else:
            return self._create(config)

    def close(self):
        self._before_close()
        for v in self._kv.values():
            self._close(v)

    def _put(self, config: K, value: R):
        self._kv[config] = value

    def _validate(self, v: R) -> bool:
        raise NotImplementedError()

    def _create(self, config: K = None) -> R:
        raise NotImplementedError()

    def _close(self, v: R):
        raise NotImplementedError()

    def _before_close(self):
        pass