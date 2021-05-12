"""Blueprint for connecting to Twitch API."""

from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.requests import OAuth2Session
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object
import os

from flask import _app_ctx_stack as stack


__maintainer__ = "Kerry Hatcher <kerry.hatcher@protonmail.com>"


class ClientIdHeaderOAuth2Session(OAuth2Session):
    """
    https://blog.twitch.tv/en/2016/05/05/client-id-required-for-kraken-api-calls-afbb8e95f843/
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers["client-id"] = self.client_id


def make_twitch_blueprint(
    client_id=None,
    client_secret=None,
    *,
    scope=None,
    redirect_url=None,
    redirect_to=None,
    login_url=None,
    authorized_url=None,
    session_class=ClientIdHeaderOAuth2Session,
    storage=None,
    rule_kwargs=None,
):
    """Make a blueprint for authenticating with Twitch using OAuth 2.

    This requires a client ID and client secret from Twitch.
    You should either pass them to this constructor, or make sure that your
    Flask application config defines them, using the variables
    :envvar:`TWITCH_OAUTH_CLIENT_ID` and :envvar:`TWITCH_OAUTH_CLIENT_SECRET`.

    Args:
        client_id (str): The client ID for your application on Twitch.
            Defaults to app config "TWITCH_OAUTH_CLIENT_ID".
        client_secret (str): The client Secret for your application on Twitch.
            Defaults to app config "TWITCH_OAUTH_CLIENT_SECRET".
        scope (list, optional): Comma-separated list of scopes for the OAuth token.
            Defaults to None.
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/twitch``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/twitch/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.contrib.twitch.ClientIdHeaderOAuth2Session`.
        storage: A token storage class, or an instance of a token storage
                class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.storage.session.SessionStorage`.
        rule_kwargs (dict, optional): Additional arguments that should be passed when adding
            the login and authorized routes. Defaults to ``None``.

    Returns:
        :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint` A :doc:`blueprint <flask:blueprints>` to attach to your Flask app.
    """
    twitch_bp = OAuth2ConsumerBlueprint(
        "twitch",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url="https://api.twitch.tv/helix/",
        authorization_url="https://id.twitch.tv/oauth2/authorize",
        token_url="https://id.twitch.tv/oauth2/token",
        token_url_params={"include_client_id": True},
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        storage=storage,
        rule_kwargs=rule_kwargs,
    )

    twitch_bp.from_config["client_id"] = "TWITCH_OAUTH_CLIENT_ID"
    twitch_bp.from_config["client_secret"] = "TWITCH_OAUTH_CLIENT_SECRET"

    # TODO: The key won't auto renew. See https://github.com/singingwolfboy/flask-dance/issues/35
    # I think this will work but needs a test.
    twitch_bp.auto_refresh_url = twitch_bp.token_url
    twitch_bp.auto_refresh_kwargs = {
        "client_id": twitch_bp.client_id,
        "client_secret": twitch_bp.client_secret,
    }

    @twitch_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.twitch_oauth = twitch_bp.session

    return twitch_bp


twitch = LocalProxy(partial(_lookup_app_object, "twitch_oauth"))
