import six
from abc import ABCMeta, abstractmethod


class BaseBackend(six.with_metaclass(ABCMeta)):
    @abstractmethod
    def get(self, blueprint):
        return None

    @abstractmethod
    def set(self, blueprint, token):
        return None

    @abstractmethod
    def delete(self, blueprint):
        return None


class NullBackend(BaseBackend):
    """
    Don't actually store anything
    """
    def get(self, blueprint):
        return None
    def set(self, blueprint, token):
        return None
    def delete(self, blueprint):
        return None


class MemoryBackend(BaseBackend):
    """
    "Store" the token in memory
    """
    def __init__(self, token=None, *args, **kwargs):
        self.token = token

    def get(self, blueprint):
        return self.token

    def set(self, blueprint, token):
        self.token = token

    def delete(self, blueprint):
        self.token = None
