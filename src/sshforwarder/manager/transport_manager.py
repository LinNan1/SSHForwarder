"""
SSH传输通道管理模块

该模块提供了TransportManager类，用于管理SSH传输通道的创建、验证和关闭。
支持通过跳板机建立SSH连接，并自动处理连接失败重试。
"""
import logging
import threading
from time import sleep

from sshforwarder.config import SSHConfig
from sshforwarder.utils import ResourceAgent
from .base import Manager
from paramiko import Transport
from .socket_manager import SocketManager


class TransportManager(Manager):
    """
    SSH传输通道管理器
    
    负责创建、验证和维护SSH传输通道，支持通过跳板机建立连接。
    线程安全，可通过exit_event安全终止连接过程。
    
    Attributes:
        exit_event (threading.Event): 线程退出事件
        socket_manager (ResourceAgent[SocketManager]): 套接字管理代理
        logger (logging.Logger): 日志记录器
    """
    def __init__(self, socket_manager: SocketManager = None):
        """
        初始化传输管理器
        
        Args:
            socket_manager: 可选的套接字管理对象
        """
        super().__init__()
        self.exit_event = threading.Event()
        self.socket_manager = ResourceAgent(SocketManager, socket_manager).init()
        self.logger = logging.getLogger("TransportManager")

    def _validate(self, v: Transport) -> bool:
        """
        验证传输通道是否有效
        
        Args:
            v: 待验证的传输通道对象
            
        Returns:
            bool: 通道是否有效且活跃
        """
        return v is not None and v.is_active()

    def _create(self, config: SSHConfig = None) -> Transport | None:
        """
        创建SSH传输通道
        
        该方法实现了通过跳板机链式建立SSH连接的完整流程：
        1. 构建连接链(本地->跳板机1->...->目标服务器)
        2. 为每个节点创建TCP通道
        3. 在每个节点上建立SSH传输层
        4. 自动重试失败的连接
        
        连接过程可被exit_event安全终止，线程安全。
        
        Args:
            config (SSHConfig): SSH连接配置，必须包含目标服务器参数
                - 如果配置了jump_server_list，将按顺序通过跳板机连接
                
        Returns:
            Transport: 成功创建的SSH传输通道对象
            None: 连接被终止或配置无效
            
        Raises:
            AssertionError: 当config参数为None时抛出
            
        Notes:
            - 保持连接活跃: 自动设置keepalive=30秒
            - 错误处理: 连接失败会自动重试，间隔5秒
            - 线程安全: 可通过exit_event立即终止连接过程
        """
        assert config is not None
        transport = None
        jump_server_list = config.jump_server_list
        connection_chain = [] if jump_server_list is None else jump_server_list.copy()
        connection_chain.append(config)
        create_retry = 0
        while not self.exit_event.is_set():
            try:
                for jump_server in connection_chain:
                    j_ssh_server_ip = jump_server.ip
                    j_ssh_user_name = jump_server.user
                    j_private_key = jump_server.private_key
                    j_ssh_port = jump_server.port
                    if transport:
                        sock = transport.open_channel(
                            kind='direct-tcpip',
                            src_addr=transport.getpeername(),
                            dest_addr=(j_ssh_server_ip, j_ssh_port))
                    else:
                        sock = self.socket_manager.get()
                        sock.connect((j_ssh_server_ip, j_ssh_port))
                    transport = Transport(sock)
                    transport.set_keepalive(30)
                    transport.connect(username=j_ssh_user_name, pkey=j_private_key)
                if create_retry > 0: self.logger.info(f"{config} 连接成功!")
                return transport
            except Exception as e:
                self.logger.error(f"{config} ssh 连接失败 ({e.__class__.__name__}: {e}), 5s 后重试...")
                sleep(5)
                create_retry += 1
        return None

    def _before_close(self):
        """
        关闭前的清理工作
        
        设置退出事件并关闭套接字管理器
        """
        self.exit_event.set()
        self.socket_manager.close()

    def _close(self, transport: Transport):
        """
        关闭传输通道
        
        Args:
            transport: 要关闭的传输通道
        """
        transport.close()