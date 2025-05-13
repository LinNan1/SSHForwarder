from concurrent.futures import ThreadPoolExecutor, wait

from fowarder.base import Forwarder
from utils import ResourceAgent
from .base import Manager


class ForwarderManager(Manager):

    def __init__(self, thread_pool_executor: ThreadPoolExecutor=None):
        super().__init__()
        self.thread_pool_executor = ResourceAgent(ThreadPoolExecutor, thread_pool_executor,
                                                  thread_name_prefix='Forwarder',
                                                  max_workers=4096).init()
        self._futures = []

    def _create(self, forwarder: Forwarder = None):
        assert forwarder is not None
        future = self.thread_pool_executor.submit(forwarder.forward)
        self._futures.append(future)
        return forwarder

    def _close(self, forwarder: Forwarder):
        forwarder.close()

    def wait(self):
        wait(self._futures)