from __future__ import unicode_literals

import os.path
from urlobject import URLObject
from oauthlib.oauth1 import SIGNATURE_RSA
from flask_dance.consumer import OAuth1ConsumerBlueprint
from flask_dance.consumer.requests import OAuth1Session
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object

try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


__maintainer__ = "David Baumgold <david@davidbaumgold.com>"


class JsonOAuth1Session(OAuth1Session):
    def __init__(self, *args, **kwargs):
        super(JsonOAuth1Session, self).__init__(*args, **kwargs)
        self.headers["Content-Type"] = "application/json"


def make_jira_blueprint(
    base_url,
    consumer_key=None,
    rsa_key=None,
    redirect_url=None,
    redirect_to=None,
    login_url=None,
    authorized_url=None,
    session_class=None,
    backend=None,
    storage=None,
):
    """
    Make a blueprint for authenticating with JIRA using OAuth 1. This requires
    a consumer key and RSA key for the JIRA application link. You should either
    pass them to this constructor, or make sure that your Flask application
    config defines them, using the variables JIRA_OAUTH_CONSUMER_KEY and
    JIRA_OAUTH_RSA_KEY.

    Args:
        base_url (str): The base URL of your JIRA installation. For example,
            for Atlassian's hosted Cloud JIRA, the base_url would be
            ``https://jira.atlassian.com``
        consumer_key (str): The consumer key for your Application Link on JIRA
        rsa_key (str or path): The RSA private key for your Application Link
            on JIRA. This can be the contents of the key as a string, or a path
            to the key file on disk.
        redirect_url (str): the URL to redirect to after the authentication
            dance is complete
        redirect_to (str): if ``redirect_url`` is not defined, the name of the
            view to redirect to after the authentication dance is complete.
            The actual URL will be determined by :func:`flask.url_for`
        login_url (str, optional): the URL path for the ``login`` view.
            Defaults to ``/jira``
        authorized_url (str, optional): the URL path for the ``authorized`` view.
            Defaults to ``/jira/authorized``.
        session_class (class, optional): The class to use for creating a
            Requests session. Defaults to
            :class:`~flask_dance.contrib.jira.JsonOAuth1Session`.
        storage: A token storage class, or an instance of a token storage
                class, to use for this blueprint. Defaults to
                :class:`~flask_dance.consumer.storage.session.SessionStorage`.

    :rtype: :class:`~flask_dance.consumer.OAuth1ConsumerBlueprint`
    :returns: A :ref:`blueprint <flask:blueprints>` to attach to your Flask app.
    """
    if rsa_key and os.path.isfile(rsa_key):
        with open(rsa_key) as f:
            rsa_key = f.read()
    base_url = URLObject(base_url)

    jira_bp = OAuth1ConsumerBlueprint(
        "jira",
        __name__,
        client_key=consumer_key,
        rsa_key=rsa_key,
        signature_method=SIGNATURE_RSA,
        base_url=base_url,
        request_token_url=base_url.relative("plugins/servlet/oauth/request-token"),
        access_token_url=base_url.relative("plugins/servlet/oauth/access-token"),
        authorization_url=base_url.relative("plugins/servlet/oauth/authorize"),
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
        session_class=session_class or JsonOAuth1Session,
        backend=backend,
        storage=storage,
    )
    jira_bp.from_config["client_key"] = "JIRA_OAUTH_CONSUMER_KEY"
    jira_bp.from_config["rsa_key"] = "JIRA_OAUTH_RSA_KEY"

    @jira_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.jira_oauth = jira_bp.session

    return jira_bp


jira = LocalProxy(partial(_lookup_app_object, "jira_oauth"))
