from __future__ import unicode_literals

from flask_dance.consumer import OAuth2ConsumerBlueprint, OAuth2Session
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object

from flask_dance import __version__ as _flask_dance_version

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack

__maintainer__ = "Sergey Storchay <r8@r8.com.ua>"


DEFAULT_USER_AGENT = "Flask-Dance/{version}".format(version=_flask_dance_version)


class RedditOAuth2Session(OAuth2Session):
    def __init__(self, *args, **kwargs):
        super(RedditOAuth2Session, self).__init__(*args, **kwargs)

        # The Reddit API requires a non-generic user agent
        self.headers["User-Agent"] = self.blueprint.user_agent or DEFAULT_USER_AGENT

    def fetch_token(self, *args, **kwargs):
        # Pass client_id to session so it could trigger Basic Auth
        return super(RedditOAuth2Session, self).fetch_token(
            client_id=self.blueprint.client_id, *args, **kwargs
        )


def make_reddit_blueprint(
    client_id=None,
    client_secret=None,
    scope="identity",
    permanent=False,
    redirect_url=None,
    redirect_to=None,
    login_url=None,
    authorized_url=None,
    session_class=None,
    backend=None,
    storage=None,
    user_agent=None,
):
    """
    Make a blueprint for authenticating with Reddit using OAuth 2. This requires
    a client ID and client secret from Reddit. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables REDDIT_OAUTH_CLIENT_ID and REDDIT_OAUTH_CLIENT_SECRET.

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
            Defaults to ``Flask-Dance/{{version}}``

    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :ref:`blueprint <flask:blueprints>` to attach to your Flask app.
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
        backend=backend,
        storage=storage,
    )

    reddit_bp.from_config["client_id"] = "REDDIT_OAUTH_CLIENT_ID"
    reddit_bp.from_config["client_secret"] = "REDDIT_OAUTH_CLIENT_SECRET"

    reddit_bp.user_agent = user_agent

    @reddit_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.reddit_oauth = reddit_bp.session

    return reddit_bp


reddit = LocalProxy(partial(_lookup_app_object, "reddit_oauth"))
