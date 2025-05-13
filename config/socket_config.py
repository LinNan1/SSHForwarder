import socket
from typing import NamedTuple


class SocketConfig(NamedTuple):
    bind_port: int = None
    bind_address: str = None
    family: socket.AddressFamily = socket.AF_INET
    type_: socket.SocketKind = socket.SOCK_STREAM
    proto: int = 0
    timeout: int = 1
