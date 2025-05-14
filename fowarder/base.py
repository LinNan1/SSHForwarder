"""
SSH端口转发器基类模块

提供基础的端口转发功能，包括连接管理、数据转发和错误处理。
"""
import logging
import select
import threading
from concurrent.futures import ThreadPoolExecutor

from utils import ResourceAgent, parse_cleartext_payload


class Forwarder:
    """
    SSH端口转发器基类
    
    提供通用的端口转发功能实现，子类需要实现具体的连接建立逻辑(_from和_to方法)。
    
    Attributes:
        thread_pool_executor: 线程池执行器，用于处理并发连接
        exit_event: 线程退出事件标志
        logger: 日志记录器
    """
    def __init__(self, thread_pool_executor: ThreadPoolExecutor = None):
        """
        初始化转发器
        
        Args:
            thread_pool_executor: 可选的线程池执行器，如果未提供将创建新的
        """
        self.thread_pool_executor = ResourceAgent(ThreadPoolExecutor, thread_pool_executor,
                                                  thread_name_prefix=f"{self.__class__.__name__}.connection",
                                                  max_workers=4096).init()
        self.exit_event = threading.Event()
        self.logger = logging.getLogger("Forwarder")

    def forward(self):
        """
        启动转发主循环
        
        持续监听源端连接，为每个连接创建目标端连接并启动转发线程。
        处理连接过程中的异常和超时。
        """
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
        """
        建立源端连接(抽象方法)
        
        Returns:
            tuple: (源端连接对象, 源端地址字符串)
        """
        raise NotImplementedError()

    def _to(self, _from) -> tuple[any, str]:
        """
        建立目标端连接(抽象方法)
        
        Args:
            _from: 源端连接对象
            
        Returns:
            tuple: (目标端连接对象, 目标端地址字符串)
        """
        raise NotImplementedError()

    def _forward_failed(self):
        """
        转发失败回调方法
        
        子类可重写此方法实现自定义失败处理逻辑。
        """
        pass

    def _connection_handler(self, f, f_a, t, t_a):
        """
        连接处理线程
        
        监控连接状态并转发数据，直到连接关闭或退出事件触发。
        
        Args:
            f: 源端连接对象
            f_a: 源端地址
            t: 目标端连接对象
            t_a: 目标端地址
        """
        while not self.exit_event.is_set():
            r, _, x = select.select([f, t], [], [], 1)
            if f in r and not self._relay_streams(f, f_a, t, t_a): break
            if t in r and not self._relay_streams(t, t_a, f, f_a): break
        if f: f.close()
        if t: t.close()

    def _relay_streams(self, f, f_a, t, t_a):
        """
        转发数据流
        
        Args:
            f: 源端连接对象
            f_a: 源端地址
            t: 目标端连接对象
            t_a: 目标端地址
            
        Returns:
            bool: 转发是否成功
        """
        logger = self.logger.getChild(f"[{"%s:%s"%f_a} --> {"%s:%s"%t_a}]")
        try:
            data = f.recv(4096)
            if data == b'':
                return False
            logger.debug(parse_cleartext_payload(data))
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
        """
        关闭转发器
        
        停止所有转发线程并释放资源。
        """
        self.exit_event.set()
        self.thread_pool_executor.shutdown()

