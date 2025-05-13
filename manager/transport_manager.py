import logging
import threading
from time import sleep

from config import SSHConfig
from utils import ResourceAgent
from .base import Manager
from paramiko import Transport
from .socket_manager import SocketManager


class TransportManager(Manager):
    def __init__(self, socket_manager: SocketManager = None):
        super().__init__()
        self.exit_event = threading.Event()
        self.socket_manager = ResourceAgent(SocketManager, socket_manager).init()
        self.logger = logging.getLogger("TransportManager")

    def _validate(self, v: Transport) -> bool:
        return v is not None and v.is_active()

    def _create(self, config: SSHConfig = None) -> Transport | None:
        assert config is not None
        transport = None
        jump_server_list = config.jump_server_list
        connection_chain = [] if jump_server_list is None else jump_server_list.copy()
        connection_chain.append(config)
        create_retry = 0
        while not self.exit_event.is_set():
            try:
                for jump_server in connection_chain:
                    j_ssh_server_ip, j_ssh_user_name, j_private_key, _,j_ssh_port = jump_server
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
        self.exit_event.set()
        self.socket_manager.close()

    def _close(self, transport: Transport):
        transport.close()