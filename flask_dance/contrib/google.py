from flask_dance.consumer import OAuth2ConsumerBlueprint
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object

from flask import _app_ctx_stack as stack


__maintainer__ = "David Baumgold <david@davidbaumgold.com>"


def make_google_blueprint(
    client_id=None,
    client_secret=None,
    *,
    scope=None,
    offline=False,
    reprompt_consent=False,
    reprompt_select_account=False,
    redirect_url=None,
    redirect_to=None,
    login_url=None,
    authorized_url=None,
    session_class=None,
    storage=None,
    hosted_domain=None,
    rule_kwargs=None,
):
    """
    Make a blueprint for authenticating with Google using OAuth 2. This requires
    a client ID and client secret from Google. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables :envvar:`GOOGLE_OAUTH_CLIENT_ID` and
    :envvar:`GOOGLE_OAUTH_CLIENT_SECRET`.

    Args:
        client_id (str): The client ID for your application on Google
        client_secret (str): The client secret for your application on Google
        scope (str, optional): comma-separated list of scopes for the OAuth token.
            Defaults to the "https://www.googleapis.com/auth/userinfo.profile" scope.
        offline (bool): Whether to request `offline access
            <https://developers.google.com/accounts/docs/OAuth2WebServer#offline>`_
            for the OAuth token. Defaults to False
        reprompt_consent (bool): If True, force Google to re-prompt the user
            for their consent, even if the user has already given their
            consent. Defaults to False
        reprompt_select_account (bool): If True, force Google to re-prompt the select account page,
            even if there is a single logged-in user. Defaults to False
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/google``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/google/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.consumer.requests.OAuth2Session`.
        storage: A token storage class, or an instance of a token storage
                class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.storage.session.SessionStorage`.
        hosted_domain (str, optional): The domain of the G Suite user. Used to indicate that the account selection UI
            should be optimized for accounts at this domain. Note that this only provides UI optimization, and requires
            response validation (see warning).
        rule_kwargs (dict, optional): Additional arguments that should be passed when adding
            the login and authorized routes. Defaults to ``None``.

    .. _google_hosted_domain_warning:
    .. warning::
       The ``hosted_domain`` argument **only provides UI optimization**. Don't rely on this argument to control
       who can access your application. You must verify that the ``hd`` claim of the response ID token matches the
       ``hosted_domain`` argument passed to ``make_google_blueprint``.

    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :doc:`blueprint <flask:blueprints>` to attach to your Flask app.
    """
    scope = scope or ["https://www.googleapis.com/auth/userinfo.profile"]
    authorization_url_params = {}
    prompt_params = []
    auto_refresh_url = None
    if offline:
        authorization_url_params["access_type"] = "offline"
        auto_refresh_url = "https://accounts.google.com/o/oauth2/token"
    if reprompt_consent:
        prompt_params.append("consent")
    if reprompt_select_account:
        prompt_params.append("select_account")
    if prompt_params:
        prompt_params = " ".join(prompt_params)
        authorization_url_params["prompt"] = prompt_params
    if hosted_domain:
        authorization_url_params["hd"] = hosted_domain
    google_bp = OAuth2ConsumerBlueprint(
        "google",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url="https://www.googleapis.com/",
        authorization_url="https://accounts.google.com/o/oauth2/auth",
        token_url="https://accounts.google.com/o/oauth2/token",
        auto_refresh_url=auto_refresh_url,
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        authorization_url_params=authorization_url_params,
        session_class=session_class,
        storage=storage,
        rule_kwargs=rule_kwargs,
    )
    google_bp.from_config["client_id"] = "GOOGLE_OAUTH_CLIENT_ID"
    google_bp.from_config["client_secret"] = "GOOGLE_OAUTH_CLIENT_SECRET"

    @google_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.google_oauth = google_bp.session

    return google_bp


google = LocalProxy(partial(_lookup_app_object, "google_oauth"))
