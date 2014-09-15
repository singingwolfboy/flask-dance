from __future__ import unicode_literals

import os.path
from urlobject import URLObject
from oauthlib.oauth1 import SIGNATURE_RSA
from flask_dance.consumer import OAuth1ConsumerBlueprint
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


def make_jira_blueprint(consumer_key, rsa_key, base_url,
                        redirect_url=None, redirect_to=None,
                        login_url=None, authorized_url=None):
    if os.path.isfile(rsa_key):
        with open(rsa_key) as f:
            rsa_key = f.read()
    base_url = URLObject(base_url)

    jira_bp = OAuth1ConsumerBlueprint("jira", __name__,
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
    )
    jira_bp.session.headers["Content-Type"] = "application/json"

    @jira_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.jira_oauth = jira_bp.session

    return jira_bp

jira = LocalProxy(partial(_lookup_app_object, "jira_oauth"))
