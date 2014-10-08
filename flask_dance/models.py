from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.ext.declarative import declared_attr


class OAuthMixin(object):
    @declared_attr
    def __tablename__(cls):
        return "flask_dance_{}".format(cls.__name__.lower())

    id = Column(Integer, primary_key=True)
    provider = Column(String(50))
    created_on = Column(DateTime, default=datetime.utcnow)
    token = Column(MutableDict.as_mutable(JSON))
