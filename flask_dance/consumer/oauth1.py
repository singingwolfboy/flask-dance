import logging
from flask import request, url_for, redirect, current_app
from werkzeug.wrappers import Response
from werkzeug.utils import cached_property
from requests_oauthlib.oauth1_session import TokenRequestDenied, TokenMissing
from oauthlib.oauth1 import SIGNATURE_HMAC, SIGNATURE_TYPE_AUTH_HEADER
from oauthlib.common import to_unicode
from .base import (
    BaseOAuthConsumerBlueprint,
    oauth_authorized,
    oauth_before_login,
    oauth_error,
)
from .requests import OAuth1Session
from flask_dance.utils import invalidate_cached_property


log = logging.getLogger(__name__)


class OAuth1ConsumerBlueprint(BaseOAuthConsumerBlueprint):
    """
    A subclass of :class:`flask.Blueprint` that sets up OAuth 1 authentication.
    """

    def __init__(
        self,
        name,
        import_name,
        client_key=None,
        client_secret=None,
        *,
        signature_method=SIGNATURE_HMAC,
        signature_type=SIGNATURE_TYPE_AUTH_HEADER,
        rsa_key=None,
        client_class=None,
        force_include_body=False,
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
        request_token_url=None,
        authorization_url=None,
        access_token_url=None,
        redirect_url=None,
        redirect_to=None,
        session_class=None,
        storage=None,
        rule_kwargs=None,
        **kwargs
    ):
        """
        Most of the constructor arguments are forwarded either to the
        :class:`flask.Blueprint` constructor or the
        :class:`requests_oauthlib.OAuth1Session` constructor, including
        ``**kwargs`` (which is forwarded to
        :class:`~requests_oauthlib.OAuth1Session`).
        Only the arguments that are relevant to Flask-Dance are documented here.

        Args:
            base_url: The base URL of the OAuth provider.
                If specified, all URLs passed to this instance will be
                resolved relative to this URL.
            request_token_url: The URL specified by the OAuth provider for
                obtaining a
                `request token <http://oauth.net/core/1.0a/#auth_step1>`_.
                This can be an fully-qualified URL, or a path that is
                resolved relative to the ``base_url``.
            authorization_url: The URL specified by the OAuth provider for
                the user to
                `grant token authorization <http://oauth.net/core/1.0a/#auth_step2>`_.
                This can be an fully-qualified URL, or a path that is
                resolved relative to the ``base_url``.
            access_token_url: The URL specified by the OAuth provider for
                obtaining an
                `access token <http://oauth.net/core/1.0a/#auth_step3>`_.
                This can be an fully-qualified URL, or a path that is
                resolved relative to the ``base_url``.
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
                :class:`~flask_dance.consumer.requests.OAuth1Session`.
            storage: A token storage class, or an instance of a token storage
                class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.storage.session.SessionStorage`.
            rule_kwargs (dict, optional): Additional arguments that should be passed when adding
                the login and authorized routes. Defaults to ``None``.
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
            rule_kwargs=rule_kwargs,
        )

        self.base_url = base_url
        self.session_class = session_class or OAuth1Session

        # passed to OAuth1Session()
        self.client_key = client_key
        self.client_secret = client_secret
        self.signature_method = signature_method
        self.signature_type = signature_type
        self.rsa_key = rsa_key
        self.client_class = client_class
        self.force_include_body = force_include_body
        self.kwargs = kwargs

        # used by view functions
        self.request_token_url = request_token_url
        self.authorization_url = authorization_url
        self.access_token_url = access_token_url
        self.redirect_url = redirect_url
        self.redirect_to = redirect_to

        self.teardown_app_request(self.teardown_session)

    @cached_property
    def session(self):
        """
        This is a session between the consumer (your website) and the provider
        (e.g. Twitter). It is *not* a session between a user of your website
        and your website.
        :return:
        """
        return self.session_class(
            client_key=self.client_key,
            client_secret=self.client_secret,
            signature_method=self.signature_method,
            signature_type=self.signature_type,
            rsa_key=self.rsa_key,
            client_class=self.client_class,
            force_include_body=self.force_include_body,
            blueprint=self,
            base_url=self.base_url,
            **self.kwargs
        )

    def teardown_session(self, exception=None):
        try:
            invalidate_cached_property(self, "session")
        except KeyError:
            pass

    def login(self):
        callback_uri = url_for(".authorized", _external=True)
        self.session._client.client.callback_uri = to_unicode(callback_uri)

        try:
            self.session.fetch_request_token(
                self.request_token_url, should_load_token=False
            )
        except TokenRequestDenied as err:
            message = err.args[0]
            response = getattr(err, "response", None)
            log.warning("OAuth 1 request token error: %s", message)
            oauth_error.send(self, message=message, response=response)
            # can't proceed with OAuth, have to just redirect to next_url
            if self.redirect_url:
                next_url = self.redirect_url
            elif self.redirect_to:
                next_url = url_for(self.redirect_to)
            else:
                next_url = "/"
            return redirect(next_url)

        url = self.session.authorization_url(self.authorization_url)
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

        try:
            self.session.parse_authorization_response(request.url)
        except TokenMissing as err:
            message = err.args[0]
            response = getattr(err, "response", None)
            log.warning("OAuth 1 access token error: %s", message)
            oauth_error.send(self, message=message, response=response)
            return redirect(next_url)

        try:
            token = self.session.fetch_access_token(
                self.access_token_url, should_load_token=False
            )
        except ValueError as err:
            # can't proceed with OAuth, have to just redirect to next_url
            message = err.args[0]
            response = getattr(err, "response", None)
            log.warning("OAuth 1 access token error: %s", message)
            oauth_error.send(self, message=message, response=response)
            return redirect(next_url)

        results = oauth_authorized.send(self, token=token) or []
        set_token = True
        for func, ret in results:
            if isinstance(ret, (Response, current_app.response_class)):
                return ret
            if ret == False:
                set_token = False

        if set_token:
            self.token = token
        return redirect(next_url)
