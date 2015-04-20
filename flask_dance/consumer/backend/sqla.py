from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy_utils import JSONType
from sqlalchemy.orm.exc import NoResultFound
from flask_dance.utils import FakeCache, first, getattrd
from flask_dance.consumer.backend import BaseBackend
try:
    from flask_login import AnonymousUserMixin
except ImportError:
    AnonymousUserMixin = None


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


class SQLAlchemyBackend(BaseBackend):
    """
    Stores and retrieves OAuth tokens using a relational database through
    the `SQLAlchemy`_ ORM.

    .. _SQLAlchemy: http://www.sqlalchemy.org/
    """
    def __init__(self, model, session,
                 user=None, user_id=None, anon_user=None, cache=None):
        """
        Args:
            model: The SQLAlchemy model class that represents the OAuth token
                table in the database. At a minimum, it must have a
                ``provider`` column and a ``token`` column. If tokens are to be
                associated with individual users in the application, it must
                also have a ``user`` relationship to your User model.
                It is recommended, though not required, that your model class
                inherit from
                :class:`~flask_dance.consumer.storage.sqla.OAuthConsumerMixin`.
            session:
                The :class:`SQLAlchemy session <sqlalchemy.orm.session.Session>`
                for the database. If you're using `Flask-SQLAlchemy`_, this is
                ``db.session``.
            user:
                If you want OAuth tokens to be associated with individual users
                in your application, this is a reference to the user that you
                want to use for the current request. It can be an actual User
                object, a function that returns a User object, or a proxy to the
                User object. If you're using `Flask-Login`_, this is
                :attr:`~flask.ext.login.current_user`.
            user_id:
                If you want to pass an identifier for a user instead of an actual
                User object, use this argument instead. Sometimes it can save
                a database query or two. If both ``user`` and ``user_id`` are
                provided, ``user_id`` will take precendence.
            anon_user:
                If anonymous users are represented by a class in your application,
                provide that class here. If you are using `Flask-Login`_,
                anonymous users are represented by the
                :class:`flask_login.AnonymousUserMixin` class, but you don't have
                to provide that -- Flask-Dance treats it as the default.
            cache:
                An instance of `Flask-Cache`_. Providing a caching system is
                highly recommended, but not required.

        .. _Flask-SQLAlchemy: http://pythonhosted.org/Flask-SQLAlchemy/
        .. _Flask-Login: https://flask-login.readthedocs.org/
        .. _Flask-Cache: http://pythonhosted.org/Flask-Cache/
        """
        self.model = model
        self.session = session
        self.user = user
        self.user_id = user_id
        self.anon_user = anon_user or AnonymousUserMixin
        self.cache = cache or FakeCache()

    def make_cache_key(self, blueprint, user=None, user_id=None):
        uid = first([user_id, self.user_id, blueprint.config.get("user_id")])
        if not uid:
            u = first(_get_real_user(ref, self.anon_user)
                      for ref in (user, self.user, blueprint.config.get("user")))
            uid = getattr(u, "id", u)
        return "flask_dance_token|{name}|{user_id}".format(
            name=blueprint.name, user_id=uid,
        )

    def get(self, blueprint, user=None, user_id=None):
        # check cache
        cache_key = self.make_cache_key(blueprint=blueprint, user=user, user_id=user_id)
        token = self.cache.get(cache_key)
        if token:
            return token

        # if not cached, make database queries
        query = (
            self.session.query(self.model)
            .filter_by(provider=blueprint.name)
        )
        uid = first([user_id, self.user_id, blueprint.config.get("user_id")])
        u = first(_get_real_user(ref, self.anon_user)
                  for ref in (user, self.user, blueprint.config.get("user")))
        # check for user ID
        if hasattr(self.model, "user_id") and uid:
            query = query.filter_by(user_id=uid)
        # check for user (relationship property)
        elif hasattr(self.model, "user") and u:
            query = query.filter_by(user=u)
        # if we have the property, but not value, filter by None
        elif hasattr(self.model, "user_id"):
            query = query.filter_by(user_id=None)
        # run query
        try:
            token = query.one().token
        except NoResultFound:
            token = None

        # cache the result
        self.cache.set(cache_key, token)

        return token

    def set(self, blueprint, token, user=None, user_id=None):
        # if there was an existing model, delete it
        existing_query = (
            self.session.query(self.model)
            .filter_by(provider=blueprint.name)
        )
        # check for user ID
        has_user_id = hasattr(self.model, "user_id")
        if has_user_id:
            uid = first([user_id, self.user_id, blueprint.config.get("user_id")])
            if uid:
                existing_query = existing_query.filter_by(user_id=uid)
        # check for user (relationship property)
        has_user = hasattr(self.model, "user")
        if has_user:
            u = first(_get_real_user(ref, self.anon_user)
                      for ref in (user, self.user, blueprint.config.get("user")))
            if u:
                existing_query = existing_query.filter_by(user=u)
        # queue up delete query -- won't be run until commit()
        existing_query.delete()
        # create a new model for this token
        kwargs = {
            "provider": blueprint.name,
            "token": token,
        }
        if has_user_id and uid:
            kwargs["user_id"] = uid
        if has_user and u:
            kwargs["user"] = u
        self.session.add(self.model(**kwargs))
        # commit to delete and add simultaneously
        self.session.commit()
        # invalidate cache
        self.cache.delete(self.make_cache_key(
            blueprint=blueprint, user=user, user_id=user_id
        ))

    def delete(self, blueprint, user=None, user_id=None):
        query = (
            self.session.query(self.model)
            .filter_by(provider=blueprint.name)
        )
        uid = first([user_id, self.user_id, blueprint.config.get("user_id")])
        u = first(_get_real_user(ref, self.anon_user)
                  for ref in (user, self.user, blueprint.config.get("user")))
        # check for user ID
        if hasattr(self.model, "user_id") and uid:
            query = query.filter_by(user_id=uid)
        # check for user (relationship property)
        elif hasattr(self.model, "user") and u:
            query = query.filter_by(user=u)
        # if we have the property, but not value, filter by None
        elif hasattr(self.model, "user_id"):
            query = query.filter_by(user_id=None)
        # run query
        query.delete()
        self.session.commit()
        # invalidate cache
        self.cache.delete(self.make_cache_key(
            blueprint=blueprint, user=user, user_id=user_id,
        ))


def _get_real_user(user, anon_user=None):
    """
    Given a "user" that could be:

    * a real user object
    * a function that returns a real user object
    * a LocalProxy to a real user object (like Flask-Login's ``current_user``)

    This function returns the real user object, regardless of which we have.
    """
    if hasattr(user, "_get_current_object"):
        # this is a proxy
        user = user._get_current_object()
    if callable(user):
        # this is a function
        user = user()
    if anon_user and isinstance(user, anon_user):
        return None
    return user
