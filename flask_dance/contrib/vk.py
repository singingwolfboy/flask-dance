from __future__ import unicode_literals

from flask_dance.consumer import OAuth2ConsumerBlueprint
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


__maintainer__ = "Alexander Orlov <nitrok@gmail.com>"


def make_vk_blueprint(
        client_id=None, client_secret=None, scope=None, redirect_url=None,
        redirect_to=None, login_url=None, authorized_url=None,
        session_class=None, backend=None):
    """
    Make a blueprint for authenticating with VK using OAuth 2. This requires
    a client ID and client secret from VK. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables VK_OAUTH_CLIENT_ID and VK_OAUTH_CLIENT_SECRET.

    Args:
        client_id (str): The client ID for your application on VK.
        client_secret (str): The client secret for your application on VK
        scope (str, optional): comma-separated list of scopes for the OAuth token
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/vk``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/vk/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.consumer.requests.OAuth2Session`.
        backend: A storage backend class, or an instance of a storage
                backend class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.backend.session.SessionBackend`.

    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :ref:`blueprint <flask:blueprints>` to attach to your Flask app.
    """
    vk_bp = OAuth2ConsumerBlueprint("vk", __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url="https://api.vk.com/",
        authorization_url="https://oauth.vk.com/authorize",
        token_url="https://oauth.vk.com/access_token",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        backend=backend,
    )
    vk_bp.from_config["client_id"] = "VK_OAUTH_CLIENT_ID"
    vk_bp.from_config["client_secret"] = "VK_OAUTH_CLIENT_SECRET"

    @vk_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.vk_oauth = vk_bp.session

    return vk_bp

vk = LocalProxy(partial(_lookup_app_object, "vk_oauth"))
