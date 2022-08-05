from flask import g, request
from werkzeug.local import LocalProxy

from flask_dance import __version__ as _flask_dance_version
from flask_dance.consumer import OAuth2ConsumerBlueprint, OAuth2Session

__maintainer__ = "Jimmy Hedman <jimmy.hedman@gmail.com>"


DEFAULT_USER_AGENT = f"Flask-Dance/{_flask_dance_version}"


class StravaOAuth2Session(OAuth2Session):
    def fetch_token(self, *args, **kwargs):
        # Pass client_id to session so it could trigger Basic Auth
        return super().fetch_token(
            include_client_id=True,
            method="POST",
            code=request.args.get("code"),
            *args,
            **kwargs,
        )


def make_strava_blueprint(
    client_id=None,
    client_secret=None,
    *,
    scope="read",
    redirect_url=None,
    redirect_to=None,
    login_url=None,
    authorized_url=None,
    session_class=None,
    storage=None,
    user_agent=None,
    rule_kwargs=None,
):
    """
    Make a blueprint for authenticating with Strava using OAuth 2. This requires
    a client ID and client secret from Strava. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables :envvar:`STRAVA_OAUTH_CLIENT_ID` and
    :envvar:`STRAVA_OAUTH_CLIENT_SECRET`.

    Args:
        client_id (str): The client ID for your application on Strava.
        client_secret (str): The client secret for your application on Strava
        scope (str, optional): space-separated list of scopes for the OAuth token
            Defaults to ``identity``
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/strava``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/strava/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.contrib.strava.StravaOAuth2Session`.
        storage: A token storage class, or an instance of a token storage
            class, to use for this blueprint. Defaults to
            :class:`~flask_dance.consumer.storage.session.SessionStorage`.
        user_agent (str, optional): User agent for the requests to Strava API.
            Defaults to ``Flask-Dance/{{version}}``.
        rule_kwargs (dict, optional): Additional arguments that should be passed when adding
            the login and authorized routes. Defaults to ``None``.

    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :doc:`blueprint <flask:blueprints>` to attach to your Flask app.
    """

    strava_bp = OAuth2ConsumerBlueprint(
        "strava",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url="https://www.strava.com/api/v3",
        authorization_url="https://www.strava.com/api/v3/oauth/authorize",
        token_url="https://www.strava.com/api/v3/oauth/token",
        auto_refresh_url="https://www.strava.com/api/v3/oauth/token",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class or StravaOAuth2Session,
        storage=storage,
        rule_kwargs=rule_kwargs,
    )

    strava_bp.from_config["client_id"] = "STRAVA_OAUTH_CLIENT_ID"
    strava_bp.from_config["client_secret"] = "STRAVA_OAUTH_CLIENT_SECRET"

    strava_bp.user_agent = user_agent

    @strava_bp.before_app_request
    def set_applocal_session():
        g.flask_dance_strava = strava_bp.session

    return strava_bp


strava = LocalProxy(lambda: g.flask_dance_strava)
