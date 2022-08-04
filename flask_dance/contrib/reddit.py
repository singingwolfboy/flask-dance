from flask import g
from werkzeug.local import LocalProxy

from flask_dance import __version__ as _flask_dance_version
from flask_dance.consumer import OAuth2ConsumerBlueprint, OAuth2Session

__maintainer__ = "Sergey Storchay <r8@r8.com.ua>"


DEFAULT_USER_AGENT = f"Flask-Dance/{_flask_dance_version}"


class RedditOAuth2Session(OAuth2Session):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # The Reddit API requires a non-generic user agent
        self.headers["User-Agent"] = self.blueprint.user_agent or DEFAULT_USER_AGENT

    def fetch_token(self, *args, **kwargs):
        # Pass client_id to session so it could trigger Basic Auth
        return super().fetch_token(client_id=self.blueprint.client_id, *args, **kwargs)


def make_reddit_blueprint(
    client_id=None,
    client_secret=None,
    *,
    scope="identity",
    permanent=False,
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
    Make a blueprint for authenticating with Reddit using OAuth 2. This requires
    a client ID and client secret from Reddit. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables :envvar:`REDDIT_OAUTH_CLIENT_ID` and
    :envvar:`REDDIT_OAUTH_CLIENT_SECRET`.

    Args:
        client_id (str): The client ID for your application on Reddit.
        client_secret (str): The client secret for your application on Reddit
        scope (str, optional): space-separated list of scopes for the OAuth token
            Defaults to ``identity``
        permanent (bool, optional): Whether to request permanent access token.
            Defaults to False, access will be valid for 1 hour
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/reddit``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/reddit/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.contrib.reddit.RedditOAuth2Session`.
        storage: A token storage class, or an instance of a token storage
            class, to use for this blueprint. Defaults to
            :class:`~flask_dance.consumer.storage.session.SessionStorage`.
        user_agent (str, optional): User agent for the requests to Reddit API.
            Defaults to ``Flask-Dance/{{version}}``.
        rule_kwargs (dict, optional): Additional arguments that should be passed when adding
            the login and authorized routes. Defaults to ``None``.

    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :doc:`blueprint <flask:blueprints>` to attach to your Flask app.
    """
    authorization_url_params = {}
    if permanent:
        authorization_url_params["duration"] = "permanent"

    reddit_bp = OAuth2ConsumerBlueprint(
        "reddit",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url="https://oauth.reddit.com/",
        authorization_url="https://www.reddit.com/api/v1/authorize",
        authorization_url_params=authorization_url_params,
        token_url="https://www.reddit.com/api/v1/access_token",
        auto_refresh_url="https://www.reddit.com/api/v1/access_token",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class or RedditOAuth2Session,
        storage=storage,
        rule_kwargs=rule_kwargs,
    )

    reddit_bp.from_config["client_id"] = "REDDIT_OAUTH_CLIENT_ID"
    reddit_bp.from_config["client_secret"] = "REDDIT_OAUTH_CLIENT_SECRET"

    reddit_bp.user_agent = user_agent

    @reddit_bp.before_app_request
    def set_applocal_session():
        g.flask_dance_reddit = reddit_bp.session

    return reddit_bp


reddit = LocalProxy(lambda: g.flask_dance_reddit)
