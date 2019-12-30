from __future__ import unicode_literals

from flask_dance.consumer import OAuth2ConsumerBlueprint
from requests_oauthlib.compliance_fixes.instagram import instagram_compliance_fix
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


__maintainer__ = "Adam Goldschmidt <adamgold7@gmail.com>"


class InstagramBlueprint(OAuth2ConsumerBlueprint):
    def session_created(self, session):
        return instagram_compliance_fix(session)


def make_instagram_blueprint(
    client_id=None,
    client_secret=None,
    scope=None,
    redirect_url=None,
    redirect_to=None,
    login_url=None,
    authorized_url=None,
    session_class=None,
    storage=None,
):
    """
    Make a blueprint for authenticating with Instagram using OAuth 2. This requires
    a client ID and client secret from Instagram. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables INSTAGRAM_OAUTH_CLIENT_ID and INSTAGRAM_OAUTH_CLIENT_SECRET.

    Args:
        client_id (str): The client ID for your application on INSTAGRAM.
        client_secret (str): The client secret for your application on INSTAGRAM
        scope (str, optional): comma-separated list of scopes for the OAuth token
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/instagram``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/instagram/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.consumer.requests.OAuth2Session`.
        storage: A token storage class, or an instance of a token storage
                class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.storage.session.SessionStorage`.

    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :ref:`blueprint <flask:blueprints>` to attach to your Flask app.
    """
    scope = scope or ["identify", "chat:write:bot"]
    instagram_bp = InstagramBlueprint(
        "instagram",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url="https://api.instagram.com/v1/",
        authorization_url="https://api.instagram.com/oauth/authorize/",
        token_url="https://api.instagram.com/oauth/access_token",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        storage=storage,
        token_url_params={"include_client_id": True},
    )
    instagram_bp.from_config["client_id"] = "INSTAGRAM_OAUTH_CLIENT_ID"
    instagram_bp.from_config["client_secret"] = "INSTAGRAM_OAUTH_CLIENT_SECRET"

    @instagram_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.instagram_oauth = instagram_bp.session

    return instagram_bp


instagram = LocalProxy(partial(_lookup_app_object, "instagram_oauth"))
