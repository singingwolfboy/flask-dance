from flask_dance.consumer import OAuth2ConsumerBlueprint
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object

from flask import _app_ctx_stack as stack


__maintainer__ = "David Baumgold <david@davidbaumgold.com>"


def make_meetup_blueprint(
    key=None,
    secret=None,
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
    Make a blueprint for authenticating with Meetup using OAuth 2. This requires
    an OAuth consumer from Meetup. You should either pass the key and secret to
    this constructor, or make sure that your Flask application config defines
    them, using the variables :envvar:`MEETUP_OAUTH_CLIENT_ID` and
    :envvar:`MEETUP_OAUTH_CLIENT_SECRET`.

    Args:
        key (str): The OAuth consumer key for your application on Meetup
        secret (str): The OAuth consumer secret for your application on Meetup
        scope (str, optional): comma-separated list of scopes for the OAuth token
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/meetup``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/meetup/authorized``.
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
    scope = scope or ["basic"]
    meetup_bp = OAuth2ConsumerBlueprint(
        "meetup",
        __name__,
        client_id=key,
        client_secret=secret,
        scope=scope,
        base_url="https://api.meetup.com/2/",
        authorization_url="https://secure.meetup.com/oauth2/authorize",
        token_url="https://secure.meetup.com/oauth2/access",
        token_url_params={"include_client_id": True},
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        storage=storage,
        rule_kwargs=rule_kwargs,
    )
    meetup_bp.from_config["client_id"] = "MEETUP_OAUTH_CLIENT_ID"
    meetup_bp.from_config["client_secret"] = "MEETUP_OAUTH_CLIENT_SECRET"

    @meetup_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.meetup_oauth = meetup_bp.session

    return meetup_bp


meetup = LocalProxy(partial(_lookup_app_object, "meetup_oauth"))
