from functools import partial

from flask.globals import LocalProxy, _lookup_app_object
from flask_dance.consumer import OAuth2ConsumerBlueprint

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


def make_jira_blueprint(
    client_id=None,
    client_secret=None,
    scope=None,
    reprompt_consent=False,
    redirect_url=None,
    redirect_to=None,
    login_url=None,
    authorized_url=None,
    session_class=None,
    storage=None,
):
    """
    Make a blueprint for authenticating with Jira using OAuth 2. This requires
    a client ID and client secret from Jira. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables :envvar:`JIRA_OAUTH2_CLIENT_ID` and
    :envvar:`JIRA_OAUTH2_CLIENT_SECRET`.

    Args:
        client_id (str): The client ID for your application on Jira.
        client_secret (str): The client secret for your application on Jira.
        scope (str, optional): comma-separated list of scopes for the OAuth token.
        reprompt_consent (bool): If True, force Jira to re-prompt the user
            for their consent, even if the user has already given their
            consent. Defaults to False.
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete.
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`.
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/jira``.
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/jira/authorized``.
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
    if reprompt_consent:
        authorization_url_params["prompt"] = "consent"

    jira_bp = OAuth2ConsumerBlueprint(
        "jira",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url="https://api.atlassian.com/",
        authorization_url=(
            "https://auth.atlassian.com/authorize?audience=api.atlassian.com"
        ),
        token_url="https://auth.atlassian.com/oauth/token",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        authorization_url_params=authorization_url_params,
        session_class=session_class,
        storage=storage,
    )
    jira_bp.from_config["client_id"] = "JIRA_OAUTH2_CLIENT_ID"
    jira_bp.from_config["client_secret"] = "JIRA_OAUTH2_CLIENT_SECRET"

    @jira_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.jira_oauth = jira_bp.session

    return jira_bp


jira = LocalProxy(partial(_lookup_app_object, "jira_oauth"))
