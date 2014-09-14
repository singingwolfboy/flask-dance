# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import responses
from six.moves.urllib.parse import quote_plus
import flask
from flask_dance.consumer import OAuth1ConsumerBlueprint
from oauthlib.oauth1.rfc5849.utils import parse_authorization_header


def make_app(login_url=None):
    blueprint = OAuth1ConsumerBlueprint("test-service", __name__,
        client_key="client_key",
        client_secret="client_secret",
        base_url="https://example.com",
        request_token_url="https://example.com/oauth/request_token",
        access_token_url="https://example.com/oauth/access_token",
        authorization_url="https://example.com/oauth/authorize",
        redirect_to="index",
        login_url=login_url,
    )
    app = flask.Flask(__name__)
    app.secret_key = "secret"
    app.register_blueprint(blueprint, url_prefix="/login")

    @app.route("/")
    def index():
        return "index"

    return app

def test_generate_login_url():
    app = make_app()
    with app.test_request_context("/"):
        login_url = flask.url_for("test-service.login")
        assert login_url == "/login/test-service"

def test_override_login_url():
    app = make_app(login_url="/crazy/custom/url")
    with app.test_request_context("/"):
        login_url = flask.url_for("test-service.login")
        assert login_url == "/login/crazy/custom/url"

@responses.activate
def test_login_url():
    responses.add(
        responses.POST,
        "https://example.com/oauth/request_token",
        body="oauth_token=foobar&oauth_token_secret=bazqux",
    )
    app = make_app()
    client = app.test_client()
    resp = client.get(
        "/login/test-service",
        base_url="https://a.b.c",
        follow_redirects=False,
    )
    # check that we obtained a request token
    assert len(responses.calls) == 1
    assert "Authorization" in responses.calls[0].request.headers
    auth_header = dict(parse_authorization_header(
        responses.calls[0].request.headers['Authorization']
    ))
    assert auth_header["oauth_consumer_key"] == "client_key"
    assert "oauth_signature" in auth_header
    assert auth_header["oauth_callback"] == quote_plus("https://a.b.c/login/test-service/authorized")
    # check that we redirected the client
    assert resp.status_code == 302
    assert resp.headers["Location"] == "https://example.com/oauth/authorize?oauth_token=foobar"

@responses.activate
def test_authorized_url():
    responses.add(
        responses.POST,
        "https://example.com/oauth/access_token",
        body="oauth_token=xxx&oauth_token_secret=yyy",
    )
    app = make_app()
    with app.test_client() as client:
        resp = client.get(
            "/login/test-service/authorized?oauth_token=foobar&oauth_verifier=xyz",
            base_url="https://a.b.c",
        )
        # check that we obtained an access token
        assert len(responses.calls) == 1
        assert "Authorization" in responses.calls[0].request.headers
        auth_header = dict(parse_authorization_header(
            responses.calls[0].request.headers['Authorization']
        ))
        assert auth_header["oauth_consumer_key"] == "client_key"
        assert auth_header["oauth_token"] == "foobar"
        assert auth_header["oauth_verifier"] == "xyz"
        # check that we stored the access token and secret in the session
        assert (
            flask.session["test-service_oauth_token"] ==
            {'oauth_token': 'xxx', 'oauth_token_secret': 'yyy'}
        )
    # check that we redirected the client
    assert resp.status_code == 302
    assert resp.headers["Location"] == "https://a.b.c/"
