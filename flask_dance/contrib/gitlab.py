from flask import g
from werkzeug.local import LocalProxy

from flask_dance.consumer import OAuth2ConsumerBlueprint
from flask_dance.consumer.requests import OAuth2Session

__maintainer__ = "Justin Georgeson <jgeorgeson@lopht.net>"


class NoVerifyOAuth2Session(OAuth2Session):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.verify = False


def make_gitlab_blueprint(
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
    hostname="gitlab.com",
    verify_tls_certificates=True,
    rule_kwargs=None,
):
    """
    Make a blueprint for authenticating with GitLab using OAuth 2. This requires
    a client ID and client secret from GitLab. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables :envvar:`GITLAB_OAUTH_CLIENT_ID` and
    :envvar:`GITLAB_OAUTH_CLIENT_SECRET`.

    Args:
        client_id (str): The client ID for your application on GitLab.
        client_secret (str): The client secret for your application on GitLab
        scope (str, optional): comma-separated list of scopes for the OAuth token
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/gitlab``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/gitlab/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.consumer.requests.OAuth2Session`.
        storage: A token storage class, or an instance of a token storage
                class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.storage.session.SessionStorage`.
        hostname (str, optional): If using a private instance of GitLab CE/EE,
            specify the hostname, default is ``gitlab.com``.
        verify_tls_certificates (bool, optional): Specify whether TLS
            certificates should be verified. Set this to ``False`` if
            certificates fail to validate for self-hosted GitLab instances.
        rule_kwargs (dict, optional): Additional arguments that should be passed when adding
            the login and authorized routes. Defaults to ``None``.
            specify the hostname, default is ``gitlab.com``

    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :doc:`blueprint <flask:blueprints>` to attach to your Flask app.
    """
    if not verify_tls_certificates:
        if session_class:
            raise ValueError(
                "cannot override session_class and disable certificate validation"
            )
        else:
            session_class = NoVerifyOAuth2Session

    gitlab_bp = OAuth2ConsumerBlueprint(
        "gitlab",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url=f"https://{hostname}/api/v4/",
        authorization_url=f"https://{hostname}/oauth/authorize",
        token_url=f"https://{hostname}/oauth/token",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        storage=storage,
        token_url_params={"verify": verify_tls_certificates},
        rule_kwargs=rule_kwargs,
    )
    gitlab_bp.from_config["client_id"] = "GITLAB_OAUTH_CLIENT_ID"
    gitlab_bp.from_config["client_secret"] = "GITLAB_OAUTH_CLIENT_SECRET"

    @gitlab_bp.before_app_request
    def set_applocal_session():
        g.flask_dance_gitlab = gitlab_bp.session

    return gitlab_bp


gitlab = LocalProxy(lambda: g.flask_dance_gitlab)
