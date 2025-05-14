"""
SSH连接配置模块

提供SSHConfig类用于存储和管理SSH连接配置信息，包括主机、用户、密钥、跳板服务器列表等。
"""
from dataclasses import dataclass
from typing import List, Union

from paramiko import PKey


@dataclass
class SSHConfig:
    """
    SSH连接配置类
    
    Attributes:
        ip (str): 目标服务器IP地址
        user (str): SSH登录用户名
        private_key (PKey): SSH私钥对象
        jump_server_list (List[Union[SSHConfig, tuple]]): 跳板服务器配置列表
        port (int): SSH端口号，默认为22
    """
    ip: str
    user: str
    private_key: PKey
    jump_server_list: List[Union['SSHConfig', tuple]] = None
    port: int = 22

    def __post_init__(self):
        """
        初始化后处理跳板服务器列表转换
        """
        if isinstance(self.jump_server_list, list) and len(self.jump_server_list) > 0 \
                and not isinstance(self.jump_server_list[0], SSHConfig):
            self.jump_server_list = [SSHConfig(*_) for _ in self.jump_server_list]


    def __repr__(self):
        """
        返回对象的官方字符串表示
        
        Returns:
            str: 包含用户名、IP、端口和私钥信息的字符串
        """
        return f"{self.user}@{self.ip}:{self.port}, private key: {self.private_key}"

    def __str__(self):
        """
        返回对象的用户友好字符串表示
        
        Returns:
            str: 包含用户名、IP和端口信息的字符串
        """
        return f"{self.user}@{self.ip}:{self.port}"

    def __eq__(self, other):
        """
        比较两个SSH配置是否相等
        
        Args:
            other (SSHConfig): 另一个SSH配置对象
            
        Returns:
            bool: 如果IP、用户和端口相同则返回True
        """
        return self.ip == other.ip and self.user == other.user and self.port == other.port

    def __hash__(self):
        """
        返回对象的哈希值

        Returns:
            int: 基于IP、用户和端口计算的哈希值
        """
        return hash((self.ip, self.user,self.port))


if __name__ == "__main__":
    config1 = SSHConfig('192.168.1.1', 'user', PKey(), [], 25)
    config2 = SSHConfig('192.168.1.1', 'user', PKey(), [config1], 25)
    kv = dict()
    kv[config1] = 1
    print(config1 == config2)
    print(kv.get(config2))