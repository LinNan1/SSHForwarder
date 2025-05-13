import logging
import select
import threading
from concurrent.futures import ThreadPoolExecutor

from utils import ResourceAgent


class Forwarder:
    def __init__(self,thread_pool_executor :ThreadPoolExecutor = None):
        self.thread_pool_executor = ResourceAgent(ThreadPoolExecutor, thread_pool_executor,
                                                  thread_name_prefix=f"{self.__class__.__name__}.connection",
                                                  max_workers=4096).init()
        self.exit_event = threading.Event()
        self.logger = logging.getLogger("Forwarder")

    def forward(self):
        while not self.exit_event.is_set():
            _from_conn = None
            try:
                _from_conn, _from_addr = self._from()
                if _from_conn is None: continue
                _to_conn, _to_addr = self._to(_from_conn)
                self.thread_pool_executor.submit(self._connection_handler, _from_conn, _from_addr, _to_conn, _to_addr)
            except TimeoutError as e:
                pass
            except Exception as e:
                if _from_conn: _from_conn.close()
                self.logger.error(f'{e.__class__.__name__}: {e}')
                self._forward_failed()

    def _from(self) -> tuple[any, str]:
        raise NotImplementedError()

    def _to(self, _from) -> tuple[any, str]:
        raise NotImplementedError()

    def _forward_failed(self):
        pass

    def _connection_handler(self, f, f_a, t, t_a):
        while not self.exit_event.is_set():
            r, _, x = select.select([f, t], [], [], 1)
            if f in r and not self._relay_streams(f, f_a, t, t_a): break
            if t in r and not self._relay_streams(t, t_a, f, f_a): break
        if f: f.close()
        if t: t.close()

    def _relay_streams(self, f, f_a, t, t_a):
        logger = self.logger.getChild(f"[{"%s:%s"%f_a} --> {"%s:%s"%t_a}]")
        try:
            data = f.recv(4096)
            if data == b'':
                return False
        except Exception as e:
            logger.debug(f'{e.__class__.__name__}: {e}')
            return False
        try:
            t.send(data)
        except Exception as e:
            logger.debug(f'{e.__class__.__name__}: {e}')
            return False

        return True

    def close(self):
        self.exit_event.set()

