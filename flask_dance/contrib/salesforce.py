from flask_dance.consumer import OAuth2ConsumerBlueprint
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object

from flask import _app_ctx_stack as stack


__maintainer__ = "Przemyslaw Kanach <kanach16@gmail.com>"


def make_salesforce_blueprint(
    client_id=None,
    client_secret=None,
    *,
    scope=None,
    reprompt_consent=False,
    hostname=None,
    is_sandbox=False,
    redirect_url=None,
    redirect_to=None,
    login_url=None,
    authorized_url=None,
    session_class=None,
    storage=None,
):
    """
    Make a blueprint for authenticating with Salesforce using OAuth 2. This requires
    a client ID and client secret from Salesforce. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables :envvar:`SALESFORCE_OAUTH_CLIENT_ID` and
    :envvar:`SALESFORCE_OAUTH_CLIENT_SECRET`.

    Args:
        client_id (str): The client ID for your application on Salesforce.
        client_secret (str): The client secret for your application on Salesforce.
        scope (str, optional): comma-separated list of scopes for the OAuth token.
        reprompt_consent (bool): If True, force Salesforce to re-prompt the user
            for their consent, even if the user has already given their
            consent. Defaults to False.
        hostname (str, optional): The hostname of your Salesforce instance.
            By default, Salesforce uses ``login.salesforce.com`` for production
            instances and ``test.salesforce.com`` for sandboxes.
        is_sandbox (bool): If hostname is not defined specify whether Salesforce
            instance is a sandbox. Defaults to False.
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete.
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`.
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/salesforce``.
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/salesforce/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.consumer.requests.OAuth2Session`.
        storage: A token storage class, or an instance of a token storage
                class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.storage.session.SessionStorage`.

    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :doc:`blueprint <flask:blueprints>` to attach to your Flask app.
    """
    authorization_url_params = {}
    if reprompt_consent:
        authorization_url_params["prompt"] = "consent"

    if not hostname:
        hostname = "test.salesforce.com" if is_sandbox else "login.salesforce.com"

    salesforce_bp = OAuth2ConsumerBlueprint(
        "salesforce",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url=f"https://{hostname}/",
        authorization_url=f"https://{hostname}/services/oauth2/authorize",
        token_url=f"https://{hostname}/services/oauth2/token",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        authorization_url_params=authorization_url_params,
        session_class=session_class,
        storage=storage,
    )
    salesforce_bp.from_config["client_id"] = "SALESFORCE_OAUTH_CLIENT_ID"
    salesforce_bp.from_config["client_secret"] = "SALESFORCE_OAUTH_CLIENT_SECRET"

    @salesforce_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.salesforce_oauth = salesforce_bp.session

    return salesforce_bp


salesforce = LocalProxy(partial(_lookup_app_object, "salesforce_oauth"))
