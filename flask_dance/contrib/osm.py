from flask import g
from werkzeug.local import LocalProxy

from flask_dance.consumer import OAuth2ConsumerBlueprint

__maintainer__ = "Martijn van Exel <m@rtijn.org>"


def make_osm_blueprint(
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
    Make a blueprint for authenticating with OpenStreetMap (OSM) using OAuth 2. This requires
    a client ID and client secret from OpenStreetMap. You should either pass them to
    this constructor, or make sure that your Flask application config defines
    them, using the variables :envvar:`OSM_OAUTH_CLIENT_ID` and
    :envvar:`OSM_OAUTH_CLIENT_SECRET`.

    Args:
        client_id (str): The client ID for your application on OpenStreetMap.
        client_secret (str): The client secret for your application on OpenStreetMap
        scope (str, optional): comma-separated list of scopes for the OAuth token
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/osm``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/osm/authorized``.
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
    osm_bp = OAuth2ConsumerBlueprint(
        "osm",
        __name__,
        client_id=client_id,
        client_secret=client_secret,
        scope=scope,
        base_url="https://www.openstreetmap.org/api/0.6/",
        authorization_url="https://www.openstreetmap.org/oauth2/authorize",
        token_url="https://www.openstreetmap.org/oauth2/token",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class,
        storage=storage,
        rule_kwargs=rule_kwargs,
    )
    osm_bp.from_config["client_id"] = "OSM_OAUTH_CLIENT_ID"
    osm_bp.from_config["client_secret"] = "OSM_OAUTH_CLIENT_SECRET"

    @osm_bp.before_app_request
    def set_applocal_session():
        g.flask_dance_osm = osm_bp.session

    return osm_bp


osm = LocalProxy(lambda: g.flask_dance_osm)
