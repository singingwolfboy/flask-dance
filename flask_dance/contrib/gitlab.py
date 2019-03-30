from __future__ import unicode_literals

from flask_dance.consumer import OAuth2ConsumerBlueprint
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


__maintainer__ = "Justin Georgeson <jgeorgeson@lopht.net>"


def make_gitlab_blueprint(
    client_id=None,
    client_secret=None,
    scope=None,
    redirect_url=None,
    redirect_to=None,
    login_url=None,
    authorized_url=None,
    session_class=None,
    storage=None,
    hostname="gitlab.com",
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
            specify the hostname, default is ``gitlab.com``

    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :ref:`blueprint <flask:blueprints>` to attach to your Flask app.
    """
    gitlab_bp = OAuth2ConsumerBlueprint(
        "gitlab",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url="https://{hostname}/api/v4/".format(hostname=hostname),
        authorization_url="https://{hostname}/oauth/authorize".format(
            hostname=hostname
        ),
        token_url="https://{hostname}/oauth/token".format(hostname=hostname),
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        storage=storage,
    )
    gitlab_bp.from_config["client_id"] = "GITLAB_OAUTH_CLIENT_ID"
    gitlab_bp.from_config["client_secret"] = "GITLAB_OAUTH_CLIENT_SECRET"

    @gitlab_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.gitlab_oauth = gitlab_bp.session

    return gitlab_bp


gitlab = LocalProxy(partial(_lookup_app_object, "gitlab_oauth"))
