from dataclasses import dataclass
from config import SSHConfig


@dataclass
class ForwardConfig:
    """
    SSH端口转发配置类
    
    Attributes:
        local_port (int): 本地端口号
        remote_port (int | None): 远程端口号
        ssh_config (SSHConfig | tuple): SSH连接配置
        local_host (str): 本地主机地址，默认为'localhost'
        remote_host (str): 远程主机地址，默认为'localhost'
    """
    local_port: int
    remote_port: int | None
    ssh_config: SSHConfig | tuple
    local_host: str = 'localhost'
    remote_host: str = 'localhost'

    def __post_init__(self):
        if not isinstance(self.ssh_config, SSHConfig):
            self.ssh_config = SSHConfig(*self.ssh_config)