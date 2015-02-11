from __future__ import unicode_literals, print_function

import flask
from flask import request, url_for, redirect
from urlobject import URLObject
from requests_oauthlib import OAuth2Session
from .base import BaseOAuthConsumerBlueprint, oauth_authorized


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
    """
    A subclass of :class:`flask.Blueprint` that sets up OAuth 2 authentication.
    """
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
            session_class=None,

            **kwargs):
        """
        Most of the constructor arguments are forwarded either to the
        :class:`flask.Blueprint` constructor or the
        :class:`requests_oauthlib.OAuth2Session` construtor, including
        ``**kwargs`` (which is forwarded to
        :class:`~requests_oauthlib.OAuth2Session`).
        The only arguments that are specific to this class are
        ``base_url``,
        ``authorization_url``, ``token_url``,
        ``login_url``, ``authorized_url``,
        ``redirect_url``, ``redirect_to``, and ``session_class``.

        Args:
            base_url (str, optional): The base URL of the OAuth provider.
                If specified, all URLs passed to this instance will be
                resolved relative to this URL.
            authorization_url (str): The URL specified by the OAuth provider for
                obtaining an
                `authorization grant <http://tools.ietf.org/html/rfc6749#section-1.3>`_.
                This can be an fully-qualified URL, or a path that is
                resolved relative to the ``base_url``.
            token_url (str): The URL specified by the OAuth provider for
                obtaining an
                `access token <http://tools.ietf.org/html/rfc6749#section-1.4>`_.
                This can be an fully-qualified URL, or a path that is
                resolved relative to the ``base_url``.
            login_url (str, optional): The URL route for the ``login`` view that kicks off
                the OAuth dance. This string will be
                :ref:`formatted <python:formatstrings>`
                with the instance so that attributes can be interpolated.
                Defaults to ``/{bp.name}``, so that the URL is based on the name
                of the blueprint.
            authorized_url (str, optional): The URL route for the ``authorized`` view that
                completes the OAuth dance. This string will be
                :ref:`formatted <python:formatstrings>`
                with the instance so that attributes can be interpolated.
                Defaults to ``/{bp.name}/authorized``, so that the URL is
                based on the name of the blueprint.
            redirect_url (str, optional): When the OAuth dance is complete,
                redirect the user to this URL.
            redirect_to (str, optional): When the OAuth dance is complete,
                redirect the user to the URL obtained by calling
                :func:`~flask.url_for` with this argument. If you do not specify
                either ``redirect_url`` or ``redirect_to``, the user will be
                redirected to the root path (``/``).
            session_class (class, optional): The class to use for creating a
                Requests session. Defaults to
                :class:`~flask_dance.consumer.oauth2.OAuth2SessionWithBaseURL`.
        """
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

        session_class = session_class or OAuth2SessionWithBaseURL
        self.session = session_class(
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
        """
        A decorator used to indicate the function used to store a token
        from a completed OAuth dance, so that it can be retrieved later.
        This function will also be called when the token is refreshed.
        """
        BaseOAuthConsumerBlueprint.token_setter(self, func)
        if hasattr(self, "session"):
            self.session.token_updater = func

    @property
    def client_id(self):
        return self.session.client_id

    @client_id.setter
    def client_id(self, value):
        self.session.client_id = value
        self.session._client.client_id = value

    def login(self):
        secure = request.is_secure or request.headers.get("X-Forwarded-Proto", "http") == "https"
        self.session.redirect_uri = url_for(
            ".authorized", next=request.args.get('next'), _external=True,
            _scheme="https" if secure else "http",
        )
        url, state = self.session.authorization_url(
            self.authorization_url, state=self.state,
        )
        state_key = "{bp.name}_oauth_state".format(bp=self)
        flask.session[state_key] = state
        return redirect(url)

    def authorized(self):
        if "next" in request.args:
            next_url = request.args["next"]
        elif self.redirect_url:
            next_url = self.redirect_url
        elif self.redirect_to:
            next_url = url_for(self.redirect_to)
        else:
            next_url = "/"
        state_key = "{bp.name}_oauth_state".format(bp=self)
        self.session._state = flask.session[state_key]
        del flask.session[state_key]

        url = URLObject(request.url)
        if request.headers.get("X-Forwarded-Proto", "http") == "https":
            url = url.with_scheme("https")
        token = self.session.fetch_token(
            self.token_url,
            authorization_response=url,
            client_secret=self.client_secret,
        )
        self.token = token
        oauth_authorized.send(self, token=token)
        return redirect(next_url)

    def load_token(self):
        token = self.token
        if token:
            # This really, really violates the Law of Demeter, but
            # I don't see a better way to set these parameters. :(
            self.session.token = token
            self.session._client.token = token
            self.session._client._populate_attributes(token)
