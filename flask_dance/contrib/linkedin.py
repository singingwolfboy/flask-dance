from flask_dance.consumer import OAuth2ConsumerBlueprint
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object

from flask import _app_ctx_stack as stack


__maintainer__ = "David Baumgold <david@davidbaumgold.com>"


def make_linkedin_blueprint(
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
    Make a blueprint for authenticating with LinkedIn using OAuth 2. This requires
    a client ID and client secret from LinkedIn. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables :envvar:`LINKEDIN_OAUTH_CLIENT_ID` and
    :envvar:`LINKEDIN_OAUTH_CLIENT_SECRET`.

    Args:
        client_id (str): The client ID for your application on LinkedIn.
        client_secret (str): The client secret for your application on LinkedIn
        scope (str, optional): comma-separated list of scopes for the OAuth token
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/linkedin``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/linkedin/authorized``.
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
    linkedin_bp = OAuth2ConsumerBlueprint(
        "linkedin",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url="https://api.linkedin.com/v2/",
        authorization_url="https://www.linkedin.com/oauth/v2/authorization",
        token_url="https://www.linkedin.com/oauth/v2/accessToken",
        token_url_params={"include_client_id": True},
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        storage=storage,
        rule_kwargs=rule_kwargs,
    )
    linkedin_bp.from_config["client_id"] = "LINKEDIN_OAUTH_CLIENT_ID"
    linkedin_bp.from_config["client_secret"] = "LINKEDIN_OAUTH_CLIENT_SECRET"

    @linkedin_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.linkedin_oauth = linkedin_bp.session

    return linkedin_bp


linkedin = LocalProxy(partial(_lookup_app_object, "linkedin_oauth"))
