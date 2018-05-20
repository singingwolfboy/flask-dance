# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

try:
    from urllib.parse import quote_plus
except ImportError:
    from urllib import quote_plus
import pytest
import mock
import responses
import flask
from werkzeug.contrib.fixers import ProxyFix
from flask_dance.consumer import (
    OAuth1ConsumerBlueprint, oauth_authorized, oauth_error
)
from oauthlib.oauth1.rfc5849.utils import parse_authorization_header
from flask_dance.consumer.requests import OAuth1Session

try:
    import blinker
except ImportError:
    blinker = None
requires_blinker = pytest.mark.skipif(not blinker, reason="requires blinker")


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
    responses.add(
        responses.POST,
        "https://example.com/oauth/request_token",
        body="oauth_token=foobar&oauth_token_secret=bazqux",
    )
    app, _ = make_app()
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
        responses.calls[0].request.headers['Authorization'].decode('utf-8')
    ))
    assert auth_header["oauth_consumer_key"] == "client_key"
    assert "oauth_signature" in auth_header
    assert auth_header["oauth_callback"] == quote_plus("https://a.b.c/login/test-service/authorized")
    # check that we redirected the client
    assert resp.status_code == 302
    assert resp.headers["Location"] == "https://example.com/oauth/authorize?oauth_token=foobar"

@responses.activate
def test_login_url_forwarded_proto():
    responses.add(
        responses.POST,
        "https://example.com/oauth/request_token",
        body="oauth_token=foobar&oauth_token_secret=bazqux",
    )
    app, _ = make_app()
    app.wsgi_app = ProxyFix(app.wsgi_app)
    with app.test_client() as client:
        resp = client.get(
            "/login/test-service",
            base_url="http://a.b.c",
            headers={"X-Forwarded-Proto": "https"},
            follow_redirects=False,
        )
    auth_header = dict(parse_authorization_header(
        responses.calls[0].request.headers['Authorization'].decode('utf-8')
    ))
    # this should be https
    assert auth_header["oauth_callback"] == quote_plus("https://a.b.c/login/test-service/authorized")


@responses.activate
def test_authorized_url():
    responses.add(
        responses.POST,
        "https://example.com/oauth/access_token",
        body="oauth_token=xxx&oauth_token_secret=yyy",
    )
    app, _ = make_app()
    with app.test_client() as client:
        resp = client.get(
            "/login/test-service/authorized?oauth_token=foobar&oauth_verifier=xyz",
            base_url="https://a.b.c",
        )
        # check that we redirected the client
        assert resp.status_code == 302
        assert resp.headers["Location"] == "https://a.b.c/"
        # check that we obtained an access token
        assert len(responses.calls) == 1
        assert "Authorization" in responses.calls[0].request.headers
        auth_header = dict(parse_authorization_header(
            responses.calls[0].request.headers['Authorization'].decode('utf-8')
        ))
        assert auth_header["oauth_consumer_key"] == "client_key"
        assert auth_header["oauth_token"] == "foobar"
        assert auth_header["oauth_verifier"] == "xyz"
        # check that we stored the access token and secret in the session
        assert (
            flask.session["test-service_oauth_token"] ==
            {'oauth_token': 'xxx', 'oauth_token_secret': 'yyy'}
        )


