from flask import g
from werkzeug.local import LocalProxy

from flask_dance.consumer import OAuth2ConsumerBlueprint

__maintainer__ = "Michael Delpech <michaeldel@protonmail.com>"


def make_discord_blueprint(
    client_id=None,
    client_secret=None,
    *,
    scope=None,
    redirect_url=None,
    redirect_to=None,
    login_url=None,
    authorized_url=None,
    session_class=None,
    storage=None,
    prompt="consent",
    rule_kwargs=None,
):
    """
    Make a blueprint for authenticating with Discord using OAuth 2. This requires
    a client ID and client secret from Discord. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables :envvar:`DISCORD_OAUTH_CLIENT_ID` and
    :envvar:`DISCORD_OAUTH_CLIENT_SECRET`.

    Args:
        client_id (str): The client ID for your application on Discord.
        client_secret (str): The client secret for your application on Discord
        scope (list, optional): list of scopes (str) for the OAuth token
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/discord``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/discord/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.consumer.requests.OAuth2Session`.
        storage: A token storage class, or an instance of a token storage
                class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.storage.session.SessionStorage`.
        prompt (str, optional): Define authorization flow.
            Defaults to ``consent``, setting it to ``None`` will skip user
            interaction if the application was previously approved.
        rule_kwargs (dict, optional): Additional arguments that should be passed when adding
            the login and authorized routes. Defaults to ``None``.

    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :doc:`blueprint <flask:blueprints>` to attach to your Flask app.
    """
    scope = scope or ["identify"]
    authorization_url_params = {"prompt": "consent"}
    if prompt is None:
        authorization_url_params["prompt"] = None
    discord_bp = OAuth2ConsumerBlueprint(
        "discord",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url="https://discord.com/",
        token_url="https://discord.com/api/oauth2/token",
        authorization_url="https://discord.com/api/oauth2/authorize",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        storage=storage,
        authorization_url_params=authorization_url_params,
        rule_kwargs=rule_kwargs,
    )
    discord_bp.from_config["client_id"] = "DISCORD_OAUTH_CLIENT_ID"
    discord_bp.from_config["client_secret"] = "DISCORD_OAUTH_CLIENT_SECRET"

    @discord_bp.before_app_request
    def set_applocal_session():
        g.flask_dance_discord = discord_bp.session

    return discord_bp


discord = LocalProxy(lambda: g.flask_dance_discord)
