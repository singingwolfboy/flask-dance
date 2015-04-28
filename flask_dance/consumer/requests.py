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
    def authorized(self):
        self.load_token()
        return super(OAuth2Session, self).authorized

    def request(self, method, url, data=None, headers=None, **kwargs):
        if self.base_url:
            url = self.base_url.relative(url)

        self.load_token()
        return super(OAuth2Session, self).request(
            method=method, url=url, data=data, headers=headers, **kwargs
        )