@responses.activate
def test_redirect_url():
    responses.add(
        responses.POST,
        "https://example.com/oauth/access_token",
        body="oauth_token=xxx&oauth_token_secret=yyy",
    )
    blueprint = OAuth1ConsumerBlueprint("test-service", __name__,
        client_key="client_key",
        client_secret="client_secret",
        base_url="https://example.com",
        request_token_url="https://example.com/oauth/request_token",
        access_token_url="https://example.com/oauth/access_token",
        authorization_url="https://example.com/oauth/authorize",
        redirect_url="http://mysite.cool/whoa?query=basketball",
    )
    app = flask.Flask(__name__)
    app.secret_key = "secret"
    app.register_blueprint(blueprint, url_prefix="/login")


    with app.test_client() as client:
        resp = client.get(
            "/login/test-service/authorized?oauth_token=foobar&oauth_verifier=xyz",
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
        body="oauth_token=xxx&oauth_token_secret=yyy",
    )
    blueprint = OAuth1ConsumerBlueprint("test-service", __name__,
        client_key="client_key",
        client_secret="client_secret",
        base_url="https://example.com",
        request_token_url="https://example.com/oauth/request_token",
        access_token_url="https://example.com/oauth/access_token",
        authorization_url="https://example.com/oauth/authorize",
        redirect_to="my_view",
    )
    app = flask.Flask(__name__)
    app.secret_key = "secret"
    app.register_blueprint(blueprint, url_prefix="/login")

    @app.route("/blargl")
    def my_view():
        return "check out my url"

    with app.test_client() as client:
        resp = client.get(
            "/login/test-service/authorized?oauth_token=foobar&oauth_verifier=xyz",
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
        body="oauth_token=xxx&oauth_token_secret=yyy",
    )
    blueprint = OAuth1ConsumerBlueprint("test-service", __name__,
        client_key="client_key",
        client_secret="client_secret",
        base_url="https://example.com",
        request_token_url="https://example.com/oauth/request_token",
        access_token_url="https://example.com/oauth/access_token",
        authorization_url="https://example.com/oauth/authorize",
    )
    app = flask.Flask(__name__)
    app.secret_key = "secret"
    app.register_blueprint(blueprint, url_prefix="/login")

    with app.test_client() as client:
        resp = client.get(
            "/login/test-service/authorized?oauth_token=foobar&oauth_verifier=xyz",
            base_url="https://a.b.c",
        )
        # check that we redirected the client
        assert resp.status_code == 302
        assert resp.headers["Location"] == "https://a.b.c/"


@requires_blinker
def test_signal_oauth_authorized(request):
    app, bp = make_app()
    fake_token = {"access_token": "test-token"}
    bp.session.fetch_access_token = mock.Mock(return_value=fake_token)

    calls = []
    def callback(*args, **kwargs):
        calls.append((args, kwargs))

    oauth_authorized.connect(callback)
    request.addfinalizer(lambda: oauth_authorized.disconnect(callback))

    with app.test_client() as client:
        resp = client.get(
            "/login/test-service/authorized?oauth_token=foobar&oauth_verifier=xyz",
        )
        # check that we stored the token
        assert flask.session["test-service_oauth_token"] == fake_token

    assert len(calls), 1
    assert calls[0][0] == (bp,)
    assert calls[0][1] == {"token": fake_token}


@requires_blinker
def test_signal_oauth_authorized_abort(request):
    app, bp = make_app()
    bp.session.fetch_access_token = mock.Mock(return_value="test-token")

    calls = []
    def callback(*args, **kwargs):
        calls.append((args, kwargs))
        return False

    oauth_authorized.connect(callback)
    request.addfinalizer(lambda: oauth_authorized.disconnect(callback))

    with app.test_client() as client:
        resp = client.get(
            "/login/test-service/authorized?oauth_token=foobar&oauth_verifier=xyz",
        )
        # check that we did NOT store the token
        assert "test-token_oauth_token" not in flask.session

    # the callback should still have been called
    assert len(calls) == 1


@requires_blinker
def test_signal_oauth_authorized_response(request):
    app, bp = make_app()
    bp.session.fetch_access_token = mock.Mock(return_value="test-token")

    calls = []
    def callback(*args, **kwargs):
        calls.append((args, kwargs))
        return flask.redirect("/url")

    oauth_authorized.connect(callback)
    request.addfinalizer(lambda: oauth_authorized.disconnect(callback))

    with app.test_client() as client:
        resp = client.get(
            "/login/test-service/authorized?oauth_token=foobar&oauth_verifier=xyz",
        )
        assert resp.status_code == 302
        assert resp.headers["Location"] == "http://localhost/url"
        # check that we did NOT store the token
        assert "test-token_oauth_token" not in flask.session

    # the callback should still have been called
    assert len(calls) == 1


