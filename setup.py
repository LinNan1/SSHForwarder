from setuptools import setup, find_packages

setup(
    name="sshforwarder",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir = {"": "src"},
    description="基于 paramiko 开发的管理 ssh 端口转发的 python 小工具",
    python_requires=">=3.6",
    install_requires=["paramiko"]
)