import warnings
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage


class SQLAlchemyBackend(SQLAlchemyStorage):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "flask_dance.consumer.backend.sqla.SQLAlchemyBackend is deprecated. "
            "Please use flask_dance.consumer.storage.sqla.SQLAlchemyStorage instead.",
            DeprecationWarning,
        )
        super(SQLAlchemyBackend, self).__init__(*args, **kwargs)
