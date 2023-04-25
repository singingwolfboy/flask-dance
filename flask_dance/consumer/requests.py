from functools import wraps

from flask import redirect, url_for
from oauthlib.common import to_unicode
from requests_oauthlib import OAuth1Session as BaseOAuth1Session
from requests_oauthlib import OAuth2Session as BaseOAuth2Session
from urlobject import URLObject
from werkzeug.utils import cached_property


class OAuth1Session(BaseOAuth1Session):
    """
    A :class:`requests.Session` subclass that can do some special things:

    * lazy-loads OAuth1 tokens from the storage via the blueprint
    * handles OAuth1 authentication
      (from :class:`requests_oauthlib.OAuth1Session` superclass)
    * has a ``base_url`` property used for relative URL resolution

    Note that this is a session between the consumer (your website) and the
    provider (e.g. Google), and *not* a session between a user of your website
    and your website.
    """

    def __init__(self, blueprint=None, base_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.blueprint = blueprint
        self.base_url = URLObject(base_url)

    @cached_property
    def token(self):
        """
        Get and set the values in the OAuth token, structured as a dictionary.
        """
        return self.blueprint.token

    def load_token(self):
        t = self.token
        if t and "oauth_token" in t and "oauth_token_secret" in t:
            # This really, really violates the Law of Demeter, but
            # I don't see a better way to set these parameters. :(
            self.auth.client.resource_owner_key = to_unicode(t["oauth_token"])
            self.auth.client.resource_owner_secret = to_unicode(t["oauth_token_secret"])
            return True
        return False

    @property
    def authorized(self):
        """This is the property used when you have a statement in your code
        that reads "if <provider>.authorized:", e.g. "if google.authorized:".

        The way it works is kind of complicated: this function just tries
        to load the token, and then the 'super()' statement basically just
        tests if the token exists (see BaseOAuth1Session.authorized).

        To load the token, it calls the load_token() function within this class,
        which in turn checks the 'token' property of this class (another
        function), which in turn checks the 'token' property of the blueprint
        (see base.py), which calls 'storage.get()' to actually try to load
        the token from the cache/db (see the 'get()' function in
        storage/sqla.py).
        """
        self.load_token()
        return super().authorized

    @property
    def authorization_required(self):
        """
        .. versionadded:: 1.3.0

        This is a decorator for a view function. If the current user does not
        have an OAuth token, then they will be redirected to the
        :meth:`~flask_dance.consumer.oauth1.OAuth1ConsumerBlueprint.login`
        view to obtain one.
        """

        def wrapper(func):
            @wraps(func)
            def check_authorization(*args, **kwargs):
                if not self.authorized:
                    endpoint = f"{self.blueprint.name}.login"
                    return redirect(url_for(endpoint))
                return func(*args, **kwargs)

            return check_authorization

        return wrapper

    def prepare_request(self, request):
        if self.base_url:
            request.url = self.base_url.relative(request.url)
        return super().prepare_request(request)

    def request(
        self, method, url, data=None, headers=None, should_load_token=True, **kwargs
    ):
        if should_load_token:
            self.load_token()
        return super().request(
            method=method, url=url, data=data, headers=headers, **kwargs
        )


class OAuth2Session(BaseOAuth2Session):
    """
    A :class:`requests.Session` subclass that can do some special things:

    * lazy-loads OAuth2 tokens from the storage via the blueprint
    * handles OAuth2 authentication
      (from :class:`requests_oauthlib.OAuth2Session` superclass)
    * has a ``base_url`` property used for relative URL resolution

    Note that this is a session between the consumer (your website) and the
    provider (e.g. Google), and *not* a session between a user of your website
    and your website.
    """

    def __init__(self, blueprint=None, base_url=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.blueprint = blueprint
        self.base_url = URLObject(base_url)
        del self.token

    @cached_property
    def token(self):
        """
        Get and set the values in the OAuth token, structured as a dictionary.
        """
        return self.blueprint.token

    def load_token(self):
        self._client.token = self.token
        if self.token:
            self._client.populate_token_attributes(self.token)
            return True
        return False

    @property
    def access_token(self):
        """
        Returns the ``access_token`` from the OAuth token.
        """
        return self.token and self.token.get("access_token")

    @property
    def authorized(self):
        """This is the property used when you have a statement in your code
        that reads "if <provider>.authorized:", e.g. "if google.authorized:".

        The way it works is kind of complicated: this function just tries
        to load the token, and then the 'super()' statement basically just
        tests if the token exists (see BaseOAuth1Session.authorized).

        To load the token, it calls the load_token() function within this class,
        which in turn checks the 'token' property of this class (another
        function), which in turn checks the 'token' property of the blueprint
        (see base.py), which calls 'storage.get()' to actually try to load
        the token from the cache/db (see the 'get()' function in
        storage/sqla.py).
        """
        self.load_token()
        return super().authorized

    @property
    def authorization_required(self):
        """
        .. versionadded:: 1.3.0

        This is a decorator for a view function. If the current user does not
        have an OAuth token, then they will be redirected to the
        :meth:`~flask_dance.consumer.oauth2.OAuth2ConsumerBlueprint.login`
        view to obtain one.
        """

        def wrapper(func):
            @wraps(func)
            def check_authorization(*args, **kwargs):
                if not self.authorized:
                    endpoint = f"{self.blueprint.name}.login"
                    return redirect(url_for(endpoint))
                return func(*args, **kwargs)

            return check_authorization

        return wrapper

    def request(self, method, url, data=None, headers=None, **kwargs):
        if self.base_url:
            url = self.base_url.relative(url)

        self.load_token()
        return super().request(
            method=method,
            url=url,
            data=data,
            headers=headers,
            client_id=self.blueprint.client_id,
            client_secret=self.blueprint.client_secret,
            **kwargs,
        )
