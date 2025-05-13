from typing import TypeVar

ResourceType = TypeVar('ResourceType')
class ResourceAgent:
    def __init__(self, resource_class: ResourceType, resource, *args, **kwargs):
        self.internal = resource is None
        if self.internal:
            self.resource = resource_class(*args, **kwargs)
        else:
            self.resource = resource

    def init(self) -> ResourceType:
        return self.resource

    def close(self):
        if self.internal:
            if self.resource.close:
                self.resource.close()
            if self.resource.shutdown:
                self.resource.shutdown()