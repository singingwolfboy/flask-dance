from __future__ import unicode_literals, print_function

import flask
from flask import request, url_for, redirect
from urlobject import URLObject
from requests_oauthlib import OAuth2Session
from .base import BaseOAuthConsumerBlueprint


class OAuth2SessionWithBaseURL(OAuth2Session):
    def __init__(self, base_url=None, *args, **kwargs):
        super(OAuth2SessionWithBaseURL, self).__init__(*args, **kwargs)
        self.base_url = URLObject(base_url)

    def request(self, method, url, data=None, headers=None, **kwargs):
        if self.base_url:
            url = self.base_url.relative(url)
        return super(OAuth2SessionWithBaseURL, self).request(
            method=method, url=url, data=data, headers=headers, **kwargs
        )


class OAuth2ConsumerBlueprint(BaseOAuthConsumerBlueprint):
    def __init__(self, name, import_name,
            client_id=None,
            client_secret=None,
            client=None,
            auto_refresh_url=None,
            auto_refresh_kwargs=None,
            scope=None,
            state=None,

            static_folder=None, static_url_path=None, template_folder=None,
            url_prefix=None, subdomain=None, url_defaults=None, root_path=None,

            login_url=None,
            authorized_url=None,
            base_url=None,
            authorization_url=None,
            token_url=None,
            redirect_url=None,
            redirect_to=None,

            **kwargs):

        if not redirect_url and not redirect_to:
            raise AttributeError("One of redirect_url or redirect_to must be defined")

        BaseOAuthConsumerBlueprint.__init__(
            self, name, import_name,
            static_folder=static_folder,
            static_url_path=static_url_path,
            template_folder=template_folder,
            url_prefix=url_prefix, subdomain=subdomain,
            url_defaults=url_defaults, root_path=root_path,
            login_url=login_url,
            authorized_url=authorized_url,
        )

        self.session = OAuth2SessionWithBaseURL(
            client_id=client_id,
            client=client,
            auto_refresh_url=auto_refresh_url,
            auto_refresh_kwargs=auto_refresh_kwargs,
            scope=scope,
            state=state,
            token_updater=self.set_token,
            base_url=base_url,
            **kwargs
        )

        self.client_secret = client_secret
        self.state = state

        self.authorization_url = authorization_url
        self.token_url = token_url
        self.redirect_url = redirect_url
        self.redirect_to = redirect_to

    def token_setter(self, func):
        BaseOAuthConsumerBlueprint.token_setter(self, func)
        if hasattr(self, "session"):
            self.session.token_updater = func

    def login(self):
        self.session.redirect_uri = url_for(
            ".authorized", next=request.args.get('next'), _external=True,
        )
        url, state = self.session.authorization_url(
            self.authorization_url, state=self.state,
        )
        state_key = "{bp.name}_oauth_state".format(bp=self)
        flask.session[state_key] = state
        return redirect(url)

    def authorized(self):
        next_url = request.args.get('next') or self.redirect_url or url_for(self.redirect_to)
        state_key = "{bp.name}_oauth_state".format(bp=self)
        self.session._state = flask.session[state_key]
        del flask.session[state_key]

        token = self.session.fetch_token(
            self.token_url,
            authorization_response=request.url,
            client_secret=self.client_secret,
        )
        self.logged_in_callback(token)
        self.token = token
        return redirect(next_url)

    def assign_token_to_session(self, identifier=None):
        token = self.get_token(identifier=identifier)
        if token:
            # This really, really violates the Law of Demeter, but
            # I don't see a better way to set these parameters. :(
            self.session.token = token
            self.session._client.token = token
            self.session._client._populate_attributes(token)
