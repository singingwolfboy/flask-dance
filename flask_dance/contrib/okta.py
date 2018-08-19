from __future__ import unicode_literals

from flask_dance.consumer import OAuth2ConsumerBlueprint
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


__maintainer__ = "Tom Nolan <tomnolan95@gmail.com>"


def make_okta_blueprint(
        client_id=None, client_secret=None, base_url=None, scope=None, redirect_url=None,
        token_url=None, redirect_to=None, login_url=None, authorization_url=None,
        session_class=None, backend=None):
    """
    Make a blueprint for authenticating with Okta using OAuth 2. This requires
    a client ID and client secret from OKta. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables OKTA_OAUTH_CLIENT_ID and OKTA_OAUTH_CLIENT_SECRET.

    Args:
        client_id (str): The client ID for your application on Okta.
        client_secret (str): The client secret for your application on Okta
        scope (list, optional): list of scopes (str) for the OAuth token
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/okta``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/okta/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.consumer.requests.OAuth2Session`.
        backend: A storage backend class, or an instance of a storage
                backend class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.backend.session.SessionBackend`.

    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :ref:`blueprint <flask:blueprints>` to attach to your Flask app.
    """
    scope = scope or ["openid", "email", "profile"]
    okta_bp = OAuth2ConsumerBlueprint("okta", __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url=base_url,
        token_url=token_url,
        authorization_url=authorization_url,
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        session_class=session_class,
        backend=backend,
    )
    okta_bp.from_config["client_id"] = "OKTA_OAUTH_CLIENT_ID"
    okta_bp.from_config["client_secret"] = "OKTA_OAUTH_CLIENT_SECRET"

    @okta_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.okta_oauth = okta_bp.session

    return okta_bp

okta = LocalProxy(partial(_lookup_app_object, "okta_oauth"))
