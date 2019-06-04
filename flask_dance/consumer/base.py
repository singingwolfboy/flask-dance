from __future__ import unicode_literals, print_function

import warnings
from datetime import datetime, timedelta
import six
from abc import ABCMeta, abstractmethod, abstractproperty
from werkzeug.datastructures import CallbackDict
import flask
from flask.signals import Namespace
from flask_dance.consumer.storage.session import SessionStorage
from flask_dance.utils import (
    getattrd,
    timestamp_from_datetime,
    invalidate_cached_property,
)


_signals = Namespace()
oauth_authorized = _signals.signal("oauth-authorized")
oauth_before_login = _signals.signal("oauth-before-login")
oauth_error = _signals.signal("oauth-error")


class BaseOAuthConsumerBlueprint(six.with_metaclass(ABCMeta, flask.Blueprint)):
    def __init__(
        self,
        name,
        import_name,
        static_folder=None,
        static_url_path=None,
        template_folder=None,
        url_prefix=None,
        subdomain=None,
        url_defaults=None,
        root_path=None,
        login_url=None,
        authorized_url=None,
        storage=None,
    ):

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
        # `root_path` didn't exist in 0.10, and will cause an error if it's
        # passed in that version. Only pass `root_path` if it's set.
        if bp_kwargs["root_path"] is None:
            del bp_kwargs["root_path"]
        flask.Blueprint.__init__(self, **bp_kwargs)

        login_url = login_url or "/{bp.name}"
        authorized_url = authorized_url or "/{bp.name}/authorized"

        self.add_url_rule(
            rule=login_url.format(bp=self), endpoint="login", view_func=self.login
        )
        self.add_url_rule(
            rule=authorized_url.format(bp=self),
            endpoint="authorized",
            view_func=self.authorized,
        )

        if storage is None:
            self.storage = SessionStorage()
        elif callable(storage):
            self.storage = storage()
        else:
            self.storage = storage

        self.logged_in_funcs = []
        self.from_config = {}
        invalidate_token = lambda d: invalidate_cached_property(self.session, "token")
        self.config = CallbackDict(on_update=invalidate_token)
        self.before_app_request(self.load_config)

    def load_config(self):
        """
        Used to dynamically load variables from the Flask application config
        into the blueprint. To tell this blueprint to pull configuration from
        the app, just set key-value pairs in the ``from_config`` dict. Keys
        are the name of the local variable to set on the blueprint object,
        and values are the variable name in the Flask application config.
        For example:

            blueprint.from_config["session.client_id"] = "GITHUB_OAUTH_CLIENT_ID"

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

    @property
    def storage(self):
        """
        The :doc:`token storage <storages>` that this blueprint
        uses.
        """
        return self._storage

    @storage.setter
    def storage(self, value):
        self._storage = value

    @storage.deleter
    def storage(self):
        del self._storage

    @property
    def token(self):
        """
        This property functions as pass-through to the token storage.
        If you read from this property, you will receive the current
        value from the token storage. If you assign a value to this
        property, it will get set in the token storage.
        """
        _token = self.storage.get(self)
        if _token and _token.get("expires_in") and _token.get("expires_at"):
            # Update the `expires_in` value, so that requests-oauthlib
            # can handle automatic token refreshing. Assume that
            # `expires_at` is a valid Unix timestamp.
            expires_at = datetime.utcfromtimestamp(_token["expires_at"])
            expires_in = expires_at - datetime.utcnow()
            _token["expires_in"] = expires_in.total_seconds()
        return _token

    @token.setter
    def token(self, value):
        _token = value
        if _token and _token.get("expires_in"):
            # Set the `expires_at` value, overwriting any value
            # that may already be there.
            delta = timedelta(seconds=_token["expires_in"])
            expires_at = datetime.utcnow() + delta
            _token["expires_at"] = timestamp_from_datetime(expires_at)
        self.storage.set(self, _token)
        invalidate_cached_property(self.session, "token")

    @token.deleter
    def token(self):
        self.storage.delete(self)
        invalidate_cached_property(self.session, "token")

    @abstractproperty
    def session(self):
        """
        This is a session between the consumer (your website) and the provider
        (e.g. Twitter). It is *not* a session between a user of your website
        and your website.
        """
        raise NotImplementedError()

    @abstractmethod
    def login(self):
        raise NotImplementedError()

    @abstractmethod
    def authorized(self):
        """
        This is the route/function that the user will be redirected to by
        the provider (e.g. Twitter) after the user has logged into the
        provider's website and authorized your app to access their account.
        """
        raise NotImplementedError()
