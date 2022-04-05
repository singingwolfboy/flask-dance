from functools import partial

from flask import _app_ctx_stack as stack
from flask.globals import LocalProxy, _lookup_app_object

from flask_dance.consumer import OAuth2ConsumerBlueprint

__maintainer__ = "David Baumgold <david@davidbaumgold.com>"


def make_nylas_blueprint(
    client_id=None,
    client_secret=None,
    *,
    scope="email",
    redirect_url=None,
    redirect_to=None,
    login_url=None,
    authorized_url=None,
    session_class=None,
    storage=None,
    rule_kwargs=None,
):
    """
    Make a blueprint for authenticating with Nylas using OAuth 2. This requires
    an API ID and API secret from Nylas. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables :envvar:`NYLAS_OAUTH_CLIENT_ID` and
    :envvar:`NYLAS_OAUTH_CLIENT_SECRET`.

    Args:
        client_id (str): The client ID for your developer account on Nylas.
        client_secret (str): The client secret for your developer account
            on Nylas.
        scope (str, optional): comma-separated list of scopes for the OAuth
            token. Defaults to "email".
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/nylas``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/nylas/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.consumer.requests.OAuth2Session`.
        storage: A token storage class, or an instance of a token storage
                class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.storage.session.SessionStorage`.
        rule_kwargs (dict, optional): Additional arguments that should be passed when adding
            the login and authorized routes. Defaults to ``None``.

    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :doc:`blueprint <flask:blueprints>` to attach to your Flask app.
    """
    nylas_bp = OAuth2ConsumerBlueprint(
        "nylas",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url="https://api.nylas.com/",
        authorization_url="https://api.nylas.com/oauth/authorize",
        token_url="https://api.nylas.com/oauth/token",
        token_url_params={"include_client_id": True},
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        storage=storage,
        rule_kwargs=rule_kwargs,
    )
    nylas_bp.from_config["client_id"] = "NYLAS_OAUTH_CLIENT_ID"
    nylas_bp.from_config["client_secret"] = "NYLAS_OAUTH_CLIENT_SECRET"

    @nylas_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.nylas_oauth = nylas_bp.session

    return nylas_bp


nylas = LocalProxy(partial(_lookup_app_object, "nylas_oauth"))
