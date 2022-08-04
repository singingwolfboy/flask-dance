from flask import g
from werkzeug.local import LocalProxy

from flask_dance.consumer import OAuth2ConsumerBlueprint

__maintainer__ = "Steven MARTINS <steven.martins.fr@gmail.com>"


def make_azure_blueprint(
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
    tenant="common",
    prompt=None,
    domain_hint=None,
    login_hint=None,
    rule_kwargs=None,
):
    """
    Make a blueprint for authenticating with Azure AD using OAuth 2. This requires
    a client ID and client secret from Azure AD. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables :envvar:`AZURE_OAUTH_CLIENT_ID` and
    :envvar:`AZURE_OAUTH_CLIENT_SECRET`.

    Args:
        client_id (str): The client ID for your application on Azure AD.
        client_secret (str): The client secret for your application on Azure AD
        scope (str, optional): comma-separated list of scopes for the OAuth token
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/azure``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/azure/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.consumer.requests.OAuth2Session`.
        storage: A token storage class, or an instance of a token storage
                class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.storage.session.SessionStorage`.
        tenant: Determine which accounts are allowed to authenticate with Azure.
                `See the Azure documentation for more information about this parameter.
                <https://docs.microsoft.com/en-us/azure/active-directory/develop/active-directory-v2-protocols#endpoints>`_
                Defaults to ``common``.
        prompt (str, optional): Indicate the type of user interaction that is required.
            Valid values are ``login``, ``select_account``, ``consent``, ``admin_consent``.
            Learn more about the options `here.
            <https://docs.microsoft.com/en-us/azure/active-directory/develop/v1-protocols-oauth-code#request-an-authorization-code>`_
            Defaults to ``None``
        domain_hint (str, optional): Provides a hint about the tenant or domain that
            the user should use to sign in. The value of the domain_hint is a
            registered domain for the tenant. If the tenant is federated to an
            on-premises directory, AAD redirects to the specified tenant federation server.
            Defaults to ``None``
        login_hint (str, optional): Can be used to pre-fill the username/email
            address field of the sign-in page for the user, if you know their
            username ahead of time. Often apps use this parameter during re-authentication,
            having already extracted the username from a previous sign-in using the
            preferred_username claim.
            Defaults to ``None``
        rule_kwargs (dict, optional): Additional arguments that should be passed when adding
            the login and authorized routes. Defaults to ``None``.

    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :doc:`blueprint <flask:blueprints>` to attach to your Flask app.
    """
    scope = scope or ["openid", "email", "profile", "User.Read"]
    authorization_url_params = {}
    if login_hint:
        authorization_url_params["login_hint"] = login_hint
    if domain_hint:
        authorization_url_params["domain_hint"] = domain_hint
    if prompt:
        authorization_url_params["prompt"] = prompt
    azure_bp = OAuth2ConsumerBlueprint(
        "azure",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url="https://graph.microsoft.com",
        authorization_url=f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize",
        token_url=f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        authorization_url_params=authorization_url_params,
        session_class=session_class,
        storage=storage,
        rule_kwargs=rule_kwargs,
    )
    azure_bp.from_config["client_id"] = "AZURE_OAUTH_CLIENT_ID"
    azure_bp.from_config["client_secret"] = "AZURE_OAUTH_CLIENT_SECRET"

    @azure_bp.before_app_request
    def set_applocal_session():
        g.flask_dance_azure = azure_bp.session

    return azure_bp


azure = LocalProxy(lambda: g.flask_dance_azure)
