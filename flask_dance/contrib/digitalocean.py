from flask_dance.consumer import OAuth2ConsumerBlueprint
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object

from flask import _app_ctx_stack as stack


__maintainer__ = "Michael Abrahamsen <support@conveyor.dev>"


def make_digitalocean_blueprint(
    client_id=None,
    client_secret=None,
    *,
    scope=None,
    redirect_url=None,
    redirect_to=None,
    login_url=None,
    authorized_url=None,
    session_class=None,
    storage=None,
    rule_kwargs=None,
):
    """
    Make a blueprint for authenticating with Digital Ocean using OAuth 2.
    This requires a client ID and client secret from Digital Ocean.
    You should either pass them to this constructor, or make sure that your
    Flask application config defines them, using the variables
    :envvar:`DIGITALOCEAN_OAUTH_CLIENT_ID` and
    :envvar:`DIGITALOCEAN_OAUTH_CLIENT_SECRET`.

    Args:
        client_id (str): Client ID for your application on Digital Ocean
        client_secret (str): Client secret for your Digital Ocean application
        scope (str, optional): comma-separated list of scopes for the OAuth
            token.
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/digitalocean``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/digitalocean/authorized``.
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
    digitalocean_bp = OAuth2ConsumerBlueprint(
        "digitalocean",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope.replace(",", " ") if scope else None,
        base_url="https://cloud.digitalocean.com/v1/oauth",
        authorization_url="https://cloud.digitalocean.com/v1/oauth/authorize",
        token_url="https://cloud.digitalocean.com/v1/oauth/token",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        storage=storage,
        rule_kwargs=rule_kwargs,
    )
    digitalocean_bp.from_config["client_id"] = "DIGITALOCEAN_OAUTH_CLIENT_ID"
    digitalocean_bp.from_config["client_secret"] = "DIGITALOCEAN_OAUTH_CLIENT_SECRET"

    @digitalocean_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.digitalocean_oauth = digitalocean_bp.session

    return digitalocean_bp


digitalocean = LocalProxy(partial(_lookup_app_object, "digitalocean_oauth"))
