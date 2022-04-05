from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm.exc import NoResultFound

from flask_dance.consumer.storage import BaseStorage
from flask_dance.utils import FakeCache, first

try:
    from flask_login import AnonymousUserMixin
except ImportError:
    AnonymousUserMixin = None


class OAuthConsumerMixin:
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
        a :class:`JSON <sqlalchemy.types.JSON>` field to store
        the actual token received from the OAuth provider
    """

    @declared_attr
    def __tablename__(cls):
        return f"flask_dance_{cls.__name__.lower()}"

    id = Column(Integer, primary_key=True)
    provider = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    token = Column(MutableDict.as_mutable(JSON), nullable=False)

    def __repr__(self):
        parts = []
        parts.append(self.__class__.__name__)
        if self.id:
            parts.append(f"id={self.id}")
        if self.provider:
            parts.append(f'provider="{self.provider}"')
        return "<{}>".format(" ".join(parts))


class SQLAlchemyStorage(BaseStorage):
    """
    Stores and retrieves OAuth tokens using a relational database through
    the `SQLAlchemy`_ ORM.

    .. _SQLAlchemy: http://www.sqlalchemy.org/
    """

    def __init__(
        self,
        model,
        session,
        user=None,
        user_id=None,
        user_required=None,
        anon_user=None,
        cache=None,
    ):
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
            user_required:
                If set to ``True``, an exception will be raised if you try to
                set or retrieve an OAuth token without an associated user.
                If set to ``False``, OAuth tokens can be set with or without
                an associated user. The default is auto-detection: it will
                be ``True`` if you pass a ``user`` or ``user_id`` parameter,
                ``False`` otherwise.
            anon_user:
                If anonymous users are represented by a class in your application,
                provide that class here. If you are using `Flask-Login`_,
                anonymous users are represented by the
                :class:`flask_login.AnonymousUserMixin` class, but you don't have
                to provide that -- Flask-Dance treats it as the default.
            cache:
                An instance of `Flask-Caching`_. Providing a caching system is
                highly recommended, but not required.

        .. _Flask-SQLAlchemy: http://pythonhosted.org/Flask-SQLAlchemy/
        .. _Flask-Login: https://flask-login.readthedocs.io/
        .. _Flask-Caching: https://flask-caching.readthedocs.io/en/latest/
        """
        self.model = model
        self.session = session
        self.user = user
        self.user_id = user_id
        if user_required is None:
            self.user_required = user is not None or user_id is not None
        else:
            self.user_required = user_required
        self.anon_user = anon_user or AnonymousUserMixin
        self.cache = cache or FakeCache()

    def make_cache_key(self, blueprint, user=None, user_id=None):
        uid = first([user_id, self.user_id, blueprint.config.get("user_id")])
        if not uid:
            u = first(
                _get_real_user(ref, self.anon_user)
                for ref in (user, self.user, blueprint.config.get("user"))
            )
            uid = getattr(u, "id", u)
        return "flask_dance_token|{name}|{user_id}".format(
            name=blueprint.name, user_id=uid
        )

    def get(self, blueprint, user=None, user_id=None):
        """When you have a statement in your code that says
        "if <provider>.authorized:" (for example "if twitter.authorized:"),
        a long string of function calls result in this function being used to
        check the Flask server's cache and database for any records associated
        with the current_user. The `user` and `user_id` parameters are actually
        not set in that case (see base.py:token(), that's what calls this
        function), so the user information is instead loaded from the
        current_user (if that's what you specified when you created the
        blueprint) with blueprint.config.get('user_id').

        :param blueprint:
        :param user:
        :param user_id:
        :return:
        """
        # check cache
        cache_key = self.make_cache_key(blueprint=blueprint, user=user, user_id=user_id)
        token = self.cache.get(cache_key)
        if token:
            return token

        # if not cached, make database queries
        query = self.session.query(self.model).filter_by(provider=blueprint.name)
        uid = first([user_id, self.user_id, blueprint.config.get("user_id")])
        u = first(
            _get_real_user(ref, self.anon_user)
            for ref in (user, self.user, blueprint.config.get("user"))
        )

        if self.user_required and not u and not uid:
            raise ValueError("Cannot get OAuth token without an associated user")

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
        uid = first([user_id, self.user_id, blueprint.config.get("user_id")])
        u = first(
            _get_real_user(ref, self.anon_user)
            for ref in (user, self.user, blueprint.config.get("user"))
        )

        if self.user_required and not u and not uid:
            raise ValueError("Cannot set OAuth token without an associated user")

        # if there was an existing model, delete it
        existing_query = self.session.query(self.model).filter_by(
            provider=blueprint.name
        )
        # check for user ID
        has_user_id = hasattr(self.model, "user_id")
        if has_user_id and uid:
            existing_query = existing_query.filter_by(user_id=uid)
        # check for user (relationship property)
        has_user = hasattr(self.model, "user")
        if has_user and u:
            existing_query = existing_query.filter_by(user=u)
        # queue up delete query -- won't be run until commit()
        existing_query.delete()
        # create a new model for this token
        kwargs = {"provider": blueprint.name, "token": token}
        if has_user_id and uid:
            kwargs["user_id"] = uid
        if has_user and u:
            kwargs["user"] = u
        self.session.add(self.model(**kwargs))
        # commit to delete and add simultaneously
        self.session.commit()
        # invalidate cache
        self.cache.delete(
            self.make_cache_key(blueprint=blueprint, user=user, user_id=user_id)
        )

    def delete(self, blueprint, user=None, user_id=None):
        query = self.session.query(self.model).filter_by(provider=blueprint.name)
        uid = first([user_id, self.user_id, blueprint.config.get("user_id")])
        u = first(
            _get_real_user(ref, self.anon_user)
            for ref in (user, self.user, blueprint.config.get("user"))
        )

        if self.user_required and not u and not uid:
            raise ValueError("Cannot delete OAuth token without an associated user")

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
        self.cache.delete(
            self.make_cache_key(blueprint=blueprint, user=user, user_id=user_id)
        )


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
