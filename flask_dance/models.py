from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.ext.declarative import declared_attr


class OAuthMixin(object):
    """
    A :ref:`SQLAlchemy declarative mixin <sqlalchemy:declarative_mixins>` with
    some suggested columns for a model to store OAuth tokens:

    ``id``
        an integer primary key
    ``provider``
        a short name to indicate which OAuth provider issued
        this token
    ``created_on``
        an automatically generated datetime that indicates when
        the OAuth provider issued this token
    ``token``
        a :class:`~sqlalchemy.dialects.postgresql.JSON` field to store
        the actual token received from the OAuth provider

    .. warning::

        Currently, :class:`~sqlalchemy.dialects.postgresql.JSON` fields are
        `specific to PostgreSQL
        <http://www.postgresql.org/docs/current/static/datatype-json.html>`_.
        If you want to use a different database, you should override the
        ``token`` property to use a data type that your database supports.
    """
    @declared_attr
    def __tablename__(cls):
        return "flask_dance_{}".format(cls.__name__.lower())

    id = Column(Integer, primary_key=True)
    provider = Column(String(50))
    created_on = Column(DateTime, default=datetime.utcnow)
    token = Column(MutableDict.as_mutable(JSON))
