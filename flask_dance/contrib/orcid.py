from flask import g
from werkzeug.local import LocalProxy

from flask_dance.consumer import OAuth2ConsumerBlueprint

__maintainer__ = "Matthew Evans <git@ml-evs.science>"


def make_orcid_blueprint(
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
    sandbox=False,
):
    """
    Make a blueprint for authenticating with ORCID (https://orcid.org)
    using OAuth2.

    This requires a client ID and client secret from ORCID. You should
    either pass them to this constructor, or make sure that your Flask
    application config defines them, using the variables
    :envvar:`ORCID_OAUTH_CLIENT_ID` and :envvar:`ORCID_OAUTH_CLIENT_SECRET`.

    The ORCID Sandbox API (https://sandbox.orcid.org) will be used if
    the ``sandbox`` argument is set to true.

    Args:
        client_id (str): The client ID for your application on ORCID.
        client_secret (str): The client secret for your application on ORCID
        scope (str, optional): comma-separated list of scopes for the OAuth token
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/orcid``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/orcid/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.consumer.requests.OAuth2Session`.
        storage: A token storage class, or an instance of a token storage
                class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.storage.session.SessionStorage`.
        rule_kwargs (dict, optional): Additional arguments that should be passed when adding
            the login and authorized routes. Defaults to ``None``.
        sandbox (bool): Whether to use the ORCID sandbox instead of the production API.

    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :doc:`blueprint <flask:blueprints>` to attach to your Flask app.
    """

    base_url = "https://api.orcid.org"
    authorization_url = "https://orcid.org/oauth/authorize"
    token_url = "https://orcid.org/oauth/token"
    if sandbox:
        base_url = "https://api.sandbox.orcid.org"
        authorization_url = "https://sandbox.orcid.org/oauth/authorize"
        token_url = "https://sandbox.orcid.org/oauth/token"

    orcid_bp = OAuth2ConsumerBlueprint(
        "orcid",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url=base_url,
        authorization_url=authorization_url,
        token_url=token_url,
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        storage=storage,
        rule_kwargs=rule_kwargs,
    )
    orcid_bp.from_config["client_id"] = "ORCID_OAUTH_CLIENT_ID"
    orcid_bp.from_config["client_secret"] = "ORCID_OAUTH_CLIENT_SECRET"

    @orcid_bp.before_app_request
    def set_applocal_session():
        g.flask_dance_orcid = orcid_bp.session

    return orcid_bp


orcid = LocalProxy(lambda: g.flask_dance_orcid)
