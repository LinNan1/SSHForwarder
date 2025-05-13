import logging

from config import ForwardConfig
from manager import SocketManager, TransportManager
from utils import ResourceAgent
from .base import Forwarder


class LocalForwarder(Forwarder):
    def __init__(self, config: ForwardConfig | tuple, socket_manager: SocketManager = None, transport_manager: TransportManager = None):
        super().__init__()
        if not isinstance(config, ForwardConfig):
            self.config = ForwardConfig(*config)
        self.socket_manager = ResourceAgent(SocketManager, socket_manager).init()
        self.transport_manager = ResourceAgent(TransportManager, transport_manager).init()

        self.transport = self.transport_manager.get(self.config.ssh_config)
        self.local_socket = self.socket_manager.get((self.config.local_port, self.config.local_host))

        self.logger = logging.getLogger(f"LocalForwarder[{'%s:%s'%self.local_socket.getsockname()} <--> {self.config.ssh_config} <--> {self.config.remote_host}:{self.config.remote_port}]")

        self.logger.info("Successfully initialized local forwarder")

    def _from(self):
        connection, address = self.local_socket.accept()
        return connection, address

    def _to(self, _from):
        to_addr = (self.config.remote_host, self.config.remote_port)
        channel = self.transport.open_channel(
            kind='direct-tcpip',
            src_addr=_from.getpeername(),
            dest_addr=to_addr,
            timeout=5
        )
        return channel, to_addr

    def close(self):
        super().close()
        self.local_socket.close()
        self.transport_manager.close()