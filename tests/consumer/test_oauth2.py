# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

try:
    from urllib.parse import quote_plus, parse_qsl
except ImportError:
    from urllib import quote_plus
    from urlparse import parse_qsl

import mock
import responses
from urlobject import URLObject
import flask
from flask_dance.consumer import OAuth2ConsumerBlueprint, oauth_authorized
from flask_dance.consumer.oauth2 import OAuth2SessionWithBaseURL


def make_app(login_url=None):
    blueprint = OAuth2ConsumerBlueprint("test-service", __name__,
        client_id="client_id",
        client_secret="client_secret",
        scope="admin",
        state="random-string",
        base_url="https://example.com",
        authorization_url="https://example.com/oauth/authorize",
        token_url="https://example.com/oauth/access_token",
        redirect_to="index",
        login_url=login_url,
    )
    app = flask.Flask(__name__)
    app.secret_key = "secret"
    app.register_blueprint(blueprint, url_prefix="/login")

    @app.route("/")
    def index():
        return "index"

    return app, blueprint

def test_generate_login_url():
    app, _ = make_app()
    with app.test_request_context("/"):
        login_url = flask.url_for("test-service.login")
        assert login_url == "/login/test-service"

def test_override_login_url():
    app, _ = make_app(login_url="/crazy/custom/url")
    with app.test_request_context("/"):
        login_url = flask.url_for("test-service.login")
        assert login_url == "/login/crazy/custom/url"


@responses.activate
def test_login_url():
    app, _ = make_app()
    with app.test_client() as client:
        resp = client.get(
            "/login/test-service",
            base_url="https://a.b.c",
            follow_redirects=False,
        )
        # check that we saved the state in the session
        assert flask.session["test-service_oauth_state"] == "random-string"
    # check that we redirected the client
    assert resp.status_code == 302
    location = URLObject(resp.headers["Location"])
    assert location.without_query() == "https://example.com/oauth/authorize"
    assert location.query_dict["client_id"] == "client_id"
    assert location.query_dict["redirect_uri"] == "https://a.b.c/login/test-service/authorized"
    assert location.query_dict["scope"] == "admin"
    assert location.query_dict["state"] == "random-string"

@responses.activate
def test_authorized_url():
    responses.add(
        responses.POST,
        "https://example.com/oauth/access_token",
        body='{"access_token":"foobar","token_type":"bearer","scope":"admin"}',
    )
    app, _ = make_app()
    with app.test_client() as client:
        # reset the session before the request
        with client.session_transaction() as sess:
            sess["test-service_oauth_state"] = "random-string"
        # make the request
        resp = client.get(
            "/login/test-service/authorized?code=secret-code&state=random-string",
            base_url="https://a.b.c",
        )
        # check that we redirected the client
        assert resp.status_code == 302
        assert resp.headers["Location"] == "https://a.b.c/"
        # check that we obtained an access token
        assert len(responses.calls) == 1
        request_data = dict(parse_qsl(responses.calls[0].request.body))
        assert request_data["client_id"] == "client_id"
        # check that we stored the access token and secret in the session
        assert (
            flask.session["test-service_oauth_token"] ==
            {'access_token': 'foobar', 'scope': ['admin'], 'token_type': 'bearer'}
        )


@responses.activate
def test_redirect_url():
    responses.add(
        responses.POST,
        "https://example.com/oauth/access_token",
        body='{"access_token":"foobar","token_type":"bearer","scope":"admin"}',
    )
    blueprint = OAuth2ConsumerBlueprint("test-service", __name__,
        client_id="client_id",
        client_secret="client_secret",
        state="random-string",
        base_url="https://example.com",
        authorization_url="https://example.com/oauth/authorize",
        token_url="https://example.com/oauth/access_token",
        redirect_url="http://mysite.cool/whoa?query=basketball",
    )
    app = flask.Flask(__name__)
    app.secret_key = "secret"
    app.register_blueprint(blueprint, url_prefix="/login")

    with app.test_client() as client:
        # reset the session before the request
        with client.session_transaction() as sess:
            sess["test-service_oauth_state"] = "random-string"
        # make the request
        resp = client.get(
            "/login/test-service/authorized?code=secret-code&state=random-string",
            base_url="https://a.b.c",
        )
        # check that we redirected the client
        assert resp.status_code == 302
        assert resp.headers["Location"] == "http://mysite.cool/whoa?query=basketball"


