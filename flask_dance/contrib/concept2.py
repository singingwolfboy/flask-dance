from __future__ import unicode_literals

from flask_dance.consumer import OAuth2ConsumerBlueprint
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


__maintainer__ = "Stephen Wood <stephen@onabora.com>"


def make_concept2_blueprint(
        client_id=None, client_secret=None, scope=None, redirect_url=None,
        redirect_to=None, login_url=None, authorized_url=None,
        session_class=None, backend=None):
    """
    Make a blueprint for authenticating with Concept2 LogBook using OAuth 2. This requires
    a client ID and client secret from Concept2. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables CONCEPT2_OAUTH_CLIENT_ID and CONCEPT2_OAUTH_CLIENT_SECRET.

    Args:
        client_id (str): The client ID for your application on Concept2 Logbook API.
        client_secret (str): The client secret for your application on Concept2 Logbook API
        scope (str, optional): comma-separated list of scopes for the OAuth token
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/concept2``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/concept2/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.consumer.requests.OAuth2Session`.
        backend: A storage backend class, or an instance of a storage
                backend class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.backend.session.SessionBackend`.

    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :ref:`blueprint <flask:blueprints>` to attach to your Flask app.
    """
    concept2_bp = OAuth2ConsumerBlueprint("concept2", __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url="https://log.concept2.com/",
        authorization_url="https://log.concept2.com/oauth/authorize",
        token_url="https://log.concept2.com/oauth/access_token",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        backend=backend,
    )
    concept2_bp.from_config["client_id"] = "CONCEPT2_OAUTH_CLIENT_ID"
    concept2.from_config["client_secret"] = "CONCEPT2_OAUTH_CLIENT_SECRET"

    @concept2_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.concept2_oauth = concept2_bp.session

    return concept2_bp

concept2 = LocalProxy(partial(_lookup_app_object, "concept2_oauth"))
