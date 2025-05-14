"""
SOCKS5协议实现模块

提供SOCKS5协议的客户端请求解析功能，支持IPv4、IPv6和域名地址类型。
"""
import logging
import socket


class Socks5:
    """
    SOCKS5协议处理类
    
    Attributes:
        sock: socket.socket - 客户端连接socket
        logger: logging.Logger - 日志记录器
    """
    def __init__(self, sock: socket.socket):
        """
        初始化SOCKS5处理器
        
        Args:
            sock: socket.socket - 客户端连接socket
        """
        self.sock = sock
        self.logger = logging.getLogger('socks5')

    def destination(self):
        """
        解析客户端请求的目标地址和端口
        
        Returns:
            tuple: (address, port) - 目标地址和端口，如果协议错误返回(None, None)
        """
        logger = self.logger.getChild('destination')
        version, nmethods = self.sock.recv(2)
        if version != 5:
            self.sock.send(b'')
            logger.error("非法请求")
            return None, None
        method = self.sock.recv(nmethods)
        self.sock.send(b'\x05\x00')
        version, cmd, rsv, addr_type = self.sock.recv(4)
        # 解析目标地址
        # 地址类型: 0x01(IPv4), 0x03(域名), 0x04(IPv6)
        if addr_type == 0x01:  # IPv4
            addr = socket.inet_ntoa(self.sock.recv(4))
        elif addr_type == 0x03:  # 域名
            domain_len = ord(self.sock.recv(1))
            addr = self.sock.recv(domain_len)
        elif addr_type == 0x04:  # IPv6
            addr = socket.inet_ntop(socket.AF_INET6, self.sock.recv(16))
        else:
            addr = 'unknown'
        addr = addr.decode()
        port = int.from_bytes(self.sock.recv(2))
        logger.debug(f"{addr}:{port}")
        # 返回SOCKS5响应
        # 格式: VER REP RSV ATYP BND.ADDR BND.PORT
        self.sock.sendall(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
        return addr, port