@responses.activate
def test_redirect_to():
    responses.add(
        responses.POST,
        "https://example.com/oauth/access_token",
        body='{"access_token":"foobar","token_type":"bearer","scope":"admin"}',
    )
    blueprint = OAuth2ConsumerBlueprint("test-service", __name__,
        client_id="client_id",
        client_secret="client_secret",
        state="random-string",
        base_url="https://example.com",
        authorization_url="https://example.com/oauth/authorize",
        token_url="https://example.com/oauth/access_token",
        redirect_to="my_view",
    )
    app = flask.Flask(__name__)
    app.secret_key = "secret"
    app.register_blueprint(blueprint, url_prefix="/login")

    @app.route("/blargl")
    def my_view():
        return "check out my url"

    with app.test_client() as client:
        # reset the session before the request
        with client.session_transaction() as sess:
            sess["test-service_oauth_state"] = "random-string"
        # make the request
        resp = client.get(
            "/login/test-service/authorized?code=secret-code&state=random-string",
            base_url="https://a.b.c",
        )
        # check that we redirected the client
        assert resp.status_code == 302
        assert resp.headers["Location"] == "https://a.b.c/blargl"


@responses.activate
def test_redirect_fallback():
    responses.add(
        responses.POST,
        "https://example.com/oauth/access_token",
        body='{"access_token":"foobar","token_type":"bearer","scope":"admin"}',
    )
    blueprint = OAuth2ConsumerBlueprint("test-service", __name__,
        client_id="client_id",
        client_secret="client_secret",
        state="random-string",
        base_url="https://example.com",
        authorization_url="https://example.com/oauth/authorize",
        token_url="https://example.com/oauth/access_token",
    )
    app = flask.Flask(__name__)
    app.secret_key = "secret"
    app.register_blueprint(blueprint, url_prefix="/login")

    @app.route("/blargl")
    def my_view():
        return "check out my url"

    with app.test_client() as client:
        # reset the session before the request
        with client.session_transaction() as sess:
            sess["test-service_oauth_state"] = "random-string"
        # make the request
        resp = client.get(
            "/login/test-service/authorized?code=secret-code&state=random-string",
            base_url="https://a.b.c",
        )
        # check that we redirected the client
        assert resp.status_code == 302
        assert resp.headers["Location"] == "https://a.b.c/"


def test_signal_oauth_authorized():
    app, bp = make_app()
    bp.session.fetch_token = mock.Mock(return_value="test-token")

    calls = []
    def callback(*args, **kwargs):
        calls.append((args, kwargs))

    oauth_authorized.connect(callback)

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["test-service_oauth_state"] = "random-string"

        resp = client.get(
            "/login/test-service/authorized?code=secret-code&state=random-string",
        )

    assert len(calls) == 1
    assert calls[0][0] == (bp,)
    assert calls[0][1] == {"token": "test-token"}


def test_signal_sender_oauth_authorized():
    app, bp = make_app()
    bp.session.fetch_token = mock.Mock(return_value="test-token")
    bp2 = OAuth2ConsumerBlueprint("test2", __name__,
        client_id="client_id",
        client_secret="client_secret",
        scope="admin",
        state="random-string",
        base_url="https://example.com",
        authorization_url="https://example.com/oauth/authorize",
        token_url="https://example.com/oauth/access_token",
        redirect_to="index",
    )
    bp2.session.fetch_token = mock.Mock(return_value="test2-token")
    app.register_blueprint(bp2, url_prefix="/login")

    calls = []
    def callback(*args, **kwargs):
        calls.append((args, kwargs))

    oauth_authorized.connect(callback, sender=bp)

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["test-service_oauth_state"] = "random-string"

        resp = client.get(
            "/login/test2/authorized?code=secret-code&state=random-string",
        )

    assert len(calls) == 0

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["test-service_oauth_state"] = "random-string"

        resp = client.get(
            "/login/test-service/authorized?code=secret-code&state=random-string",
        )

    assert len(calls) == 1
    assert calls[0][0] == (bp,)
    assert calls[0][1] == {"token": "test-token"}

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["test-service_oauth_state"] = "random-string"

        resp = client.get(
            "/login/test2/authorized?code=secret-code&state=random-string",
        )

    assert len(calls) == 1  # unchanged


class CustomOAuth2Session(OAuth2SessionWithBaseURL):
    my_attr = "foobar"


def test_custom_session_class():
    bp = OAuth2ConsumerBlueprint("test", __name__,
        client_id="client_id",
        client_secret="client_secret",
        scope="admin",
        state="random-string",
        base_url="https://example.com",
        authorization_url="https://example.com/oauth/authorize",
        token_url="https://example.com/oauth/access_token",
        redirect_to="index",
        session_class=CustomOAuth2Session,
    )
    assert isinstance(bp.session, CustomOAuth2Session)
    assert bp.session.my_attr == "foobar"
