from flask import g
from werkzeug.local import LocalProxy

from flask_dance.consumer import OAuth2ConsumerBlueprint

__maintainer__ = "Matt Bachmann <bachmann.matt@gmail.com>"


def make_facebook_blueprint(
    client_id=None,
    client_secret=None,
    *,
    scope=None,
    redirect_url=None,
    redirect_to=None,
    login_url=None,
    authorized_url=None,
    rerequest_declined_permissions=False,
    session_class=None,
    storage=None,
    rule_kwargs=None,
):
    """
    Make a blueprint for authenticating with Facebook using OAuth 2. This requires
    a client ID and client secret from Facebook. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables :envvar:`FACEBOOK_OAUTH_CLIENT_ID` and
    :envvar:`FACEBOOK_OAUTH_CLIENT_SECRET`.

    Args:
        client_id (str): The client ID for your application on Facebook.
        client_secret (str): The client secret for your application on Facebook
        scope (str, optional): comma-separated list of scopes for the OAuth token
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/facebook``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/facebook/authorized``.
        rerequest_declined_permissions (bool, optional): should the blueprint ask again for declined permissions.
            Defaults to ``False``
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
    authorization_url_params = {}
    if rerequest_declined_permissions:
        authorization_url_params["auth_type"] = "rerequest"
    facebook_bp = OAuth2ConsumerBlueprint(
        "facebook",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url="https://graph.facebook.com/",
        authorization_url="https://www.facebook.com/dialog/oauth",
        authorization_url_params=authorization_url_params,
        token_url="https://graph.facebook.com/oauth/access_token",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        storage=storage,
        rule_kwargs=rule_kwargs,
    )
    facebook_bp.from_config["client_id"] = "FACEBOOK_OAUTH_CLIENT_ID"
    facebook_bp.from_config["client_secret"] = "FACEBOOK_OAUTH_CLIENT_SECRET"

    @facebook_bp.before_app_request
    def set_applocal_session():
        g.flask_dance_facebook = facebook_bp.session

    return facebook_bp


facebook = LocalProxy(lambda: g.flask_dance_facebook)
