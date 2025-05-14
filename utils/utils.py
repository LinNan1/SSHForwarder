from typing import TypeVar, Optional, Any

ResourceType = TypeVar('ResourceType')

class ResourceAgent:
    """
    资源代理类，提供对资源对象的统一生命周期管理
    
    该类封装了资源对象的创建和管理逻辑，支持两种使用方式：
    1. 内部创建：当resource参数为None时，自动创建新的资源实例
    2. 外部管理：当resource参数提供时，创建代理类包装外部资源
    
    对于外部资源，会自动创建代理类并重写close/shutdown方法为空操作，
    确保外部资源不会被意外关闭。
    
    Args:
        resource_class (type[ResourceType]): 资源类类型，必须实现__init__方法
        resource (Optional[ResourceType]): 可选的外部资源实例，如果为None则内部创建
        *args (Any): 传递给资源构造器的位置参数
        **kwargs (Any): 传递给资源构造器的关键字参数
    
    Attributes:
        internal (bool): 标识资源是否为内部创建
        resource (ResourceType): 管理的资源实例
    
    Example:
        >>> from concurrent.futures.thread import ThreadPoolExecutor
        >>> resource = ThreadPoolExecutor() # or resource = None
        >>> agent = ResourceAgent(ThreadPoolExecutor, resource)
        >>> res = agent.init()  # 获取内部创建的资源
    """
    
    def __init__(self, 
                resource_class: type[ResourceType], 
                resource: Optional[ResourceType] = None, 
                *args: Any, 
                **kwargs: Any) -> None:
        self.internal = resource is None
        if self.internal:
            self.resource = resource_class(*args, **kwargs)
        else:
            # 为外部资源创建代理类，重写close和shutdown方法为空操作
            ExternalResource = type(
                'ExternalResource', 
                (resource_class,),
                {"close": lambda _: None, "shutdown": lambda _: None}
            )
            self.resource = ExternalResource.__new__(ExternalResource)
            self.resource.__dict__ = resource.__dict__
    
    def init(self) -> ResourceType:
        """
        获取管理的资源实例
        
        Returns:
            ResourceType: 当前管理的资源对象实例
            
        Note:
            无论资源是内部创建还是外部传入，
            返回的都是统一接口的资源实例
        """
        return self.resource