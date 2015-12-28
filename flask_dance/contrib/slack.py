from __future__ import unicode_literals

from flask_dance.consumer import OAuth2ConsumerBlueprint
from requests_oauthlib.compliance_fixes.slack import slack_compliance_fix
from functools import partial
from werkzeug.urls import url_encode, url_decode
from urlobject import URLObject
from flask.globals import LocalProxy, _lookup_app_object
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


__maintainer__ = "David Baumgold <david@davidbaumgold.com>"


class SlackBlueprint(OAuth2ConsumerBlueprint):
    def session_created(self, session):
        return slack_compliance_fix(session)


def make_slack_blueprint(
        client_id=None, client_secret=None, scope=None, redirect_url=None,
        redirect_to=None, login_url=None, authorized_url=None,
        session_class=None, backend=None):
    """
    Make a blueprint for authenticating with Slack using OAuth 2. This requires
    a client ID and client secret from Slack. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables SLACK_OAUTH_CLIENT_ID and SLACK_OAUTH_CLIENT_SECRET.

    Args:
        client_id (str): The client ID for your application on Slack.
        client_secret (str): The client secret for your application on Slack
        scope (str, optional): comma-separated list of scopes for the OAuth token
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/slack``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/slack/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.consumer.requests.OAuth2Session`.
        backend: A storage backend class, or an instance of a storage
                backend class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.backend.session.SessionBackend`.

    :rtype: :class:`~flask_dance.consumer.OAuth2ConsumerBlueprint`
    :returns: A :ref:`blueprint <flask:blueprints>` to attach to your Flask app.
    """
    scope = scope or ["identify", "chat:write:bot"]
    slack_bp = SlackBlueprint("slack", __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url="https://slack.com/api/",
        authorization_url="https://slack.com/oauth/authorize",
        token_url="https://slack.com/api/oauth.access",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        backend=backend,
    )
    slack_bp.from_config["client_id"] = "SLACK_OAUTH_CLIENT_ID"
    slack_bp.from_config["client_secret"] = "SLACK_OAUTH_CLIENT_SECRET"

    @slack_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.slack_oauth = slack_bp.session

    return slack_bp

slack = LocalProxy(partial(_lookup_app_object, "slack_oauth"))
