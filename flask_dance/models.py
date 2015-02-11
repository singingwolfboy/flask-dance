from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy_utils import JSONType


class OAuthConsumerMixin(object):
    """
    A :ref:`SQLAlchemy declarative mixin <sqlalchemy:declarative_mixins>` with
    some suggested columns for a model to store OAuth tokens:

    ``id``
        an integer primary key
    ``provider``
        a short name to indicate which OAuth provider issued
        this token
    ``created_at``
        an automatically generated datetime that indicates when
        the OAuth provider issued this token
    ``token``
        a :class:`JSON <sqlalchemy_utils.types.json.JSONType>` field to store
        the actual token received from the OAuth provider
    """
    @declared_attr
    def __tablename__(cls):
        return "flask_dance_{}".format(cls.__name__.lower())

    id = Column(Integer, primary_key=True)
    provider = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    token = Column(MutableDict.as_mutable(JSONType))

    def __repr__(self):
        parts = []
        parts.append(self.__class__.__name__)
        if self.id:
            parts.append("id={}".format(self.id))
        if self.provider:
            parts.append('provider="{}"'.format(self.provider))
        return "<{}>".format(" ".join(parts))
