from __future__ import unicode_literals

from flask_dance.consumer import OAuth2ConsumerBlueprint
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


__maintainer__ = "David Baumgold <david@davidbaumgold.com>"


def make_dropbox_blueprint(
    app_key=None,
    app_secret=None,
    scope=None,
    force_reapprove=False,
    disable_signup=False,
    require_role=None,
    redirect_url=None,
    redirect_to=None,
    login_url=None,
    authorized_url=None,
    session_class=None,
    storage=None,
):
    """
    Make a blueprint for authenticating with Dropbox using OAuth 2. This requires
    a client ID and client secret from Dropbox. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables :envvar:`DROPBOX_OAUTH_CLIENT_ID` and
    :envvar:`DROPBOX_OAUTH_CLIENT_SECRET`.

    For more information about the ``force_reapprove``, ``disable_signup``,
    and ``require_role`` arguments, `check the Dropbox API documentation
    <https://www.dropbox.com/developers-v1/core/docs#oa2-authorize>`_.

    Args:
        app_key (str): The client ID for your application on Dropbox.
        app_secret (str): The client secret for your application on Dropbox
        scope (str, optional): Comma-separated list of scopes for the OAuth token
        force_reapprove (bool): Force the user to approve the app again
            if they've already done so.
        disable_signup (bool): Prevent users from seeing a sign-up link
            on the authorization page.
        require_role (str): Pass the string ``work`` to require a Dropbox
            for Business account, or the string ``personal`` to require a
            personal account.
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/dropbox``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/dropbox/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.consumer.requests.OAuth2Session`.
        storage: A token storage class, or an instance of a token storage
                class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.storage.session.SessionStorage`.

    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :ref:`blueprint <flask:blueprints>` to attach to your Flask app.
    """
    authorization_url_params = {}
    if force_reapprove:
        authorization_url_params["force_reapprove"] = "true"
    if disable_signup:
        authorization_url_params["disable_signup"] = "true"
    if require_role:
        authorization_url_params["require_role"] = require_role

    dropbox_bp = OAuth2ConsumerBlueprint(
        "dropbox",
        __name__,
        client_id=app_key,
        client_secret=app_secret,
        scope=scope,
        base_url="https://api.dropbox.com/2/",
        authorization_url="https://www.dropbox.com/oauth2/authorize",
        token_url="https://api.dropbox.com/oauth2/token",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        authorization_url_params=authorization_url_params,
        session_class=session_class,
        storage=storage,
    )
    dropbox_bp.from_config["client_id"] = "DROPBOX_OAUTH_CLIENT_ID"
    dropbox_bp.from_config["client_secret"] = "DROPBOX_OAUTH_CLIENT_SECRET"

    @dropbox_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.dropbox_oauth = dropbox_bp.session

    return dropbox_bp


dropbox = LocalProxy(partial(_lookup_app_object, "dropbox_oauth"))
