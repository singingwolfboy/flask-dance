from __future__ import unicode_literals, print_function

from lazy import lazy
from urlobject import URLObject
from requests_oauthlib import OAuth1Session as BaseOAuth1Session
from requests_oauthlib import OAuth2Session as BaseOAuth2Session
from oauthlib.common import to_unicode


class OAuth1Session(BaseOAuth1Session):
    """
    A :class:`requests.Session` subclass that can do some special things:

    * lazy-loads OAuth1 tokens from the backend via the blueprint
    * handles OAuth1 authentication
      (from :class:`requests_oauthlib.OAuth1Session` superclass)
    * has a ``base_url`` property used for relative URL resolution

    Note that this is a session between the consumer (your website) and the
    provider (e.g. Twitter), and *not* a session between a user of your website
    and your website.
    """
    def __init__(self, blueprint=None, base_url=None, *args, **kwargs):
        super(OAuth1Session, self).__init__(*args, **kwargs)
        self.blueprint = blueprint
        self.base_url = URLObject(base_url)

    @lazy
    def token(self):
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
        """ This is the property used when you have a statement in your code
        that reads "if <provider>.authorized:", e.g. "if twitter.authorized:".

        The way it works is kind of complicated: this function just tries
        to load the token, and then the 'super()' statement basically just
        tests if the token exists (see BaseOAuth1Session.authorized).

        To load the token, it calls the load_token() function within this class,
        which in turn checks the 'token' property of this class (another
        function), which in turn checks the 'token' property of the blueprint
        (see base.py), which calls 'backend.get()' to actually try to load
        the token from the cache/db (see the 'get()' function in
        backend/sqla.py).

        :return:
        """
        self.load_token()
        return super(OAuth1Session, self).authorized

    def prepare_request(self, request):
        if self.base_url:
            request.url = self.base_url.relative(request.url)
        return super(OAuth1Session, self).prepare_request(request)

    def request(self, method, url, data=None, headers=None, **kwargs):
        self.load_token()
        return super(OAuth1Session, self).request(
            method=method, url=url, data=data, headers=headers, **kwargs
        )


class OAuth2Session(BaseOAuth2Session):
    """
    A :class:`requests.Session` subclass that can do some special things:

    * lazy-loads OAuth2 tokens from the backend via the blueprint
    * handles OAuth2 authentication
      (from :class:`requests_oauthlib.OAuth2Session` superclass)
    * has a ``base_url`` property used for relative URL resolution

    Note that this is a session between the consumer (your website) and the
    provider (e.g. Twitter), and *not* a session between a user of your website
    and your website.
    """
    def __init__(self, blueprint=None, base_url=None, *args, **kwargs):
        super(OAuth2Session, self).__init__(*args, **kwargs)
        self.blueprint = blueprint
        self.base_url = URLObject(base_url)
        lazy.invalidate(self, "token")

    @lazy
    def token(self):
        return self.blueprint.token

    def load_token(self):
        self._client.token = self.token
        if self.token:
            self._client._populate_attributes(self.token)
            return True
        return False

    @property
    def access_token(self):
        return self.token and self.token.get("access_token")

    @property
    def authorized(self):
        """ This is the property used when you have a statement in your code
        that reads "if <provider>.authorized:", e.g. "if twitter.authorized:".

        The way it works is kind of complicated: this function just tries
        to load the token, and then the 'super()' statement basically just
        tests if the token exists (see BaseOAuth1Session.authorized).

        To load the token, it calls the load_token() function within this class,
        which in turn checks the 'token' property of this class (another
        function), which in turn checks the 'token' property of the blueprint
        (see base.py), which calls 'backend.get()' to actually try to load
        the token from the cache/db (see the 'get()' function in
        backend/sqla.py).

        :return:
        """
        self.load_token()
        return super(OAuth2Session, self).authorized

    def request(self, method, url, data=None, headers=None, **kwargs):
        if self.base_url:
            url = self.base_url.relative(url)

        self.load_token()
        return super(OAuth2Session, self).request(
            method=method, url=url, data=data, headers=headers,
            client_id=self.blueprint.client_id,
            client_secret=self.blueprint.client_secret,
            **kwargs
        )
