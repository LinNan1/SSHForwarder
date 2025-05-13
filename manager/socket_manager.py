import logging
import socket
import threading

from config import SocketConfig
from .base import Manager


class SocketManager(Manager):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('SocketManager')
        self.exit_event = threading.Event()

    def _create(self, config: SocketConfig | tuple = None) -> socket.socket:
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
        return v is not None

    def _before_close(self):
        self.exit_event.set()

    def _close(self, v: socket.socket):
        v.close()

    def bind_port(self, v: socket.socket, port: int, host: str = 'localhost') -> int | None:
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
