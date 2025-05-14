"""
本地端口转发器实现模块

该模块提供了LocalForwarder类，用于实现本地到远程的SSH端口转发功能。
"""
import logging
from concurrent.futures.thread import ThreadPoolExecutor

from sshforwarder.config import ForwardConfig
from sshforwarder.manager import SocketManager, TransportManager
from sshforwarder.utils import ResourceAgent
from .base import Forwarder


class LocalForwarder(Forwarder):
    """
    本地端口转发器类
    
    继承自Forwarder基类，实现本地端口到远程主机的SSH隧道转发功能。
    
    Attributes:
        config: 转发配置对象
        socket_manager: 套接字管理对象
        transport_manager: SSH传输管理对象
        transport: SSH传输通道
        local_socket: 本地监听套接字
        logger: 日志记录器
    """
    def __init__(self, config: ForwardConfig | tuple,
                 socket_manager: SocketManager = None,
                 transport_manager: TransportManager = None,
                 thread_pool_executor: ThreadPoolExecutor = None):
        """
        初始化本地端口转发器
        
        Args:
            config: 转发配置对象或配置元组
            socket_manager: 可选的套接字管理对象
            transport_manager: 可选的SSH传输管理对象
            thread_pool_executor: 可选的线程池执行器
        """
        super().__init__(thread_pool_executor)
        if not isinstance(config, ForwardConfig):
            self.config = ForwardConfig(*config)
        self.socket_manager = ResourceAgent(SocketManager, socket_manager).init()
        self.transport_manager = ResourceAgent(TransportManager, transport_manager).init()

        self.transport = self.transport_manager.get(self.config.ssh_config)
        self.local_socket = self.socket_manager.get((self.config.local_port, self.config.local_host))

        self.logger = logging.getLogger(f"LocalForwarder[{'%s:%s'%self.local_socket.getsockname()} <--> {self.config.ssh_config} <--> {self.config.remote_host}:{self.config.remote_port}]")

        self.logger.info("Successfully initialized local forwarder")

    def _from(self):
        """
        获取本地连接
        
        Returns:
            tuple: (连接对象, 客户端地址)
        """
        connection, address = self.local_socket.accept()
        return connection, address

    def _to(self, _from):
        """
        建立到远程目标的连接
        
        Args:
            _from: 本地连接对象
            
        Returns:
            tuple: (SSH通道对象, 远程目标地址)
        """
        to_addr = (self.config.remote_host, self.config.remote_port)
        channel = self.transport.open_channel(
            kind='direct-tcpip',
            src_addr=_from.getpeername(),
            dest_addr=to_addr,
            timeout=5
        )
        return channel, to_addr

    def _forward_failed(self):
        """
        转发失败处理
        
        当转发失败时重新获取SSH传输通道
        """
        self.transport = self.transport_manager.get(self.config.ssh_config)

    def close(self):
        """
        关闭转发器并释放所有资源
        """
        super().close()
        self.local_socket.close()
        self.socket_manager.close()
        self.transport_manager.close()