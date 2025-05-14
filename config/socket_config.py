"""
Socket配置模块，定义Socket连接的基础配置参数
"""
import socket
from typing import NamedTuple


class SocketConfig(NamedTuple):
    """
    Socket配置类，用于定义Socket连接的参数
    
    Attributes:
        bind_port (int): 绑定端口号，默认为None表示不绑定
        bind_address (str): 绑定地址，默认为None表示任意地址
        family (socket.AddressFamily): 地址族，默认为IPv4 (AF_INET)
        type_ (socket.SocketKind): Socket类型，默认为流式Socket (SOCK_STREAM)
        proto (int): 协议号，默认为0表示自动选择
        timeout (int): 超时时间(秒)，默认为1秒
    """
    bind_port: int = None
    bind_address: str = None
    family: socket.AddressFamily = socket.AF_INET
    type_: socket.SocketKind = socket.SOCK_STREAM
    proto: int = 0
    timeout: int = 1
