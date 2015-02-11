from __future__ import unicode_literals, print_function

import sys
from flask import request, url_for, redirect
from urlobject import URLObject
from requests_oauthlib import OAuth1Session
from oauthlib.oauth1 import SIGNATURE_HMAC, SIGNATURE_TYPE_AUTH_HEADER
from oauthlib.common import to_unicode
from .base import BaseOAuthConsumerBlueprint, oauth_authorized


class OAuth1SessionWithBaseURL(OAuth1Session):
    def __init__(self, base_url=None, *args, **kwargs):
        super(OAuth1SessionWithBaseURL, self).__init__(*args, **kwargs)
        self.base_url = URLObject(base_url)

    def prepare_request(self, request):
        if self.base_url:
            request.url = self.base_url.relative(request.url)
        return super(OAuth1SessionWithBaseURL, self).prepare_request(request)


class OAuth1ConsumerBlueprint(BaseOAuthConsumerBlueprint):
    """
    A subclass of :class:`flask.Blueprint` that sets up OAuth 1 authentication.
    """
    def __init__(self, name, import_name,
            client_key=None,
            client_secret=None,
            signature_method=SIGNATURE_HMAC,
            signature_type=SIGNATURE_TYPE_AUTH_HEADER,
            rsa_key=None,
            client_class=None,
            force_include_body=False,

            static_folder=None, static_url_path=None, template_folder=None,
            url_prefix=None, subdomain=None, url_defaults=None, root_path=None,

            login_url=None,
            authorized_url=None,
            base_url=None,
            request_token_url=None,
            authorization_url=None,
            access_token_url=None,
            redirect_url=None,
            redirect_to=None,
            session_class=None,

            **kwargs):
        """
        Most of the constructor arguments are forwarded either to the
        :class:`flask.Blueprint` constructor or the
        :class:`requests_oauthlib.OAuth1Session` construtor, including
        ``**kwargs`` (which is forwarded to
        :class:`~requests_oauthlib.OAuth1Session`).
        The only arguments that are specific to this class are
        ``base_url``,
        ``request_token_url``, ``authorization_url``, ``access_token_url``,
        ``login_url``, ``authorized_url``,
        ``redirect_url``, ``redirect_to``, and ``session_class``.

        Args:
            base_url (str, optional): The base URL of the OAuth provider.
                If specified, all URLs passed to this instance will be
                resolved relative to this URL.
            request_token_url (str): The URL specified by the OAuth provider for
                obtaining a
                `request token <http://oauth.net/core/1.0a/#auth_step1>`_.
                This can be an fully-qualified URL, or a path that is
                resolved relative to the ``base_url``.
            authorization_url (str): The URL specified by the OAuth provider for
                the user to
                `grant token authorization <http://oauth.net/core/1.0a/#auth_step2>`_.
                This can be an fully-qualified URL, or a path that is
                resolved relative to the ``base_url``.
            access_token_url (str): The URL specified by the OAuth provider for
                obtaining an
                `access token <http://oauth.net/core/1.0a/#auth_step3>`_.
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
                :class:`~flask_dance.consumer.oauth1.OAuth1SessionWithBaseURL`.
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

        session_class = session_class or OAuth1SessionWithBaseURL
        self.session = session_class(
            client_key=client_key,
            client_secret=client_secret,
            signature_method=signature_method,
            signature_type=signature_type,
            rsa_key=rsa_key,
            client_class=client_class,
            force_include_body=force_include_body,
            base_url=base_url,
            **kwargs
        )

        self.request_token_url = request_token_url
        self.authorization_url = authorization_url
        self.access_token_url = access_token_url
        self.redirect_url = redirect_url
        self.redirect_to = redirect_to

    @property
    def client_key(self):
        return self.session._client.client.client_key

    @client_key.setter
    def client_key(self, value):
        self.session._client.client.client_key = to_unicode(value)

    @property
    def client_secret(self):
        return self.session._client.client.client_secret

    @client_secret.setter
    def client_secret(self, value):
        self.session._client.client.client_secret = to_unicode(value)

    @property
    def rsa_key(self):
        return self.session._client.client.rsa_key

    @rsa_key.setter
    def rsa_key(self, value):
        self.session._client.client.rsa_key = to_unicode(value)

    def login(self):
        secure = request.is_secure or request.headers.get("X-Forwarded-Proto", "http") == "https"
        callback_uri = url_for(
            ".authorized", next=request.args.get('next'), _external=True,
            _scheme="https" if secure else "http",
        )
        self.session._client.client.callback_uri = to_unicode(callback_uri)
        self.session.fetch_request_token(self.request_token_url)
        url = self.session.authorization_url(self.authorization_url)
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
        self.session.parse_authorization_response(request.url)
        token = self.session.fetch_access_token(self.access_token_url)
        self.token = token
        oauth_authorized.send(self, token=token)
        return redirect(next_url)

    def load_token(self):
        token = self.token
        if token and "oauth_token" in token and "oauth_token_secret" in token:
            # This really, really violates the Law of Demeter, but
            # I don't see a better way to set these parameters. :(
            self.session.auth.client.resource_owner_key = to_unicode(token["oauth_token"])
            self.session.auth.client.resource_owner_secret = to_unicode(token["oauth_token_secret"])
