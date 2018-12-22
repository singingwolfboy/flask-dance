from __future__ import unicode_literals

from flask_dance.consumer import OAuth2ConsumerBlueprint
from requests_oauthlib.compliance_fixes.slack import slack_compliance_fix
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


__maintainer__ = "David Baumgold <david@davidbaumgold.com>"


class SlackBlueprint(OAuth2ConsumerBlueprint):
    def __init__(self, name, import_name,
            client_id=None,
            client_secret=None,
            client=None,
            auto_refresh_url=None,
            auto_refresh_kwargs=None,
            scope=None,
            state=None,

            static_folder=None, static_url_path=None, template_folder=None,
            url_prefix=None, subdomain=None, url_defaults=None, root_path=None,

            login_url=None,
            authorized_url=None,
            base_url=None,
            authorization_url=None,
            authorization_url_params=None,
            token_url=None,
            token_url_params=None,
            redirect_url=None,
            redirect_to=None,
            session_class=None,
            backend=None,
            enable_slack_app_directory=False,
            **kwargs):
        """
        Most of the constructor arguments are forwarded either to the
        :class:`flask.Blueprint` constructor or the
        :class:`requests_oauthlib.OAuth2Session` constructor, including
        ``**kwargs`` (which is forwarded to
        :class:`~requests_oauthlib.OAuth2Session`).
        :param: enable_slack_app_directory
        Defaults to False. If set to True, modifies ``authorized_url``
        to ``{authorized_url}/strong`` and the original ``authorized_url``
        view does not check OAuth ``state``.
        """
        if enable_slack_app_directory:
            weak_authorized_url = authorized_url or "/{bp.name}/authorized"
            authorized_url = weak_authorized_url.rstrip("/") + "/strong"

        OAuth2ConsumerBlueprint.__init__(
            self, name, import_name,
            client_id=client_id,
            client_secret=client_secret,
            client=client,
            auto_refresh_url=auto_refresh_url,
            auto_refresh_kwargs=auto_refresh_kwargs,
            scope=scope,
            state=state,

            static_folder=static_folder, static_url_path=static_url_path, template_folder=template_folder,
            url_prefix=url_prefix, subdomain=subdomain, url_defaults=url_defaults, root_path=root_path,

            login_url=login_url,
            authorized_url=authorized_url,
            base_url=base_url,
            authorization_url=authorization_url,
            authorization_url_params=authorization_url_params,
            token_url=token_url,
            token_url_params=token_url_params,
            redirect_url=redirect_url,
            redirect_to=redirect_to,
            session_class=session_class,
            backend=backend,

            **kwargs
        )

        if enable_slack_app_directory:
            self.add_url_rule(
                rule=weak_authorized_url.format(bp=self),
                endpoint="weak_authorized",
                view_func=partial(self.authorized, check_state=False),
            )

    def session_created(self, session):
        return slack_compliance_fix(session)


def make_slack_blueprint(
        client_id=None, client_secret=None, scope=None, redirect_url=None,
        redirect_to=None, login_url=None, authorized_url=None,
        session_class=None, backend=None, enable_slack_app_directory=False):
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
            Defaults to ``/slack/authorized``. If ``enable_slack_app_directory``
            is set to `True`, defaults to ``/slack/authorized/strong``
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.consumer.requests.OAuth2Session`.
        backend: A storage backend class, or an instance of a storage
                backend class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.backend.session.SessionBackend`.
        enable_slack_app_directory: Defaults to False.
            If set to `True`, appends `/strong` to ``authorized_url`` and
            passes this URL as redirect_uri to the provider. `/strong`
            will require presence (and matching) of `state` value from
            the provider, and the original ``authorized_url`` will not require it.
            This is needed to avoid double authorization when installing
            Slack app from Slack directory, but weakens security by not
            implementing CSRF protection on the original ``authorized_url`` path.

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
        enable_slack_app_directory=enable_slack_app_directory
    )
    slack_bp.from_config["client_id"] = "SLACK_OAUTH_CLIENT_ID"
    slack_bp.from_config["client_secret"] = "SLACK_OAUTH_CLIENT_SECRET"

    @slack_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.slack_oauth = slack_bp.session

    return slack_bp

slack = LocalProxy(partial(_lookup_app_object, "slack_oauth"))
