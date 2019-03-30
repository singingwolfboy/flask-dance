from __future__ import unicode_literals, print_function
import json

import logging
import flask
from flask import request, url_for, redirect, current_app
from werkzeug.wrappers import Response
from werkzeug.utils import cached_property
from oauthlib.oauth2 import MissingCodeError
from .base import (
    BaseOAuthConsumerBlueprint,
    oauth_authorized,
    oauth_before_login,
    oauth_error,
)
from .requests import OAuth2Session
from flask_dance.utils import invalidate_cached_property


log = logging.getLogger(__name__)


class OAuth2ConsumerBlueprint(BaseOAuthConsumerBlueprint):
    """
    A subclass of :class:`flask.Blueprint` that sets up OAuth 2 authentication.
    """

    def __init__(
        self,
        name,
        import_name,
        client_id=None,
        client_secret=None,
        client=None,
        auto_refresh_url=None,
        auto_refresh_kwargs=None,
        scope=None,
        state=None,
        static_folder=None,
        static_url_path=None,
        template_folder=None,
        url_prefix=None,
        subdomain=None,
        url_defaults=None,
        root_path=None,
        login_url=None,
        authorized_url=None,
        base_url=None,
        authorization_url=None,
        authorization_url_params=None,
        token_url=None,
        token_url_params=None,
        redirect_url=None,
        redirect_to=None,
        session_class=None,
        storage=None,
        **kwargs
    ):
        """
        Most of the constructor arguments are forwarded either to the
        :class:`flask.Blueprint` constructor or the
        :class:`requests_oauthlib.OAuth2Session` constructor, including
        ``**kwargs`` (which is forwarded to
        :class:`~requests_oauthlib.OAuth2Session`).
        Only the arguments that are relevant to Flask-Dance are documented here.

        Args:
            base_url: The base URL of the OAuth provider.
                If specified, all URLs passed to this instance will be
                resolved relative to this URL.
            authorization_url: The URL specified by the OAuth provider for
                obtaining an
                `authorization grant <http://tools.ietf.org/html/rfc6749#section-1.3>`__.
                This can be an fully-qualified URL, or a path that is
                resolved relative to the ``base_url``.
            authorization_url_params (dict): A dict of extra
                key-value pairs to include in the query string of the
                ``authorization_url``, beyond those necessary for a standard
                OAuth 2 authorization grant request.
            token_url: The URL specified by the OAuth provider for
                obtaining an
                `access token <http://tools.ietf.org/html/rfc6749#section-1.4>`__.
                This can be an fully-qualified URL, or a path that is
                resolved relative to the ``base_url``.
            token_url_params (dict): A dict of extra
                key-value pairs to include in the query string of the
                ``token_url``, beyond those necessary for a standard
                OAuth 2 access token request.
            login_url: The URL route for the ``login`` view that kicks off
                the OAuth dance. This string will be
                :ref:`formatted <python:formatstrings>`
                with the instance so that attributes can be interpolated.
                Defaults to ``/{bp.name}``, so that the URL is based on the name
                of the blueprint.
            authorized_url: The URL route for the ``authorized`` view that
                completes the OAuth dance. This string will be
                :ref:`formatted <python:formatstrings>`
                with the instance so that attributes can be interpolated.
                Defaults to ``/{bp.name}/authorized``, so that the URL is
                based on the name of the blueprint.
            redirect_url: When the OAuth dance is complete,
                redirect the user to this URL.
            redirect_to: When the OAuth dance is complete,
                redirect the user to the URL obtained by calling
                :func:`~flask.url_for` with this argument. If you do not specify
                either ``redirect_url`` or ``redirect_to``, the user will be
                redirected to the root path (``/``).
            session_class: The class to use for creating a Requests session
                between the consumer (your website) and the provider (e.g.
                Twitter). Defaults to
                :class:`~flask_dance.consumer.requests.OAuth2Session`.
            storage: A token storage class, or an instance of a token storage
                class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.storage.session.SessionStorage`.
        """
        BaseOAuthConsumerBlueprint.__init__(
            self,
            name,
            import_name,
            static_folder=static_folder,
            static_url_path=static_url_path,
            template_folder=template_folder,
            url_prefix=url_prefix,
            subdomain=subdomain,
            url_defaults=url_defaults,
            root_path=root_path,
            login_url=login_url,
            authorized_url=authorized_url,
            storage=storage,
        )

        self.base_url = base_url
        self.session_class = session_class or OAuth2Session

        # passed to OAuth2Session()
        self._client_id = client_id
        self.client = client
        self.auto_refresh_url = auto_refresh_url
        self.auto_refresh_kwargs = auto_refresh_kwargs
        self.scope = scope
        self.state = state
        self.kwargs = kwargs
        self.client_secret = client_secret

        # used by view functions
        self.authorization_url = authorization_url
        self.authorization_url_params = authorization_url_params or {}
        self.token_url = token_url
        self.token_url_params = token_url_params or {}
        self.redirect_url = redirect_url
        self.redirect_to = redirect_to

        self.teardown_app_request(self.teardown_session)

    @property
    def client_id(self):
        return self.session.client_id

    @client_id.setter
    def client_id(self, value):
        self.session.client_id = value
        # due to a bug in requests-oauthlib, we need to set this manually
        self.session._client.client_id = value

    @cached_property
    def session(self):
        """
        This is a session between the consumer (your website) and the provider
        (e.g. Twitter). It is *not* a session between a user of your website
        and your website.
        :return:
        """
        ret = self.session_class(
            client_id=self._client_id,
            client=self.client,
            auto_refresh_url=self.auto_refresh_url,
            auto_refresh_kwargs=self.auto_refresh_kwargs,
            scope=self.scope,
            state=self.state,
            blueprint=self,
            base_url=self.base_url,
            **self.kwargs
        )

        def token_updater(token):
            self.token = token

        ret.token_updater = token_updater
        return self.session_created(ret)

    def session_created(self, session):
        return session

    def teardown_session(self, exception=None):
        invalidate_cached_property(self, "session")

    def login(self):
        log.debug("client_id = %s", self.client_id)
        self.session.redirect_uri = url_for(".authorized", _external=True)
        url, state = self.session.authorization_url(
            self.authorization_url, state=self.state, **self.authorization_url_params
        )
        state_key = "{bp.name}_oauth_state".format(bp=self)
        flask.session[state_key] = state
        log.debug("state = %s", state)
        log.debug("redirect URL = %s", url)
        oauth_before_login.send(self, url=url)
        return redirect(url)

    def authorized(self):
        """
        This is the route/function that the user will be redirected to by
        the provider (e.g. Twitter) after the user has logged into the
        provider's website and authorized your app to access their account.
        """
        if self.redirect_url:
            next_url = self.redirect_url
        elif self.redirect_to:
            next_url = url_for(self.redirect_to)
        else:
            next_url = "/"
        log.debug("next_url = %s", next_url)

        # check for error in request args
        error = request.args.get("error")
        if error:
            error_desc = request.args.get("error_description")
            error_uri = request.args.get("error_uri")
            log.warning(
                "OAuth 2 authorization error: %s description: %s uri: %s",
                error,
                error_desc,
                error_uri,
            )
            oauth_error.send(
                self, error=error, error_description=error_desc, error_uri=error_uri
            )
            return redirect(next_url)

        state_key = "{bp.name}_oauth_state".format(bp=self)
        if state_key not in flask.session:
            # can't validate state, so redirect back to login view
            log.info("state not found, redirecting user to login")
            return redirect(url_for(".login"))

        state = flask.session[state_key]
        log.debug("state = %s", state)
        self.session._state = state
        del flask.session[state_key]

        self.session.redirect_uri = url_for(".authorized", _external=True)

        log.debug("client_id = %s", self.client_id)
        log.debug("client_secret = %s", self.client_secret)
        try:
            token = self.session.fetch_token(
                self.token_url,
                authorization_response=request.url,
                client_secret=self.client_secret,
                **self.token_url_params
            )
        except MissingCodeError as e:
            e.args = (
                e.args[0],
                "The redirect request did not contain the expected parameters. Instead I got: {}".format(
                    json.dumps(request.args)
                ),
            )
            raise

        results = oauth_authorized.send(self, token=token) or []
        set_token = True
        for func, ret in results:
            if isinstance(ret, (Response, current_app.response_class)):
                return ret
            if ret == False:
                set_token = False

        if set_token:
            try:
                self.token = token
            except ValueError as error:
                log.warning("OAuth 2 authorization error: %s", str(error))
                oauth_error.send(self, error=error)
        return redirect(next_url)
