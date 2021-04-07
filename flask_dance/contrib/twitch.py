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
    redirect_url=None,
    redirect_to=None,
    login_url=None,
    base_url="https://api.twitch.tv/helix/",
    authorization_url="https://id.twitch.tv/oauth2/authorize",
    token_url="https://id.twitch.tv/oauth2/token",
    token_url_params={"include_client_id": True},
    authorized_url=None,
    session_class=None,
    storage=None, ):
    """[summary]

    Args:
        client_id ([type], optional): [description]. Defaults to None.
        client_secret ([type], optional): [description]. Defaults to None.
        scope ([type], optional): [description]. Defaults to None.
        redirect_url ([type], optional): [description]. Defaults to None.
        redirect_to ([type], optional): [description]. Defaults to None.
        login_url ([type], optional): [description]. Defaults to None.
        base_url (str, optional): [description]. Defaults to "https://api.twitch.tv/helix/".
        authorization_url (str, optional): [description]. Defaults to "https://id.twitch.tv/oauth2/authorize".
        token_url (str, optional): [description]. Defaults to "https://id.twitch.tv/oauth2/token".
        token_url_params (dict, optional): [description]. Defaults to {"include_client_id": True}.
        authorized_url ([type], optional): [description]. Defaults to authorized_url.
        session_class ([type], optional): [description]. Defaults to None.
        storage ([type], optional): [description]. Defaults to None.

    Raises:
        TypeError: [description]
        TypeError: [description]
        TypeError: [description]

    Returns:
        [type]: [description]
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
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        storage=storage,
    )
    if twitch_bp.client_id is None:
        twitch_bp.from_config["client_id"] = "TWITCH_OAUTH_CLIENT_ID"
    

    if twitch_bp.client_secret is None:
        twitch_bp.from_config["client_secret"] = "TWITCH_OAUTH_CLIENT_SECRET"
    

    

    @twitch_bp.before_app_request
    def set_applocal_session():

        ctx = stack.top

       # if twitch_bp.client_id is None:
       #     raise TypeError(f"client_id is required, currently is {type(twitch_bp.client_id)}")

        if type(twitch_bp.client_id) != str:
            raise MissingConfigException(f"client_id should be a str, is: {type(twitch_bp.client_id)}")

       # if twitch_bp.client_id is None:
       #     raise TypeError(f"client_id is required, currently is {type(twitch_bp.client_id)}")

        if type(twitch_bp.client_secret) != str:
            raise MissingConfigException(f"client_secret should be a str, is {type(twitch_bp.client_secret)}")
    

        twitch_bp.session.headers.update({"client-id": twitch_bp.client_id})

        ctx.twitch_oauth = twitch_bp.session

    return twitch_bp


twitch = LocalProxy(partial(_lookup_app_object, "twitch_oauth"))
