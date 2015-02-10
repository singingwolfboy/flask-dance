from __future__ import unicode_literals

from flask_dance.consumer import OAuth2ConsumerBlueprint
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


__maintainer__ = "David Baumgold <david@davidbaumgold.com>"


def make_google_blueprint(client_id=None, client_secret=None, scope=None,
                          redirect_url=None, redirect_to=None,
                          login_url=None, authorized_url=None,
                          session_class=None):
    """
    Make a blueprint for authenticating with Google using OAuth 2. This requires
    a client ID and client secret from Google. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET.

    Args:
        client_id (str): The client ID for your application on Github
        client_secret (str): The client secret for your application on Github
        scope (str, optional): comma-separated list of scopes for the OAuth token.
            Defaults to the "profile" scope.
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/google``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/google/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.consumer.oauth2.OAuth2SessionWithBaseURL`.

    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :ref:`blueprint <flask:blueprints>` to attach to your Flask app.
    """
    scope = scope or ["profile"]
    google_bp = OAuth2ConsumerBlueprint("google", __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url="https://www.googleapis.com/",
        authorization_url="https://accounts.google.com/o/oauth2/auth",
        token_url="https://accounts.google.com/o/oauth2/token",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
    )
    google_bp.from_config["client_id"] = "GOOGLE_OAUTH_CLIENT_ID"
    google_bp.from_config["client_secret"] = "GOOGLE_OAUTH_CLIENT_SECRET"

    @google_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.google_oauth = google_bp.session

    return google_bp

google = LocalProxy(partial(_lookup_app_object, "google_oauth"))
