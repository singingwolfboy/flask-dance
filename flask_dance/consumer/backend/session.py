import warnings
from flask_dance.consumer.storage.session import SessionStorage


class SessionBackend(SessionStorage):
    def __init__(self, key="{bp.name}_oauth_token"):
        warnings.warn(
            "flask_dance.consumer.backend.session.SessionBackend is deprecated. "
            "Please use flask_dance.consumer.storage.session.SessionStorage instead.",
            DeprecationWarning,
        )
        super(SessionBackend, self).__init__(key)
