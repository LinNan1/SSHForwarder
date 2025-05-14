"""
管理器基类模块

提供线程安全的资源管理基础实现，支持泛型配置和资源类型。
"""
import threading
from typing import TypeVar
from abc import abstractmethod

K = TypeVar('K')  # 配置键类型变量
R = TypeVar('R')  # 资源类型变量

class Manager:
    """
    线程安全的资源管理器基类
    
    提供配置到资源的映射管理，确保线程安全的资源创建和访问。
    
    Attributes:
        _kv: 配置到资源的映射字典
        _lock_add_lock: 用于保护_create_locks字典的锁
        _create_locks: 每个配置对应的资源创建锁
    """

    def __init__(self):
        """初始化资源管理器"""
        self._kv = {}  # 配置到资源的映射
        self._lock_add_lock = threading.Lock()  # 保护_create_locks字典的锁
        self._create_locks = {}  # 每个配置对应的资源创建锁

    def get(self, config: K = None) -> R:
        """
        获取或创建资源实例
        
        Args:
            config: 配置对象，如果为None则创建默认资源
            
        Returns:
            与配置对应的资源实例
            
        Note:
            当配置对应的资源不存在时，会线程安全地创建新资源
        """
        if config:
            v = self._kv.get(config)
            if v and self._validate(v):
                return v
            else:
                _create_lock = None
                with self._lock_add_lock:
                    _create_lock = self._create_locks.setdefault(config, threading.Lock())
                with _create_lock:
                    instance = self._create(config)
                    self._put(config, instance)
                    return instance
        else:
            return self._create(config)

    def close(self):
        """
        关闭所有资源
        
        先执行_before_close钩子，然后关闭所有管理的资源
        """
        self._before_close()
        for v in self._kv.values():
            self._close(v)

    def _put(self, config: K, value: R):
        """
        内部方法：存储资源
        
        Args:
            config: 配置对象
            value: 资源实例
        """
        self._kv[config] = value

    @abstractmethod
    def _validate(self, v: R) -> bool:
        """
        抽象方法：验证资源有效性
        
        Args:
            v: 资源实例
            
        Returns:
            bool: 资源是否有效
        """
        raise NotImplementedError()

    @abstractmethod
    def _create(self, config: K = None) -> R:
        """
        抽象方法：创建资源
        
        Args:
            config: 配置对象
            
        Returns:
            新创建的资源实例
        """
        raise NotImplementedError()

    @abstractmethod
    def _close(self, v: R):
        """
        抽象方法：关闭资源
        
        Args:
            v: 要关闭的资源实例
        """
        raise NotImplementedError()

    def _before_close(self):
        """
        钩子方法：关闭前的预处理
        
        子类可重写此方法实现自定义关闭逻辑
        """
        pass