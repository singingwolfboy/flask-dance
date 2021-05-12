from flask_dance.consumer import OAuth2ConsumerBlueprint
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object

from flask import _app_ctx_stack as stack


__maintainer__ = "Pieter Ennes <support@authentiq.com>"


def make_authentiq_blueprint(
    client_id=None,
    client_secret=None,
    *,
    scope="openid profile",
    redirect_url=None,
    redirect_to=None,
    login_url=None,
    authorized_url=None,
    session_class=None,
    storage=None,
    hostname="connect.authentiq.io",
    rule_kwargs=None,
):
    """
    Make a blueprint for authenticating with authentiq using OAuth 2. This requires
    a client ID and client secret from authentiq. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables :envvar:`AUTHENTIQ_OAUTH_CLIENT_ID` and
    :envvar:`AUTHENTIQ_OAUTH_CLIENT_SECRET`.

    Args:
        client_id (str): The client ID for your application on Authentiq.
        client_secret (str): The client secret for your application on Authentiq.
        scope (str, optional): comma-separated list of scopes for the OAuth token.
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete.
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`.
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/authentiq``.
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/authentiq/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.consumer.requests.OAuth2Session`.
        storage: A token storage class, or an instance of a token storage
                class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.storage.session.SessionStorage`.
        hostname (str, optional): If using a private instance of authentiq CE/EE,
            specify the hostname, default is ``connect.authentiq.io``.
        rule_kwargs (dict, optional): Additional arguments that should be passed when adding
            the login and authorized routes. Defaults to ``None``.

    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :doc:`blueprint <flask:blueprints>` to attach to your Flask app.
    """
    authentiq_bp = OAuth2ConsumerBlueprint(
        "authentiq",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url=f"https://{hostname}/",
        authorization_url=f"https://{hostname}/authorize",
        token_url=f"https://{hostname}/token",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        storage=storage,
        rule_kwargs=rule_kwargs,
    )
    authentiq_bp.from_config["client_id"] = "AUTHENTIQ_OAUTH_CLIENT_ID"
    authentiq_bp.from_config["client_secret"] = "AUTHENTIQ_OAUTH_CLIENT_SECRET"

    @authentiq_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.authentiq_oauth = authentiq_bp.session

    return authentiq_bp


authentiq = LocalProxy(partial(_lookup_app_object, "authentiq_oauth"))
