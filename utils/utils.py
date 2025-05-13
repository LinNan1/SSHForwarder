from os import close
from typing import TypeVar

ResourceType = TypeVar('ResourceType')
class ResourceAgent:
    def __init__(self, resource_class: ResourceType, resource, *args, **kwargs):
        self.internal = resource is None
        if self.internal:
            self.resource = resource_class(*args, **kwargs)
        else:
            external_resource = type('ExternalResource', (resource_class, ),{
                "close": lambda _self: None,
                "shutdown": lambda _self: None,
            })
            self.resource = external_resource.__new__(external_resource)
            self.resource.__dict__ = resource.__dict__
    def init(self) -> ResourceType:
        return self.resource