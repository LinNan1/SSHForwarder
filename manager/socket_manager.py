"""
Socket管理器模块

提供socket创建、绑定、验证和关闭等操作的管理功能
"""
import logging
import socket
import threading

from config import SocketConfig
from .base import Manager


class SocketManager(Manager):
    """
    Socket管理器类
    
    负责管理socket生命周期，包括创建、端口绑定、验证和关闭等操作
    
    Attributes:
        logger: 日志记录器
        exit_event: 线程退出事件
    """
    def __init__(self):
        """
        初始化SocketManager
        
        设置日志记录器和线程退出事件
        """
        super().__init__()
        self.logger = logging.getLogger('SocketManager')
        self.exit_event = threading.Event()

    def _create(self, config: SocketConfig | tuple = None) -> socket.socket:
        """
        创建并配置socket
        
        Args:
            config: Socket配置对象或元组，如果为None则使用默认配置
            
        Returns:
            socket.socket: 创建并配置好的socket对象
        """
        if config is None:
            config = SocketConfig()
        elif not isinstance(config, SocketConfig):
            config = SocketConfig(*config)

        port, host, family, type_, proto, timeout = config
        sock = socket.socket(family, type_, proto)
        sock.settimeout(timeout)
        if port is not None and port > 0:
            self.bind_port(sock, port, host)
            sock.listen(10)
        return sock

    def _validate(self, v: socket.socket) -> bool:
        """
        验证socket是否有效
        
        Args:
            v: 要验证的socket对象
            
        Returns:
            bool: 如果socket不为None则返回True
        """
        return v is not None

    def _before_close(self):
        """
        关闭前的准备工作
        
        设置退出事件以通知所有线程停止
        """
        self.exit_event.set()

    def _close(self, v: socket.socket):
        """
        关闭socket
        
        Args:
            v: 要关闭的socket对象
        """
        v.close()

    def bind_port(self, v: socket.socket, port: int, host: str = 'localhost') -> int | None:
        """
        绑定socket到指定端口
        
        如果端口被占用，会自动尝试下一个端口直到成功或线程退出
        
        Args:
            v: 要绑定的socket对象
            port: 起始端口号
            host: 绑定主机地址，默认为localhost
            
        Returns:
            int | None: 成功绑定的端口号，如果线程退出则返回None
        """
        logger = self.logger.getChild('bind_port')
        while not self.exit_event.is_set():
            try:
                v.bind((host, port))
                logger.info(f'监听端口 {port}')
                return port
            except OSError:
                logger.error(f'端口 {port} 被占用, 尝试新端口 {port + 1} ...')
                port += 1
        return None
