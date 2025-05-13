import logging
from concurrent.futures import ThreadPoolExecutor

from config import ForwardConfig
from manager import SocketManager, TransportManager
from utils import ResourceAgent
from .base import Forwarder


class RemoteForwarder(Forwarder):
    def __init__(self, config: ForwardConfig | tuple,
                 socket_manager: SocketManager = None,
                 transport_manager: TransportManager = None,
                 thread_pool_executor: ThreadPoolExecutor = None):
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
        connection, address = self.transport.accept(timeout=1), None
        if connection: address = connection.origin_addr
        return connection, address

    def _to(self, _from):
        local_sock = self.socket_manager.get()
        to_addr = (self.config.local_host, self.config.local_port)
        local_sock.connect(to_addr)
        return local_sock, to_addr

    def _forward_failed(self):
        self.transport = self.transport_manager.get(self.config.ssh_config)


    def close(self):
        super().close()
        self.socket_manager.close()
        self.transport_manager.close()