from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.requests import OAuth2Session
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object

from flask import _app_ctx_stack as stack


__maintainer__ = "David Baumgold <david@davidbaumgold.com>"


class HerokuOAuth2Session(OAuth2Session):
    def __init__(self, api_version, *args, **kwargs):
        super().__init__(*args, **kwargs)
        accept = f"application/vnd.heroku+json; version={api_version}"
        self.headers["Accept"] = accept


def make_heroku_blueprint(
    client_id=None,
    client_secret=None,
    *,
    scope=None,
    api_version="3",
    redirect_url=None,
    redirect_to=None,
    login_url=None,
    authorized_url=None,
    session_class=None,
    storage=None,
    rule_kwargs=None,
):
    """
    Make a blueprint for authenticating with Heroku using OAuth 2. This requires
    a client ID and client secret from Heroku. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables :envvar:`HEROKU_OAUTH_CLIENT_ID` and
    :envvar:`HEROKU_OAUTH_CLIENT_SECRET`.

    Args:
        client_id (str): The client ID for your application on Heroku.
        client_secret (str): The client secret for your application on Heroku
        scope (str, optional): comma-separated list of scopes for the OAuth token
        api_version (str): The version number of the Heroku API you want to use.
            Defaults to version 3.
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/heroku``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/heroku/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.contrib.HerokuOAuth2Session`.
        storage: A token storage class, or an instance of a token storage
                class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.storage.session.SessionStorage`.
        rule_kwargs (dict, optional): Additional arguments that should be passed when adding
            the login and authorized routes. Defaults to ``None``.

    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :doc:`blueprint <flask:blueprints>` to attach to your Flask app.
    """
    heroku_bp = OAuth2ConsumerBlueprint(
        "heroku",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        api_version=api_version,
        base_url="https://api.heroku.com/",
        authorization_url="https://id.heroku.com/oauth/authorize",
        token_url="https://id.heroku.com/oauth/token",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class or HerokuOAuth2Session,
        storage=storage,
        rule_kwargs=rule_kwargs,
    )
    heroku_bp.from_config["client_id"] = "HEROKU_OAUTH_CLIENT_ID"
    heroku_bp.from_config["client_secret"] = "HEROKU_OAUTH_CLIENT_SECRET"

    @heroku_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.heroku_oauth = heroku_bp.session

    return heroku_bp


heroku = LocalProxy(partial(_lookup_app_object, "heroku_oauth"))
