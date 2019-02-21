from __future__ import unicode_literals
from oauthlib.oauth2.rfc6749 import tokens
from oauthlib.oauth2.rfc6749.clients.web_application import WebApplicationClient
from flask_dance.consumer import OAuth2ConsumerBlueprint
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

__maintainer__ = "Ryan Schaffer <schaffer.ry@gmail.com>"

AUTH_HEADER = "auth_header"
URI_QUERY = "query"
BODY = "body"
ZOHO_TOKEN_HEADER = "Zoho-oauthtoken"


def make_zoho_blueprint(
    client_id=None,
    client_secret=None,
    scope=None,
    redirect_url=None,
    offline=False,
    redirect_to=None,
    login_url=None,
    session_class=None,
    backend=None,
    storage=None,
    reprompt_consent=False,
):
    """
    Make a blueprint for authenticating with Zoho using OAuth 2. This requires
    a client ID and client secret from Zoho. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables ZOHO_OAUTH_CLIENT_ID and ZOHO_OAUTH_CLIENT_SECRET.
    IMPORTANT: Configuring the base_url is not supported in this config.

    Args:
        client_id (str): The client ID for your application on Zoho.
        client_secret (str): The client secret for your application on Zoho
        scope (list, optional): list of scopes (str) for the OAuth token
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/zoho``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/zoho/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.consumer.requests.OAuth2Session`.
        storage: A token storage class, or an instance of a token storage
                class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.storage.session.SessionStorage`.
        offline (bool): Whether to request `offline access`
            for the OAuth token. Defaults to False
        reprompt_consent (bool): If True, force Zoho to re-prompt the user
            for their consent, even if the user has already given their
            consent. Defaults to False
    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :ref:`blueprint <flask:blueprints>` to attach to your Flask app.
    """
    scope = scope or ["ZohoCRM.users.all"]
    base_url = "https://www.zohoapis.com/"
    client = ZohoWebClient(client_id, token_type=ZOHO_TOKEN_HEADER)
    authorization_url_params = {}
    authorization_url_params["access_type"] = "offline" if offline else "online"
    if reprompt_consent:
        authorization_url_params["prompt"] = "consent"
    zoho_bp = OAuth2ConsumerBlueprint(
        "zoho",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        client=client,
        scope=scope,
        base_url=base_url,
        token_url="https://accounts.zoho.com/oauth/v2/token",
        authorization_url="https://accounts.zoho.com/oauth/v2/auth",
        authorization_url_params=authorization_url_params,
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        session_class=session_class,
        backend=backend,
        storage=storage,
    )
    if not client_id:
        zoho_bp.from_config["client_id"] = "ZOHO_OAUTH_CLIENT_ID"
    if not client_secret:
        zoho_bp.from_config["client_secret"] = "ZOHO_OAUTH_CLIENT_SECRET"

    @zoho_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.zoho_oauth = zoho_bp.session

    return zoho_bp


zoho = LocalProxy(partial(_lookup_app_object, "zoho_oauth"))


class ZohoWebClient(WebApplicationClient):
    """
    Remove the requirement that token_types adhere to OAuth Standard
    """

    @property
    def token_types(self):
        return {
            "Bearer": self._add_bearer_token,
            "MAC": self._add_mac_token,
            ZOHO_TOKEN_HEADER: self._add_zoho_token,
        }

    def _add_zoho_token(
        self, uri, http_method="GET", body=None, headers=None, token_placement=None
    ):
        """Add a zoho token to the request uri, body or authorization header. follows bearer pattern"""
        headers = self.prepare_zoho_headers(self.access_token, headers)
        return uri, headers, body

    @staticmethod
    def prepare_zoho_headers(token, headers=None):
        """Add a `Zoho Token`_ to the request URI.
        Recommended method of passing bearer tokens.

        Authorization: Zoho-oauthtoken h480djs93hd8

        .. _`Zoho-oauthtoken Token`: custom zoho token
        """
        headers = headers or {}
        headers["Authorization"] = "{token_header} {token}".format(
            token_header=ZOHO_TOKEN_HEADER, token=token
        )
        return headers
