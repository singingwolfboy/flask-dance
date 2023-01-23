from flask import g
from werkzeug.local import LocalProxy

from flask_dance.consumer import OAuth2ConsumerBlueprint

__maintainer__ = "Karan Bhatia <karan.bhatia@gmail.com>"


def make_dexcom_blueprint(
    client_id=None,
    client_secret=None,
    *,
    base_url="https://api.dexcom.com/",
    scope="offline_access",
    redirect_url=None,
    redirect_to=None,
    login_url=None,
    authorized_url=None,
    session_class=None,
    storage=None,
    rule_kwargs=None,
):
    """
    Make a blueprint for authenticating with Dexcom using OAuth 2. This requires
    a client ID and client secret from Dexcom. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables :envvar:`DEXCOM_OAUTH_CLIENT_ID` and
    :envvar:`DEXCOM_OAUTH_CLIENT_SECRET`.

    Args:
        client_id (str): The client ID for your application on Dexcom.
        client_secret (str): The client secret for your application on Dexcom
        scope (str, optional): comma-separated list of scopes for the OAuth token
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/dexcom``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/dexcom/authorized``.
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
    dexcom_bp = OAuth2ConsumerBlueprint(
        "dexcom",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url=base_url,
        authorization_url="https://api.dexcom.com/v2/oauth2/login",
        token_url="https://api.dexcom.com/v2/oauth2/token",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        storage=storage,
        rule_kwargs=rule_kwargs,
    )
    dexcom_bp.from_config["client_id"] = "DEXCOM_OAUTH_CLIENT_ID"
    dexcom_bp.from_config["client_secret"] = "DEXCOM_OAUTH_CLIENT_SECRET"
    dexcom_bp.auto_refresh_url = dexcom_bp.token_url

    @dexcom_bp.before_app_request
    def set_applocal_session():
        g.flask_dance_dexcom = dexcom_bp.session

    return dexcom_bp


dexcom = LocalProxy(lambda: g.flask_dance_dexcom)
