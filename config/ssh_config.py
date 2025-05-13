from typing_extensions import NamedTuple

from paramiko import PKey
from collections import namedtuple


class SSHConfig(namedtuple("_SSHConfig", ["ip", "user", "private_key", "jump_server_list", "port"], defaults=[None, 22])):
    ip: str
    user: str
    private_key: PKey
    jump_server_list: list["SSHConfig"]
    port: int

    def __new__(cls, *args, **kwargs):
        if len(args) > 3:
            jump_server_list = [SSHConfig(*_) for _ in args[3]]
            args = (*args[:3], jump_server_list, *args[4:])
        c = super().__new__(cls, *args, **kwargs)
        return c


    def __repr__(self):
        return f"{self.user}@{self.ip}:{self.port}, private key: {self.private_key}"

    def __str__(self):
        return f"{self.user}@{self.ip}:{self.port}"

    def __eq__(self, other):
        return self.ip == other.ip and self.user == other.user and self.port == other.port

    def __hash__(self):
        return hash((self.ip, self.user,self.port))


if __name__ == "__main__":
    config1 = SSHConfig('192.168.1.1', 'user', PKey(), [], 25)
    config2 = SSHConfig('192.168.1.1', 'user', PKey(), [config1], 25)
    kv = dict()
    kv[config1] = 1
    print(config1 == config2)
    print(kv.get(config2))