from collections import namedtuple

from config import SSHConfig


class ForwardConfig(namedtuple("_ForwardConfig","local_port remote_port ssh_config local_host remote_host", defaults=['localhost','localhost'])):
    local_port: int
    remote_port: int | None
    ssh_config: SSHConfig
    local_host: str
    remote_host: str

    def __new__(cls, *args, **kwargs):
        args = (*args[:2], SSHConfig(*args[2]), *args[3:])
        c = super().__new__(cls, *args, **kwargs)
        return c