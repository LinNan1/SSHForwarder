from sshforwarder import LocalForwarder, DynamicForwarder, RemoteForwarder
from sshforwarder import ForwarderManager
from paramiko import Ed25519Key
import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("paramiko").setLevel(logging.CRITICAL)

if __name__ == '__main__':
    forwarder_manager = ForwarderManager()
    bryn_private_key = Ed25519Key.from_private_key_file("/home/bryn/.ssh/id_ed25519")

    master = ('202.116.105.20', 'ln', bryn_private_key)
    aliyun = ('47.243.111.186', 'admin', bryn_private_key)
    gpu02 = ('gpu02', 'ln', bryn_private_key, [master])

    local_forward_args = [
        (8888, 9443, gpu02),
        (8889, 9443, master, 'localhost', 'gpu02'),
    ]
    remote_forward_args = [
        (8888, 1081, aliyun),
    ]
    dynamic_forward_args = [
        (1080, None, master),
    ]

    for args in local_forward_args:
        forwarder_manager.get(LocalForwarder(args))
    for args in remote_forward_args:
        forwarder_manager.get(RemoteForwarder(args))
    for args in dynamic_forward_args:
        forwarder_manager.get(DynamicForwarder(args))

    try:
        forwarder_manager.wait()
    except KeyboardInterrupt:
        forwarder_manager.close()