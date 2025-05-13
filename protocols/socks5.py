import logging
import socket


class Socks5:
    def __init__(self, sock: socket.socket):
        self.sock = sock
        self.logger = logging.getLogger('socks5')

    def destination(self):
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
        # 返回 SOCKS5 响应
        self.sock.sendall(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
        return addr, port