from __future__ import unicode_literals

from flask_dance.consumer import OAuth1ConsumerBlueprint
from functools import partial
from flask.globals import LocalProxy, _lookup_app_object
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


def make_twitter_blueprint(api_key, api_secret,
                           redirect_url=None, redirect_to=None,
                           login_url=None, authorized_url=None):
    twitter_bp = OAuth1ConsumerBlueprint("twitter", __name__,
        client_key=api_key,
        client_secret=api_secret,
        base_url="https://api.twitter.com/1.1/",
        request_token_url="https://api.twitter.com/oauth/request_token",
        access_token_url="https://api.twitter.com/oauth/access_token",
        authorization_url="https://api.twitter.com/oauth/authorize",
        redirect_url=redirect_url,
        redirect_to=redirect_to,
        login_url=login_url,
        authorized_url=authorized_url,
    )

    @twitter_bp.before_app_request
    def set_applocal_session():
        ctx = stack.top
        ctx.twitter_oauth = twitter_bp.session

    return twitter_bp

twitter = LocalProxy(partial(_lookup_app_object, "twitter_oauth"))
