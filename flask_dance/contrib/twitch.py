"""Blueprint for connecting to Twitch API."""

from flask_dance.consumer import OAuth2ConsumerBlueprint
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object
import os

from flask import _app_ctx_stack as stack


__maintainer__ = "Kerry Hatcher <kerry.hatcher@protonmail.com>"


class MissingConfigException(Exception):
    """Exception raised when a required config is missing."""


def make_twitch_blueprint(
    client_id=None,
    client_secret=None,
    scope=None,
    redirect_to=None,
    base_url="https://api.twitch.tv/helix/",
    authorization_url="https://id.twitch.tv/oauth2/authorize",
    token_url="https://id.twitch.tv/oauth2/token",
    token_url_params={"include_client_id": True},
    storage=None,
):
    """Make a blueprint for authenticating with Twitch using OAuth 2.

    This requires a client ID and client secret from Twitch.
    You should either pass them to this constructor, or make sure that your Flask application config defines them, using the variables :envvar:`TWITCH_OAUTH_CLIENT_ID` and :envvar:`TWITCH_OAUTH_CLIENT_SECRET`.
    
    Args:
        client_id (str): The client ID for your application on Twitch. Defaults to app config "TWITCH_OAUTH_CLIENT_ID".
        client_secret (str): The client Secret for your application on Twitch. Defaults to app config "TWITCH_OAUTH_CLIENT_SECRET".
        scope (list, optional): Comma-separated list of scopes for the OAuth token.Defaults to None.
        redirect_to (str, optional): If ``redirect_url`` is not defined, the name of the view to redirect to after the authentication dance is complete. Defaults to None.
        base_url (str, optional): Base URL for the Twitch API. Defaults to "{Twitch API}/helix/".
        authorization_url (str, optional): URL for the Twitch API login endpoint. Defaults to "{Twitch API}/oauth2/authorize".
        token_url (str, optional): URL for Twitch token API. Defaults to "{Twitch API}/oauth2/token".
        token_url_params (dict, optional): Options to send to the token URL. Defaults to {"include_client_id": True}.
        storage (class, optional): A token storage class, or an instance of a token storage class, to use for this blueprint. Defaults to None.

    Raises:
        MissingConfigException: If client_id or client_secret is missing when request is made.

    Returns:
        :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint` A :ref:`blueprint <flask:blueprints>` to attach to your Flask app.
    """
    twitch_bp = OAuth2ConsumerBlueprint(
        "twitch",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url=base_url,
        authorization_url=authorization_url,
        token_url=token_url,
        token_url_params=token_url_params,
        redirect_to=redirect_to,
        storage=storage,
    )

    twitch_bp.from_config["client_id"] = "TWITCH_OAUTH_CLIENT_ID"

    twitch_bp.from_config["client_secret"] = "TWITCH_OAUTH_CLIENT_SECRET"

    # TODO: The key won't auto renew. See https://github.com/singingwolfboy/flask-dance/issues/35 I think this will work but needs a test.
    twitch_bp.auto_refresh_url = twitch_bp.token_url
    twitch_bp.auto_refresh_kwargs = {
        "client_id": twitch_bp.client_id,
        "client_secret": twitch_bp.client_secret,
    }

    @twitch_bp.before_app_request
    def set_applocal_session():

        ctx = stack.top

        if twitch_bp.client_id is None:
            raise MissingConfigException(
                f"client_id is required, currently is {twitch_bp.client_id}. Type: {type(twitch_bp.client_id)}"
            )

        if twitch_bp.client_secret is None:
            raise MissingConfigException(
                f"client_secret is required, currently is  is {twitch_bp.client_secret}. Type: {type(twitch_bp.client_secret)}"
            )

        twitch_bp.session.headers.update({"client-id": twitch_bp.client_id})

        ctx.twitch_oauth = twitch_bp.session

    return twitch_bp


twitch = LocalProxy(partial(_lookup_app_object, "twitch_oauth"))
