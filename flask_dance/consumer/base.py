from __future__ import unicode_literals, print_function

import types
from distutils.version import StrictVersion
import flask
from flask.signals import Namespace
from flask_dance.utils import proxy_property, FakeCache, getattrd


_signals = Namespace()
oauth_authorized = _signals.signal('oauth-authorized')


class BaseOAuthConsumerBlueprint(flask.Blueprint):
    def __init__(self, name, import_name,
            static_folder=None, static_url_path=None, template_folder=None,
            url_prefix=None, subdomain=None, url_defaults=None, root_path=None,
            login_url=None, authorized_url=None):

        bp_kwargs = dict(
            name=name,
            import_name=import_name,
            static_folder=static_folder,
            static_url_path=static_url_path,
            template_folder=template_folder,
            url_prefix=url_prefix,
            subdomain=subdomain,
            url_defaults=url_defaults,
            root_path=root_path,
        )
        # `root_path` didn't exist until 1.0
        if StrictVersion(flask.__version__) < StrictVersion('1.0'):
            del bp_kwargs["root_path"]
        flask.Blueprint.__init__(self, **bp_kwargs)

        login_url = login_url or "/{bp.name}"
        authorized_url = authorized_url or "/{bp.name}/authorized"

        self.add_url_rule(
            rule=login_url.format(bp=self),
            endpoint="login",
            view_func=self.login,
        )
        self.add_url_rule(
            rule=authorized_url.format(bp=self),
            endpoint="authorized",
            view_func=self.authorized,
        )

        self.set_token_storage_session()
        self.logged_in_funcs = []
        self.from_config = {}
        self.before_app_request(self.load_config)
        self.before_app_request(self.load_token)

    def login(self):
        raise NotImplementedError()

    def authorized(self):
        raise NotImplementedError()

    def load_config(self):
        """
        Used to dynamically load variables from the Flask application config
        into the blueprint. To tell this blueprint to pull configuration from
        the app, just set key-value pairs in the ``from_config`` dict. Keys
        are the name of the local variable to set on the blueprint object,
        and values are the variable name in the Flask application config.
        For example:

            blueprint["session.client_id"] = "GITHUB_OAUTH_CLIENT_ID"

        """
        for local_var, config_var in self.from_config.items():
            value = flask.current_app.config.get(config_var)
            if value:
                if "." in local_var:
                    # this is a dotpath -- needs special handling
                    body, tail = local_var.rsplit(".", 1)
                    obj = getattrd(self, body)
                    setattr(obj, tail, value)
                else:
                    # just use a normal setattr call
                    setattr(self, local_var, value)

    def load_token(self):
        raise NotImplementedError()

    token = proxy_property(
        "token", pass_self=False,
        doc=("A proxy property for getting, setting, and deleting the stored "
             "OAuth token."),
    )

    def token_getter(self, func):
        """
        A decorator used to indicate the function used to retrieve a stored
        token from a completed OAuth dance.
        """
        self.get_token = func

    def token_setter(self, func):
        """
        A decorator used to indicate the function used to store a token
        from a completed OAuth dance, so that it can be retrieved later.
        """
        self.set_token = func

    def token_deleter(self, func):
        """
        A decorator used to indicate the function used to delete a
        previously-stored OAuth token.
        """
        self.delete_token = func

    def set_token_storage_session(self):
        """
        A helper method to set up the blueprint to store and retrieve OAuth
        tokens using the Flask session. This will overwrite any custom token
        accessors you've set up. This method is called by the constructor as
        a default -- in general, you shouldn't call this method yourself.
        """
        key = "{name}_oauth_token".format(name=self.name)

        @self.token_getter
        def get_token():
            return flask.session.get(key)

        @self.token_setter
        def set_token(token):
            flask.session[key] = token

        @self.token_deleter
        def delete_token():
            del flask.session[key]

    def set_token_storage_sqlalchemy(self, model, session, user=None, cache=None):
        """
        A helper method to set up the blueprint to store and retrieve OAuth
        tokens using SQLAlchemy. This will overwrite any custom token
        accessors you've set up.

        Args:
            model: A class that represents a database table. At a minimum, it
                must have a ``token`` column and a ``provider`` column.
                If you're using a User class, this model must also declare a
                ``user`` relation to that class. It is recommended, but not
                required, that your model inherit from
                :class:`flask_dance.models.OAuthConsumerMixin`.
            session: A :class:`sqlalchemy.orm.session.Session` object. If you're
                using `Flask-SQLAlchemy`_, this is ``db.session``.
            user: The current logged in user, if any.
                This can also be a function that returns the current logged
                in user. This argument is optional; if not provided,
                OAuth tokens will not be associated with specific users in
                your application.
            cache: An instance of `Flask-Cache`_. This is optional, but highly
                recommended for performance reasons.

        .. _Flask-SQLAlchemy: http://pythonhosted.org/Flask-SQLAlchemy/
        .. _Flask-Cache: http://pythonhosted.org/Flask-Cache/
        """
        from sqlalchemy.orm.exc import NoResultFound
        if not cache:
            cache = FakeCache()
        def make_cache_key(name=None):
            u = _get_real_user(user)
            return "flask_dance_token|{name}|{user}".format(
                name=self.name, user=getattr(u, "id", u),
            )

        @cache.memoize()
        def get_token():
            query = session.query(model).filter_by(provider=self.name)
            if hasattr(model, "user"):
                u = _get_real_user(user)
                query = query.filter_by(user=u)
            try:
                return query.one().token
            except NoResultFound:
                return None
        get_token.make_cache_key = make_cache_key
        self.token_getter(get_token)

        @self.token_setter
        def set_token(token):
            has_user = hasattr(model, "user")
            # if there was an existing model, delete it
            existing_query = session.query(model).filter_by(provider=self.name)
            if has_user:
                u = _get_real_user(user)
                existing_query = existing_query.filter_by(user=u)
            existing_query.delete()
            # create a new model for this token
            kwargs = {
                "provider": self.name,
                "token": token,
            }
            if has_user:
                kwargs["user"] = u
            session.add(model(**kwargs))
            # commit to delete and add simultaneously
            session.commit()
            # invalidate cache
            cache.delete_memoized(self.get_token)

        @self.token_deleter
        def delete_token():
            query = session.query(model).filter_by(provider=self.name)
            if hasattr(model, "user"):
                u = _get_real_user(user)
                query = query.filter_by(user=u)
            query.delete()
            # invalidate cache
            cache.delete_memoized(self.get_token)


def _get_real_user(user):
    """
    set_token_storage_sqlalchemy() has a user parameter that can be called with:

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
    return user
