"""
SSH端口转发管理器模块

该模块提供ForwarderManager类，用于管理多个SSH端口转发器的生命周期和线程池执行。
"""
from concurrent.futures import ThreadPoolExecutor, wait

from fowarder.base import Forwarder
from utils import ResourceAgent
from .base import Manager


class ForwarderManager(Manager):
    """
    SSH端口转发管理器
    
    负责管理多个Forwarder实例的生命周期，使用线程池异步执行转发任务。
    
    Attributes:
        thread_pool_executor (ThreadPoolExecutor): 用于执行转发任务的线程池
        _futures (list): 存储所有转发任务的Future对象列表
    """

    def __init__(self, thread_pool_executor: ThreadPoolExecutor=None):
        """
        初始化转发管理器
        
        Args:
            thread_pool_executor (ThreadPoolExecutor, optional): 外部传入的线程池实例。
                如果为None，将创建新的线程池，最大工作线程数为4096。
        """
        super().__init__()
        self.thread_pool_executor = ResourceAgent(ThreadPoolExecutor, thread_pool_executor,
                                                  thread_name_prefix='Forwarder',
                                                  max_workers=4096).init()
        self._futures = []

    def _create(self, forwarder: Forwarder = None):
        """
        创建并启动转发任务
        
        Args:
            forwarder (Forwarder): 要启动的转发器实例
            
        Returns:
            Forwarder: 传入的转发器实例
            
        Raises:
            AssertionError: 如果forwarder参数为None
        """
        assert forwarder is not None
        future = self.thread_pool_executor.submit(forwarder.forward)
        self._futures.append(future)
        return forwarder

    def _before_close(self):
        """
        关闭前操作：停止线程池接受新任务
        """
        self.thread_pool_executor.shutdown()

    def _close(self, forwarder: Forwarder):
        """
        关闭指定的转发器
        
        Args:
            forwarder (Forwarder): 要关闭的转发器实例
        """
        forwarder.close()

    def wait(self):
        """
        等待所有转发任务完成
        """
        wait(self._futures)