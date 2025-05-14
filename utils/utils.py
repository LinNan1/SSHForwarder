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

def parse_cleartext_payload(data, print_len: int = 16) -> str:
    """
    解析明文或常见协议数据，返回可读的字符串表示
    
    支持解析TLS、HTTP、SSH等常见协议，以及普通文本和二进制数据。
    
    Args:
        data: 原始字节数据
        print_len: 返回字符串中显示的数据长度，默认为16字节
        
    Returns:
        str: 格式化后的协议信息或数据片段
        
    Examples:
        >>> parse_cleartext_payload(b'GET / HTTP/1.1\\r\\nHost: example.com')
        'HTTP数据: GET / HTTP/1.1 ... (共2行)'
    """
    # 协议识别和数据解析
    if len(data) >= 3 and (data[0] == 0x16 or data[0] == 0x14 or data[0] == 0x17):  # TLS记录层
        # TLS记录层协议解析
        # 字节0: 内容类型(0x16=握手协议, 0x14=应用数据, 0x17=应用数据协议)
        content_type = "握手协议" if data[0] == 0x16 else "应用数据" if data[0] == 0x14 else "应用数据协议"
        # 字节1-2: 协议版本
        version = data[1:3]
        version_str = "未知版本"
        if version == b'\x03\x01':
            version_str = "TLS 1.0"
        elif version == b'\x03\x02':
            version_str = "TLS 1.1"
        elif version == b'\x03\x03':
            version_str = "TLS 1.2"
        elif version == b'\x03\x04':
            version_str = "TLS 1.3"
        # 字节3-4: 记录长度
        record_length = int.from_bytes(data[3:5], 'big')
        return f"TLS数据: 类型={content_type} 版本={version_str} 长度={record_length} 数据: {data[:print_len]}..."
    elif b'HTTP/' in data or b'GET ' in data or b'POST ' in data:  # HTTP
        try:
            text = data.decode('utf-8')
            lines = text.split('\r\n')
            return f"HTTP数据: {lines[0]} ... (共{len(lines)}行)"
        except UnicodeDecodeError:
            return f"HTTP数据(无法解码): {data[:print_len]}..."
    elif b'SSH-' in data:  # SSH
        # SSH协议解析
        # 前 4 字节: 协议标识长度
        # 后续字节: 协议标识(SSH-2.0-...)
        proto_length = int.from_bytes(data[:4], 'big')
        proto_id = data[4:4 + proto_length].decode('ascii')
        return f"SSH协议数据: 标识长度={proto_length} 协议标识={proto_id} 数据: {data[:print_len]}..."
    else:
        try:
            text = data.decode('utf-8')
            if len(text) > 50:
                text = text[:print_len] + '...'
            return f"明文数据: {text}"
        except UnicodeDecodeError:
            # 尝试解析常见二进制协议
            if len(data) >= 4 and data[0] == 0x00:  # 可能为长度前缀协议
                length = int.from_bytes(data[:4], 'big')
                return f"二进制协议数据: 长度前缀={length} 数据: {data[:print_len]}..."
            else:
                return f"二进制数据: {data[:print_len]}..."