@requires_blinker
def test_signal_sender_oauth_authorized(request):
    app, bp = make_app()
    bp2 = OAuth1ConsumerBlueprint("test2", __name__,
        client_key="client_key",
        client_secret="client_secret",
        base_url="https://example.com",
        request_token_url="https://example.com/oauth/request_token",
        access_token_url="https://example.com/oauth/access_token",
        authorization_url="https://example.com/oauth/authorize",
        redirect_to="index",
    )
    app.register_blueprint(bp2, url_prefix="/login")

    calls = []
    def callback(*args, **kwargs):
        calls.append((args, kwargs))

    oauth_authorized.connect(callback, sender=bp)
    request.addfinalizer(lambda: oauth_authorized.disconnect(callback, sender=bp))

    with app.test_client() as client:
        bp.session.fetch_access_token = mock.Mock(return_value="test-token")
        bp2.session.fetch_access_token = mock.Mock(return_value="test2-token")
        resp = client.get(
            "/login/test2/authorized?oauth_token=foobar&oauth_verifier=xyz",
        )

    assert len(calls) == 0

    with app.test_client() as client:
        bp.session.fetch_access_token = mock.Mock(return_value="test-token")
        bp2.session.fetch_access_token = mock.Mock(return_value="test2-token")
        resp = client.get(
            "/login/test-service/authorized?oauth_token=foobar&oauth_verifier=xyz",
        )

    assert len(calls) == 1
    assert calls[0][0] == (bp,)
    assert calls[0][1] == {"token": "test-token"}

    with app.test_client() as client:
        bp.session.fetch_access_token = mock.Mock(return_value="test-token")
        bp2.session.fetch_access_token = mock.Mock(return_value="test2-token")
        resp = client.get(
            "/login/test2/authorized?oauth_token=foobar&oauth_verifier=xyz",
        )

    assert len(calls) == 1  # unchanged


@requires_blinker
@responses.activate
def test_signal_oauth_error_login(request):
    responses.add(
        responses.POST,
        "https://example.com/oauth/request_token",
        body="oauth_problem=nonce_used", status=401,
    )
    app, bp = make_app()

    calls = []
    def callback(*args, **kwargs):
        calls.append((args, kwargs))

    oauth_error.connect(callback)
    request.addfinalizer(lambda: oauth_error.disconnect(callback))

    with app.test_client() as client:
        resp = client.get(
            "/login/test-service",
            base_url="https://a.b.c",
        )

    assert len(calls) == 1
    assert calls[0][0] == (bp,)
    assert calls[0][1]["message"] == "Token request failed with code 401, response was 'oauth_problem=nonce_used'."
    assert resp.status_code == 302
    location = resp.headers["Location"]
    assert location == "https://a.b.c/"


@requires_blinker
@responses.activate
def test_signal_oauth_error_authorized(request):
    responses.add(
        responses.POST,
        "https://example.com/oauth/access_token",
        body="Invalid request token.", status=401,
    )
    app, bp = make_app()

    calls = []
    def callback(*args, **kwargs):
        calls.append((args, kwargs))

    oauth_error.connect(callback)
    request.addfinalizer(lambda: oauth_error.disconnect(callback))

    with app.test_client() as client:
        resp = client.get(
            "/login/test-service/authorized?"
            "oauth_token=faketoken&"
            "oauth_token_secret=fakesecret&"
            "oauth_verifier=fakeverifier",
            base_url="https://a.b.c",
        )

    assert len(calls) == 1
    assert calls[0][0] == (bp,)
    assert calls[0][1]["message"] == "Token request failed with code 401, response was 'Invalid request token.'."
    assert resp.status_code == 302


@requires_blinker
def test_signal_oauth_notoken_authorized(request):
    app, bp = make_app()

    calls = []
    def callback(*args, **kwargs):
        calls.append((args, kwargs))

    oauth_error.connect(callback)
    request.addfinalizer(lambda: oauth_error.disconnect(callback))

    with app.test_client() as client:
        resp = client.get(
            "/login/test-service/authorized?"
            "denied=faketoken",
            base_url="https://a.b.c",
        )

    assert len(calls) == 1
    assert calls[0][0] == (bp,)
    assert "Response does not contain a token" in calls[0][1]["message"]
    assert calls[0][1]["response"] == {'denied':'faketoken'}
    assert resp.status_code == 302
    location = resp.headers["Location"]
    assert location == "https://a.b.c/"

class CustomOAuth1Session(OAuth1Session):
    my_attr = "foobar"


def test_custom_session_class():
    bp = OAuth1ConsumerBlueprint("test", __name__,
        client_key="client_key",
        client_secret="client_secret",
        base_url="https://example.com",
        request_token_url="https://example.com/oauth/request_token",
        access_token_url="https://example.com/oauth/access_token",
        authorization_url="https://example.com/oauth/authorize",
        redirect_to="index",
        session_class=CustomOAuth1Session,
    )
    assert isinstance(bp.session, CustomOAuth1Session)
    assert bp.session.my_attr == "foobar"
