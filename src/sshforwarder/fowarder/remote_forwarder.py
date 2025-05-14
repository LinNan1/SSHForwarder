"""
远程端口转发器模块

该模块实现了通过SSH隧道将远程主机端口转发到本地网络的功能。
"""
import logging
from concurrent.futures import ThreadPoolExecutor

from sshforwarder.config import ForwardConfig
from sshforwarder.manager import SocketManager, TransportManager
from sshforwarder.utils import ResourceAgent
from .base import Forwarder


class RemoteForwarder(Forwarder):
    """
    远程端口转发器类，负责建立和管理远程端口转发连接
    
    通过SSH隧道将远程主机的指定端口转发到本地网络。
    """
    def __init__(self, config: ForwardConfig | tuple,
                 socket_manager: SocketManager = None,
                 transport_manager: TransportManager = None,
                 thread_pool_executor: ThreadPoolExecutor = None):
        """
        初始化远程端口转发器
        
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

        self.logger = logging.getLogger(
            f"RemoteForwarder[{self.config.local_host}:{self.config.local_port} <--> {self.config.ssh_config} <--> {self.config.remote_host}:{self.config.remote_port}]")

        try:
            new_port = self.transport.request_port_forward(self.config.remote_host, self.config.remote_port)
        except Exception as e:
            self.logger.error(f'绑定指定的远程端口失败 {e.__class__.__name__}: {e}')
            new_port = self.transport.request_port_forward(self.config.remote_host, 0)
            self.logger.error(f'随机绑定远程端口: {new_port}')

        self.logger = logging.getLogger(
            f"RemoteForwarder[{self.config.local_host}:{self.config.local_port} <--> {self.config.ssh_config} <--> {self.config.remote_host}:{new_port}]")

        self.logger.info("Successfully initialized remote forwarder")

    def _from(self):
        """
        获取来自远程端的连接
        
        Returns:
            tuple: (connection, address) 连接对象和地址元组
        """
        connection, address = self.transport.accept(timeout=1), None
        if connection: address = connection.origin_addr
        return connection, address

    def _to(self, _from):
        """
        建立到本地目标的连接
        
        Args:
            _from: 来自远程端的连接对象
            
        Returns:
            tuple: (local_sock, to_addr) 本地套接字和目标地址
        """
        local_sock = self.socket_manager.get()
        to_addr = (self.config.local_host, self.config.local_port)
        local_sock.connect(to_addr)
        return local_sock, to_addr

    def _forward_failed(self):
        """
        转发失败时的处理，重新获取传输对象
        """
        self.transport = self.transport_manager.get(self.config.ssh_config)


    def close(self):
        """
        关闭所有资源，包括套接字和传输管理器
        """
        super().close()
        self.socket_manager.close()
        self.transport_manager.close()