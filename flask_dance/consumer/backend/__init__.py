import warnings
from flask_dance.consumer.storage import BaseStorage as BaseBackend
from flask_dance.consumer.storage import NullStorage, MemoryStorage


class NullBackend(NullStorage):
    def __init__(self):
        warnings.warn(
            "flask_dance.consumer.backend.NullBackend is deprecated. "
            "Please use flask_dance.consumer.storage.NullStorage instead.",
            DeprecationWarning,
        )
        super(NullBackend, self).__init__()


class MemoryBackend(MemoryStorage):
    def __init__(self, token=None, *args, **kwargs):
        warnings.warn(
            "flask_dance.consumer.backend.MemoryBackend is deprecated. "
            "Please use flask_dance.consumer.storage.MemoryStorage instead.",
            DeprecationWarning,
        )
        super(MemoryBackend, self).__init__(token, *args, **kwargs)
